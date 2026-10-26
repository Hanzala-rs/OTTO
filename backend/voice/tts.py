"""
TTS router:
  English -> edge-tts (en-US-GuyNeural, male)
  Urdu    -> edge-tts (ur-PK-AsadNeural, male)
"""
from __future__ import annotations
import tempfile
import os
import re


MAX_SPOKEN_ROWS = 3   # table data rows read aloud; full table stays on screen
_MORE_ON_SCREEN = {"en": "More details are shown on screen.", "ur": "مزید تفصیلات اسکرین پر موجود ہیں۔"}


def _speech_text(text: str, lang: str = "en") -> str:
    """Strip markdown so TTS doesn't read symbols aloud. Displayed text is unchanged."""
    lines = []
    rows = 0          # data rows seen in the current table
    truncated = False
    for line in text.splitlines():
        line = line.strip()
        if re.fullmatch(r"\|?[\s:|-]+\|?", line):          # table separator row
            if lines and rows == 1:                         # row before separator is the header
                lines.pop()
                rows = 0
            continue
        if line.startswith("|"):                            # table row -> "a, b, c."
            rows += 1
            if rows > MAX_SPOKEN_ROWS:
                truncated = True
                continue
            cells = [c.strip() for c in line.strip("|").split("|") if c.strip()]
            line = ", ".join(cells) + "." if cells else ""
        else:
            rows = 0
        line = re.sub(r"^#{1,6}\s*|^[-*•]\s+|^\d+\.\s+", "", line)  # headings, bullets
        line = re.sub(r"[*_`]+", "", line)                  # bold/italic/code marks
        if line:
            lines.append(line)
    if truncated:
        lines.append(_MORE_ON_SCREEN.get(lang, _MORE_ON_SCREEN["en"]))
    return " ".join(lines)


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
    text = _speech_text(text, lang) or text
    if lang == "ur":
        return await _edge_tts(text, voice="ur-PK-AsadNeural")
    return await _edge_tts(text, voice="en-US-GuyNeural")
