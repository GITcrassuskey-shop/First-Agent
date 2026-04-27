# ADR-1 — v0.1 use-case scope

- **Status:** proposed
- **Date:** 2026-04-27
- **Deciders:** project owner (`0oi9z7m1z8`), Devin (drafting)

## Context

[`project-overview.md`](../project-overview.md) lists four use cases
explored in research:

1. UC1 — Persistent coding & PR management.
2. UC2 — Continuous multi-source research.
3. UC3 — Local documentation to wiki.
4. UC4 — Multi-user Telegram (10-person group).

Doing all four at once defeats the "pragmatic, medium-weight
hybrid" goal stated in
[`research/memory-architecture-design-2026-04-26.md`](../research/memory-architecture-design-2026-04-26.md)
§1. We need an explicit ranking and a deferral list before scaffolding.

User priorities (verbatim from PR-#17 review):

> 1 — coding+PR / 3 — local-docs-to-wiki (main)
> 4 — multi-user TG
> 2 — multi-source research (i can live with costly search once in a while)

Plus an end-to-end acceptance scenario (PR-#17 Q5):

> Agent делает полный цикл: ingest folder → search → edit code →
> push branch → open PR (UC1 end-to-end).

## Options considered

### Option A — Ship UC1 + UC3 in v0.1; defer UC4 and best-effort UC2

- Pros:
  - Smallest end-to-end footprint (no Telegram bot, no graph).
  - UC1 acceptance scenario is concrete and demonstrable.
  - UC3 falls out of UC1's chunker + retrieval almost for free.
  - UC2 stays available as best-effort LLM-fan-out without needing
    new infra.
- Cons:
  - UC4 multi-user namespacing, which shapes the volatile-memory
    design, is not exercised; we could miss design pressure that
    matters for v0.2.
  - "Best-effort UC2" can be brittle on token cost without measurement.

### Option B — Ship UC1 + UC4 in v0.1

- Pros:
  - Forces volatile-memory design (per-user namespacing) early.
  - Unique value vs hosted agents: Telegram-driven workflows.
- Cons:
  - Telegram bot infra + multi-user store ≈ 2× engineering cost
    of UC3.
  - User explicitly ranked UC4 below UC1 + UC3.
  - Pulls in Mem0-style volatile store from v0.2 → v0.1, against
    the architectural staging.

### Option C — Ship all four in v0.1

- Pros: complete demo.
- Cons: contradicts "pragmatic, medium-weight" goal; sprawling scope;
  uneven quality on each.

## Decision

We will choose **Option A** because the user's explicit ranking
puts UC1 + UC3 first and the end-to-end UC1 PR-creation flow is the
acceptance bar. UC2 is included as **best-effort retrieval-only**
(no new infra). UC4 is **deferred to v0.2** along with the
volatile-store work that will support it.

### Concrete v0.1 in-scope list

- UC1 end-to-end: ingest folder → search → edit code → push branch
  → open PR via `gh` CLI.
- UC3 docs-to-wiki: large-textual-file ingest into `notes/inbox/`,
  retrieval via grep + SQLite FTS5 BM25, LLM Q&A on top-k chunks.
- UC2 best-effort: LLM-fan-out on top-k chunks for cross-source
  questions; no graph layer, no special infra.

### Concrete v0.1 deferred list

- UC4 Telegram multi-user.
- Mem0-style volatile store and 4-op tool-call API.
- Embeddings / vector store.
- Binary-format extractors (PDF, DOCX) — see
  [`project-overview.md`](../project-overview.md) §4.
- YouTube / Whisper / video ingest.

## Consequences

- **Positive:** Clear scope for scaffolding (Phase S of the roadmap
  in `research/memory-architecture-design-2026-04-26.md` §9).
  ADR-3 can pick Variant A unambiguously. ADR-2 only needs to
  cover the three-role static routing actually used in v0.1.
- **Positive:** UC1 acceptance is mechanically verifiable (a PR
  was created in a controlled repo from an FA session).
- **Negative:** v0.2 will discover volatile-memory design pressure
  for the first time; we accept that risk in exchange for shipping
  v0.1.
- **Negative:** "Best-effort UC2" needs a token-cost guardrail to
  avoid surprise spend; partially mitigated by static role routing
  ([ADR-2](./ADR-2-llm-tiering.md)) which keeps multi-source
  fan-out on Planner-tier OSS rather than elite. Fully addressed
  only when per-role token budgets land — explicitly deferred (see
  ADR-2 §Consequences "Follow-up work").
- **Follow-up work this unlocks:**
  - PR-write allow-list config (`~/.fa/repos.toml`) — single user
    repo + FA itself for v0.1.
  - LLM-as-judge eval baseline for UC1/UC3 acceptance (gstack
    scaled-down).
  - v0.2 ADR slot reserved for "Volatile store + UC4 Telegram"
    once v0.1 is shipped.

## References

- [`project-overview.md`](../project-overview.md) §4 (in scope) and §5 (non-goals).
- [`research/memory-architecture-design-2026-04-26.md`](../research/memory-architecture-design-2026-04-26.md) §8 (use-case mapping) and §9 (roadmap).
- PR #17 review thread (`https://github.com/GITcrassuskey-shop/First-Agent/pull/17`) — user's verbatim priority ranking.
