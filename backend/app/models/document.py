"""Source document metadata persisted from the datasets directory."""

from datetime import UTC, datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Document(Base):
    """Raw source file ingested from the local datasets path.

    :ivar str id: Primary key identifier (``doc-{stem}``).
    :ivar str filename: Original dataset filename.
    :ivar str document_type: Normalized type label (``json``, ``markdown``, ``text``).
    :ivar str content: Full UTF-8 decoded file contents.
    :ivar str created_at: ISO-8601 UTC timestamp of ingestion.
    :ivar list[Record] records: Semantic chunks derived from this document.
    """

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=lambda: datetime.now(UTC).isoformat(),
    )

    records: Mapped[list["Record"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
