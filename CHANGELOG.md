# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `MemoryRepository` with keyword search and document lookup (`search_records`, `get_document_by_id`)
- `MemoryService` async retrieval orchestration (`retrieve_context`, `assemble_source_attribution`)
- `SourceAttribution` provenance dataclass mapping records to parent documents
- Unit test suite `backend/tests/test_memory_service.py` (10 retrieval and attribution tests)
- MIT `LICENSE`, `CONTRIBUTING.md`, and `SECURITY.md` open-source governance scaffolding
- SQLAlchemy 2.0 relational models: `Document`, `Record`, `Evidence`, `Receipt`
- Unique index on `Receipt.payload_hash` for forensic cryptographic linkage
- `DatasetService` fail-fast ingestion engine with typed initialization errors
- Startup dataset load via FastAPI lifespan hook (`datasets/` → `memory_store/`)
- Reference demo dataset shipped under `datasets/` (accession, curator notes, ledger, photographs)
- Unit test suite `backend/tests/test_dataset_service.py` (11 ingestion and schema tests)
- Repository directory topography: `datasets/`, `memory_store/`, `backend/app/*`, `frontend/src/*`
- `backend/pyproject.toml` with Python 3.14+ target, hatchling build backend, and Sovereign SDK dependencies
- `uv` lockfile workflow (`backend/uv.lock`, `backend/.python-version`, `[dependency-groups]`)
- FastAPI application entrypoint (`backend/main.py`) with `GET /api/health` checkpoint
- Async health route integration test (`backend/tests/test_main.py`) using pytest and httpx
- Project tracking documents: `README.md`, `CHANGELOG.md`, `ROADMAP.md`
