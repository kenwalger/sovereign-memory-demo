"""Repository queries for localized memory record retrieval."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, sessionmaker

from app.models import Document, Record


def _escape_like_term(term: str) -> str:
    """Escape SQL ``LIKE`` wildcard characters in a user-supplied search term.

    :param str term: Sanitized search token before pattern interpolation.
    :returns: Term with ``%``, ``_``, and escape characters neutralized.
    :rtype: str
    """
    return (
        term.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


class MemoryRepository:
    """Execute SQLAlchemy 2.0 queries against ingested memory records.

    :ivar sessionmaker[Session] _session_factory: Factory for short-lived
        database sessions used by query methods.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """Initialize the repository with a session factory.

        :param sessionmaker[Session] session_factory: Factory used to open
            short-lived database sessions for queries.
        :returns: None
        :rtype: None
        """
        self._session_factory = session_factory

    def search_records(self, query: str, limit: int = 3) -> list[Record]:
        """Return record chunks whose title or content match the query terms.

        Each whitespace-separated term must appear in either the record title
        or content (case-insensitive). Results are ordered by confidence
        descending, then title ascending.

        :param str query: Sanitized search string with one or more terms.
        :param int limit: Maximum number of records to return.
        :returns: Matching memory records with eagerly loaded documents.
        :rtype: list[Record]
        """
        terms = query.split()
        if not terms:
            return []

        statement = (
            select(Record)
            .options(joinedload(Record.document))
            .order_by(Record.confidence.desc(), Record.title.asc())
            .limit(limit)
        )

        for term in terms:
            pattern = f"%{_escape_like_term(term)}%"
            statement = statement.where(
                or_(
                    func.lower(Record.title).like(pattern, escape="\\"),
                    func.lower(Record.content).like(pattern, escape="\\"),
                )
            )

        with self._session_factory() as session:
            return list(session.scalars(statement).unique().all())

    def get_document_by_id(self, doc_id: str) -> Document | None:
        """Fetch upstream source document metadata for attribution.

        :param str doc_id: Primary key of the source document.
        :returns: Matching document row, or ``None`` when not found.
        :rtype: Document | None
        """
        with self._session_factory() as session:
            return session.get(Document, doc_id)
