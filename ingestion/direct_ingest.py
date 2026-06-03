"""Direct ingestion — reads from PostgreSQL, chunks, embeds, upserts to Qdrant. No Kafka needed."""
import os
import psycopg2
from loguru import logger

from workers.language_detector import detect_language
from workers.chunker import ParentChildChunker
from workers.embedder import Embedder
from workers.qdrant_upserter import QdrantUpserter
from schemas.document_schema import DocumentEvent

POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://otto_user:changeme0@postgres:5432/otto")

def main():
    conn = psycopg2.connect(POSTGRES_URL)
    logger.info("Connected to PostgreSQL")

    chunker = ParentChildChunker()
    embedder = Embedder()
    upserter = QdrantUpserter()

    with conn.cursor() as cur:
        cur.execute("SELECT id, title, content, source FROM documents ORDER BY id")
        rows = cur.fetchall()

    logger.info(f"Found {len(rows)} documents")

    for doc_id, title, content, source in rows:
        try:
            lang = detect_language(content)
            chunks = chunker.chunk(doc_id=doc_id, content=content, lang=lang, source=source)
            vectors = embedder.embed_chunks(chunks)
            upserter.upsert(vectors)
            logger.success(f"doc_id={doc_id} title={title[:40]} lang={lang} chunks={len(chunks)}")
        except Exception as e:
            logger.error(f"doc_id={doc_id} failed: {e}")

    conn.close()
    logger.info("Done.")

if __name__ == "__main__":
    main()
