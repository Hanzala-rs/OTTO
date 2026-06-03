"""
Voice Activity Detection using silero-vad.
Strips silence before Whisper to prevent hallucination on empty audio.
"""
from __future__ import annotations
import io
from functools import lru_cache

import torch
import torchaudio
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


def has_speech(audio_bytes: bytes, sample_rate: int = 16000) -> bool:
    """Return True if voice activity is detected in the audio bytes."""
    try:
        model, (get_speech_timestamps, *_) = _load_vad_model()

        waveform, sr = torchaudio.load(io.BytesIO(audio_bytes))
        if sr != sample_rate:
            waveform = torchaudio.functional.resample(waveform, sr, sample_rate)

        # Mono
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        timestamps = get_speech_timestamps(
            waveform.squeeze(),
            model,
            sampling_rate=sample_rate,
            threshold=0.5,
        )
        return len(timestamps) > 0
    except Exception as exc:
        logger.warning(f"VAD check failed ({exc}), assuming speech present")
        return True
