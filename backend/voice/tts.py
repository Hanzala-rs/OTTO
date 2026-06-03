"""
TTS router:
  English → ElevenLabs API     (free 10k chars)
  Urdu    → edge-tts            (Microsoft neural, ur-PK-AsadNeural, free)
"""
from __future__ import annotations
import asyncio
import tempfile
import os

from loguru import logger
from config.settings import get_settings


def _elevenlabs_tts(text: str) -> bytes:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
    s = get_settings()
    client = ElevenLabs(api_key=s.elevenlabs_api_key)
    audio = client.text_to_speech.convert(
        voice_id=s.elevenlabs_voice_id,
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75),
        output_format="pcm_24000",
    )
    return b"".join(audio)


def _edge_tts_urdu(text: str) -> bytes:
    """Microsoft Edge neural TTS — ur-PK-AsadNeural (male) or ur-PK-UzmaNeural (female)."""
    import edge_tts

    async def _generate() -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            communicate = edge_tts.Communicate(text, voice="ur-PK-AsadNeural")
            await communicate.save(tmp_path)
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return asyncio.run(_generate())


def _edge_tts_english(text: str) -> bytes:
    import edge_tts

    async def _generate() -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            communicate = edge_tts.Communicate(text, voice="en-US-JennyNeural")
            await communicate.save(tmp_path)
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return asyncio.run(_generate())


def synthesize(text: str, lang: str) -> bytes:
    """Return audio bytes (MP3) for given text and language."""
    if lang == "ur":
        return _edge_tts_urdu(text)
    return _edge_tts_english(text)
