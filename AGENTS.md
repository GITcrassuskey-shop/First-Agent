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

- **Session bootstrap.** At the start of any new agent session, fetch
  [`knowledge/llms.txt`](./knowledge/llms.txt) first. It is the
  project map for LLM agents. files are reachable from there in
  one hop. Do not crawl the repo before reading this file.
- All documentation is Markdown. ATX headings (`#`, `##`), short lines ~150 chars.
- Fenced code blocks
  - ALWAYS open with a language tag:
    - Code: `python`, `yaml`, `json`, `bash`.
    - Non-code (ASCII art, directory trees, prompts, logs): `text`.
  -Close with bare ` ``` `.
- New docs go in the right folder:
  - Guides / references → `docs/`. Update [`docs/README.md`](./docs/README.md).
  - Project artifacts (decisions, research, prompts) → `knowledge/`.
- Research notes are read by both humans and agents. Prefer Russian for
  analytical prose, project recommendations. Keep protocol names, API field names, code,
  and direct quotes in their source language.
- readability > size
- Architectural decisions → ADR from [`knowledge/adr/ADR-template.md`](./knowledge/adr/ADR-template.md).

## PR Checklist

Verify before opening a PR. Each item has triggered wasted review cycles.

1. **Code fences have language tags.** No bare ` ``` ` at opening! See rule above.
2. **Frontmatter uses `compiled:`, not `date:`.** Schema: [`knowledge/README.md`](./knowledge/README.md#conventions).
3. **File length within tier limits.**
   - Summaries / overviews: **<1000 lines**.
   - Deep-dive research: **<2000 lines**.
   - Readability > size
4. **`compiled:` date ≥ all dates cited in text.** No temporal impossibilities.
5. **Supersession, not overwrite.** Mark old file `> **Status:** superseded by <link>`. Keep for audit.
6. **PR description lists changed/new files as clickable blob-URLs**
   (`https://github.com/<owner>/<repo>/blob/<branch>/<path>`), at
   least for non-trivial files. Plain bullet text is insufficient —
   reviewers should be able to open each file in one click without
   copy-pasting paths. Use the head branch of the PR, not `main`.
7. **`knowledge/llms.txt` reflects reality.** If this PR adds,
   removes, or renames any file under `docs/` or `knowledge/`, update
   the corresponding entry (or add / remove a row) in
   [`knowledge/llms.txt`](./knowledge/llms.txt). The index is
   hand-maintained; it drifts silently if not enforced on every PR.
   A pre-commit hook or generator can be added later (see
   [`docs/workflow.md`](./docs/workflow.md) Phase S).

## Stacked / sequenced PRs

Some PRs intentionally reference files, sections, or amendments that
are added in a parallel PR not yet merged to `main`. Example: a
`HANDOFF.md` update PR pointing to ADR amendments that live in a
sibling research-note PR. This is a normal part of the project's
small-PR review style, not a defect. The convention:

1. **Document the dependency.** In the dependent PR (`B`)
   description, state explicitly: «Recommended merge order: PR `A`
   → PR `B`». Reference `A` by number and link.
2. **Expect "broken reference" findings from review tooling.**
   Devin Review and other reference-checkers will flag links / file
   references that are not yet on `main` as broken. This is
   expected. Reply in-thread «Resolves on merge order PR `A` →
   PR `B`» with the link to PR `A`. Do not silence the bot or
   change the PR to remove the reference.
3. **Do not pre-emptively rebase `B` onto `A`.** Rebasing creates
   a fragile chain that breaks when `A` is squash-merged (commit
   hashes differ on `main` vs in the rebase base). Only rebase if
   (i) `A` is days away from merging and (ii) reviewer explicitly
   requests it.
4. **Atomic-coupling exception.** If `A` and `B` must merge
   together because separating them would leave `main` in a
   broken state — combine them into a single PR. Stacked PRs are
   only for cases where `B` is *useful but stale-looking* without
   `A`, not where `B` is *broken* without `A`.
5. **Each PR must still pass its own pre-commit / lint / format
   checks.** Stacked-PR convention covers cross-PR semantic
   references; it does **not** waive code-quality or
   AGENTS.md-rules in either PR individually.

## Development Workflow

- Branch: `devin/<timestamp>-<slug>` from `main`.
- All changes via Pull Request.
- Commit messages: descriptive, English, present tense (`docs: add architecture note`).
- Never push directly to `main`.
- **`AI-Session:` git trailer.** When a commit is driven by a Devin
  (or other LLM-agent) session, add an `AI-Session: <session-id>`
  trailer to the commit message. This preserves the link from a
  squash-merged commit back to the originating session for audit and
  re-entry. Pattern lifted from `codedna` (see
  [`research/agentic-memory-supplement.md` §3](./knowledge/research/agentic-memory-supplement.md)).
  Example:

  ```text
  docs: add ADR-N on <topic>

  Body...

  AI-Session: 2f45f66ef9ff45eab03161ecef165c0e
  Co-Authored-By: <human> <email>
  ```

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
