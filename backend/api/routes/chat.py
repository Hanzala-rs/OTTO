"""Text chat endpoint."""
from __future__ import annotations
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from rag.pipeline import get_rag_graph
from voice.language_router import detect_lang

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    language: str


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    language = detect_lang(req.message)

    graph = get_rag_graph()
    result = graph.invoke({
        "session_id": session_id,
        "query": req.message,
        "language": language,
        "is_voice": False,
        "audio_bytes": None,
        "transcript": None,
        "hyde_query": None,
        "retrieved_chunks": None,
        "reranked_chunks": None,
        "context": None,
        "response": None,
        "audio_response": None,
        "error": None,
    })

    if not result.get("response"):
        raise HTTPException(status_code=500, detail="No response generated")

    return ChatResponse(
        response=result["response"],
        session_id=session_id,
        language=language,
    )
