"""Orchestration service for memory retrieval and source attribution."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass

from app.models import Document, Record
from app.repositories.memory_repository import MemoryRepository

DEFAULT_RETRIEVAL_LIMIT = 3
_SANITIZE_PATTERN = re.compile(r"[^a-zA-Z0-9\s]+")
_STOP_WORDS = frozenset({
    "a",
    "all",
    "an",
    "and",
    "are",
    "for",
    "how",
    "is",
    "show",
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
    """Provenance mapping from a retrieved record to its source document."""

    record_id: str
    record_title: str
    record_classification: str
    record_confidence: float
    document_id: str
    document_filename: str
    document_type: str


class MemoryService:
    """Coordinate sanitized retrieval queries and provenance assembly."""

    def __init__(
        self,
        repository: MemoryRepository,
        retrieval_limit: int = DEFAULT_RETRIEVAL_LIMIT,
    ) -> None:
        self._repository = repository
        self._retrieval_limit = retrieval_limit

    async def retrieve_context(self, question: str) -> list[Record]:
        """Sanitize a question and retrieve matching memory record chunks."""
        sanitized_query = self._sanitize_question(question)
        if not sanitized_query:
            return []

        return await asyncio.to_thread(
            self._repository.search_records,
            sanitized_query,
            self._retrieval_limit,
        )

    def assemble_source_attribution(
        self,
        records: list[Record],
    ) -> list[SourceAttribution]:
        """Map retrieved records back to their parent document metadata."""
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
        """Normalize a user question into lowercase search terms."""
        normalized = _SANITIZE_PATTERN.sub(" ", question)
        terms = [
            term
            for term in normalized.lower().split()
            if term and term not in _STOP_WORDS
        ]
        return " ".join(terms)
