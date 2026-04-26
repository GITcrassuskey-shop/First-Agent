# AGENTS.md

Instructions for AI agents (Devin and similar) working in this repo.

## Project Overview

**First-Agent** — LLM agent research project.
Stage: `research → start of module creation`. No code in `src/` yet.
Details: [`README.md`](./README.md).

## Repository Structure

- [`README.md`](./README.md) — project overview.
- [`AGENTS.md`](./AGENTS.md) — this file.
- [`docs/`](./docs/README.md) — wiki (architecture, workflow,
  prompting, devin-reference, glossary, agent creation tutorial).
- [`knowledge/`](./knowledge/README.md) — durable memory (project-overview, ADR, prompts, research).

## Working in This Repo

- All documentation is Markdown. ATX headings (`#`, `##`), lines ≤ 120 chars.
- Fenced code blocks — always with a language tag:
  - Code: `python`, `yaml`, `json`, `bash`.
  - Non-code (ASCII art, directory trees, prompts, logs): `text`.
  - Never leave a bare ` ``` `.
- New docs go in the right folder:
  - Guides / references → `docs/`. Update [`docs/README.md`](./docs/README.md).
  - Project artifacts (decisions, research, prompts) → `knowledge/`.
- Architectural decisions → ADR from [`knowledge/adr/0000-template.md`](./knowledge/adr/0000-template.md).

## PR Checklist

Verify before opening a PR. Each item has triggered wasted review cycles.

1. **Code fences have language tags.** No bare ` ``` `. See rule above.
2. **Frontmatter uses `compiled:`, not `date:`.** Schema: [`knowledge/README.md`](./knowledge/README.md#conventions).
3. **File length within tier limits.**
   - Summaries / overviews: **~500 lines**.
   - Deep-dive research: **~1 200 lines**.
4. **`compiled:` date ≥ all dates cited in text.** No temporal impossibilities.
5. **Supersession, not overwrite.** Mark old file `> **Status:** superseded by <link>`. Keep for audit.

## Development Workflow

- Branch: `devin/<timestamp>-<slug>` from `main`.
- All changes via Pull Request.
- Commit messages: descriptive, English, present tense (`docs: add architecture note`).
- Never push directly to `main`.

## Query Routing

Route questions to the right folder. Do not load everything into context.

| Question type | Look first | Verify with |
|---|---|---|
| Architecture, patterns | [`docs/architecture.md`](./docs/architecture.md) | ADR |
| Decisions and rationale | [`knowledge/adr/`](./knowledge/adr/) | — |
| Workflow, Devin usage | `docs/workflow.md`, `docs/devin-reference.md` | — |
| Research findings | [`knowledge/research/`](./knowledge/research/) | Primary sources from `source:` frontmatter |
| Specific number / date / quote | **Primary source** (URL / code / gist), not a summary note | — |
| Terms | [`docs/glossary.md`](./docs/glossary.md) | — |

**Chain-of-custody rule.** If citing a specific number, date, name,
or decision — go to the primary source and quote from there.
Summaries in `knowledge/research/` are pointers, not authoritative
sources.
Rationale: [`knowledge/research/llm-wiki-critique.md`](./knowledge/research/llm-wiki-critique.md).

**Supersession, not overwrite.** Never silently overwrite an outdated
note. Mark it `> **Status:** superseded by <link>` and keep for audit.

## Testing

- No CI yet (docs-only). Verify:
  - Markdown links resolve correctly.
  - Tables/docs render properly on GitHub.
- When `src/` exists: `make lint / typecheck / test` (see [`docs/workflow.md`](./docs/workflow.md)).

## Code Style (future)

- Python 3.11+, full type hints.
- `ruff check` + `ruff format`.
- `mypy --strict` on modules.
- `pytest`; LLM client and network mocked in tests.
- Prompts as files in `src/<module>/prompts/`, not Python strings.
