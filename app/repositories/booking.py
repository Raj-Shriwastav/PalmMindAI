from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.booking import Booking
from typing import List, Optional
import uuid

class BookingRepository(BaseRepository):
    """Repository handling read/write database actions for interview Bookings."""

    def create_booking(self, full_name: str, email: str, date: str, time: str) -> Booking:
        """Create and commit a new transactional interview booking."""
        booking = Booking(
            full_name=full_name,
            email=email,
            date=date,
            time=time
        )
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def get_booking_by_id(self, booking_id: uuid.UUID) -> Optional[Booking]:
        """Fetch a specific Booking by UUID key."""
        return self.db.query(Booking).filter(Booking.id == booking_id).first()

    def get_bookings_by_email(self, email: str) -> List[Booking]:
        """Fetch all Bookings scheduled under a target email address."""
        return self.db.query(Booking).filter(Booking.email == email).all()
