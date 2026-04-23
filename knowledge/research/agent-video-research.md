# Research — Agent Patterns from 5 YouTube Videos

> **Status:** draft research note, 2026-04-23. Synthesizes transcripts of five
> YouTube videos into a concept map + ranking + concrete recommendations for
> First-Agent. Meant to be loaded as context when making architecture decisions
> (Шаги 2–5 из [README](../../README.md#4-план-исследования-перед-тем-как-писать-код)).
>
> Источники — прямые ссылки на видео в §[Sources](#sources). Транскрипты
> вытянуты через публичные сервисы; цитаты даны дословно, с таймкодами.

## 0. TL;DR

Из пяти видео выкристаллизовываются **пять сквозных тезисов**, которые имеет
смысл заложить в First-Agent с самого начала:

1. **Deterministic shell, probabilistic core.** LLM — не система, а ядро.
   Систему вокруг него делаем детерминированной: фиксированный цикл, жёсткие
   шаги, проверяемые контракты между шагами. Недетерминизм допустим *внутри*
   одного конкретного выбора «какой инструмент вызвать», но не в форме петли.
2. **Четыре композируемых паттерна** (Andrew Ng): *tool use → RAG → planning →
   multi-agent*. Любой работающий агент — их комбинация. Начинаем с tool use,
   добавляем слои по мере необходимости.
3. **Память — семь уровней, не один**. От automemory / `CLAUDE.md` к
   Obsidian-vault к light/graph RAG к агентному multimodal RAG. «Уровень 7» —
   overkill для большинства; для v0.1 целимся в 3–4.
4. **Harness engineering** (rules + commands + hooks + skills) — отдельный
   первоклассный артефакт проекта. Он определяет, *что* агент обязан делать,
   *как*, и *что никогда не должно произойти*. Без harness'а агент — «умный,
   но неуправляемый».
5. **Self-improving loop** возможен уже сегодня (Hermes): auto-retrospective
   → извлечение skill'а из 3+ успешных выполнений → persistence → refresh. Это
   шаг, без которого агент не улучшается от сессии к сессии.

Матрица приоритетов для нас — в §[3. Ranking matrix](#3-ranking-matrix).
Конкретный mapping в наши [`docs/architecture.md`](../../docs/architecture.md) —
в §[5. Implications for First-Agent](#5-implications-for-first-agent).

---

## 1. Videos analyzed

| # | Title | Channel | Length | Character |
|---|---|---|---|---|
| V1 | [Hermes Agent: Self-Improving Strategy Explained](https://www.youtube.com/watch?v=qUqcLNcP5Tc) | Devs Kingdom | 18:34 | Product walkthrough |
| V2 | [The 7 Levels of Claude Code & RAG](https://www.youtube.com/watch?v=kQu5pWKS8GA) | Chase AI | 45:58 | Pedagogical deep-dive |
| V3 | [4 Design Patterns Behind Every AI Agent](https://www.youtube.com/watch?v=pIoKdpsuODg) | TechWhistle | 09:38 | Taxonomy / cheat-sheet |
| V4 | [The Core of an AI Agent Is Determinism](https://www.youtube.com/watch?v=fiysocjyAho) | (personal vlog) | ~07:30 | Practitioner reflection |
| V5 | [Claude Design & the Harness Question: What Agentic Workflows Really Need](https://www.youtube.com/watch?v=n18V4zlIWOo) | (personal vlog) | ~07:30 | Practitioner reflection |

V1–V3 — источники высокой плотности технического содержания. V4–V5 — короткие
daily-log вайбы того же автора-вайботчера; их ценность в том, что они
формулируют то же, что V2–V3, в виде личных «ага-моментов» и подтверждают, что
сообщество сходится на одних и тех же паттернах (harness, determinism,
plan→execute→evaluate).

---

## 2. Concept catalogue

Ниже — все значимые концепты, которые встретились, сгруппированные по темам и
с указанием источников. Каждый концепт переоценён в §3.

### 2.1 Архитектурные паттерны

- **Tool use** (V3). LLM сам не исполняет — генерирует *структурированный
  запрос*, код исполняет. «The LLM doesn't run the tool itself. It generates a
  structured request, usually JSON, and your code handles the execution.
  That's the safety boundary.»
- **RAG** (V2, V3). Три шага: retrieve → augment → generate. RAG — *память*
  для агента, не умение.
- **Planning** (V3). Decompose → execute → reflect. «This loop is the heart of
  every serious AI agent.»
- **Multi-agent** (V3, V1). «Multi-agent isn't a separate pattern. It's the
  composition of all the others.» Каждый суб-агент — свой prompt, свои tools,
  своя ответственность; manager — координатор.
- **Deterministic shell, probabilistic core** (V4, и фоном в V2/V5). Весь loop
  детерминированный; точка, где разрешён недетерминизм — выбор «какой
  инструмент в данном контексте вызвать».

### 2.2 Семь уровней памяти / RAG (V2)

| Level | What it is | When to graduate |
|---|---|---|
| 1. Automemory | `~/.claude/projects/*/memory/*.md`, создаётся агентом сам | когда поняли, что «бесконтрольная память» засоряет контекст |
| 2. `CLAUDE.md` | Один файл с правилами проекта | когда он распухает и становится «bloated rulebook» |
| 3. State files | Несколько MD — `project.md`, `requirements.md`, `roadmap.md`, `state.md`; `CLAUDE.md` превращается в индекс | когда нужна переиспользуемость между проектами |
| 4. Obsidian vault | Vault с `raw/`, `wiki/`, index-файлами; Карпати-style knowledge-base | «enough for 80%+ use cases». Масштаб — до нескольких тысяч документов |
| 5. Naive RAG | Chunking → embeddings → vector DB → similarity search | когда нужны связи между документами / масштаб ≫ 10⁴ |
| 6. Graph RAG | Entity + relationship extraction (LightRAG, Microsoft GraphRAG) | когда нужен multimodal ingest |
| 7. Agentic multimodal RAG | Images / scanned PDFs / videos (RAG-Anything, Gemini embedding-2), data-ingestion pipelines | это потолок. В 2026 — бурно меняется. |

Ключевой тезис: **«context rot» реален**. Большой контекст ≠ хороший ответ; с
ростом заполнения окна качество падает. Следствие — активная гигиена контекста
важнее размера окна.

### 2.3 Hermes Agent как референс self-improvement (V1)

Пять типов памяти, которые у них явно выделены:

1. **Built-in prompt memory** — `memories/memory.md` (про проект) +
   `memories/user.md` (про пользователя).
2. **Session memory** — SQLite (`state.db` / FTS5); хранятся все сессии, можно
   делать прямой SQL.
3. **Procedural memory** — `skills/`. Автосоздаётся, когда агент отловил
   «повторяющуюся сложную последовательность» (у них — 3+ tool-вызовов
   подряд).
4. **Daily structured log** — `memories/2026/…` с саммари по дням.
5. **External memory providers** — Mem0, Honcho, hyperbolic, Zep, Supermemory,
   RememberDB, ByteRover и т. п. (модульный слой).

Учебные моменты:

- **Learning loop**: «after every task → automatic retrospective → if a pattern
  repeats ≥3 times, spawn a skill → refine from user feedback».
- **Security modes**: `manual` (default, prompt on dangerous ops), `smart`
  (LLM-based approval), `off/YOLO` (bypass). Плюс allow-list команд.
- **Sub-agents** через `delegate_task`; изолированные окружения; merge
  результатов после.
- **Public API gateway** — `hermes gateway` поднимает OpenAI-compatible
  endpoint на `:8642`; авторизация через `API_SERVER_KEY`. Это переводит
  агента из «мой ноутбук» в «сервис, в который можно ходить из любого клиента»
  без написания кастомного API.

### 2.4 Harness engineering (V5, V2, фоном V1)

Harness — каркас, который мы надеваем на LLM. Четыре первоклассных сущности:

- **Rules** (`CLAUDE.md` / `AGENTS.md`) — что делать **всегда**.
- **Commands** (slash-commands в Claude Code, `prompts/*.md` у нас) — *как*
  делать повторяющиеся задачи.
- **Hooks** — что должно/не должно произойти до или после действия
  (pre-commit, pre-tool-call, post-test). Самый мощный из четырёх слоёв.
- **Skills** — процедурные артефакты, которые LLM сам обнаруживает и
  сохраняет; они *становятся* частью harness'а со временем.

Почему это важно для SOTA-агента: без явного harness'а «efficiency
degrades over time because people never clear their context» (V2) и «agents
pick the wrong tools, drift from the user's goal, burn tokens in loops» (V3).
Harness — противодействие обоим.

### 2.5 Вторичные, но полезные идеи

- **«AskUserQuestion» tool** (Claude Code 0.21, упомянут в расшифровке блога к
  V2): агент может сам приостановиться и задать 1–4 уточняющих вопроса.
  Снижает hallucinations на ранних шагах плана. Аналог есть в Devin playbook —
  «ask a clarifying question, but only alongside a concrete action».
- **Plan Mode + CLAUDE.md** как «две привычки, которые уже резко поднимают
  качество» — подтверждается в V2 и в блоге к видео.
- **Rerankers** как дешёвый способ поднять naive-RAG точность без переезда на
  graph RAG.
- **«Rag vs textual LLM — 1200× по токенам/latency»** (V2, данные 2025 года).
  Сам Chase подчёркивает, что разрыв сократился; но order-of-magnitude
  выигрыш остался, и это аргумент вводить RAG *даже если* Obsidian «работает
  достаточно хорошо».
- **Исполнитель vs супервайзер** (V2, Level 5–6 по оригинальной разбивке;
  также в V5): переводить себя из роли «пишу промпт каждый раз» в роль
  «смотрю за агентом, который сам выполняет циклы».

---

## 3. Ranking matrix

Ранжирование сделано по двум осям:

- **Applicability** — насколько концепт *применим* к First-Agent на фазе v0.1
  (1 = чисто теория, 5 = надо закладывать в первый же модуль).
- **Usefulness for SOTA-tier** — насколько он необходим, чтобы агент можно
  было всерьёз называть «state-of-the-art» в 2026 (1 = nice-to-have, 5 =
  без него агент не дотягивает).

| Rank | Concept | Source | Applic. (v0.1) | SOTA-tier | Notes |
|---:|---|---|:---:|:---:|---|
| 1 | Deterministic shell, probabilistic core | V4, V2 | 5 | 5 | Базовый принцип архитектуры. Фиксирует `docs/architecture.md §П1`. |
| 2 | Tool use (structured JSON boundary) | V3, V1 | 5 | 5 | Первый Execution-инструмент. Без него нет агента. |
| 3 | Feedback loop (test/lint/typecheck после действий) | V3 (Planning), ∞ | 5 | 5 | Уже зафиксировано в `architecture.md §П1`; подтверждено всеми. |
| 4 | Planning: decompose → execute → reflect | V3 | 5 | 5 | Закрывает Шаг 3 исследования (ReAct vs Plan-and-Execute). |
| 5 | `CLAUDE.md` / `AGENTS.md` как индекс, а не как правила | V2 (Level 2→3) | 5 | 4 | У нас уже есть `AGENTS.md`, но им пользуются как свалкой. Нужен пересмотр: «индекс, не свод правил». |
| 6 | Procedural memory / skills (самоизвлечение из 3+ успехов) | V1 | 4 | 5 | Отдельный ADR; даёт self-improvement. |
| 7 | Harness: rules + commands + hooks | V5, V1 | 4 | 5 | Hooks особенно: pre-commit, pre-tool-call, post-tool-call. |
| 8 | Session memory в SQLite + history query | V1 | 4 | 4 | Дёшево, сразу решает «агент забывает о прошлой сессии». |
| 9 | Context hygiene / `/clear` как ритуал | V2 | 5 | 4 | Это *операционная дисциплина*, не код; нужно прописать в `docs/workflow.md`. |
| 10 | Plan Mode (Shift+Tab×2) как шаблон для задач | V2 | 4 | 4 | Превращается в наш `prompts/plan-mode.md`. |
| 11 | AskUserQuestion-style tool (1–4 clarifying qs) | V2 | 4 | 4 | Ещё один инструмент Execution-слоя. Снижает hallucinations. |
| 12 | Sub-agents с изоляцией + merge | V1, V3 | 3 | 5 | В v0.1 не нужно; но архитектуру закладываем так, чтобы не переписывать. |
| 13 | State-file architecture (`project/requirements/roadmap/state.md`) | V2 (Level 3) | 4 | 3 | Почти бесплатно, даёт «контекст поверх чата». |
| 14 | Obsidian-style knowledge vault (Карпати-паттерн) | V2 (Level 4) | 3 | 4 | Для knowledge-heavy задач — 80/20-победа. |
| 15 | External memory providers (Mem0/Honcho/Zep) как pluggable слой | V1 | 3 | 4 | Абстракция важнее конкретного провайдера. |
| 16 | Security modes (manual / smart / YOLO) + allow-list | V1 | 3 | 4 | С самого начала закладывать ≠ chat-бот с shell-доступом. |
| 17 | OpenAI-compatible gateway на агенте | V1 | 3 | 3 | Позволяет использовать агента из любого клиента. |
| 18 | Naive / Graph / Agentic RAG | V2 (Level 5–7) | 2 | 4 | Вводим на следующей итерации, когда вырастет knowledge base. |
| 19 | Rerankers поверх naive RAG | V2 | 2 | 3 | Дешёвый подъём точности без graph-RAG. |
| 20 | Multimodal ingest (images/video) — Gemini embedding-2, RAG-Anything | V2 (Level 7) | 1 | 3 | За горизонтом v0.1. |
| 21 | Исполнитель → супервайзер (role-shift) | V2, V5 | 4 | 3 | Меняется то, *как мы работаем с агентом*. Прописываем в `workflow.md`. |

### Как читать матрицу

- **9–10 по сумме** — включить в Шаг 2–5 (до ADR).
- **7–8** — candidate для ADR после v0.1, но архитектуру не ломать
  (оставить «hook» для них).
- **≤6** — в `knowledge/research/_deferred.md`.

---

## 4. Cross-cuts (чего в видео нет и что стоит добавить руками)

Видео — не полная картина. Что явно *не раскрыто*, но нужно для SOTA-агента:

- **Evaluation.** Ни одно из пяти видео серьёзно не говорит о eval-suite,
  regression set, per-commit scoring. Для First-Agent это Шаг 0 (см. README,
  «собрать eval-набор из 10–30 кейсов»).
- **Cost accounting.** Упоминается вскользь («usage fills up»). Нужен
  собственный «token budget per task» и телеметрия.
- **Safety beyond allow-lists.** Security в V1 — про shell, не про
  данные/prompt-injection. Ссылка на внешние материалы (OWASP LLM Top-10,
  Anthropic system card) — обязательна до прод-ready.
- **Версионирование skills/prompts.** В V1 skill-файлы редактируются; но про
  миграции / обратную совместимость ничего. Для нас — завести
  `prompts/CHANGELOG.md` по факту появления второго skill'а.

---

## 5. Implications for First-Agent

Переложим высокоранжированные концепты на наши артефакты.

### 5.1 Обновления в существующих документах

- [`docs/architecture.md`](../../docs/architecture.md):
  - Явно назвать принцип **Deterministic shell / Probabilistic core** (ранг 1)
    новым пунктом «П0» — *до* feedback loop.
  - В §«Архитектура памяти» добавить строку **Procedural memory: `SKILL.md`,
    автосоздаётся при повторении паттерна ≥N раз** (N — параметр ADR).
  - В §«Дизайн инструментов» дописать два принципа:
    - *Structured-request boundary* — инструмент возвращает и принимает только
      строго типизированные payload'ы.
    - *AskUserQuestion-класс* — отдельный инструмент эскалации, не просто
      «retry с ошибкой».
- [`docs/workflow.md`](../../docs/workflow.md):
  - Добавить подфазу «context hygiene» в фазу R — явное `/clear` / `/compact`
    после завершения исследовательской сессии.
  - В фазу S добавить «scaffold harness» — rules + commands + hooks до
    первого модуля.
- [`AGENTS.md`](../../AGENTS.md):
  - Переписать так, чтобы он работал как *индекс* (V2, Level 3), а не как
    «bloated rulebook»: каждый раздел — одна строка + ссылка.

### 5.2 Новые артефакты

- **ADR-0001 — Orchestration style.** Кандидаты: ReAct / Plan-and-Execute /
  hand-rolled state machine. Рекомендация по итогам видео: **Plan-and-Execute
  с детерминированным outer-loop и ReAct-подобным inner-step**. Обосновать в
  ADR.
- **ADR-0002 — Memory layers.** Выбрать стартовый набор: session (in-proc) +
  persistent (JSON / SQLite?) + procedural (SKILL.md). Episodic — отложить.
- **ADR-0003 — Skill-extraction policy.** Когда агенту разрешено предложить
  новый skill, кто его ревьюит, как хранить.
- **`knowledge/research/harness-design.md`** — детальный разбор rules /
  commands / hooks; какие hooks должны быть с нулевого дня (хотя бы
  `pre-commit` и `post-test`).
- **`knowledge/research/eval-set.md`** — 10–30 тест-кейсов, чтобы не
  регрессировать. Без этого остальные улучшения нельзя измерить.

### 5.3 Тулинг

- Настроить **pre-commit** (hook из §2.4). Минимум: `ruff check`,
  `ruff format`, простая валидация markdown-ссылок (например,
  [`lychee`](https://github.com/lycheeverse/lychee)). Это же — первый реальный
  hook harness'а.
- Ввести правило: «каждый skill-файл — помечен `owner:`,
  `last-verified-on:`, ссылка на сессию, где он был извлечён».

---

## 6. Open questions (для следующих сессий)

1. **Plan-and-Execute vs ReAct** — нужен ли hybrid (подтверждается V2: Level
   5 «executor → supervisor»)? Или мы начинаем с чистой plan-exec, а ReAct —
   внутри одного шага?
2. **Где живут skills** — в репо (`knowledge/skills/`) или в stateful storage
   вне репо (Hermes-style `state.db`)? Пока склоняюсь к «в репо» (диффится,
   ревьюится), но тогда нужен механизм «горячего» обновления.
3. **Объём harness'а до первого модуля.** V5 говорит «hooks — самый мощный
   слой». Вопрос: что считать минимальным harness'ом, чтобы *не* парализовать
   разработку.
4. **Eval набор.** Какие *классы задач* покрываем в первых 10 кейсах? (см.
   README §4, Шаг 1 — определить задачу.)

---

## Sources

- V1. Devs Kingdom — *Hermes Agent: Self-Improving Strategy Explained* (18:34,
  2026-04-21). <https://www.youtube.com/watch?v=qUqcLNcP5Tc>
- V2. Chase AI — *The 7 Levels of Claude Code & RAG* (45:58, 2026-04-14).
  <https://www.youtube.com/watch?v=kQu5pWKS8GA>
- V3. TechWhistle — *4 Design Patterns Behind Every AI Agent* (9:38,
  2026-04-11). <https://www.youtube.com/watch?v=pIoKdpsuODg>
- V4. *The Core of an AI Agent Is Determinism* (~7:30).
  <https://www.youtube.com/watch?v=fiysocjyAho>
- V5. *Claude Design & the Harness Question: What Agentic Workflows Really
  Need* (~7:30). <https://www.youtube.com/watch?v=n18V4zlIWOo>

Вторичные источники, на которые ссылаются спикеры и которые стоит пройти
следующими (prioritized by relevance):

- Anthropic — *Building effective agents*.
  <https://docs.anthropic.com/en/docs/build-with-claude/agent>
- Andrew Ng — *Agentic AI Design Patterns* (DeepLearning.AI).
  <https://learn.deeplearning.ai/courses/agentic-ai>
- Carpathy — LLM knowledge-base / Obsidian pattern (ссылки в описании V2).
- LightRAG. <https://github.com/HKUDS/LightRAG>
- RAG-Anything (multimodal, упомянут в V2).
- Hermes Agent. <https://github.com/nousresearch/hermes-agent>
- Towards AI — *Deterministic Shells, Probabilistic Cores* (статейный
  вариант V4).
  <https://pub.towardsai.net/deterministic-shells-probabilistic-cores-the-architecture-pattern-behind-every-reliable-agent-a5de28e36bd0>

---

*Keep this note under 250 lines of substance. Если концепт разрастается — выделяем
в отдельный `knowledge/research/<slug>.md` и оставляем здесь ссылку.*
