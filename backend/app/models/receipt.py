"""Forensic cryptographic verification envelope for audited answers."""

from datetime import UTC, datetime

from sqlalchemy import Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Receipt(Base):
    """Immutable forensic receipt with a unique payload hash index."""

    __tablename__ = "receipts"
    __table_args__ = (
        Index("ix_receipts_payload_hash", "payload_hash", unique=True),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
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
