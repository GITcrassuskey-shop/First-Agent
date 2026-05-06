---
title: "Efficient LLM agent harness — исследовательская заметка для First-Agent ADR-7"
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
  Факты взяты из arXiv abstract / HTML pages, документации Anthropic,
  документации Bright Data и user-provided YouTube transcript attachment,
  скачанного в локальную Devin-сессию. Transcript используется как вторичный
  источник: claims о paper/doc сверялись с primary URLs, когда primary page была
  доступна. Mapping на First-Agent выведен из текущих repo files на `main`,
  особенно ADR-1..6, `docs/architecture.md` и предыдущих harness/tool research
  notes.
goal_lens: "Подготовить решения для ADR-7 inner-loop / tool-contract: эффективный First-Agent v0.1 harness без расширения v0.1 scope."
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
  - "Числа из video transcript могут содержать ошибки распознавания; перед переносом в ADR нужно повторно открыть primary paper/doc URLs."
  - "Заметка даёт input для ADR-7, но не является принятой архитектурной decision."
  - "Code execution with MCP даёт сильную token-efficiency, но требует настоящего execution sandbox; эта заметка не доказывает, что feature безопасна для v0.1."
superseded_by: ""
---

> **Status:** active. Заметка подготовлена по workflow
> [`knowledge/prompts/research-briefing.md`](../prompts/research-briefing.md),
> но `goal_lens:` был выведен из явного user task, а не elicited отдельным
> blocking question.
>
> §0 — Decision Briefing для project lead и будущих LLM agents. §1.. — deep dive;
> загружайте их только если §0 недостаточно.

## 0. Decision Briefing

### R-1 — Описать ADR-7 как subtraction-first harness contract

- **What:** ADR-7 должен зафиксировать минимальный исполнимый harness для UC1/UC3:
  loop, context policy, tool registry, hooks, permissions, durable trace и stop
  conditions. Critic, extra verifiers, multi-candidate search и sub-agents должны
  быть opt-in later modules, а не default.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: YES (~один ADR-level contract избавит будущих
    agents от перечитывания нескольких harness notes перед implementation)
  - (B) helps LLM find context when needed: YES (ADR-7 станет canonical pointer для
    inner-loop/tool-contract questions)
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens "Подготовить решения для ADR-7 inner-loop /
    tool-contract: эффективный First-Agent v0.1 harness без расширения v0.1
    scope.": YES (это ровно тот ADR slot, для которого нужна подготовка)
- **Cost:** medium (1-4h)
- **Verdict:** TAKE
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Оставить выводы как research/backlog и позволить
  первому inner-loop PR самому обнаружить contract ad hoc.
- **Concrete first step (if TAKE):** Draft `knowledge/adr/ADR-7-inner-loop-tool-contract.md`
  из §6.1 и cross-link ADR-2 / ADR-6.

### R-2 — Ввести tiered tool disclosure до расширения tool set

- **What:** v0.1 tool registry должен показывать model только lightweight
  descriptors by default (`name`, one-line `description`, permission, tags), а full
  schemas загружать по demand для выбранных tools. Это переносит принцип tool search
  / dynamic context loading без зависимости от Anthropic API feature.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: YES (tool schemas не попадают в initial prompt)
  - (B) helps LLM find context when needed: YES (descriptor → schema даёт явный
    progressive-disclosure path)
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens "Подготовить решения для ADR-7 inner-loop /
    tool-contract: эффективный First-Agent v0.1 harness без расширения v0.1
    scope.": YES (это правило tool-contract, а не новая infrastructure)
- **Cost:** cheap (<1h для ADR text; medium при implementation)
- **Verdict:** TAKE
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Захардкодить маленький v0.1 tool list в system prompt
  и вернуться к вопросу только после фактического context bloat.
- **Concrete first step (if TAKE):** Добавить в ADR-7 split `ToolSpec.summary()` /
  `ToolSpec.schema()`.

### R-3 — Не включать code-execution-over-MCP в v0.1, но сохранить shape

- **What:** Не shipping general code execution bridge over MCP в v0.1. Но internal
  tool names, schemas, errors, traces и filesystem discovery стоит сделать
  compatible с future code-mode / MCP exposure.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: PARTIAL (future-ready naming помогает, но сама
    feature остаётся deferred)
  - (B) helps LLM find context when needed: YES (tool-as-files и registry search —
    future-compatible discovery surfaces)
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens "Подготовить решения для ADR-7 inner-loop /
    tool-contract: эффективный First-Agent v0.1 harness без расширения v0.1
    scope.": YES (мы сохраняем efficiency upside без нарушения ADR-1 scope)
- **Cost:** cheap как design guardrail; expensive при implementation сейчас
- **Verdict:** DEFER
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Реализовать direct MCP integration уже сейчас и принять
  sandbox / token-surface complexity до появления первого feature module.
- **Concrete first step (if TAKE):** В ADR-7 отметить `ToolRegistry.export_code_api()`
  как v0.2 и зарезервировать stable IDs сейчас.

### R-4 — Сделать raw trace files eval substrate, а summaries — только index

- **What:** Каждый harness run должен писать structured JSONL events и держать raw
  tool outputs / error details адресуемыми на disk. Summaries (`hot.md`, handoff,
  eval cards) должны ссылаться на raw traces, а не заменять их.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: YES (future agents сначала читают краткий
    summary)
  - (B) helps LLM find context when needed: YES (raw trace paths дают selective
    grep/replay, когда summary недостаточно)
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens "Подготовить решения для ADR-7 inner-loop /
    tool-contract: эффективный First-Agent v0.1 harness без расширения v0.1
    scope.": YES (Meta-Harness evidence показывает, что compressed feedback теряет
    важный signal)
- **Cost:** medium (trace schema + writer + retention rule)
- **Verdict:** TAKE
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Хранить только final summaries и принять слабую
  future diagnosis / meta-eval.
- **Concrete first step (if TAKE):** Добавить в ADR-7 `~/.fa/state/runs/<run_id>/events.jsonl`
  и artifact-path fields.

### R-5 — Не добавлять Critic / verifier loops в v0.1 default

- **What:** Сохранить ADR-2 no-Critic stance. Использовать deterministic checks
  (sandbox, schema validation, linters/tests, git status, CI) как gates; LLM Critic,
  reflection и multi-candidate search оставить для measured v0.2 experiments.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: YES (меньше default roles и prompts)
  - (B) helps LLM find context when needed: PARTIAL (меньше generated critique для
    поиска; больше reliance on deterministic logs)
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens "Подготовить решения для ADR-7 inner-loop /
    tool-contract: эффективный First-Agent v0.1 harness без расширения v0.1
    scope.": YES (это снижает scope creep и token waste)
- **Cost:** cheap
- **Verdict:** TAKE
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Добавить always-on Reflector/Critic role и отдельно
  измерять, окупает ли success-rate лишний cost.
- **Concrete first step (if TAKE):** В ADR-7 зафиксировать `critic_loop = out_of_scope_v0.1`
  и перечислить deterministic validation gates.

### Summary

| R-N | Verdict | Project-fit (A / B) | Goal-fit (C) | Cost | Alternative-if-rejected | User decision needed? |
|-----|---------|---------------------|--------------|------|--------------------------|------------------------|
| R-1 | TAKE | YES / YES | YES (ADR-7) | medium | Research/backlog only | No (TAKE) |
| R-2 | TAKE | YES / YES | YES (tool contract) | cheap→medium | Small hard-coded prompt tool list | No (TAKE) |
| R-3 | DEFER | PARTIAL / YES | YES (scope guard) | cheap now / expensive if built | Direct MCP now | No (DEFER) |
| R-4 | TAKE | YES / YES | YES (eval substrate) | medium | Summary-only memory | No (TAKE) |
| R-5 | TAKE | YES / PARTIAL | YES (scope control) | cheap | Always-on Critic | No (TAKE) |

## 1. TL;DR

- Harness — это не framework и не prompt. Это control surface, который превращает
  одноразовый model call в agent: loop, state, tools, permissions, context,
  validation и stopping.
- Две 2026 papers усиливают уже существующую intuition First-Agent: reusable asset —
  не только model tier, но и внешний harness вокруг model.
- Для FA v0.1 правильный ход — не "больше orchestration", а маленький, явный,
  inspectable ADR-7 contract, который потом можно ablate.
- Tool-token efficiency стоит начинать с progressive disclosure: descriptor first,
  schema on demand, external MCP/code execution deferred.
- Raw traces важны. Meta-Harness-style learning зависит от code, scores и execution
  traces на filesystem, а не от коротких summaries.
- ADR-2 и ADR-6 уже направлены правильно: static role routing, MCP-shaped tools,
  no Critic в v0.1 и sandbox как canonical pre-tool gate.
- Новый практический вывод: сделать "subtraction" design norm. Каждый harness
  component должен оправдывать token/runtime/security cost.

## 2. Scope и метод

**Goal-lens:** "Подготовить решения для ADR-7 inner-loop / tool-contract:
эффективный First-Agent v0.1 harness без расширения v0.1 scope."

Прочитаны:

- user-provided transcript трёх videos;
- primary pages для двух papers и linked Anthropic / Bright Data / MCP docs;
- ADR-1..6, `docs/architecture.md`, previous First-Agent notes по Amp,
  MCP/tooling radar и harness-adjacent design.

Метод:

1. Выделить core harness claims из transcript.
2. Проверить paper/doc claims по primary URLs, где страницы были доступны.
3. Сопоставить claims с принятыми ADR constraints.
4. Перенести в recommendations только high-confidence pieces, совместимые с v0.1.

Ограничение: Video 3 transcript содержит benchmark numbers, которые не все видны в
fetched paper snippets. В этой заметке такие числа рассматриваются как secondary
evidence, если они не повторены в primary abstract / docs.

## 3. Основные факты перед reasoning

1. First-Agent v0.1 scope — UC1 coding+PR и UC3 local-docs-to-wiki; UC2 best-effort,
   UC4/UC5 deferred по [ADR-1](../adr/ADR-1-v01-use-case-scope.md).
2. [ADR-2](../adr/ADR-2-llm-tiering.md) выбирает static role routing и добавляет:
   `tool_protocol: native | prompt-only`, no v0.1 Critic, MCP-shaped agent↔tool
   request/response.
3. [ADR-3](../adr/ADR-3-memory-architecture-variant.md) выбирает Mechanical Wiki:
   filesystem-canonical Markdown, без Mem0, graph и embeddings в v0.1.
4. [ADR-4](../adr/ADR-4-storage-backend.md) выбирает SQLite FTS5 как disposable BM25
   index over chunks.
5. [ADR-5](../adr/ADR-5-chunker-tool.md) выбирает `universal-ctags` +
   `markdown-it-py` и задаёт chunker contract.
6. [ADR-6](../adr/ADR-6-tool-sandbox-allow-list.md) требует sandbox/path allow-list
   перед filesystem-touching tools.
7. `docs/architecture.md` уже описывает agents через Instruction / Execution /
   Integration layers и называет Feedback Loop центральным pattern.
8. Amp note уже показывает минимального coding agent как `LLM + loop + tools`, но FA
   нужно обернуть этот shape Python runtime, sandbox, traces и role routing.
9. Новые sources не требуют менять ADR-1..6; они уточняют, что должен содержать ADR-7.
10. Missing information на старте: exact transcript content и primary paper/doc pages.
    Этот context был получен до написания заметки.

## 4. Ключевые понятия

- **Harness:** orchestration layer, который управляет control flow, context, tools,
  state, validation, permissions и stop conditions вокруг одного или нескольких LLM
  calls.
- **Framework:** abstractions, которыми human собирает agent; это не обязательно тот
  task-running loop, который реально shipped.
- **Natural-Language Agent Harness (NLAH):** термин Tsinghua paper для executable,
  structured natural-language representation of harness logic.
- **Intelligent Harness Runtime (IHR):** runtime, который интерпретирует NLAH через
  charter, backend tools, child-agent lifecycle, state и contracts.
- **Meta-Harness:** Stanford/MIT paper system, который ищет harness code, используя
  full prior source, scores и execution traces на filesystem.
- **Progressive disclosure:** сначала показывать minimal descriptors; full context,
  schemas или data загружать только после relevance signal.
- **Subtraction principle:** не добавлять harness structure по умолчанию; удалять или
  откладывать components, whose assumptions больше не оправданы.
- **Code execution with MCP:** представлять MCP tools как code/files, чтобы model
  загружала только нужные definitions и не протаскивала intermediate data через
  context.

## 5. Mapping / анализ

### 5.1 Harness definition vs current FA architecture

Transcript определяет harness как fixed architecture, который превращает model в
agent. Это хорошо совпадает с текущим First-Agent architecture note. Полезное
уточнение: harness — не только prompt и не только tools. Это весь loop, который
решает, что model видит, что исполняется, что сохраняется и когда run остановлен.

Поэтому ADR-7 не должен быть узким "tool registry" ADR. Он должен закрепить
smallest executable inner-loop contract:

| Harness piece | Current FA anchor | ADR-7 implication |
|---|---|---|
| Iteration loop | Amp note; `docs/architecture.md` feedback loop | Formalize turn loop and stop conditions |
| Context management | ADR-3 Mechanical Wiki; `hot.md` invariant | Define initial context vs retrieved context vs trace paths |
| Tool registry | ADR-2 MCP-shaped convention | Define `ToolSpec`, descriptor/schema split, errors |
| Permissions | ADR-6 sandbox | Sandbox is pre-tool hook, not optional helper |
| Memory / persistence | ADR-3, ADR-4 | Keep raw events + summaries; filesystem canon stays source |
| Validation | Makefile / CI / pre-commit | Deterministic gates before LLM Critic |
| Sub-agents | ADR-1 UC5 deferred | Out of v0.1 except future-compatible trace shape |

### 5.2 Natural-language harnesses: relevant, но не новый runtime сейчас

NLAH paper важна не тем, что FA должен срочно строить generic IHR. Главный сигнал —
representational: harness control logic можно сделать explicit, editable artifact с
contracts, roles, stage structure, adapters, scripts, state semantics и failure
taxonomy. Paper также отделяет runtime policy от task-family harness logic.

Это хорошо ложится на текущий repo: First-Agent уже использует `AGENTS.md`, prompts,
ADRs, research notes и handoff files как исполнимый для agents natural-language
слой. Но v0.1 implementation не должен вводить generic IHR — это отвлечёт от Phase M.
Вместо этого:

- написать ADR-7 в contract-first style, который future agents смогут исполнять как
  text guidance;
- оставить deterministic low-level code для sandbox, tool dispatch и validation;
- считать note/ADR/prompt corpus natural-language harness layer.

Creative synthesis: **у First-Agent уже есть text half of NLAH; ADR-7 должен стать
мостом к code half.** Для этого не нужен новый runtime.

### 5.3 Meta-Harness: raw traces ценнее polished summaries

Meta-Harness оптимизирует harness code, позволяя coding agent читать все previous
candidate code, scores и execution traces на filesystem. Abstract сообщает:

- +7.7 points over state-of-the-art context-management system на online text
  classification при 4× fewer context tokens;
- +4.7 points average across five held-out models для retrieval-augmented math
  reasoning;
- лучше hand-engineered baselines на TerminalBench-2 в reported setup.

Вывод для FA — не "строить Meta-Harness сейчас". Вывод проще:

1. не уничтожать raw experience;
2. хранить traces так, чтобы future agents могли `grep` / selectively inspect;
3. делать summaries index over raw logs;
4. version harness changes как artifacts.

Это прямо поддерживает ADR-3 filesystem-first memory и требует ADR-7 trace folder
shape до появления self-improving harness work.

### 5.4 Tool-token efficiency: сначала cheap controls, потом code mode

Transcript и linked docs дают несколько layers token reduction:

| Technique | Primary-source claim | FA v0.1 fit |
|---|---|---|
| Tool search | Anthropic docs: multi-server setup может съедать ~55k tool-definition tokens; tool search снижает это на >85% и загружает 3-5 tools | Реализовать локальный shape через descriptor → schema; без Anthropic-specific dependency |
| Bright Data groups | Docs показывают Rapid / Pro / 11 Groups и `GROUPS` config | Использовать как design analogy для tool tags/groups, не как dependency |
| Custom tool list | Transcript: load exact tools after discovery | Подходит для production recipes / Skills, но слишком жёсткий как единственный mechanism |
| Dynamic context loading | Three-level disclosure: server → tool list → full schema | Лучший fit для ADR-7 registry |
| Programmatic tool calling | Intermediate results остаются вне model context | Defer; требует code execution tool semantics |
| Code execution with MCP | Anthropic blog: tool-as-file discovery, 150k → 2k tokens в example (98.7%) | Defer implementation; зарезервировать stable filesystem/export shape |
| Output stripping / compact formats | Убирать formatted web/page output; TOON помогает для flat tabular data | Хороший принцип для tool result summaries; не делать новую notation default |

Efficient path для FA staged:

1. v0.1: descriptor-first registry + compact `ToolResult.summary` + raw artifact path.
2. v0.1: groups/tags для tools, но только если tools станет больше ~10.
3. v0.2: search over tool catalog, если schema list вырастет.
4. v0.2+: code execution / MCP tool-as-files, если sandbox достаточно зрелый.

### 5.5 MCP: standard boundary, но не permission to load everything

MCP задаёт ecosystem standard boundary: hosts, clients, servers; resources, prompts,
tools; JSON-RPC; capability negotiation; consent and safety. Anthropic launch post
позиционирует MCP как замену fragmented integrations одним protocol. MCP spec особо
подчёркивает user consent/control, privacy, tool safety и authorization flows.

ADR-2 amendment от 2026-05-01 поэтому выбран правильно: pin to MCP shape, not MCP
transport. Новые efficiency sources добавляют warning: **MCP compatibility и context
efficiency — разные задачи.** Naive MCP client может загрузить все schemas в system
prompt, быть standard-compliant и всё равно тратить лишние tokens.

ADR-7 должен сказать:

- tool identity/schema/error shape is MCP-compatible;
- initial prompt получает только compact descriptors;
- full schemas загружаются only when selected;
- external MCP servers out of v0.1;
- security/consent enforced before tool execution по ADR-6.

### 5.6 Subtraction beats maximal architecture для FA v0.1

Video 3 подчёркивает pattern, совместимый с ADR-2 no-Critic amendment: больше harness
modules не всегда лучше. Transcript cites ablations, где self-evolution consistently
helped, а verifiers и multi-candidate search sometimes hurt. Даже если exact numbers
нужно перепроверить по primary paper, design lesson безопасен:

- verifier не автоматически безопаснее, если он тратит budget, добавляет wrong vetoes
  или прячет deterministic failures за prose;
- multi-candidate search не free, если UC1 acceptance идёт через один PR path;
- sub-agents не free, потому что они умножают state, permissions и traces.

Для FA subtraction значит:

1. сначала build boring loop;
2. логировать достаточно, чтобы видеть failure modes;
3. добавлять Critic/search/sub-agents только когда trace-backed failure pattern
   оправдывает extra module.

## 6. Cross-reference с ADR-1..6

| ADR | Existing decision | Эффект этой заметки |
|---|---|---|
| ADR-1 — scope | UC1 + UC3 in; UC4/UC5 deferred | Поддерживает scope discipline: no generic IHR, no code-exec MCP bridge, no multi-agent harness в v0.1 |
| ADR-2 — tiering | Static roles; native tool calls; no Critic; MCP-shaped tools | Усиливает ADR-7 inheritance; добавляет descriptor/schema progressive disclosure как likely contract detail |
| ADR-3 — memory | Mechanical Wiki; filesystem canon; no Mem0/graph/embeddings | Сильно поддержано Meta-Harness: raw filesystem traces — feature, not compromise |
| ADR-4 — storage | SQLite FTS5 disposable index | Поддерживает future tool/search catalog через BM25; no new vector need для v0.1 tool search |
| ADR-5 — chunker | ctags + markdown-it-py | Изменений нет; chunker остаётся prerequisite для context-efficient retrieval |
| ADR-6 — sandbox | Deny-by-default path allow-list; audit log | Усилен: permissions/hook layer — core harness, особенно до code execution или MCP expansion |

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

Этот sketch намеренно переиспользует ADR-2 MCP-shaped convention и ADR-6 sandbox,
а не создаёт параллельный tool protocol.

## 7. Риски и caveats

1. **Transcript numbers are secondary.** Часть benchmark details из Video 3 не была
   видна в fetched snippets. Использовать их как leads, не как ADR-ready facts.
2. **Code execution with MCP is security-heavy.** Token savings в Anthropic example
   сильные, но FA нельзя безопасно раскрывать arbitrary code execution без sandbox,
   permissions, resource limits и artifact redaction.
3. **Tool search may be premature.** Если v0.1 tool catalog маленький, descriptor /
   schema split достаточно; BM25 tool search должен ждать роста catalog.
4. **Natural-language harnesses can drift.** Если ADR-7 станет executable guidance,
   implementation tests должны держать code behavior aligned with text.
5. **Subtraction can go too far.** Убирать verifiers хорошо только если deterministic
   checks покрывают risk. Для filesystem writes sandbox и tests non-negotiable.

## 8. Пронумерованные рекомендации (R-1..R-5)

### R-1 — Сделать ADR-7 subtraction-first harness contract (cost: medium)

ADR-7 должен стать местом, где future agents перестают спорить, что такое inner loop.
Он должен задавать только v0.1 pieces для UC1/UC3: turn loop, context assembly, tool
dispatch, permission checks, trace writes, deterministic validation и stop conditions.
Сложность не в том, чтобы придумать больше roles; сложность — не дать implicit
runtime behavior расползтись между code, prompts и notes.

Слово subtraction-first важно: источники показывают, что harness structure имеет
cost. Critic loops, verifiers, multi-candidate search и sub-agents могут быть полезны,
но каждый добавляет context, failure modes и audit surface. Для FA v0.1 они должны
быть out of scope, пока trace не докажет конкретную need.

### R-2 — Добавить tiered tool disclosure до расширения tool set (cost: cheap→medium)

Минимальный FA registry может взять insight Anthropic tool search без копирования
product feature. Model сначала видит small tool descriptors. Когда tool выбран,
runtime валидирует against full schema. Если catalog вырастет, можно добавить local
`repo.search_tools` или BM25-backed catalog.

Это согласуется с ADR-4, потому что SQLite FTS5 уже выбран как search primitive, и
с ADR-2, потому что JSON Schema уже согласованный tool shape. Это cheap способ
держать initial prompt small и снизить noise при tool selection.

### R-3 — Держать code-execution-over-MCP вне v0.1, но проектировать совместимый shape (cost: cheap now / expensive if built)

Anthropic code-execution-with-MCP pattern — самый сильный efficiency lever в sources:
tool definitions становятся files, intermediate data остаётся в execution environment,
а model получает только final summaries. Именно поэтому pattern рискованный: нужны
sandboxing, resource limits, data-flow redaction и trustworthy API surface.

FA v0.1 должен сохранить shape, но не ship feature. Stable tool names, JSON schemas,
compact results, raw artifact paths и future `tools/as_files/` export достаточно,
чтобы не делать redesign later.

### R-4 — Сделать raw trace files eval substrate, а summaries — только index (cost: medium)

Meta-Harness предупреждает против over-summarizing. Proposer улучшает harnesses,
читая prior source, scores и raw traces через filesystem. Это почти та же философия,
что Mechanical Wiki: canonical data остаётся inspectable, а index/summary нужен для
удобства.

Для FA каждый loop turn должен писать JSONL events: tool request, permission result,
compact output, raw artifact path, model role, token/cost metadata if known и stop
reason. Human-friendly summaries могут жить в `hot.md` или handoff notes, но должны
cite raw trace paths.

### R-5 — Не добавлять Critic / verifier loops в v0.1 default (cost: cheap)

ADR-2 уже говорит no Critic в v0.1. Harness sources поддерживают это: verification
logic не automatically helpful, а verifier может стать ещё одним model call, который
надо интерпретировать, логировать и debug. Deterministic checks — другое дело:
schema validation, sandbox denial, syntax/lint/type/test/CI results — cheap evidence
и должны быть частью loop.

Future v0.2 Critic должен появиться из measured failure classes, а не из эстетики.
Пример trigger: repeated traces, где deterministic checks pass, но PR review находит
semantic bugs, которые second LLM consistently catches.

## 9. Открытые вопросы (Q-1..Q-5)

### Q-1 — Каким должен быть первый v0.1 tool list?

ADR-7 может задать registry shape до выбора first names. Вероятные candidates:
`repo.read`, `repo.search`, `repo.edit`, `git.status`, `test.run`, `memory.write_hot`.
Финализировать стоит вместе с первым inner-loop PR.

### Q-2 — Нужно ли сразу индексировать tool descriptors?

Если first catalog меньше ~10 tools, plain list достаточно. BM25 tool search нужен,
когда descriptors превысят reliable selection range модели или когда external MCP
catalogs войдут в scope.

### Q-3 — Какая trace retention policy приемлема?

Raw traces полезны, но могут содержать private code или tool outputs. ADR-7 должен
выбрать default local retention и redaction rules до того, как traces станут long-lived.

### Q-4 — Где заканчивается `hot.md` и начинается JSONL trace?

Практичный split: `hot.md` — session-level human/agent handoff; JSONL — replayable
machine trace. Первый summarizes; второй source-of-truth for eval.

### Q-5 — Как sandbox future code-execution mode?

ADR-6 покрывает path allow-lists, но code execution требует CPU/time/network limits,
process isolation и output redaction. Вероятно, это отдельный v0.2 ADR.

## 10. Использованные files

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

## 11. Вне scope

- Написание самого ADR-7.
- Implementation inner-loop, tool registry, sandbox или trace writer.
- Построение real MCP servers или MCP clients.
- Implementation code execution / programmatic tool calling.
- Выбор final model/provider slugs.
- Retrofit старых research notes в §0 Decision Briefing format.
