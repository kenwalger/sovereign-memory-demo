"""HTTP route handlers for the Sovereign Memory Demo API."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sovereign_airlock import AirlockPolicyViolation, AirlockResult

from app.api.dependencies import (
    get_memory_service,
    get_outbound_processor,
    get_receipt_service,
)
from app.api.schemas import QuestionRequest, QuestionResponse, SourceAttributionResponse
from app.models import Record
from app.receipts import build_evidence_strings
from app.sdk.boundary import OutboundContextProcessor
from app.services.exceptions import ReceiptDuplicateError
from app.services.memory_service import MemoryService
from app.services.receipt_service import ReceiptService

router = APIRouter(prefix="/api", tags=["memory"])
"""APIRouter: Mounted router exposing memory and receipt HTTP endpoints."""

_EMPTY_ANSWER = "No institutional memory records matched this question."
"""str: Fallback answer returned when retrieval yields no matching records."""


@router.post("/questions", response_model=QuestionResponse)
async def ask_question(
    payload: QuestionRequest,
    memory_service: MemoryService = Depends(get_memory_service),
    receipt_service: ReceiptService = Depends(get_receipt_service),
    outbound_processor: OutboundContextProcessor = Depends(get_outbound_processor),
) -> QuestionResponse:
    """Execute the question lifecycle: retrieve, minimize, govern, and receipt.

    Retrieves matching memory records, runs sieve and airlock governance over
    the unified outbound context, assembles a mock answer and provenance
    metadata, and generates or reuses a forensic receipt for the evidence set.

    :param QuestionRequest payload: Validated inbound question request body.
    :param MemoryService memory_service: Application-scoped memory service.
    :param ReceiptService receipt_service: Application-scoped receipt service.
    :param OutboundContextProcessor outbound_processor: SDK outbound processor.
    :returns: Answer text, evidence strings, source attributions, and receipt.
    :rtype: QuestionResponse
    :raises HTTPException: With status 400 when airlock policy blocks the payload.
    """
    records = await memory_service.retrieve_context(payload.question)
    raw_evidence = build_evidence_strings(records)

    try:
        airlock_result = await outbound_processor.process(payload.question, raw_evidence)
    except AirlockPolicyViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "policy_blocked",
                "message": str(exc),
                "warnings": exc.warnings,
            },
        ) from exc

    if not records:
        return QuestionResponse(
            answer=_EMPTY_ANSWER,
            evidence=[],
            sources=[],
            receipt=None,
        )

    sieved_evidence = _split_sieved_evidence(airlock_result.sieved_content)
    answer = _build_mock_answer(records)
    attributions = await memory_service.assemble_source_attribution(records)
    sources = [
        SourceAttributionResponse(
            record_id=attribution.record_id,
            record_title=attribution.record_title,
            record_classification=attribution.record_classification,
            record_confidence=attribution.record_confidence,
            document_id=attribution.document_id,
            document_filename=attribution.document_filename,
            document_type=attribution.document_type,
        )
        for attribution in attributions
    ]
    confidence = _calculate_confidence(records)
    receipt_payload = await asyncio.to_thread(
        _generate_or_fetch_receipt,
        receipt_service,
        records,
        confidence,
        airlock_result,
        sieved_evidence,
    )

    return QuestionResponse(
        answer=answer,
        evidence=sieved_evidence,
        sources=sources,
        receipt=receipt_payload,
    )


@router.get("/receipts/{receipt_id}")
async def get_receipt(
    receipt_id: str,
    receipt_service: ReceiptService = Depends(get_receipt_service),
) -> dict[str, Any]:
    """Fetch a persisted forensic receipt by identifier.

    :param str receipt_id: Forensic receipt primary key (e.g. ``FR-0001``).
    :param ReceiptService receipt_service: Application-scoped receipt service.
    :returns: Parsed forensic receipt JSON body.
    :rtype: dict[str, Any]
    :raises HTTPException: With status 404 when the receipt does not exist.
    """
    receipt_body = receipt_service.retrieve_receipt(receipt_id)
    if receipt_body is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt not found: {receipt_id}",
        )

    return receipt_body


def _split_sieved_evidence(sieved_content: str) -> list[str]:
    """Split minimized sieve output into displayable evidence chunks.

    :param str sieved_content: Minimized outbound context string.
    :returns: Non-empty evidence chunks derived from the sieved content.
    :rtype: list[str]
    """
    if not sieved_content.strip():
        return []

    chunks = [chunk.strip() for chunk in sieved_content.split("\n") if chunk.strip()]
    return chunks or [sieved_content.strip()]


def _build_mock_answer(records: list[Record]) -> str:
    """Generate a deterministic mock answer from matched evidence records.

    :param list[Record] records: Retrieved memory records for the question.
    :returns: Mock answer string derived from record content heuristics.
    :rtype: str
    """
    for record in records:
        if record.classification == "property_ledger" and "Fido" in record.content:
            return "Fido was a dog owned by John Miller in 1908."

    primary = max(records, key=lambda record: record.confidence)
    lead_line = next(
        (line.strip() for line in primary.content.splitlines() if line.strip()),
        primary.title,
    )
    return f"Based on institutional records ({primary.title}), {lead_line}"


def _calculate_confidence(records: list[Record]) -> float:
    """Average record confidence for the matched evidence set.

    :param list[Record] records: Retrieved memory records for the question.
    :returns: Mean confidence rounded to two decimal places.
    :rtype: float
    """
    return round(sum(record.confidence for record in records) / len(records), 2)


def _generate_or_fetch_receipt(
    receipt_service: ReceiptService,
    records: list[Record],
    confidence: float,
    airlock_result: AirlockResult,
    sieved_evidence: list[str],
) -> dict[str, Any]:
    """Generate a receipt or return an existing receipt for identical evidence.

    :param ReceiptService receipt_service: Service used to create or fetch receipts.
    :param list[Record] records: Evidence records backing the answer.
    :param float confidence: Aggregated confidence score for the receipt.
    :param AirlockResult airlock_result: Successful airlock processing result for SDK metadata.
    :param list[str] sieved_evidence: Minimized evidence strings for persistence.
    :returns: Parsed forensic receipt JSON body.
    :rtype: dict[str, Any]
    :raises ReceiptDuplicateError: If a duplicate hash is detected but the
        existing receipt cannot be retrieved.
    """
    try:
        receipt = receipt_service.generate_forensic_receipt(
            records,
            confidence,
            airlock_result=airlock_result,
            sieved_evidence=sieved_evidence,
        )
    except ReceiptDuplicateError as exc:
        existing = receipt_service.retrieve_receipt_by_payload_hash(exc.payload_hash)
        if existing is None:
            raise
        return existing

    return json.loads(receipt.receipt_json)
