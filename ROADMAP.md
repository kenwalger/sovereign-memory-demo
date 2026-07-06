# Sovereign Memory Demo — Roadmap

Cross-referenced against [Technical Specification v1](project_specs/sovereign-memory-demo-technical-spec-v1.md) development workflow.

## Development Workflow

| Step | Milestone                              | Status      |
|------|----------------------------------------|-------------|
| 1    | Create repository structure            | **Done**    |
| 2    | Implement SQLite models                  | **Done**    |
| 3    | Implement dataset loader                 | **Done**    |
| 4    | Implement retrieval services             | **Done**    |
| 5    | Implement receipt generation             | Pending     |
| 6    | Implement API routes                     | Pending     |
| 7    | Implement React UI                       | Pending     |
| 8    | Integrate SDK components                 | Pending     |

## Phase 1 — Project Scaffolding

- [x] Directory topography (`datasets/`, `memory_store/`, `backend/app/*`, `frontend/src/*`)
- [x] `backend/pyproject.toml` (Python 3.14+, hatchling, SDK + production deps)
- [x] `uv` lockfile and environment workflow (`uv.lock`, `.python-version`)
- [x] FastAPI entrypoint with `/api/health`
- [x] pytest + httpx health route test stub
- [ ] React + Vite frontend bootstrap

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

- [ ] `ReceiptService` generate / store / retrieve
- [ ] Ledger linkage via `sovereign-sdk-ledger`

## Phase 5 — Evidence Rendering

- [ ] Evidence assembly in answer workflow
- [ ] Source document viewer API

## Phase 6 — React UI

- [ ] QuestionPanel, AnswerPanel, EvidencePanel, ReceiptPanel, SourceViewer
- [ ] Deploy to `sovereignplatform.dev/demos/memory`

## Phase 7 — SDK Integration

- [ ] `sovereign-sdk-sieve` context minimisation
- [ ] `sovereign-sdk-airlock` outbound policy check
- [ ] Full query lifecycle: Ingestion → Retrieval → Minimisation → Airlock → Receipt

## Phase 8 — Documentation & Demo

- [ ] Screenshots and video walkthrough
- [ ] Conference-ready demonstration assets
