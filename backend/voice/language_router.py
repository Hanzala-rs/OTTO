"""Language detection for text queries (non-voice path)."""
import re

from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0
SUPPORTED = {"ur", "en"}


def detect_lang(text: str) -> str:
    if not text or len(text.strip()) < 5:
        return "en"
    try:
        lang = detect(text)
        return lang if lang in SUPPORTED else "en"
    except LangDetectException:
        return "en"


_URDU_SCRIPT = re.compile(r"[؀-ۿ]")
_REPLY_LANGUAGES = {
    "urdu script": "Urdu, written in Urdu (Nastaliq/Arabic) script",
    "roman urdu": "Roman Urdu (Urdu written in Latin/English letters, NOT Urdu script)",
    "english": "English",
}


def reply_language(detected: str | None, text: str) -> str:
    """Instruction naming the script the answer must be written in. `detected` is the
    LLM's label from query rewriting; if it is missing, fall back to the script used."""
    label = (detected or "").strip().lower()
    if label not in _REPLY_LANGUAGES:
        label = "urdu script" if _URDU_SCRIPT.search(text or "") else "english"
    return _REPLY_LANGUAGES[label]
