"""Extracted semantic memory chunks derived from source documents."""

from datetime import UTC, datetime

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Record(Base):
    """Normalized semantic chunk ready for retrieval and evidence assembly.

    :ivar str id: Primary key identifier for the memory chunk.
    :ivar str document_id: Foreign key to the parent :class:`~app.models.document.Document`.
    :ivar str title: Human-readable chunk title.
    :ivar str content: Searchable textual content of the chunk.
    :ivar str classification: Semantic category (e.g. ``accession``, ``photograph``).
    :ivar float confidence: Confidence score in the range ``[0.0, 1.0]``.
    :ivar str provenance_json: JSON-encoded provenance metadata.
    :ivar str created_at: ISO-8601 UTC timestamp of record creation.
    :ivar Document document: Parent source document relationship.
    """

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
