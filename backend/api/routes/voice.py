"""Voice chat endpoint — accepts .ogg audio, returns .ogg audio."""
from __future__ import annotations
import uuid

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response

from voice.vad import has_speech
from voice.stt import transcribe
from voice.tts import synthesize
from voice.audio_formatter import to_ogg
from rag.pipeline import get_rag_graph

router = APIRouter()


@router.post("")
async def voice_chat(
    audio: UploadFile = File(..., description="Audio file (.ogg, .webm, .wav)"),
    session_id: str = Form(default=None),
):
    session_id = session_id or str(uuid.uuid4())
    audio_bytes = await audio.read()

    # 1. VAD — reject silence
    if not has_speech(audio_bytes):
        raise HTTPException(status_code=400, detail="No speech detected in audio")

    # 2. STT — Whisper
    transcript = transcribe(audio_bytes)
    if not transcript.text.strip():
        raise HTTPException(status_code=400, detail="Could not transcribe audio")

    language = transcript.language

    # 3. RAG pipeline (same as text path)
    graph = get_rag_graph()
    result = graph.invoke({
        "session_id": session_id,
        "query": transcript.text,
        "language": language,
        "is_voice": True,
        "audio_bytes": audio_bytes,
        "transcript": transcript.text,
        "hyde_query": None,
        "retrieved_chunks": None,
        "reranked_chunks": None,
        "context": None,
        "response": None,
        "audio_response": None,
        "error": None,
    })

    text_response = result.get("response")
    if not text_response:
        raise HTTPException(status_code=500, detail="No response generated")

    # 4. TTS → 5. Convert to .ogg
    raw_audio = await synthesize(text_response, language)
    ogg_audio = to_ogg(raw_audio, input_format="mp3")

    return Response(
        content=ogg_audio,
        media_type="audio/ogg",
        headers={
            "X-Session-Id": session_id,
            "X-Transcript": transcript.text,
            "X-Language": language,
            "X-Response": text_response,
            "Access-Control-Expose-Headers": "X-Session-Id, X-Transcript, X-Language, X-Response",
        },
    )
