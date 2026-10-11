"""
Database connection and session management module using SQLAlchemy 2.x.
Seamlessly supports MySQL (via PyMySQL) and SQLite, with production connection pooling.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import get_settings

settings = get_settings()

connect_args = {}
engine_kwargs = {
    "echo": False,
    "future": True,
}

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # Production connection pool settings for MySQL / PostgreSQL
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,  # Verifies connection liveness before checkout
        "pool_recycle": 3600,    # Recycles connections every hour to avoid MySQL timeouts
    })

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session per request.
    Ensures proper cleanup and rollback on unhandled exceptions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    import app.models  # noqa: F401 - ensure models register in Base.metadata
    Base.metadata.create_all(bind=engine)
