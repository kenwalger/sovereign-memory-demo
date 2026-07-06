# Sovereign Memory Demo

Canonical reference implementation of the [Sovereign Systems Specification](https://github.com/kenwalger/sovereign-memory-demo).

This application demonstrates that **semantic retrieval** and **immutable institutional memory** are not equivalent. Retrieval answers *"Can I find it?"* — memory answers *"Can I trust it?"*

**Production frontend target:** [sovereignplatform.dev/demos/memory](https://sovereignplatform.dev/demos/memory)

## Repository Layout

```text
sovereign-memory-demo/
├── LICENSE, CONTRIBUTING.md, SECURITY.md
├── README.md, CHANGELOG.md, ROADMAP.md
├── project_specs/          # Execution blueprint and technical specification
├── datasets/               # Raw source tracking data (shipped demo corpus)
├── memory_store/           # Local SQLite binary footprint (gitignored at runtime)
├── backend/
│   ├── pyproject.toml      # Python 3.14+ package (FastAPI)
│   ├── uv.lock             # uv dependency lockfile
│   ├── .python-version     # Python 3.14 pin for uv
│   ├── main.py             # Application entrypoint (startup ingestion)
│   ├── app/
│   │   ├── api/            # HTTP route handlers
│   │   ├── models/         # SQLAlchemy relational models
│   │   ├── services/       # DatasetService and domain services
│   │   ├── repositories/   # SQLite engine and session factory
│   │   ├── receipts/       # Forensic receipt assembly
│   │   └── sdk/            # Sovereign SDK adapters
│   └── tests/
└── frontend/
    └── src/
        ├── components/
        ├── pages/
        ├── services/
        └── types/
```

## Requirements

| Layer    | Runtime                          |
|----------|----------------------------------|
| Backend  | Python **3.14+**, [uv](https://docs.astral.sh/uv/) |
| Frontend | Node.js 20+, npm, Vite |
| Storage  | SQLite (local `memory_store/`)   |

## Backend Quick Start

### Local setup

Install dependencies from the backend package root:

```bash
cd backend
uv sync --group dev
```

### Required environment variable

`SOVEREIGN_NODE_SECRET` is **required** for local cryptographic ledger operations.
The backend enforces a fail-fast startup invariant: if this variable is absent,
the server raises a `RuntimeError` and refuses to launch. No default secret is
injected by the application.

Declare the variable in your shell **before** starting Uvicorn.

**Windows PowerShell**

```powershell
cd backend
$env:SOVEREIGN_NODE_SECRET="your-secret-key"
uv run uvicorn main:app --reload --port 8000
```

**Linux / macOS (bash, zsh)**

```bash
cd backend
export SOVEREIGN_NODE_SECRET="your-secret-key"
uv run uvicorn main:app --reload --port 8000
```

**Linux / macOS (inline, single command)**

```bash
cd backend
SOVEREIGN_NODE_SECRET="your-secret-key" uv run uvicorn main:app --reload --port 8000
```

On startup the backend initializes the SQLite schema and ingests the
reference dataset from `datasets/` into `memory_store/memory.db`.
Cryptographic identity keys under `memory_store/.sovereign_keys/` are gitignored and must never be committed.

### API (Step 6)

| Endpoint                  | Method | Description |
|---------------------------|--------|-------------|
| `/api/health`             | GET    | Service health checkpoint |
| `/api/questions`          | POST   | Question → answer → evidence → receipt |
| `/api/receipts/{id}`      | GET    | Fetch forensic receipt by ID |

#### `POST /api/questions` response keys

`answer`, `evidence`, `sources`, `receipt`

Policy-blocked payloads return HTTP `400` with `{ "error": "policy_blocked", "message": "...", "warnings": [] }`.

## SDK Integration (Step 8)

The question lifecycle runs retrieval, then sieve + airlock governance over the unified outbound context (question + evidence), then forensic receipt generation:

```text
Ingestion → Retrieval → Minimisation → Outbound Airlock → Immutable Forensic Receipt
```

| Component | Package | Role |
|-----------|---------|------|
| `OutboundContextProcessor` | `sovereign-sdk-airlock` | Policy evaluation + sieve orchestration |
| `SovereignLedger` | `sovereign-sdk-ledger` | Append-only forensic receipt commits |
| `airlock_policy.yaml` | local config | Deny rules for credentials and key material |

## Frontend Quick Start

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` with the backend running on port `8000`.
The Vite dev server proxies `/api` requests to the backend.
The backend also mounts `CORSMiddleware` for direct cross-origin access during showcase deployments.

### Panels

| Component | Purpose |
|-----------|---------|
| `QuestionPanel` | Prompt input and query submission |
| `AnswerPanel` | Mock natural-language answer |
| `EvidencePanel` | Raw evidence chunks and source attribution |
| `ReceiptPanel` | Forensic receipt JSON envelope |

### Run Tests

```bash
cd backend
uv run pytest
```

## Data Model

| Entity     | Purpose                                              |
|------------|------------------------------------------------------|
| `Document` | Source file metadata ingested from `datasets/`       |
| `Record`   | Extracted semantic chunk ready for retrieval         |
| `Receipt`  | Forensic envelope (`sequence` autoincrement PK, `payload_hash` unique index)|

## Retrieval Layer

| Component | Method | Purpose |
|-----------|--------|---------|
| `MemoryRepository` | `search_records(query, limit=3)` | Keyword matching across `Record` title/content |
| `MemoryRepository` | `get_document_by_id(doc_id)` | Upstream source document lookup |
| `MemoryService` | `retrieve_context(question)` | Async sanitized query orchestration |
| `MemoryService` | `assemble_source_attribution(records)` | Record → Document provenance mapping |
| `ReceiptService` | `generate_forensic_receipt(records, confidence)` | SHA-256 sealed receipt persistence |

## Reference Dataset

Shipped under `datasets/`:

- `accession_records.json`
- `curator_notes.md`
- `property_ledger_1908.txt` — verbose 1908 household ledger with real estate transaction tables and administrative boilerplate (ideal for Prose Tax token-savings demos)
- `photograph_catalog.json`

**Demo query for token optimization:** *"Summarize all real estate transactions and properties for the John Miller household in 1908"*

## Sovereign SDK Dependencies

The backend declares these platform primitives as required dependencies:

- `sovereign-sdk-core>=1.3.0`
- `sovereign-sdk-sieve>=1.3.0`
- `sovereign-sdk-ledger>=1.3.0`
- `sovereign-sdk-airlock>=1.4.0`

## Specifications

- [Execution Blueprint v3](project_specs/sovereign-memory-demo-execution-blueprint-v3.md)
- [Technical Specification v1](project_specs/sovereign-memory-demo-technical-spec-v1.md)

## Contributing & Security

- See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- See [SECURITY.md](SECURITY.md) for vulnerability disclosure

---

(c) 2026 — Ken W. Alger
