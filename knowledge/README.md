# Knowledge

Durable project knowledge for First-Agent. Everything here is:

1. **Committed** to the repo so it is versioned and reviewable.
2. **Cross-referenced** from Devin Knowledge notes where useful (see
   [`docs/devin-reference.md`](../docs/devin-reference.md#1-knowledge-notes--long-term-memory)).

## Layout

```text
knowledge/
├── README.md                 # this file
├── llms.txt                  # one-fetch URL index for LLM agents (llmstxt.org)
├── project-overview.md       # one-page product + scope snapshot
├── adr/                      # architecture decision records
│   ├── README.md
│   └── ADR-template.md
├── prompts/                  # reusable prompts
│   ├── README.md
│   ├── RESOLVER.md           # intent-to-template dispatcher
│   └── research-topic.md
└── research/                 # (created on demand) research notes
```

## Conventions

- One concept per file.
- Markdown only. **Two line-length tiers:**
  - **Simple summaries / overviews** — keep under **~500 lines**.
    If a summary pushes >600 lines — think of splitting it topic-wise.
  - **Deep-dive / detailed research** — keep under **~1,200 lines**.
    Deep reviews (multi-source critique, per-project verdicts,
    cross-cutting analysis) often require 600–1,200 lines without losing
    coherence. If a deep-dive is >1,300 lines — think of splitting it topic-wise.
- Link to source URLs for any non-obvious claim.
- **Never silently overwrite.** When a file is superseded: mark the old
  file with `> **Status:** superseded by <link>` at the top, add a
  `superseded_by:` field to its frontmatter if present, and keep the old
  content for audit. See the critique-driven rationale in
  [`research/llm-wiki-critique.md`](./research/llm-wiki-critique.md).

### Provenance-frontmatter (for `research/` and any summary notes)

Any note that *synthesizes* multiple sources or contains
specific numbers/dates/names must carry a frontmatter:

```yaml
---
title: "<title>"
source:
  - "<url or repo path>"
compiled: "<YYYY-MM-DD>"
chain_of_custody: "<where to find the primary source for specific facts>"
claims_requiring_verification:
  - "<claim 1>"
superseded_by: "<path, if any>"
---
```

The minimum required fields are `source` and `compiled`. `chain_of_custody` is mandatory if
the note contains numbers, dates, quotes, or decisions that someone might
reference. The goal is not to lose the connection between the LLM-written summary and
the primary source. For more details, see
[`research/llm-wiki-critique-first-agent.md §9`](./research/llm-wiki-critique-first-agent.md#9-specific-edits-to-existing-files).

### Frontmatter v2 — optional fields (additive)

The schema above (v1) stays mandatory for new notes. The fields below
are **optional** and **additive** — existing files do not need to be
backfilled. They become useful once the agent starts maintaining a
typed index over the corpus (post-v0.1, see
[`adr/ADR-3-memory-architecture-variant.md`](./adr/ADR-3-memory-architecture-variant.md)
Volatile-store hooks).

All v1 fields above stay required. The v2 block adds only the
optional fields:

```yaml
---
# ... all v1 fields above (title, source, compiled, chain_of_custody) ...

# v2 optional fields
tier: stable          # stable | volatile
links:                # internal cross-refs (relative paths from this file)
  - "./other-note.md"
mentions:             # external entities (people, projects, papers, repos, URLs)
  - "OpenRouter"
  - "https://arxiv.org/abs/2504.19413"
confidence: extracted # extracted | inferred | ambiguous
---
```

Field semantics:

- **`tier`** — which memory tier the note belongs to. `stable` is the
  filesystem canon (PR-write); `volatile` is the v0.2 Mem0-style
  store (does not exist in v0.1). If absent, assume `stable`.
- **`links`** — explicit graph edges to other notes in this repo, as
  relative paths. Lets the future indexer build a citation graph
  without re-parsing prose.
- **`mentions`** — external entities referenced in the note. Free-form
  strings (names, URLs, repo handles). Used by the future indexer for
  external-entity recall.
- **`confidence`** — origin of the note's claims. `extracted` if
  copied verbatim from a primary source; `inferred` if synthesised by
  the author / LLM from multiple sources; `ambiguous` if the source-to-
  claim mapping is unclear and the note needs a verification pass.

None of these fields are validated by tooling yet. They exist so that
when v0.2 indexer lands, the additive backfill is mechanical, not a
schema migration.

## What goes where

| If it is… | Put it in… |
|---|---|
| A decision we made (and why) | `knowledge/adr/` |
| Background research / literature summary | `knowledge/research/` |
| A reusable prompt | `knowledge/prompts/` |
| Project-wide context (mission, scope, users) | `knowledge/project-overview.md` |
| How-to / guide / reference | `docs/` (not here) |

## Routing — Where the agent looks for an answer

| Question type | Primary source | Secondary / verification |
|---|---|---|
| "What is our architecture for X?" | `docs/architecture.md` | ADRs in `knowledge/adr/` |
| "What decision did we make regarding Y and why?" | `knowledge/adr/` | — |
| "What did we find during the research of Z?" | `knowledge/research/<Z>.md` | Primary sources from `source:` frontmatter |
| Specific number / date / quote | **Always** the primary source (`source:` of the note), not the summary | — |
| Procedure / how-to | `docs/` | Future `SKILL.md` |

This same rule is documented in [`AGENTS.md`](../AGENTS.md#query-routing).
