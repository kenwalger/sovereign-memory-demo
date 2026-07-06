"""Forensic cryptographic verification envelope for audited answers."""

from datetime import UTC, datetime

from sqlalchemy import Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Receipt(Base):
    """Immutable forensic receipt with a unique payload hash index.

    :ivar int sequence: Autoincrementing primary key for atomic ID allocation.
    :ivar str id: Forensic receipt identifier (e.g. ``FR-0001``).
    :ivar str answer_id: Correlated answer identifier (e.g. ``ANS-0001``).
    :ivar float confidence: Aggregated confidence score for the audited answer.
    :ivar str receipt_json: JSON-encoded forensic receipt body.
    :ivar str | None payload_hash: Deterministic SHA-256 hash of evidence strings.
    :ivar str | None ledger_reference: Simulated ledger linkage reference.
    :ivar str created_at: ISO-8601 UTC timestamp of receipt creation.
    """

    __tablename__ = "receipts"
    __table_args__ = (
        Index("ix_receipts_payload_hash", "payload_hash", unique=True),
        Index("ix_receipts_forensic_id", "id", unique=True),
    )

    sequence: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id: Mapped[str | None] = mapped_column(String, nullable=True)
    answer_id: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    receipt_json: Mapped[str] = mapped_column(Text, nullable=False)
    payload_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    ledger_reference: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=lambda: datetime.now(UTC).isoformat(),
    )
