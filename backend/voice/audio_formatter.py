"""Convert raw audio bytes to .ogg (Opus codec, 24 kHz) via ffmpeg."""
from __future__ import annotations
import subprocess
import tempfile
import os
from loguru import logger


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
