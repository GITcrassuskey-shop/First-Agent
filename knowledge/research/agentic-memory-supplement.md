---
title: "Agentic Memory — supplement: Mem0 paper + дельты к batch-1/batch-2 + gstack"
compiled: "2026-04-26"
source:
  - https://arxiv.org/abs/2504.19413
  - https://arxiv.org/html/2504.19413v1
  - https://github.com/garrytan/gstack
  - https://github.com/garrytan/gbrain
  - https://github.com/yogirk/sparks
  - https://github.com/Larens94/codedna
  - "user-dossier: agentic-dossiers v2.md (Arena.ai Agent Mode, four repos: gstack, codedna, gbrain, sparks)"
chain_of_custody:
  - "Mem0 paper — arXiv:2504.19413v1 (Chhikara et al., 28 Apr 2025).
    Прочитан полный HTML; цитируемые цифры взяты из §4.4 Latency
    Analysis и §4.3 Performance Comparison."
  - "v2 dossier (Arena.ai Agent Mode) — secondary source. Цитируемые
    архитектурные паттерны сверены с README/SPEC.md upstream-репо
    выборочно (codedna SPEC, sparks-contracts.md, gbrain INSTALL_FOR_AGENTS),
    но не построчно с кодом — это secondary-проход."
  - "Дельты вычислялись против двух наших нот: batch-1 §3.6 (codedna)
    и batch-2 §3.1 (gbrain), §3.4 (sparks). gstack у нас не покрывался."
status: research
supersedes: none
extends:
  - knowledge/research/llm-wiki-community-batch-1.md  # §3.6 codedna
  - knowledge/research/llm-wiki-community-batch-2.md  # §3.1 gbrain, §3.4 sparks
  - knowledge/research/ai-context-os-memm-deep-dive.md  # forthcoming via PR #12 (в полёте при создании этой ноты)
related:
  - knowledge/research/llm-wiki-critique.md
  - knowledge/research/llm-wiki-critique-first-agent.md
  - knowledge/research/agent-roles.md
claims_requiring_verification:
  - "Mem0 'p95 search 0.200s, p95 total 1.44s vs full-context 17.117s'
    (paper §4.4) — измерено на LOCOMO (10 conversations × ~26 000 tokens),
    железо/embedding-модель в paper'е указаны (GPT-4o-mini, dense
    embeddings, без upreply названия модели). На других корпусах цифры
    могут отличаться."
  - "Mem0 '26% relative improvement в LLM-as-Judge vs OpenAI memory'
    — относительное число; baseline-конфигурация OpenAI ChatGPT memory
    в paper описана через manual extraction в playground (§4.4 last
    paragraph), что не вполне fair-baseline."
  - "v2 dossier цифры о звёздах/процессах в репо — на дату его генерации
    (Arena.ai run); не сверял заново."
  - "gstack нашими инструментами не клонировался в этой сессии — анализ
    идёт по v2 dossier как primary, спот-чек по upstream README."
scope: |
  Дополнение к двум основным research-нотам:
  (a) дельта по codedna — что batch-1 не покрыл из v2 dossier;
  (b) дельта по gbrain и sparks — что batch-2 не покрыл из v2 dossier;
  (c) gstack — новый репо, не было в наших разборах;
  (d) Mem0 paper (arXiv:2504.19413) — production-grade memory
  architecture, прямо релевантна задаче FA, у нас отсутствовала.

  Цель — закрыть пробелы первого прохода и связать community-паттерны
  с research-grade архитектурой Mem0.
---

# Agentic Memory — supplement

> **Статус:** research note, 2026-04-26.
> **Что внутри:** дельты к существующим нотам и одна крупная новая
> ссылка (Mem0 paper). Батч-1 и батч-2 остаются каноном для первичного
> разбора шести+пяти проектов; этот файл их *не* заменяет — он
> добавляет то, что в первом проходе ушло в фон.

## 1. TL;DR — пять вещей, которые мы пропустили в первом проходе

1. **Mem0-architecture (arXiv:2504.19413).** Production-grade
   memory pipeline с двумя phases (extraction → update) и tool-call
   API из четырёх операций (`ADD / UPDATE / DELETE / NOOP`). Это та
   инженерная схема, которая у нас в `agent-roles.md` пока
   описана как «работа с памятью», но без формы. См. §2.
2. **codedna v0.8/v0.9 evolution.** В батче-1 мы зафиксировали
   `rules:` и `used_by:` как «in-source аннотация», но пропустили
   три ключевых эволюционных шага: rolling `agent:`-лог, мягкий
   `message:`-канал с lifecycle promote/dismiss, `wiki:`-pointer
   и git-trailers как authoritative audit log. См. §3.
3. **gbrain — operations contract.** Батч-2 сказал «trust boundary
   через `OperationContext.remote`»; но не разглядел *откуда*
   приходит это API, — single-source `src/core/operations.ts`,
   из которого genrated и CLI, и MCP-server. Это другой архитектурный
   паттерн, чем «MCP поверх ядра». См. §4.
4. **sparks — contract-in-binary + multi-harness init.** Батч-2
   взял mechanical/semantic split; пропустил, что *сам контракт
   агента* embedded в бинарник, и `sparks init --agent X` пишет
   `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` из одного источника. Это
   ровно тот паттерн, который снимает «пишу AGENTS.md руками для
   каждого нового агента». См. §5.
5. **gstack — skills-as-filesystem с template-generation.** Этого
   репо вообще не было в наших разборах. Ключевое: `SKILL.md`
   генерируется из `.tmpl` + per-host config (claude/codex/cursor/…),
   и три-tier тестовая система (gate/periodic + diff-based selection)
   для skill-eval. См. §6.

## 2. Mem0 (arXiv:2504.19413) — production memory architecture

> Источник: [paper PDF](https://arxiv.org/pdf/2504.19413v1) ·
> [HTML](https://arxiv.org/html/2504.19413v1) · производственный
> код: <https://mem0.ai/research>.
> Авторы: Chhikara, Khant, Aryan, Singh, Yadav (Mem0 team), 28 Apr 2025.

### 2.1 Что предлагается

Две архитектуры:
- **Mem0** — flat memory с extraction/update phases. Memory store —
  vector embeddings, обновления — через LLM tool-call с четырьмя
  операциями.
- **Mem0ᵍ** — то же самое + directed labeled graph поверх
  (`(v_s, r, v_d)`-триплеты, Neo4j). Adds ~2pp точности на
  LLM-as-Judge ценой ~80% увеличения p95 latency.

### 2.2 Pipeline двумя фазами (§2.1 paper)

**Extraction phase** (на каждый новый message-pair `(m_{t-1}, m_t)`):

```text
P = (S, {m_{t-m}, ..., m_{t-2}}, m_{t-1}, m_t)
Ω = φ(P)   # LLM extraction: returns set of salient facts
```

Где `S` — асинхронно обновляемый conversation summary (background
job), `m_{t-m..t-2}` — recent-window (m=10 в paper'е). `φ` — LLM
function (GPT-4o-mini в их сетапе). Возвращает «candidate facts».

> **Точка для FA.** Расщепление контекста на (1) глобальный summary,
> (2) recent window, (3) текущий message-pair — это та самая
> three-source схема, которая нас потом будет нужна для long-running
> сессий. Сейчас в `agent-roles.md` упомянут «working memory», но
> формы нет.

**Update phase** (для каждого ω_i ∈ Ω):

```text
1. retrieve top-s semantically similar memories (s=10 in paper)
2. tool_call(LLM, candidate=ω_i, similar=memories) → operation
3. operation ∈ {ADD, UPDATE, DELETE, NOOP}
4. execute on store
```

**Algorithm 1 (Appendix B):**

```text
for each fact f ∈ F:
    op ← ClassifyOperation(f, M)
    if op == ADD:
        M ← M ∪ {(new_id, f, "ADD")}
    else if op == UPDATE:
        m_i ← FindRelatedMemory(f, M)
        if InformationContent(f) > InformationContent(m_i):
            M ← (M \ {m_i}) ∪ {(id_i, f, "UPDATE")}
    else if op == DELETE:
        M ← M \ {m_i}
    else:  # NOOP
        pass
```

> **Точки для FA, которые нам нужны:**
> 1. **Четыре операции как закрытое множество.** Не «save_memory» как
>    единый primitive (как у MEMM), а **четырёхвариантный** tool-call.
>    Это правильная форма для агента: модель *явно* классифицирует,
>    что делает с памятью, и это попадает в логи.
> 2. **InformationContent gate перед UPDATE** — чтобы агент не
>    overwrite'ил содержательную память бедной. Это та проверка,
>    которой у MEMM нет: их `save_memory` всегда перезаписывает.
> 3. **Mark-invalid вместо физического удаления** в Mem0ᵍ
>    (paper §2.2): «mark them as invalid rather than physically
>    removing them to enable temporal reasoning». Это прямой ответ
>    на наш `protected: bool` из MEMM-разбора — там был бинарный
>    флаг, здесь — explicit lifecycle.

### 2.3 Numbers (§4.4) — что важно для FA-планирования

| Подход | p50 search | p95 search | p95 total | p95 tokens |
|---|---|---|---|---|
| Mem0 | **0.148s** | **0.200s** | **1.44s** | low |
| Mem0ᵍ | ~0.5s | ~0.8s | ~2.6s | low |
| Zep | ~0.7s | — | ~1.3s | mid |
| LangMem | 17.99s | 59.82s | — | mid |
| A-Mem | 0.668s | — | 1.41s | mid |
| Full-context (26K tokens) | n/a | n/a | **17.117s** | very high |

LLM-as-Judge `J` overall:
- Mem0: ~67%
- Mem0ᵍ: ~68%
- Best RAG (k=2, chunk=1024): ~61%
- Full-context: ~73% (но 17s p95 latency — нерабочая схема для
  интерактивного агента).

> **Берём как baseline:** «memory-based на длинной истории
> разговора может быть в **>10× раз быстрее** full-context при
> потере ~6pp в LLM-as-Judge». Это аргумент в пользу того, что нам
> нужна именно extraction-into-store схема, а не «full chat history
> в каждый запрос».

### 2.4 Что *не* брать из Mem0 на v0.1

- **Neo4j** в Mem0ᵍ — overkill, и наш batch-2 §4 уже показал, что
  graph-слой берётся *после* того, как корпус устаканился.
- **Vector embeddings как обязательная часть** — в paper они dense
  (size не указан), и для FA на v0.1 это ещё одна зависимость.
  MEMM-стиль (tag+l0-overlap как «poor man's semantic») остаётся
  правильным первым шагом.
- **GPT-4o-mini как extraction-model** — это про latency/$cost
  баланс, не про архитектуру; на нашей стороне будет litellm-
  абстракция и любая модель.

## 3. codedna delta (что batch-1 §3.6 не покрыл)

В батче-1 мы взяли только `used_by:` и `rules:`. В v2 dossier есть
ещё четыре эволюционных слоя протокола, которые не были в первом
проходе:

### 3.1 `agent:` rolling log (5 entries)

Format: `model-id | provider | YYYY-MM-DD | session_id | what you did`.
Хранится в шапке файла, oldest entry дропается на 6-м. Полная
история — в git.

> **Точка для FA.** У нас в `knowledge/research/`-frontmatter есть
> `compiled:` и `chain_of_custody:`, но нет **rolling-log активности
> агентов на конкретный артефакт**. Это другой класс данных: не «когда
> заметка создана», а «кто и в какой сессии её последний раз трогал
> и зачем». Полезно для long-running проектов с >5 агент-сессий.

### 3.2 `message:` (v0.8) — мягкий канал наблюдений

Двухслойная система:
- `rules:` — *архитектурная истина* (pinned, hard constraint).
- `message:` — *гипотеза/наблюдение*, lifecycle: append → promote
  to `rules:` или dismiss. Append-only.

> **Точка для FA.** У нас сейчас всё валится в один тип заметок
> (`research/`). Идея «soft observations с lifecycle» хорошо
> ложится на наши `claims_requiring_verification:` — но как
> *отдельный канал*, не как поле frontmatter'а. Стоит обсудить
> в ADR.

### 3.3 `wiki:` field (v0.9) — opt-in deep context

Из docstring файла можно сослаться на отдельный `docs/wiki/<slug>.md`
с расширенным контекстом. Создаётся, *только когда* предыдущий агент
посчитал нужным. Не «все файлы автоматически имеют расширенный wiki».

> **Точка для FA.** Это ровно та идея «прогрессивная глубина по
> требованию», что у MEMM реализована через `<!-- L1 -->`/`<!-- L2 -->`,
> но в codedna она *file-to-file*, не *внутри-файла*. Для нас
> в `knowledge/research/` ссылка на отдельный deep-dive (как мы
> уже делаем для AI-Context-OS — [PR #12](https://github.com/GITcrassuskey-shop/First-Agent/pull/12),
> `ai-context-os-memm-deep-dive.md`) — это *тот же паттерн*,
> и он валидируется codedna v0.9 как осознанный приём.

### 3.4 Git trailers как authoritative audit log

Каждый AI-commit включает: `AI-Agent: <name>`, `AI-Provider:`,
`AI-Session:`, `AI-Visited:`, `AI-Message:`. `.codedna` и
docstrings — это *кэш быстрого доступа*; git history — *источник
истины*.

> **Точка для FA.** В наших коммитах сейчас Devin-session ID
> добавляется в PR-описание автоматически, но *не в git-trailer
> коммита*. Это значит, что после squash-merge'а связь с сессией
> теряется. Это исправляется: добавить `AI-Session: <id>` в
> commit-trailers.

### 3.5 Что НЕ берём из codedna v0.8/v0.9

- **`.codedna` manifest как YAML на уровне проекта** — для FA
  это лишний слой, у нас уже есть AGENTS.md и frontmatter.
- **Cascade-tagged dependencies (`[cascade]`)** — паттерн полезен
  для кода, не для knowledge-base.

## 4. gbrain delta (что batch-2 §3.1 не покрыл)

Батч-2 взял write-time extraction, thin harness + fat skills, trust
boundary. Не покрыл четыре существенные вещи:

### 4.1 Operations contract как single source of truth

`src/core/operations.ts` — ~41 операция, **из которой generated и
CLI, и MCP-server**. Не «MCP поверх ядра», а *контракт первичен,
оба surface — производные от него*.

```text
src/core/operations.ts          ← THE CONTRACT
├── src/cli.ts          (remote=false, trusted)
└── src/mcp/server.ts   (remote=true,  restricted surface)
```

> **Точка для FA.** Это другой архитектурный паттерн, чем у MEMM:
> у MEMM есть `core/`, и `commands/` (Tauri) поверх него, но там
> каждая команда пишется руками. У gbrain — операции декларируются
> *один раз*, surface'ы — производные. Если у нас будет CLI + MCP,
> это правильная форма.

### 4.2 RESOLVER.md — Markdown-dispatcher навыков

`skills/RESOLVER.md` — это *таблица*: trigger phrase → skill file
path. Агент читает её первой, потом читает скилл, потом действует.
*Никакого* code-routing.

> **Точка для FA.** В нашем `knowledge/prompts/` сейчас лежат T1–T5
> шаблоны, но *диспетчера* нет — мы полагаемся на Devin-runtime,
> чтобы решить, какой шаблон применить. Это работает для одного
> агента, но если мы хотим, чтобы skill-инструкции были портируемы
> между агентами (как декларирует AGENTS.md), нужен явный
> RESOLVER.md как часть `knowledge/`. Хорошо ляжет в ADR.

### 4.3 Always-on parallel skills (signal-detector)

Два «всегда работающих» скилла, fire on every inbound message:
- `signal-detector` — passive entity/idea capture.
- `brain-ops` — brain-first lookup перед external API.

«The brain compounds.»

> **Точка для FA.** Это другой стиль работы памяти: не «агент
> запросил context, получил context», а «агент пассивно пишет
> в память на каждом сообщении». Для FA это пригодится, когда
> появится long-running сессия — но *не сейчас*, до этого Devin
> сам решает, что записать.

### 4.4 `llms.txt` / `llms-full.txt` documentation protocol

`llms.txt` = URL-индекс всей документации. `llms-full.txt` = тот
же индекс с inlined-контентом для one-fetch ingestion. Любой агент
может скачать **один** URL и получить всю документацию.

> **Точка для FA.** У нас сейчас агент при чтении репо скачивает
> AGENTS.md, потом docs/, потом knowledge/ — это N запросов.
> Один `llms-full.txt` решит это в один запрос. Полезно для
> portable-режимов (когда FA вызывается *не* через Devin).
> [llmstxt.org](https://llmstxt.org/) — спецификация.

### 4.5 Что НЕ берём из gbrain

- **PGLite/Postgres+pgvector как пара engines** — батч-2 уже
  отметил, что для v0.1 файлы достаточно.
- **Tree-sitter chunker с 36 WASM grammars** — overkill для
  knowledge-вики. Полезно, когда дойдём до code-indexing.

## 5. sparks delta (что batch-2 §3.4 не покрыл)

Батч-2 взял mechanical/semantic split, three-layer model
(`raw/wiki/sparks.db`), page types, maturity, ingest --prepare/--finalize.
Не покрыл четыре вещи:

### 5.1 Contract-in-binary + multi-harness init

```text
sparks describe        # prints embedded sparks-contracts.md
sparks init --agent claude    # writes CLAUDE.md (same content)
sparks init --agent codex     # writes AGENTS.md (same content)
sparks init --agent gemini    # writes GEMINI.md (same content)
sparks init --agent generic   # writes generic AGENTS.md
```

Контракт — embedded resource в Go-бинарнике. Один источник, четыре
файла, ноль дублирования.

> **Точка для FA.** Это решение для проблемы, которую мы скоро
> встретим: «как заставить новый агент (Cursor / Codex / Claude
> Code) работать в нашем репо без того, чтобы я руками писал
> CLAUDE.md и .cursorrules». Сейчас у нас только AGENTS.md.
> Когда появится `src/`, можно сделать `tools/init_agent.py
> --target claude|cursor|codex` по тому же паттерну.

### 5.2 Hint-not-classify pattern

`sparks ingest --prepare` применяет *детерминированный pattern-
match* (URL → bookmark candidate, `- [ ]` → task candidate,
`> ` → quote candidate) и возвращает **hints**, не **decisions**.
Семантическая классификация — у агента.

> **Точка для FA.** Это ровно то разделение, которого нам сейчас
> не хватает в `inbox/`-стиле workflow: что должен делать
> детерминированный код, что — LLM. Hints возвращаются как JSON,
> агент берёт их как *подсказки*, не как обязательные решения.

### 5.3 Architecture guard test

Тест в репо, который **проваливает билд**, если business-logic
просочилась из `internal/core` в любой adapter (CLI/MCP/viewer).

> **Точка для FA.** Когда дойдёт до `src/`, такой тест защитит
> нашу three-layer-архитектуру от drift'а. Это *архитектурный
> CI-gate*, а не code-style; стоит сразу заложить.

### 5.4 SQLite WAL mode + concurrent-ingest lock

CLI и MCP-server могут работать **одновременно** на одном vault,
потому что (a) WAL mode позволяет concurrent reads, (b) явный
lock на ingest-операциях.

> **Точка для FA.** Если у нас когда-нибудь будет MCP-server
> поверх knowledge/, эта пара (WAL + ingest-lock) — обязательна.
> Не велосипедить.

### 5.5 Что НЕ берём из sparks

- **`sparks brief --json`** — weekly-snapshot формат интересен,
  но это специфика sparks (raw → archive lifecycle), не наша.
- **Hardcoded 8 collection extractors** (Quotes/Bookmarks/Books/…)
  — это конкретный домен sparks, не general-purpose.

## 6. gstack — новый разбор (не было в batch-1/2)

> Источник: [garrytan/gstack](https://github.com/garrytan/gstack).
> Описание: «AI software factory», skills-as-filesystem.

### 6.1 Skill-as-directory с template generation

Каждый скилл — отдельная директория с **`SKILL.md`**, который
**сгенерирован** из `SKILL.md.tmpl` + per-host config:

```text
gstack/
├── review/SKILL.md         ← generated
├── qa/SKILL.md             ← generated
├── ship/SKILL.md           ← generated
├── …
├── SKILL.md.tmpl           ← source of truth
├── scripts/
│   ├── gen-skill-docs.ts   ← template engine
│   └── host-config.ts      ← HostConfig validator
└── hosts/
    ├── claude.ts
    ├── codex.ts
    ├── cursor.ts
    └── index.ts            ← registry, derives Host type
```

Запускается `bun run gen-skill-docs --host codex` — генерирует
`SKILL.md` под целевого агента (claude/codex/cursor/kiro/hermes/gbrain).

> **Точка для FA.** В батче-2 §3.3 obsidian-wiki у нас был
> «symlink-зеркала per-agent» как самый дешёвый способ multi-host.
> gstack делает это **через генерацию из шаблона**, а не симлинки —
> это позволяет per-host *разное* содержимое, а не идентичные копии.
> Если у нас в `knowledge/prompts/` появятся agent-specific
> варианты, это правильный паттерн.

### 6.2 Three-tier test system + diff-based selection

```text
test/
├── helpers/
│   ├── touchfiles.ts        ← test → file-deps map
│   ├── session-runner.ts    ← E2E via `claude -p` with stream-JSON
│   └── llm-judge.ts         ← LLM-as-judge harness
├── skill-validation.test.ts ← Tier 1: static, free, <1s, gate
├── skill-llm-eval.test.ts   ← Tier 3: LLM-judge (~$0.15/run, periodic)
└── skill-e2e-*.test.ts      ← Tier 2: E2E via claude -p (~$3.85/run)
```

- **gate** = deterministic, blocks merge.
- **periodic** = quality, runs weekly.
- **diff-based** = test runs only if its declared file-deps changed.
  `EVALS_ALL=1` overrides.

> **Точка для FA.** Это правильная форма CI для skill-based проектов:
> большинство тестов — про prompt content (parsing/validation,
> deterministic), но реальная проверка качества — это LLM-eval,
> который дорогой. Diff-based selection ограничивает дорогие
> evals только тем, что реально менялось.

### 6.3 Daemon + state file pattern (browse/)

Long-lived headless Chromium (Playwright) поверх localhost
HTTP-сервера. Состояние — в `.gstack/browse.json` (PID + port +
token). Atomic-write: tmp + rename. Auto-shutdown через 30 минут
idle. Health-check перед использованием.

> **Точка для FA.** Если у нас будет долгоживущий вспомогательный
> процесс (e.g. embedding-server), эта пара «atomic state file +
> health-check + auto-shutdown» — стандартная и правильная.

### 6.4 Что НЕ берём из gstack

- **23 готовых skill-роли** (CEO reviewer, QA, security, release…)
  — мы их *не* копируем; у нас своя role-decomposition в
  `knowledge/research/agent-roles.md`. Но *формат* (SKILL.md как
  стандалон-файл) — берём.
- **Dual-listener tunnel security** — это про remote-pairing
  use case, к нам не относится.
- **Bun runtime + TypeScript** — наш план Python.

## 7. Кросс-репо: новые паттерны, которые мы не зафиксировали

| Паттерн | Источник | Куда в FA |
|---|---|---|
| Operations contract → CLI + MCP | gbrain | ADR, когда появится `src/memory/` |
| RESOLVER.md как skill dispatcher | gbrain | `knowledge/prompts/RESOLVER.md` (можно сейчас) |
| Contract-in-binary + multi-harness init | sparks | `tools/init_agent.py` (после v0.1) |
| Architecture guard test | sparks | CI-gate, когда появится `src/` |
| Hint-not-classify ingest | sparks | стандарт для будущего `tools/ingest.py` |
| Template-generated skills (per-host) | gstack | если в `knowledge/prompts/` появятся agent-specific варианты |
| Three-tier test system (gate/periodic + diff-based) | gstack | CI-стратегия, когда появятся LLM-evals |
| Mem0 four-op tool-call (ADD/UPDATE/DELETE/NOOP) | Mem0 paper | API будущей `src/memory/` |
| Mem0 two-source context (summary + recent window) | Mem0 paper | working-memory layer в `agent-roles.md` §3 |
| codedna `agent:` rolling log | codedna v0.8+ | расширение frontmatter (после ADR) |
| codedna `message:` soft-channel | codedna v0.8+ | формализация наших `claims_requiring_verification:` |
| codedna git-trailers | codedna v0.8+ | `AI-Session: <id>` в commit trailers (можно сейчас) |
| `llms.txt` / `llms-full.txt` documentation map | gbrain | можно сейчас, дёшево |
| Mark-invalid вместо delete (temporal reasoning) | Mem0 paper Mem0ᵍ | расширение `protected:` semantics, ADR |
| InformationContent gate перед UPDATE | Mem0 paper Algorithm 1 | будущая `src/memory/` |

## 8. Что меняется в наших открытых вопросах

В deep-dive по AI-Context-OS (см. §9 там) у нас были три открытых
вопроса. Mem0 paper и v2 dossier дают по ним новые входы:

1. **Ontology — четыре MEMM-типа vs наши.**
   Mem0 entity-types (Person, Location, Event, Object, Concept,
   Attribute) — *шесть* типов, и они ближе к natural-language
   universe, чем MEMM-овские (source/entity/concept/synthesis).
   Наш план: посмотреть на codedna `rules:`/`message:`/`wiki:` как
   на третий вариант (не типы памятей, а **типы каналов**).
   Решение — в ADR (см. §9 ниже).

2. **Skill-активация через scoring vs explicit triggers.**
   gbrain RESOLVER.md — это *explicit triggers*, без scoring.
   gstack — explicit invocation (`/skill-name`). MEMM —
   scoring-based (skill «прорывается» через top-5). Mem0 — нет
   skills как сущности.
   Похоже, что **community-консенсус — explicit, не scoring**.
   Scoring — оптимизация, нужная только когда skill'ов > ~30.

3. **Graph now or later.**
   Mem0 paper §4.3: Mem0ᵍ vs Mem0 — **+2pp на LLM-as-Judge ценой
   ~80% latency**. Это слабое улучшение за большую цену. Подтверждает
   нашу batch-2 §8: graph-слой имеет смысл *после* того, как
   filesystem-канон работает; не в v0.1.

## 9. Действия (доступные сразу, без новых ADR)

Низкорисковое, можно делать без длинных решений:

1. **Добавить `AI-Session: <devin-session-id>` в git-trailers** на
   PR-уровне или в `.gitmessage`. Источник истины — git history,
   PR-описание — кэш.
2. **Создать `knowledge/llms.txt`** — URL-индекс наших `docs/` и
   `knowledge/`. Дёшево, *читается* любым агентом за один запрос.
   Опциональный второй файл `llms-full.txt` — inlined-версия (можно
   позже).
3. **Создать `knowledge/prompts/RESOLVER.md`** — таблица
   `intent → prompt template` для T1–T5 шаблонов. Сейчас
   неявная, агент догадывается; явная резолвинг-таблица сделает
   её portable между агентами.

Среднериск, требует ADR:

4. **Расширить frontmatter `chain_of_custody:` до тройной структуры**
   — `rules:` (hard), `message:` (soft observations), `wiki:`
   (deep-dive pointer). Перед этим нужен ADR — это меняет
   read-shape для агента.
5. **Заложить будущий `src/memory/` API на Mem0-четырёхопераций**
   (`add / update / delete / noop`) с InformationContent-gate
   перед UPDATE. Это ADR-уровень: задаёт контракт.

## 10. Sources

**Primary:**
- [arXiv:2504.19413 (Mem0 paper)](https://arxiv.org/abs/2504.19413) ·
  [HTML version](https://arxiv.org/html/2504.19413v1) — §2 Proposed Methods,
  §4.4 Latency Analysis, Appendix B Algorithm.
- [garrytan/gstack](https://github.com/garrytan/gstack) — `AGENTS.md`,
  `ARCHITECTURE.md`, `scripts/gen-skill-docs.ts`, `hosts/index.ts`,
  `test/helpers/touchfiles.ts`.
- [garrytan/gbrain](https://github.com/garrytan/gbrain) —
  `src/core/operations.ts`, `skills/RESOLVER.md`,
  `INSTALL_FOR_AGENTS.md`, `llms.txt` / `llms-full.txt`.
- [yogirk/sparks](https://github.com/yogirk/sparks) —
  `sparks-contracts.md`, `sparks-spec.md`, `internal/core/`,
  `internal/contract/`, `internal/inbox/`.
- [Larens94/codedna](https://github.com/Larens94/codedna) —
  `SPEC.md`, `.codedna` manifest, `integrations/`,
  `tools/traces_to_training.py`.

**Secondary:**
- `~/attachments/.../agentic-dossiers v2.md` — Arena.ai Agent Mode
  generated dossier (gstack/codedna/gbrain/sparks).
- `knowledge/research/llm-wiki-community-batch-1.md` §3.6 (codedna).
- `knowledge/research/llm-wiki-community-batch-2.md` §3.1 (gbrain),
  §3.4 (sparks).
- `knowledge/research/ai-context-os-memm-deep-dive.md` — для
  сравнения с Mem0 architecture. **В полёте в
  [PR #12](https://github.com/GITcrassuskey-shop/First-Agent/pull/12);**
  будет доступен по этому пути после мержа.

**Related research-grade context:**
- [llmstxt.org](https://llmstxt.org/) — `llms.txt` спецификация.
- LOCOMO benchmark (Maharana et al., 2024, см. paper §3.1).
