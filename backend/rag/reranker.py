"""Lightweight cross-encoder reranker — ms-marco-MiniLM-L-6-v2 (~22MB, fast CPU)."""
from __future__ import annotations
from functools import lru_cache
from typing import List

from sentence_transformers import CrossEncoder
from loguru import logger

from config.settings import get_settings

TOP_N = 5


class Reranker:
    def __init__(self) -> None:
        model = get_settings().reranker_model
        logger.info(f"Loading reranker {model}...")
        self.model = CrossEncoder(model)
        logger.info("Reranker ready.")

    def rerank(self, query: str, chunks: List[dict]) -> List[dict]:
        if not chunks:
            return []

        pairs = [[query, c["text"]] for c in chunks]
        scores = self.model.predict(pairs).tolist()

        scored = sorted(
            zip(scores, chunks),
            key=lambda x: x[0],
            reverse=True,
        )
        return [chunk for _, chunk in scored[:TOP_N]]


@lru_cache
def get_reranker() -> Reranker:
    return Reranker()
