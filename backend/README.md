# Sovereign Memory Demo — Backend

Python 3.14+ FastAPI backend for the Sovereign Memory Demo reference implementation.

## Requirements

- [uv](https://docs.astral.sh/uv/) (package manager, lockfile, and environment)
- Python 3.14 or newer (managed automatically by `uv`)

## Setup

```bash
cd backend
uv sync --group dev
```

This creates `.venv/`, installs locked dependencies from `uv.lock`, and installs the backend package in editable mode.

On startup the backend initializes the SQLite schema and ingests the
reference dataset from `../datasets/` into `../memory_store/memory.db`.

## Running the application

### Required environment variable

`SOVEREIGN_NODE_SECRET` is **required** for local cryptographic ledger operations.
The application fails fast at lifespan startup when this variable is missing:

```text
RuntimeError: SOVEREIGN_NODE_SECRET is missing. Please declare this variable in your execution environment before launching.
```

Set the variable in your shell before running Uvicorn or pytest against a live SDK stack.

**Windows PowerShell**

```powershell
$env:SOVEREIGN_NODE_SECRET="your-secret-key"
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Linux / macOS**

```bash
export SOVEREIGN_NODE_SECRET="your-secret-key"
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Linux / macOS (inline)**

```bash
SOVEREIGN_NODE_SECRET="your-secret-key" uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Identity key material is written to `../memory_store/.sovereign_keys/` at runtime.
That directory and all `*.pem` files are gitignored and must never be committed.

## Data Model

| Entity     | Purpose                                        |
|------------|------------------------------------------------|
| `Document` | Source file metadata from `datasets/`          |
| `Record`   | Extracted semantic chunk for retrieval         |
| `Receipt`  | Forensic envelope (`payload_hash` unique index)|

## Retrieval

| Component          | Method                              |
|--------------------|-------------------------------------|
| `MemoryRepository` | `search_records`, `get_document_by_id` |
| `MemoryService`    | `retrieve_context`, `assemble_source_attribution` |
| `ReceiptService`   | `generate_forensic_receipt` |

## SDK Integration

| Component | Package | Role |
|-----------|---------|------|
| `OutboundContextProcessor` | `sovereign-sdk-airlock` | Sieve + outbound policy on unified context |
| `SovereignLedger` | `sovereign-sdk-ledger` | Append-only forensic receipt commits |
| `airlock_policy.yaml` | `backend/config/` | Deny rules for API keys and private key material |

Policy violations on `POST /api/questions` return HTTP `400` with `{ error, message, warnings }`.

Receipt IDs are allocated atomically via SQLite autoincrement (`Receipt.sequence`).
Forensic receipt persistence runs in `asyncio.to_thread` to avoid blocking the event loop.
A single `SovereignLedger` handle is shared between `AirlockBoundary` and `ReceiptService`.

Cross-origin browser requests are supported via `CORSMiddleware`. Production
origins are read from `SOVEREIGN_ALLOWED_ORIGINS` (comma-separated, default
`https://sovereignplatform.dev`). Local Vite dev hosts are included only when
`SOVEREIGN_ENV=development` is set explicitly.

## Test

`SOVEREIGN_NODE_SECRET` is injected automatically by the pytest suite. For ad-hoc
local commands, export the variable using the shell examples in
[Running the application](#running-the-application) above.

```bash
uv run pytest
```

## API

| Endpoint       | Method | Description              |
|----------------|--------|--------------------------|
| `/api/health`  | GET    | Service health checkpoint |

### Questions

```http
POST /api/questions
```

```json
{
  "question": "Who is Fido?"
}
```

Response keys: `answer`, `evidence`, `sources`, `receipt`

### Receipts

```http
GET /api/receipts/{receipt_id}
```

## Dependency management

```bash
# Refresh lockfile after pyproject.toml changes
uv lock

# Sync environment to lockfile
uv sync --group dev
```
