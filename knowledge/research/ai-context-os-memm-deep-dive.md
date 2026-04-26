---
title: "AI-Context-OS (MEMM) — глубокий разбор бэкенда: что брать в First-Agent"
compiled: "2026-04-26"
source:
  - https://github.com/alexdcd/AI-Context-OS
  - "branch: codex/inbox-review-ui-phase2 (HEAD: 0fa0688)"
  - https://memm.dev/docs/architecture-and-operating-model/
  - https://memm.dev/docs/paper/
  - https://memm.dev/docs/whitepaper/
  - "user-dossier: AI-Context-OS+MEMM.txt"
  - "user-dossier: 0.+A+workflow+for+github+repo+analysisprompt.md"
chain_of_custody:
  - "Репозиторий клонирован 2026-04-26, ветка codex/inbox-review-ui-phase2
    отстаёт от main на 23 коммита (в основном UI-полировка InboxView).
    Бэкенд этой ветки полностью совпадает с main по содержимому ядра."
  - "Все цитируемые сниппеты — прямые выдержки из репо (line numbers
    указаны рядом). Цифры/паттерны проверены против
    src-tauri/src/core/*.rs, не по саммари."
  - "Цитаты из memm.dev/docs читаются как авторская позиция (Alex DC),
    не как peer-reviewed источник."
status: research
supersedes: none
extends:
  - knowledge/research/llm-wiki-community-batch-1.md  # §3.3 краткий обзор
related:
  - knowledge/research/llm-wiki-critique.md
  - knowledge/research/llm-wiki-critique-first-agent.md
  - knowledge/research/agent-roles.md
claims_requiring_verification:
  - "memm.dev/docs/whitepaper заявляет «sub-10ms на запрос» для Rust
    scoring engine — нет публичного бенчмарка с указанием размера
    корпуса/железа; считать как design target, не измерение."
  - "Заявление о ~`/`-стороне «filesystem-first» не отменяет того, что
    `engine.rs:execute_context_query` каждый раз делает полный
    `scan_memories(root)` + `read_memory(...)` для всех найденных файлов
    (engine.rs:96–107). На больших корпусах это станет узким местом —
    в коде нет в-памяти кэша или инкрементального индекса."
  - "Декларируется 4 типа онтологии (source/entity/concept/synthesis)
    как стабильный контракт; в `MemoryOntology` есть `Unknown` вариант
    с `#[serde(other)]` (types.rs:11–17). Это значит схема ещё дрифтит
    де-факто, что важно для совместимости."
scope: |
  Глубокий разбор бэкенда AI-Context-OS (MEMM) применительно к
  First-Agent. Не дублирует §3.3 в `llm-wiki-community-batch-1.md`,
  а раскрывает ровно то, о чём попросил пользователь: backend code
  snippets и архитектурные паттерны, пригодные для имплементации в
  нашем агенте позже. Без оценок «production-ready / нет» (это
  сделано в batch-1); фокус — что именно копировать на уровне
  кода/контракта и что — нет.
---

# AI-Context-OS (MEMM) — глубокий разбор бэкенда

> **Статус:** research note, 2026-04-26.
> **Что внутри:** дополняет §3.3 в
> [`llm-wiki-community-batch-1.md`](./llm-wiki-community-batch-1.md).
> Раскрывает: (1) карту бэкенда MEMM по модулям, (2) ключевые
> data-контракты, (3) точные code-snippets, готовые к адаптации в
> First-Agent, (4) WIP-добавления в ветке `codex/inbox-review-ui-phase2`
> (Inbox enrichment + Ingest Proposals), (5) что НЕ берём.

## 1. TL;DR — что хочется забрать

Пять вещей, которые я бы взял в FA сразу, и одна — отложил:

1. **Memory data-contract** (frontmatter + `<!-- L1 -->` / `<!-- L2 -->`
   markers + level-aware loader). Это плоский, не-database контракт,
   git-friendly, и его можно ввести в нашем `knowledge/` уже сейчас.
2. **`execute_context_query` как deterministic shell** вокруг scoring
   (см. §4.1). Pure function, легко тестируется, легко переписать на
   Python.
3. **Hybrid scoring с интент-зависимыми весами** (§4.2). Шесть сигналов
   в одном dataclass + три профиля весов. Эталон того, что мы хотели
   как «explainable scoring» в `agent-roles.md`.
4. **MCP tool-shape**: `get_context / save_memory / get_skill /
   log_session` (§4.5). Это удачный минимальный API для агента-памяти,
   который мы можем экспортировать как `src/memory/mcp.py` без Tauri.
5. **Folder contracts (`.folder.yaml`)** (§4.6) — декларативные
   lifecycle-policies на папку. Простой механизм, закрывает реальную
   проблему («inbox должен быть transient, sources — immutable»).
6. **Откладываем:** ингест-прокси с LLM-провайдерами (Anthropic /
   OpenRouter / LM Studio / Ollama), `inbox.rs` на 3900 строк (§5).
   Слишком большая поверхность для v0.1; это проект сам по себе.

## 2. Карта бэкенда — что где живёт

```text
src-tauri/src/
├── core/                   # домен; чистый, без Tauri-зависимостей
│   ├── types.rs    (728)   # MemoryMeta, Memory, ScoreBreakdown,
│   │                       # IngestProposal, Config, GraphNode, …
│   ├── frontmatter.rs(106) # YAML parse/serialize + body split
│   ├── levels.rs    (76)   # split_levels / join_levels / estimate_tokens
│   ├── index.rs     (110)  # scan_memories(root) → [(meta, path)]
│   ├── memory.rs    (43)   # read_memory / write_memory (+ usage)
│   ├── usage.rs     (96)   # access tracking → .cache/memory-usage.json
│   ├── search.rs    (234)  # tokenize, BM25, tag/L0 overlap
│   ├── scoring.rs   (336)  # 6-сигнальный hybrid scoring
│   ├── engine.rs    (437)  # 2-pass execute_context_query → ContextResult
│   ├── graph.rs     (885)  # PPR, community detection, GraphNode
│   ├── decay.rs     (46)   # Ebbinghaus-modified decay
│   ├── governance.rs(261)  # conflicts, decay candidates, consolidation
│   ├── folder_contract.rs(187) # .folder.yaml schema + validators
│   ├── router.rs    (452)  # RouterManifest + 4 артефакта (claude/cursor/…)
│   ├── compat.rs    (42)   # adapter-format glue
│   ├── mcp.rs       (498)  # rmcp ServerHandler + 4 tools
│   ├── mcp_http.rs  (54)   # Axum-обёртка stdio→HTTP/SSE на :3847
│   ├── observability.rs(662) # SQLite в .cache/observability.db
│   ├── health.rs    (150)  # health score
│   ├── optimizer.rs (249)  # optimization suggestions
│   ├── wikilinks.rs (820)  # [[link]] парсер + резолвер
│   └── …
├── commands/               # Tauri-binds; тонкая обёртка над core
│   ├── inbox.rs    (3900)  # WIP: ingest pipeline + LLM-провайдеры
│   ├── memory.rs    (845)  # CRUD + rename/duplicate/move/backlinks
│   ├── onboarding.rs(761)  # template bootstrap
│   ├── vault.rs     (223)  # workspace lifecycle
│   ├── filesystem.rs(325)  # raw read/write
│   └── …
├── lib.rs           (290)  # invoke_handler — central registry
├── state.rs         (125)  # AppState (Arc<RwLock<…>>)
├── cli.rs                  # MCP stdio entrypoint
└── main.rs                 # tauri::Builder bootstrap
```

Архитектурный принцип здесь — **«core ничего не знает о Tauri»**. Это
важно для нас: всё что в `core/`, можно перенести один-в-один в
Python-пакет (`src/memory/{types,frontmatter,levels,scoring,engine}.py`)
без Tauri-зависимости. `commands/` мы пропускаем целиком — у нас CLI,
а не десктоп.

> **Чтение по порядку:** `types.rs` → `frontmatter.rs` → `levels.rs` →
> `index.rs` → `scoring.rs` → `engine.rs` → `mcp.rs`. Шесть файлов
> ~1800 строк суммарно — это вся «сердцевина» MEMM. Всё остальное —
> вспомогательное.

## 3. Data-контракт памяти

### 3.1 Memory как файл

Каждая память — это `.md` с YAML-frontmatter и **двумя обязательными
маркерами тела**: `<!-- L1 -->` и `<!-- L2 -->`. Frontmatter-схема
(`MemoryMeta`):

```rust
// src-tauri/src/core/types.rs:37–83
pub struct MemoryMeta {
    pub id: String,
    #[serde(rename = "type", default = "default_ontology")]
    pub ontology: MemoryOntology,            // source|entity|concept|synthesis
    #[serde(default)] pub l0: String,
    #[serde(default = "default_importance")] pub importance: f64,   // 0..1
    #[serde(default = "default_decay_rate")] pub decay_rate: f64,   // 0.998
    #[serde(default = "Utc::now", skip_serializing)]
    pub last_access: DateTime<Utc>,          // НЕ пишется на диск
    #[serde(default, skip_serializing)] pub access_count: u32,      // НЕ пишется
    #[serde(default = "default_confidence")] pub confidence: f64,   // 0.9
    #[serde(default)] pub tags: Vec<String>,
    #[serde(default)] pub related: Vec<String>,
    #[serde(default = "Utc::now")] pub created: DateTime<Utc>,
    #[serde(default = "Utc::now")] pub modified: DateTime<Utc>,
    #[serde(default = "default_version")] pub version: u32,
    // skill-специфичные
    #[serde(default)] pub triggers: Vec<String>,
    #[serde(default)] pub requires: Vec<String>,
    #[serde(default)] pub optional: Vec<String>,
    #[serde(default)] pub output_format: Option<String>,
    #[serde(default)] pub status: Option<MemoryStatus>,
    #[serde(default)] pub protected: bool,
    #[serde(default)] pub derived_from: Vec<String>,
    // derived runtime fields, не сериализуются на диск
    #[serde(default, skip_serializing, skip_deserializing)]
    pub folder_category: Option<String>,
    #[serde(default, skip_serializing, skip_deserializing)]
    pub system_role: Option<SystemRole>,     // Rule | Skill
}
```

Три инженерных решения, которые я бы скопировал буквально:

1. **`#[serde(skip_serializing)]` на `last_access`/`access_count`.** Это
   ровно то, чего нам не хватает в идее «git-friendly knowledge»:
   counter-поля, обновляемые на каждый чтение, разнесены по
   *внеканоническому* `.cache/memory-usage.json` (см. `usage.rs:25–35`),
   а frontmatter остаётся стабильным между коммитами.
2. **`MemoryOntology::Unknown` с `#[serde(other)]`** (`types.rs:11–17`)
   — forward-compatible обработка неизвестных значений. Память
   подгружается, только scoring даёт нейтральный вес. Нам это пригодится
   как только мы заведём своё перечисление ролей/типов.
3. **`derived_from: Vec<String>`** — explicit provenance. Это первый
   экземпляр chain-of-custody на уровне data-model'и, который я видел в
   open-source LLM-wiki проектах. Прямая параллель с
   `chain_of_custody:` во frontmatter наших research-заметок.

### 3.2 Levels-парсер: 76 строк, переиспользовать как есть

```rust
// src-tauri/src/core/levels.rs:1–31
pub fn split_levels(body: &str) -> (String, String) {
    let l1_marker = "<!-- L1 -->";
    let l2_marker = "<!-- L2 -->";
    let l1_start = body.find(l1_marker);
    let l2_start = body.find(l2_marker);
    match (l1_start, l2_start) {
        (Some(l1_pos), Some(l2_pos)) => {
            let l1 = body[l1_pos + l1_marker.len()..l2_pos].trim().to_string();
            let l2 = body[l2_pos + l2_marker.len()..].trim().to_string();
            (l1, l2)
        }
        (Some(l1_pos), None) => (body[l1_pos + l1_marker.len()..].trim().to_string(), String::new()),
        (None, Some(l2_pos)) => (body[..l2_pos].trim().to_string(), body[l2_pos + l2_marker.len()..].trim().to_string()),
        (None, None) => (body.trim().to_string(), String::new()),
    }
}

pub fn estimate_tokens(text: &str) -> u32 {
    (text.split_whitespace().count() as f64 * 1.3).ceil() as u32
}
```

Я бы перевёл это в Python один-в-один как ~30 строк (split на двух
маркерах + грубый token-estimate). Это весь L0/L1/L2-механизм; всё
остальное — *политика* того, какой уровень загружать.

## 4. Что копируем/адаптируем (с кодом)

### 4.1 Two-pass `execute_context_query`

Это «deterministic shell» поверх scoring. Pure function, всё состояние —
в аргументах, easy to test. Структура:

```rust
// src-tauri/src/core/engine.rs:90–162 (упрощено)
pub fn execute_context_query(
    root: &Path, query: &str, token_budget: u32, config: &Config,
) -> Result<ContextResult, String> {
    let all_entries = scan_memories(root);
    let mut memories: Vec<Memory> = all_entries.iter()
        .filter_map(|(meta, path)| {
            read_memory(root, Path::new(path)).ok().map(|mut m| { m.meta = meta.clone(); m })
        })
        .collect();
    // ... empty-check ...

    let documents: Vec<&str> = memories.iter().map(|m| m.raw_content.as_str()).collect();
    let bm25_corpus = Bm25Corpus::from_documents(&documents);
    let empty_ppr = HashMap::new();

    // PASS 1 — без графа, чтобы найти seeds
    let mut base_scored: Vec<(usize, ScoreBreakdown)> = memories.iter().enumerate()
        .map(|(i, m)| (i, compute_score(query, m, &memories, &bm25_corpus, &empty_ppr, now)))
        .collect();
    base_scored.sort_by(|a, b| b.1.final_score.partial_cmp(&a.1.final_score).unwrap_or(Equal));
    let selected_ids: Vec<String> = base_scored.iter().take(5)
        .map(|(idx, _)| memories[*idx].meta.id.clone()).collect();

    // PASS 2 — с PPR, seeds = top-5
    let ppr_scores = personalized_pagerank(&memories, &selected_ids, 0.15);
    let mut scored = memories.iter().enumerate()
        .map(|(i, m)| (i, compute_score(query, m, &memories, &bm25_corpus, &ppr_scores, now)))
        .collect::<Vec<_>>();
    // ... sort, skill force-load (см. §4.4), greedy budget allocation ...
}
```

**Что забираем:**
- two-pass паттерн дословно. PPR без сидов даёт случайные результаты;
  PPR с сидами из top-5 первого прохода — это конкретное архитектурное
  решение, которое снимает graph-bias. (Уже отмечено в batch-1 §4.1, но
  здесь — *как именно* это сделано в коде.)
- разделение `LoadedMemory` / `UnloadedMemory` (`engine.rs:16–40`) с
  явным `reason: "budget_exhausted" | "below_threshold"`. Это
  готовая explainability-структура: пользователь/агент видит, почему
  память *не* попала в контекст.
- `force_load` для `requires` зависимостей skill'ов (`engine.rs:164–178`)
  — обязательный паттерн для роли «agent должен видеть зависимости
  выбранного навыка целиком».

### 4.2 Hybrid scoring — 6 сигналов в одной структуре

```rust
// src-tauri/src/core/types.rs:128–137
pub struct ScoreBreakdown {
    pub semantic: f64,
    pub bm25: f64,
    pub recency: f64,
    pub importance: f64,
    pub access_frequency: f64,
    pub graph_proximity: f64,
    pub final_score: f64,
}
```

Финальный скор — линейная комбинация шести компонентов с
**интент-зависимыми весами**. Три профиля:

```rust
// src-tauri/src/core/scoring.rs:32–71 (упрощено)
fn detect_intent_weights(query: &str) -> ScoringWeights {
    if is_debug    { ScoringWeights { semantic: 0.20, bm25: 0.30, graph: 0.30,
                                       recency: 0.10, importance: 0.05, access_frequency: 0.05 } }
    else if is_brainstorm
                   { ScoringWeights { semantic: 0.30, bm25: 0.05, graph: 0.05,
                                       recency: 0.25, importance: 0.30, access_frequency: 0.05 } }
    else           { ScoringWeights { semantic: 0.30, bm25: 0.15, graph: 0.10,
                                       recency: 0.15, importance: 0.20, access_frequency: 0.10 } }
}
```

Веса сумма 1.0 во всех трёх случаях. Намерение детектируется по
пересечению **стемов** запроса со словарями `DEBUG_VOCAB` /
`BRAINSTORM_VOCAB` (билингвально ES/EN, `scoring.rs:22–29`).

**Что я бы взял:**
- структуру `ScoreBreakdown` целиком — это и retrieval-result, и
  готовый logging payload.
- интент-driven веса как идею. Под FA это, скорее всего, будет
  `task | debug | review | spec`, не `debug | brainstorm | default`,
  но *механика* — словарь стемов → выбор профиля — копируется в 30
  строк.
- query expansion через synonym clusters (`scoring.rs:79–105`) —
  дёшево, существенно повышает recall в BM25, не делает запрос
  «семантическим» (что важно: explicit, не магия).

**`semantic_score_free`** — отдельно интересен (`scoring.rs:159–217`):
вместо честного embedding-косинуса используется
`0.4*tag_score + 0.35*l0_keyword_score + 0.25*ontology_bonus`. Без
embedding-инфраструктуры. Для старта v0.1 это правильный «poor man's
semantic», который можно потом заменить на нормальный embedding-
сигнал, не перетряхивая контракт.

### 4.3 Greedy token-budget с трёх-уровневой лестницей

```rust
// src-tauri/src/core/engine.rs:54–83
fn select_load_level(
    score: f64, top_score: f64, l2_loaded_count: usize,
    is_force_loaded: bool, remaining_budget: u32,
    l0_tokens: u32, l1_tokens: u32, l2_tokens: u32,
) -> Option<(LoadLevel, u32)> {
    let l2_threshold = top_score.mul_add(0.9, 0.0).max(0.3);
    let l1_threshold = top_score.mul_add(0.65, 0.0).max(0.15);

    if l2_loaded_count < 3
        && remaining_budget >= l0_tokens + l1_tokens + l2_tokens
        && score >= l2_threshold
    { return Some((LoadLevel::L2, l0_tokens + l1_tokens + l2_tokens)); }

    if remaining_budget >= l0_tokens + l1_tokens
        && (score >= l1_threshold || is_force_loaded)
    { return Some((LoadLevel::L1, l0_tokens + l1_tokens)); }

    if remaining_budget >= l0_tokens { return Some((LoadLevel::L0, l0_tokens)); }
    None
}
```

Три инженерных детали:
1. **Пороги адаптивные относительно top-score**, не абсолютные. Это
   значит, что в «слабых» запросах (top_score=0.4) всё равно что-то
   загрузится. В абсолютных порогах нижний хвост запросов
   возвращал бы пустоту.
2. **Жёсткий cap `l2_loaded_count < 3`**. Не больше трёх памятей в
   полном объёме на запрос. Это и про «Lost in the Middle», и про
   стоимость.
3. **`is_force_loaded` обходит порог L1**, но не L2. То есть зависимости
   skill'а гарантированно попадут на уровне summary, но не накачают
   токенный бюджет полным телом.

Этот алгоритм у нас перекладывается на Python в ~50 строк.

### 4.4 Skills как memory с force-load зависимостями

Skill — это та же `Memory` с `system_role: Skill` (полученным из
пути, `paths.rs::enrich_memory_meta`) + frontmatter-полями `triggers /
requires / optional / output_format`. Логика активации:

```rust
// src-tauri/src/core/engine.rs:164–195 (упрощено)
let mut force_load_ids: HashSet<String> = HashSet::new();
let mut boost_ids: HashSet<String> = HashSet::new();
for (idx, score) in scored.iter().take(5) {
    let mem = &memories[*idx];
    if mem.meta.system_role != Some(SystemRole::Skill) || score.final_score <= 0.15 {
        continue;
    }
    for req_id in &mem.meta.requires { force_load_ids.insert(req_id.clone()); }
    for opt_id in &mem.meta.optional { boost_ids.insert(opt_id.clone()); }
}
// Apply optional boost
let mut scored: Vec<_> = scored.into_iter()
    .map(|(idx, mut s)| {
        if boost_ids.contains(&memories[idx].meta.id) {
            s.final_score = (s.final_score + 0.1).min(1.0);
        }
        (idx, s)
    }).collect();
```

Семантика:
- если **в топ-5 скорится skill** с порогом ≥0.15, его `requires` —
  **force-loaded** (минимум на L1), `optional` — **+0.10 boost к
  final_score** (не выше 1.0).
- skill, который сам не попал в топ-5, не активирует свои зависимости.
  Это аккуратно: skills не «прорываются» через скоринг, они только
  усиливают своё окружение, когда сами релевантны.

Это **готовый паттерн для нашего `agent-roles.md` §8** (где мы
обсуждали SKILL.md). Когда дойдёт до имплементации:
- складываем роли в `knowledge/skills/<role>.md` с frontmatter
  `system_role: skill`, `triggers: [...]`, `requires: [...]`,
  `optional: [...]`, `output_format: "markdown"`.
- активация — через тот же scoring-проход, что и обычные памяти.
  Никакого отдельного «registry of agents».

### 4.5 MCP API — четыре инструмента, минимум

Шейп API (`mcp.rs:171–178`, `mcp.rs:246–264`, …):

| Tool | Цель | Параметры |
|---|---|---|
| `get_context` | загрузить релевантный контекст | `query`, `token_budget=4000`, `session_id?` |
| `save_memory` | создать/обновить файл-память | `id`, `ontology`, `l0`, `importance`, `tags[]`, `l1_content`, `l2_content`, `folder?` |
| `get_skill` | вытащить skill по id (форс-загрузка зависимостей) | `skill_id` |
| `log_session` | записать событие сессии | `event_type`, `summary`, `tags[]`, `source` |

**Почему это минимум, а не «50 endpoints»:**
- **`get_context` принимает свободный `query`**, а не списки тегов /
  фильтров. Это правильно для агента: внутреннее намерение → один
  запрос → готовый пакет контекста. Никаких построенных вручную SQL.
- **`save_memory` валидирует `ontology` через explicit match-arm**
  (`mcp.rs:253–264`), а не через `serde::deserialize`. Если LLM
  пришлёт `ontology=fact`, она получит понятную ошибку, а не «failed
  to deserialize ontology field» из недр serde. Дёшево, но
  пользователь-агент видит правильную ошибку.
- **`folder` в `save_memory` whitelisted** до `inbox` / `.ai/skills` /
  `.ai/rules` / любая user-папка (`mcp.rs:75–118`). Path-traversal
  блокируется на парсинге компонентов (никаких `..`).

Это та форма, которую мы можем взять для `src/memory/mcp.py`. Для FA
без Tauri-фронта это будет CLI-скрипт + `stdio`-MCP сервер на
[`fastmcp`](https://gofastmcp.com/) (или `python-mcp`), без HTTP
обвязки.

### 4.6 Folder Contracts (`.folder.yaml`) — 187 строк, копируем

Декларативный контракт на папку. Это решает реальную проблему,
которую мы тоже встретим: «как заставить inbox быть transient,
sources — immutable, а .ai/skills — требовать `triggers` в
frontmatter».

```rust
// src-tauri/src/core/folder_contract.rs:9–46
pub enum FolderLifecycle { Transient, Permanent, Immutable }

pub struct FolderContract {
    pub role: String,                     // "inbox" | "skill" | "rule" | "source"
    pub description: String,
    pub lifecycle: FolderLifecycle,
    #[serde(default = "default_true")] pub scannable: bool,
    #[serde(default = "default_true")] pub writable_by_mcp: bool,
    #[serde(default)] pub required_fields: Vec<String>,
    #[serde(default)] pub optional_fields: Vec<String>,
    #[serde(default)] pub default_values: HashMap<String, serde_yaml::Value>,
}
```

Валидация — `check_required_fields` (`folder_contract.rs:66–84`):
неизвестные имена полей **тихо проходят** (forward-compatible), известные
проверяются на «присутствует и непуст». Логирование — через
`log::warn!` в `index.rs:75–82`, не через ошибку: legacy-контент
не блокируется.

Для FA это пригодится сразу: `knowledge/.folder.yaml` (lifecycle:
permanent, required: id/title), `knowledge/inbox/.folder.yaml`
(lifecycle: transient, required: id/title/status). Это **дешёвая
формализация** того, что у нас сейчас живёт в AGENTS.md как «правила
для людей».

### 4.7 Декаpoint: Ebbinghaus-modified — берём как идею, не формулу

```rust
// src-tauri/src/core/decay.rs (весь файл — 46 строк)
pub fn effective_decay(base_rate: f64, access_count: u32) -> f64 {
    let exponent = 1.0 / (1.0 + 0.1 * access_count as f64);
    base_rate.powf(exponent)
}
pub fn decay_score(base_rate: f64, access_count: u32, days_since_last_access: f64) -> f64 {
    effective_decay(base_rate, access_count).powf(days_since_last_access)
}
pub fn should_archive(base_rate: f64, access_count: u32, days_since: f64, threshold: f64) -> bool {
    decay_score(base_rate, access_count, days_since) < threshold
}
```

В `llm-wiki-critique.md` мы уже отметили: Ebbinghaus — это про человека,
не про KB. **Сама формула — метафора**, поэтому переносить её буквально
не надо. Но **сам приём — «декей не как линия, а как функция от
access_count»** — правильный. Когда дойдём до своего decay'я:
- считать за «активность» обращения через `usage.json` (как у MEMM,
  `usage.rs:47–96`), а не через mtime файла.
- использовать декей **только для пометки `archive_candidate: true`**,
  не для вытеснения из retrieval (`governance.rs:69–82`). Это
  governance-сигнал, не retrieval-фильтр.

### 4.8 Wikilinks с резолвером — 820 строк, дороговато

`wikilinks.rs` — это полноценный парсер `[[...]]` + резолвер с пятью
исходами:

```rust
// src-tauri/src/core/wikilinks.rs:60–73
pub enum WikilinkResolution {
    ExactId    { id: String },                              // matched meta.id
    ExactL0    { id: String },                              // unique meta.l0
    FuzzyL0    { id: String },                              // case-insensitive l0
    Ambiguous  { candidates: Vec<WikilinkCandidate> },      // не auto-resolve
    Unresolved,
}
```

Resolver-policy: id → l0-exact → l0-fuzzy. **Никогда не auto-resolve
при множественных совпадениях.** Это ровно та политика, которую мы
обсуждали в `llm-wiki-critique.md` (failure mode — silent rewriting).

**Что я бы сделал в FA проще:** взять только `parse_wikilinks` (~50
строк, regex `\[\[([^\[\]\n]+?)\]\]` + dedup) и резолвер по `id`. Поля
`l0`-fuzzy — overkill для v0.1.

### 4.9 Observability как SQLite, не frontmatter

Принципиальный архитектурный выбор: **`access_count` и `last_access`
не в frontmatter**, а в `.cache/memory-usage.json` (по последним
коммитам — раньше был `observability.db`, но реверт на JSON для
git-cleanness). Schema:

```rust
// src-tauri/src/core/usage.rs:11–23
pub struct MemoryUsageEntry {
    pub last_access: DateTime<Utc>,
    pub access_count: u32,
}
struct MemoryUsageStore {
    memories: HashMap<String, MemoryUsageEntry>,
}
```

Записывается атомарно после `get_context`-ответа
(`mcp.rs:236–238` → `record_accesses`). На diff'ы не влияет.

Telemetry-DB (`observability.db`, SQLite) — отдельно, со схемой:
`context_requests`, `memories_served`, `memories_not_loaded`,
`optimizations`, `health_score_history` (`observability.rs:120–183`).
Это уже опционально и не нужно для retrieval — только для аналитики.

**Что я бы взял для FA:** идею «counter-fields НЕ во frontmatter» как
жёсткий контракт. Без этого `git log` нашего `knowledge/` через месяц
будет неразличимым шумом.

## 5. WIP в `codex/inbox-review-ui-phase2`: что нового на бэке

Ветка отстаёт от main на 23 коммита; **бэкенд этой ветки = main**, все
изменения — в UI (`src/components/InboxView.tsx` и пр.). Но
сам Inbox-pipeline (включая `inbox.rs:3900` строк) — ВВ принципе
*относительно свежий код* в репо (последний крупный мерж — `9334d32:
feat: complete inbox enrichment backend pass`). Кратко по сути:

### 5.1 Цикл inbox-item

```text
[capture]  create_inbox_text | create_inbox_link | import_inbox_files
   ↓ writes  inbox/<slug>.md  with frontmatter (kind, status: New, ...)
[normalize]  normalize_inbox_item / normalize_inbox_batch
   ↓ status: Normalized
[propose]  generate_ingest_proposals
   ↓ для каждого item:
   ↓   build_memory_corpus(root) — vec<MemoryCorpusEntry>
   ↓   find_inbox_duplicate_candidates(item, items) — content_hash + url
   ↓   build_inbox_enrichment(root, item, corpus, dups)
   ↓     • destination candidates (по фолдер-контрактам + score)
   ↓     • related memory candidates (BM25 + tag + l0 over corpus)
   ↓   heuristic_proposal или duplicate_proposal
   ↓   apply_heuristic_enrichment → инжектит destination/related/dup
   ↓   infer_proposal (LLM provider, если настроен) → может перезаписать
   ↓ writes  .ai/proposals/<id>.json  (state: Pending)
   ↓ status: ProposalReady
[review]  list_ingest_proposals (UI рисует карточки)
[apply]   apply_ingest_proposal | reject_ingest_proposal
   ↓ promote_memory | route_to_sources | update_memory | discard
   ↓ status: Processed | Promoted | Discarded
```

### 5.2 Что важно: proposal — это explicit, audit'ируемый, JSON

Файл `.ai/proposals/<id>.json` со схемой:

```rust
// src-tauri/src/core/types.rs:526–568
pub struct IngestProposal {
    pub id: String,
    pub item_id: String,
    pub item_path: String,
    pub action: ProposalAction,             // promote | route | update | discard | needs_review
    pub state: ProposalState,               // pending | approved | rejected | applied | error
    pub confidence: f64,
    pub rationale: String,                  // human-readable объяснение
    pub destination: Option<String>,
    pub target_memory_id: Option<String>,
    pub ontology: Option<MemoryOntology>,
    pub l0: Option<String>,
    pub l1_content: Option<String>,
    pub l2_content: Option<String>,
    pub tags: Vec<String>,
    pub derived_from: Vec<String>,
    pub related_memory_candidates: Vec<InboxRelatedMemoryCandidate>,
    pub duplicate_candidates: Vec<InboxDuplicateCandidate>,
    pub destination_candidates: Vec<InboxDestinationCandidate>,
    pub inference_provider: Option<InferenceProviderKind>,
    pub origin: String,
    // ...
}
```

Это **очень хорошо легло**. Главное:
- `confidence` + `rationale` — встроены в контракт. Не «что-то посчитали
  и записали», а «вот цифра, вот текстовое обоснование, апнуть/реджектнуть
  можно с полной аудиторией».
- `related_memory_candidates`, `duplicate_candidates`,
  `destination_candidates` — *эвристики поверх корпуса* (BM25/tag/url-
  match), которые **передаются в prompt LLM**, чтобы тот не делал
  дублирование вслепую (`inbox.rs:585–657`). Hybrid: алгоритмика → LLM,
  не «всё в LLM».

### 5.3 Что я бы перенёс в FA из ингест-пайплайна

Из всех 3900 строк — **примерно 200 переносимы** в виде паттерна,
остальное специфично для Tauri-приложения:

1. **Schema `IngestProposal`** как формат для нашего будущего
   «ingest»-этапа (когда мы будем материалы из `inbox/` промотать в
   `knowledge/`). У нас это сейчас делается руками; формализация в
   виде JSON-proposal с `confidence/rationale/destination_candidates`
   — правильный шаг, **независимо от того, делает proposal LLM или
   эвристика**. Файл proposal — это аудиторская строка.
2. **Hybrid pipeline: эвристика → enrichment → LLM, с явными
   `_candidates`-полями.** Чтобы LLM решал в контексте, а не угадывал
   с нуля.
3. **Markdown-fence stripping для JSON-ответов LLM**
   (`inbox.rs:204–227`). Универсальный код, который ловит
   ` ```json...``` ` / ` ```...``` ` / голый JSON. У нас он
   обязательно понадобится в любой LLM-tool-call'е.

### 5.4 Что НЕ переносим из inbox.rs

- **Слой провайдеров** (Anthropic / OpenAI / OpenRouter / Ollama /
  LM Studio) — `inbox.rs:1088–1620`. Это правильно сделано
  (с `lm_studio_model_state` пробами, capabilities-detection,
  base-url валидацией), но это **отдельный модуль**, не «часть памяти».
  Когда дойдём до LLM-клиента в FA — берём оттуда вдохновение,
  но не таскаем целиком в memory-модуль.
- **Tauri-эмиты `inference-progress` / `proposals-changed`**
  (`inbox.rs:2832–2881`). У нас CLI; вместо этого — обычное
  логирование / JSON-stream stdout.

## 6. Что у MEMM сделано **не очень хорошо** (предупреждения)

Это полезно для контекста: даже когда копируем паттерн, надо знать
известные слабости.

1. **`scan_memories(root)` на каждый запрос.** `engine.rs:96` каждый
   раз делает рекурсивный обход + `read_memory(...)` для всех
   найденных файлов. На 1000 памятей это уже не sub-10ms (как
   декларируется в whitepaper). Нет в-памяти кэша; нет
   инкрементального индекса; `core/watcher.rs` (109 строк) только
   реагирует на FS-события для пересборки router-артефактов, не для
   индекса. Если будем брать engine — добавляем кэш сразу.
2. **Conflict detection через хардкод-пары** (`governance.rs:27–52`).
   Список `[("react", "vue"), ("postgres", "mysql"), …]` буквально в
   коде. Это работает на демо, но не масштабируется. У нас стоит
   делать через **конфиг**, не код, либо вообще не делать (это самый
   шумный сигнал из всего governance-набора).
3. **`MemoryOntology::Unknown` с `#[serde(other)]` теряет исходную
   строку** (`types.rs:11–17`). Round-trip lossy: если в файле было
   `type: fact`, после сериализации станет `type: unknown`. Для нас
   это разрушительно — мы пишем frontmatter руками. Фикс: хранить
   `Unknown(String)` либо отдельное поле `ontology_raw: Option<String>`.
4. **Скоринг линеен по 6 сигналам.** Для ML-энтузиастов: сумма с
   фиксированными весами не выучится из логов
   `observability.memories_served`. Они сами это знают (см.
   `optimizer.rs`), но «адаптации весов от телеметрии» в коде нет —
   только suggestions для пользователя.
5. **Никаких embedding'ов.** Заявлено «hybrid scoring», но
   `semantic` — это перекрытие тегов + L0 + ontology bonus
   (`scoring.rs:159–217`). Нет cosine-similarity, нет vector-store,
   нет retrieval по embedding'ам. Это **сознательный
   выбор** (см. memm.dev/docs/whitepaper «No vector database»), но
   надо понимать, что в их smysле «semantic» ≠ что обычно понимают
   под этим словом.
6. **`mcp_http.rs` — `CorsLayer::new().allow_origin(Any)`**
   (`mcp_http.rs:29–32`). На локальной машине допустимо, но
   `127.0.0.1:3847/mcp` без CORS-ограничений — это потенциальный
   вектор атаки через браузер. У них это compromise ради
   совместимости с Cursor. Нам в CLI этот файл не нужен вообще.

## 7. Конкретный bookkeeping для FA

Семь следующих шагов (если решим имплементировать):

1. **ADR-000X: «Frontmatter + L0/L1/L2 markers как формат памяти
   для FA».** Опции: (a) как у MEMM (frontmatter + `<!-- L1 -->` /
   `<!-- L2 -->`), (b) только frontmatter, всё остальное — body, (c)
   две раздельные формы (брифы vs полный текст). Решение, скорее
   всего, (a) — оно же рекомендовано всем нашим backlog'ом
   research-заметок и в `docs/architecture.md § Архитектура памяти`.
2. **Завести `knowledge/inbox/.folder.yaml`** с lifecycle: transient,
   required: `[id, title, status]`, и валидатор в Python (~80 строк
   эквивалент `folder_contract.rs`). До любого кода в `src/`.
3. **Перевести `levels.py` (split/join/estimate_tokens) — ~50 строк
   Python** + `frontmatter.py` (yaml + body, ~50 строк).
4. **Перевести `search.py` (tokenize + bm25 + tag/l0 overlap) — ~100
   строк Python**. Использовать `nltk` Snowball или `snowballstemmer`
   как в Rust-исходнике.
5. **Перевести `scoring.py` — ~150 строк** с теми же 6 сигналами.
   Embeddings *пропустить*; `semantic_score` оставить как
   tag+l0+ontology как у них.
6. **Перевести `engine.py::execute_context_query` — ~200 строк**.
   Это ядро. Сразу с `LoadedMemory/UnloadedMemory.reason`.
7. **Эспортнуть это как `mcp_server.py`** (на `fastmcp` или
   аналоге), четыре tool'а (get_context / save_memory / get_skill /
   log_session). Не HTTP, только stdio. CORS-проблемы из §6.6 не
   возникает.

Суммарно — **~700 строк Python**, плюс тесты. Это посильный объём для
v0.1; и он закроет всё, что MEMM делает в `core/`. Wikilinks,
governance, decay, observability, graph-PPR — отложим в `roadmap.md`.

## 8. Что брать в FA (cheat-sheet — две колонки)

| Берём (с кодом) | Откладываем / не берём |
|---|---|
| Frontmatter + `<L1>/<L2>` body markers как формат | Tauri десктоп, MCP-HTTP, CORS-обвязка |
| `MemoryMeta` schema (с `derived_from`, `protected`, `triggers/requires/optional`) | Полный `inbox.rs` со слоем LLM-провайдеров (это отдельный модуль) |
| `levels.rs::{split, join, estimate_tokens}` | `wikilinks.rs` целиком (820 строк); только `parse + id-resolve` |
| `frontmatter.rs::{parse, serialize}` со `skip_serializing` на runtime-полях | `graph.rs` целиком (885 строк); PPR — потом, не для v0.1 |
| `search.rs::{tokenize, bm25, tag/l0 overlap}` | Embedding-семантика (у них и нет; не делаем) |
| `scoring.rs::{6 сигналов, intent-aware веса, query-expansion}` | Conflict detection через захардкоженные tech-пары |
| `engine.rs::execute_context_query` (two-pass паттерн) | `optimizer.rs` (governance suggestions) — отложим |
| `select_load_level` (адаптивные пороги, cap L2≤3) | `observability.rs` SQLite-схема — заменим на JSONL для v0.1 |
| MCP API shape (4 tool'а) | `mcp_http.rs` (CORS-Any) — только stdio для CLI |
| `folder_contract.rs` (`.folder.yaml`) | `decay.rs` буквально — формула как метафора, не закон |
| `IngestProposal` schema как audit-формат | `health.rs` / `health_score_history` — нет до v0.2 |
| `usage.rs` (counter-поля **не в frontmatter**) | `compat.rs` adapter glue — у нас один потребитель |
| Markdown-fence stripping для LLM JSON-ответов (`inbox.rs:204–227`) | `commands/*.rs` целиком — это Tauri-обвязка |

## 9. Нерешённые вопросы

- **Делаем ли мы graph-proximity сразу или нет?** PPR без графа —
  бесполезен, граф без адекватного количества памятей (n<50) тоже.
  Скорее всего, в v0.1 фиксируем `graph_proximity = 0` во всех
  профилях весов, добавляем граф позже. Зафиксировать в ADR.
- **Onthology — четыре или другое?** У MEMM:
  source/entity/concept/synthesis. У нас в текущих research-заметках
  понятия другие (`research`, `adr`, `prompts`, `glossary`). Смешанная
  таксономия не сходится. Либо принимаем их 4 (ценой переименования
  наших папок), либо вводим свои 4–5. Скорее всего — свои, по
  аналогии. **Это ADR.**
- **Skill triggers активируются через ту же scoring-функцию или
  отдельной dispatch-функцией?** У MEMM — через scoring (если skill в
  топ-5 → активация). Это элегантно, но плохо предсказуемо: skill с
  плохо подобранными `l0/tags` не активируется. Альтернатива — explicit
  `triggers: [...]` matching (как у `agentic-local-brain`). Нужно
  выбрать. **Возможно, ADR.**

## 10. Источники

Все ссылки внутри документа указывают на конкретные строки в
repo на дату 2026-04-26. Главные:

- [`src-tauri/src/core/types.rs`](https://github.com/alexdcd/AI-Context-OS/blob/codex/inbox-review-ui-phase2/src-tauri/src/core/types.rs)
  — data-model.
- [`src-tauri/src/core/scoring.rs`](https://github.com/alexdcd/AI-Context-OS/blob/codex/inbox-review-ui-phase2/src-tauri/src/core/scoring.rs)
  — 6-сигнальный hybrid scoring.
- [`src-tauri/src/core/engine.rs`](https://github.com/alexdcd/AI-Context-OS/blob/codex/inbox-review-ui-phase2/src-tauri/src/core/engine.rs)
  — `execute_context_query` (two-pass).
- [`src-tauri/src/core/mcp.rs`](https://github.com/alexdcd/AI-Context-OS/blob/codex/inbox-review-ui-phase2/src-tauri/src/core/mcp.rs)
  — MCP API shape.
- [`src-tauri/src/core/folder_contract.rs`](https://github.com/alexdcd/AI-Context-OS/blob/codex/inbox-review-ui-phase2/src-tauri/src/core/folder_contract.rs)
  — `.folder.yaml`.
- [`src-tauri/src/commands/inbox.rs`](https://github.com/alexdcd/AI-Context-OS/blob/codex/inbox-review-ui-phase2/src-tauri/src/commands/inbox.rs)
  — WIP ingest pipeline (3900 строк, разбираем выборочно).
- [memm.dev/docs/architecture-and-operating-model](https://memm.dev/docs/architecture-and-operating-model/)
  — авторская позиция Alex DC по «filesystem-first».
- [memm.dev/docs/paper](https://memm.dev/docs/paper/) — design paper
  «Files as Memory».
- [memm.dev/docs/whitepaper](https://memm.dev/docs/whitepaper/) —
  технический whitepaper.
