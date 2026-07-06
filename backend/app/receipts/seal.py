"""Tamper-evident seal simulation for airlock and ledger provenance linkage."""

from __future__ import annotations

import hashlib


def build_forensic_seal(payload_hash: str, receipt_id: str) -> dict[str, str]:
    """Simulate sovereign-sdk-airlock and sovereign-sdk-ledger forensic metadata.

    Maps the pre-sieve payload hash into a signed metadata envelope that can be
    persisted alongside the relational receipt row for audit replay.

    :param str payload_hash: Deterministic SHA-256 hash of the evidence payload.
    :param str receipt_id: Forensic receipt identifier used in signature material.
    :returns: Metadata envelope containing signature, seal algorithm, ledger
        reference, and airlock boundary labels.
    :rtype: dict[str, str]
    """
    signature_material = f"{receipt_id}:{payload_hash}".encode("utf-8")
    signature = hashlib.sha256(signature_material).hexdigest()
    ledger_reference = f"LEDGER-{payload_hash[:8].upper()}"

    return {
        "payload_hash": payload_hash,
        "signature": signature,
        "seal_algorithm": "sha256-sim",
        "ledger_reference": ledger_reference,
        "airlock_boundary": "outbound-answer-governance",
    }
