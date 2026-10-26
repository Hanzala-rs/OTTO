"""
Voice Activity Detection using silero-vad.
Strips silence before Whisper to prevent hallucination on empty audio.
"""
from __future__ import annotations
from functools import lru_cache

import numpy as np
import torch
from loguru import logger


@lru_cache
def _load_vad_model():
    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad",
        model="silero_vad",
        force_reload=False,
        trust_repo=True,
    )
    return model, utils


def has_speech(audio: np.ndarray, sample_rate: int = 16000) -> bool:
    """Return True if voice activity is detected in 16 kHz mono float32 audio."""
    try:
        model, (get_speech_timestamps, *_) = _load_vad_model()

        waveform = torch.from_numpy(audio)

        timestamps = get_speech_timestamps(
            waveform,
            model,
            sampling_rate=sample_rate,
            threshold=0.5,
        )
        return len(timestamps) > 0
    except Exception as exc:
        logger.warning(f"VAD check failed ({exc}), assuming speech present")
        return True
