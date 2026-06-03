"""Language detection for ingested documents."""
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Make detection deterministic
DetectorFactory.seed = 0

SUPPORTED = {"ur", "en"}


def detect_language(text: str) -> str:
    """Returns 'ur' or 'en'. Falls back to 'en' on failure."""
    if not text or len(text.strip()) < 10:
        return "en"
    try:
        lang = detect(text)
        return lang if lang in SUPPORTED else "en"
    except LangDetectException:
        return "en"
