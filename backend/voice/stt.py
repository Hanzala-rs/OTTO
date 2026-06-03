"""
faster-whisper STT — faster, lower memory, same accuracy as openai-whisper.
Uses CTranslate2 backend with int8 quantization for CPU efficiency.
"""
from __future__ import annotations
import tempfile
import os
from functools import lru_cache
from dataclasses import dataclass

from faster_whisper import WhisperModel
from loguru import logger

from config.settings import get_settings


@dataclass
class TranscriptResult:
    text: str
    language: str   # "en" or "ur"


@lru_cache
def get_stt() -> WhisperModel:
    model_size = get_settings().whisper_model
    logger.info(f"Loading faster-whisper model '{model_size}'...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    logger.info("faster-whisper ready.")
    return model


def transcribe(audio_bytes: bytes) -> TranscriptResult:
    model = get_stt()

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments, info = model.transcribe(tmp_path, beam_size=5)
        text = " ".join(seg.text.strip() for seg in segments)
        lang = info.language if info.language in ("ur", "en") else "en"
        return TranscriptResult(text=text.strip(), language=lang)
    finally:
        os.unlink(tmp_path)
