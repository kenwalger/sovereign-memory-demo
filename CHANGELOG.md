# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Repository directory topography: `datasets/`, `memory_store/`, `backend/app/*`, `frontend/src/*`
- `backend/pyproject.toml` with Python 3.14+ target, hatchling build backend, and Sovereign SDK dependencies
- `uv` lockfile workflow (`backend/uv.lock`, `backend/.python-version`, `[dependency-groups]`)
- FastAPI application entrypoint (`backend/main.py`) with `GET /api/health` checkpoint
- Async health route integration test (`backend/tests/test_main.py`) using pytest and httpx
- Project tracking documents: `README.md`, `CHANGELOG.md`, `ROADMAP.md`
