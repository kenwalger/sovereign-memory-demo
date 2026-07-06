# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Atomic receipt ID allocation using SQLite autoincrement `sequence` primary key on `Receipt`
- Non-blocking forensic receipt persistence via `asyncio.to_thread` in `POST /api/questions`
- Shared `SovereignLedger` handle injected into `AirlockBoundary` (eliminates dual-writer file locks)
- Frontend `formatErrorDetail` helper for structured FastAPI `detail` payloads (policy blocks, 422 validation)
- Sovereign SDK integration: `OutboundContextProcessor` wires sieve + airlock into `POST /api/questions`
- `backend/config/airlock_policy.yaml` deny rules for API keys and private key material
- `ReceiptService` ledger commits via `sovereign-sdk-ledger` with SDK telemetry metadata
- Policy-blocked responses return HTTP 400 with `{ error, message, warnings }` envelope
- Integration test for airlock policy rejection (`test_post_questions_policy_violation_returns_structured_400`)
- React + Vite frontend with quad-panel UI (`QuestionPanel`, `AnswerPanel`, `EvidencePanel`, `ReceiptPanel`)
- TypeScript API contracts and `frontend/src/services/api.ts` fetch client with TSDoc
- Comprehensive Sphinx-style docstrings across backend modules per `.cursorrules`
- Comprehensive TSDoc comments across frontend types, services, and components
- FastAPI API router with `POST /api/questions` and `GET /api/receipts/{receipt_id}`
- Unified question response contract: `answer`, `evidence`, `sources`, `receipt`
- `ReceiptService.retrieve_receipt` and `retrieve_receipt_by_payload_hash` lookup methods
- Integration test suite `backend/tests/test_api_routes.py` (6 HTTP lifecycle tests)
- `ReceiptService.generate_forensic_receipt` with deterministic SHA-256 payload hashing
- Forensic seal simulation (`app/receipts/seal.py`) mapping pre-sieve hash into signed metadata
- `ReceiptDuplicateError` guard against unique `payload_hash` index violations
- Unit test suite `backend/tests/test_receipt_service.py` (7 receipt lifecycle tests)
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

### Fixed

- Receipt ID race condition under concurrent requests (replaced `COUNT + 1` allocation)
- Ledger file handle leak from duplicate `SovereignLedger` instantiation in `create_airlock_boundary`
- Frontend `"[object Object]"` fallback when policy violation errors return structured `detail` objects
- Receipt retrieval `DetachedInstanceError` on `GET /api/receipts/{id}` by materializing JSON inside the session boundary
- Duplicate-hash receipt fallback now receives a parsed receipt body instead of a detached ORM instance

### Changed

- `.gitignore` now blocks `*.db`, `*.sqlite3`, and SQLite WAL/SHM sidecars (`*.db-shm`, `*.db-wal`, `*.sqlite3-shm`, `*.sqlite3-wal`) repository-wide
- `MemoryService.retrieve_context` offloads regex sanitization via `asyncio.to_thread`
- `MemoryService.assemble_source_attribution` offloads repository fallback lookups via `asyncio.to_thread`
- `_generate_or_fetch_receipt` declares explicit `AirlockResult` parameter typing
- `QuestionRequest.question` bounded to `max_length=1000` characters
- `MemoryRepository.search_records` escapes `%` and `_` wildcards in `LIKE` patterns
- `property_ledger_1908.txt` expanded with historical boilerplate, transaction tables, and administrative headers for sieve token-savings demos
- `frontend/.gitignore` blocks `*.tsbuildinfo` build artifacts
- `ReceiptMetadata` refactored to a TypeScript union (`SimulatedSealMetadata | SdkReceiptMetadata`)
- Removed unused `Evidence` ORM model, `Record.evidence_items` relationship, and dead `session_scope` utility
- `CORSMiddleware` mounted with local development and showcase origins
