"""
Parent-Child chunker.

Parent chunks (~512 tokens) are stored in Qdrant for LLM context.
Child chunks (~128 tokens) are stored for retrieval.
Every child carries a parent_id so the reranker can fetch the full parent.
"""
import hashlib
import uuid
from typing import List

try:
    import urduhack
    urduhack.download()
    from urduhack.tokenization import sentence_tokenizer as urdu_sent_tokenize
    URDUHACK_AVAILABLE = True
except Exception:
    URDUHACK_AVAILABLE = False

from schemas.document_schema import ChunkPayload

PARENT_TOKEN_LIMIT = 512
CHILD_TOKEN_LIMIT = 128
WORDS_PER_TOKEN = 0.75   # rough approximation


def _word_split(text: str) -> List[str]:
    return text.split()


def _chunk_words(words: List[str], limit: int) -> List[str]:
    """Split a word list into chunks of ~limit tokens."""
    size = int(limit / WORDS_PER_TOKEN)
    return [
        " ".join(words[i : i + size])
        for i in range(0, len(words), size)
        if words[i : i + size]
    ]


def _sentence_split(text: str, lang: str) -> List[str]:
    if lang == "ur" and URDUHACK_AVAILABLE:
        try:
            return urdu_sent_tokenize(text)
        except Exception:
            pass
    # Fallback: split on common sentence-ending punctuation
    import re
    parts = re.split(r"(?<=[.!?۔])\s+", text)
    return [p.strip() for p in parts if p.strip()]


class ParentChildChunker:
    def chunk(
        self,
        doc_id: int,
        content: str,
        lang: str,
        source: str | None,
    ) -> List[ChunkPayload]:
        doc_hash = hashlib.md5(content.encode()).hexdigest()
        chunks: List[ChunkPayload] = []

        sentences = _sentence_split(content, lang)
        words = _word_split(content)

        # Build parent chunks first
        parent_word_chunks = _chunk_words(words, PARENT_TOKEN_LIMIT)
        for p_text in parent_word_chunks:
            parent_id = str(uuid.uuid4())
            parent_chunk = ChunkPayload(
                doc_id=doc_id,
                chunk_id=parent_id,
                parent_id=None,
                chunk_type="parent",
                lang=lang,
                source=source,
                doc_hash=doc_hash,
                text=p_text,
            )
            chunks.append(parent_chunk)

            # Build child chunks from within this parent
            child_words = _word_split(p_text)
            child_word_chunks = _chunk_words(child_words, CHILD_TOKEN_LIMIT)
            for c_text in child_word_chunks:
                child_chunk = ChunkPayload(
                    doc_id=doc_id,
                    chunk_id=str(uuid.uuid4()),
                    parent_id=parent_id,
                    chunk_type="child",
                    lang=lang,
                    source=source,
                    doc_hash=doc_hash,
                    text=c_text,
                )
                chunks.append(child_chunk)

        return chunks
