"""One-chunk-per-file fallback chunker.

Used by ADR-5 §Decision steps 3 (config files: ``.yaml`` / ``.toml`` /
``.json``) and 4 (catch-all). Also covers ``.txt`` plain text where
splitting on Markdown headings is not meaningful.

For the v0.1 chunker slice this also stands in for source-code files
(``.py``, ``.go``, ``.ps1``, ``.ts``, …) until the ctags-backed code
chunker lands as a follow-up — see
``src/fa/chunker/README.md`` §Roadmap.
"""

from __future__ import annotations

from pathlib import Path

from fa.chunker._slug import slugify
from fa.chunker.types import Chunk


class PlainTextChunker:
    """Emit a single :class:`~fa.chunker.types.Chunk` covering the entire file."""

    def __init__(self, *, lang: str = "text") -> None:
        self._lang = lang

    def chunk_file(self, path: Path) -> list[Chunk]:
        text = path.read_text(encoding="utf-8")
        encoded = text.encode("utf-8")
        if not text:
            line_count = 0
        elif text.endswith("\n"):
            line_count = text.count("\n")
        else:
            line_count = text.count("\n") + 1
        anchor = slugify(path.name) or slugify(path.stem) or "chunk"
        return [
            Chunk(
                path=str(path),
                anchor=anchor,
                parent_title=path.name,
                breadcrumb=(),
                lang=self._lang,
                body=text,
                line_start=1,
                line_end=max(line_count, 1),
                byte_start=0,
                byte_end=len(encoded),
                topic=None,
            ),
        ]


__all__ = ["PlainTextChunker"]
