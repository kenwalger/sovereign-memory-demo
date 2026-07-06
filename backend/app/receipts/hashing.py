"""Deterministic hashing helpers for forensic receipt payloads."""

from __future__ import annotations

import hashlib

from app.models import Record


def build_evidence_strings(evidence_records: list[Record]) -> list[str]:
    """Return sorted, normalized evidence strings for stable hashing.

    :param list[Record] evidence_records: Memory records whose content forms
        the forensic evidence set.
    :returns: Stripped, non-empty record contents sorted lexicographically.
    :rtype: list[str]
    """
    return sorted(record.content.strip() for record in evidence_records if record.content.strip())


def compute_payload_hash(evidence_strings: list[str]) -> str:
    """Compute the pre-sieve SHA-256 digest of unified evidence strings.

    :param list[str] evidence_strings: Normalized evidence strings joined for hashing.
    :returns: Lowercase hexadecimal SHA-256 digest of the unified payload.
    :rtype: str
    """
    unified_payload = "\n".join(evidence_strings)
    return hashlib.sha256(unified_payload.encode("utf-8")).hexdigest()
