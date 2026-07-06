"""Orchestration service for memory retrieval and source attribution."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass

from app.models import Document, Record
from app.repositories.memory_repository import MemoryRepository

DEFAULT_RETRIEVAL_LIMIT = 3
"""int: Default maximum number of memory records returned per retrieval query."""
_SANITIZE_PATTERN = re.compile(r"[^a-zA-Z0-9\s]+")
_STOP_WORDS = frozenset({
    "a",
    "about",
    "all",
    "an",
    "and",
    "are",
    "everything",
    "for",
    "how",
    "is",
    "known",
    "show",
    "summarize",
    "summarise",
    "that",
    "the",
    "this",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
})


@dataclass(frozen=True)
class SourceAttribution:
    """Provenance mapping from a retrieved record to its source document.

    :ivar str record_id: Primary key of the retrieved memory record.
    :ivar str record_title: Human-readable title of the memory record.
    :ivar str record_classification: Semantic classification of the record.
    :ivar float record_confidence: Confidence score of the memory record.
    :ivar str document_id: Primary key of the parent source document.
    :ivar str document_filename: Original filename of the source document.
    :ivar str document_type: Normalized document type label.
    """

    record_id: str
    record_title: str
    record_classification: str
    record_confidence: float
    document_id: str
    document_filename: str
    document_type: str


class MemoryService:
    """Coordinate sanitized retrieval queries and provenance assembly.

    :ivar MemoryRepository _repository: Repository used for record search and
        document lookup.
    :ivar int _retrieval_limit: Maximum number of records returned per query.
    """

    def __init__(
        self,
        repository: MemoryRepository,
        retrieval_limit: int = DEFAULT_RETRIEVAL_LIMIT,
    ) -> None:
        """Initialize the memory service.

        :param MemoryRepository repository: Repository used to search records
            and fetch source documents.
        :param int retrieval_limit: Maximum number of records returned per query.
        :returns: None
        :rtype: None
        """
        self._repository = repository
        self._retrieval_limit = retrieval_limit

    async def retrieve_context(self, question: str) -> list[Record]:
        """Sanitize a question and retrieve matching memory record chunks.

        CPU-bound question sanitization and repository search are offloaded to
        worker threads to avoid blocking the event loop.

        :param str question: Raw user question text.
        :returns: Matching memory records, or an empty list when the sanitized
            query contains no searchable terms.
        :rtype: list[Record]
        """
        sanitized_query = await asyncio.to_thread(self._sanitize_question, question)
        if not sanitized_query:
            return []

        return await asyncio.to_thread(
            self._repository.search_records,
            sanitized_query,
            self._retrieval_limit,
        )

    async def assemble_source_attribution(
        self,
        records: list[Record],
    ) -> list[SourceAttribution]:
        """Map retrieved records back to their parent document metadata.

        Repository fallback lookups are offloaded to a worker thread to avoid
        blocking the event loop.

        :param list[Record] records: Retrieved memory records to attribute.
        :returns: Provenance mappings for records with resolvable documents.
        :rtype: list[SourceAttribution]
        """
        if not records:
            return []

        return await asyncio.to_thread(self._assemble_source_attribution, records)

    def _assemble_source_attribution(
        self,
        records: list[Record],
    ) -> list[SourceAttribution]:
        """Build provenance mappings for retrieved records on a worker thread.

        Records whose parent document cannot be resolved are skipped.

        :param list[Record] records: Retrieved memory records to attribute.
        :returns: Provenance mappings for records with resolvable documents.
        :rtype: list[SourceAttribution]
        """
        attributions: list[SourceAttribution] = []

        for record in records:
            document = record.document
            if document is None:
                document = self._repository.get_document_by_id(record.document_id)
            if document is None:
                continue

            attributions.append(
                SourceAttribution(
                    record_id=record.id,
                    record_title=record.title,
                    record_classification=record.classification,
                    record_confidence=record.confidence,
                    document_id=document.id,
                    document_filename=document.filename,
                    document_type=document.document_type,
                )
            )

        return attributions

    @staticmethod
    def _sanitize_question(question: str) -> str:
        """Normalize a user question into lowercase search terms.

        Strips non-alphanumeric characters, lowercases tokens, and removes
        common stop words.

        :param str question: Raw user question text.
        :returns: Space-joined search terms suitable for repository lookup.
        :rtype: str
        """
        normalized = _SANITIZE_PATTERN.sub(" ", question)
        terms = [
            term
            for term in normalized.lower().split()
            if term and term not in _STOP_WORDS
        ]
        return " ".join(terms)
