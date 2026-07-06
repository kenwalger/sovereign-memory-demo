"""FastAPI entrypoint for the Sovereign Memory Demo backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import DATASETS_PATH, MEMORY_STORE_PATH
from app.repositories.database import (
    create_engine_for_path,
    create_session_factory,
    init_schema,
)
from app.services.dataset_service import DatasetService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize the schema and ingest datasets at application startup."""
    engine = create_engine_for_path(MEMORY_STORE_PATH)
    init_schema(engine)
    session_factory = create_session_factory(engine)
    dataset_service = DatasetService(DATASETS_PATH, session_factory)
    await dataset_service.load_dataset()

    app.state.engine = engine
    app.state.session_factory = session_factory

    yield

    engine.dispose()


app = FastAPI(
    title="Sovereign Memory Demo",
    description=(
        "Reference implementation demonstrating that semantic retrieval "
        "and immutable institutional memory are not equivalent."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Return a lightweight service health checkpoint."""
    return {"status": "ok"}
