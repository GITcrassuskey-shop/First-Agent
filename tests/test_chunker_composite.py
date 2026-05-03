"""Tests for :class:`fa.chunker.CompositeChunker` extension routing."""

from __future__ import annotations

from pathlib import Path

import pytest

from fa.chunker import CompositeChunker, default_chunker


def _write(tmp_path: Path, name: str, body: str) -> Path:
    target = tmp_path / name
    target.write_text(body, encoding="utf-8")
    return target


@pytest.mark.parametrize(
    ("name", "expected_lang"),
    [
        ("plain.txt", "text"),
        ("script.py", "python"),
        ("module.go", "go"),
        ("profile.ps1", "powershell"),
        ("module.psm1", "powershell"),
        ("ui.ts", "typescript"),
        ("ui.tsx", "tsx"),
        ("ui.js", "javascript"),
        ("ui.jsx", "jsx"),
        ("config.yaml", "yaml"),
        ("config.yml", "yaml"),
        ("config.toml", "toml"),
        ("config.json", "json"),
        ("unknown.xyz", "text"),
    ],
)
def test_extension_routes_to_one_chunk_with_expected_lang(
    tmp_path: Path, name: str, expected_lang: str
) -> None:
    path = _write(tmp_path, name, "content\nmore content\n")

    chunks = CompositeChunker().chunk_file(path)

    assert len(chunks) == 1
    assert chunks[0].lang == expected_lang


def test_markdown_extension_routes_to_markdown_chunker(tmp_path: Path) -> None:
    path = _write(tmp_path, "note.md", "# Title\n\nbody\n")

    chunks = CompositeChunker().chunk_file(path)

    assert chunks[0].lang == "markdown"
    assert chunks[0].parent_title == "Title"


def test_default_chunker_is_a_composite() -> None:
    assert isinstance(default_chunker(), CompositeChunker)
