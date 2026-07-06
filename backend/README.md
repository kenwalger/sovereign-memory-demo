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

## Data Model

| Entity     | Purpose                                        |
|------------|------------------------------------------------|
| `Document` | Source file metadata from `datasets/`          |
| `Record`   | Extracted semantic chunk for retrieval         |
| `Evidence` | Verified excerpt for a query lifecycle         |
| `Receipt`  | Forensic envelope (`payload_hash` unique index)|

## Retrieval

| Component          | Method                              |
|--------------------|-------------------------------------|
| `MemoryRepository` | `search_records`, `get_document_by_id` |
| `MemoryService`    | `retrieve_context`, `assemble_source_attribution` |
| `ReceiptService`   | `generate_forensic_receipt` |

## Run

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
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

## Test

```bash
uv run pytest
```

## Dependency management

```bash
# Refresh lockfile after pyproject.toml changes
uv lock

# Sync environment to lockfile
uv sync --group dev
```
