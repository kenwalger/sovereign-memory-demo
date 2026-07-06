"""Extracted semantic memory chunks derived from source documents."""

from datetime import UTC, datetime

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Record(Base):
    """Normalized semantic chunk ready for retrieval and evidence assembly."""

    __tablename__ = "records"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("documents.id"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    classification: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    provenance_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=lambda: datetime.now(UTC).isoformat(),
    )

    document: Mapped["Document"] = relationship(back_populates="records")
    evidence_items: Mapped[list["Evidence"]] = relationship(
        back_populates="record",
        cascade="all, delete-orphan",
    )
