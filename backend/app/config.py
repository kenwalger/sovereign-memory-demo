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

AIRLOCK_POLICY_PATH = PROJECT_ROOT / "backend" / "config" / "airlock_policy.yaml"
"""Filesystem path to the outbound airlock YAML policy configuration.

:vartype: Path
"""

SOVEREIGN_KEYS_PATH = PROJECT_ROOT / "memory_store" / ".sovereign_keys"
"""Directory containing Ed25519 signing keys for forensic receipts.

:vartype: Path
"""

SOVEREIGN_LEDGER_PATH = PROJECT_ROOT / "memory_store" / "sovereign_audit.db"
"""SQLite database path for the append-only sovereign forensic ledger.

:vartype: Path
"""
