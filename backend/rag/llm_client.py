"""LLM client — OpenAI-compatible LiteLLM proxy (Groq behind it; proxy owns retries/rpm/fallbacks)."""
from functools import lru_cache
from langchain_openai import ChatOpenAI
from config.settings import get_settings


@lru_cache
def get_llm(model: str | None = None) -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        base_url=s.llm_proxy_url,
        api_key=s.llm_proxy_key,
        model=model or s.llm_proxy_model,
        temperature=s.llm_temperature,
        timeout=20,
        max_retries=0,
    )
