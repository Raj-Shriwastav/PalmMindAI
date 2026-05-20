from pydantic import BaseModel, Field
from typing import List, Dict

class ChatRequest(BaseModel):
    """Pydantic V2 schema defining the contract for inbound chat turn requests."""
    session_id: str = Field(..., description="Unique thread/session ID for conversational memory checkpointing")
    message: str = Field(..., description="User message content")

class ChatResponse(BaseModel):
    """Pydantic V2 schema defining the contract for outbound agent chat responses."""
    session_id: str
    response: str
    history: List[Dict[str, str]] = Field(default_factory=list, description="Chronological listing of conversational turns")
