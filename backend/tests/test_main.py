"""Integration tests for the FastAPI application entrypoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import _require_sovereign_node_secret, app


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok() -> None:
    """Verify the async health route returns the expected structured status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "secret_value",
    [None, "", "   ", "\t\n", "  valid-secret  "],
)
def test_require_sovereign_node_secret_validation(
    monkeypatch: pytest.MonkeyPatch,
    secret_value: str | None,
) -> None:
    """Missing, blank, and whitespace-only secrets fail fast; trimmed values pass."""
    monkeypatch.delenv("SOVEREIGN_NODE_SECRET", raising=False)
    if secret_value is not None:
        monkeypatch.setenv("SOVEREIGN_NODE_SECRET", secret_value)

    if secret_value is None or not secret_value.strip():
        with pytest.raises(RuntimeError, match="SOVEREIGN_NODE_SECRET is missing"):
            _require_sovereign_node_secret()
    else:
        _require_sovereign_node_secret()

