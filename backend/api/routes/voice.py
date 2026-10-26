"""Voice chat endpoint — accepts .ogg audio, returns .ogg audio."""
from __future__ import annotations
import time
import uuid
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

from voice.vad import has_speech
from voice.stt import transcribe
from voice.tts import synthesize
from voice.audio_formatter import to_ogg, decode_to_pcm16k
from rag.pipeline import get_rag_graph
from monitoring.voice_logger import log_voice_session

router = APIRouter()


@router.post("")
async def voice_chat(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(..., description="Audio file (.ogg, .webm, .wav)"),
    session_id: str = Form(default=None),
):
    session_id = session_id or str(uuid.uuid4())
    audio_bytes = await audio.read()
    total_start = time.perf_counter()

    if len(audio_bytes) < 200:
        raise HTTPException(status_code=400, detail="Audio too short or empty")

    # 0. Decode once to 16 kHz mono float32 (handles browser webm/opus)
    try:
        pcm = await run_in_threadpool(decode_to_pcm16k, audio_bytes)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not decode audio")

    # 1. VAD — reject silence
    if not await run_in_threadpool(has_speech, pcm):
        raise HTTPException(status_code=400, detail="No speech detected in audio")

    # 2. STT — Whisper
    stt_start = time.perf_counter()
    transcript = await run_in_threadpool(transcribe, pcm)
    stt_latency_ms = int((time.perf_counter() - stt_start) * 1000)
    if not transcript.text.strip():
        raise HTTPException(status_code=400, detail="Could not transcribe audio")

    language = transcript.language

    # 3. RAG pipeline (same as text path)
    rag_start = time.perf_counter()
    graph = get_rag_graph()
    result = await run_in_threadpool(graph.invoke, {
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

    rag_latency_ms = int((time.perf_counter() - rag_start) * 1000)

    text_response = result.get("response")
    if not text_response:
        raise HTTPException(status_code=500, detail="No response generated")

    # 4. TTS → 5. Convert to .ogg
    tts_start = time.perf_counter()
    raw_audio = await synthesize(text_response, language)
    ogg_audio = await run_in_threadpool(to_ogg, raw_audio, "mp3")
    tts_latency_ms = int((time.perf_counter() - tts_start) * 1000)
    total_latency_ms = int((time.perf_counter() - total_start) * 1000)

    background_tasks.add_task(
        log_voice_session,
        session_id=session_id,
        transcript=transcript.text,
        detected_lang=language,
        tts_engine="edge-tts",
        stt_latency_ms=stt_latency_ms,
        tts_latency_ms=tts_latency_ms,
        rag_latency_ms=rag_latency_ms,
        total_latency_ms=total_latency_ms,
    )

    return Response(
        content=ogg_audio,
        media_type="audio/ogg",
        headers={
            "X-Session-Id": session_id,
            "X-Transcript": quote(transcript.text),
            "X-Language": language,
            "X-Response": quote(text_response, safe=' '),
            "Access-Control-Expose-Headers": "X-Session-Id, X-Transcript, X-Language, X-Response",
        },
    )
