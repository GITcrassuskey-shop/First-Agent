---
title: "Радар cutting-edge исследований по агентам — май 2026"
source:
  - "https://modelcontextprotocol.io/specification/2025-03-26/server/tools"
  - "https://www.anthropic.com/index/building-effective-agents"
  - "https://docs.anthropic.com/en/docs/claude-code/hooks"
  - "https://swe-agent.com/latest/background/aci/"
  - "https://openai.github.io/openai-agents-python"
  - "https://platform.openai.com/docs/guides/agent-evals"
  - "https://docs.letta.com/guides/agents/memory/"
  - "https://www.gitworktree.org/ai-tools/parallel-agents"
  - "./semi-autonomous-agents-cross-reference-2026-05.md"
  - "./cross-reference-ampcode-sliders-to-adr-2026-04.md"
  - "../adr/ADR-2-llm-tiering.md"
  - "../adr/ADR-6-tool-sandbox-allow-list.md"
compiled: "2026-05-03"
chain_of_custody: "Факты из первичных источников цитируются или пересказываются по URL в `source`; mapping на First-Agent выведен из ADR-2, ADR-6 и перечисленных cross-reference notes."
claims_requiring_verification:
  - "Документация провайдеров и названия продуктов быстро меняются; перед implementation ADR нужно заново проверить tool, hook, eval и memory API."
  - "Рекомендации здесь — radar/backlog, а не принятые архитектурные решения."
superseded_by: ""
---

# Радар cutting-edge исследований по агентам — май 2026

> **Статус:** research radar / backlog input. Не ADR.
>
> Цель: зафиксировать текущие внешние паттерны, которые выглядят
> релевантными для First-Agent v0.1/v0.2, без старта реализации и без
> пересечения с workstream chunker'а.

## 0. Краткое резюме

First-Agent уже сделал несколько сильных ставок:

- filesystem-canonical memory вместо opaque vector-first state;
- статический role routing вместо непредсказуемой auto-escalation;
- MCP-shaped tool calls без зависимости от MCP в v0.1;
- path allow-list sandbox до любого Coder loop, который трогает FS;
- маленькие PR и явная координация агентов.

Радар ниже сверяет это направление с текущими сигналами из agent
tooling:

1. **MCP/tool registry** остаётся правильной compatibility-целью, но
   v0.1 должен зафиксировать только in-process shape: стабильные имена
   tools, JSON Schema inputs, structured results, structured errors и
   audit metadata. Реальную сложность MCP server/process лучше не
   брать до v0.2.
2. **ACI design важнее raw shell access.** Выводы в стиле SWE-agent
   ведут к windowed file views, search-first tools, синтаксическим
   проверкам вокруг edits и явным сообщениям для empty output.
3. **Hooks — самый чистый способ собрать sandbox, validation, audit и
   будущий HITL.** Форма v0.1 должна остаться маленькой:
   `pre_tool` + `post_tool`.
4. **Agent memory должна оставаться filesystem-first.**
   Letta/MemGPT-style stateful agents подтверждают важность persistent
   state, но First-Agent не должен импортировать memory server до
   работающего baseline Mechanical Wiki.
5. **Eval надо начинать с traces и маленьких datasets.** Не нужно
   ждать большого benchmark. Каждый Phase M module должен эмитить
   достаточно trace-like data, чтобы позже оценивать tool choice,
   sandbox denials и edit success.
6. **Sandbox/tool audit не optional.** MCP и современные agent SDK docs
   сходятся на input validation, access controls, timeouts, logs и
   user confirmation для sensitive operations.
7. **Multi-agent coordination — в основном workspace isolation + file
   ownership.** Forks/worktrees — детали реализации; правило такое:
   one agent, one branch/workspace, one PR target.

Рекомендуемые следующие PR:

1. ADR-7 prep note: inner-loop + tool contract.
2. Glossary update: MCP, Hook, ACI, Trace, Guardrail, Handoff.
3. Маленькая eval-fixture note: какими должны быть первые 5
   trace/eval cases.
4. Optional playbook: "launch two non-overlapping First-Agent agents".

---

## 1. Radar table

| Область | Внешний сигнал | Fit для First-Agent | Действие |
|---|---|---|---|
| MCP/tool registry | MCP tools expose `name`, `description`, `inputSchema`; calls use `tools/call`; results can set `isError`. | Совпадает с ADR-2 MCP-shaped convention. | Подать в ADR-7 contract. |
| ACI | SWE-agent подчёркивает custom file viewer, concise search, edit-time lint и explicit empty-output messages. | Сильный fit для UC1 и UC3 с mid-tier Coder. | Использовать как ограничения tool surface. |
| Hooks | Claude Code exposes lifecycle hooks, включая `PreToolUse` / `PostToolUse`, с JSON input/output и deny decisions. | Mapping на ADR-6 sandbox и future audit log. | В v0.1 использовать только `pre_tool` / `post_tool`. |
| Memory | Letta хранит state, messages, tool calls и editable memory blocks. | Подтверждает потребность в persistent state; слишком тяжело для v0.1. | Оставить Mechanical Wiki; volatile store пересмотреть в v0.2. |
| Eval | OpenAI agent evals подчёркивают сначала traces, потом datasets/eval runs. | Подходит для маленьких Phase M modules. | Добавить trace schema до большого eval suite. |
| Sandbox/audit | MCP security notes требуют validation, access control, rate limits, output sanitization, timeouts, audit logs. | Усиливает ADR-6. | ADR-7 должен включать structured errors и audit rows. |
| Multi-agent | Worktree/fork guidance говорит, что isolated workspace per agent предотвращает write/read/build interference. | Совпадает с текущим two-fork workflow. | Сохранять ownership declarations до старта работы. |

---

## 2. MCP / tool registry

### 2.1 Что говорят источники

MCP tools spec определяет tools как model-invoked capabilities с:

- уникальным `name`;
- human-readable `description`;
- `inputSchema` на JSON Schema;
- `tools/list` для discovery;
- `tools/call` для invocation;
- structured result content;
- `isError` для tool execution errors;
- JSON-RPC protocol errors для invalid tools / invalid arguments.

Спека также говорит, что tools are model-controlled, но applications
должны сохранять human-in-the-loop affordances для safety-sensitive
invocations.

MCP security guidance в той же спеке говорит, что servers должны
validate tool inputs, implement access controls, rate-limit invocations
и sanitize outputs; clients должны показывать inputs для sensitive
operations, validate tool results, implement timeouts и log usage for
audit.

### 2.2 Mapping на First-Agent

ADR-2 уже сделал правильный zero-cost ход:

```text
request:  { name: str, params: dict[str, Any] }
response: { result: Any | None, error: { code: int, message: str } | None }
```

Обновление радара: ADR-7 должен ближе выровняться с публичным
словарём MCP tools:

- `name` — stable tool string, например `repo.read`, `repo.search`;
- `description` — короткое model-facing description;
- `input_schema` — JSON Schema;
- `annotations` — optional v0.2 field, не нужен в v0.1;
- `result.content` — text-first result payload;
- `is_error` или `error` — один canonical error surface.

### 2.3 Рекомендация

Для v0.1 не брать реальную MCP dependency. Реализовать in-process
`ToolRegistry` с MCP-compatible shape:

```text
ToolSpec
  name: str
  description: str
  input_schema: dict
  handler: Callable

ToolRequest
  name: str
  params: dict

ToolResult
  result: object | None
  error: ToolError | None
  summary: str
```

ADR-7 должен явно сказать:

- transport out of scope;
- external MCP servers out of scope;
- internal shape MCP-compatible, чтобы избежать redesign позже.

### 2.4 Открытый вопрос для ADR-7

MCP различает protocol errors и tool execution errors. First-Agent
нужна одна локальная конвенция:

- unknown tool / schema validation failure = protocol-ish error;
- sandbox denial / grep no match / command failed = execution error.

Точная Python exception hierarchy может быть маленькой, но её надо
задать до реализации.

---

## 3. Agent-Computer Interface (ACI)

### 3.1 Что говорят источники

SWE-agent описывает ACI как tool/interface layer, через который agent
работает с computer environment. В docs выделены пять практических
выводов:

1. запускать linter при edit command и блокировать syntactically
   invalid edits;
2. использовать purpose-built file viewer вместо raw `cat`;
3. показывать маленькие file windows, около 100 lines per turn;
4. делать repository search concise, часто listing files with matches
   вместо dumping every matching line;
5. явно говорить, когда command succeeds with empty output.

Главный урок не "copy SWE-agent", а то, что LLM agents — новый тип
пользователя, которому нужны interfaces под его failure modes.

### 3.2 Mapping на First-Agent

Ограничения UC1/UC3 в First-Agent делают ACI важнее, чем в
Claude-only systems:

- Coder by design — mid-tier OSS;
- full-file reads тратят context window;
- Mechanical Wiki chunker может давать stable windows;
- ADR-6 считает reads network egress, когда используются remote LLMs;
- sandbox denials должны быть достаточно понятны, чтобы model мог
  recover.

### 3.3 Рекомендация

ADR-7 должен определить tools как ACI primitives, а не thin shell
wrappers:

```text
repo.search(pattern, path, limit) -> list[SearchHitSummary]
repo.read(path, start_line, end_line) -> FileWindow
repo.write_patch(path, patch) -> EditResult
repo.status() -> RepoStatus
```

Избегать в v0.1:

- unrestricted `run_command`;
- full-file `read_file` как default path;
- raw `cat` / `grep` dumps как model-facing results;
- editing commands без syntax / formatting checks.

### 3.4 Открытый вопрос для ADR-7

Должен ли `repo.read` всегда требовать window или разрешать `path`-only
для small files?

Предлагаемый v0.1 compromise:

- files ниже небольшого byte threshold можно возвращать целиком;
- larger files требуют `start_line` / `end_line` или chunk anchor;
- каждый result включает `truncated: true | false`.

---

## 4. Inner-loop hooks

### 4.1 Что говорят источники

Claude Code hook reference exposes lifecycle events, включая
`SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`, `PreCompact` и
другие. Hooks получают JSON context и могут возвращать decisions.
`PreToolUse` hook может deny dangerous shell command и вернуть reason
обратно agent'у.

Это совпадает с прежней First-Agent cross-reference note: hooks ценны,
когда отделяют cross-cutting concerns от tool bodies.

### 4.2 Mapping на First-Agent

ADR-6 sandbox концептуально уже pre-tool hook:

```text
ToolRequest -> sandbox check -> allow or structured error
```

Audit logging — это post-tool hook:

```text
ToolRequest + ToolResult + duration -> JSONL audit row
```

HITL confirmation — будущий pre-tool hook:

```text
dangerous write / push -> ask user -> allow or deny
```

### 4.3 Рекомендация

v0.1 должен реализовать только:

- `pre_tool(request, context) -> HookDecision`;
- `post_tool(request, result, context) -> None`.

Не реализовывать:

- `pre_run`;
- `post_run`;
- `on_event`;
- async hooks;
- HTTP hooks;
- plugin systems.

Минимальная hook chain должна идти в таком порядке:

1. schema validation;
2. sandbox/path policy;
3. optional one-shot bypass policy;
4. tool execution;
5. audit log;
6. result summarization.

### 4.4 Открытый вопрос для ADR-7

Schema validation должна быть hook или частью dispatcher?

Предлагаемый ответ: dispatcher core. Hooks должны получать
typed/validated requests. Так hook code остаётся простым, и каждый hook
не пере-реализует JSON Schema checks.

---

## 5. Agent memory

### 5.1 Что говорят источники

Letta memory docs описывают stateful agents, где system prompts,
memory blocks, messages, reasoning и tool calls persist in a database.
Важные core memories inject'ятся в context, а agents могут менять свои
memories через tools.

Это близко к идее MemGPT: context window как active memory, а larger
persistent tiers находятся outside context.

### 5.2 Mapping на First-Agent

У First-Agent уже есть более безопасный v0.1 baseline:

- Markdown files are source of truth;
- ADR-3 rejects vector/graph complexity for v0.1;
- ADR-4 uses SQLite FTS5 for search;
- `hot.md` / session archives задуманы как audit trail;
- future volatile-store hooks зарезервированы, но не implemented.

Обновление радара: пока не импортировать memory platform. Паттерны
релевантны, но ранняя implementation будет конфликтовать с принципом
filesystem-canon.

### 5.3 Рекомендация

Для v0.1:

- keep memory writes explicit and reviewable;
- write durable notes as Markdown;
- store tool/session traces as JSONL under `~/.fa/state/`;
- let the Mechanical Wiki index read those files later.

Для v0.2:

- рассмотреть "memory blocks" как frontmatter-addressable Markdown
  sections;
- рассматривать shared blocks только после возврата multi-user scope;
- рассмотреть volatile store только для low-stakes, evictable facts.

### 5.4 Открытый вопрос для v0.2

Можно ли agent'у редактировать свою durable memory без PR review?

Предлагаемый ответ пока: нет. Agent может предлагать memory edits, но
durable project memory всё ещё должна попадать через PR review.

---

## 6. Eval harness и traces

### 6.1 Что говорят источники

OpenAI agent-evals docs рекомендуют начинать с traces во время
debugging behavior. Trace captures model calls, tool calls, guardrails
и handoffs for a run. Trace grading отвечает на вопросы вроде:

- Did the agent pick the right tool?
- Did a handoff happen when it should?
- Did the workflow violate an instruction or safety policy?
- Did a prompt or routing change improve end-to-end behavior?

Затем, когда behavior понятнее, можно переходить к repeatable datasets
and eval runs.

OpenAI Agents SDK также treats tracing as a first-class feature рядом с
tools, handoffs, guardrails, sessions и MCP tool calling.

### 6.2 Mapping на First-Agent

First-Agent не нужен hosted eval product, чтобы взять полезную форму.
Нужна local trace schema достаточно рано, чтобы Phase M modules могли
emit data до появления eval suite.

### 6.3 Рекомендация

Определить local trace/audit row family:

```json
{
  "session_id": "2026-05-03T...",
  "step": 12,
  "role": "coder",
  "event": "tool_call",
  "tool": "repo.read",
  "args_hash": "sha256:...",
  "result_summary": "returned 80 lines",
  "is_error": false,
  "duration_ms": 42
}
```

Затем добавить tiny eval fixtures:

1. tool selection: search before read on large file;
2. sandbox: denied read returns recoverable structured error;
3. edit: patch changes exactly one intended file;
4. chunker: markdown and code chunks preserve provenance;
5. role routing: Coder failure does not auto-escalate to Debug.

### 6.4 Открытый вопрос для ADR-7

Trace logging должен жить в ADR-7 или отдельном Eval ADR?

Предлагаемый ответ: ADR-7 owns raw event schema, потому что её emit'ит
loop. Поздний Eval ADR owns graders/datasets.

---

## 7. Sandbox и tool audit

### 7.1 Что говорят источники

MCP tool security guidance говорит:

- validate all tool inputs;
- implement access controls;
- rate-limit tool invocations;
- sanitize tool outputs;
- prompt for confirmation on sensitive operations;
- validate tool results before passing them back to the LLM;
- implement timeouts;
- log tool usage for audit.

OpenAI Agents SDK docs listed guardrails, sandbox agents,
human-in-the-loop mechanisms и tracing as core runtime primitives.

Claude Code hooks демонстрируют deterministic pre-tool blocking со
structured denial reason.

### 7.2 Mapping на First-Agent

ADR-6 хорошо покрывает path access control, но ADR-7 должен связать
policy с actual loop:

- где запускается schema validation;
- как выглядит sandbox denial;
- как denials видны model;
- что логируется;
- включают ли logs raw paths или hashes;
- какие operations требуют human confirmation.

### 7.3 Рекомендация

ADR-7 должен определить:

- structured `ToolError`;
- audit JSONL path;
- path redaction/hash policy;
- max tool duration / timeout policy;
- recoverable vs fatal errors;
- one-shot bypass flow from ADR-6.

Предлагаемый `ToolError` shape:

```json
{
  "code": "sandbox.denied",
  "message": "Read denied by sandbox policy",
  "recoverable": true,
  "hint": "Use repo.search within an allowed repository"
}
```

### 7.4 Открытый вопрос для ADR-7

Должны ли audit logs хранить raw paths?

Предлагаемый v0.1 answer:

- store raw paths for allowed project files;
- redact/omit denied sensitive-looking paths;
- always store `args_hash` for correlation.

---

## 8. Multi-agent coordination

### 8.1 Что говорят источники

Git worktree guidance для parallel agents подчёркивает isolated
workspaces: несколько agents в одной директории могут overwrite files
друг друга, читать half-written changes или конфликтовать на builds и
ports. Worktrees дают каждому agent отдельную директорию и branch при
общем git object store.

Та же логика относится к separate forks: isolation важнее, чем то, как
UI показывает fork-chain.

### 8.2 Mapping на First-Agent

Текущий project workflow:

```text
GITcrassuskey-shop/First-Agent:main
├─ GrasshopperBoy/First-Agent-fork:<branch>
└─ MondayInRussian/First-Agent-fork2:<branch>
```

Важные invariants:

- each agent starts from upstream `main`;
- each agent owns a disjoint file set;
- each agent opens a direct PR to the main repo target;
- dependent PRs document merge order;
- no agent merges through another agent's fork as routine workflow.

### 8.3 Рекомендация

Оставить это project-level default:

1. Assign ownership before agent launch.
2. Give each agent a standalone prompt.
3. Require each agent to list intended files before editing.
4. Use separate branches/forks/worktrees.
5. Use direct PRs to `GITcrassuskey-shop/First-Agent:main`.
6. If stacked, write `Recommended merge order: PR A → PR B`.

### 8.4 Открытый вопрос для v0.2

Должен ли First-Agent когда-нибудь включить "dispatcher", который
launches parallel child agents?

Предлагаемый ответ: defer. Current scope explicitly defers UC5.
Полезная часть сегодня — human-readable coordination protocol.

---

## 9. Candidate backlog

### 9.1 v0.1 hard requirements

1. **ADR-7 prep note / ADR draft**
   - Tool registry.
   - Inner-loop pseudocode.
   - MCP-shaped request/result/error.
   - `native` vs `prompt-only` handling.
   - `pre_tool` / `post_tool`.
   - audit trace schema.
   - cancellation / hot.md flush.

2. **Tool trace schema**
   - Minimal JSONL rows.
   - Required event types.
   - Redaction policy.
   - Test fixture for one denied sandbox read.

3. **ACI tool surface**
   - `repo.search`.
   - `repo.read` window.
   - `repo.write_patch` or equivalent.
   - no unrestricted shell in v0.1.

### 9.2 v0.1 nice-to-have

1. **Glossary update**
   - MCP.
   - ACI.
   - Hook.
   - Trace.
   - Guardrail.
   - Handoff.

2. **Multi-agent playbook**
   - Copy-paste prompt.
   - File ownership checklist.
   - Direct upstream PR rule.

3. **Five-case eval seed**
   - small enough to run manually;
   - covers tool choice, sandbox, edit, chunk, role routing.

### 9.3 v0.2 candidates

1. Real MCP server mode for selected tools.
2. Rich hook lifecycle beyond `pre_tool` / `post_tool`.
3. Volatile memory blocks or self-managed memory.
4. Parallel child-agent dispatcher.
5. Hosted/remote trace viewer.
6. Graph/vector layer after Mechanical Wiki proves insufficient.

---

## 10. Явные non-goals

Эта note **не** рекомендует:

- adding a real MCP dependency in v0.1;
- adopting OpenAI Agents SDK, Letta, Claude Code hooks, or SWE-agent
  wholesale;
- implementing multi-agent execution in v0.1;
- replacing Markdown source-of-truth with a memory database;
- adding unrestricted shell access;
- changing ADR-1 scope;
- changing the chunker implementation plan owned by the parallel agent.

---

## 11. Follow-up prompt for ADR-7 prep

Использовать после merge radar PR:

```text
Write an ADR-7 prep note for First-Agent: inner-loop + tool contract.

Inputs:
- knowledge/research/cutting-edge-agent-research-radar-2026-05.md
- knowledge/research/semi-autonomous-agents-cross-reference-2026-05.md
- knowledge/research/cross-reference-ampcode-sliders-to-adr-2026-04.md §10 R-1
- knowledge/adr/ADR-2-llm-tiering.md amendments 2026-04-29 and 2026-05-01
- knowledge/adr/ADR-6-tool-sandbox-allow-list.md

Output:
- A focused research/pre-ADR note, not the final ADR.
- Must specify candidate decisions, open questions, and minimal v0.1 scope.
- Do not touch chunker implementation files.
```

---

## 12. Bottom line

Главный cutting-edge сигнал — не "use a bigger framework". Он такой:

- keep the loop simple;
- make tools schema-first;
- make file access windowed and searchable;
- place sandbox/validation before tool execution;
- log every tool decision;
- evaluate from traces;
- isolate parallel agents by workspace and file ownership.

Это хорошо совпадает с текущим First-Agent ADR direction.
