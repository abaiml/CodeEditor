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

class CodeRequest(BaseModel):
    code: str
    language: str

@app.post("/run")
async def run_code(code_request: CodeRequest):
    payload = {
        "language": code_request.language,
        "version": "*",  # This uses the latest version of the language
        "files": [
            {
                "name": f"main.{ 'cpp' if code_request.language == 'cpp' else 'py' if code_request.language == 'python' else 'js' }",
                "content": code_request.code
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("https://emkc.org/api/v2/piston/execute", json=payload)
            response.raise_for_status()
            result = response.json()
            output = result.get("run", {}).get("output", "")
            return {"output": output}
        except httpx.HTTPStatusError as e:
            return {"output": f"Error executing code: {str(e)}"}
