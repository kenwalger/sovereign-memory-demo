"""Forensic receipt generation and persistence service."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sovereign_airlock import AirlockResult
from sovereign_ledger import SovereignLedger

from app.models import Receipt, Record
from app.receipts import build_evidence_strings, build_forensic_seal, compute_payload_hash
from app.services.exceptions import ReceiptDuplicateError, ReceiptValidationError


class ReceiptService:
    """Generate, seal, and persist forensic receipts for audited answers.

    :ivar sessionmaker[Session] _session_factory: Factory for transactional
        database sessions used during receipt persistence.
    :ivar SovereignLedger | None _ledger: Optional append-only ledger for
        tamper-evident forensic receipt commits.
    """

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        ledger: SovereignLedger | None = None,
    ) -> None:
        """Initialize the receipt service.

        :param sessionmaker[Session] session_factory: Factory used to open
            transactional sessions for receipt persistence.
        :param SovereignLedger | None ledger: Optional sovereign ledger used
            for append-only forensic receipt commits.
        :returns: None
        :rtype: None
        """
        self._session_factory = session_factory
        self._ledger = ledger

    def generate_forensic_receipt(
        self,
        evidence_records: list[Record],
        confidence_score: float,
        *,
        airlock_result: AirlockResult | None = None,
        sieved_evidence: list[str] | None = None,
    ) -> Receipt:
        """Generate a sealed receipt from evidence records and persist it.

        :param list[Record] evidence_records: Memory records forming the audited
            evidence set.
        :param float confidence_score: Aggregated confidence in the range
            ``[0.0, 1.0]``.
        :param AirlockResult | None airlock_result: Optional airlock processing
            outcome containing SDK telemetry and signed forensic receipt data.
        :param list[str] | None sieved_evidence: Optional minimized evidence
            strings produced by the sieve pass.
        :returns: Newly persisted forensic receipt row.
        :rtype: Receipt
        :raises ReceiptValidationError: If inputs are invalid or evidence
            content is empty after normalization.
        :raises ReceiptDuplicateError: If a receipt with the same payload hash
            already exists.
        """
        self._validate_inputs(evidence_records, confidence_score)

        evidence_strings = sieved_evidence or build_evidence_strings(evidence_records)
        if not evidence_strings:
            raise ReceiptValidationError("Evidence records must contain non-empty content")

        if airlock_result is not None:
            payload_hash = airlock_result.telemetry.payload_hash
            forensic_metadata = self._build_sdk_metadata(airlock_result)
            ledger_reference = forensic_metadata["ledger_reference"]
        else:
            payload_hash = compute_payload_hash(evidence_strings)
            forensic_metadata = None
            ledger_reference = None

        sources = self._collect_sources(evidence_records)

        with self._session_factory() as session:
            if self._payload_hash_exists(session, payload_hash):
                raise ReceiptDuplicateError(payload_hash)

            timestamp = datetime.now(UTC).isoformat()

            receipt = Receipt(
                confidence=confidence_score,
                receipt_json="{}",
                payload_hash=payload_hash,
                ledger_reference=ledger_reference,
                created_at=timestamp,
                answer_id="",
            )
            session.add(receipt)
            session.flush()

            receipt_id = self._format_receipt_id(receipt.sequence)
            answer_id = f"ANS-{receipt.sequence:04d}"
            receipt.id = receipt_id
            receipt.answer_id = answer_id

            if forensic_metadata is None:
                forensic_metadata = build_forensic_seal(payload_hash, receipt_id)
                ledger_reference = forensic_metadata["ledger_reference"]
                receipt.ledger_reference = ledger_reference

            receipt_body: dict[str, Any] = {
                "receipt_id": receipt_id,
                "timestamp": timestamp,
                "confidence": confidence_score,
                "sources": sources,
                "evidence": evidence_strings,
                "ledger_reference": ledger_reference,
                "metadata": forensic_metadata,
            }
            receipt.receipt_json = json.dumps(receipt_body)

            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ReceiptDuplicateError(payload_hash) from exc

            session.refresh(receipt)
            session.expunge(receipt)

        if airlock_result is not None:
            self._commit_to_ledger(airlock_result)

        return receipt

    @staticmethod
    def _build_sdk_metadata(airlock_result: AirlockResult) -> dict[str, Any]:
        """Build receipt metadata from a successful airlock processing result.

        :param AirlockResult airlock_result: Successful airlock boundary result.
        :returns: Metadata envelope containing SDK telemetry and receipt fields.
        :rtype: dict[str, Any]
        """
        telemetry = airlock_result.telemetry
        metadata: dict[str, Any] = {
            "payload_hash": telemetry.payload_hash,
            "raw_tokens": telemetry.raw_tokens,
            "sieved_tokens": telemetry.sieved_tokens,
            "tax_savings_percentage": telemetry.tax_savings_percentage,
            "airlock_boundary": "outbound-answer-governance",
            "ledger_reference": f"LEDGER-{telemetry.payload_hash[:8].upper()}",
            "policy_warnings": list(airlock_result.policy_warnings),
        }

        if airlock_result.receipt is not None:
            sdk_receipt = airlock_result.receipt
            metadata.update(
                {
                    "signature": sdk_receipt["signature"],
                    "public_key": sdk_receipt["public_key"],
                    "sdk_timestamp": sdk_receipt["timestamp"],
                    "sdk_metadata": sdk_receipt.get("metadata", {}),
                }
            )

        return metadata

    def _commit_to_ledger(self, airlock_result: AirlockResult) -> None:
        """Commit a signed forensic receipt to the append-only sovereign ledger.

        :param AirlockResult airlock_result: Airlock result containing the signed
            forensic receipt and sieved content.
        :returns: None
        :rtype: None
        """
        if self._ledger is None or airlock_result.receipt is None:
            return

        try:
            self._ledger.append_receipt(
                airlock_result.receipt,
                airlock_result.sieved_content,
            )
        except sqlite3.IntegrityError:
            # Airlock may have already committed the same payload hash.
            return

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
    def _format_receipt_id(sequence: int) -> str:
        """Format a forensic receipt identifier from an autoincrement sequence.

        :param int sequence: Database-assigned autoincrement sequence value.
        :returns: Forensic receipt identifier in ``FR-####`` format.
        :rtype: str
        """
        return f"FR-{sequence:04d}"

    def retrieve_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        """Fetch a persisted receipt body by its forensic identifier.

        The receipt JSON is materialized while the database session is active so
        callers never touch a detached SQLAlchemy instance.

        :param str receipt_id: Forensic receipt identifier (e.g. ``FR-0001``).
        :returns: Parsed forensic receipt JSON body, or ``None`` when not found.
        :rtype: dict[str, Any] | None
        """
        with self._session_factory() as session:
            receipt = session.scalar(select(Receipt).where(Receipt.id == receipt_id))
            if receipt is None:
                return None
            return json.loads(receipt.receipt_json)

    def retrieve_receipt_by_payload_hash(self, payload_hash: str) -> dict[str, Any] | None:
        """Fetch a persisted receipt body by its deterministic payload hash.

        The receipt JSON is materialized while the database session is active so
        callers never touch a detached SQLAlchemy instance.

        :param str payload_hash: SHA-256 digest of normalized evidence strings.
        :returns: Parsed forensic receipt JSON body, or ``None`` when not found.
        :rtype: dict[str, Any] | None
        """
        with self._session_factory() as session:
            receipt = session.scalar(
                select(Receipt).where(Receipt.payload_hash == payload_hash)
            )
            if receipt is None:
                return None
            return json.loads(receipt.receipt_json)
