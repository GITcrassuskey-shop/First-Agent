---
title: "Efficient LLM agent harness — research note for First-Agent ADR-7"
source:
  - "https://arxiv.org/abs/2603.25723"
  - "https://arxiv.org/html/2603.25723"
  - "https://arxiv.org/abs/2603.28052v1"
  - "https://arxiv.org/html/2603.28052v1"
  - "https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool"
  - "https://docs.brightdata.com/ai/mcp-server/tools"
  - "https://www.anthropic.com/news/model-context-protocol"
  - "https://www.anthropic.com/engineering/code-execution-with-mcp"
  - "https://modelcontextprotocol.io/specification/2025-11-25"
  - "https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation"
  - "user attachment: youtube_transcripts.md (Devin attachment 67357fd4-8809-44d8-981e-8b6b48589af2)"
  - "../adr/ADR-1-v01-use-case-scope.md"
  - "../adr/ADR-2-llm-tiering.md"
  - "../adr/ADR-3-memory-architecture-variant.md"
  - "../adr/ADR-4-storage-backend.md"
  - "../adr/ADR-5-chunker-tool.md"
  - "../adr/ADR-6-tool-sandbox-allow-list.md"
  - "./how-to-build-an-agent-ampcode-2026-04.md"
  - "./cutting-edge-agent-research-radar-2026-05.md"
compiled: "2026-05-06"
chain_of_custody: |
  Source facts are taken from the arXiv abstracts / HTML pages, Anthropic
  and Bright Data documentation pages listed above, and the user-provided
  YouTube transcript attachment downloaded to the local Devin session. The
  transcript is treated as secondary commentary: specific paper/doc claims are
  cross-checked against primary URLs when the primary page was reachable.
  Mapping to First-Agent is inferred from current repo files on `main`, especially
  ADR-1..6, `docs/architecture.md`, and prior harness/tool research notes.
goal_lens: "Prepare ADR-7 inner-loop / tool-contract choices for an efficient First-Agent v0.1 harness without expanding v0.1 scope."
tier: stable
links:
  - "../adr/ADR-1-v01-use-case-scope.md"
  - "../adr/ADR-2-llm-tiering.md"
  - "../adr/ADR-3-memory-architecture-variant.md"
  - "../adr/ADR-4-storage-backend.md"
  - "../adr/ADR-5-chunker-tool.md"
  - "../adr/ADR-6-tool-sandbox-allow-list.md"
  - "./how-to-build-an-agent-ampcode-2026-04.md"
  - "./cutting-edge-agent-research-radar-2026-05.md"
mentions:
  - "Natural-Language Agent Harnesses"
  - "Intelligent Harness Runtime"
  - "Meta-Harness"
  - "MCP"
  - "Tool search tool"
  - "Code execution with MCP"
  - "Bright Data MCP Groups"
  - "subtraction principle"
confidence: inferred
claims_requiring_verification:
  - "Video-transcript benchmark numbers may contain transcription errors; paper/doc claims should be re-opened at the primary URLs before becoming ADR text."
  - "The note recommends ADR-7 inputs, not accepted architecture decisions."
  - "Code execution with MCP is powerful but needs a real execution sandbox; this note does not prove First-Agent can safely ship it in v0.1."
superseded_by: ""
---

> **Status:** active. Note produced via
> [`knowledge/prompts/research-briefing.md`](../prompts/research-briefing.md),
> but the `goal_lens:` was inferred from the user's explicit task rather than
> elicited in a separate blocking question.
>
> §0 below is the Decision Briefing intended for the project lead and
> future LLM agents. §1.. are the deep-dive sections; load them only when
> §0 is insufficient.

## 0. Decision Briefing

### R-1 — Make ADR-7 a subtraction-first harness contract

- **What:** ADR-7 should define the minimal executable harness for UC1/UC3:
  loop, context policy, tool registry, hooks, permissions, durable trace, and
  stop conditions. Treat extra verifiers, critic loops, multi-candidate search,
  and sub-agent routing as opt-in later modules, not defaults.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: YES (~one ADR-level contract prevents
    future agents from re-reading multiple harness notes before implementation)
  - (B) helps LLM find context when needed: YES (ADR-7 becomes the canonical
    pointer for inner-loop/tool-contract questions)
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens "Prepare ADR-7 inner-loop / tool-contract
    choices for an efficient First-Agent v0.1 harness without expanding v0.1
    scope.": YES (it turns the research into the exact ADR slot already reserved)
- **Cost:** medium (1-4h)
- **Verdict:** TAKE
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Keep recommendations as research/backlog and let
  the first inner-loop implementation discover the contract ad hoc.
- **Concrete first step (if TAKE):** Draft `knowledge/adr/ADR-7-inner-loop-tool-contract.md`
  from §6.1 and cross-link ADR-2 / ADR-6.

### R-2 — Add tiered tool disclosure before adding more tools

- **What:** The v0.1 tool registry should expose only lightweight descriptors by
  default (`name`, one-line `description`, permission, maybe tags) and load full
  schemas only for selected tools. This mirrors tool search / dynamic context
  loading without depending on Anthropic's API feature.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: YES (keeps tool schemas out of the initial
    prompt)
  - (B) helps LLM find context when needed: YES (descriptor → schema is an
    explicit progressive-disclosure path)
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens "Prepare ADR-7 inner-loop / tool-contract
    choices for an efficient First-Agent v0.1 harness without expanding v0.1
    scope.": YES (it is a tool-contract rule, not new infrastructure)
- **Cost:** cheap (<1h for ADR text; medium when implemented)
- **Verdict:** TAKE
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Hard-code a small v0.1 tool list in the system
  prompt and revisit only after context bloat appears.
- **Concrete first step (if TAKE):** Add `ToolSpec.summary()` / `ToolSpec.schema()`
  split to the ADR-7 contract.

### R-3 — Keep code-execution-over-MCP out of v0.1, but design for it

- **What:** Do not ship a general code execution bridge over MCP in v0.1. Do make
  internal tool names, schemas, errors, traces, and filesystem discovery compatible
  with later code-mode / MCP exposure.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: PARTIAL (future-ready naming helps, but the
    feature itself is deferred)
  - (B) helps LLM find context when needed: YES (tool-as-files and registry search
    are future-compatible discovery surfaces)
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens "Prepare ADR-7 inner-loop / tool-contract
    choices for an efficient First-Agent v0.1 harness without expanding v0.1
    scope.": YES (it preserves efficiency upside without violating ADR-1 scope)
- **Cost:** cheap for design guardrail; expensive if implemented now
- **Verdict:** DEFER
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Implement direct MCP server integration now, accepting
  sandbox and token-surface complexity before the first module exists.
- **Concrete first step (if TAKE):** In ADR-7, mark `ToolRegistry.export_code_api()`
  as v0.2 and reserve stable IDs now.

### R-4 — Make raw trace files the eval substrate, summaries only the index

- **What:** Every harness run should append structured JSONL events and keep raw
  tool outputs / error details addressable on disk. Summaries (`hot.md`, handoff,
  eval cards) should point to raw traces, not replace them.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: YES (future agents read a small summary first)
  - (B) helps LLM find context when needed: YES (raw trace paths support selective
    grep/replay when summaries are insufficient)
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens "Prepare ADR-7 inner-loop / tool-contract
    choices for an efficient First-Agent v0.1 harness without expanding v0.1
    scope.": YES (Meta-Harness evidence says compressed feedback loses signal)
- **Cost:** medium (trace schema + writer + retention rule)
- **Verdict:** TAKE
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Store only final summaries and accept weaker failure
  diagnosis / meta-eval later.
- **Concrete first step (if TAKE):** Add `~/.fa/state/runs/<run_id>/events.jsonl`
  and artifact-path fields to ADR-7.

### R-5 — Do not add Critic / verifier loops to v0.1 by default

- **What:** Keep ADR-2's no-Critic stance. Use deterministic checks (sandbox,
  schema validation, linters/tests, git status, CI) as gates; reserve LLM Critic,
  reflection, and multi-candidate search for measured v0.2 experiments.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: YES (fewer default roles and prompts)
  - (B) helps LLM find context when needed: PARTIAL (less generated critique to
    search; more reliance on deterministic logs)
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens "Prepare ADR-7 inner-loop / tool-contract
    choices for an efficient First-Agent v0.1 harness without expanding v0.1
    scope.": YES (prevents scope creep and token waste)
- **Cost:** cheap
- **Verdict:** TAKE
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Add an always-on Reflector/Critic role and measure
  if success improves enough to justify extra cost.
- **Concrete first step (if TAKE):** In ADR-7, state `critic_loop = out_of_scope_v0.1`
  and list deterministic validation gates instead.

### Summary

| R-N | Verdict | Project-fit (A / B) | Goal-fit (C) | Cost | Alternative-if-rejected | User decision needed? |
|-----|---------|---------------------|--------------|------|--------------------------|------------------------|
| R-1 | TAKE | YES / YES | YES (ADR-7) | medium | Research/backlog only | No (TAKE) |
| R-2 | TAKE | YES / YES | YES (tool contract) | cheap→medium | Small hard-coded prompt tool list | No (TAKE) |
| R-3 | DEFER | PARTIAL / YES | YES (scope guard) | cheap now / expensive if built | Direct MCP now | No (DEFER) |
| R-4 | TAKE | YES / YES | YES (eval substrate) | medium | Summary-only memory | No (TAKE) |
| R-5 | TAKE | YES / PARTIAL | YES (scope control) | cheap | Always-on Critic | No (TAKE) |

## 1. TL;DR

- Harness ≠ framework. Harness is the fixed control surface that turns a one-shot
  model into an agent: loop, state, tools, permissions, context, validation, and
  stopping.
- The two 2026 papers strengthen an existing First-Agent intuition: the reusable
  asset is not only the model tier, but the external harness around it.
- For FA v0.1 the right move is not "more orchestration"; it is a small, explicit,
  inspectable ADR-7 contract that can be ablated later.
- Tool-token efficiency should start with progressive disclosure: descriptor first,
  schema on demand, full external MCP/code execution deferred.
- Raw traces matter. Meta-Harness-style learning depends on code, scores, and
  execution traces being stored on a filesystem, not collapsed into short summaries.
- ADR-2 and ADR-6 are already directionally correct: static role routing, MCP-shaped
  tools, no Critic in v0.1, and sandbox as canonical pre-tool gate.
- The main new recommendation is to make "subtraction" an explicit design norm:
  every harness component must justify its token/runtime/security cost.

## 2. Scope, метод

**Goal-lens (verbatim):** "Prepare ADR-7 inner-loop / tool-contract choices for an
 efficient First-Agent v0.1 harness without expanding v0.1 scope."

Sources read:

- the user-provided transcript of three videos;
- primary pages for the two papers and the linked Anthropic / Bright Data / MCP docs;
- ADR-1..6, `docs/architecture.md`, and prior First-Agent research notes on Amp,
  MCP/tooling radar, and harness-adjacent design.

Method:

1. Extract core harness claims from the transcript.
2. Verify paper/doc claims where primary URLs were reachable.
3. Map each claim to accepted ADR constraints.
4. Convert only the high-confidence, v0.1-compatible pieces into recommendations.

Important limit: the transcript's Video 3 cites several benchmark numbers that are
not all visible in the fetched paper snippets. This note treats those numbers as
secondary evidence unless repeated in the primary abstract / docs.

## 3. Core facts known before reasoning

1. First-Agent v0.1 scope is UC1 coding+PR and UC3 local-docs-to-wiki; UC2 is
   best-effort, UC4/UC5 are deferred by [ADR-1](../adr/ADR-1-v01-use-case-scope.md).
2. [ADR-2](../adr/ADR-2-llm-tiering.md) chooses static role routing and adds two
   important amendments: `tool_protocol: native | prompt-only`, no v0.1 Critic,
   and MCP-shaped agent↔tool request/response.
3. [ADR-3](../adr/ADR-3-memory-architecture-variant.md) chooses Mechanical Wiki:
   filesystem-canonical Markdown, no Mem0, no graph, no embeddings in v0.1.
4. [ADR-4](../adr/ADR-4-storage-backend.md) chooses SQLite FTS5 as disposable BM25
   index over chunks.
5. [ADR-5](../adr/ADR-5-chunker-tool.md) chooses `universal-ctags` + `markdown-it-py`
   and gives the chunker contract.
6. [ADR-6](../adr/ADR-6-tool-sandbox-allow-list.md) makes sandbox/path allow-list
   mandatory before filesystem-touching tools.
7. `docs/architecture.md` already frames agents as Instruction / Execution /
   Integration layers and names Feedback Loop as the central pattern.
8. The Amp note already shows a minimal coding agent is `LLM + loop + tools`, but
   FA needs Python, sandboxing, traces, and role routing around that shape.
9. The new paper/doc sources do not require changing ADR-1..6; they sharpen what
   ADR-7 should contain.
10. Missing information at kickoff: exact content of the transcript and primary
    paper/doc pages. That context was fetched before writing this note.

## 4. Key concepts

- **Harness:** orchestration layer that determines control flow, context, tools,
  state, validation, permissions, and stop conditions around one or more LLM calls.
- **Framework:** abstractions a human uses to assemble an agent; not the shipped
  task-running loop itself.
- **Natural-Language Agent Harness (NLAH):** Tsinghua paper term for an executable,
  structured natural-language representation of harness logic.
- **Intelligent Harness Runtime (IHR):** runtime that interprets an NLAH under a
  charter, backend tools, child-agent lifecycle, state, and contracts.
- **Meta-Harness:** Stanford/MIT paper system that searches over harness code using
  full prior source, scores, and execution traces stored on a filesystem.
- **Progressive disclosure:** expose minimal descriptors first; load full context,
  schemas, or data only after the agent proves relevance.
- **Subtraction principle:** do not add harness structure by default; remove or
  defer components whose assumptions are no longer justified.
- **Code execution with MCP:** presenting MCP tools as code/files so the model can
  load only needed tool definitions and keep intermediate data out of context.

## 5. Mapping / analysis

### 5.1 Harness definition vs current FA architecture

The transcript's compact definition — a harness is the fixed architecture that
turns a model into an agent — matches First-Agent's existing architecture note.
The useful refinement is that a harness is not just a prompt or not just tools:
it is the whole loop that decides what the model sees and what gets persisted.

For First-Agent this means ADR-7 should not be a narrow "tool registry" ADR. It
should lock the smallest executable inner-loop contract:

| Harness piece | Current FA anchor | ADR-7 implication |
|---|---|---|
| Iteration loop | Amp note; `docs/architecture.md` feedback loop | Formalize turn loop and stop conditions |
| Context management | ADR-3 Mechanical Wiki; `hot.md` invariant | Define initial context vs retrieved context vs trace paths |
| Tool registry | ADR-2 MCP-shaped convention | Define `ToolSpec`, descriptor/schema split, errors |
| Permissions | ADR-6 sandbox | Sandbox is pre-tool hook, not optional helper |
| Memory / persistence | ADR-3, ADR-4 | Keep raw events + summaries; filesystem canon stays source |
| Validation | Makefile / CI / pre-commit | Deterministic gates before LLM Critic |
| Sub-agents | ADR-1 UC5 deferred | Out of v0.1 except future-compatible trace shape |

### 5.2 Natural-language harnesses: relevant, but not a new runtime now

The NLAH paper's primary contribution is representational: harness control logic
becomes an explicit, editable artifact with contracts, roles, stage structure,
adapters, scripts, state semantics, and failure taxonomy. The paper separates
runtime policy from task-family harness logic.

This is highly compatible with the current repo because First-Agent already uses
`AGENTS.md`, prompts, ADRs, research notes, and handoff files as executable-ish
natural language. But the v0.1 implementation should not introduce a generic IHR.
That would compete with the immediate Phase M goal. Instead:

- write ADR-7 in a contract-first style that future agents can execute from text;
- keep deterministic low-level code for sandbox, tool dispatch, and validation;
- use the note/ADR/prompt corpus as the natural-language harness layer.

This is the out-of-the-box synthesis: **First-Agent already has the text half of
NLAH; ADR-7 should be the bridge to the code half.** No new runtime is needed to
capture the benefit.

### 5.3 Meta-Harness: raw traces are more valuable than polished summaries

Meta-Harness optimizes harness code by letting a coding agent inspect all prior
candidate code, scores, and execution traces on a filesystem. Its abstract reports:

- +7.7 points over a state-of-the-art context-management system on online text
  classification while using 4× fewer context tokens;
- +4.7 points on average across five held-out models for retrieval-augmented math
  reasoning;
- top/better-than-hand-engineered results on TerminalBench-2 in the reported setup.

The operational lesson for FA is not "build Meta-Harness now". The lesson is:

1. do not destroy raw experience;
2. store traces where future agents can grep them;
3. make summaries an index over raw logs;
4. evaluate harness changes as versioned artifacts.

This directly supports ADR-3's filesystem-first memory and argues for an ADR-7
trace folder shape before any self-improving harness work exists.

### 5.4 Tool-token efficiency: stack cheap controls before heavy code mode

The transcript and linked docs describe several token-reduction layers:

| Technique | Primary-source claim | FA v0.1 fit |
|---|---|---|
| Tool search | Anthropic docs: multi-server setup can consume ~55k tool-definition tokens; tool search reduces this by >85% and loads 3-5 tools | Implement shape locally via descriptor → schema; no Anthropic-specific dependency |
| Bright Data groups | Docs expose Rapid / Pro / 11 Groups and `GROUPS` config | Use as design analogy for tool tags/groups, not a dependency |
| Custom tool list | Transcript: load exact tools after discovery | Good for production recipes / Skills, but too rigid as only mechanism |
| Dynamic context loading | Three-level disclosure: server → tool list → full schema | Best fit for ADR-7 registry |
| Programmatic tool calling | Intermediate results stay outside model context | Defer; requires code execution tool semantics |
| Code execution with MCP | Anthropic blog: tool-as-file discovery, 150k → 2k tokens in example (98.7%) | Defer implementation; reserve stable filesystem/export shape |
| Output stripping / compact formats | Strip formatted web/page output; TOON helps flat tabular data | Good principle for tool result summaries; avoid new notation as default |

The efficient path is additive but staged:

1. v0.1: descriptor-first registry + compact `ToolResult.summary` + raw artifact path.
2. v0.1: groups/tags for tools, but only if more than ~10 tools exist.
3. v0.2: search over tool catalog if schema list grows.
4. v0.2+: code execution / MCP tool-as-files if sandbox maturity supports it.

### 5.5 MCP: standard boundary, not a license to load every tool

MCP is the ecosystem's standard integration protocol: hosts, clients, servers;
resources, prompts, tools; JSON-RPC; capability negotiation; consent and safety.
Anthropic's launch post frames it as replacing fragmented integrations with one
protocol. The spec emphasizes user consent/control, privacy, tool safety, and
authorization flows.

ADR-2's 2026-05-01 amendment is therefore correct: pin to MCP shape, not MCP
transport. The new efficiency evidence adds one more warning: **MCP compatibility
and context efficiency are separate problems.** A naive MCP client that loads all
schemas into the system prompt can be standard-compliant and still wasteful.

ADR-7 should therefore say:

- tool identity/schema/error shape is MCP-compatible;
- initial prompt gets only small descriptors;
- full schemas are loaded only when selected;
- external MCP servers are out of v0.1;
- security/consent are enforced before tool execution, per ADR-6.

### 5.6 Subtraction beats maximal architecture for FA v0.1

Video 3 emphasizes a pattern also consistent with ADR-2's no-Critic amendment:
more harness modules can hurt. The transcript cites ablations where self-evolution
helped consistently while verifiers and multi-candidate search sometimes hurt. Even
if exact numbers need primary-paper recheck, the design lesson is safe:

- a verifier is not automatically safer if it consumes budget, adds wrong vetoes,
  or hides deterministic failures behind prose;
- multi-candidate search is not free if UC1 acceptance is a single PR path;
- sub-agents are not free because they multiply state, permissions, and traces.

For FA, subtraction means:

1. build the boring loop first;
2. log enough to evaluate failure modes;
3. add Critic/search/sub-agents only when a trace-backed failure pattern justifies
   the extra module.

## 6. Cross-reference against ADR-1..6

| ADR | Existing decision | New note's effect |
|---|---|---|
| ADR-1 — scope | UC1 + UC3 in; UC4/UC5 deferred | Supports scope discipline: no generic IHR, no code-exec MCP bridge, no multi-agent harness in v0.1 |
| ADR-2 — tiering | Static roles; native tool calls; no Critic; MCP-shaped tools | Strengthens ADR-7 inheritance; adds descriptor/schema progressive disclosure as likely contract detail |
| ADR-3 — memory | Mechanical Wiki; filesystem canon; no Mem0/graph/embeddings | Strongly supported by Meta-Harness: raw filesystem traces are a feature, not a compromise |
| ADR-4 — storage | SQLite FTS5 disposable index | Supports tool/search catalog via BM25 later; no new vector need for tool search in v0.1 |
| ADR-5 — chunker | ctags + markdown-it-py | No change; chunker remains prerequisite for context-efficient retrieval |
| ADR-6 — sandbox | Deny-by-default path allow-list; audit log | Strengthened: permissions/hook layer is core harness, especially before code execution or MCP expansion |

### 6.1 Draft ADR-7 contract sketch

```text
ADR-7 Inner-loop / tool contract (candidate shape)

Scope:
  - v0.1 UC1/UC3 single-agent loop only
  - no Critic, no multi-agent orchestration, no external MCP server dependency

Runtime loop:
  1. assemble static prompt prefix
  2. load dynamic repo/session context by pointers, not full dumps
  3. expose compact tool descriptors
  4. receive model response
  5. if tool call: validate schema → sandbox pre_tool → execute → post_tool audit
  6. append JSONL event + artifact paths
  7. return compact result summary to model
  8. stop on explicit final answer, max iterations, hard error, or user approval gate

ToolSpec:
  name: stable dotted string
  description: one-line model-facing summary
  input_schema: JSON Schema, loaded on demand
  permission: read | workspace | full
  tags: repo | search | git | test | memory
  handler: deterministic callable hidden behind dispatcher

ToolResult:
  result: compact structured payload | null
  error: { code: int, message: str, retryable: bool } | null
  summary: short model-facing text
  artifacts: paths to raw output / diff / logs

Trace:
  ~/.fa/state/runs/<run_id>/events.jsonl
  ~/.fa/state/runs/<run_id>/artifacts/*
```

This sketch deliberately reuses ADR-2's MCP-shaped convention and ADR-6's sandbox
rather than inventing a parallel tool protocol.

## 7. Risks and caveats

1. **Transcript numbers are secondary.** Some Video 3 benchmark details were not
   visible in the fetched snippets. Treat them as leads, not ADR-ready facts.
2. **Code execution with MCP is security-heavy.** The token savings are real in
   Anthropic's example, but FA cannot safely expose arbitrary code execution until
   sandbox, permissions, resource limits, and artifact redaction exist.
3. **Tool search may be premature if v0.1 has only a few tools.** Descriptor/schema
   split is cheap; full BM25 tool search should wait for catalogue size.
4. **Natural-language harnesses can drift.** If ADR-7 becomes executable guidance,
   implementation tests must keep code behavior aligned with text.
5. **Subtraction can go too far.** Removing verifiers is good only when deterministic
   checks cover the risk. For filesystem writes, sandbox and tests are non-negotiable.

## 8. Numbered recommendations (R-1..R-5)

### R-1 — Make ADR-7 a subtraction-first harness contract (cost: medium)

ADR-7 should be the place where future agents stop debating what the inner loop is.
It should specify only the pieces needed for UC1/UC3: turn loop, context assembly,
tool dispatch, permission checks, trace writes, deterministic validation, and stop
conditions. The hard part is not inventing more roles; it is preventing implicit
runtime behavior from spreading across code, prompts, and notes.

The "subtraction-first" wording matters because the source set repeatedly warns
that harness structure has cost. Critic loops, verifiers, multi-candidate search,
and sub-agents can all be useful, but each introduces extra context, failure modes,
and audit surface. For FA v0.1 they should be marked out of scope unless a trace
proves a specific need.

### R-2 — Add tiered tool disclosure before adding more tools (cost: cheap→medium)

A minimal FA registry can copy the insight behind Anthropic tool search without
copying the product feature. The model initially sees small tool descriptors. When
it chooses a tool, the runtime validates against that tool's full schema. If the
catalog grows, a local `repo.search_tools` or BM25-backed catalog can be added.

This aligns with ADR-4 because SQLite FTS5 already exists as the project's chosen
search primitive, and with ADR-2 because JSON Schema is already the agreed tool
shape. It is a cheap way to keep the initial prompt small and make tool selection
less noisy.

### R-3 — Keep code-execution-over-MCP out of v0.1, but design for it (cost: cheap now / expensive if built)

Anthropic's code-execution-with-MCP pattern is the most dramatic efficiency lever
in the source set: tool definitions become files, intermediate data stays in the
execution environment, and only final summaries return to the model. But that is
exactly why it is risky. It requires strong sandboxing, resource limits, data-flow
redaction, and a trustworthy API surface.

FA v0.1 should therefore reserve the shape, not ship the feature. Stable tool names,
JSON schemas, compact results, raw artifact paths, and maybe a future
`tools/as_files/` export are enough to avoid redesign later.

### R-4 — Make raw trace files the eval substrate, summaries only the index (cost: medium)

Meta-Harness is a warning against over-summarizing. Its proposer improves harnesses
by inspecting prior source, scores, and raw traces through the filesystem. This is
nearly the same philosophy as Mechanical Wiki: keep the canonical data inspectable,
then index/summarize for convenience.

For FA, every loop turn should write JSONL events with tool request, permission
result, compact output, raw artifact path, model role, token/cost metadata if known,
and stop reason. Human-friendly summaries can live in `hot.md` or handoff notes,
but they should cite raw trace paths.

### R-5 — Do not add Critic / verifier loops to v0.1 by default (cost: cheap)

ADR-2 already says no Critic in v0.1. The harness sources support that posture:
verification logic is not automatically helpful, and a verifier can become another
model call that must itself be interpreted, logged, and debugged. Deterministic
checks are different: schema validation, sandbox denial, syntax/lint/type/test/CI
results are cheap evidence and should be part of the loop.

A future v0.2 Critic should be triggered by measured failure classes, not aesthetic
symmetry. Example trigger: repeated traces where deterministic checks pass but PR
review finds semantic bugs that a second LLM consistently catches.

## 9. Open questions (Q-1..Q-5)

### Q-1 — What is the exact first v0.1 tool list?

ADR-7 can define the registry shape before the implementation picks the first
names. Likely candidates are `repo.read`, `repo.search`, `repo.edit`, `git.status`,
`test.run`, and `memory.write_hot`, but this should be finalized with the first
inner-loop PR.

### Q-2 — Should tool descriptors be indexed immediately?

If the first catalog has fewer than ~10 tools, a plain list is enough. BM25 tool
search becomes worthwhile when descriptors exceed the model's reliable selection
range or when external MCP catalogs enter scope.

### Q-3 — What trace retention policy is acceptable?

Raw traces are useful but can contain private code or tool outputs. ADR-7 should
choose default local retention and redaction rules before traces become long-lived.

### Q-4 — Where does `hot.md` end and JSONL trace begin?

A useful split: `hot.md` is session-level human/agent handoff; JSONL is replayable
machine trace. The former summarizes; the latter is source-of-truth for eval.

### Q-5 — How should future code-execution mode be sandboxed?

ADR-6 handles path allow-lists, but code execution needs CPU/time/network limits,
process isolation, and output redaction. This is probably a separate v0.2 ADR.

## 10. Files used

- User-provided attachment `youtube_transcripts.md` (downloaded in-session to
  `/home/ubuntu/attachments/77691155-ce86-46fe-99dd-24028b1facba/youtube_transcripts.md`)
- <https://arxiv.org/abs/2603.25723>
- <https://arxiv.org/html/2603.25723>
- <https://arxiv.org/abs/2603.28052v1>
- <https://arxiv.org/html/2603.28052v1>
- <https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool>
- <https://docs.brightdata.com/ai/mcp-server/tools>
- <https://www.anthropic.com/news/model-context-protocol>
- <https://www.anthropic.com/engineering/code-execution-with-mcp>
- <https://modelcontextprotocol.io/specification/2025-11-25>
- <https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation>
- [`../adr/ADR-1-v01-use-case-scope.md`](../adr/ADR-1-v01-use-case-scope.md)
- [`../adr/ADR-2-llm-tiering.md`](../adr/ADR-2-llm-tiering.md)
- [`../adr/ADR-3-memory-architecture-variant.md`](../adr/ADR-3-memory-architecture-variant.md)
- [`../adr/ADR-4-storage-backend.md`](../adr/ADR-4-storage-backend.md)
- [`../adr/ADR-5-chunker-tool.md`](../adr/ADR-5-chunker-tool.md)
- [`../adr/ADR-6-tool-sandbox-allow-list.md`](../adr/ADR-6-tool-sandbox-allow-list.md)
- [`./how-to-build-an-agent-ampcode-2026-04.md`](./how-to-build-an-agent-ampcode-2026-04.md)
- [`./cutting-edge-agent-research-radar-2026-05.md`](./cutting-edge-agent-research-radar-2026-05.md)
- [`../../docs/architecture.md`](../../docs/architecture.md)

## 11. Out of scope

- Writing ADR-7 itself.
- Implementing the inner-loop, tool registry, sandbox, or trace writer.
- Building real MCP servers or MCP clients.
- Implementing code execution / programmatic tool calling.
- Choosing final model/provider slugs.
- Retrofitting old research notes into the §0 Decision Briefing format.
