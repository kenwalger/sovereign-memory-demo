# Sovereign Memory Demo — Roadmap

Cross-referenced against [Technical Specification v1](project_specs/sovereign-memory-demo-technical-spec-v1.md) development workflow.

## Development Workflow

| Step | Milestone                              | Status      |
|------|----------------------------------------|-------------|
| 1    | Create repository structure            | **Done**    |
| 2    | Implement SQLite models                  | **Done**    |
| 3    | Implement dataset loader                 | **Done**    |
| 4    | Implement retrieval services             | **Done**    |
| 5    | Implement receipt generation             | **Done**    |
| 6    | Implement API routes                     | **Done**    |
| 7    | Implement React UI                       | **Done**    |
| 8    | Integrate SDK components                 | **Done**    |

## Phase 1 — Project Scaffolding

- [x] Directory topography (`datasets/`, `memory_store/`, `backend/app/*`, `frontend/src/*`)
- [x] `backend/pyproject.toml` (Python 3.14+, hatchling, SDK + production deps)
- [x] `uv` lockfile and environment workflow (`uv.lock`, `.python-version`)
- [x] FastAPI entrypoint with `/api/health`
- [x] pytest + httpx health route test stub
- [x] React + Vite frontend bootstrap

## Phase 2 — Data Layer

- [x] SQLite schema (`Document`, `Record`, `Evidence`, `Receipt`)
- [x] `Receipt.payload_hash` unique index for forensic linkage
- [x] Dataset loader with fail-fast validation (`DatasetService`)
- [x] Ship reference dataset (accession records, curator notes, property ledger, photograph catalog)
- [x] Open-source governance (`LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`)
- [x] Startup ingestion via FastAPI lifespan hook

## Phase 3 — Memory & Retrieval

- [x] `MemoryRepository` keyword search across ingested `Record` chunks
- [x] `MemoryService.retrieve_context` with query sanitization
- [x] `MemoryService.assemble_source_attribution` provenance mapping
- [x] Retrieval unit tests (`test_memory_service.py`)

## Phase 4 — Forensic Receipts

- [x] `ReceiptService.generate_forensic_receipt` with SHA-256 payload hashing
- [x] Forensic seal metadata simulation (`app/receipts/seal.py`)
- [x] Unique `payload_hash` duplicate protection
- [x] Receipt unit tests (`test_receipt_service.py`)
- [x] Full `sovereign-sdk-ledger` integration (Phase 7)

## Phase 5 — Evidence Rendering

- [x] Evidence assembly in answer workflow (`POST /api/questions`)
- [x] Source attribution exposed in API response
- [ ] Source document viewer API (`GET /api/sources/{id}`)

## Phase 6 — React UI

- [x] `QuestionPanel`, `AnswerPanel`, `EvidencePanel`, `ReceiptPanel`
- [x] `Home.tsx` quad-panel layout with loading, error, and empty states
- [x] TypeScript API types and fetch service with TSDoc
- [ ] Deploy to `sovereignplatform.dev/demos/memory`

## Phase 7 — SDK Integration

- [x] `sovereign-sdk-sieve` context minimisation
- [x] `sovereign-sdk-airlock` outbound policy check
- [x] Full query lifecycle: Ingestion → Retrieval → Minimisation → Airlock → Receipt

## Phase 8 — Documentation & Demo

- [ ] Screenshots and video walkthrough
- [ ] Conference-ready demonstration assets

## Style Guide Audit (`.cursorrules` Compliance)

- [x] CPU-bound question sanitization offloaded via `asyncio.to_thread` in `MemoryService.retrieve_context`
- [x] Explicit `AirlockResult` type annotation on `_generate_or_fetch_receipt` route helper

## Production Robustness (PR Final Polish)

- [x] Atomic receipt ID allocation via SQLite autoincrement sequence
- [x] Non-blocking receipt persistence via `asyncio.to_thread` in `POST /api/questions`
- [x] Singleton `SovereignLedger` handle injected into airlock boundary (no dual-writer leak)
- [x] Frontend structured FastAPI error detail rendering (policy blocks and validation errors)
- [x] Gitignore hardening for `*.db` / `*.sqlite3` artifacts
- [x] Receipt retrieval materialized inside session boundary (fixes `DetachedInstanceError`)
- [x] Expanded `property_ledger_1908.txt` boilerplate for Prose Tax token savings demo
- [x] Frontend `*.tsbuildinfo` gitignore and artifact cleanup
