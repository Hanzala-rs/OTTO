"""
TTS router:
  English -> edge-tts (en-US-GuyNeural, male)
  Urdu    -> edge-tts (ur-PK-AsadNeural, male)
"""
from __future__ import annotations
import tempfile
import os


async def _edge_tts(text: str, voice: str, rate: str = "-5%", pitch: str = "-2Hz") -> bytes:
    import edge_tts
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
        await communicate.save(tmp_path)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def synthesize(text: str, lang: str) -> bytes:
    """Return MP3 audio bytes for given text and language."""
    if lang == "ur":
        return await _edge_tts(text, voice="ur-PK-AsadNeural")
    return await _edge_tts(text, voice="en-US-GuyNeural")
