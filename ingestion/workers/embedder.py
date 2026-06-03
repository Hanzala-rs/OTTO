"""BAAI/bge-m3 multilingual embedder."""
import os
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from loguru import logger

from schemas.document_schema import ChunkPayload

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")


class Embedder:
    def __init__(self) -> None:
        logger.info(f"Loading embedding model {MODEL_NAME}...")
        self.model = SentenceTransformer(MODEL_NAME)
        self.dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding model ready. Dimension: {self.dim}")

    def embed_chunks(
        self, chunks: List[ChunkPayload]
    ) -> List[Tuple[ChunkPayload, List[float]]]:
        texts = [c.text for c in chunks]
        # Only embed child chunks for retrieval; parent chunks need vectors too
        # for potential parent-level search
        vectors = self.model.encode(texts, normalize_embeddings=True).tolist()
        return list(zip(chunks, vectors))
