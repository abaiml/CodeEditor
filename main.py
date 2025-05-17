import os
import pty
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState

app = FastAPI()

# Update allowed origins to your frontend URL(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://unique-kleicha-411291.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_terminal(websocket: WebSocket):
    await websocket.accept()

    pid, fd = pty.fork()
    if pid == 0:
        # Child process: replace with interpreter you want. For example:
        os.execvp("python3", ["python3"])
    else:
        loop = asyncio.get_event_loop()

        def read_pty():
            try:
                return os.read(fd, 1024)
            except OSError:
                return b""

        async def send_pty_output():
            while True:
                data = await loop.run_in_executor(None, read_pty)
                if data:
                    if websocket.application_state == WebSocketState.CONNECTED:
                        try:
                            await websocket.send_text(data.decode(errors="ignore"))
                        except:
                            break
                else:
                    break

        send_task = asyncio.create_task(send_pty_output())

        try:
            while True:
                data = await websocket.receive_text()
                os.write(fd, data.encode())
        except WebSocketDisconnect:
            pass
        finally:
            send_task.cancel()
