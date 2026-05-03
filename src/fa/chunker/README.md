# `fa.chunker` — deterministic chunker for the Mechanical Wiki (v0.1)

First feature-module slice of v0.1 — implements
[ADR-5](../../../knowledge/adr/ADR-5-chunker-tool.md) §Decision step 1
(Markdown / plain text via `markdown-it-py`) and the matching
[ADR-4](../../../knowledge/adr/ADR-4-storage-backend.md) §Decision plus
2026-04-29 provenance amendment for the `Chunk` shape consumed by the
SQLite FTS5 index.

The package ships a stable interface so the storage / retrieval layer
can be built against it before the source-code chunker lands:

```python
from fa.chunker import CHUNKER_VERSION, Chunk, Chunker, default_chunker

chunks: list[Chunk] = default_chunker().chunk_file(path)
```

## What ships in v0.1 first slice

- `Chunk` frozen dataclass with provenance fields
  (`parent_title`, `breadcrumb`, `byte_start`/`byte_end`, `topic`)
  per ADR-5 amendment 2026-04-29.
- `Chunker` `Protocol` matching ADR-5 §Decision §7.3.
- `MarkdownChunker` — heading-aware splitter for `.md` / `.markdown`.
  Configurable split depth (default H1 + H2) and single-chunk
  threshold (default 500 lines, per ADR-5 §Decision step 1).
- `PlainTextChunker` — one-file-one-chunk fallback for plain text,
  config files (`.yaml` / `.yml` / `.toml` / `.json`), and
  catch-all extensions per ADR-5 §Decision steps 3 and 4.
- `CompositeChunker` — per-extension router used as the default
  entry point; matches the ADR-5 §Decision routing table.
- `CHUNKER_VERSION` composite string written into the storage `meta`
  table per ADR-4 §Cache Invalidation.

The shipped `MarkdownChunker` covers research-note sample-tests 2
(Markdown smoke-test) and 4 (round-trip reconstruction) from
[`chunker-design.md` §8](../../../knowledge/research/chunker-design.md#8-sample-test-plan-pre-implementation).

## Roadmap — follow-up PRs

The full ADR-5 pipeline has two more steps that are intentionally
deferred to keep the first PR small and reviewable:

1. **`CtagsChunker` for source code** (ADR-5 §Decision step 2) —
   `subprocess.run(["ctags", "--output-format=json", ...])` with
   PowerShell `#region` pre-splitting. Requires the four `chunker-design.md` §8
   sample-tests to actually run before merge:
     - Sample-test 1 (PowerShell sanity-check on the project lead's
       1500-line `.ps1`) — needs the real file from the project lead.
     - Sample-test 3 (Go sample) — needs a representative `.go` file.
   Once that PR lands, `CompositeChunker` swaps source-code
   extensions from `PlainTextChunker` to `CtagsChunker`; the
   `Chunker` Protocol does not change.
2. **`CHUNKER_VERSION` upgrade** to include the resolved `ctags`
   binary version (string composition handled inside this package).

Tree-sitter remains the explicit re-evaluation trigger documented in
ADR-5 §Consequences (only re-opened if the ctags slice fails the §8
sample-tests, or if symbol-chunks > 2 K tokens degrade UC1 retrieval).

## CLI smoke command

```bash
fa chunk path/to/file.md            # human-readable
fa chunk path/to/file.md --output json
```

`fa chunk` exists for manual inspection of the produced chunks
(ADR-5 §Decision §7.3 stable interface) — not as a production
indexing command. The real `fa reindex` (ADR-4 §Decision) lands
once storage is wired.
