"""LangSmith tracer setup — enabled via env vars in main.py."""
import os
from config.settings import get_settings


def configure_tracing() -> None:
    s = get_settings()
    if s.langchain_tracing_v2 and s.langchain_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = s.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = s.langchain_project
