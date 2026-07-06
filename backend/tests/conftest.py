"""Shared pytest fixtures for backend integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.config import AIRLOCK_POLICY_PATH
from app.models import Document, Record
from app.repositories.database import create_engine_for_path, create_session_factory, init_schema
from app.services.dataset_service import DatasetService

VALID_ACCESSION_RECORDS = """[
  {
    "accession_number": "2024.001",
    "title": "Marble Bust of John Miller",
    "date_acquired": "2024-03-12",
    "source": "Miller Estate Donation",
    "confidence": 0.98
  }
]"""

VALID_CURATOR_NOTES = """# Curator Notes

Artifact 2024.001 was donated by the Miller family.

Family correspondence suggests the bust was commissioned
between 1905 and 1908.

Supporting documentation remains incomplete.
"""

VALID_PROPERTY_LEDGER = """Miller Household Property Ledger
1908

Dog: Fido
Breed: Mixed Terrier
Owner: John Miller

Marble Bust commissioned from local sculptor.
"""

VALID_PHOTOGRAPH_CATALOG = """[
  {
    "photo_id": "PHOTO-1908-001",
    "caption": "Miller Family Portrait",
    "estimated_year": 1908,
    "subjects": [
      "John Miller",
      "Mary Miller",
      "Fido"
    ]
  }
]"""


def write_valid_dataset(datasets_path: Path) -> None:
    """Write the canonical reference dataset into a temporary directory."""
    datasets_path.mkdir(parents=True, exist_ok=True)
    files = {
        "accession_records.json": VALID_ACCESSION_RECORDS,
        "curator_notes.md": VALID_CURATOR_NOTES,
        "property_ledger_1908.txt": VALID_PROPERTY_LEDGER,
        "photograph_catalog.json": VALID_PHOTOGRAPH_CATALOG,
    }
    for filename, content in files.items():
        (datasets_path / filename).write_text(content, encoding="utf-8")


@pytest.fixture
def memory_store_path(tmp_path: Path) -> Path:
    """Provide an isolated SQLite memory store directory."""
    path = tmp_path / "memory_store"
    path.mkdir()
    return path


@pytest.fixture
def datasets_path(tmp_path: Path) -> Path:
    """Provide a temporary datasets directory with valid reference assets."""
    path = tmp_path / "datasets"
    write_valid_dataset(path)
    return path


@pytest.fixture
def sovereign_keys_path(tmp_path: Path) -> Path:
    """Provide an isolated directory for Ed25519 signing key material."""
    path = tmp_path / ".sovereign_keys"
    path.mkdir()
    return path


@pytest.fixture
def sovereign_ledger_path(tmp_path: Path) -> Path:
    """Provide an isolated SQLite path for the append-only sovereign ledger."""
    return tmp_path / "sovereign_audit.db"


@pytest.fixture
def airlock_policy_path() -> Path:
    """Return the repository airlock policy used by integration tests."""
    return AIRLOCK_POLICY_PATH


@pytest.fixture
def session_factory(memory_store_path: Path) -> sessionmaker[Session]:
    """Create a session factory backed by an initialized in-memory schema."""
    engine = create_engine_for_path(memory_store_path)
    init_schema(engine)
    return create_session_factory(engine)


@pytest.fixture
def dataset_service(
    datasets_path: Path,
    session_factory: sessionmaker[Session],
) -> DatasetService:
    """Return a dataset service bound to isolated test paths."""
    return DatasetService(datasets_path, session_factory)


@pytest.fixture
def count_documents(session_factory: sessionmaker[Session]):
    """Return a helper that counts persisted documents."""

    def _count() -> int:
        with session_factory() as session:
            return len(session.scalars(select(Document)).all())

    return _count


@pytest.fixture
def count_records(session_factory: sessionmaker[Session]):
    """Return a helper that counts persisted records."""

    def _count() -> int:
        with session_factory() as session:
            return len(session.scalars(select(Record)).all())

    return _count
