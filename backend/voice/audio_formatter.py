"""Convert raw audio bytes to .ogg (Opus codec, 24 kHz) via ffmpeg."""
from __future__ import annotations
import subprocess
import tempfile
import os
import numpy as np
from loguru import logger


def decode_to_pcm16k(audio_bytes: bytes, timeout: int = 30) -> np.ndarray:
    """Decode any ffmpeg-readable audio (webm/opus, ogg, wav...) to 16 kHz mono float32."""
    try:
        proc = subprocess.run(
            [
                "ffmpeg", "-nostdin", "-loglevel", "error",
                "-i", "pipe:0",
                "-f", "f32le",
                "-ac", "1",
                "-ar", "16000",
                "pipe:1",
            ],
            input=audio_bytes,
            check=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as exc:
        logger.error(f"ffmpeg decode failed: {exc.stderr.decode(errors='ignore')}")
        raise
    return np.frombuffer(proc.stdout, dtype=np.float32).copy()  # writable for torch.from_numpy


def to_ogg(audio_bytes: bytes, input_format: str = "wav") -> bytes:
    """
    Takes raw audio bytes, outputs Opus-encoded OGG bytes.
    ffmpeg must be installed in the container (included in Dockerfile).
    """
    with tempfile.NamedTemporaryFile(suffix=f".{input_format}", delete=False) as inp:
        inp.write(audio_bytes)
        inp_path = inp.name

    out_path = inp_path.replace(f".{input_format}", ".ogg")

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", inp_path,
                "-c:a", "libopus",
                "-b:a", "24k",
                "-ar", "24000",
                "-ac", "1",
                out_path,
            ],
            check=True,
            capture_output=True,
        )
        with open(out_path, "rb") as f:
            return f.read()
    except subprocess.CalledProcessError as exc:
        logger.error(f"ffmpeg conversion failed: {exc.stderr.decode()}")
        raise
    finally:
        for path in (inp_path, out_path):
            if os.path.exists(path):
                os.unlink(path)
