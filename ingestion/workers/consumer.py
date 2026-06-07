"""
Redpanda consumer — reads CDC events from the raw-documents topic,
runs the full ingestion pipeline for each event.
"""
import json
import os
from kafka import KafkaConsumer
from loguru import logger

from workers.language_detector import detect_language
from workers.chunker import ParentChildChunker
from workers.embedder import Embedder
from workers.qdrant_upserter import QdrantUpserter
from schemas.document_schema import DocumentEvent

BROKERS = os.getenv("REDPANDA_BROKERS", "localhost:9092")
TOPIC = os.getenv("REDPANDA_TOPIC_RAW", "raw-documents")
GROUP_ID = os.getenv("REDPANDA_GROUP_ID", "ingestion-workers")

chunker = ParentChildChunker()
embedder = Embedder()
upserter = QdrantUpserter()


def process_event(event: DocumentEvent) -> None:
    if event.op == "d":
        upserter.delete_by_doc_id(event.doc_id)
        logger.info(f"Deleted vectors for doc_id={event.doc_id}")
        return

    if event.op == "u":
        upserter.delete_by_doc_id(event.doc_id)
        logger.info(f"Cleared stale vectors for updated doc_id={event.doc_id}")

    lang = detect_language(event.content)
    chunks = chunker.chunk(
        doc_id=event.doc_id,
        content=event.content,
        lang=lang,
        source=event.source,
    )

    vectors = embedder.embed_chunks(chunks)
    upserter.upsert(vectors)
    logger.info(
        f"Ingested doc_id={event.doc_id} lang={lang} "
        f"chunks={len(chunks)} op={event.op}"
    )


def main() -> None:
    logger.info(f"Connecting to Redpanda at {BROKERS}, topic={TOPIC}")
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BROKERS,
        group_id=GROUP_ID,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    logger.info("Consumer ready, waiting for messages...")
    for msg in consumer:
        try:
            payload = msg.value
            # Debezium wraps the row in payload.after (create/update) or payload.before (delete)
            op = payload.get("op", "c")
            row = payload.get("after") or payload.get("before") or {}
            if not row:
                continue

            event = DocumentEvent(op=op, **row)
            process_event(event)
        except Exception as exc:
            logger.error(f"Failed to process message: {exc}")


if __name__ == "__main__":
    main()
