"""FastAPI entrypoint for the Sovereign Memory Demo backend.

Exposes the ASGI application, startup lifecycle hooks that initialize the
memory store and ingest datasets, and a lightweight health-check endpoint.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import router
from app.config import DATASETS_PATH, MEMORY_STORE_PATH
from app.repositories.database import (
    create_engine_for_path,
    create_session_factory,
    init_schema,
)
from app.repositories.memory_repository import MemoryRepository
from app.services.dataset_service import DatasetService
from app.services.memory_service import MemoryService
from app.services.receipt_service import ReceiptService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize the schema and ingest datasets at application startup.

    Creates the SQLite engine, loads demo datasets, and attaches service
    singletons to ``app.state``. Disposes the engine on shutdown.

    :param FastAPI app: FastAPI application whose ``state`` receives engine,
        session factory, repository, and service instances.
    :yields: None
    :rtype: None
    """
    engine = create_engine_for_path(MEMORY_STORE_PATH)
    init_schema(engine)
    session_factory = create_session_factory(engine)
    dataset_service = DatasetService(DATASETS_PATH, session_factory)
    await dataset_service.load_dataset()

    memory_repository = MemoryRepository(session_factory)
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.memory_repository = memory_repository
    app.state.memory_service = MemoryService(memory_repository)
    app.state.receipt_service = ReceiptService(session_factory)

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

app.include_router(router)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Return a lightweight service health checkpoint.

    :returns: Mapping with a ``status`` key set to ``"ok"``.
    :rtype: dict[str, str]
    """
    return {"status": "ok"}
