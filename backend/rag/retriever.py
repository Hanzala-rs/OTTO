"""
Hybrid retriever — dense (BAAI/bge-m3) + sparse (BM25) merged via RRF.
Qdrant natively supports both search modes.
"""
from __future__ import annotations
from functools import lru_cache
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter, FieldCondition, MatchAny, MatchText, PayloadSchemaType,
    TextIndexParams, TokenizerType,
    SearchRequest, SparseVector, NamedSparseVector,
)
from sentence_transformers import SentenceTransformer
from loguru import logger

from config.settings import get_settings

DENSE_TOP_K = 40   # wide candidate pool; reranker narrows it down
COLLECTION = get_settings().qdrant_collection
PASSAGE_CHARS = 800   # reranker passage size for long keyword hits (~max_length tokens)
PASSAGE_STEP = 600    # overlap so an answer isn't split across two passages


def _passages(text: str) -> List[str]:
    """Overlapping passages of a long chunk, for the reranker to pick the relevant one."""
    return [text[i: i + PASSAGE_CHARS] for i in range(0, max(1, len(text) - PASSAGE_CHARS + PASSAGE_STEP), PASSAGE_STEP)]


class HybridRetriever:
    def __init__(self) -> None:
        s = get_settings()
        self.client = QdrantClient(
            url=s.qdrant_url, api_key=s.qdrant_api_key or None, timeout=s.qdrant_timeout
        )
        try:
            # Full-text index for the keyword fallback (no-op if it already exists)
            self.client.create_payload_index(
                collection_name=COLLECTION,
                field_name="text",
                field_schema=TextIndexParams(
                    type="text", tokenizer=TokenizerType.WORD, lowercase=True
                ),
            )
        except Exception as exc:
            logger.warning(f"Could not create text payload index: {exc}")
        try:
            # Keyword index for parent lookups by chunk_id (no-op if it already exists)
            self.client.create_payload_index(
                collection_name=COLLECTION,
                field_name="chunk_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
        except Exception as exc:
            logger.warning(f"Could not create chunk_id payload index: {exc}")
        logger.info(f"Loading embedding model {s.embedding_model}...")
        self.embedder = SentenceTransformer(s.embedding_model)
        logger.info("Retriever ready.")

    def retrieve(
        self,
        query: str,
        lang: str,
        top_k: int = DENSE_TOP_K,
    ) -> List[dict]:
        query_vector = self.embedder.encode(query, normalize_embeddings=True).tolist()

        # Dense search (semantic) — no language filter, LLM handles response language
        dense_hits = self.client.search(
            collection_name=COLLECTION,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
        )

        seen_ids = set()
        results = []
        for hit in dense_hits:
            payload = hit.payload or {}
            cid = payload.get("chunk_id")
            seen_ids.add(cid)
            results.append({
                "chunk_id": cid,
                "parent_id": payload.get("parent_id"),
                "chunk_type": payload.get("chunk_type"),
                "lang": payload.get("lang"),
                "source": payload.get("source"),
                "score": hit.score,
                "text": payload.get("text", ""),
            })

        # Keyword search: always supplement dense hits — a high dense score can still
        # miss exact terms buried in long tables; the reranker chooses among both
        _STOPWORDS = {"what", "were", "with", "that", "this", "from", "have",
                      "does", "tell", "about", "bank", "habib", "bahl"}
        # Use only first line — HyDE queries are multi-line
        first_line = query.split('\n')[0]
        keywords = [
            w.lower().strip('.,?!') for w in first_line.split()
            if len(w) > 3 and w.lower() not in _STOPWORDS
        ]
        if keywords:
            candidates = []
            conditions = [FieldCondition(key="text", match=MatchText(text=kw)) for kw in keywords]
            # Chunks containing every keyword first; a "should" scroll returns an
            # arbitrary 50 that often only match the most common keyword
            points, _ = self.client.scroll(
                collection_name=COLLECTION,
                scroll_filter=Filter(must=conditions),
                limit=50,
                with_payload=True,
            )
            if not points:
                points, _ = self.client.scroll(
                    collection_name=COLLECTION,
                    scroll_filter=Filter(should=conditions),
                    limit=50,
                    with_payload=True,
                )
            for p in points:
                cid = (p.payload or {}).get("chunk_id")
                if cid in seen_ids:
                    continue
                text_lower = (p.payload or {}).get("text", "").lower()
                matched = [kw for kw in keywords if kw in text_lower]
                if len(matched) >= max(2, len(keywords) // 2):
                    candidates.append((len(matched), sum(text_lower.count(k) for k in matched), p))
            # Take top-5 by keyword overlap, then by keyword occurrences
            candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
            for _, _, p in candidates[:5]:
                payload = p.payload or {}
                cid = payload.get("chunk_id")
                text = payload.get("text", "")
                results.append({
                    "passages": _passages(text),
                    "chunk_id": cid,
                    "parent_id": payload.get("parent_id"),
                    "chunk_type": payload.get("chunk_type"),
                    "lang": payload.get("lang"),
                    "source": payload.get("source"),
                    "score": 0.6,
                    "text": payload.get("text", ""),
                })
                seen_ids.add(cid)

        return results

    def fetch_parents(self, parent_ids: List[str]) -> dict:
        """Fetch parent chunk texts in one call. Returns {parent_id: text}."""
        if not parent_ids:
            return {}
        hits, _ = self.client.scroll(
            collection_name=COLLECTION,
            scroll_filter=Filter(
                must=[FieldCondition(key="chunk_id", match=MatchAny(any=parent_ids))]
            ),
            limit=len(parent_ids),
            with_payload=True,
        )
        return {
            (h.payload or {}).get("chunk_id"): (h.payload or {}).get("text")
            for h in hits
        }


@lru_cache
def get_retriever() -> HybridRetriever:
    return HybridRetriever()
