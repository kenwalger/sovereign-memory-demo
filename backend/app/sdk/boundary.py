"""Sovereign SDK outbound context processing adapters."""

from __future__ import annotations

from pathlib import Path

from sovereign_airlock import AirlockBoundary, AirlockResult, normalize_raw
from sovereign_ledger import SovereignLedger


def build_unified_context(question: str, evidence: list[str]) -> str:
    """Combine a user question and evidence strings into one outbound payload.

    :param str question: Sanitized user question text.
    :param list[str] evidence: Retrieved evidence strings from memory records.
    :returns: Unified newline-delimited outbound context payload.
    :rtype: str
    """
    parts = [question.strip(), *[chunk.strip() for chunk in evidence if chunk.strip()]]
    return "\n".join(parts)


def create_airlock_boundary(
    policy_path: Path,
    signing_key_path: Path,
    ledger_path: Path,
) -> AirlockBoundary:
    """Construct an :class:`AirlockBoundary` wired to local policy, keys, and ledger.

    :param Path policy_path: Filesystem path to the YAML airlock policy file.
    :param Path signing_key_path: Directory for Ed25519 signing key material.
    :param Path ledger_path: SQLite path for the append-only sovereign ledger.
    :returns: Configured airlock boundary ready for outbound processing.
    :rtype: AirlockBoundary
    :raises AirlockConfigurationError: If the policy file is missing or invalid.
    """
    signing_key_path.mkdir(parents=True, exist_ok=True)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger = SovereignLedger(str(ledger_path))
    return AirlockBoundary(policy_path, signing_key_path, ledger=ledger)


class OutboundContextProcessor:
    """Run sieve and airlock governance over retrieved institutional memory context.

    :ivar AirlockBoundary _boundary: Configured outbound governance boundary.
    """

    def __init__(self, boundary: AirlockBoundary) -> None:
        """Initialize the processor with a configured airlock boundary.

        :param AirlockBoundary boundary: Outbound governance boundary instance.
        :returns: None
        :rtype: None
        """
        self._boundary = boundary

    async def process(self, question: str, evidence: list[str]) -> AirlockResult:
        """Minimize and inspect a unified outbound context payload.

        :param str question: User question associated with the outbound payload.
        :param list[str] evidence: Retrieved evidence strings joined into the payload.
        :returns: Sieved content, telemetry, signed receipt, and policy warnings.
        :rtype: AirlockResult
        :raises AirlockPolicyViolation: If a configured deny rule blocks the payload.
        """
        raw_context = build_unified_context(question, evidence)
        payload = normalize_raw(raw_context, source="sovereign-memory-demo")
        return await self._boundary.process(payload)
