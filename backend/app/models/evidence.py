"""Context verified for a query lifecycle."""

from datetime import UTC, datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Evidence(Base):
    """Verified excerpt linking a record to a query lifecycle.

    :ivar str id: Primary key identifier for the evidence row.
    :ivar str record_id: Foreign key to the parent :class:`~app.models.record.Record`.
    :ivar str | None query_id: Optional identifier of the originating query.
    :ivar str excerpt: Verified textual excerpt from the linked record.
    :ivar str verified_at: ISO-8601 UTC timestamp of verification.
    :ivar Record record: Parent memory record relationship.
    """

    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    record_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("records.id"),
        nullable=False,
    )
    query_id: Mapped[str | None] = mapped_column(String, nullable=True)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    verified_at: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=lambda: datetime.now(UTC).isoformat(),
    )

    record: Mapped["Record"] = relationship(back_populates="evidence_items")
