"""Lightweight cross-encoder reranker — ms-marco-MiniLM-L-6-v2 (~22MB, fast CPU)."""
from __future__ import annotations
from functools import lru_cache
from typing import List

from sentence_transformers import CrossEncoder
from loguru import logger

from config.settings import get_settings

TOP_N = 7   # distinct parents passed to the LLM (eval: 7 kept the answer for 21/23 vs 19/23 at 5)
SCORE_THRESHOLD = -5.0  # cross-encoder raw logit; below this = not relevant


class Reranker:
    def __init__(self) -> None:
        model = get_settings().reranker_model
        logger.info(f"Loading reranker {model}...")
        # 256 tokens: 2.3x faster than 512 on CPU with equal recall in eval
        self.model = CrossEncoder(model, max_length=256)
        logger.info("Reranker ready.")

    def rerank(self, query: str, chunks: List[dict]) -> List[dict]:
        if not chunks:
            return []

        # Long keyword hits come split into passages (set by the retriever) so a match
        # deep in the chunk isn't cut off by max_length; a chunk scores as its best
        # passage, kept as rerank_text so the LLM context is centred on it
        texts = [c.get("passages") or [c["text"]] for c in chunks]
        pairs = [[query, t] for ts in texts for t in ts]
        flat = iter(self.model.predict(pairs).tolist())
        scored = []
        for c, ts in zip(chunks, texts):
            s, best = max(zip([next(flat) for _ in ts], ts), key=lambda x: x[0])
            scored.append((s, {**c, "rerank_text": best} if c.get("passages") else c))
        scored.sort(key=lambda x: x[0], reverse=True)
        # Drop irrelevant chunks; keep TOP_N distinct parents (children of the same
        # parent would otherwise put duplicate text in the LLM context)
        result, seen = [], set()
        for s, c in scored:
            key = c.get("parent_id") or c.get("chunk_id")
            if s < SCORE_THRESHOLD or key in seen:
                continue
            seen.add(key)
            result.append(c)
            if len(result) == TOP_N:
                break
        return result


@lru_cache
def get_reranker() -> Reranker:
    return Reranker()
