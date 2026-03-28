from __future__ import annotations

from fastapi import FastAPI  # type: ignore[import-untyped]
from fastapi.staticfiles import StaticFiles  # type: ignore[import-untyped]
from fastapi.responses import JSONResponse  # type: ignore[import-untyped]
from pydantic import BaseModel  # type: ignore[import-untyped]
import uuid
import os
from dotenv import load_dotenv  # type: ignore[import-untyped]
from agents import Orchestrator, blank_memory

load_dotenv()

app = FastAPI(title="Elite AI Travel Concierge API")

# In-memory session store
SESSIONS: dict[str, dict[str, object]] = {}
orchestrator = Orchestrator()


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


@app.post("/chat")
async def chat(req: ChatRequest) -> JSONResponse:
    sid: str = req.session_id
    if not sid or sid not in SESSIONS:
        sid = str(uuid.uuid4())
        SESSIONS[sid] = blank_memory()

    result: dict[str, object] = orchestrator.process(req.message, SESSIONS[sid])
    # Persist updated memory back
    if "memory" in result:
        SESSIONS[sid] = result["memory"]  # type: ignore[assignment]
    result["session_id"] = sid
    return JSONResponse(content=result)


@app.delete("/session/{session_id}")
async def clear_session(session_id: str) -> dict[str, str]:
    SESSIONS.pop(session_id, None)
    return {"message": "Session cleared"}


@app.get("/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "gemini": bool(os.getenv("GEMINI_API_KEY", ""))}


# Serve frontend static files
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn  # type: ignore[import-untyped]
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
