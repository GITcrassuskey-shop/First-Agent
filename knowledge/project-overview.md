# Project Overview — First-Agent

> **Status:** filled 2026-04-27. Source for v0.1 scope decisions in
> [ADR-0001](./adr/0001-v01-use-case-scope.md). Refresh whenever
> something on this page changes (do not let it drift).

## 1. Problem statement

First-Agent (FA) is a **locally orchestrated, mixed-tier LLM coding
agent** for a single power-user. It exists because:

- Hosted coding agents (Devin, Cursor, Copilot Workspace) are great
  but expensive at scale and constrained to their own context-/memory-
  models. We need a setup where **planner / coder / debug roles can
  use different LLM tiers** (top-tier OSS / mid-tier OSS / Anthropic
  elite) under our config control.
- Local "GraphRAG" stacks (MS GraphRAG, LightRAG, HippoRAG) optimise
  *reading* but produce write-side bookkeeping the user has to
  maintain. LLM-Wiki stacks (Karpathy, AI-Context-OS, sparks) optimise
  *writing* but read-side is often grep+BM25 only.
- We want the **hybrid**: filesystem-canon (human-readable, git-able,
  diff-reviewable) **plus** a search-side that scales by lazily
  adding capability (BM25 → vectors → graph) only when the corpus
  justifies it.

## 2. Users

- **v0.1 user:** a single power-user (project owner) running FA on a
  single workstation. Used in casual sessions for code edits, docs
  Q&A, and PR creation, plus occasional research synthesis.
- **Future users (post-v0.2):** the same user inside a Telegram
  group of ~10 people, where FA needs per-user memory namespacing.
  This shapes the architecture but is **not implemented in v0.1**.
- **Audience for documentation:** other LLM agents (Devin, Codex,
  Claude Code) navigating the repo. Hence routing-by-folder in
  [`AGENTS.md`](../AGENTS.md) and provenance-frontmatter in
  [`knowledge/README.md`](./README.md).

## 3. Success metrics

v0.1 is a prototype, so metrics are deliberately coarse:

- **End-to-end UC1 demo passes**: agent ingests a folder, answers a
  scoped question by retrieval, edits a code file in a controlled
  side project, opens a PR. Manually verified — no automated eval
  bar yet.
- **Token-efficiency in casual API calls**: each retrieval-augmented
  turn must consume ≤ ~10 % of what a full-context (raw-file-dump)
  approach would. Measured as `tokens_in_context / tokens_in_full_corpus`
  on 5 fixture sessions.
- **No production latency SLA in v0.1.** Target: "feels usable" on
  a workstation. Hard latency budgets enter when we add embeddings
  or graph (v0.2+).
- **LLM-as-judge baseline** (gstack three-tier eval) on a small
  fixture set of search/edit tasks. Set baseline, regulate
  iteratively. No labelled gold-set yet (none exists for our
  corpora).

## 4. Scope

### In scope (v0.1)

- **UC1 — Persistent coding & PR management** end-to-end:
  - Ingest user's controlled-list code projects (FA itself + 1–2
    personal repos: golang library, ~1 500-line PowerShell script).
  - Chunk-aware reading (no full-file raw dumps in context) for
    Markdown / plain text, Python, Go, PowerShell `.ps1`,
    TypeScript/JavaScript, YAML / TOML / JSON.
  - Edit code files via shell tools, push to a feature branch,
    open a GitHub PR via `gh` CLI.
- **UC3 — Local documentation to wiki**:
  - `fa ingest <path-or-url>` for local docs / web pages /
    arxiv-html summaries.
  - **Large textual files (any size) in scope**: Markdown, plain
    text, source files. Chunker splits at write-time so retrieval
    pulls selective chunks (not raw-dump). The point is
    "large file → inbox → indexed → selective retrieval" — the
    user can drop a 50 KB or 1 MB notes/docs file in `notes/inbox/`
    and the agent answers questions over it without reading the
    whole thing into context.
  - Three-layer retrieval baseline: filename/title/tag grep →
    SQLite FTS5 BM25 → (vector layer reserved, deferred to v0.2).
  - Q&A over the resulting wiki using LLM synthesis on top-k chunks.
- **Memory architecture: Variant A** (Mechanical Wiki) per
  [ADR-0003](./adr/0003-memory-architecture-variant.md), with
  `volatile/`-store hooks scaffolded for v0.2 promotion.
- **LLM tiering: static role-routing** (Planner / Coder / Debug) per
  [ADR-0002](./adr/0002-llm-tiering.md). Mix per-model: local +
  OpenRouter + Anthropic.
- **Inbox-hybrid ingest**: `notes/inbox/` watched directory **plus**
  explicit `fa ingest <url>` for web / arxiv / PR sources.
- **Session model**: `hot.md` per session, auto-archived to
  `notes/sessions/<date>.md` at session end (audit trail).
- **Eval baseline**: gstack three-tier scaled-down — gate (smoke
  tests on fixtures) + LLM-as-judge on ad-hoc queries. No periodic
  / diff-based eval yet.

### Out of scope (v0.1)

- **UC2 — Continuous multi-source research** (multi-repo /
  multi-paper synthesis): best-effort via LLM-fan-out on top-k chunks.
  No graph-traversal, no cross-source joins.
- **UC4 — Multi-user Telegram chat**: deferred to v0.2 entirely.
  No TG bot, no per-user memory namespacing in v0.1.
- **Embeddings / vector store** (sentence-transformers, sqlite-vss):
  scaffolded as an interface point, not implemented.
- **Graph layer** (typed edges, PPR): explicit non-goal for v0.1.
  See [ADR-0003](./adr/0003-memory-architecture-variant.md) §Decision.
- **Mem0-style volatile store** with 4-op tool-call API: deferred to
  v0.2 upgrade.
- **YouTube / Whisper / video ingest**: deferred to v0.2+.
- **Binary-format extractors** (PDF→text, DOCX→text, etc.): deferred
  to v0.2+. Note: "large file ingest" capability *is* in scope (see
  UC3 above) — it is the **format-specific extractor for PDF and
  similar binary formats** that is deferred. Plain HTML arxiv
  abstract is in scope; full-paper PDF needs a pdfplumber/pymupdf
  pipeline that is v0.2 work.
- **General-purpose multi-repo write**: PR-write is restricted to
  FA itself + a controlled allow-list of 1–2 user repos (config).

## 5. Non-goals

- **Not a hosted product.** Single-machine, single-user. No
  multi-tenant story in v0.1; v0.2's TG-mode will be the first
  multi-user step.
- **Not a generic LLM framework.** We do not aim to compete with
  LangChain, LlamaIndex, AutoGen on coverage. We pick a small, opinionated
  toolset and build for our own usage patterns.
- **Not a self-hosted LLM serving stack.** Local models (vLLM, Ollama)
  are an *access path*, not a deliverable. We assume the user has
  the model running or available via a remote API.
- **Not a research benchmark.** No published eval numbers; LLM-as-judge
  baseline is for our own iteration, not for paper-grade comparison.
- **Not a permanent / immutable archive.** `knowledge/` is curated,
  but `notes/` and `hot.md` are designed for churn; supersession is
  the lifecycle, not deletion-prevention.

## 6. Key constraints

- **Runtime:** Python 3.11+, async where it pays off (LLM concurrency,
  inbox watcher). Single-process. No daemon required for v0.1; an
  optional foreground watcher for `notes/inbox/`.
- **LLM providers (v0.1):** **mix per-model in config**.
  - **Planner (top-tier OSS):** GLM 5.1 / Kimi 2.6 / Xiaomi Mimo 2.5
    via OpenRouter or local vLLM (whichever is configured).
  - **Coder (mid-tier OSS):** Nemotron 3 Super / Qwen 3.6 27B via
    local vLLM or OpenRouter.
  - **Debug / elite:** Anthropic Claude (latest available — Opus
    4.7-tier when accessible, Sonnet otherwise) via Anthropic API.
  - Static role-routing (no dynamic auto-escalation in v0.1). Decision:
    [ADR-0002](./adr/0002-llm-tiering.md).
- **Latency budget:** no hard SLA in v0.1. Target ≤ 10 s p95 per turn
  on local-vLLM Coder and ≤ 30 s when Anthropic-Debug is invoked.
  Will harden with v0.2 / when adding embeddings.
- **Cost budget:** "casual API use" — no fixed cap, but token-efficiency
  is a v0.1 success metric (see §3). Anthropic-Debug invocations are
  the most expensive and are gated by static role routing, not
  fan-out per turn.
- **Privacy / data handling:** remote API ≈ 99 % of traffic; user
  is OK with TG-data going to providers in v0.2. No special
  data-residency / PII-redaction requirements in v0.1.
- **Storage:** filesystem-canonical (Markdown + frontmatter) per
  [`knowledge/README.md`](./README.md). Disposable index in SQLite
  (FTS5 for BM25). No remote DB. Decision:
  [ADR-0004](./adr/0004-storage-backend.md).

## 7. Risks & open questions

- **R1 — Multi-language chunking quality.** Six file kinds in v0.1
  (Markdown, Python, Go, PowerShell, TS/JS, YAML/TOML/JSON). Per-language
  regex chunkers may produce uneven boundaries on edge cases. *Mitigation:*
  start with `universal-ctags` for code (well-supported across these
  languages) + heading-aware chunker for Markdown + simple block-aware
  chunker for config files. Re-evaluate after first 10 ingest sessions.
- **R2 — `gh` CLI authentication & repo allow-list.** PR-write requires
  GitHub credentials and a controlled list of writable repos. *Mitigation:*
  config-driven allow-list (`~/.fa/repos.toml`); fail-closed if a repo
  isn't listed. ADR-0001 §Consequences.
- **R3 — Multi-LLM static routing brittleness.** Three providers means
  three failure modes (rate limits, model deprecation, account
  exhaustion). *Mitigation:* per-role fallback chain in config (`primary
  → fallback`); no auto-escalation between tiers.
- **R4 — Inbox-watcher edge cases.** Files moved into `notes/inbox/`
  mid-write or while open in an editor. *Mitigation:* watch with
  inotify + debounce window; ignore `*.tmp` / `.swp` / `~`.
- **R5 — Eval baseline drift.** LLM-as-judge baseline can drift if the
  judge model itself updates. *Mitigation:* version-pin the judge in
  config; re-baseline on judge upgrade and document the delta.
- **OQ1 — When do we add the volatile (Mem0-style) store?** v0.2 trigger:
  user explicitly notices "I keep retelling the agent the same context."
  Or after 30 + sessions on the same project where session-archive grep
  is no longer enough.
- **OQ2 — When do we add embeddings?** v0.2 trigger: BM25 + grep miss
  rate becomes noticeable on UC3 (docs Q&A) — measured by LLM-as-judge
  eval saying "context insufficient" > N % of evaluations.
- **OQ3 — When do we add the graph layer (Variant C)?** Possibly never.
  Trigger: a use case appears whose multi-hop nature can't be answered
  by LLM-fan-out at acceptable cost. UC2 (multi-source research) is
  the candidate.

## 8. Glossary (project-specific)

- **FA** — First-Agent (this project).
- **v0.1 / v0.2** — milestone numbering. v0.1 = first end-to-end
  prototype matching §4 In scope. v0.2 = adds volatile store
  (Mem0-style) and TG mode. v0.3 = embeddings / graph if needed.
- **Variant A / B / C** — three memory architectures explored in
  [`research/memory-architecture-design-2026-04-26.md`](./research/memory-architecture-design-2026-04-26.md).
  v0.1 = Variant A; v0.2 = adds Variant B hooks. Variant C = explicit
  non-goal.
- **Planner / Coder / Debug** — three LLM-roles routed to different
  tiers via static config. See [ADR-0002](./adr/0002-llm-tiering.md).
- **`hot.md`** — per-session working summary, ~ 500 words, archived to
  `notes/sessions/<date>.md` at session end. Borrowed from
  obsidian-wiki pattern.
- **`notes/inbox/`** — watched directory; new files there are auto-
  ingested into the wiki on settle.
- **Mechanical / semantic split** — sparks pattern: deterministic
  Python parsers do mechanical work (chunk, hash, regen, commit);
  LLM does semantic work (typing, summary, classification).
- **Top-tier / mid-tier / elite** — LLM tier shorthand. Top-tier OSS
  ≈ GLM 5.1 / Kimi 2.6 / Xiaomi Mimo 2.5. Mid-tier OSS ≈ Nemotron
  3 / Qwen 3.6 27B. Elite ≈ Anthropic Claude latest.

---

*Detail belongs in ADRs and PRDs (under `docs/prd/` once we have any).
This page stays one screen long; update on every milestone.*
