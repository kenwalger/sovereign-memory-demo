"""Unit tests for fail-fast dataset ingestion."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import inspect, select

from app.models import Document, Record, Receipt
from app.repositories.database import create_engine_for_path, init_schema
from app.services.dataset_service import DatasetService
from app.services.exceptions import (
    DatasetEncodingError,
    DatasetFileNotFoundError,
    DatasetSchemaError,
    DatasetValidationError,
)
from tests.conftest import write_valid_dataset


@pytest.mark.asyncio
async def test_load_valid_dataset_persists_documents_and_records(
    dataset_service: DatasetService,
    count_documents,
    count_records,
    session_factory,
) -> None:
    """A valid data drop parses into four documents and four semantic records."""
    documents = await dataset_service.load_dataset()

    assert len(documents) == 4
    assert count_documents() == 4
    assert count_records() == 4

    with session_factory() as session:
        record_ids = {
            row.id
            for row in session.scalars(select(Record)).all()
        }

    assert record_ids == {
        "record-2024.001",
        "record-curator-notes",
        "record-property-ledger-1908",
        "record-PHOTO-1908-001",
    }


@pytest.mark.asyncio
async def test_load_valid_dataset_normalizes_document_metadata(
    dataset_service: DatasetService,
    session_factory,
) -> None:
    """Each source file is persisted with the expected document type."""
    await dataset_service.load_dataset()

    with session_factory() as session:
        documents = {
            document.filename: document.document_type
            for document in session.scalars(select(Document)).all()
        }

    assert documents == {
        "accession_records.json": "json",
        "curator_notes.md": "markdown",
        "property_ledger_1908.txt": "text",
        "photograph_catalog.json": "json",
    }


@pytest.mark.asyncio
async def test_missing_required_file_raises_file_not_found(
    datasets_path: Path,
    session_factory,
) -> None:
    """Missing schema files trigger an explicit initialization error."""
    (datasets_path / "photograph_catalog.json").unlink()
    service = DatasetService(datasets_path, session_factory)

    with pytest.raises(DatasetFileNotFoundError):
        await service.load_dataset()


@pytest.mark.asyncio
async def test_invalid_json_raises_schema_error(
    datasets_path: Path,
    session_factory,
) -> None:
    """Malformed JSON forces a fast schema failure."""
    (datasets_path / "accession_records.json").write_text("{not-json", encoding="utf-8")
    service = DatasetService(datasets_path, session_factory)

    with pytest.raises(DatasetSchemaError, match="Invalid JSON"):
        await service.load_dataset()


@pytest.mark.asyncio
async def test_invalid_utf8_raises_encoding_error(
    datasets_path: Path,
    session_factory,
) -> None:
    """Non-UTF-8 byte sequences raise a typed encoding error."""
    (datasets_path / "curator_notes.md").write_bytes(b"\xff\xfe Curator")
    service = DatasetService(datasets_path, session_factory)

    with pytest.raises(DatasetEncodingError):
        await service.load_dataset()


@pytest.mark.asyncio
async def test_invalid_confidence_raises_validation_error(
    datasets_path: Path,
    session_factory,
) -> None:
    """Out-of-range confidence values fail strict record validation."""
    invalid_payload = """[
      {
        "accession_number": "2024.001",
        "title": "Marble Bust of John Miller",
        "date_acquired": "2024-03-12",
        "source": "Miller Estate Donation",
        "confidence": 1.5
      }
    ]"""
    (datasets_path / "accession_records.json").write_text(invalid_payload, encoding="utf-8")
    service = DatasetService(datasets_path, session_factory)

    with pytest.raises(DatasetValidationError):
        await service.load_dataset()


@pytest.mark.asyncio
async def test_empty_text_file_raises_schema_error(
    datasets_path: Path,
    session_factory,
) -> None:
    """Whitespace-only text assets are rejected at initialization."""
    (datasets_path / "property_ledger_1908.txt").write_text("   \n\t  ", encoding="utf-8")
    service = DatasetService(datasets_path, session_factory)

    with pytest.raises(DatasetSchemaError, match="non-whitespace"):
        await service.load_dataset()


@pytest.mark.asyncio
async def test_dataset_ingestion_offloads_blocking_work_to_worker_thread(
    datasets_path: Path,
    session_factory,
) -> None:
    """Dataset ingestion runs blocking file and database work via asyncio.to_thread."""
    service = DatasetService(datasets_path, session_factory)

    with patch("asyncio.to_thread", wraps=asyncio.to_thread) as mock_thread:
        await service.load_dataset()

    mock_thread.assert_called_once_with(service.initialize_datasets)


def test_schema_creates_relational_tables(memory_store_path: Path) -> None:
    """All core relational entities are registered in the SQLite schema."""
    engine = create_engine_for_path(memory_store_path)
    init_schema(engine)
    table_names = set(inspect(engine).get_table_names())

    assert {"documents", "records", "receipts"} <= table_names


def test_receipt_payload_hash_has_unique_index(memory_store_path: Path) -> None:
    """Receipt payload hashes are guarded by a unique database index."""
    engine = create_engine_for_path(memory_store_path)
    init_schema(engine)
    indexes = inspect(engine).get_indexes(Receipt.__tablename__)
    payload_indexes = [
        index for index in indexes if "payload_hash" in index["column_names"]
    ]

    assert any(index.get("unique") for index in payload_indexes)


@pytest.mark.asyncio
async def test_reload_skips_reingestion_when_documents_exist(
    tmp_path: Path,
    session_factory,
    count_documents,
) -> None:
    """Subsequent startup loads skip ingestion when documents already exist."""
    datasets_path = tmp_path / "datasets"
    write_valid_dataset(datasets_path)
    service = DatasetService(datasets_path, session_factory)

    await service.load_dataset()
    await service.load_dataset()

    assert count_documents() == 4
