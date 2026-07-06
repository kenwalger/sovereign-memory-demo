"""Forensic receipt generation and persistence service."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.models import Receipt, Record
from app.receipts import build_evidence_strings, build_forensic_seal, compute_payload_hash
from app.services.exceptions import ReceiptDuplicateError, ReceiptValidationError


class ReceiptService:
    """Generate, seal, and persist forensic receipts for audited answers."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def generate_forensic_receipt(
        self,
        evidence_records: list[Record],
        confidence_score: float,
    ) -> Receipt:
        """Generate a sealed receipt from evidence records and persist it."""
        self._validate_inputs(evidence_records, confidence_score)

        evidence_strings = build_evidence_strings(evidence_records)
        if not evidence_strings:
            raise ReceiptValidationError("Evidence records must contain non-empty content")

        payload_hash = compute_payload_hash(evidence_strings)
        sources = self._collect_sources(evidence_records)

        with self._session_factory() as session:
            if self._payload_hash_exists(session, payload_hash):
                raise ReceiptDuplicateError(payload_hash)

            receipt_id = self._allocate_receipt_id(session)
            answer_id = f"ANS-{receipt_id.removeprefix('FR-')}"
            forensic_metadata = build_forensic_seal(payload_hash, receipt_id)
            timestamp = datetime.now(UTC).isoformat()

            receipt_body = {
                "receipt_id": receipt_id,
                "timestamp": timestamp,
                "confidence": confidence_score,
                "sources": sources,
                "evidence": evidence_strings,
                "ledger_reference": forensic_metadata["ledger_reference"],
                "metadata": forensic_metadata,
            }

            receipt = Receipt(
                id=receipt_id,
                answer_id=answer_id,
                confidence=confidence_score,
                receipt_json=json.dumps(receipt_body),
                payload_hash=payload_hash,
                ledger_reference=forensic_metadata["ledger_reference"],
                created_at=timestamp,
            )

            try:
                session.add(receipt)
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ReceiptDuplicateError(payload_hash) from exc

            session.refresh(receipt)
            return receipt

    @staticmethod
    def _validate_inputs(
        evidence_records: list[Record],
        confidence_score: float,
    ) -> None:
        """Fail fast when receipt inputs are invalid."""
        if not evidence_records:
            raise ReceiptValidationError("At least one evidence record is required")
        if not 0.0 <= confidence_score <= 1.0:
            raise ReceiptValidationError("Confidence score must be between 0.0 and 1.0")

    @staticmethod
    def _collect_sources(evidence_records: list[Record]) -> list[str]:
        """Collect sorted upstream source filenames for attribution."""
        sources: set[str] = set()
        for record in evidence_records:
            if record.document is not None:
                sources.add(record.document.filename)
                continue

            provenance = json.loads(record.provenance_json)
            source_file = provenance.get("source_file")
            if isinstance(source_file, str) and source_file:
                sources.add(source_file)

        return sorted(sources)

    @staticmethod
    def _payload_hash_exists(session: Session, payload_hash: str) -> bool:
        """Return whether a receipt with the payload hash already exists."""
        existing = session.scalar(
            select(Receipt.id).where(Receipt.payload_hash == payload_hash)
        )
        return existing is not None

    @staticmethod
    def _allocate_receipt_id(session: Session) -> str:
        """Allocate the next sequential forensic receipt identifier."""
        receipt_count = session.scalar(select(func.count()).select_from(Receipt)) or 0
        return f"FR-{receipt_count + 1:04d}"
