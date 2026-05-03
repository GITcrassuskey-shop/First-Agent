"""Chunker public types — :class:`Chunk` dataclass and :class:`Chunker` Protocol.

Schema mirrors `ADR-5 §Decision` plus the
`ADR-5 amendment 2026-04-29 — Chunk dataclass extension for doc-level metadata`,
and aligns with the storage contract in `ADR-4 §Decision` plus the
`ADR-4 amendment 2026-04-29 — chunks schema extension for provenance`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Chunk:
    """One indexed unit produced by a :class:`Chunker` over a source file.

    Field semantics — short version (full rationale lives in ADR-5 / ADR-4):

    - ``path`` — source file path. Caller decides absolute vs.
      repo-relative; the chunker only stringifies what it is given.
    - ``anchor`` — slugified heading or symbol name; stable identifier
      inside ``path``. For Markdown chunks: slug of the chunk's own
      heading (or filename stem when the file has no headings). For
      single-chunk files: filename slug.
    - ``parent_title`` — frontmatter ``title:`` if present, else the
      first H1's text, else the filename stem (Markdown). Filename for
      code / config / catch-all files.
    - ``breadcrumb`` — tuple of ancestor heading texts up to **but not
      including** the chunk's own anchor heading. Empty tuple for code,
      config, catch-all, and for files emitted as a single chunk.
    - ``lang`` — language tag (``"markdown"``, ``"text"``, ``"python"``,
      ``"go"``, ``"powershell"``, ``"typescript"``, ``"yaml"``, …).
    - ``body`` — chunk text exactly as it appears in ``path`` between
      ``byte_start`` and ``byte_end``; chunks tile the file with no
      gaps so that round-trip reconstruction is faithful (modulo the
      trailing-whitespace caveat in ``research/chunker-design.md §8``
      item 4).
    - ``line_start`` / ``line_end`` — 1-based, inclusive line range.
    - ``byte_start`` — 0-based, inclusive byte offset in the source
      file (UTF-8).
    - ``byte_end`` — 0-based, **exclusive** byte offset (Pythonic
      slice end).
    - ``topic`` — frontmatter ``topic:`` if present, else ``None``.
      v0.1 retrieval ignores this; populated for forward-compat with
      SLIDERS-style extraction (see ADR-5 amendment §Topic propagation).
    """

    path: str
    anchor: str
    parent_title: str
    breadcrumb: tuple[str, ...]
    lang: str
    body: str
    line_start: int
    line_end: int
    byte_start: int
    byte_end: int
    topic: str | None = None


class Chunker(Protocol):
    """Stable interface from ADR-5 §Decision; future swaps (e.g.
    ctags-backed code chunker, tree-sitter) must not change this shape.
    """

    def chunk_file(self, path: Path) -> list[Chunk]: ...


__all__ = ["Chunk", "Chunker"]
