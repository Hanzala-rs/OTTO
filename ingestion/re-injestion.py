"""
reingest_file.py — Targeted single-file re-ingestion.

Use this when a specific file has changed and you want to update
only that file's vectors in Qdrant WITHOUT re-running the full pipeline.

Flow:
    1. Delete existing PostgreSQL row(s) for this file  (by source path)
    2. Re-read the file
    3. Insert fresh row → Debezium CDC picks it up → Qdrant updated automatically

Usage:
    python reingest_file.py <file_path>

Examples:
    python reingest_file.py ./datasets/products/pricing/enterprise.md
    python reingest_file.py ./datasets/manual.pdf
"""

import os
import sys
from pathlib import Path
from datetime import datetime

import psycopg2
from loguru import logger

# ── Reuse existing readers from your ingestion package ────────────────────────
from ingestion.readers.pdf_reader  import read_pdf
from ingestion.readers.docx_reader import read_docx
from ingestion.readers.text_reader import read_text

# ─────────────────────────────────────────────────────────────────────────────

SUPPORTED = {".pdf", ".docx", ".doc", ".txt", ".md"}

POSTGRES_URL = os.getenv(
    "POSTGRES_URL",
    "postgresql://otto_user:changeme@localhost:5432/otto",
)


# ── File reader (same dispatch as ingestion.py) ───────────────────────────────

def read_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return read_pdf(str(path))
    if ext in (".docx", ".doc"):
        return read_docx(str(path))
    if ext in (".txt", ".md"):
        return read_text(str(path))
    raise ValueError(f"Unsupported file type: {ext}")


# ── PostgreSQL operations ─────────────────────────────────────────────────────

DELETE_SQL = """
    DELETE FROM documents
    WHERE source = %s
    RETURNING id, title;
"""

INSERT_SQL = """
    INSERT INTO documents (title, content, source, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id;
"""

def delete_existing(conn, source: str) -> list[int]:
    """Delete all rows for this source path. Returns list of deleted IDs."""
    with conn.cursor() as cur:
        cur.execute(DELETE_SQL, (source,))
        rows = cur.fetchall()
        conn.commit()
    return rows  # [(id, title), ...]


def insert_document(conn, title: str, content: str, source: str) -> int:
    """Insert fresh document row. Debezium will stream it to Qdrant."""
    now = datetime.utcnow()
    with conn.cursor() as cur:
        cur.execute(INSERT_SQL, (title, content, source, now, now))
        row = cur.fetchone()
        conn.commit()
    return row[0]


# ── Main ──────────────────────────────────────────────────────────────────────

def reingest(file_path_str: str):
    file_path = Path(file_path_str)

    # ── Validate ──────────────────────────────────────────────────────────────
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)

    if not file_path.is_file():
        logger.error(f"Path is a directory. Use ingestion.py for full folder ingestion.")
        sys.exit(1)

    if file_path.suffix.lower() not in SUPPORTED:
        logger.error(f"Unsupported file type: {file_path.suffix}. Supported: {SUPPORTED}")
        sys.exit(1)

    # Normalize to the same format ingestion.py uses: str(file_path)
    source = str(file_path)

    logger.info(f"Target file : {file_path.name}")
    logger.info(f"Source path : {source}")

    # ── Connect ───────────────────────────────────────────────────────────────
    conn = psycopg2.connect(POSTGRES_URL)
    logger.info("Connected to PostgreSQL")

    # ── Step 1: Delete old rows ───────────────────────────────────────────────
    deleted = delete_existing(conn, source)
    if deleted:
        logger.info(f"[1/3] Deleted {len(deleted)} existing row(s) → IDs: {[r[0] for r in deleted]}")
        logger.info("      Debezium DELETE event will remove old vectors from Qdrant.")
    else:
        logger.info(f"[1/3] No existing rows found for this path (fresh insert).")

    # ── Step 2: Read file ─────────────────────────────────────────────────────
    logger.info(f"[2/3] Reading file...")
    content = read_file(file_path)

    if not content.strip():
        logger.error("File content is empty. Aborting.")
        conn.close()
        sys.exit(1)

    logger.info(f"      Read {len(content)} characters.")

    # ── Step 3: Insert fresh row ──────────────────────────────────────────────
    new_id = insert_document(
        conn,
        title=file_path.stem,
        content=content,
        source=source,
    )
    logger.success(f"[3/3] Inserted → doc_id={new_id}")
    logger.success(f"      Debezium INSERT event will push new vectors to Qdrant.")

    conn.close()
    logger.success(
        f"\nDone. '{file_path.name}' re-ingested successfully.\n"
        f"All other documents in Qdrant remain untouched."
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python reingest_file.py <file_path>")
        print("Example: python reingest_file.py ./datasets/products/pricing/enterprise.md")
        sys.exit(1)

    reingest(sys.argv[1])