"""Unit tests for memory retrieval and source attribution."""

from __future__ import annotations

import asyncio

import pytest

from app.repositories.memory_repository import MemoryRepository
from app.services.memory_service import MemoryService


@pytest.fixture
def memory_repository(session_factory) -> MemoryRepository:
    """Provide a memory repository bound to the test database."""
    return MemoryRepository(session_factory)


@pytest.fixture
def memory_service(memory_repository: MemoryRepository) -> MemoryService:
    """Provide a memory service bound to the test repository."""
    return MemoryService(memory_repository)


@pytest.fixture
def ingested_corpus(dataset_service) -> None:
    """Load the canonical reference dataset into the test database."""
    asyncio.run(dataset_service.load_dataset())


@pytest.mark.asyncio
async def test_retrieve_context_finds_fido_record(
    memory_service: MemoryService,
    ingested_corpus: None,
) -> None:
    """A known keyword from the property ledger returns the correct chunk."""
    records = await memory_service.retrieve_context("Who is Fido?")

    assert len(records) >= 1
    assert any(record.id == "record-property-ledger-1908" for record in records)
    property_record = next(
        record for record in records if record.id == "record-property-ledger-1908"
    )
    assert "Fido" in property_record.content


@pytest.mark.asyncio
async def test_retrieve_context_finds_marble_bust_record(
    memory_service: MemoryService,
    ingested_corpus: None,
) -> None:
    """Phrase matching returns the accession record for a known artifact."""
    records = await memory_service.retrieve_context("Marble Bust of John Miller")

    assert len(records) >= 1
    assert any(record.id == "record-2024.001" for record in records)


@pytest.mark.asyncio
async def test_retrieve_context_respects_limit(
    memory_service: MemoryService,
    ingested_corpus: None,
) -> None:
    """Broad queries are capped at the configured retrieval limit."""
    service = MemoryService(memory_service._repository, retrieval_limit=2)
    records = await service.retrieve_context("Miller")

    assert len(records) <= 2


@pytest.mark.asyncio
async def test_retrieve_context_empty_question_returns_empty_list(
    memory_service: MemoryService,
    ingested_corpus: None,
) -> None:
    """Whitespace-only questions return a clean empty result."""
    records = await memory_service.retrieve_context("   \t  ")

    assert records == []


@pytest.mark.asyncio
async def test_retrieve_context_unmatched_query_returns_empty_list(
    memory_service: MemoryService,
    ingested_corpus: None,
) -> None:
    """Unknown keywords return an empty list without raising errors."""
    records = await memory_service.retrieve_context("xyzzy unobtainium")

    assert records == []


@pytest.mark.asyncio
async def test_retrieved_records_have_document_relationship(
    memory_service: MemoryService,
    ingested_corpus: None,
) -> None:
    """Retrieved records maintain foreign keys back to source documents."""
    records = await memory_service.retrieve_context("Fido")

    assert len(records) >= 1
    property_record = next(
        (record for record in records if record.id == "record-property-ledger-1908"),
        None,
    )
    assert property_record is not None
    record = property_record
    assert record.document is not None
    assert record.document_id == record.document.id
    assert record.document.filename == "property_ledger_1908.txt"


@pytest.mark.asyncio
async def test_assemble_source_attribution_maps_provenance(
    memory_repository: MemoryRepository,
    memory_service: MemoryService,
    ingested_corpus: None,
) -> None:
    """Source attribution exposes unbroken record-to-document provenance."""
    records = memory_repository.search_records("property ledger fido", limit=1)
    attributions = await memory_service.assemble_source_attribution(records)

    assert len(attributions) == 1
    attribution = attributions[0]
    assert attribution.record_id == "record-property-ledger-1908"
    assert attribution.document_id == "doc-property_ledger_1908"
    assert attribution.document_filename == "property_ledger_1908.txt"
    assert attribution.document_type == "text"
    assert attribution.record_classification == "property_ledger"


@pytest.mark.asyncio
async def test_assemble_source_attribution_empty_records_returns_empty_list(
    memory_service: MemoryService,
) -> None:
    """An empty retrieval yields an empty attribution list."""
    assert await memory_service.assemble_source_attribution([]) == []


def test_get_document_by_id_returns_metadata(
    memory_repository: MemoryRepository,
    ingested_corpus: None,
) -> None:
    """Document lookup returns upstream file metadata for attribution."""
    document = memory_repository.get_document_by_id("doc-curator_notes")

    assert document is not None
    assert document.filename == "curator_notes.md"
    assert document.document_type == "markdown"


def test_get_document_by_id_missing_returns_none(
    memory_repository: MemoryRepository,
    ingested_corpus: None,
) -> None:
    """Unknown document identifiers return None instead of raising."""
    assert memory_repository.get_document_by_id("doc-does-not-exist") is None
