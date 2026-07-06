"""Integration tests for the public HTTP API routes."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sovereign_ledger import SovereignLedger

from app.repositories.database import create_engine_for_path, create_session_factory, init_schema
from app.repositories.memory_repository import MemoryRepository
from app.sdk.boundary import OutboundContextProcessor, create_airlock_boundary
from app.services.dataset_service import DatasetService
from app.services.memory_service import MemoryService
from app.services.receipt_service import ReceiptService
from main import app


@pytest.fixture
async def api_client(
    memory_store_path,
    datasets_path,
    airlock_policy_path,
    sovereign_keys_path,
    sovereign_ledger_path,
):
    """Provide an async HTTP client with an isolated ingested corpus."""
    engine = create_engine_for_path(memory_store_path)
    init_schema(engine)
    session_factory = create_session_factory(engine)
    dataset_service = DatasetService(datasets_path, session_factory)
    await dataset_service.load_dataset()

    memory_repository = MemoryRepository(session_factory)
    ledger = SovereignLedger(str(sovereign_ledger_path))
    boundary = create_airlock_boundary(
        airlock_policy_path,
        sovereign_keys_path,
        sovereign_ledger_path,
    )

    app.state.session_factory = session_factory
    app.state.memory_repository = memory_repository
    app.state.memory_service = MemoryService(memory_repository)
    app.state.ledger = ledger
    app.state.outbound_processor = OutboundContextProcessor(boundary)
    app.state.receipt_service = ReceiptService(session_factory, ledger=ledger)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    ledger.close()


@pytest.mark.asyncio
async def test_post_questions_fido_completes_full_pipeline(api_client: AsyncClient) -> None:
    """A targeted keyword completes retrieval, attribution, and receipt generation."""
    response = await api_client.post(
        "/api/questions",
        json={"question": "Who is Fido?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert "evidence" in body
    assert "sources" in body
    assert "receipt" in body
    assert "Fido" in body["answer"]
    assert len(body["evidence"]) >= 1
    assert len(body["sources"]) >= 1
    assert body["receipt"] is not None
    assert body["receipt"]["receipt_id"].startswith("FR-")
    assert body["receipt"]["metadata"]["payload_hash"]
    assert body["receipt"]["metadata"]["sieved_tokens"] >= 0
    assert any(
        source["document_filename"] == "property_ledger_1908.txt"
        for source in body["sources"]
    )


@pytest.mark.asyncio
async def test_post_questions_unmatched_returns_empty_context(api_client: AsyncClient) -> None:
    """Unmatched questions return empty evidence and sources without crashing."""
    response = await api_client.post(
        "/api/questions",
        json={"question": "xyzzy unobtainium"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"]
    assert body["evidence"] == []
    assert body["sources"] == []
    assert body["receipt"] is None


@pytest.mark.asyncio
async def test_post_questions_policy_violation_returns_structured_400(
    api_client: AsyncClient,
) -> None:
    """Restricted credential strings are blocked by airlock policy without crashing."""
    response = await api_client.post(
        "/api/questions",
        json={"question": "Who is Fido? api_key=sk-live-RESTRICTEDCREDENTIAL12345"},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"] == "policy_blocked"
    assert detail["message"]
    assert isinstance(detail["warnings"], list)


@pytest.mark.asyncio
async def test_get_receipt_returns_saved_transaction_block(api_client: AsyncClient) -> None:
    """A saved receipt can be fetched by its forensic identifier."""
    question_response = await api_client.post(
        "/api/questions",
        json={"question": "Who is Fido?"},
    )
    receipt_id = question_response.json()["receipt"]["receipt_id"]

    response = await api_client.get(f"/api/receipts/{receipt_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["receipt_id"] == receipt_id
    assert body["metadata"]["payload_hash"]
    assert body["evidence"]


@pytest.mark.asyncio
async def test_get_receipt_missing_returns_404(api_client: AsyncClient) -> None:
    """Unknown receipt identifiers return a clean HTTP 404."""
    response = await api_client.get("/api/receipts/FR-9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Receipt not found: FR-9999"


@pytest.mark.asyncio
async def test_post_questions_rejects_empty_question(api_client: AsyncClient) -> None:
    """Empty question payloads are rejected by request validation."""
    response = await api_client.post("/api/questions", json={"question": "   "})

    assert response.status_code == 422
