"""Groq LLM client (free tier — llama-3.3-70b-versatile)."""
from functools import lru_cache
from langchain_groq import ChatGroq
from langchain_core.rate_limiters import InMemoryRateLimiter
from config.settings import get_settings

# Stay within Groq free tier: ~30 req/min across HyDE + LLM calls
_rate_limiter = InMemoryRateLimiter(requests_per_second=0.4, check_every_n_seconds=0.1)


@lru_cache
def get_llm() -> ChatGroq:
    s = get_settings()
    return ChatGroq(
        api_key=s.groq_api_key,
        model=s.llm_model,
        temperature=s.llm_temperature,
        rate_limiter=_rate_limiter,
        max_retries=3,
    )
