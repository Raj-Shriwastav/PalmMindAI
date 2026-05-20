from pydantic import BaseModel, Field, field_validator
from typing import List, Dict
import re


class ChatRequest(BaseModel):
    """Pydantic V2 schema defining the contract for inbound chat turn requests."""

    session_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique thread/session ID for conversational memory checkpointing. Must be 1-100 characters containing only alphanumeric keys, dashes, or underscores.",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User message content. Constrained to 10k characters to prevent Prompt DoS.",
    )

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Enforces alphanumeric keys, dashes, and underscores strictly to prevent namespace injection."""
        v = v.strip()
        if not re.match(r"^[a-zA-Z0-9_\-]+$", v):
            raise ValueError(
                "session_id must only contain alphanumeric characters, dashes, or underscores"
            )
        return v


class ChatResponse(BaseModel):
    """Pydantic V2 schema defining the contract for outbound agent chat responses."""

    session_id: str
    response: str
    history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Chronological listing of conversational turns",
    )
