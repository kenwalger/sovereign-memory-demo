"""Shared filters for stripping creator attribution from searchable content."""

from __future__ import annotations

import re

AUTHOR_FOOTER_LINE_PATTERN = re.compile(
    r"^\s*(?:\(c\)|copyright|author(?:\s+signature)?|created by|curated by|"
    r"ken\s+w\.?\s*alger|system metrics?)\b.*$",
    re.IGNORECASE | re.MULTILINE,
)
"""re.Pattern[str]: Pattern matching architectural author or system footer lines."""

AUTHOR_SIGNATURE_TERMS = frozenset({
    "alger",
    "architect",
    "attribution",
    "author",
    "copyright",
    "creator",
    "curated",
    "footer",
    "ken",
    "kenal",
    "kenw",
    "metrics",
    "profile",
    "signature",
    "signed",
})
"""frozenset[str]: Tokens that must never participate in keyword search intersection."""


def strip_author_footers(text: str) -> str:
    """Remove creator attribution and system footer lines from source text.

    :param str text: Raw dataset or query text.
    :returns: Text with architectural attribution lines removed.
    :rtype: str
    """
    return AUTHOR_FOOTER_LINE_PATTERN.sub(" ", text).strip()
