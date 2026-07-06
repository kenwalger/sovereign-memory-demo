"""Application path configuration."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATASETS_PATH = PROJECT_ROOT / "datasets"
MEMORY_STORE_PATH = PROJECT_ROOT / "memory_store"
