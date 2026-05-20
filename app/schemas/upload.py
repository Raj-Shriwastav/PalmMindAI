from pydantic import BaseModel, UUID4
from typing import Dict, Any


class UploadResponse(BaseModel):
    """Pydantic V2 schema defining the contract for file ingestion responses."""

    status: str
    message: str
    document_id: UUID4
    strategy_used: str
    embedding_model: str
    chunks_count: int
    metadata: Dict[str, Any]
