"""Per-extension delegating chunker.

Implements ADR-5 §Decision routing:

1. Markdown / plain text (``*.md``, ``*.markdown``, ``*.txt``) —
   :class:`MarkdownChunker`. Plain ``.txt`` shares the heading-aware
   pipeline so long note-style files split on ``#``/``##`` markers
   when they happen to use them, and otherwise fall back to a single
   chunk via the chunker's own no-headings branch. ``lang`` is
   ``"markdown"`` for ``.md``/``.markdown`` and ``"text"`` for
   ``.txt``.
2. Source code (``*.py``, ``*.go``, ``*.ps1``/``*.psm1``, ``*.ts``,
   ``*.tsx``, ``*.js``, ``*.jsx``) — **deferred** to a follow-up PR
   that wires universal-ctags. v0.1 falls back to one-chunk-per-file
   via :class:`PlainTextChunker` so the indexing pipeline can be wired
   end-to-end before ctags integration lands.
3. Config files (``*.yaml``, ``*.yml``, ``*.toml``, ``*.json``) —
   :class:`PlainTextChunker` (one file = one chunk).
4. Catch-all — :class:`PlainTextChunker` with ``lang="text"``.
"""

from __future__ import annotations

from pathlib import Path

from fa.chunker.markdown import MarkdownChunker
from fa.chunker.plaintext import PlainTextChunker
from fa.chunker.types import Chunk

_LANG_BY_EXT: dict[str, str] = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "text",
    ".py": "python",
    ".go": "go",
    ".ps1": "powershell",
    ".psm1": "powershell",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "jsx",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".json": "json",
}

_MARKDOWN_EXTS = frozenset({".md", ".markdown"})
_PLAIN_TEXT_EXTS = frozenset({".txt"})


class CompositeChunker:
    """Routes :meth:`chunk_file` to a per-extension implementation."""

    def __init__(self) -> None:
        self._markdown = MarkdownChunker()
        # Distinct ``MarkdownChunker`` for ``.txt`` so the emitted
        # chunk's ``lang`` is ``"text"``, matching the ``_LANG_BY_EXT``
        # contract while sharing the heading-aware pipeline (ADR-5
        # §Decision step 1).
        self._markdown_text = MarkdownChunker(lang="text")
        self._plain_by_lang: dict[str, PlainTextChunker] = {}

    def chunk_file(self, path: Path) -> list[Chunk]:
        ext = path.suffix.lower()
        lang = _LANG_BY_EXT.get(ext, "text")
        if ext in _MARKDOWN_EXTS:
            return self._markdown.chunk_file(path)
        if ext in _PLAIN_TEXT_EXTS:
            return self._markdown_text.chunk_file(path)
        return self._plain_chunker(lang).chunk_file(path)

    def _plain_chunker(self, lang: str) -> PlainTextChunker:
        existing = self._plain_by_lang.get(lang)
        if existing is None:
            existing = PlainTextChunker(lang=lang)
            self._plain_by_lang[lang] = existing
        return existing


def default_chunker() -> CompositeChunker:
    """Factory used by the CLI; return type narrowed for callers that
    want the concrete class without going through the Protocol."""

    return CompositeChunker()


__all__ = ["CompositeChunker", "default_chunker"]
