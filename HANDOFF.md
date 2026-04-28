# HANDOFF.md — for the next agent / session

> **Read this first if you are an LLM agent (Devin, Claude, ChatGPT,
> Cursor, etc.) starting a new session on this repository.**
>
> **Last updated:** 2026-04-28 by Devin session
> [`c9a88fb8`](https://app.devin.ai/sessions/c9a88fb811fd4891b7f932aaeee9ad26).

This file is a portable counterpart to the Devin Knowledge note
"First-Agent — current state pointer". Both contain the same
information. The Knowledge note auto-injects into Devin sessions;
this Markdown file exists for any LLM client that does not have
Devin's MCP context (Claude Code, Cursor, ChatGPT with repo
access, plain `git clone`).

If both disagree, the Devin Knowledge note is canonical (it gets
updated more often). When you finish a session that materially
changes the project state, update **both**.

## 60-second bootstrap

1. Read [`AGENTS.md`](./AGENTS.md) — repo conventions, PR
   checklist, query routing.
2. Read [`knowledge/llms.txt`](./knowledge/llms.txt) — one-fetch
   index of every documentation file in this repo
   ([llmstxt.org](https://llmstxt.org/) convention).
3. Skim [`knowledge/project-overview.md`](./knowledge/project-overview.md)
   — what the project is, what v0.1 ships, what is non-goal.
4. Skim the ADR index at
   [`knowledge/adr/README.md`](./knowledge/adr/README.md) — the
   five accepted decisions that shape v0.1.
5. Check the **Current state** section below for what is in
   flight right now.

You should now have everything you need. Do not crawl the repo
manually beyond this point.

## Current state (as of 2026-04-28)

- **Stage:** Phase S scaffolding complete; start of first module
  implementation. Minimal `src/fa` package exists only as a CLI
  smoke entrypoint. No feature module is implemented yet.
- **Architecture decisions (accepted):**
  - [ADR-1](./knowledge/adr/ADR-1-v01-use-case-scope.md) — UC1
    (coding + PR write) and UC3 (local-docs-to-wiki) in;
    UC4 deferred; UC2 best-effort.
  - [ADR-2](./knowledge/adr/ADR-2-llm-tiering.md) — static role
    routing (Planner / Coder / Debug / Eval) via
    `~/.fa/models.yaml`.
  - [ADR-3](./knowledge/adr/ADR-3-memory-architecture-variant.md) —
    Variant A (mechanical wiki, no embeddings, no graph,
    no Mem0).
  - [ADR-4](./knowledge/adr/ADR-4-storage-backend.md) — SQLite
    FTS5 (external-content mode); zero extra deps.
  - [ADR-5](./knowledge/adr/ADR-5-chunker-tool.md) —
    universal-ctags + markdown-it-py.
- **Scaffolding:** PR #27 added `pyproject.toml`, Ruff, mypy,
  pytest, pre-commit, GitHub Actions CI, `Makefile`, `markdown-it-py`,
  and system dependency documentation for `universal-ctags`.
- **Open PRs.** Check
  <https://github.com/GITcrassuskey-shop/First-Agent/pulls>.
- **Research notes that close design questions:**
  - [`research/memory-architecture-design-2026-04-26.md`](./knowledge/research/memory-architecture-design-2026-04-26.md)
    — three variants for memory (input to ADR-3).
  - [`research/chunker-design.md`](./knowledge/research/chunker-design.md)
    — five tool classes, coverage matrix, ten open questions
    (input to ADR-5).

## Next steps (intended order)

1. **Implementation PR — chunker.** Implement
   `src/fa/chunker/` with the `Chunk` dataclass and `Chunker`
   Protocol from
   [ADR-5 §Decision](./knowledge/adr/ADR-5-chunker-tool.md#decision).
   **Hard gate:** the four sample-tests in
   [`research/chunker-design.md` §8](./knowledge/research/chunker-design.md#8-sample-test-plan-pre-implementation)
   must pass — including the PowerShell sanity-check on the
   project lead's real 1500-line `.ps1` (not synthetic).
   The project lead should provide the real `.ps1` and a representative
   Go sample before this PR is considered mergeable.
2. **Chunker CLI surface.** Add `fa chunk <path>` for manual
   inspection of produced chunks as part of the chunker PR.

Phase-S item #7 (auto-generated `llms.txt`) is recorded in
[`docs/workflow.md`](./docs/workflow.md) as future work; not
blocking.

## Conventions worth knowing in 5 lines

- **Branch:** `devin/<unix-timestamp>-<slug>` from `main`.
- **Commit trailer:** every LLM-driven commit ends with
  `AI-Session: <session-id>` plus
  `Co-Authored-By: <human> <email>` (codedna pattern).
  Trailers must be in the squash-merge commit body — see PRs #19,
  #21, #23 for examples.
- **PR description:** every changed/new file listed as a clickable
  blob URL on the head branch (rule #6).
- **`knowledge/llms.txt`:** must be updated whenever `docs/` or
  `knowledge/` changes structure (rule #7).
- **Code fences:** always have a language tag (`python`, `yaml`,
  `text`, …); never a bare ` ``` ` opening.

## When to update this file

- After any PR merge that materially changes the project state
  (new ADR, new phase, new module, new big research note).
- Bump the **Last updated** date at the top.
- Also update the matching Devin Knowledge note (or replace it
  entirely with the body of this file — they are meant to be
  identical).

## Why this file exists

Pattern lifted from the educational angle of this project: every
convention should be discoverable via either Devin-specific
infrastructure (Knowledge note) **or** plain repo browsing
(this file). Forks of this repo as a starter template do not
necessarily use Devin; HANDOFF.md is what they get for free.
