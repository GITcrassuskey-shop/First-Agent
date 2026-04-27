# RESOLVER — intent-to-prompt dispatcher

Explicit mapping from user / agent intent to the prompt template
that should be loaded. Pattern lifted from gbrain
(see [`research/agentic-memory-supplement.md` §4](../research/agentic-memory-supplement.md)).

The point of this file is that an agent dropped into the repo can
decide which prompt to load **without rereading every prompt file**.

## How to use this file

1. Identify the intent from the user request (left column).
2. Load the prompt indicated in the right column verbatim into
   the LLM call.
3. Fill in the `<placeholders>` from the request before sending.
4. Follow the `[Acceptance]` block of the chosen prompt as the
   exit criterion.

If no row matches, the request is out of scope for the current
prompt library — escalate to the user or open a research note via
T1 first.

## Intent table

| Intent | Trigger phrases (examples) | Template | File |
|---|---|---|---|
| Research a topic and produce a structured note | "investigate X", "summarise the literature on Y", "compare papers on Z" | T1 | [`research-topic.md`](./research-topic.md) |
| Scaffold a new code module with tests | "scaffold module M", "create the skeleton for `src/<m>/`", "set up the package for X" | T2 | (no file yet — see [`docs/prompting.md` §T2](../../docs/prompting.md)) |
| Compare two implementation approaches | "A vs B", "two parallel PRs for <feature>", "benchmark approach 1 against approach 2" | T3 | (no file yet — see [`docs/prompting.md` §T3](../../docs/prompting.md)) |
| Co-develop a PRD (no code) | "draft the PRD for <feature>", "spec X before we build" | T4 | (no file yet — see [`docs/prompting.md` §T4](../../docs/prompting.md)) |
| Reproduce a bug with a failing test, then fix | "reproduce <bug>", "write a failing test for X then patch", "TDD this regression" | T5 | (no file yet — see [`docs/prompting.md` §T5](../../docs/prompting.md)) |
| Plan an architectural change as Architect / Planner role | "plan the change", "Architect, design the rollout", "draft the migration plan" | role | [`architect-fa.md`](./architect-fa.md) (full) or [`architect-fa-compact.md`](./architect-fa-compact.md) (compact) |
| Record an architectural decision | "record the decision", "open an ADR for X", "we decided Y, write it up" | ADR | [`../adr/ADR-template.md`](../adr/ADR-template.md) |

## Notes on the role-prompt rows

The Architect / Planner files in this folder are **system prompts** —
load them in the `system` slot of the API call, not as a Devin task.
See [`prompts/README.md` §Note on system prompts vs. task prompts](./README.md#note-on-system-prompts-vs-task-prompts).

## When to add a row

Add a row when the same intent has come up twice and resolved to the
same template both times. Do not pre-populate speculative rows — RESOLVER
is a record of patterns we have already seen, not a wishlist.
