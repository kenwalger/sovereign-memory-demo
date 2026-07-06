"""Pydantic schemas for the public HTTP API."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class QuestionRequest(BaseModel):
    """Inbound question payload.

    :ivar str question: Non-empty user question after whitespace trimming,
        bounded to a production-safe maximum length.
    """

    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        """Reject whitespace-only question payloads.

        :param str value: Raw question string from the request body.
        :returns: Stripped question text suitable for retrieval.
        :rtype: str
        :raises ValueError: If the stripped question is empty.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("question must not be empty")
        return stripped


class SourceAttributionResponse(BaseModel):
    """Provenance mapping exposed to API consumers.

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


class QuestionResponse(BaseModel):
    """Unified question lifecycle response contract.

    :ivar str answer: Generated answer text for the user question.
    :ivar list[str] evidence: Normalized evidence strings used for attribution.
    :ivar list[SourceAttributionResponse] sources: Provenance mappings for
        matched records.
    :ivar dict[str, Any] | None receipt: Forensic receipt payload, or ``None``
        when no records matched.
    """

    answer: str
    evidence: list[str]
    sources: list[SourceAttributionResponse]
    receipt: dict[str, Any] | None
