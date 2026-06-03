"""Groq LLM client (free tier — llama-3.3-70b-versatile)."""
from functools import lru_cache
from langchain_groq import ChatGroq
from config.settings import get_settings


@lru_cache
def get_llm() -> ChatGroq:
    s = get_settings()
    return ChatGroq(
        api_key=s.groq_api_key,
        model=s.llm_model,
        temperature=s.llm_temperature,
    )
