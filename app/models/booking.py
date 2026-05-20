import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.core.database import Base


class Booking(Base):
    """SQLAlchemy model for transactional interview bookings scheduled by the agent."""

    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, index=True)
    date = Column(
        String(30), nullable=False
    )  # Store parsed date string (e.g. "2026-06-10")
    time = Column(
        String(20), nullable=False
    )  # Store parsed time string (e.g. "11:00 AM")
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
