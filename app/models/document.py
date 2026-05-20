import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Document(Base):
    """SQLAlchemy model for document files (metadata registration)."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    chunk_strategy = Column(String(50), nullable=False)  # recursive vs semantic
    embedding_model = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    """SQLAlchemy model mapping text chunks to original document and Qdrant vector UUIDs."""
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    qdrant_uuid = Column(String(50), nullable=False, index=True)  # Qdrant upsert vector key
    chunk_index = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=False)

    document = relationship("Document", back_populates="chunks")
