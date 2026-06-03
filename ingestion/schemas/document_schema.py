from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentEvent(BaseModel):
    """CDC event payload from Debezium."""
    op: str                     # c=create, u=update, d=delete, r=read/snapshot
    doc_id: int = None
    id: Optional[int] = None    # Debezium sends 'id', mapped to doc_id

    def __init__(self, **data):
        if 'id' in data and 'doc_id' not in data:
            data['doc_id'] = data['id']
        super().__init__(**data)
    title: str
    content: str
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChunkPayload(BaseModel):
    """Qdrant point payload stored alongside each vector."""
    doc_id: int
    chunk_id: str
    parent_id: Optional[str]    # None for parent chunks
    chunk_type: str             # "parent" | "child"
    lang: str                   # "en" | "ur"
    source: Optional[str]
    doc_hash: str
    text: str
