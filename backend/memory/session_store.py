"""Redis-backed session store with TTL."""
from __future__ import annotations
from functools import lru_cache

import redis
from config.settings import get_settings


@lru_cache
def get_redis() -> redis.Redis:
    return redis.from_url(get_settings().redis_url, decode_responses=True)


def get_session(session_id: str) -> dict:
    r = get_redis()
    raw = r.hgetall(f"session:{session_id}")
    return raw or {}


def set_session(session_id: str, data: dict) -> None:
    r = get_redis()
    ttl = get_settings().session_ttl_seconds
    key = f"session:{session_id}"
    r.hset(key, mapping=data)
    r.expire(key, ttl)


def delete_session(session_id: str) -> None:
    get_redis().delete(f"session:{session_id}")
