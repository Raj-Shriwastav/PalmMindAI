import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from qdrant_client.http import models as qd_models
from fastembed import TextEmbedding

from app.core.config import settings
from app.core.qdrant import client as qdrant_client
from app.repositories.document import DocumentRepository
from app.utils.pdf import extract_text_from_bytes
from app.utils.chunking import RecursiveCharacterChunker, SemanticChunker

# Initialize TextEmbedding once at module level to reuse weights and save memory
embedder = TextEmbedding(model_name=settings.EMBEDDING_MODEL_NAME)


class IngestionService:
    """Orchestrates RAG ingestion pipelines, converting documents to metadata database entries and vector keys."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = DocumentRepository(db)

    def ingest_document(
        self,
        filename: str,
        file_bytes: bytes,
        chunk_strategy: str = "recursive",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        similarity_percentile: float = 90.0,
    ) -> Dict[str, Any]:
        """Runs the multi-stage ingestion pipeline.

        Steps:
          1. Extract raw text.
          2. Chunk text hierarchically or semantically.
          3. Save document entry to PostgreSQL.
          4. Embed chunks using Snowflake Arctic.
          5. Batch-upsert vectors to Qdrant.
          6. Commit chunk mapping details to PostgreSQL.
        """
        # 1. Extract plain text
        raw_text = extract_text_from_bytes(file_bytes, filename)

        # 2. Select and run chunking strategy
        strategy = chunk_strategy.lower().strip()
        if strategy == "semantic":
            # Semantic chunking relies on FastEmbed under the hood
            chunker = SemanticChunker(
                model_name=settings.EMBEDDING_MODEL_NAME,
                similarity_percentile=similarity_percentile,
            )
        else:
            # Fallback/Default to Recursive character chunker
            chunker = RecursiveCharacterChunker(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )

        chunks = chunker.chunk_text(raw_text)
        if not chunks:
            raise ValueError(f"Document chunking produced zero segments.")

        # 3. Create document master record in PostgreSQL
        document = self.repo.create_document(
            filename=filename,
            chunk_strategy=strategy,
            embedding_model=settings.EMBEDDING_MODEL_NAME,
        )

        # 4. Generate text embeddings in a single optimized batch
        embeddings = list(embedder.embed(chunks))

        # 5. Prepare batch points for Qdrant and repository entries for PostgreSQL
        points = []
        db_chunks = []

        for idx, chunk_text in enumerate(chunks):
            # Generate stable chunk identification UUIDs
            chunk_uuid = str(uuid.uuid4())
            vector = embeddings[idx].tolist()

            # Map Qdrant structures
            points.append(
                qd_models.PointStruct(
                    id=chunk_uuid,
                    vector=vector,
                    payload={"document_id": str(document.id), "chunk_index": idx},
                )
            )

            # Prepare SQL structures (Postgres acts as single source of truth for raw text)
            db_chunks.append((chunk_uuid, idx, chunk_text))

        # 6. Perform batch vector upsert in Qdrant (very high performance)
        qdrant_client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME, points=points
        )

        # 7. Commit metadata structures to PostgreSQL in a single transaction
        for q_uuid, idx, text in db_chunks:
            self.repo.create_document_chunk(
                document_id=document.id,
                qdrant_uuid=q_uuid,
                chunk_index=idx,
                text_content=text,
            )

        return {
            "status": "success",
            "message": f"File '{filename}' ingested successfully.",
            "document_id": document.id,
            "strategy_used": strategy,
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "chunks_count": len(chunks),
            "metadata": {
                "filename": filename,
                "file_size_bytes": len(file_bytes),
                "timestamp": document.created_at.isoformat(),
            },
        }
