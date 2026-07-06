"""Repository queries for localized memory record retrieval."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, sessionmaker

from app.models import Document, Record

_SEARCH_STOP_WORDS = frozenset({
    "about",
    "everything",
    "from",
    "household",
    "into",
    "known",
    "summarize",
    "summarise",
    "their",
    "transactions",
    "with",
    "your",
})


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


def _filter_search_terms(query: str) -> list[str]:
    """Remove repository-level stop words from a sanitized search query.

    :param str query: Sanitized whitespace-delimited search string.
    :returns: Searchable terms that contribute to keyword-density ranking.
    :rtype: list[str]
    """
    return [
        term
        for term in query.split()
        if term and term.lower() not in _SEARCH_STOP_WORDS
    ]


def _keyword_match_score(record: Record, terms: list[str]) -> int:
    """Count how many query terms appear in a record's title or content.

    :param Record record: Candidate memory record to score.
    :param list[str] terms: Filtered search terms from the user query.
    :returns: Number of terms matched in the record haystack.
    :rtype: int
    """
    haystack = f"{record.title} {record.content}".lower()
    return sum(1 for term in terms if term.lower() in haystack)


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
        """Return record chunks ranked by keyword density instead of strict AND.

        Candidates must match at least one searchable term. Results are ordered
        by the number of matched terms descending, then confidence descending,
        then title ascending.

        :param str query: Sanitized search string with one or more terms.
        :param int limit: Maximum number of records to return.
        :returns: Matching memory records with eagerly loaded documents.
        :rtype: list[Record]
        """
        terms = _filter_search_terms(query)
        if not terms:
            return []

        term_conditions = []
        for term in terms:
            pattern = f"%{_escape_like_term(term)}%"
            term_conditions.append(
                or_(
                    func.lower(Record.title).like(pattern, escape="\\"),
                    func.lower(Record.content).like(pattern, escape="\\"),
                )
            )

        statement = (
            select(Record)
            .options(joinedload(Record.document))
            .where(or_(*term_conditions))
        )

        with self._session_factory() as session:
            candidates = list(session.scalars(statement).unique().all())

        ranked = sorted(
            candidates,
            key=lambda record: (
                -_keyword_match_score(record, terms),
                -record.confidence,
                record.title,
            ),
        )
        return ranked[:limit]

    def get_document_by_id(self, doc_id: str) -> Document | None:
        """Fetch upstream source document metadata for attribution.

        :param str doc_id: Primary key of the source document.
        :returns: Matching document row, or ``None`` when not found.
        :rtype: Document | None
        """
        with self._session_factory() as session:
            return session.get(Document, doc_id)
