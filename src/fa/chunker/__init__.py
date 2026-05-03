"""Deterministic chunker package for the v0.1 Mechanical Wiki.

Public surface (stable per ADR-5 §Decision):

- :data:`CHUNKER_VERSION` — composite version string written into the
  storage ``meta`` table per ADR-4 §Cache Invalidation. Bump on any
  algorithm or dependency change so SQLite rows can be re-extracted
  on next access.
- :class:`Chunk` — frozen dataclass produced by every chunker. Schema
  matches ADR-4 §Decision plus the 2026-04-29 provenance amendment
  and the matching ADR-5 ``Chunk`` amendment.
- :class:`Chunker` — Protocol every concrete chunker implements.
- :class:`CompositeChunker` — per-extension delegating chunker used
  as the default entry point.
- :func:`default_chunker` — convenience factory returning a
  :class:`CompositeChunker`.
- :class:`MarkdownChunker`, :class:`PlainTextChunker` — concrete
  per-format chunkers exposed for direct use and testing.
"""

from __future__ import annotations

from fa.chunker.composite import CompositeChunker, default_chunker
from fa.chunker.markdown import MarkdownChunker
from fa.chunker.plaintext import PlainTextChunker
from fa.chunker.types import Chunk, Chunker

# Composite "<algorithm>+<deps>" string. The first segment is the
# chunker package's own algorithm revision; the second documents which
# concrete chunkers participate in this build (markdown-only for the
# v0.1 first slice; ctags will extend it to "md+ctags" in a follow-up).
CHUNKER_VERSION = "0.1.0+md-only.1"

__all__ = [
    "CHUNKER_VERSION",
    "Chunk",
    "Chunker",
    "CompositeChunker",
    "MarkdownChunker",
    "PlainTextChunker",
    "default_chunker",
]
