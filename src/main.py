from __future__ import annotations

import logging

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

load_dotenv()

# Observability must be configured before any agents or AF clients are created
from src.observability import setup_observability
setup_observability()

from src.agents.host_agent import HostAgent
from src.config import get_settings
from src.database import Base, engine

# Create all tables on startup (no-op if they already exist)
Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=getattr(logging, get_settings().log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Restaurant Management System", version="0.1.0")

def _get_host_agent() -> HostAgent:
    return HostAgent()


@app.get("/health")
async def health() -> dict:
    settings = get_settings()
    return {"status": "ok", "provider": settings.model_provider.value}


@app.post("/chat")
async def chat(request: Request) -> JSONResponse:
    """Single-turn chat — runs the full handoff workflow and returns the final reply."""
    body = await request.json()
    message = body.get("message", "")
    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    agent = _get_host_agent()
    reply = await agent.route(message)
    return JSONResponse({"reply": reply})


@app.post("/chat/stream")
async def chat_stream(request: Request) -> StreamingResponse:
    """Streaming endpoint — yields WorkflowEvents as newline-delimited JSON."""
    import json

    body = await request.json()
    message = body.get("message", "")
    if not message:
        return StreamingResponse(iter([]), status_code=400)

    agent = _get_host_agent()

    async def event_generator():
        async for event in agent._workflow.run(message, stream=True):
            event_type = getattr(event, "type", None)
            data = getattr(event, "data", None)

            if event_type == "output" and hasattr(data, "messages"):
                for msg in data.messages:
                    if getattr(msg, "text", None):
                        payload = {
                            "type": "output",
                            "author": msg.author_name or msg.role,
                            "text": msg.text,
                        }
                        yield json.dumps(payload) + "\n"

            elif event_type == "output" and hasattr(data, "contents"):
                for content in data.contents:
                    if getattr(content, "text", None):
                        payload = {
                            "type": "output",
                            "author": data.author_name or data.role,
                            "text": content.text,
                        }
                        yield json.dumps(payload) + "\n"

            elif event_type == "handoff_sent":
                payload = {"type": "handoff_sent", "from": data.source, "to": data.target}
                yield json.dumps(payload) + "\n"

            elif event_type in ("executor_invoked", "executor_completed"):
                payload = {"type": event_type}
                yield json.dumps(payload) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


if __name__ == "__main__":
    settings = get_settings()
    logger.info(
        "Starting Restaurant Management System | provider=%s | port=%d",
        settings.model_provider.value,
        settings.app_port,
    )
    uvicorn.run(
        "src.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )

