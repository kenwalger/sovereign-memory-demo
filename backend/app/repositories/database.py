"""SQLite engine and session factory for the memory store."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base

DEFAULT_DB_FILENAME = "memory.db"
"""str: SQLite database filename persisted inside the memory store directory."""


def get_database_url(memory_store_path: Path) -> str:
    """Build a SQLite URL for the given memory store directory.

    Creates the memory store directory if it does not already exist.

    :param Path memory_store_path: Directory where the SQLite database file
        is stored.
    :returns: SQLAlchemy-compatible SQLite connection URL.
    :rtype: str
    """
    memory_store_path.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{memory_store_path / DEFAULT_DB_FILENAME}"


def create_engine_for_path(memory_store_path: Path) -> Engine:
    """Create a SQLAlchemy engine bound to the local memory store.

    :param Path memory_store_path: Directory containing the SQLite database.
    :returns: Configured SQLAlchemy engine with thread-safe SQLite settings.
    :rtype: Engine
    """
    return create_engine(
        get_database_url(memory_store_path),
        connect_args={"check_same_thread": False},
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a configured session factory for the given engine.

    :param Engine engine: SQLAlchemy engine bound to the memory store.
    :returns: Session factory with autoflush and autocommit disabled.
    :rtype: sessionmaker[Session]
    """
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_schema(engine: Engine) -> None:
    """Create all relational tables if they do not yet exist.

    :param Engine engine: SQLAlchemy engine used to execute DDL statements.
    :returns: None
    :rtype: None
    """
    Base.metadata.create_all(engine)


def session_scope(
    session_factory: sessionmaker[Session],
) -> Generator[Session]:
    """Yield a transactional session that commits on success.

    Rolls back the transaction and re-raises on any exception before closing
    the session in a ``finally`` block.

    :param sessionmaker[Session] session_factory: Factory used to create
        database sessions.
    :yields: Active SQLAlchemy session within a transaction boundary.
    :rtype: Session
    :raises Exception: Re-raises any exception raised during the yielded block
        after rolling back the transaction.
    """
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
