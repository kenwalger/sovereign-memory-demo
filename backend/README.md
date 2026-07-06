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

## Run

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API

| Endpoint       | Method | Description              |
|----------------|--------|--------------------------|
| `/api/health`  | GET    | Service health checkpoint |

### Health response

```json
{
  "status": "ok"
}
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
