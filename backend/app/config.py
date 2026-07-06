"""Application path configuration.

Defines filesystem paths for demo datasets and the SQLite memory store,
resolved relative to the repository project root.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
"""Absolute path to the repository project root.

:vartype: Path
"""

DATASETS_PATH = PROJECT_ROOT / "datasets"
"""Directory containing demo dataset source files for ingestion.

:vartype: Path
"""

MEMORY_STORE_PATH = PROJECT_ROOT / "memory_store"
"""Directory where the SQLite memory store database is persisted.

:vartype: Path
"""
