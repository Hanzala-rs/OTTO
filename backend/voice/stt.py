"""
faster-whisper STT — faster, lower memory, same accuracy as openai-whisper.
Uses CTranslate2 backend with int8 quantization for CPU efficiency.
"""
from __future__ import annotations
from functools import lru_cache
from dataclasses import dataclass

import numpy as np
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


def transcribe(audio: np.ndarray) -> TranscriptResult:
    """Transcribe 16 kHz mono float32 audio."""
    model = get_stt()

    # Detect language first (lightweight pass)
    _, info = model.transcribe(audio, beam_size=1)
    # Hindi (hi) and Punjabi (pa) are misdetected Urdu in this context
    whisper_lang = "en" if info.language == "en" else "ur"

    # Re-transcribe with correct language to get proper script
    # Greedy decoding: much faster on CPU for short voice queries
    segments, _ = model.transcribe(audio, beam_size=1, language=whisper_lang)
    text = " ".join(seg.text.strip() for seg in segments)
    return TranscriptResult(text=text.strip(), language=whisper_lang)
