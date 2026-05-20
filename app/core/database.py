from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator
from app.core.config import settings

# Robust SQLAlchemy engine with connection pool parameters for high concurrency
engine = create_engine(
    settings.postgres_url,
    pool_pre_ping=True,  # Disconnect resilience
    pool_size=15,
    max_overflow=25
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator:
    """FastAPI Dependency yielding a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
