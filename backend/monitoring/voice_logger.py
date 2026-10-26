"""Writes per-session latency/engine analytics to the voice_logs table (see
database/migrations/002_voice_logs.sql). Best-effort — a logging failure must
never break the voice response, so all errors are swallowed and logged."""
from __future__ import annotations

import psycopg2
from loguru import logger

from config.settings import get_settings


def log_voice_session(
    session_id: str,
    transcript: str,
    detected_lang: str,
    tts_engine: str,
    stt_latency_ms: int,
    tts_latency_ms: int,
    rag_latency_ms: int,
    total_latency_ms: int,
) -> None:
    try:
        conn = psycopg2.connect(get_settings().postgres_url)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO voice_logs (
                        session_id, transcript, detected_lang, tts_engine,
                        stt_latency_ms, tts_latency_ms, rag_latency_ms, total_latency_ms
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        session_id,
                        transcript,
                        detected_lang,
                        tts_engine,
                        stt_latency_ms,
                        tts_latency_ms,
                        rag_latency_ms,
                        total_latency_ms,
                    ),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        logger.exception(f"Failed to write voice_logs row for session {session_id}")
