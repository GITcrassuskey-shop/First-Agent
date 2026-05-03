"""Smoke tests for the public chunker types."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from fa.chunker import CHUNKER_VERSION, Chunk, Chunker


def _sample_chunk(**overrides: object) -> Chunk:
    defaults: dict[str, object] = {
        "path": "sample.md",
        "anchor": "intro",
        "parent_title": "Sample",
        "breadcrumb": (),
        "lang": "markdown",
        "body": "# Sample\n\nbody\n",
        "line_start": 1,
        "line_end": 3,
        "byte_start": 0,
        "byte_end": 18,
        "topic": None,
    }
    defaults.update(overrides)
    return Chunk(**defaults)  # type: ignore[arg-type]


def test_chunk_is_frozen() -> None:
    chunk = _sample_chunk()
    with pytest.raises(FrozenInstanceError):
        chunk.path = "other.md"  # type: ignore[misc]


def test_chunk_has_provenance_fields() -> None:
    field_names = {f.name for f in fields(Chunk)}
    expected = {
        "path",
        "anchor",
        "parent_title",
        "breadcrumb",
        "lang",
        "body",
        "line_start",
        "line_end",
        "byte_start",
        "byte_end",
        "topic",
    }
    assert expected <= field_names


def test_chunker_protocol_is_satisfied_by_callable_class() -> None:
    class _Stub:
        def chunk_file(self, path: Path) -> list[Chunk]:  # pragma: no cover - shape check
            return [_sample_chunk(path=str(path))]

    stub: Chunker = _Stub()
    chunks = stub.chunk_file(Path("foo.md"))
    assert len(chunks) == 1
    assert chunks[0].path == "foo.md"


def test_chunker_version_is_versioned_string() -> None:
    assert isinstance(CHUNKER_VERSION, str)
    assert CHUNKER_VERSION.startswith("0.1.")
