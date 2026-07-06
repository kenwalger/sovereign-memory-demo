# Contributing to Sovereign Memory Demo

Thank you for your interest in contributing to the canonical reference
implementation of the Sovereign Systems Specification.

## Getting Started

1. Fork the repository and clone your fork.
2. Install [uv](https://docs.astral.sh/uv/).
3. Set up the backend environment:

   ```bash
   cd backend
   uv sync --group dev
   ```

4. Run the test suite before making changes:

   ```bash
   uv run pytest
   ```

## Development Guidelines

- Target **Python 3.14+** for all backend code.
- Use `uv` exclusively for dependency management and lockfile updates.
- Follow PEP 8 and include strict type hints on all public interfaces.
- Write `pytest` coverage for new services, repositories, and dataset loaders.
- Prefer fail-fast validation at startup over silent data coercion.
- Wrap disk-bound or CPU-heavy work in `asyncio.to_thread` inside async paths.

## Pull Request Process

1. Create a focused branch from `main`.
2. Update `CHANGELOG.md` under `[Unreleased]` for user-visible changes.
3. Ensure all tests pass: `uv run pytest`.
4. Open a pull request with a clear description of the problem and solution.
5. Reference any related specification sections in `project_specs/`.

## Code of Conduct

Be respectful, constructive, and precise. This project demonstrates
institutional memory and provenance — our collaboration should reflect
the same standards of clarity and accountability.
