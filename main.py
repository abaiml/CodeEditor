import os
import pty
import asyncio
import tempfile
import subprocess
import signal
import resource

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState

app = FastAPI()

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

    try:
        init_msg = await websocket.receive_json()
        code = init_msg.get("code")
        language = init_msg.get("language")
        if not code or not language:
            await websocket.send_text("Error: Missing code or language.")
            await websocket.close()
            return
    except Exception:
        await websocket.send_text("Error: Failed to receive code and language.")
        await websocket.close()
        return

    temp_dir = tempfile.TemporaryDirectory()
    file_path = ""
    cmd = []

    try:
        if language == "python":
            file_path = os.path.join(temp_dir.name, "script.py")
            with open(file_path, "w") as f:
                # Set recursion limit in the script itself
                f.write("import sys\nsys.setrecursionlimit(1000)\n")
                f.write(code)
            cmd = ["python3", file_path]

        elif language == "javascript":
            file_path = os.path.join(temp_dir.name, "script.js")
            with open(file_path, "w") as f:
                f.write(code)
            cmd = ["node", file_path]

        elif language == "cpp":
            file_path = os.path.join(temp_dir.name, "program.cpp")
            with open(file_path, "w") as f:
                f.write(code)

            exe_path = os.path.join(temp_dir.name, "program.out")
            compile_proc = subprocess.run(
                ["g++", file_path, "-o", exe_path], capture_output=True, text=True
            )
            if compile_proc.returncode != 0:
                await websocket.send_text(f"Compilation failed:\n{compile_proc.stderr}")
                await websocket.send_json({"type": "done"})
                await websocket.close()
                return
            cmd = [exe_path]

        else:
            await websocket.send_text(f"Error: Unsupported language '{language}'.")
            await websocket.send_json({"type": "done"})
            await websocket.close()
            return
    except Exception as e:
        await websocket.send_text(f"Internal error preparing code: {str(e)}")
        await websocket.send_json({"type": "done"})
        await websocket.close()
        return

    pid, fd = pty.fork()

    if pid == 0:
        try:
            # Set a time limit (e.g. 3 seconds)
            def timeout_handler(signum, frame):
                os._exit(1)
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(3)

            # Memory limit (64 MB max RAM)
            resource.setrlimit(resource.RLIMIT_AS, (64 * 1024 * 1024, resource.RLIM_INFINITY))

            os.execvp(cmd[0], cmd)
        except Exception:
            os._exit(1)
    else:
        loop = asyncio.get_event_loop()

        def read_pty():
            try:
                return os.read(fd, 1024)
            except OSError:
                return b""

        async def send_output():
            while True:
                data = await loop.run_in_executor(None, read_pty)
                if data:
                    if websocket.application_state == WebSocketState.CONNECTED:
                        try:
                            await websocket.send_text(data.decode(errors="ignore"))
                        except Exception:
                            break
                else:
                    break
            try:
                await websocket.send_json({"type": "done"})
            except:
                pass

        send_task = asyncio.create_task(send_output())

        try:
            while True:
                try:
                    data = await websocket.receive_text()
                    os.write(fd, data.encode())
                except WebSocketDisconnect:
                    break
                except Exception:
                    break
        finally:
            send_task.cancel()
            temp_dir.cleanup()
