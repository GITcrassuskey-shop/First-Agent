"""One-chunk-per-file fallback chunker.

Used by ADR-5 §Decision steps 3 (config files: ``.yaml`` / ``.toml`` /
``.json``) and 4 (catch-all).

For the v0.1 chunker slice this also stands in for source-code files
(``.py``, ``.go``, ``.ps1``, ``.ts``, …) until the ctags-backed code
chunker lands as a follow-up — see
``src/fa/chunker/README.md`` §Roadmap.

ADR-5 §Decision step 3 spells out ``anchor = filename`` for config
files. We materialise that contract via a dot-safe slug
(``config.yaml`` → ``config-yaml``, ``foo.py`` → ``foo-py``) so the
anchor stays a valid URL fragment / shell-safe identifier while still
preserving the extension visibly. ``Chunk.path`` carries the literal
filename for callers that need a byte-exact path.
"""

from __future__ import annotations

from pathlib import Path

from fa.chunker._slug import slugify
from fa.chunker.types import Chunk


def _filename_anchor(name: str) -> str:
    """Dot-safe filename slug.

    Naive ``slugify("config.yaml")`` returns ``"configyaml"`` because
    ``.`` is not a word character; that collapses distinct filenames
    (``foo.py`` vs ``foopy``) and loses the extension in human-facing
    surfaces (CLI, future search UIs). Pre-replacing dots with hyphens
    keeps the extension boundary visible while still routing through
    the same Unicode-aware slug pipeline as Markdown anchors.
    """

    return slugify(name.replace(".", "-"))


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
        anchor = _filename_anchor(path.name) or _filename_anchor(path.stem) or "chunk"
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
