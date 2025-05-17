import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Update allowed origins to your frontend URL(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://unique-kleicha-411291.netlify.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PISTON_API_URL = "https://emkc.org/api/v2/piston/execute"  # or your self-hosted endpoint

class RunRequest(BaseModel):
    language: str
    code: str
    stdin: str = ""

@app.post("/run")
async def run_code(req: RunRequest):
    payload = {
        "language": req.language,
        "source": req.code,
        "stdin": req.stdin,
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(PISTON_API_URL, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            return {
                "output": data.get("output", ""),
                "run_time": data.get("run_time", None),
                "language": data.get("language", req.language),
            }
        except Exception as e:
            return {"output": f"Error executing code: {str(e)}"}
