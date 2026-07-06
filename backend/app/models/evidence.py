"""Context verified for a query lifecycle."""

from datetime import UTC, datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Evidence(Base):
    """Verified excerpt linking a record to a query lifecycle."""

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
