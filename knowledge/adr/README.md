# Architecture Decision Records (ADRs)

We record significant decisions as short ADRs, adapted from
[Michael Nygard's template](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).

## When to write one

Write an ADR when the decision:

- Locks in a trade-off that will be expensive to reverse, **or**
- Affects multiple modules or public APIs, **or**
- Picks between multiple credible options (frameworks, models, storage, orchestration).

You do **not** need an ADR for routine code-level choices.

## Process

1. Copy [`ADR-template.md`](./ADR-template.md) → `ADR-N-short-slug.md` (next integer, no padding).
2. Fill it in. Keep it under one page.
3. Open a PR titled `ADR: <short title>`.
4. Merge once reviewers agree with the decision, not just the wording.

## Index

| # | Title | Status |
|---|---|---|
| [1](./ADR-1-v01-use-case-scope.md) | v0.1 use-case scope | accepted |
| [2](./ADR-2-llm-tiering.md) | LLM tiering & access | accepted |
| [3](./ADR-3-memory-architecture-variant.md) | Memory architecture variant for v0.1 | accepted |
| [4](./ADR-4-storage-backend.md) | Storage backend for v0.1 | accepted |
