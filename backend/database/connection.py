"""
Database connection and session management.
"""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from config import settings
from models.database import Base
import logging

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DATABASE_ECHO,
    future=True
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

async def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    _ensure_runtime_columns()
    logger.info("Database tables created successfully")

async def close_db():
    """Close database connection."""
    engine.dispose()

def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_runtime_columns() -> None:
    """
    Backfill small schema additions for local environments that rely on create_all.

    The project has Alembic migrations, but this app also boots directly against
    an existing local database. These ALTERs keep older local installs working
    without forcing a manual migration step every time a simple nullable column
    is added.
    """
    inspector = inspect(engine)
    if "campaigns" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("campaigns")}
    alter_statements: list[str] = []

    if "primary_status" not in existing_columns:
        alter_statements.append("ALTER TABLE campaigns ADD COLUMN primary_status VARCHAR(64)")
    if "primary_status_reasons" not in existing_columns:
        alter_statements.append("ALTER TABLE campaigns ADD COLUMN primary_status_reasons JSONB")

    if not alter_statements:
        return

    with engine.begin() as connection:
        for statement in alter_statements:
            connection.execute(text(statement))
