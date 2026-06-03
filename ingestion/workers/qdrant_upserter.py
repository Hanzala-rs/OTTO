"""Upserts embedded chunks into Qdrant with deduplication via doc_hash."""
import os
from typing import List, Tuple
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)
from loguru import logger

from schemas.document_schema import ChunkPayload

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION = os.getenv("QDRANT_COLLECTION", "documents")
VECTOR_DIM = int(os.getenv("VECTOR_DIM", "384"))


class QdrantUpserter:
    def __init__(self) -> None:
        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        existing = [c.name for c in self.client.get_collections().collections]
        if COLLECTION not in existing:
            self.client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection '{COLLECTION}'")

    def _hash_exists(self, doc_hash: str) -> bool:
        """Check if any point with this doc_hash already exists (deduplication)."""
        results = self.client.scroll(
            collection_name=COLLECTION,
            scroll_filter=Filter(
                must=[FieldCondition(key="doc_hash", match=MatchValue(value=doc_hash))]
            ),
            limit=1,
        )
        return len(results[0]) > 0

    def upsert(self, chunks_with_vectors: List[Tuple[ChunkPayload, List[float]]]) -> None:
        if not chunks_with_vectors:
            return

        # Deduplication: skip if doc_hash already present
        sample_hash = chunks_with_vectors[0][0].doc_hash
        if self._hash_exists(sample_hash):
            logger.info(f"Skipping duplicate doc_hash={sample_hash}")
            return

        points = [
            PointStruct(
                id=chunk.chunk_id,
                vector=vector,
                payload=chunk.model_dump(exclude={"text"}),
            )
            for chunk, vector in chunks_with_vectors
        ]

        self.client.upsert(collection_name=COLLECTION, points=points)
        logger.info(f"Upserted {len(points)} points to Qdrant")

    def delete_by_doc_id(self, doc_id: int) -> None:
        self.client.delete(
            collection_name=COLLECTION,
            points_selector=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            ),
        )
