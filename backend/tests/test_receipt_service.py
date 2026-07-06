"""Unit tests for forensic receipt generation and persistence."""

from __future__ import annotations

import asyncio
import json

import pytest
from sqlalchemy import select

from app.models import Receipt, Record
from app.receipts import build_evidence_strings, compute_payload_hash
from app.repositories.memory_repository import MemoryRepository
from app.services.exceptions import ReceiptDuplicateError, ReceiptValidationError
from app.services.receipt_service import ReceiptService


@pytest.fixture
def receipt_service(session_factory) -> ReceiptService:
    """Provide a receipt service bound to the test database."""
    return ReceiptService(session_factory)


@pytest.fixture
def ingested_corpus(dataset_service) -> None:
    """Load the canonical reference dataset into the test database."""
    asyncio.run(dataset_service.load_dataset())


@pytest.fixture
def fido_evidence_records(
    session_factory,
    ingested_corpus: None,
) -> list[Record]:
    """Return property ledger evidence records mentioning Fido."""
    repository = MemoryRepository(session_factory)
    return repository.search_records("property ledger fido", limit=1)


def test_generate_forensic_receipt_persists_receipt_row(
    receipt_service: ReceiptService,
    fido_evidence_records: list[Record],
    session_factory,
) -> None:
    """Valid evidence records write a Receipt row with a unique payload hash."""
    receipt = receipt_service.generate_forensic_receipt(
        fido_evidence_records,
        confidence_score=0.96,
    )

    assert receipt.id == "FR-0001"
    assert receipt.payload_hash is not None
    assert len(receipt.payload_hash) == 64
    assert receipt.ledger_reference == f"LEDGER-{receipt.payload_hash[:8].upper()}"

    with session_factory() as session:
        stored = session.get(Receipt, receipt.id)

    assert stored is not None
    assert stored.payload_hash == receipt.payload_hash


def test_generate_forensic_receipt_embeds_metadata_payload_hash(
    receipt_service: ReceiptService,
    fido_evidence_records: list[Record],
) -> None:
    """Receipt JSON metadata carries the pre-sieve payload hash and seal."""
    receipt = receipt_service.generate_forensic_receipt(
        fido_evidence_records,
        confidence_score=0.96,
    )
    receipt_body = json.loads(receipt.receipt_json)

    assert receipt_body["receipt_id"] == "FR-0001"
    assert receipt_body["metadata"]["payload_hash"] == receipt.payload_hash
    assert receipt_body["metadata"]["signature"]
    assert receipt_body["metadata"]["airlock_boundary"] == "outbound-answer-governance"
    assert "property_ledger_1908.txt" in receipt_body["sources"]
    assert any("Fido" in evidence for evidence in receipt_body["evidence"])


def test_payload_hash_is_deterministic_for_identical_evidence(
    fido_evidence_records: list[Record],
) -> None:
    """Identical evidence strings always produce the same payload hash."""
    evidence_strings = build_evidence_strings(fido_evidence_records)
    first_hash = compute_payload_hash(evidence_strings)
    second_hash = compute_payload_hash(evidence_strings)

    assert first_hash == second_hash


def test_duplicate_payload_hash_raises_receipt_duplicate_error(
    receipt_service: ReceiptService,
    fido_evidence_records: list[Record],
) -> None:
    """Duplicate payload hashes are rejected by the unique index constraint."""
    receipt_service.generate_forensic_receipt(
        fido_evidence_records,
        confidence_score=0.96,
    )

    with pytest.raises(ReceiptDuplicateError):
        receipt_service.generate_forensic_receipt(
            fido_evidence_records,
            confidence_score=0.96,
        )


def test_empty_evidence_records_raise_validation_error(
    receipt_service: ReceiptService,
) -> None:
    """Receipt generation requires at least one evidence record."""
    with pytest.raises(ReceiptValidationError, match="At least one evidence record"):
        receipt_service.generate_forensic_receipt([], confidence_score=0.9)


def test_invalid_confidence_raises_validation_error(
    receipt_service: ReceiptService,
    fido_evidence_records: list[Record],
) -> None:
    """Confidence scores must remain within the closed unit interval."""
    with pytest.raises(ReceiptValidationError, match="Confidence score"):
        receipt_service.generate_forensic_receipt(
            fido_evidence_records,
            confidence_score=1.5,
        )


def test_sequential_receipt_ids_increment(
    receipt_service: ReceiptService,
    session_factory,
    ingested_corpus: None,
) -> None:
    """Each new receipt receives the next sequential FR-XXXX identifier."""
    repository = MemoryRepository(session_factory)
    ledger_record = repository.search_records("property ledger fido", limit=1)
    photo_record = repository.search_records("miller family portrait", limit=1)

    first = receipt_service.generate_forensic_receipt(ledger_record, confidence_score=0.9)
    second = receipt_service.generate_forensic_receipt(photo_record, confidence_score=0.9)

    assert first.id == "FR-0001"
    assert second.id == "FR-0002"
    assert first.payload_hash != second.payload_hash

    with session_factory() as session:
        receipt_count = len(session.scalars(select(Receipt)).all())

    assert receipt_count == 2
