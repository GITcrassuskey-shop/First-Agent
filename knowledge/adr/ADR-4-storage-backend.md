# ADR-4 — Storage backend for v0.1

- **Status:** proposed
- **Date:** 2026-04-27
- **Deciders:** project owner (`0oi9z7m1z8`), Devin (drafting)

## Context

[ADR-3](./ADR-3-memory-architecture-variant.md) commits v0.1 to
**Variant A** with a three-layer retrieval (grep → BM25 → reserved
vector slot). [ADR-1](./ADR-1-v01-use-case-scope.md) keeps the
embedding / vector layer out of scope for v0.1.

We still need an explicit choice of **where the disposable index
lives** and **what the BM25 implementation is**. The user's PR-#17
review answer for Q3 (10.5 in original questions) was:

> 10.5. Storage backend для v0.1 — your call. for 0.1 it's better
> to create a working prototype faster.

[`knowledge/README.md`](../README.md) already mandates filesystem-
canonical Markdown for *human-readable canon*. This ADR only chooses
the **disposable index store** that makes search fast.

## Options considered

### Option A — In-memory index from a Python BM25 library, persisted as a pickle

Use `rank-bm25` (PyPI) or `bm25s`, build the index in memory at FA
process start by re-reading the corpus, persist as a pickle on
shutdown to avoid the cold rebuild cost.

- Pros:
  - Zero extra dependency at the storage layer (rank-bm25 is pure
    Python).
  - Easy to reason about; pickle is a single artefact.
- Cons:
  - Pickle is brittle across Python versions and library upgrades.
  - Cold-rebuild on cache invalidation is O(corpus); fine for
    v0.1's "single user, ~thousands of chunks", bad otherwise.
  - No built-in transaction / concurrency story if FA forks an
    inbox-watcher.

### Option B — SQLite FTS5 (chosen)

Use the `FTS5` extension shipped with the standard `sqlite3`
module. Store one row per chunk; `MATCH` queries return BM25-ranked
results out of the box. Index file is `~/.fa/index.sqlite` (or
similar).

- Pros:
  - **Zero extra dependency.** `sqlite3` is in the Python stdlib;
    `FTS5` is enabled in the binaries that come with Ubuntu / macOS
    / Windows Python distributions.
  - **Persistent**; incremental upserts; single-writer multi-reader
    by default.
  - **BM25 ranking built-in** (`MATCH` + `bm25()`).
  - Plays well with the inbox-watcher: a small write transaction
    per file change.
  - Disposable: rebuild from the filesystem canon at any time.
- Cons:
  - FTS5 BM25 parameters (`k1`, `b`) are fixed via tokeniser
    options; not as tunable as `rank-bm25`. Acceptable for v0.1.
  - SQLite locking semantics need attention if we add a daemon
    writer + CLI reader; for v0.1 we run single-process.

### Option C — External services (Postgres + pgvector / Elasticsearch / OpenSearch)

- Pros: most powerful; production-ready.
- Cons:
  - Operational overhead inappropriate for "single workstation,
    single user" v0.1.
  - Contradicts the user's "create a working prototype faster"
    directive.

### Option D — Files-only (no index, grep at query time)

- Pros: zero state.
- Cons:
  - Linear-scan over the whole corpus per query.
  - No BM25 ranking — only exact-match grep.
  - Forces every search to dump matches into LLM context, breaking
    the token-efficiency success metric in
    [`project-overview.md`](../project-overview.md) §3.

## Decision

We will choose **Option B (SQLite FTS5)** for the v0.1 disposable
index, with the following concrete shape:

- **One database file**: `~/.fa/state/index.sqlite` (path
  config-overridable). Disposable — rebuildable from filesystem
  canon by `fa reindex`.
- **Tables (v0.1 minimum):**
  - `chunks(id INTEGER PK, path TEXT, anchor TEXT, lang TEXT,
    body TEXT, mtime REAL, sha256 TEXT)`.
  - `chunks_fts(body, content='chunks', content_rowid='id')` —
    external-content FTS5 for BM25 (the FTS table reads body from
    `chunks` rather than storing its own copy; supports row-level
    UPDATE / DELETE for incremental upserts).
  - `meta(key TEXT PK, value TEXT)` — schema version, last reindex
    timestamp, FA version.
- **Tokeniser**: `unicode61 remove_diacritics 2` + porter stemmer
  for English. Russian / mixed-script content acceptable on `unicode61`
  alone; revisit if recall is poor.
- **No vector store in v0.1.** A future ADR (or v0.2 ADR-5)
  introduces either `sqlite-vec` (in the same DB file) or a separate
  `embeddings.sqlite`. The interface the wiki layer talks to will be
  abstract enough to swap implementations without churn in callers.
- **Filesystem canon stays authoritative.** SQLite is a cache.
  Any time `chunks.sha256 ≠ sha256(read_file(chunks.path))`, the
  row is re-extracted on next access. Full `fa reindex` is always
  available.

## Consequences

- **Positive:** Zero extra runtime deps for storage. `pip install
  first-agent` doesn't pull anything heavier than what `rank-bm25`
  alone would.
- **Positive:** `fa reindex` is mechanically verifiable: drop the
  DB file, run reindex, the search results equal the prior run.
- **Positive:** Adding the v0.2 vector layer is additive — same
  DB file, new table, same connection pool.
- **Negative:** FTS5's stemmer / tokeniser are fixed by build-time
  options; if our retrieval quality plateaus we may have to bring
  in `rank-bm25` or another lib alongside.
- **Negative:** Single-DB-file means parallel writers (e.g. inbox-
  watcher and CLI ingest at once) must be coordinated; we side-step
  this in v0.1 by running single-process.
- **Follow-up work this unlocks:**
  - Schema migrations: a tiny `migrations/` folder with numbered
    SQL scripts. Replays from `meta.schema_version`.
  - `fa reindex` CLI command.
  - v0.2 ADR slot for vector store (likely `sqlite-vec` to keep
    the "one file" property).
  - Decide whether `~/.fa/state/index.sqlite` should be committed
    to a project-local `.fa/` directory instead. v0.1 keeps it in
    `$HOME` to avoid bloating user repos.

## References

- [ADR-1](./ADR-1-v01-use-case-scope.md) — v0.1 scope.
- [ADR-3](./ADR-3-memory-architecture-variant.md) — Variant A
  read-side: grep → BM25 → reserved vector slot.
- [`research/memory-architecture-design-2026-04-26.md`](../research/memory-architecture-design-2026-04-26.md) §3 (design space, ось A — filesystem-canonical), §4 (Variant A read-side).
- [`research/llm-wiki-community-batch-2.md`](../research/llm-wiki-community-batch-2.md) §3.2 (llm-wiki-kit's "ripgrep + lunr/BM25" pattern).
- SQLite FTS5 documentation: `https://www.sqlite.org/fts5.html`.
