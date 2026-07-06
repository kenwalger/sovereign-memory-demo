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
    """Generate, seal, and persist forensic receipts for audited answers.

    :ivar sessionmaker[Session] _session_factory: Factory for transactional
        database sessions used during receipt persistence.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """Initialize the receipt service.

        :param sessionmaker[Session] session_factory: Factory used to open
            transactional sessions for receipt persistence.
        :returns: None
        :rtype: None
        """
        self._session_factory = session_factory

    def generate_forensic_receipt(
        self,
        evidence_records: list[Record],
        confidence_score: float,
    ) -> Receipt:
        """Generate a sealed receipt from evidence records and persist it.

        :param list[Record] evidence_records: Memory records forming the audited
            evidence set.
        :param float confidence_score: Aggregated confidence in the range
            ``[0.0, 1.0]``.
        :returns: Newly persisted forensic receipt row.
        :rtype: Receipt
        :raises ReceiptValidationError: If inputs are invalid or evidence
            content is empty after normalization.
        :raises ReceiptDuplicateError: If a receipt with the same payload hash
            already exists.
        """
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
        """Fail fast when receipt inputs are invalid.

        :param list[Record] evidence_records: Candidate evidence records for
            receipt generation.
        :param float confidence_score: Confidence value to validate.
        :returns: None
        :rtype: None
        :raises ReceiptValidationError: If no evidence records are supplied or
            the confidence score is outside ``[0.0, 1.0]``.
        """
        if not evidence_records:
            raise ReceiptValidationError("At least one evidence record is required")
        if not 0.0 <= confidence_score <= 1.0:
            raise ReceiptValidationError("Confidence score must be between 0.0 and 1.0")

    @staticmethod
    def _collect_sources(evidence_records: list[Record]) -> list[str]:
        """Collect sorted upstream source filenames for attribution.

        :param list[Record] evidence_records: Memory records whose provenance
            is inspected for source filenames.
        :returns: Lexicographically sorted unique source filenames.
        :rtype: list[str]
        """
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
        """Return whether a receipt with the payload hash already exists.

        :param Session session: Active database session for the lookup.
        :param str payload_hash: Deterministic evidence payload hash.
        :returns: ``True`` when a receipt with the hash exists, else ``False``.
        :rtype: bool
        """
        existing = session.scalar(
            select(Receipt.id).where(Receipt.payload_hash == payload_hash)
        )
        return existing is not None

    @staticmethod
    def _allocate_receipt_id(session: Session) -> str:
        """Allocate the next sequential forensic receipt identifier.

        :param Session session: Active database session used to count receipts.
        :returns: Forensic receipt identifier in ``FR-####`` format.
        :rtype: str
        """
        receipt_count = session.scalar(select(func.count()).select_from(Receipt)) or 0
        return f"FR-{receipt_count + 1:04d}"

    def retrieve_receipt(self, receipt_id: str) -> Receipt | None:
        """Fetch a persisted receipt by its forensic identifier.

        :param str receipt_id: Primary key of the forensic receipt.
        :returns: Matching receipt row, or ``None`` when not found.
        :rtype: Receipt | None
        """
        with self._session_factory() as session:
            return session.get(Receipt, receipt_id)

    def retrieve_receipt_by_payload_hash(self, payload_hash: str) -> Receipt | None:
        """Fetch a persisted receipt by its deterministic payload hash.

        :param str payload_hash: SHA-256 digest of normalized evidence strings.
        :returns: Matching receipt row, or ``None`` when not found.
        :rtype: Receipt | None
        """
        with self._session_factory() as session:
            return session.scalar(
                select(Receipt).where(Receipt.payload_hash == payload_hash)
            )
