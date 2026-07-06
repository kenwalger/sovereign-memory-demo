"""FastAPI entrypoint for the Sovereign Memory Demo backend.

Exposes the ASGI application, startup lifecycle hooks that initialize the
memory store and ingest datasets, and a lightweight health-check endpoint.
"""

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sovereign_ledger import SovereignLedger
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.api import router
from app.config import (
    AIRLOCK_POLICY_PATH,
    DATASETS_PATH,
    MEMORY_STORE_PATH,
    SOVEREIGN_KEYS_PATH,
    SOVEREIGN_LEDGER_PATH,
)
from app.repositories.database import (
    create_engine_for_path,
    create_session_factory,
    init_schema,
)
from app.repositories.memory_repository import MemoryRepository
from app.sdk.boundary import OutboundContextProcessor, create_airlock_boundary
from app.services.dataset_service import DatasetService
from app.services.memory_service import MemoryService
from app.services.receipt_service import ReceiptService

_MISSING_SOVEREIGN_NODE_SECRET_MESSAGE = (
    "SOVEREIGN_NODE_SECRET is missing. Please declare this variable in your "
    "execution environment before launching."
)
"""str: Fail-fast startup message when the sovereign node secret is unset."""


def _require_sovereign_node_secret() -> None:
    """Fail fast when ``SOVEREIGN_NODE_SECRET`` is absent from the environment.

    :returns: None
    :rtype: None
    :raises RuntimeError: If ``SOVEREIGN_NODE_SECRET`` is not configured.
    """
    if not os.environ.get("SOVEREIGN_NODE_SECRET"):
        raise RuntimeError(_MISSING_SOVEREIGN_NODE_SECRET_MESSAGE)


def _bootstrap_memory_store() -> tuple[Engine, sessionmaker[Session]]:
    """Initialize the SQLite schema and ingest datasets on a worker thread.

    :returns: Configured SQLAlchemy engine and session factory.
    :rtype: tuple[Engine, sessionmaker[Session]]
    """
    engine = create_engine_for_path(MEMORY_STORE_PATH)
    init_schema(engine)
    session_factory = create_session_factory(engine)
    dataset_service = DatasetService(DATASETS_PATH, session_factory)
    dataset_service.initialize_datasets()
    return engine, session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize the schema and ingest datasets at application startup.

    Creates the SQLite engine, loads demo datasets, wires sovereign SDK
    components, and attaches service singletons to ``app.state``. Disposes the
    engine on shutdown.

    :param FastAPI app: FastAPI application whose ``state`` receives engine,
        session factory, repository, and service instances.
    :yields: None
    :rtype: None
    """
    _require_sovereign_node_secret()

    engine, session_factory = await asyncio.to_thread(_bootstrap_memory_store)

    memory_repository = MemoryRepository(session_factory)
    SOVEREIGN_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    ledger = SovereignLedger(str(SOVEREIGN_LEDGER_PATH))
    boundary = create_airlock_boundary(
        AIRLOCK_POLICY_PATH,
        SOVEREIGN_KEYS_PATH,
        ledger,
    )

    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.memory_repository = memory_repository
    app.state.memory_service = MemoryService(memory_repository)
    app.state.ledger = ledger
    app.state.outbound_processor = OutboundContextProcessor(boundary)
    app.state.receipt_service = ReceiptService(session_factory, ledger=ledger)

    yield

    ledger.close()
    engine.dispose()


def _resolve_allowed_origins() -> list[str]:
    """Build the CORS allow-list from local dev hosts and configured production origins.

    :returns: Distinct origin URLs permitted for cross-origin browser access.
    :rtype: list[str]
    """
    local_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    configured_origins = os.environ.get(
        "SOVEREIGN_ALLOWED_ORIGINS",
        "https://demo.sovereignsystems.io",
    )
    production_origins = [
        origin.strip()
        for origin in configured_origins.split(",")
        if origin.strip()
    ]
    return local_origins + production_origins


app = FastAPI(
    title="Sovereign Memory Demo",
    description=(
        "Reference implementation demonstrating that semantic retrieval "
        "and immutable institutional memory are not equivalent."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolve_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(router)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Return a lightweight service health checkpoint.

    :returns: Mapping with a ``status`` key set to ``"ok"``.
    :rtype: dict[str, str]
    """
    return {"status": "ok"}
