"""Deterministic hashing helpers for forensic receipt payloads."""

from __future__ import annotations

import hashlib

from app.models import Record


def build_evidence_strings(evidence_records: list[Record]) -> list[str]:
    """Return sorted, normalized evidence strings for stable hashing."""
    return sorted(record.content.strip() for record in evidence_records if record.content.strip())


def compute_payload_hash(evidence_strings: list[str]) -> str:
    """Compute the pre-sieve SHA-256 digest of unified evidence strings."""
    unified_payload = "\n".join(evidence_strings)
    return hashlib.sha256(unified_payload.encode("utf-8")).hexdigest()
