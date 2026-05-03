"""Tests for :class:`fa.chunker.PlainTextChunker`."""

from __future__ import annotations

from pathlib import Path

from fa.chunker import PlainTextChunker


def test_plain_text_yields_single_chunk(tmp_path: Path) -> None:
    body = "alpha\nbeta\ngamma\n"
    path = tmp_path / "notes.txt"
    path.write_text(body, encoding="utf-8")

    chunks = PlainTextChunker().chunk_file(path)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.body == body
    assert chunk.line_start == 1
    assert chunk.line_end == 3
    assert chunk.byte_start == 0
    assert chunk.byte_end == len(body.encode("utf-8"))
    assert chunk.parent_title == "notes.txt"
    assert chunk.breadcrumb == ()
    assert chunk.lang == "text"
    assert chunk.topic is None


def test_lang_label_is_propagated(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("key: value\n", encoding="utf-8")

    chunks = PlainTextChunker(lang="yaml").chunk_file(path)

    assert chunks[0].lang == "yaml"


def test_empty_file_emits_one_minimal_chunk(tmp_path: Path) -> None:
    path = tmp_path / "blank.txt"
    path.write_text("", encoding="utf-8")

    chunks = PlainTextChunker().chunk_file(path)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.body == ""
    assert chunk.byte_start == 0
    assert chunk.byte_end == 0
    assert chunk.line_start == 1
    assert chunk.line_end == 1


def test_no_trailing_newline_counts_last_line(tmp_path: Path) -> None:
    body = "alpha\nbeta"
    path = tmp_path / "ragged.txt"
    path.write_text(body, encoding="utf-8")

    chunks = PlainTextChunker().chunk_file(path)

    chunk = chunks[0]
    assert chunk.line_end == 2
    assert chunk.byte_end == len(body.encode("utf-8"))
