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

1. Copy [`0000-template.md`](./0000-template.md) → `NNNN-short-slug.md` (next number, zero-padded 4).
2. Fill it in. Keep it under one page.
3. Open a PR titled `ADR: <short title>`.
4. Merge once reviewers agree with the decision, not just the wording.

## Index

| # | Title | Status |
|---|---|---|
| [0001](./0001-v01-use-case-scope.md) | v0.1 use-case scope | proposed |
| [0002](./0002-llm-tiering.md) | LLM tiering & access | proposed |
| [0003](./0003-memory-architecture-variant.md) | Memory architecture variant for v0.1 | proposed |
| [0004](./0004-storage-backend.md) | Storage backend for v0.1 | proposed |
