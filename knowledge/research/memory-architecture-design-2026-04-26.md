---
title: "FA — Memory architecture: research roadmap + 3 архитектурных варианта + open questions"
compiled: "2026-04-26"
source:
  - knowledge/research/llm-wiki-critique-first-agent.md
  - knowledge/research/llm-wiki-community-batch-1.md
  - knowledge/research/llm-wiki-community-batch-2.md
  - knowledge/research/ai-context-os-memm-deep-dive.md
  - knowledge/research/agentic-memory-supplement.md
  - knowledge/research/agent-roles.md
  - docs/architecture.md
  - "user-attachment: architect-fa-compact.md (Architect/Planner v2.1 system prompt)"
  - "https://arxiv.org/abs/2504.19413 (Mem0 paper)"
chain_of_custody: >
  Этот файл — *синтез* поверх семи существующих research-нот и двух
  внешних источников (Mem0 paper, attached architect-prompt). Все
  внешние факты (Mem0 latency, MEMM scoring, gbrain hybrid search,
  sparks ingest protocol, codedna `agent:`-log) уже верифицированы
  в parent-нотах; здесь — применение к задаче FA-агента, не
  пересказ source code.
status: research
claims_requiring_verification:
  - "User-озвученный 100K-токен порог для GraphRAG — это рабочая
     эвристика, согласующаяся с batch-2 §8 и Mem0 §4.4, но не
     измеренный бенчмарк FA. Когда корпус будет реальный, перемерим."
  - "LLM-tier распределение (60/30/10) — заявлено пользователем;
     цифры из FA-eval'ов нет."
  - "Mem0 numbers взяты с LOCOMO benchmark (paper §4.4). На
     code+research-корпусах First-Agent ожидаются другие, но
     порядок-величины (sub-second p95 search для memory-store
     vs >10s для full-context) воспроизводится."
related:
  - knowledge/adr/  # будущий ADR — выбор варианта
  - knowledge/project-overview.md  # пока заполнен TODO; v0.1 scope не зафиксирован
scope: |
  Два разделимых артефакта:
  1) Roadmap memory-исследования — timeline от текущего состояния
     до интегрированной memory-подсистемы FA v0.1 (Phase R → S → M).
  2) Три архитектурных варианта поверх FA-building-blocks. Каждый
     — самостоятельный путь, не «декомпозиция одного решения».
     Сравнение по 6 осям (complexity, capability/коэффициент попадания,
     scalability, write-side, read-side, deps).
  Плюс десять открытых вопросов, на которые нужно ответить перед
  финальным ADR. Этот файл — research-grade задание, не ADR;
  он входит в `knowledge/research/`, не в `knowledge/adr/`.
---

# FA — Memory architecture: roadmap + 3 архитектурных варианта

> **Статус:** research note, 2026-04-26.
> **Зачем эта нота:** консолидировать всё, что мы накопили о memory-
> и agentic-системах (семь research-нот, две внешние работы), в **один
> design-document** уровня research-grade — *перед* написанием ADR.
> Финальный выбор архитектуры — отдельный ADR; этот файл готовит
> почву.
> **Кому адресовано:** будущему Architect/Planner-агенту FA (см.
> `architect-fa-compact.md`), у которого short-context-окно и weaker
> coder-LLM ниже по pipeline. Поэтому форма — нумерованные блоки,
> mechanical predicates, никаких «follow the pattern in X».

---

## 1. TL;DR

1. **Read-side ≠ Write-side. Hybrid обязан адресовать обе.**
   GraphRAG-семейство решает «как извлечь и ответить» (Microsoft
   GraphRAG, LightRAG, HippoRAG, Mem0ᵍ). LLM-Wiki-семейство решает
   «как вырастить и поддерживать канон» (Karpathy, AI-Context-OS,
   obsidian-wiki, llm-wiki-kit, codedna). FA-память **не выбирает
   между** ними — она их *склеивает на одном filesystem-каноне*.

2. **Под mixed-LLM-tier (60/30/10) — design constraint №1.**
   Architect/Planner-tier работает с Mem0-style классификаторами и
   LLM-as-judge оценками. Coder/Debug-tier должен работать с
   **детерминированными Python-операциями** и не делать семантических
   решений. Граница пролегает по принципу sparks: «mechanical work →
   binary, semantic work → agent». Это диктует, что **scoring,
   chunking, parsing, hash, regen, commit** — все в Python; **typing,
   classification, reflection, summary** — в LLM.

3. **Три варианта — не «лучший / средний / худший», а три точки
   на design-space.** Variant A («Mechanical Wiki») — минимальная
   LLM-сложность, максимально debuggable. Variant B («Hybrid Brain») —
   Mem0-pipeline + filesystem canon, тяжелее, но решает use case 4
   (multi-user TG) изящно. Variant C («Layered KG») — write-time
   typed extraction, дорогая в инженерии, окупается на use case 2
   (multi-source research).

4. **Pragmatic scaling работает только с явными порогами.**
   Под ~100K токенов корпуса graph-слой имеет отрицательный ROI
   (Mem0 paper §4.3: Mem0ᵍ vs Mem0 — +2pp J ценой +80% latency).
   Между ~10K и ~100K — три-уровневый retrieval (grep → BM25 →
   embeddings) достаточен. Выше — лениво подключаем graph только
   на multi-hop запросах. Это не «выбор» в архитектуре, а
   **runtime-router**.

5. **Начинаем со scaffolding, который не зависит от выбора варианта.**
   Frontmatter v2 (с tier-меткой `stable | volatile`), supersession-
   рендерер, hybrid-search baseline (grep+BM25), четыре-операционная
   memory-API (Mem0-style: `add/update/delete/noop` с
   `InformationContent`-gate) — общие для всех трёх вариантов. ADR
   фиксирует выбор расширения (graph? Mem0-pipeline? просто
   wiki+search?), а основа — общая.

---

## 2. Anchor в существующих FA building blocks

Прежде чем проектировать, фиксируем что **уже есть** в репо. Это
не «то, что мы хотели бы», а то, что ADR-able и committed.

| Слой | Артефакт в FA сейчас | Источник |
|---|---|---|
| Архитектура агента | Three-layer model (Instruction / Execution / Integration) | `docs/architecture.md` §Трёхслойная модель |
| Memory taxonomy | Working / Persistent / Procedural / Episodic, маппинг на CogSci | `docs/architecture.md` §Архитектура памяти |
| Storage canonical | Filesystem-first, Markdown + frontmatter, no DB-canon | `knowledge/README.md` §Conventions |
| Provenance | `source:` + `compiled:` + `chain_of_custody:` + `claims_requiring_verification:` обязательны | `knowledge/README.md` §Provenance-frontmatter |
| Lifecycle | Supersession-not-overwrite (`> Status: superseded by …`) | `knowledge/README.md` §Conventions |
| Routing | По папкам (architecture.md / adr/ / research/ / prompts/) | `AGENTS.md` §Query Routing |
| Roles | Planner / Executor / Critic; Reflexion-style critic | `knowledge/research/agent-roles.md` |
| Architect prompt | Compact v2.1 — STANDARD/TRIVIAL/LARGE classification, mechanical acceptance taxonomy, no invented APIs | attachment `architect-fa-compact.md` |

**Что НЕ зафиксировано** (TODO-блокеры из `project-overview.md`):
runtime, LLM-providers, latency-budget, cost-budget, privacy. Эти
TODO влияют на выбор варианта и **должны** быть закрыты в ADR.
См. §10 (открытые вопросы 1–10).

---

## 3. Design space — три ортогональные оси

Прежде чем сравнивать варианты, разлагаем design-space на три оси
решений. Любой варианта — комбинация выборов по этим осям.

### Ось A — Где живёт «канон»

- **A1: Filesystem-canonical** (sparks, MEMM, llm-wiki-kit) — markdown
  + frontmatter в git, любая БД/индекс — disposable. Восстанавливается
  rescan'ом.
- **A2: DB-canonical** (Mem0, gbrain prod) — Postgres+pgvector / Neo4j
  истина, файлы — экспорт.
- **A3: Hybrid** (gbrain dev mode с PGLite) — БД для фактов, файлы
  для нарратива. Контракт: DB ⊥ FS, никакой записи в одно через
  другое.

→ Для FA, **выбор A1** уже сделан в `knowledge/README.md`. Это
не пересматриваем. Все три варианта ниже — на A1.

### Ось B — Когда происходит «extraction»

- **B1: Read-time extraction** (RAG-classic, full-context) — на
  каждый запрос re-extract из raw. Дорого по токенам, прост код.
- **B2: Write-time deterministic** (gbrain regex, sparks parse) —
  Python-парсер при каждом write. LLM не зовём. Дёшево по токенам,
  жёсткие схемы.
- **B3: Write-time semantic** (Mem0 extraction-phase, MEMM ingest)
  — LLM extract из новых сообщений. Дорого по токенам, гибко по
  схеме.
- **B4: Hybrid B2+B3** — деревянный код достаёт что может (URL,
  даты, имена в @-нотации), LLM достаёт остальное.

### Ось C — Как происходит retrieval

- **C1: Filesystem-grep + BM25** (llm-wiki-kit Tier-1, MEMM seed-pass)
  — без эмбеддингов, под weaker-coder-LLM работает.
- **C2: Hybrid (BM25 + vector)** (cavemem, gbrain dev) — BM25 →
  RRF-fusion → vectors. Embedding-store обязателен.
- **C3: Hybrid + graph traversal** (Mem0ᵍ, gbrain prod, MEMM
  two-pass с PPR) — graph-walk поверх seeds. Дорогой write-side
  (typed edges).
- **C4: Multi-hop reasoning over passage-graph** (HippoRAG, MS
  GraphRAG) — Personalized PageRank, community detection.

### Что закрепляем по умолчанию

- **A = A1** (filesystem-canonical) — **закрыто** уже в
  `knowledge/README.md`.
- **B = B4** (hybrid: deterministic + semantic) — детерминированный
  парсер для очевидных primitives (URL, дата, file-path, @-mention,
  SHA), LLM для остального. Это sparks hint-not-classify pattern.
- **C** — **различается между вариантами** (см. §4–§6).

→ Три варианта ниже отличаются именно по оси C (retrieval) и
по тому, **как они масштабируются** при росте корпуса.

---

## 4. Variant A — «Mechanical Wiki»

> Минимум LLM, максимум Python. Цель: всё, что можно делать кодом,
> делается кодом; LLM пишет содержимое, не структуру.

### 4.1. Краткая суть

Память FA — это `knowledge/` + `notes/` (плюс per-use-case
поддиректории), где:

- **Запись.** Python-CLI `fa ingest --prepare` (sparks-стиль):
  читает inbox-источник (файл / URL / TG-сообщение / PR-комментарий),
  применяет deterministic regex/AST-pass, возвращает **JSON-hints**
  (page-type candidate, entity candidates, related-files candidate,
  hash). Агент берёт hints, генерит markdown-страницу с правильным
  frontmatter, кладёт в правильную папку. `fa ingest --finalize`
  ребилдит индекс (BM25, link-graph), коммитит.
- **Чтение.** Three-layer retrieval (llm-wiki-kit pattern):
  1. `grep` по path/title/tags;
  2. BM25 по body;
  3. **(Опционально, deferrable)** vector-search через локальный
     SQLite-vector (sqlite-vss) — только если grep+BM25 < threshold
     совпадений.
- **Графа нет.** Cross-document reasoning делается *в LLM-prompt'е*
  (передаём top-K и просим связать). Это RAG, не GraphRAG.

### 4.2. Что копируем по нашим notes

| Откуда | Что | Зачем |
|---|---|---|
| sparks (`agentic-memory-supplement.md` §5) | Mechanical/semantic split, hint-not-classify, ingest --prepare/--finalize | Архитектурный костяк |
| sparks | Three-layer vault: `raw/` (immutable) → `wiki/` (derived) → `index/` (disposable) | Lifecycle |
| llm-wiki-kit (`batch-2.md` §3.2) | Three-layer retrieval (grep → BM25 → embeddings) | Read-side baseline |
| MEMM (`ai-context-os-memm-deep-dive.md` §4.2) | L0/L1/L2 progressive markers внутри страницы (`<!-- L1 -->`/`<!-- L2 -->`) | Token budget |
| obsidian-wiki (`batch-2.md` §3.3) | `hot.md` ~500-словная сессионная сводка | Working memory |
| graphify (`batch-2.md` §3.6) | EXTRACTED / INFERRED / AMBIGUOUS таги на любом артефакте | Provenance в frontmatter |

### 4.3. Архитектура в коде (псевдо)

```text
src/
├── memory/
│   ├── frontmatter.py      ← parse/render YAML + L0/L1/L2 markers
│   ├── ingest/
│   │   ├── prepare.py      ← deterministic hints (URL/email/SHA/etc)
│   │   ├── finalize.py     ← rebuild index, commit
│   │   └── extractors/     ← per-source: github, arxiv, telegram, web, pr
│   ├── search/
│   │   ├── grep_layer.py   ← exact match (path/title/tag)
│   │   ├── bm25_layer.py   ← Whoosh or rank-bm25
│   │   └── vector_layer.py ← sqlite-vss, optional, lazy
│   ├── hot.py              ← session ~500-word summary
│   └── lifecycle.py        ← supersession enforcement
└── tools/
    └── fa                  ← CLI (Click/Typer)
```

### 4.4. Сильные стороны

- **Самый дешёвый по токенам.** LLM не зовётся при write — только
  при ingest-классификации последнего шага (выбрать page-type),
  и при чтении (синтез ответа из top-K).
- **Самый совместимый с weaker-coder-LLM.** Coder-tier (Qwen 27B /
  Nemotron 3) пишет markdown по template'у — это его сильная
  сторона. Coder не делает retrieval-decisions.
- **Архитектура работает даже без LLM.** Если LLM падает / медленный
  / в офлайне — `fa search "X"` возвращает grep-результат за
  миллисекунды.
- **Easy debugging.** Каждый артефакт — markdown, всё в git, diff
  читаем человеком.

### 4.5. Слабые стороны

- **Multi-hop reasoning слабый.** Use case 2 (multi-source research):
  «Какие репозитории в моих заметках используют tree-sitter?» —
  это уже cross-document join. Без графа — либо grep по «tree-sitter»
  (хрупко, пропустит referencing pages), либо LLM-fan-out (дорого).
- **Use case 4 (multi-user TG) не идеален.** «Покажи последние 10
  упоминаний пользователя X» — это entity-search, который
  Variant A решает grep'ом по `@X` (работает) и BM25 по «X» (даёт
  ложные срабатывания — слова-тёзки). Без typed-edges грубее.
- **Cache hit rate — низкий.** Каждый запрос → fresh search.
  Семантическое кэширование (Mem0-style ADD-vs-NOOP) отсутствует.
- **Cross-page consistency не enforced.** Если LLM описал X
  разными терминами на двух страницах, никто не подсветит.

### 4.6. Trade-off summary

| Ось | Оценка |
|---|---|
| **Complexity** | Низкая — ~600 LoC Python для v0.1 |
| **Capability на use case 1 (coding+PR)** | Хорошо — code-graph не нужен, BM25 по кодовой базе работает |
| **Capability на use case 2 (multi-source research)** | Среднe — multi-hop через LLM-fan-out |
| **Capability на use case 3 (local-docs-to-wiki)** | Отлично — это ровно его форм-фактор |
| **Capability на use case 4 (multi-user TG)** | Среднe — entity-tracking грубоват без typed-edges |
| **Cache hit rate** | Низкий — каждый запрос свежий |
| **Scalability** | До ~50K страниц / ~100M tokens на single SQLite |
| **Mixed-LLM-friendly** | Очень — coder работает с Python-API |

---

## 5. Variant B — «Hybrid Brain»

> Mem0-pipeline (semantic memory ops) поверх filesystem-canon
> (LLM-Wiki). Цель: эксплицитная **two-tier память** — стабильный
> канон в `knowledge/`, волатильная память в Mem0-store.

### 5.1. Краткая суть

Память FA расщепляется на **два слоя**:

- **Stable corpus** (то, что сейчас в `knowledge/`): архитектура,
  ADR, research, prompts. Канон в filesystem. Запись только через
  PR. Реcurrence — supersession-rule. Используется как «семантическая
  память» (стабильные факты).
- **Volatile memory store** (Mem0-style): per-session insights,
  user profiles, episodic logs, current-task hot context. Канон —
  *операционный лог*: `add/update/delete/noop` events в JSONL.
  Текущее состояние — материализация лога. **InformationContent
  gate** перед UPDATE: не overwrite'им богатую запись бедной.

Между слоями — **promotion-pipeline**: episodic insight, который
повторился в N сессий, кандидат на promotion в `knowledge/research/`
или новый ADR. Это codedna v0.8 паттерн (`message:` → promote to
`rules:`).

### 5.2. Read-side

- **Stable corpus** ищется как Variant A: grep + BM25 + (lazy)
  vector. *Никакого* graph'а здесь — стабильный корпус малый
  (~100 страниц).
- **Volatile store** ищется по vector-similarity (Mem0 §2.1: «top-s
  semantically similar memories»). Эмбеддинги обязательны для
  volatile, опциональны для stable.
- **Two-source context** (Mem0 §2.1): на каждый агент-запрос —
  собираем `(stable-relevant, volatile-relevant, hot-summary)`.
  Архитектурно это working-memory из `docs/architecture.md`,
  но с явным расщеплением.

### 5.3. Write-side

- **Stable corpus**: write through PR. Это уже работает как факт.
- **Volatile store**: Mem0-pipeline.
  ```text
  on each new (user_msg, agent_msg) pair:
    extract_phase(P=(summary, recent_window, msg_pair)) → candidates
    for c in candidates:
      sim_top = vector_search(c, store, k=10)
      op = LLM.classify(c, sim_top) ∈ {ADD, UPDATE, DELETE, NOOP}
      if op == UPDATE and InformationContent(c) <= IC(sim_top[0]):
        skip
      else:
        execute(op, store)
  ```
- **Promotion** (background, weekly cron):
  - Volatile entries with `promoted_count >= 3` → candidate PR
    для `knowledge/research/`.
  - Volatile entries `age > 90d AND used = false` → `archive/`.

### 5.4. Что копируем

| Откуда | Что | Зачем |
|---|---|---|
| Mem0 paper (`agentic-memory-supplement.md` §2) | 4-op tool-call API (ADD/UPDATE/DELETE/NOOP) | Volatile write-side |
| Mem0 paper §2.1 | Two-source context (summary + recent window) | Working-memory shape |
| Mem0 paper Algorithm 1 | InformationContent gate перед UPDATE | Anti-degradation |
| Mem0ᵍ §2.2 | Mark-invalid, не физическое удаление | Temporal reasoning |
| codedna v0.8 (`agentic-memory-supplement.md` §3) | `message:` → promote to `rules:` lifecycle | Volatile→stable promotion |
| MEMM (`ai-context-os-memm-deep-dive.md` §4.4–4.5) | Intent-aware scoring weights, two-pass execute_context_query | Volatile retrieval |
| obsidian-wiki (`batch-2.md` §3.3) | `hot.md` ~500-словная session-summary | Working layer |
| sparks (§5) | Hint-not-classify ingest для stable corpus | Inbox→knowledge |

### 5.5. Архитектура в коде (псевдо)

```text
src/
├── memory/
│   ├── stable/                     ← (как в Variant A)
│   │   ├── frontmatter.py
│   │   ├── search/{grep,bm25,vector}.py
│   │   └── lifecycle.py
│   ├── volatile/
│   │   ├── store.py                ← JSONL log + materialized state
│   │   ├── extract.py              ← LLM extraction phase
│   │   ├── update.py               ← LLM tool-call: ADD/UPDATE/DELETE/NOOP
│   │   ├── ic_gate.py              ← InformationContent estimate
│   │   ├── embeddings.py           ← sentence-transformers, cached
│   │   └── search.py               ← top-k similarity
│   ├── working/
│   │   ├── hot.py                  ← per-session ~500w summary
│   │   ├── recent_window.py        ← last m=10 messages
│   │   └── context_builder.py      ← assembles 3 sources
│   └── promotion/
│       ├── candidates.py           ← volatile→stable promotion rules
│       └── archive.py              ← decay/cleanup
└── tools/
    ├── fa                          ← CLI
    └── fa-mcp                      ← MCP-server (optional)
```

### 5.6. Сильные стороны

- **Use case 4 (multi-user TG) — sweet spot.** Mem0 *именно* про
  per-user memory с long-running multi-session conversations. User
  X в TG — это `user_id=X` в volatile store; их профиль накапливается
  без ручного управления.
- **Cache hit rate высокий.** Volatile store предотвращает
  re-extraction (NOOP-ветка), retrieval идёт по small store
  (~10K записей в год — из paper'а), не по всему корпусу.
- **Latency предсказуемая.** Mem0 §4.4: p95 search 0.200s. На FA —
  ожидаем хуже (наш embedding-сервер другой), но порядок-величины
  тот же.
- **Use case 1 (persistent coding+PR)** — episodic-логи прошлых
  сессий по этому проекту → автоматически в context. «Что я делал
  в этом репо месяц назад» — Mem0 ровно это.

### 5.7. Слабые стороны

- **Сложность выше.** ~1500 LoC Python + sentence-transformers
  dependency + JSONL-log discipline. Larger surface area для
  багов.
- **Зависит от Architect-tier-LLM.** UPDATE/DELETE-классификация
  — нетривиальное LLM-решение. Coder-tier здесь fail'нет (см.
  Mem0 paper §3.3 — они используют GPT-4o-mini, и это уже выше
  «coder-tier» FA).
- **Two-store consistency.** Если promotion-pipeline ломается,
  один и тот же факт может быть в обоих слоях с разным значением.
  Нужен явный consistency-check (как codedna SPEC.md).
- **Use case 3 (local-docs-to-wiki) — overkill.** Stable wiki
  достаточен; Mem0-pipeline для статичного docs-корпуса не нужен.

### 5.8. Trade-off summary

| Ось | Оценка |
|---|---|
| **Complexity** | Средняя — ~1500 LoC + embeddings stack |
| **Capability на use case 1** | Отлично — episodic memory across sessions |
| **Capability на use case 2** | Хорошо — но без graph для multi-hop |
| **Capability на use case 3** | Среднe — overkill для статичного |
| **Capability на use case 4** | **Отлично — это его натуральный домен** |
| **Cache hit rate** | Высокий — Mem0-NOOP + vector cache |
| **Scalability** | До ~1M volatile entries (Mem0 paper LOCOMO ≈10K на conversation, наш домен крупнее) |
| **Mixed-LLM-friendly** | Среднe — UPDATE/DELETE требуют Architect-tier |

---

## 6. Variant C — «Layered KG»

> Write-time deterministic typed extraction (gbrain pattern) поверх
> filesystem-canon. Цель: каждое сохранение страницы автоматически
> создаёт типизированные рёбра в graph-индексе; graph включается на
> retrieve лениво.

### 6.1. Краткая суть

Любой write в `knowledge/` или `notes/` проходит через
deterministic regex/AST-pass, который **извлекает entity-references
и создаёт типизированные edges**:

```text
PR mention "@alice"           → edge:  page →[mentions]→ Person:alice
URL "github.com/X/Y"          → edge:  page →[references]→ Repo:X/Y
File path "src/foo.py:42"     → edge:  page →[touches]→ File:src/foo.py
Wikilink [[concept-bar]]      → edge:  page →[links]→ Page:concept-bar
Frontmatter source: <url>     → edge:  page →[derived_from]→ Source:<url>
Frontmatter supersedes: <ref> → edge:  page →[supersedes]→ Page:<ref>
```

Никакого LLM при write. Edges хранятся в SQLite (`edges.db`) —
disposable, регенерируется. На retrieve:

- **Default** — Variant A flow (grep + BM25).
- **Multi-hop trigger**: если запрос содержит маркеры
  («связано», «зависит», «упоминает», «who works on», `--graph`-flag),
  включается graph-walk поверх top-K seeds (MEMM two-pass pattern).

### 6.2. Read-side: lazy graph

```text
seed_pass(query) → top-K pages without graph
if multi_hop_signal(query):
    expand seeds → 1-hop neighbors (filtered by edge-type)
    rescore with graph-proximity signal
    return top-K rescored
else:
    return seed_pass result
```

Graph-proximity — один из 6 сигналов скоринга MEMM (см.
`ai-context-os-memm-deep-dive.md` §4.5). На v0.1 — простой PPR
(Personalized PageRank) в одну итерацию, не Leiden / Louvain.

### 6.3. Write-side

- Markdown-страница пишется агентом как обычно.
- При commit-hook (или `fa ingest --finalize`):
  ```python
  edges = extract_edges_deterministic(page)
  edges_db.upsert_for_page(page.path, edges)
  ```
- При delete страницы — edges marked invalid (Mem0ᵍ pattern —
  не физически удалять, для temporal reasoning).
- При rename — edges follow target.

### 6.4. Что копируем

| Откуда | Что | Зачем |
|---|---|---|
| gbrain (`agentic-memory-supplement.md` §4 + `batch-2.md` §3.1) | Write-time deterministic regex extraction → typed edges | Write-side ядро |
| MEMM (`ai-context-os-memm-deep-dive.md` §4.4) | 6-signal hybrid scoring + graph_proximity | Read rescore |
| MEMM §4.4 + Mem0ᵍ §2.2 | Two-pass execute (seeds → graph-walk-with-seeds) | Read pipeline |
| Mem0ᵍ §2.2 | Mark-invalid вместо delete | Temporal reasoning |
| codedna (`agentic-memory-supplement.md` §3) | Reverse-deps `used_by:` (это уже edge) | Edge-typology validation |
| obsidian-wiki (`batch-2.md` §3.3) | `hot.md` session-summary | Working layer |
| sparks | Architecture guard test (business logic не утечёт в adapter) | Discipline |

### 6.5. Архитектура в коде (псевдо)

```text
src/
├── memory/
│   ├── stable/                     ← (как Variant A)
│   ├── graph/
│   │   ├── extractors/
│   │   │   ├── mentions.py         ← @user, [[link]], #tag
│   │   │   ├── urls.py             ← github/arxiv/youtube domain-routing
│   │   │   ├── files.py            ← path/symbol references
│   │   │   ├── frontmatter_links.py ← supersedes/related/source
│   │   │   └── code_symbols.py     ← optional, tree-sitter
│   │   ├── edges_db.py             ← SQLite, edges + entity nodes
│   │   ├── ppr.py                  ← Personalized PageRank
│   │   └── walk.py                 ← multi-hop expansion
│   ├── search/
│   │   ├── seed_pass.py            ← grep+BM25 (как Variant A)
│   │   ├── multi_hop_detect.py     ← intent classifier
│   │   └── rescore.py              ← seeds + graph-proximity
│   └── working/
│       └── hot.py
└── tools/
    └── fa
```

### 6.6. Сильные стороны

- **Use case 2 (multi-source research) — sweet spot.** Cross-source
  reasoning («Какие arxiv papers в моих заметках связаны с
  GraphRAG-репозиториями?») — это natural-graph-query.
- **Use case 4 (multi-user TG) хорошо.** People — first-class
  entity-type. «Кто упоминал X в последнюю неделю» — graph-query
  по `Person→[mentioned_in]→Page` с date-фильтром.
- **Write-side не зависит от LLM-tier.** Extraction — regex/AST,
  работает идентично на любой модели. Coder-tier пишет страницы,
  edges получаются «автоматически».
- **Audit trail наглядный.** Edge → source-line. Можно показать
  «эту связь я вытащил из строки X в файле Y».

### 6.7. Слабые стороны

- **Write-time overhead.** Каждый commit запускает extractors;
  на корпусе ~1000 страниц это ~50–500ms на commit. Не критично, но
  ощутимо.
- **Schema lock-in.** Hardcoded edge-types — добавление нового
  типа требует кода. gbrain имеет 5 типов; FA в начале — ~7.
- **Cold-start пустой.** Граф полезен, когда есть >100 страниц
  с density. На v0.1 — почти не помогает.
- **Use case 3 (local-docs-to-wiki) — overengineering.** Статичные
  docs не нуждаются в multi-hop graph queries.
- **Use case 1 (coding+PR) — graph по коду требует tree-sitter.**
  Это +1 dependency и нетривиальный chunk-extractor (gbrain имеет
  29 grammars).

### 6.8. Trade-off summary

| Ось | Оценка |
|---|---|
| **Complexity** | Высокая — ~1800 LoC + SQLite schema migrations |
| **Capability на use case 1** | Хорошо (с tree-sitter), Среднe (без) |
| **Capability на use case 2** | **Отлично — natural domain** |
| **Capability на use case 3** | Средне — оверкилл для статичного |
| **Capability на use case 4** | Хорошо — entity-graph даёт явные ответы |
| **Cache hit rate** | Средний — graph-walk per query, BM25 cached |
| **Scalability** | До ~100K страниц на single SQLite (with PPR optimization) |
| **Mixed-LLM-friendly** | Хорошо — write-side LLM-independent; read-side зависит только в multi-hop intent classifier |

---

## 7. Сводное сравнение

| Ось | A: Mechanical Wiki | B: Hybrid Brain | C: Layered KG |
|---|---|---|---|
| Сложность (LoC) | ~600 | ~1500 | ~1800 |
| Внешние зависимости | sqlite (опц), rank-bm25 | + sentence-transformers, sqlite-vss | + (опц) tree-sitter, sqlite-vss |
| Write-side LLM | Только page-type classification | LLM на каждый user-message-pair | Никакого |
| Read-side LLM | Synthesis only | Embedding + (Architect для query-rewrite) | Multi-hop intent + synthesis |
| Latency р95 (estimate) | <100ms search, +LLM synth | ~200ms search (Mem0-paper), +synth | ~150ms (no graph) / ~300ms (graph) |
| Cache hit rate | Низкий | Высокий (Mem0 NOOP) | Средний |
| Token-efficient | Очень | Очень (vs full-context) | Очень |
| Use case 1 (coding+PR) | ✓ хорошо | ✓ отлично (episodic) | ✓ хорошо (с tree-sitter) |
| Use case 2 (multi-source research) | △ через LLM-fan-out | ○ хорошо | ✓ отлично |
| Use case 3 (local-docs-to-wiki) | ✓ отлично | △ overkill | △ overkill |
| Use case 4 (multi-user TG) | △ entity-tracking грубоват | ✓ отлично (per-user) | ✓ хорошо (entity-graph) |
| Mixed-LLM-friendly | ✓ очень | △ Architect-tier обязателен | ✓ да |
| Scalability | ~100M tokens | ~1M volatile entries | ~100K страниц |
| Risk for v0.1 | Самый низкий | Средний (Mem0-pipeline отладка) | Высокий (graph cold-start) |

Легенда: ✓ хорошо, ○ хорошо с оговорками, △ слабо, ✗ не подходит.

---

## 8. Use-case mapping (что *именно* решает каждую из 4 задач)

### 8.1. Use case 1 — Persistent Coding & PR Management
*10K LoC codebase + 50KB notes + GitHub PRs across sessions.*

- **Variant A**: BM25 по `notes/` + grep по коду. PR-context — через
  `gh pr view` в context-builder. **Работает.** Слабое место —
  cross-session episodic («что я думал об этой функции 2 недели
  назад» — нужно вручную search'ить).
- **Variant B**: Volatile store автоматически собирает
  «code-decisions» episodic-памятью. На retrieve — top-K похожих
  волатильных записей + текущая страница notes. **Лучше всего**
  для long-running проектов.
- **Variant C**: tree-sitter по коду → typed-edges
  `Function→[calls]→Function`. Multi-hop: «какие функции вызывают
  X». **Лучше всего** для cross-file reasoning, но нужен
  tree-sitter и стабильная chunker-версия (gbrain CHUNKER_VERSION
  pattern, см. `agentic-memory-supplement.md` §4.5).

### 8.2. Use case 2 — Continuous Multi-Source Research
*GitHub repos + arxiv papers + web articles + YouTube summaries
с retain-context across sessions.*

- **Variant A**: BM25 + grep — найдёт нужное по словам, но не
  свяжет «Mem0 paper упоминает LangMem» с «LangMem benchmark в
  моих заметках». Связь делает LLM в момент ответа. **Работает,
  но дорого по токенам.**
- **Variant B**: Volatile store держит episodic «прошлые research-
  insights» — это хорошо для «я уже это смотрел». Но cross-source
  joins — всё равно через LLM-fan-out.
- **Variant C**: source-URL → entity-node в графе. «Какие arxiv
  papers связаны с моим Mem0-research'ем» — `Source:arxiv.org/...`
  →[derived_from-]→ Page → [related]→ Source:arxiv.org/.... **Лучше
  всего** для этого use case.

### 8.3. Use case 3 — Local Documentation to Wiki
*Большие docs → interactive wiki → troubleshooting.*

- **Variant A**: **Лучше всего.** Это его форм-фактор. sparks-стиль
  ingest-pipeline → split на topical pages с frontmatter →
  three-layer retrieval. Никакой графовой инфраструктуры не нужно.
- **Variant B**: оверкилл для статического docs-корпуса. Mem0
  pipeline ничего не добавляет — нет «conversations», нет episodic.
- **Variant C**: Edges → wikilinks. Полезно для navigation, но
  можно и без них (markdown wikilinks parsed lazily).

### 8.4. Use case 4 — Multi-User Telegram (10 человек)
*Профили пользователей + cross-conversation tracking + контекст-
изоляция.*

- **Variant A**: User profiles — по одной markdown-странице на
  человека, BM25 по mention'ам. Работает «грубо»; ложные совпадения
  на тёзках. **Маргинально.**
- **Variant B**: **Лучше всего** — Mem0-store native поддерживает
  per-user memory namespacing. `user_id=X` → собственный slice
  volatile-памяти. Cross-talk («что A говорил B о C») —
  query-time cross-namespace.
- **Variant C**: Person — first-class entity. «X говорил с Y в
  чате по теме Z» — это three-hop graph query. Хорошо, но дороже
  чем B на per-user lookup (нужен PPR на entity-graph каждый раз).

### 8.5. Сводная пригодность

| Use case | Лучший вариант | Приемлемый | Оверкилл / слабый |
|---|---|---|---|
| 1 — coding+PR | B | A, C | — |
| 2 — multi-source research | C | B (с LLM-помощью) | A |
| 3 — local-docs-to-wiki | A | C | B |
| 4 — multi-user TG | B | C | A |

**Если нужен один вариант для всех четырёх** — это **B (Hybrid
Brain)** *с extension-hooks для C* (graph-слой подключаемый по
флагу). См. §9.5.

---

## 9. Research roadmap — timeline

> Workflow: **R → S → M** (Research → Scaffolding → Module).
> См. `docs/workflow.md`. Этот roadmap — конкретное наполнение
> для memory-подсистемы.

### 9.1. Phase R1 — закрыть открытые вопросы (now → 1 неделя)

**Goal:** ответить на 10 вопросов §10. Никакого кода. Только
research notes / ADR-наброски.

| # | Шаг | Артефакт | Acceptance |
|---|---|---|---|
| R1.1 | Заполнить `project-overview.md` (TODO) | `knowledge/project-overview.md` | Все TODO заменены на конкретику |
| R1.2 | Решить use-case priority | ADR-001 «v0.1 scope» | ADR-001 принят |
| R1.3 | Выбрать LLM-runtime/providers | ADR-002 «LLM tiering» | ADR-002 принят |
| R1.4 | Выбрать вариант (A/B/C/hybrid) | ADR-003 «memory architecture» | ADR-003 принят, ссылается на этот файл |
| R1.5 | Latency / cost budget | в ADR-001 или отдельным ADR-004 | budget-числа зафиксированы |

### 9.2. Phase R2 — недостающий research (1–2 недели)

Если ADR-003 = вариант B или C, нужны дополнительные research'ы
**до scaffolding'а**:

| # | Тема | Когда нужна |
|---|---|---|
| R2.1 | Embedding model choice (sentence-transformers vs OpenAI ada vs local) | если выбрали B или C-with-vectors |
| R2.2 | tree-sitter chunker versioning (gbrain CHUNKER_VERSION pattern) | если выбрали C-with-code-graph |
| R2.3 | sqlite-vss vs faiss vs lance | если выбрали B |
| R2.4 | InformationContent estimator (LLM или token-count heuristic) | если выбрали B |
| R2.5 | Mem0-prompt'ы для extraction/update — спот-чек на нашем домене | если выбрали B |

### 9.3. Phase S — scaffolding (1 неделя)

`src/memory/` создаётся как **скелет, общий для всех вариантов**.
Файлы появляются с TODO-телом и контрактом, проходят `mypy
--strict`, но не реализуют логику.

| # | Шаг | Файл | Acceptance |
|---|---|---|---|
| S.1 | Скелет `src/memory/__init__.py` + module map | — | `python -c "import src.memory"` exits 0 |
| S.2 | Skeleton `src/memory/frontmatter.py` (parse/render) с TODO | — | mypy --strict passes; pytest -k frontmatter не валится |
| S.3 | Skeleton `src/memory/search/` слои (по варианту) | — | as above |
| S.4 | CLI `tools/fa` (Click/Typer) с командами `fa search`, `fa ingest` (no-op) | — | `fa --help` exits 0 |
| S.5 | pre-commit hooks (ruff format + check, mypy) | `.pre-commit-config.yaml` | `pre-commit run --all-files` exits 0 |
| S.6 | CI workflow (lint, typecheck, test) | `.github/workflows/ci.yml` | actions runs and passes |

### 9.4. Phase M — модули (по варианту, 4–8 недель)

Каждый модуль — отдельный PR с зелёным CI. Порядок — зависит от
варианта, но всегда **write-side первым** (потому что без записи
читать нечего).

#### M-track для Variant A (Mechanical Wiki)

```text
M.A.1  frontmatter.py            (parse/render YAML + L0/L1/L2)
M.A.2  ingest/prepare.py         (deterministic hints)
M.A.3  ingest/finalize.py        (rebuild index, commit)
M.A.4  search/grep_layer.py      (find . -path/title/tag)
M.A.5  search/bm25_layer.py      (rank-bm25 over body)
M.A.6  hot.py                    (session ~500w summary)
M.A.7  search/vector_layer.py    (sqlite-vss, lazy)
M.A.8  CLI fa search/ingest      (wired to layers)
M.A.9  Telegram-adapter          (use case 4)
M.A.10 GitHub-adapter            (use case 1, PR ingest)
M.A.11 Web/arxiv-adapter         (use case 2)
M.A.12 Local-docs-adapter        (use case 3)
```

#### M-track для Variant B (Hybrid Brain)

```text
M.B.1   stable/* (= M.A.1–M.A.6)             (как в Variant A)
M.B.2   volatile/embeddings.py               (model choice fixed)
M.B.3   volatile/store.py                    (JSONL log + materialized state)
M.B.4   volatile/extract.py                  (Mem0 extraction prompt)
M.B.5   volatile/ic_gate.py                  (InformationContent estimator)
M.B.6   volatile/update.py                   (4-op tool-call)
M.B.7   volatile/search.py                   (top-k similarity)
M.B.8   working/context_builder.py           (3-source context)
M.B.9   promotion/candidates.py              (volatile→stable)
M.B.10  promotion/archive.py                 (decay)
M.B.11  CLI fa search/ingest/promote         (wired)
M.B.12  Adapters (telegram, github, web, docs)
```

#### M-track для Variant C (Layered KG)

```text
M.C.1   stable/* (= M.A.1–M.A.6)
M.C.2   graph/extractors/{mentions, urls, files, frontmatter}.py
M.C.3   graph/edges_db.py                    (SQLite schema, migrations)
M.C.4   graph/ppr.py                         (PPR одна итерация)
M.C.5   graph/walk.py                        (1-hop expansion)
M.C.6   search/multi_hop_detect.py           (intent classifier)
M.C.7   search/rescore.py                    (seed + graph-proximity)
M.C.8   working/hot.py
M.C.9   CLI fa search/ingest --graph         (wired)
M.C.10  Adapters
```

### 9.5. Hybrid path — B-with-C-hooks (рекомендуемый default)

Если на R1.4 нет очевидного ответа, **B-with-C-hooks** —
default-выбор:

- M.B.1–M.B.12 как описано выше.
- Дополнительно в M.B.1: `frontmatter.py` понимает поле `links:`
  (явные wikilinks) и `mentions:` (entity-references).
- В M.B.2: `volatile/store.py` дополнительно пишет
  `entity_index.jsonl` — простой inverted index `entity → list of
  volatile_ids`.
- Когда корпус превысит ~100 stable + 1000 volatile: добавить
  Phase M.C (графовый слой) поверх.

Это путь sparks-style + Mem0-style + лениво-добавляемый gbrain-
graph.

### 9.6. Eval & regression (continuous, начиная с Phase S)

| # | Что | Когда добавляется |
|---|---|---|
| E.1 | Smoke-test набор queries (10 на use case) | Phase S |
| E.2 | LLM-as-judge на retrieve quality | Phase M (середина) |
| E.3 | Latency benchmark (p50/p95) | Phase M (конец) |
| E.4 | Diff-based test selection (gstack pattern, см. `agentic-memory-supplement.md` §6) | Phase M+ (когда eval-набор станет дорогим) |

---

## 10. Open questions — обязательны к ответу до ADR-003

Каждый вопрос — *потенциальный* блокер выбора варианта. Где явно
указано — отмечу, какой вариант он завязывает.

### 10.1. Use-case priority for v0.1

User перечислил 4 use case, но в `project-overview.md` v0.1 scope
= TODO. **Можно ли ранжировать**: какой use case в v0.1 must-have,
какой — nice-to-have?

→ Влияет на выбор: если 1+3 — Variant A; если 1+4 — Variant B; если
2+4 — Variant C.

### 10.2. Single-machine vs multi-tenant

User упоминал «multi-user Telegram». Это **один FA-агент,
обслуживающий 10 пользователей**, или **10 экземпляров FA-агента,
каждый — своему пользователю**?

→ Если первое — нужно per-user namespacing в volatile-store
(Variant B native; Variant A потребует отдельной директории на
user; Variant C — entity-partitioning в графе).

### 10.3. Privacy — local LLM only, или hybrid w/ remote API?

«60% top-OS, 30% low-OS, 10% elite» — **elite** это локально-
запускаемая модель (Llama 3 405B) или удалённый Claude Opus?
Если remote — данные TG-чата уходят к провайдеру?

→ Если data privacy-critical: embedding-model должен быть локальный
(sentence-transformers ст small-en); это влияет на Variant B/C.

### 10.4. Latency budget per turn

Сколько секунд от user-msg до agent-reply допустимо?
- <500ms → Mem0-style retrieval приемлем; full-context — нет.
- <2s → любой Variant.
- 5–10s допустимо → можно даже full-context на коротких сессиях.

### 10.5. Storage backend для v0.1

Files-only (sparks)? Files + SQLite (sparks с manifest)? Files +
sqlite-vss? Files + Postgres+pgvector?

→ Прямо влияет на инженерное усилие. Если v0.1 = files-only —
Variant A очевиден; vector-store откладывается.

### 10.6. Telegram ingest scope

Агент пишет в память **всё** из 10-человечного чата, или **только**
сообщения, адресованные ему (`@FA-bot ...`)?

→ Privacy + storage. Первое — намного больший корпус и более
агрессивная decay-policy. Второе — лимитированный, чище.

### 10.7. PR-write permissions

Агент **создаёт/комментит** PR, или **только читает**?

→ Если только читает — adapter простой (gh CLI). Если пишет —
нужны permission checks, undo-стратегия, ADR по «что агенту
разрешено в Git».

### 10.8. YouTube/web ingest pipeline

YouTube-summarization — agent делает Whisper-транскрипцию (как
graphify, локально), или потребляет уже готовые text-summaries?

→ Если первое — это +1 серьёзная dependency (faster-whisper, GPU
preference). Если второе — обычный web-fetcher.

### 10.9. Code-graph granularity

Use case 1 — 10K LoC codebase. Хотим **per-symbol** retrieval
(tree-sitter, как gbrain) или **per-file** (BM25 over file content)?

→ Per-symbol = +tree-sitter dependency, нетривиальный chunker, но
acing the use case. Per-file = ctags / просто grep, проще.

### 10.10. Eval bar для v0.1

Есть ли labeled queries-with-expected-answers, или ставим LLM-as-
judge baseline и регулируем итеративно?

→ Если labeled — можем запускать precision/recall/MRR (как gbrain
P@k, R@k, MRR, nDCG@k). Если нет — gstack 3-tier eval (gate /
periodic / diff-based) с LLM-as-judge.

---

## 11. Что делаем прямо сейчас (без новых ADR)

Низкорисковые шаги, которые валидны для **любого** варианта и
которые можно делать параллельно с обсуждением ADR:

1. **Заполнить `project-overview.md`** — закрыть TODO. Это
   разблокирует ADR-001.
2. **Зарегистрировать ADR-template-instances**:
   ADR-001 «v0.1 use-case scope», ADR-002 «LLM tiering», ADR-003
   «memory architecture variant», ADR-004 «storage backend».
   Создать stub-файлы со status:proposed.
3. **Frontmatter v2 spec** — добавить опциональные поля
   `tier:` (`stable` | `volatile`), `links:`, `mentions:`,
   `confidence:` (`extracted | inferred | ambiguous`). Не ломая
   существующих файлов — только additive. Это совместимо со всеми
   тремя вариантами.
4. **`AI-Session: <id>` в commit-trailers** — codedna pattern
   (см. `agentic-memory-supplement.md` §3.4). Это уже было
   в quick-wins.
5. **`knowledge/llms.txt`** — index-файл для one-fetch ingestion
   (gbrain pattern). Дёшево, агент-friendly.
6. **`knowledge/prompts/RESOLVER.md`** — explicit dispatcher
   intent → prompt template (gbrain pattern). У нас сейчас один
   файл `research-topic.md`; когда T1–T5 будут готовы, RESOLVER
   уже будет.

---

## 12. Sources

**Internal (research-нотес FA):**
- `knowledge/research/llm-wiki-critique.md` — TL;DR критики
  Karpathy-Wiki + factcheck.
- `knowledge/research/llm-wiki-critique-first-agent.md` — что
  применимо к FA, T1–T7 берём, L1–L6 заглядываем, N1–N6 не берём.
- `knowledge/research/llm-wiki-critique-sources.md` — фактчек
  источников.
- `knowledge/research/llm-wiki-community-batch-1.md` — 6 community
  проектов (cavemem, codedna, obsidian-llm-wiki, llm-atomic-wiki,
  AI-Context-OS, agentic-local-brain).
- `knowledge/research/llm-wiki-community-batch-2.md` — gbrain,
  llm-wiki-kit, obsidian-wiki, sparks, mnemovault, graphify +
  Microsoft GraphRAG, LightRAG, HippoRAG, nano-graphrag.
- `knowledge/research/ai-context-os-memm-deep-dive.md` — 10-секционный
  deep-dive backend MEMM (модули, code snippets, что копировать).
- `knowledge/research/agentic-memory-supplement.md` — Mem0 paper +
  gstack + дельты (codedna v0.8/v0.9, gbrain operations contract,
  sparks contract-in-binary).
- `knowledge/research/agent-roles.md` — graphify + CAMEL + Reflexion;
  Planner/Executor/Critic минимальный набор v0.1.
- `docs/architecture.md` — three-layer agent model, memory taxonomy.
- `attachment: architect-fa-compact.md` — Architect/Planner v2.1
  compact system prompt.

**External:**
- [Mem0 paper, arXiv:2504.19413](https://arxiv.org/abs/2504.19413)
  — production memory architecture (extraction → update, 4-op
  tool-call, Mem0ᵍ graph variant, LOCOMO benchmark).
- [llmstxt.org](https://llmstxt.org/) — `llms.txt` спецификация.
- LOCOMO benchmark (Maharana et al., 2024) — long-conversation
  memory evaluation.
