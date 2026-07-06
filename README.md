# Sovereign Memory Demo

Canonical reference implementation of the [Sovereign Systems Specification](https://github.com/kenwalger/sovereign-memory-demo).

This application demonstrates that **semantic retrieval** and **immutable institutional memory** are not equivalent. Retrieval answers *"Can I find it?"* — memory answers *"Can I trust it?"*

**Production frontend target:** [sovereignplatform.dev/demos/memory](https://sovereignplatform.dev/demos/memory)

## Repository Layout

```text
sovereign-memory-demo/
├── README.md
├── CHANGELOG.md
├── ROADMAP.md
├── project_specs/          # Execution blueprint and technical specification
├── datasets/               # Raw source tracking data (shipped demo corpus)
├── memory_store/           # Local SQLite binary footprint (gitignored at runtime)
├── backend/
│   ├── pyproject.toml      # Python 3.14+ package (FastAPI)
│   ├── uv.lock             # uv dependency lockfile
│   ├── .python-version     # Python 3.14 pin for uv
│   ├── main.py             # Application entrypoint
│   ├── app/
│   │   ├── api/            # HTTP route handlers
│   │   ├── models/         # Pydantic / SQLAlchemy models
│   │   ├── services/       # Domain services
│   │   ├── repositories/   # SQLite persistence
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
| Frontend | Node.js 20+ (Phase 6)            |
| Storage  | SQLite (local `memory_store/`)   |

## Backend Quick Start

```bash
cd backend
uv sync --group dev
uv run uvicorn main:app --reload --port 8000
```

### API (Step 1)

| Endpoint      | Method | Response                          |
|---------------|--------|-----------------------------------|
| `/api/health` | GET    | `{"status": "ok"}`                |

### Run Tests

```bash
cd backend
uv run pytest
```

## Sovereign SDK Dependencies

The backend declares these platform primitives as required dependencies:

- `sovereign-sdk-core>=1.3.0`
- `sovereign-sdk-sieve>=1.3.0`
- `sovereign-sdk-ledger>=1.3.0`
- `sovereign-sdk-airlock>=1.4.0`

## Specifications

- [Execution Blueprint v3](project_specs/sovereign-memory-demo-execution-blueprint-v3.md)
- [Technical Specification v1](project_specs/sovereign-memory-demo-technical-spec-v1.md)

---

(c) 2026 — Ken W. Alger
