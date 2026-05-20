from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.document import Document, DocumentChunk
from typing import List, Optional
import uuid

class DocumentRepository(BaseRepository):
    """Repository handling read/write database actions for Documents and DocumentChunks."""

    def create_document(self, filename: str, chunk_strategy: str, embedding_model: str) -> Document:
        """Create and commit a new Document metadata registry entry."""
        doc = Document(
            filename=filename,
            chunk_strategy=chunk_strategy,
            embedding_model=embedding_model
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def create_document_chunk(self, document_id: uuid.UUID, qdrant_uuid: str, chunk_index: int, text_content: str) -> DocumentChunk:
        """Create and commit a mapping chunk entry linked to a Qdrant vector UUID."""
        chunk = DocumentChunk(
            document_id=document_id,
            qdrant_uuid=qdrant_uuid,
            chunk_index=chunk_index,
            text_content=text_content
        )
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk

    def get_document_by_id(self, doc_id: uuid.UUID) -> Optional[Document]:
        """Fetch overall Document metadata by database primary UUID key."""
        return self.db.query(Document).filter(Document.id == doc_id).first()

    def get_chunk_by_qdrant_uuid(self, q_uuid: str) -> Optional[DocumentChunk]:
        """Locate exact text content corresponding to a vector match from Qdrant."""
        return self.db.query(DocumentChunk).filter(DocumentChunk.qdrant_uuid == q_uuid).first()
