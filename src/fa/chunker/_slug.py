"""Deterministic slug helper for chunk anchors.

Kept private because the exact algorithm is an implementation detail of
how anchors are computed; downstream code should treat ``Chunk.anchor``
as an opaque identifier.
"""

from __future__ import annotations

import re

_WHITESPACE_RUN = re.compile(r"\s+", flags=re.UNICODE)
_NON_WORD = re.compile(r"[^\w-]+", flags=re.UNICODE)
_HYPHEN_RUN = re.compile(r"-{2,}")


def slugify(text: str) -> str:
    """Lower-case, Unicode-aware, hyphen-separated slug.

    - Collapses runs of whitespace into a single hyphen.
    - Drops characters that are neither word characters (Unicode-aware,
      so Cyrillic letters survive) nor hyphens.
    - Collapses repeated hyphens and trims leading/trailing hyphens
      and underscores.
    - Returns an empty string for input that is empty or contains no
      retainable characters; callers fall back to a deterministic
      placeholder in that case.
    """

    casefolded = text.strip().casefold()
    hyphenated = _WHITESPACE_RUN.sub("-", casefolded)
    cleaned = _NON_WORD.sub("", hyphenated)
    collapsed = _HYPHEN_RUN.sub("-", cleaned)
    return collapsed.strip("-_")


__all__ = ["slugify"]
