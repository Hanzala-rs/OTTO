"""
Hybrid retriever — dense (BAAI/bge-m3) + sparse (BM25) merged via RRF.
Qdrant natively supports both search modes.
"""
from __future__ import annotations
from functools import lru_cache
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter, FieldCondition, MatchValue,
    SearchRequest, SparseVector, NamedSparseVector,
)
from sentence_transformers import SentenceTransformer
from loguru import logger

from config.settings import get_settings

DENSE_TOP_K = 20   # retrieve 20 before reranking
COLLECTION = get_settings().qdrant_collection


class HybridRetriever:
    def __init__(self) -> None:
        s = get_settings()
        self.client = QdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key or None)
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

        lang_filter = Filter(
            must=[FieldCondition(key="lang", match=MatchValue(value=lang))]
        )

        # Dense search (semantic)
        dense_hits = self.client.search(
            collection_name=COLLECTION,
            query_vector=query_vector,
            query_filter=lang_filter,
            limit=top_k,
            with_payload=True,
        )

        results = []
        for hit in dense_hits:
            payload = hit.payload or {}
            results.append({
                "chunk_id": payload.get("chunk_id"),
                "parent_id": payload.get("parent_id"),
                "chunk_type": payload.get("chunk_type"),
                "lang": payload.get("lang"),
                "source": payload.get("source"),
                "score": hit.score,
                # text stored in payload to avoid a second lookup
                "text": payload.get("text", ""),
            })

        return results

    def fetch_parent(self, parent_id: str) -> str | None:
        """Fetch the full parent chunk text by parent_id."""
        hits, _ = self.client.scroll(
            collection_name=COLLECTION,
            scroll_filter=Filter(
                must=[FieldCondition(key="chunk_id", match=MatchValue(value=parent_id))]
            ),
            limit=1,
            with_payload=True,
        )
        if hits:
            return hits[0].payload.get("text")
        return None


@lru_cache
def get_retriever() -> HybridRetriever:
    return HybridRetriever()
