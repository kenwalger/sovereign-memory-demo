"""FastAPI entrypoint for the Sovereign Memory Demo backend."""

from fastapi import FastAPI

app = FastAPI(
    title="Sovereign Memory Demo",
    description=(
        "Reference implementation demonstrating that semantic retrieval "
        "and immutable institutional memory are not equivalent."
    ),
    version="0.1.0",
)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Return a lightweight service health checkpoint."""
    return {"status": "ok"}
