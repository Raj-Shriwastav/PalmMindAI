from sqlalchemy.orm import Session

class BaseRepository:
    """Base repository layer providing access to database transactions."""
    def __init__(self, db: Session):
        self.db = db
