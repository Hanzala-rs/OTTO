"""
Redis-backed message history per session.
Stores the last N messages so the LLM has conversation context.
"""
from __future__ import annotations
import json
from functools import lru_cache

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from memory.session_store import get_redis
from config.settings import get_settings

MAX_MESSAGES = 6    # keep last 6 turns


class RedisMessageHistory:
    def __init__(self, session_id: str) -> None:
        self.key = f"history:{session_id}"
        self.r = get_redis()
        self.ttl = get_settings().session_ttl_seconds

    def get_messages(self) -> list[BaseMessage]:
        raw = self.r.lrange(self.key, 0, -1)
        messages = []
        for item in raw:
            data = json.loads(item)
            if data["type"] == "human":
                messages.append(HumanMessage(content=data["content"]))
            else:
                messages.append(AIMessage(content=data["content"]))
        return messages

    def add_message(self, message: BaseMessage) -> None:
        payload = json.dumps({"type": message.type, "content": message.content})
        self.r.rpush(self.key, payload)
        self.r.ltrim(self.key, -MAX_MESSAGES * 2, -1)
        self.r.expire(self.key, self.ttl)

    def clear(self) -> None:
        self.r.delete(self.key)


def get_history(session_id: str) -> RedisMessageHistory:
    return RedisMessageHistory(session_id)
