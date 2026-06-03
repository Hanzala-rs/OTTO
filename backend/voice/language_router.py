"""Language detection for text queries (non-voice path)."""
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
