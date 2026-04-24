# Research — Agent Roles: graphify, CAMEL, и research-backed паттерны

> **Статус:** research note, 2026-04-23. Написан под **текущий этап First-Agent —
> «создать роли агента»** ([README §4.2](../../README.md#4-план-исследования-перед-тем-как-писать-код)). Разбирает два референс-репозитория
> (graphify, CAMEL) плюс более широкий ландшафт публикаций о multi-agent /
> role-playing LLM-системах, и выдаёт явные рекомендации «что брать в v0.1, что
> попробовать позже, что не брать».
>
> **Промпты здесь НЕ пишутся** — это сознательно, по запросу. Документ собирает
> *структурные* идеи, которые войдут в будущий промпт-пакет, но оставляет
> написание самих текстов на следующий этап.
>
> Связь с уже существующими заметками:
> - [`agent-video-research.md`](./agent-video-research.md) — пять YouTube-видео
>   о паттернах агентов; этот документ опирается на его словарь
>   (tool use / RAG / planning / multi-agent, harness, determinism).
> - [`docs/architecture.md`](../../docs/architecture.md) — трёхслойная модель
>   First-Agent (Interface / Cognitive / Execution). Роли из §5 ниже ложатся в
>   Cognitive слой.

## 0. TL;DR

1. **graphify** — это *не LLM-агент*, а **детерминированный Python-пайплайн,
   которым управляет host-агент** (Claude Code, Codex, Aider и т.п.) по
   инструкции в `skill.md`. `skill.md` играет роль «системного промпта для
   конкретного pipeline», а Python делает всё, что можно сделать без LLM
   (AST, кластеризация, экспорт). Для нас это **референс инженерной
   дисциплины**, а не источник ролей.
2. **CAMEL** — и научный проект (paper [2303.17760][p-camel]), и framework —
   построен вокруг **role-playing / inception prompting**: две роли
   (User-как-instructor и Assistant-как-executor) общаются по жёсткому
   протоколу для решения задачи. Это **эталонный источник ролей и
   их структуры** — мы берём и паттерн двух ролей, и 7-элементную анатомию
   role-prompt, и семейство «обслуживающих» агентов (task-specify, task-plan,
   critic, role-assignment).
3. **Более широкий ландшафт** (ChatDev, MetaGPT, AutoGen, CrewAI, LangGraph,
   ReAct, Reflexion, Self-Refine, Multi-Agent Debate, Tree of Thoughts,
   Constitutional AI, Generative Agents, Voyager) даёт несколько
   **research-backed** надстроек над role-playing. В First-Agent v0.1 нам стоит
   заложить только фундамент (roles + critic + reflexion), остальное — в
   бэклог.
4. Конкретный **набор ролей для v0.1** — §[5.1](#51-рекомендованный-минимальный-набор-ролей-для-v01).
   Формат записи роли — §[5.2](#52-скелет-records-роли).
   Структурные требования к будущим system-prompts — §[6](#6-идеи-не-черновики-для-дизайна-system-prompts).

---

## 1. Что исследовано

| # | Репозиторий | Что взяли для анализа |
|---|---|---|
| R1 | [safishamsi/graphify][r-graphify] | `skill.md` (1377 стр.), `skill-*.md` (10 host-адаптеров), модули `detect/extract/build/cluster/analyze/report/export`, `ARCHITECTURE.md`, `AGENTS.md` |
| R2 | [camel-ai/camel][r-camel] | `agents/` (11 типов агентов), `prompts/` (9 таск-специфичных prompt-словарей), `societies/role_playing.py`, `societies/workforce/` (prompts + workforce.py), `generators.py` |

Плюс теоретическая рамка из 12 публикаций / проектов — список в
§[Sources](#sources). Отбор работ — по одному критерию: либо они цитируются
CAMEL / graphify напрямую, либо это публикации, на которые ссылается индустрия
при проектировании ролей (AutoGen, MetaGPT, ChatDev, Reflexion и пр.).

---

## 2. graphify — глубокий разбор

### 2.1. Что это на самом деле

На обложке написано *«AI coding assistant skill»*. По коду это —
**Python-библиотека + один большой промпт-документ** (`skill.md`), который
пользователь вызывает командой `/graphify` в Claude Code (и совместимых
хостах: Codex, Aider, OpenCode, Copilot CLI, Cursor, Droid, Trae, Kiro, VS
Code Copilot Chat, Windows). Pipeline:

```text
detect() → extract() → build_graph() → cluster() → analyze() → report() → export()
```

— каждая стадия это чистая функция в своём модуле, общение через `dict` и
`networkx.Graph`, side-effects ограничены папкой `graphify-out/`
([ARCHITECTURE.md][r-graphify-arch]).

**Ключевое наблюдение:** сам граф, god-nodes, кластеризация — это
*детерминированный код*, а не LLM. LLM (то есть host-агент) вызывается точечно:

- **Шаг 2.5:** host сам сочиняет Whisper-prompt для транскрибации видео —
  по god-nodes из предыдущего detect-этапа. Это интересный reflexive шаг:
  «LLM, ты уже знаешь про этот корпус; напиши себе domain hint, с которым
  Whisper точнее распознает термины».
- **Шаг 3 (Part B):** семантическая экстракция концептов из тех файлов,
  которые tree-sitter не разбирает.
- **Шаг 5:** host читает `graphify-out/.graphify_analysis.json` и даёт
  каждой community 2–5-словное человекочитаемое имя.

Всё остальное — детерминировано.

### 2.2. Pattern: deterministic core + skill-driven host agent

Архитектурно graphify — **идеальный пример разделения компетенций**:

| Слой | Кто | Что делает |
|---|---|---|
| Execution (код) | Python | AST, графы, кластеризация, экспорт, кэш, безопасность |
| Cognitive (host-агент по skill.md) | Claude / Codex / Aider | Читает/пишет файлы, вызывает bash-блоки, где Python не даст ответа — думает (label communities, choose Whisper prompt) |
| Interface | slash-команда `/graphify` | Единая точка входа |

Это ровно та трёхслойка, к которой мы сами пришли в
[`docs/architecture.md`][fa-arch]. graphify — эмпирическое подтверждение, что
она работает.

Важные следствия для First-Agent:

- **Никогда не проси LLM делать то, что может деревянный код.** `extract.py`
  — 3440 строк pure Python по языкам (tree-sitter). Попытка сделать это
  промптом — дороже, медленнее, и теряет калибровку.
- **LLM — для семантики и неоднозначности.** Community labels, surprise
  ranking, Whisper domain hint — места, где код плохо справляется.
- **Audit trail — first-class.** См. §2.4.

### 2.3. skill.md как system prompt

`skill.md` — это не документация, это **runtime-инструкция** для host-агента,
которая загружается в его контекст при вызове `/graphify`. По структуре:

1. **YAML front-matter** (`name`, `description`, `trigger`) — маркирует skill
   для host'а.
2. **Usage cheat-sheet** — перечень флагов; задаёт скоуп.
3. **Шаги по номерам** (Step 0..11), *идущие жёстко по порядку*. Текст
   буквально говорит «Do not skip steps».
4. **Bash-блоки** со строгим форматом: вход (кэш-файл), выход (кэш-файл),
   проверка exit-code. Между блоками host не должен импровизировать.
5. **«Презентационные» правила:** *«Do NOT cat or print the JSON — read it
   silently and present a clean summary»*. Это уже стиль-гайд для
   пользователя.
6. **Контракты ошибок:** «If this step prints `ERROR: Graph is empty`, stop
   and tell the user what happened — do not proceed to labeling or
   visualization».

Этот формат — **detailed procedural prompt** с эксплицитной state machine.
Мы можем заимствовать саму концепцию: **длинный, нумерованный, детерминистский
runbook как system-prompt для оркестратора**, отличный от короткого
personality-style prompt для исполнителя.

### 2.4. «Honest audit trail» — паттерн маркировки

Каждая связь в графе получает confidence-ярлык:

| Label | Meaning |
|---|---|
| `EXTRACTED` | Явно прописано в источнике (import, call) |
| `INFERRED` | Разумный вывод (call-graph second pass, co-occurrence) |
| `AMBIGUOUS` | Неуверенно — флагается для человека в `GRAPH_REPORT.md` |

Это **калибровочный примитив**. Для нас он значит: **любой агент, который
генерирует «знание», должен маркировать степень уверенности источника**.
Применимо не только к графам, а ко всему, что агент запоминает / пишет в
память / докладывает пользователю.

Аналог в нашей [архитектуре][fa-arch]: в §5.2 (Cognitive layer) планируется
шаг *Reflect*. Ярлыки EXTRACTED/INFERRED/AMBIGUOUS — готовый словарь для
выходных артефактов Reflect'а.

### 2.5. Host-specific skill adapters

В `graphify/` лежит не один `skill.md`, а одиннадцать:

```text
skill.md          # Claude Code (canonical)
skill-aider.md    skill-claw.md     skill-codex.md
skill-copilot.md  skill-droid.md    skill-kiro.md
skill-opencode.md skill-trae.md     skill-vscode.md
skill-windows.md
```

Задача одна, промпт один — но **текст адаптируется под идиосинкразии
каждого host-агента**: у кого-то нет bash по умолчанию, кто-то любит
`apply_patch`, у кого-то свои лимиты токенов, у кого-то другой синтаксис
slash-команд. То есть: **один job — много role-адаптеров**, по одному на
«окружение исполнения».

Для First-Agent это хинт: если мы позже захотим работать как в CLI, так и в
Claude Code / Devin — **роль (job) надо отделить от адаптера (environment
shim)**. Пока это не приоритет, но знать про паттерн полезно.

### 2.6. Что из graphify берём явно

| Идея | Где применим в First-Agent |
|---|---|
| Deterministic core / LLM on demand | Все модули v0.1 пишутся как чистый Python; LLM вызывается только там, где нужна семантика |
| Skill-style runbook как system-prompt оркестратора | Будущая роль *Orchestrator / Executor* получит длинный нумерованный промпт в стиле `skill.md` |
| Confidence labels (EXTRACTED/INFERRED/AMBIGUOUS) | Любой артефакт памяти / ответ пользователю содержит confidence-тэг |
| Job ≠ Role adapter | Роли храним абстрактно; адаптеры под конкретные runtime'ы (Claude Code, OpenAI function-calling, локальный CLI) добавляем позже |
| Strict input/output contracts между шагами | Наш цикл *Plan → Act → Observe → Reflect* требует типизированных артефактов между шагами |

### 2.7. Чего в graphify **нет**, и почему это не аргумент против него

- Нет **ролей**. graphify — single-agent с host-drive. Для «ролей агента» это
  не референс — это референс *противоположного* подхода: много деталей
  процесса при одной роли. Полезно видеть оба полюса, чтобы наш дизайн был
  осознанным.
- Нет **памяти**. Кэш SHA256 — это не память агента, это мемоизация
  pipeline-шагов.
- Нет **reflexion / self-improve**. skill-инструкция фиксирована; агент не
  «учится» от запуска к запуску.

---

## 3. CAMEL — глубокий разбор

### 3.1. Контекст

CAMEL — проект, выросший из одноимённой paper (Li et al., NeurIPS 2023,
[2303.17760][p-camel]). Цель — **изучать scaling laws агентов**: что
происходит, когда два LLM-агента «играют роли» и решают задачу вместе.
Framework реализует это и накопил 11 типов агентов, 9 таск-специфичных
prompt-словарей, отдельный *workforce* — иерархический координатор. Для нас
это **лучший публично доступный референс по архитектуре ролей**.

### 3.2. Role-playing / Inception prompting — ядро

Канонический сетап (см. `camel/societies/role_playing.py` + `examples/ai_society/role_playing.py`):

```text
Человек даёт высокоуровневую task ("Develop a trading bot for the stock market")
      │
      ▼
TaskSpecifyAgent ─── конкретизирует task до одного исполнимого абзаца
      │
      ▼
(опц.) TaskPlannerAgent ─── разбивает на подзадачи
      │
      ▼
┌────────────────┐  turn-by-turn      ┌────────────────────┐
│   AI User      │ ────────────────►  │   AI Assistant     │
│ ("Stock Trader")│                    │ ("Python Programmer")│
│ [USER_PROMPT]  │  ◄────────────────  │ [ASSISTANT_PROMPT] │
└────────────────┘                    └────────────────────┘
      │                                         │
      ▼                                         ▼
(опц.) CriticAgent — выбирает лучший вариант из предложений
      │
      ▼
Завершение: USER шлёт "<CAMEL_TASK_DONE>"
```

**Принципиально важные точки:**

- **Обе роли — LLM.** «User» здесь это не человек, а *второй LLM, играющий
  роль пользователя-эксперта*.
- **Протокол шагов**: USER даёт ровно одну *инструкцию с опциональным
  инпутом*; ASSISTANT отвечает ровно одним *Solution*. Никаких вопросов от
  ASSISTANT — только решения или явный отказ.
- **Inception prompting** — одной фразой в системном промпте
  (`Never forget you are a {role}. Never flip roles!`) модель удерживается в
  своей роли на протяжении всего диалога.
- **Явное условие остановки:** строка-маркер `<CAMEL_TASK_DONE>` из USER'а
  завершает цикл.

### 3.3. Анатомия CAMEL role-prompt (7 элементов)

Разбор `ASSISTANT_PROMPT` и `USER_PROMPT` из `camel/prompts/ai_society.py`
даёт **повторяющийся 7-элементный каркас** любого role-prompt:

| # | Элемент | Пример из CAMEL | Зачем |
|---|---|---|---|
| 1 | **Role anchor** | `Never forget you are a {role} and I am a {other_role}. Never flip roles! Never instruct me!` | Фиксирует идентичность, блокирует «слив» в помощника-по-умолчанию |
| 2 | **Shared goal clause** | `We share a common interest in collaborating to successfully complete a task.` | Кооперативная рамка — без неё LLM часто уходит в адверсариальность |
| 3 | **Task anchor** | `Here is the task: {task}. Never forget our task!` | Противовес context-drift на длинных диалогах |
| 4 | **Turn-taking contract** | `I must give you one instruction at a time.` | Уменьшает галлюцинации batched инструкций |
| 5 | **Output schema** | `Always start with "Solution:" ... Always end with "Next request."` | Делает вывод parseable без специальной функции-калла |
| 6 | **Refusal clause** | `You must decline my instruction honestly if you cannot perform...` | Разрешает «нет» — без этого модель выдумывает |
| 7 | **Termination token** | `When the task is completed, you must only reply with <CAMEL_TASK_DONE>.` | Детерминистская точка выхода цикла |

Это не «идеальный промпт» — это **скелет**, куда подставляются детали
конкретной роли. **Именно этот скелет мы должны взять как стартовую точку
для дизайна First-Agent's system-prompts** (§[6](#6-идеи-не-черновики-для-дизайна-system-prompts)).

### 3.4. Специализированные подварианты этого скелета

CAMEL даёт ещё 4 производных промпт-словаря — все наследуют скелет из §3.3,
но подмешивают свои элементы:

- **`code.py` → `CodePromptTemplateDict`** — добавляет `{language}` и требует
  «`<YOUR_SOLUTION>` must contain {language} code»; тот же 7-элементный
  каркас, но Assistant «Computer Programmer», а User — «person working in
  {domain}».
- **`role_description_prompt_template.py`** — перед скелетом вставляет блок
  `===== ROLES WITH DESCRIPTION =====`, где для каждой роли явно прописаны
  *«competencies, characteristics, duties and workflows»*. Это даёт
  гораздо более «жирные» роли, чем просто имя.
- **`misalignment.py`** — тот же скелет + «DAN»-надстройка для red-team
  исследований. Держим как пример *осторожно — так можно, и тогда надо
  ставить guardrails*.
- **`persona_hub.py`** — минималистичные шаблоны `TEXT_TO_PERSONA` и
  `PERSONA_TO_PERSONA` для генерации personas из текста и graph-walking по
  ним (см. статью Persona Hub, [2406.20094][p-persona-hub]).

### 3.5. Обслуживающие агенты вокруг role-playing

CAMEL показывает, что *два role-playing агента — это только ядро*. Вокруг
строится целый ансамбль:

| Агент | Файл | Что делает | Когда полезен для нас |
|---|---|---|---|
| `TaskSpecifyAgent` | `agents/task_agent.py` | «Вот общая задача. Конкретизируй до ≤ N слов» | Перед стартом сессии, чтобы превратить расплывчатое пользовательское «помоги мне…» в чёткий task-prompt |
| `TaskPlannerAgent` | `agents/task_agent.py` | «Divide this task into subtasks» | Когда задача явно многошаговая; ответ — пронумерованный список |
| `TaskCreationAgent` | `agents/task_agent.py` | BabyAGI-стиль: создаёт новые задачи по мере прогресса | Отложить — это уже autonomy, а нам нужно сначала стабильное ядро |
| `TaskPrioritizationAgent` | `agents/task_agent.py` | Сортирует очередь задач | То же — позже |
| `RoleAssignmentAgent` | `agents/role_assignment_agent.py` | По task'у генерирует `num_roles` экспертов и их описания | Отличный кандидат для «meta»-роли First-Agent'а |
| `CriticAgent` | `agents/critic_agent.py` | Выбирает один вариант из предложений по критериям | Essential для Reflect-шага |
| `EmbodiedAgent` | `agents/embodied_agent.py` | Роль с доступом к действиям в симулируемой среде | Не нужен в v0.1 |
| `KnowledgeGraphAgent` | `agents/knowledge_graph_agent.py` | Строит граф знаний из текста | Пересечение с graphify — см. §4 |
| `SearchAgent` | `agents/search_agent.py` | Тулинговый агент для web-search | Позже, когда появится retrieval |
| `RepoAgent` | `agents/repo_agent.py` | Навигация по репо | Позже |
| `MCPAgent` | `agents/mcp_agent.py` | Тонкий клиент к MCP-серверам | Позже, когда появится MCP-экосистема |

**`RoleAssignmentAgent`** заслуживает отдельного взгляда. Его промпт (строки
86–96 в `role_assignment_agent.py`):

```text
You are a role assignment agent, and you're in charge of recruiting
{num_roles} experts for the following task.
==== TASK =====
{task}

Identify the domain experts you'd recruit and detail their associated
competencies, characteristics, duties and workflows to complete the task.
Your answer MUST adhere to the format of ANSWER PROMPT, and ONLY answer the BLANKs.
===== ANSWER PROMPT =====
Domain expert 1: <BLANK>
Associated competencies, characteristics, duties and workflows: <BLANK>. End.
Domain expert 2: <BLANK>
...
```

Это **декларативный roster-builder**. Для First-Agent это значит: мы можем
(а) хранить заранее подготовленный roster ролей в YAML, и (б) при появлении
новой нетипичной задачи — вызвать meta-агента `RoleAssignmentAgent-like`,
чтобы он собрал новый roster под задачу, который потом можно либо выполнить
ad-hoc, либо закрепить в бэклоге ролей.

### 3.6. CriticAgent

Промпт (`prompts/ai_society.py` строки 109–114):

```text
You are a {critic_role} who teams up with a {user_role} and a {assistant_role}
to solve a task: {task}.
Your job is to select an option from their proposals and provides your
explanations.
Your selection criteria are {criteria}.
You always have to choose an option from the proposals.
```

Ключевые наблюдения:

- Критик — **не генератор** альтернатив, а **селектор**. Это намеренно: он
  не конкурирует с ассистентом, он *выбирает между* предложениями
  ассистента.
- У него **явные `criteria`**. Без них LLM-critic сползает в обобщённые
  похвалы.
- Промпт запрещает «ни одна опция не подходит» (`You always have to
  choose`). Это не всегда то, что нужно — в нашем случае осмысленно
  разрешить «refuse with reasons», но держать в уме, что без такого
  запрета критик может саботировать цикл.

Это ровно тот примитив, который даёт шаг **Reflect** в нашей [трёхслойке][fa-arch]
— но с двумя оговорками: (1) критик должен видеть `criteria`, (2) мы,
скорее всего, разрешаем ему «none with reasons» с тем условием, что он
тогда обязан произвести *structured rejection*, а не пустоту.

### 3.7. Workforce — иерархический координатор

`camel/societies/workforce/` — это «следующий уровень»: не два агента, а
**один координатор + N workers**. Архитектура видна в `prompts.py`:

- **`CREATE_NODE_PROMPT`** — когда приходит категория задач, которую ни
  один worker не покрывает, координатор *сам создаёт нового worker-агента*
  с заданным role / system-message / description.
- **`ASSIGN_TASK_PROMPT`** — для каждой задачи выбирает подходящего
  worker'а и *считает зависимости между задачами* (DAG).
- **`TASK_DECOMPOSE_PROMPT`** — превращает сложную задачу в ряд
  `<task>...</task>` XML-элементов, с шестью **design principles**
  (self-contained, clear deliverables, workflow completion, aggressive
  parallelization, subtask granularity, skill-aware).
- **`TASK_ANALYSIS_PROMPT`** — пост-хок анализ качества. Если
  `quality_score < 60`, координатор выбирает стратегию восстановления:
  **retry / replan / reassign / decompose** (сам набор тоже декларативный).
- **`ROLEPLAY_SUMMARIZE_PROMPT`** — когда worker-роль это пара
  role-playing agents, финальный вывод — саммари их разговора.

Для нас это **целевая архитектура v0.2+**, а не v0.1. Но она даёт важные
готовые концепты:

- **Recovery strategies** (retry/replan/reassign/decompose) — это уже
  типология восстановления, которую в v0.1 мы введём даже с одним worker'ом.
- **Skill-aware decomposition rule:** «если задача явно требует skill'а
  — НЕ декомпозируй её, skill сам знает workflow». Этот же принцип
  применим к любым pre-built tool chains в нашей системе.
- **Task decompose design principles** — шесть правил из §219–226 файла
  `workforce/prompts.py` можно **слово в слово** взять в наш
  `decomposer`-роль, когда он появится.

### 3.8. Генерация системного сообщения: `SystemMessageGenerator`

`camel/generators.py` формализует **как рождается системный промпт роли**:

1. Берётся `TaskType` (`AI_SOCIETY`, `CODE`, `MISALIGNMENT`, …).
2. `PromptTemplateGenerator().get_system_prompt(task_type, role_type)` → шаблон.
3. Шаблон заполняется словарём `sys_msg_meta_dict` (`role_name`, `task`,
   `domain`, …).
4. Результат идёт как `system` сообщение в `ChatAgent`.

Итог: **системный промпт — не статическая строка, а функция от task-типа
и мета-словаря роли**. Для First-Agent это прямой гайд:

- Не хранить промпты как единый `role.md` — хранить как **шаблон + метадата**.
- Один template для «двух ролей, выполняющих задачу совместно» можно
  переиспользовать для десятка конкретных пар.
- Мета-ключи (`role_name`, `task`, `domain`, `criteria`, …) — это наш
  **контракт между конфигом роли и её runtime-контекстом**.

### 3.9. Что из CAMEL берём явно

| Идея | Куда в First-Agent |
|---|---|
| Dyad User/Assistant (inception prompting) | Основной паттерн v0.1, когда задача требует «напарника-заказчика» |
| 7-элементный каркас role-prompt | Template для всех наших system-prompts |
| Separate `TaskSpecifyAgent` | Обязательный первый шаг в Planning; не смешивать со стратегическим планом |
| `RoleAssignmentAgent` | Meta-роль для ad-hoc задач, когда готового roster'а не хватает |
| `CriticAgent` с явными `criteria` | Шаг Reflect. Критерии — конфиг роли, не промпт |
| Termination tokens (`<TASK_DONE>`) | Механизм выхода из любого агентского цикла |
| System-prompt = template + meta-dict | Формат хранения ролей в `knowledge/roles/` |
| Recovery strategies (retry/replan/reassign/decompose) | Error-handling таксономия в Execution-layer |
| Task decompose design principles | Текст prompt'а для будущего Decomposer-роли |

### 3.10. Что из CAMEL **не** берём в v0.1

- **Workforce / hierarchical multi-agent** — overkill, v0.2+.
- **BabyAGI-стиль `TaskCreationAgent` + `TaskPrioritizationAgent`** — эти
  автономные циклы у нас нарушат принцип «deterministic shell»
  (см. [agent-video-research.md §3][fa-video]); отложить.
- **Persona Hub в полном виде** — мы не генерим датасет, нам достаточно
  5–10 фиксированных ролей.
- **`EmbodiedAgent`** — у нас нет simulated environment.
- **Misalignment/DAN** — читаем как поучительный пример, в продакшн не
  кладём.

### 3.11. Ограничения CAMEL, которые надо учесть

- **Rigidity turn-taking**: формат `Instruction: ... Solution: ...` ломается
  на задачах, где assistant должен уточнять у user'а. CAMEL это *явно
  запрещает* (`You should instruct me not ask me questions`). Для задач с
  плохо специфицированной целью это минус.
- **Stall detection слабый**: зависит от одной строки `<CAMEL_TASK_DONE>`,
  которую USER может забыть прислать. Нужен сторонний
  turn-limiter/timeout (chat_turn_limit в примере — хардкод 50).
- **Нет памяти между ролями** кроме `ChatHistoryMemory`. Для длинных
  workflows нужно добавлять внешнюю память — см. наш [video-research §3 L4–L7][fa-video].
- **Критик — селектор, не генератор.** На задачах, где нужно «дополнить»,
  а не «выбрать», — не тот инструмент.
- **Один LLM на обе роли (часто)**. Это приводит к тому, что User-LLM и
  Assistant-LLM имеют один и тот же prior; *«два разных мнения»* — скорее
  иллюзия, чем реальность. В Multi-Agent Debate (§4.5) это явно
  оспаривается.

---

## 4. Research-backed ландшафт вокруг

Публикации и проекты, которые полезно держать в голове при дизайне ролей.
Каждому — краткая выжимка, *что оно даёт для «создания ролей»*, и вердикт
для First-Agent (*v0.1 / позже / read-only reference*).

### 4.1. CAMEL paper — Li et al., 2023 ([2303.17760][p-camel])

**Идея:** *communicative agents* — два LLM с разными ролями, играющие в
«инструктор + исполнитель», способны автономно решать многоходовые задачи.
Вводит inception prompting. Датасет AI-Society и MATH — первые
синтетические корпусы, сгенерированные именно этой схемой.

**Для ролей:** дал нам §3.3 (7-элементный каркас). Статья также обсуждает
*failure modes*: role flipping, instruction drift, infinite loop,
over-conformity. В promp'те AI Society каждый failure mode закрыт
отдельной строкой. **Это полезнее самого паттерна**: наш чек-лист на любой
role-prompt = «какие failure modes закрыты и чем».

**Вердикт:** v0.1 (базовый референс).

### 4.2. ChatDev — Qian et al., 2023 ([2307.07924][p-chatdev])

**Идея:** виртуальная софтверная компания из ролей *CEO → CTO → Programmer
→ Reviewer → Tester*. Каждая пара соседних ролей проходит «чат» по
waterfall-фазам (design, code, test, document). Вводит **communicative
dehallucination** — роль проверяющего инструктируется искать ошибки
исполнителя.

**Для ролей:** даёт **pipeline шаблон ролей**: не один dyad, а
**каскад dyad'ов по фазам**. Роли фиксированы, сценарий фиксирован,
детерминизм высокий. Противоположность workforce-подходу CAMEL.

**Вердикт:** read-only reference. Для First-Agent слишком специфично
(software company), но приём «фазы → dyad на фазу» пригодится, когда
задача явно каскадная.

### 4.3. MetaGPT — Hong et al., 2023 ([2308.00352][p-metagpt])

**Идея:** SOP-encoded ролевая система. Каждой роли прописан *Standard
Operating Procedure* — жёсткий workflow с типизированными артефактами
(PRD, design docs, code). Роли общаются через structured messages, а не
через свободный чат. Ключевое — **shared message pool + role-specific
subscription** (роль подписывается только на те типы сообщений, которые
её касаются).

**Для ролей:** лучший референс по **структурированным артефактам между
ролями**. У нас в §2.2 `graphify`-pattern требует типизированных входов и
выходов — MetaGPT это обобщает до multi-agent.

**Вердикт:** v0.2 (когда ролей станет > 2).

### 4.4. AutoGen — Wu et al., 2023 ([2308.08155][p-autogen])

**Идея:** универсальный framework для conversable agents, в котором любая
роль — это `ConversableAgent` с конфигом (system message, tools, model).
Поддерживает группы (`GroupChat` + `GroupChatManager`), human-in-the-loop,
nested agents. Введён паттерн *Assistant + UserProxy* — похожий на CAMEL,
но с более гибким контролем.

**Для ролей:** даёт **минималистичное API для роли** (`system_message +
tools + llm_config + is_termination_msg`). Именно эту 4-полевую запись
стоит взять как minimal record роли в First-Agent.

**Вердикт:** v0.1 для структуры record'а роли (§5.2 ниже).

### 4.5. Multi-Agent Debate — Du et al., 2023 ([2305.14325][p-debate])

**Идея:** **несколько** LLM-агентов (не один дважды) независимо
предлагают ответ, потом раунды *debate* — каждый видит ответы остальных и
может скорректировать свой. Улучшает factuality и reasoning на бенчмарках.
Ключевой вывод: *однородные роли на одной модели дают меньше прироста,
чем разнородные роли или разные модели*.

**Для ролей:** подсказывает: **в First-Agent «Critic» и «Executor»
полезно гонять на двух разных моделях** (даже если обе OpenAI — разный
prior из fine-tune). Это research-backed обоснование multi-model-config в
record'е роли.

**Вердикт:** v0.1 (учесть в дизайне record'а), применение — позже.

### 4.6. ReAct — Yao et al., 2022 ([2210.03629][p-react])

**Идея:** чередование *Thought → Action → Observation* внутри одного
агента. Сделало стандартом современный agent loop.

**Для ролей:** ReAct — не роль, а **формат внутреннего цикла роли**.
Любая наша исполняющая роль (Executor, Tool-Using-Agent) должна иметь
ReAct-структуру. В system-prompt это ровно один дополнительный элемент
помимо 7 из §3.3.

**Вердикт:** v0.1 (встроить во все Executor-роли).

### 4.7. Reflexion — Shinn et al., 2023 ([2303.11366][p-reflexion])

**Идея:** агент, провалившись, сам пишет *verbal feedback* о том, почему
провалился, и кладёт его в episodic memory для следующей попытки. Рост
перформанса на HotPotQA, AlfWorld.

**Для ролей:** даёт шаблон **Reflexion-роли** как отдельного агента
(или сабшага): вход — trajectory + failure; выход — structured lesson →
запись в память. **Критически важно для нашего будущего self-improving
loop** (cf. [agent-video-research §3 V1][fa-video]).

**Вердикт:** v0.1 как минимальная роль *Reflector*; полноценный
self-improving — v0.2.

### 4.8. Self-Refine — Madaan et al., 2023 ([2303.17651][p-selfrefine])

**Идея:** один LLM итеративно критикует и улучшает собственный ответ без
внешнего фидбэка. Prompt pair: *feedback prompt* + *refine prompt*.

**Для ролей:** даёт **«дешёвую версию Critic+Refiner внутри одной
роли»**. Если мы не хотим поднимать отдельного Critic-агента, Self-Refine
— минимальный guard-rail.

**Вердикт:** v0.1 как fallback, когда Critic-агент overkill (например,
простые формулировки ответов пользователю).

### 4.9. Tree of Thoughts — Yao et al., 2023 ([2305.10601][p-tot])

**Идея:** вместо линейной CoT — дерево из промежуточных «thoughts» с
branching и backtracking. Роль *evaluator* оценивает каждую ветку.

**Для ролей:** подсказывает роль *Explorer* (генерит ветки) ↔ *Evaluator*
(оценивает). Полезно для задач с большим пространством решений; overkill
для линейных задач.

**Вердикт:** v0.3+ (когда появятся задачи с ветвящимся reasoning'ом).

### 4.10. Constitutional AI — Bai et al., 2022 ([2212.08073][p-caI])

**Идея:** set of written principles («constitution») вместо human-RLHF:
модель сама критикует и исправляет себя по этим принципам.

**Для ролей:** даёт **формат «constitution file»** — список принципов с
примерами good/bad ответов. Это естественная основа для *policy-layer*
наших ролей — базовые ограничения поведения, которые применяются поверх
конкретного role-prompt.

**Вердикт:** v0.1 как короткий (10–15 принципов) constitution-блок,
включаемый во все ролевые system-prompt'ы.

### 4.11. Generative Agents — Park et al., 2023 ([2304.03442][p-genagents])

**Идея:** *Sims-like* симуляция 25 агентов с памятью, рефлексией и
планированием. Три слоя памяти: raw observations → reflections → plans.

**Для ролей:** даёт **трёхслойную модель памяти роли**: краткосрочная
(прошлые action/observation) → среднесрочная (reflections) → долгосрочная
(plans/goals). Совпадает с нашей планировкой в [`docs/architecture.md` §6.1][fa-arch].

**Вердикт:** v0.2 (v0.1 — однослойная ChatHistoryMemory).

### 4.12. Voyager — Wang et al., 2023 ([2305.16291][p-voyager])

**Идея:** агент в Minecraft, который **сам накапливает skill library** —
reusable code snippets, индексируемых по описаниям. Skills всплывают в
контекст через retrieval на следующих задачах. Self-improving без
fine-tuning.

**Для ролей:** показывает, что **skill library — это middle ground между
ролями и инструментами**. Для First-Agent это означает: помимо ролей и
tools завести третий слой — `skills/` (research-backed cookbook-style
заметки для повторяющихся sub-workflows).

**Вердикт:** v0.2+ (сейчас у нас нет даже v0.1 инструментов).

### 4.13. LLM-as-Judge — Zheng et al., 2023 ([2306.05685][p-judge])

**Идея:** использовать LLM как оценщик ответов других LLM; обнаружены
position bias, verbosity bias, self-enhancement bias. Даны методики
mitigation.

**Для ролей:** критично для **дизайна Critic-роли**. Без mitigation наш
Critic будет предпочитать более длинные / более похожие на себя ответы.

**Вердикт:** v0.1 (учесть при промпте Critic'а, хотя сам промпт пишем
позже).

### 4.14. CrewAI, LangGraph, OpenAI Swarm — фреймворки (read-only)

- **CrewAI** — «команды» ролей с хорошей DX. Роли определяются `Agent(role,
  goal, backstory, tools)`. Совпадает структурно с тем, что мы возьмём
  (§5.2). Полезен как эталон UX для конфига.
- **LangGraph** — stateful графы вокруг LangChain; в основе — typed state
  + nodes + edges. Больше про control flow, меньше про роли.
- **OpenAI Swarm** — минималистичный reference impl handoff между ролями
  (rotating control). Хороший пример *role handoff semantics*.

**Вердикт:** read-only reference; свой код пишем сами.

---

## 5. Что это значит для First-Agent прямо сейчас

### 5.1. Рекомендованный минимальный набор ролей для v0.1

На основании §3 и §4, **минимальный roster v0.1 — 4 роли**:

| # | Роль | Назначение | Прототип источника |
|---|---|---|---|
| R1 | **Task Specifier** | Превращает расплывчатый user-ввод в структурированный task-prompt (единый абзац, явный deliverable) | CAMEL `TaskSpecifyAgent` (§3.5) |
| R2 | **Planner** | Разбивает specified task на последовательность шагов с явными артефактами между ними | CAMEL `TaskPlannerAgent` + Workforce `TASK_DECOMPOSE_PROMPT` (§3.7) |
| R3 | **Executor** | Выполняет один шаг плана; внутри себя — ReAct цикл (Thought → Action → Observation) | ReAct (§4.6) + CAMEL Assistant (§3.3) |
| R4 | **Critic / Reflector** | Оценивает результат по явным критериям; если fail — выдаёт structured feedback | CAMEL `CriticAgent` (§3.6) + Reflexion (§4.7) |

**Что принципиально отсутствует:**

- Нет двухролевого inception dyad'а — оставляем на v0.2, когда появится
  «эксперт-заказчик» задачи.
- Нет Role Assigner — пока roster фиксирован; добавим, когда появятся
  задачи вне покрытия 4 ролей.
- Нет специализированных Tool-агентов (Search, Repo, MCP) — появятся
  вместе с инструментами.

**Внешние элементы поверх ролей:**

- **Constitution** (§4.10) — общий файл `knowledge/constitution.md`,
  включаемый в system-prompt каждой роли. 10–15 принципов + примеры.
- **Confidence labels** (§2.4) — любой outbound артефакт роли несёт
  `EXTRACTED / INFERRED / AMBIGUOUS`.

### 5.2. Скелет record'а роли

Формат хранения роли в `knowledge/roles/<role-slug>.md` (позже — не в этом
PR). **Писать сам текст system-prompt пока нельзя** — поэтому ниже только
**структура**:

```yaml
---
slug: "planner"              # стабильный идентификатор
version: "0.1"
name: "Planner"              # человекочитаемое имя
purpose: >                   # одна строка, что делает
  Breaks a specified task into a typed, ordered sequence of steps.
inputs:                      # типизированный вход (meta-dict)
  - task_prompt:   string
  - constraints:   list[string]
  - available_roles: list[string]
outputs:                     # типизированный выход
  - plan:
      type: list[step]
      step: {id, description, expected_artifact, depends_on}
model:
  primary:   "gpt-4o"
  fallback:  "claude-3.5-sonnet"
termination:
  marker: "<PLAN_DONE>"
  turn_limit: 1              # Planner — single-shot, не диалог
criteria:                    # для Critic, если дёрнут за план
  - covers_full_task
  - steps_have_explicit_artifacts
  - no_relative_references
failure_modes:               # что явно закрываем в промпте (см. §3.3)
  - role_flipping
  - over_decomposition
  - vague_deliverables
constitution: "../constitution.md"   # include
prompt_template: "planner.tmpl.md"   # **пока пустой — пишем позже**
---

# Planner — role description

(человекочитаемая часть: kогда вызывается, как взаимодействует с Executor,
какие артефакты оставляет в памяти. Здесь НЕТ текста system-prompt'а —
только описание контракта)
```

Ключевые решения:

- **Текст промпта отделён** от метаданных. YAML — контракт, `.tmpl.md` —
  тело (пишем позже).
- **Модель — часть роли**, не глобальный конфиг. Это готовит нас к
  Multi-Agent Debate (§4.5) и LLM-as-Judge (§4.13) — Critic на другой
  модели.
- **Failure modes — явный список**, чтобы при написании промпта (в
  следующем этапе) сверяться с чек-листом §3.3.
- **Constitution — include**, не копипаста.

### 5.3. Anti-patterns, которых избегаем

| Anti-pattern | Почему плохо | Источник |
|---|---|---|
| Один мегапромпт на всё | Нарушает single-responsibility; невозможно итерировать на конкретной роли | §3 в целом |
| Роль, которая может и спрашивать, и отвечать | Ломает turn-taking; агент впадает в бесконечные уточнения | CAMEL anti-CAMEL-TASK_DONE §3.11 |
| Критик без criteria | LLM-as-judge bias: вербозность и похожесть на себя выигрывают | §4.13 |
| Autonomous task creation в v0.1 | Ломает детерминизм shell'а | [agent-video-research §3][fa-video] |
| Inline prompts в Python | Нельзя итерировать без code-review; CAMEL хранит в `.py` но *как template*, не как hard-coded string | §3.8 |
| Персонажные backstory вместо competencies | Путает модель: «я пират» ≠ «я решаю задачу» | Воспринимать `persona_hub` с осторожностью (§3.4) |
| Нет termination marker'а | Петли | §3.2 |
| Confidence не маркируется | Пользователь считает всё достоверным | §2.4 |

---

## 6. Идеи (НЕ черновики) для дизайна system-prompts

**Ниже нет текста промпта — по явному запросу пользователя. Это
структурные требования**, которым должен удовлетворить будущий промпт
любой роли из §5.1. Когда придёт время писать промпты, этот раздел служит
спецификацией.

### 6.1. Обязательные структурные элементы (для любой роли)

1. **Role anchor** — имя роли + «never flip» (§3.3 #1).
2. **Purpose clause** — одна строка, зачем роль существует.
3. **Inputs contract** — какие meta-поля роль получит (соответствует
   `inputs` в record'е §5.2).
4. **Outputs contract** — тип / формат вывода (соответствует `outputs`).
5. **Turn-taking contract** — single-shot / dialog / ReAct-loop.
6. **Refusal clause** — право отказаться + формат отказа (структурированный,
   не пустота).
7. **Termination marker** — конкретная строка-выход.
8. **Failure-mode guards** — по одной строке на каждый пункт
   `failure_modes` из record'а.
9. **Confidence labels protocol** — роль обязана маркировать outbound
   утверждения.
10. **Constitution include** — ссылка / инлайн общих принципов.

### 6.2. Элементы, специфичные для каждой роли

| Роль | Дополнительные элементы |
|---|---|
| Task Specifier | Word limit; запрет расширять scope; запрет задавать вопросы |
| Planner | Schema плана; запрет относительных ссылок («как выше»); требование явного `expected_artifact` на шаг |
| Executor | ReAct-структура (Thought/Action/Observation); явный список разрешённых tools; contract на `observation` |
| Critic | `criteria` в явном виде; requirement on structured rejection с причинами; bias mitigation notes (§4.13) |

### 6.3. Что оставляем открытым

Вопросы, на которые сейчас нет ответа — надо решать в момент написания
промптов:

1. **Один LLM или разные?** Для Executor и Critic — разные имеет смысл
   (§4.5), но увеличивает latency и стоимость. Компромисс — разные
   `temperature`?
2. **Formal grammar / CFG constraints?** Outputs contract можно
   формализовать до BNF и валидировать парсером. CAMEL этого не делает;
   AutoGen/OpenAI tools — делают через JSON schema. Наш путь?
3. **Persona vs competencies.** CAMEL в `role_description_prompt_template`
   использует «competencies + duties + workflows», без personality.
   CrewAI поощряет `backstory`. Эмпирических данных, что *backstory*
   помогает на инженерных задачах — нет. Вероятно, идём по CAMEL.
4. **Multi-turn critic?** Critic в CAMEL — single-shot. Reflexion — multi-shot
   с памятью. Нам начать с single-shot; оставить хук на multi-shot.
5. **Где живёт state?** Каждой роли давать свой scratchpad, или общий
   артефакт-стор? MetaGPT (§4.3) — общий pool с subscription. Для v0.1
   проще раздельные + explicit handoff.

### 6.4. Что ожидать от первого прохода промптов

**На основе CAMEL paper и Reflexion** реалистичные ожидания:

- Первый промпт будет работать на 40–60% задач нашего eval'а.
- Failures кластеризуются в 3–5 типов; их и надо перечислить в
  `failure_modes` следующего prompt-итерации.
- Без eval-set'а итерация теряет смысл — **прежде чем писать промпты,
  нужно собрать 10–20 тест-кейсов** с ожидаемыми outcomes. Это отдельный
  research step (может быть в бэклоге как «eval harness»).

---

## 7. Конкретные следующие шаги

В порядке приоритета — *прежде чем писать system-prompts*:

1. **Определить eval-set** (10–20 задач + expected outcomes).
   Без этого итерация промптов — гадание.
2. **Написать `knowledge/constitution.md`** (10–15 принципов). Это
   короткий документ, не требующий eval'а; закрывает policy-layer для всех
   будущих промптов (§4.10).
3. **Создать скелеты 4 role-record'ов** из §5.1 в `knowledge/roles/*.md`
   (только YAML + human description, **БЕЗ prompt_template**).
4. **Выбрать model-matrix**: какой LLM для каждой роли, fallback, budget.
   Зависит от (1) и от текущих pricing'ов.
5. **Определить inter-role handoff contracts** — что Planner передаёт
   Executor'у, что Executor — Critic'у. Использовать MetaGPT (§4.3) как
   референс по типам сообщений.
6. **Только после (1)–(5)** — писать `prompt_template` для каждой роли.
7. Параллельно — прочитать **CAMEL paper целиком** (§4.1) для верификации
   §3.3-скелета.

Пункты 1–5 можно вести как самостоятельные PR'ы, не блокирующие друг друга.

---

## 8. Открытые вопросы (для обсуждения с пользователем)

- **Язык промптов**: английский или русский? CAMEL, AutoGen, MetaGPT —
  все англ. Русские промпты на GPT-4o работают, но аблации не делал
  никто в public. По умолчанию предлагаю **англ. для prompts, русский
  для документации/метаданных**.
- **Где хранить роли**: `knowledge/roles/` или `agent/roles/`? В
  архитектуре [`docs/architecture.md` §5.2][fa-arch] роли — часть
  Cognitive layer, это код. Но YAML+markdown — в `knowledge/`. Ощущение,
  что YAML-record в `knowledge/`, а Python-loader в `agent/` — оптимум.
- **Пилотная задача**: для первого прохода eval'а нужна *одна*
  эталонная задача. Какая?

---

## Sources

### Исследуемые репозитории

- R1: [safishamsi/graphify][r-graphify] — v0.5.0, pipeline-style skill
- R2: [camel-ai/camel][r-camel] — multi-agent research framework

### Публикации и проекты (в порядке появления в тексте §4)

- P1: [CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society][p-camel] — Li et al., NeurIPS 2023, arXiv:2303.17760
- P2: [ChatDev: Communicative Agents for Software Development][p-chatdev] — Qian et al., 2023, arXiv:2307.07924
- P3: [MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework][p-metagpt] — Hong et al., 2023, arXiv:2308.00352
- P4: [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation][p-autogen] — Wu et al., 2023, arXiv:2308.08155
- P5: [Improving Factuality and Reasoning in Language Models through Multiagent Debate][p-debate] — Du et al., 2023, arXiv:2305.14325
- P6: [ReAct: Synergizing Reasoning and Acting in Language Models][p-react] — Yao et al., 2022, arXiv:2210.03629
- P7: [Reflexion: Language Agents with Verbal Reinforcement Learning][p-reflexion] — Shinn et al., 2023, arXiv:2303.11366
- P8: [Self-Refine: Iterative Refinement with Self-Feedback][p-selfrefine] — Madaan et al., 2023, arXiv:2303.17651
- P9: [Tree of Thoughts: Deliberate Problem Solving with Large Language Models][p-tot] — Yao et al., 2023, arXiv:2305.10601
- P10: [Constitutional AI: Harmlessness from AI Feedback][p-caI] — Bai et al., 2022, arXiv:2212.08073
- P11: [Generative Agents: Interactive Simulacra of Human Behavior][p-genagents] — Park et al., 2023, arXiv:2304.03442
- P12: [Voyager: An Open-Ended Embodied Agent with Large Language Models][p-voyager] — Wang et al., 2023, arXiv:2305.16291
- P13: [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena][p-judge] — Zheng et al., 2023, arXiv:2306.05685
- P14: [Scaling Synthetic Data Creation with 1,000,000,000 Personas][p-persona-hub] — Ge et al., 2024, arXiv:2406.20094

### Фреймворки (read-only reference)

- CrewAI — https://github.com/crewAIInc/crewAI
- LangGraph — https://langchain-ai.github.io/langgraph/
- OpenAI Swarm — https://github.com/openai/swarm

### Связанные заметки в этом репо

- [`knowledge/research/agent-video-research.md`][fa-video] — 5 YouTube-видео, базовый словарь
- [`docs/architecture.md`][fa-arch] — трёхслойная модель First-Agent
- [`README.md` §4][fa-readme] — план исследования

[r-graphify]: https://github.com/safishamsi/graphify
[r-graphify-arch]: https://github.com/safishamsi/graphify/blob/main/ARCHITECTURE.md
[r-camel]: https://github.com/camel-ai/camel
[p-camel]: https://arxiv.org/abs/2303.17760
[p-chatdev]: https://arxiv.org/abs/2307.07924
[p-metagpt]: https://arxiv.org/abs/2308.00352
[p-autogen]: https://arxiv.org/abs/2308.08155
[p-debate]: https://arxiv.org/abs/2305.14325
[p-react]: https://arxiv.org/abs/2210.03629
[p-reflexion]: https://arxiv.org/abs/2303.11366
[p-selfrefine]: https://arxiv.org/abs/2303.17651
[p-tot]: https://arxiv.org/abs/2305.10601
[p-caI]: https://arxiv.org/abs/2212.08073
[p-genagents]: https://arxiv.org/abs/2304.03442
[p-voyager]: https://arxiv.org/abs/2305.16291
[p-judge]: https://arxiv.org/abs/2306.05685
[p-persona-hub]: https://arxiv.org/abs/2406.20094
[fa-video]: ./agent-video-research.md
[fa-arch]: ../../docs/architecture.md
[fa-readme]: ../../README.md#4-план-исследования-перед-тем-как-писать-код
