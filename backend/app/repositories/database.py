"""SQLite engine and session factory for the memory store."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base

DEFAULT_DB_FILENAME = "memory.db"


def get_database_url(memory_store_path: Path) -> str:
    """Build a SQLite URL for the given memory store directory."""
    memory_store_path.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{memory_store_path / DEFAULT_DB_FILENAME}"


def create_engine_for_path(memory_store_path: Path) -> Engine:
    """Create a SQLAlchemy engine bound to the local memory store."""
    return create_engine(
        get_database_url(memory_store_path),
        connect_args={"check_same_thread": False},
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a configured session factory for the given engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_schema(engine: Engine) -> None:
    """Create all relational tables if they do not yet exist."""
    Base.metadata.create_all(engine)


def session_scope(
    session_factory: sessionmaker[Session],
) -> Generator[Session]:
    """Yield a transactional session that commits on success."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
