"""
File Ingestor — reads files from a folder/path and inserts them into PostgreSQL.
Debezium CDC picks up the INSERT automatically and sends to Qdrant.

Supported formats: .pdf  .docx  .doc  .txt  .md
"""
import os
import sys
from pathlib import Path
from datetime import datetime

import psycopg2
from loguru import logger

try:
    from ingestion.readers.pdf_reader  import read_pdf
    from ingestion.readers.docx_reader import read_docx
    from ingestion.readers.text_reader import read_text
except ImportError:
    from readers.pdf_reader  import read_pdf
    from readers.docx_reader import read_docx
    from readers.text_reader import read_text

# ── Set your path here ────────────────────────────────────────────────────────
# Folder:      r"C:\Users\you\Documents\my_docs"
# Single file: r"C:\Users\you\Documents\report.pdf"
INGEST_PATH = r"./datasets/bahl_kb_2"
# ─────────────────────────────────────────────────────────────────────────────

SUPPORTED = {".pdf", ".docx", ".doc", ".txt", ".md"}

POSTGRES_URL = os.getenv(
    "POSTGRES_URL",
    "postgresql://otto_user:changeme@localhost:5432/otto",
)


# ── File reader dispatch ───────────────────────────────────────────────────────

def read_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return read_pdf(str(path))
    if ext in (".docx", ".doc"):
        return read_docx(str(path))
    if ext in (".txt", ".md"):
        return read_text(str(path))
    raise ValueError(f"Unsupported file type: {ext}")


# ── Collect files from path ────────────────────────────────────────────────────

def collect_files(target: str) -> list[Path]:
    p = Path(target)
    if not p.exists():
        logger.error(f"Path does not exist: {target}")
        sys.exit(1)

    if p.is_file():
        if p.suffix.lower() not in SUPPORTED:
            logger.error(f"Unsupported file type: {p.suffix}")
            sys.exit(1)
        return [p]

    # It's a folder — collect all supported files recursively
    files = [f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in SUPPORTED]
    if not files:
        logger.warning(f"No supported files found in {target}")
    return sorted(files)


# ── Insert into PostgreSQL ─────────────────────────────────────────────────────

INSERT_SQL = """
    INSERT INTO documents (title, content, source, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT DO NOTHING
    RETURNING id;
"""

def insert_document(conn, title: str, content: str, source: str) -> int | None:
    now = datetime.utcnow()
    with conn.cursor() as cur:
        cur.execute(INSERT_SQL, (title, content, source, now, now))
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    files = collect_files(INGEST_PATH)
    logger.info(f"Found {len(files)} file(s) to ingest")

    conn = psycopg2.connect(POSTGRES_URL)
    logger.info("Connected to PostgreSQL")

    success, skipped, failed = 0, 0, 0

    for file_path in files:
        logger.info(f"Processing: {file_path.name}")
        try:
            content = read_file(file_path)
            if not content.strip():
                logger.warning(f"  Skipped (empty content): {file_path.name}")
                skipped += 1
                continue

            doc_id = insert_document(
                conn,
                title=file_path.stem,
                content=content,
                source=str(file_path),
            )

            if doc_id:
                logger.success(f"  Inserted → doc_id={doc_id}  ({len(content)} chars)")
                success += 1
            else:
                logger.warning(f"  Skipped (already exists): {file_path.name}")
                skipped += 1

        except Exception as exc:
            logger.error(f"  Failed: {file_path.name} → {exc}")
            failed += 1

    conn.close()

    logger.info(
        f"\nDone. inserted={success}  skipped={skipped}  failed={failed}\n"
        f"Debezium will now stream these to Qdrant automatically."
    )


if __name__ == "__main__":
    main()
