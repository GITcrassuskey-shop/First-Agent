---
title: Создание агента — разбор build-your-own-openclaw
source: https://github.com/czl9707/build-your-own-openclaw
reference_impl: https://github.com/czl9707/pickle-bot
tags:
  - llm-agent
  - tutorial
  - architecture
  - openclaw
created: 2026-04-23
---

# Создание агента: разбор `build-your-own-openclaw`

> Статья-конспект туториала
> [`czl9707/build-your-own-openclaw`](https://github.com/czl9707/build-your-own-openclaw)
> — 18 шагов от простого chat loop до облегчённой версии
> [OpenClaw](https://github.com/openclaw/openclaw). Референс-реализация —
> [`pickle-bot`](https://github.com/czl9707/pickle-bot).

Формат: длинная статья для чтения со смартфона — в Obsidian или прямо в
GitHub-рендере. Технические термины сохранены на английском (tool, skill,
event bus, cron, channel, session, prompt и т.д.). Ссылки оглавления — обычные
Markdown-якоря, работают в обеих средах.

---

## TL;DR

Туториал показывает, как постепенно, шаг за шагом, нарастить из минимального
chat loop полноценного LLM-агента. Каждый следующий шаг — это один чёткий
архитектурный слой, а не ворох фичей сразу:

- **Phase 1 (steps 00–06)** — capable single agent: чат, tools, skills, память,
  команды, compaction, выход в web.
- **Phase 2 (steps 07–10)** — event-driven refactor: event bus, hot reload,
  channels (Telegram / Discord / ...), WebSocket.
- **Phase 3 (steps 11–15)** — autonomous & multi-agent: routing, cron,
  multi-layer prompts, post-message-back, subagent dispatch.
- **Phase 4 (steps 16–17)** — production: concurrency control, long-term
  memory.

---

## Оглавление

- [Общая философия проекта](#общая-философия-проекта)
- [Phase 1 — Capable Single Agent (steps 00–06)](#phase-1--capable-single-agent-steps-0006)
  - [Step 00 — Chat Loop](#step-00--chat-loop)
  - [Step 01 — Tools](#step-01--tools)
  - [Step 02 — Skills](#step-02--skills)
  - [Step 03 — Persistence](#step-03--persistence)
  - [Step 04 — Slash Commands](#step-04--slash-commands)
  - [Step 05 — Compaction](#step-05--compaction)
  - [Step 06 — Web Tools](#step-06--web-tools)
- [Phase 2 — Event-Driven Architecture (steps 07–10)](#phase-2--event-driven-architecture-steps-0710)
  - [Step 07 — Event-Driven](#step-07--event-driven)
  - [Step 08 — Config Hot Reload](#step-08--config-hot-reload)
  - [Step 09 — Channels](#step-09--channels)
  - [Step 10 — WebSocket](#step-10--websocket)
- [Phase 3 — Autonomous & Multi-Agent (steps 11–15)](#phase-3--autonomous--multi-agent-steps-1115)
  - [Step 11 — Multi-Agent Routing](#step-11--multi-agent-routing)
  - [Step 12 — Cron + Heartbeat](#step-12--cron--heartbeat)
  - [Step 13 — Multi-Layer Prompts](#step-13--multi-layer-prompts)
  - [Step 14 — Post Message Back](#step-14--post-message-back)
  - [Step 15 — Agent Dispatch](#step-15--agent-dispatch)
- [Phase 4 — Production & Scale (steps 16–17)](#phase-4--production--scale-steps-1617)
  - [Step 16 — Concurrency Control](#step-16--concurrency-control)
  - [Step 17 — Memory](#step-17--memory)
- [Что намеренно не вошло в туториал](#что-намеренно-не-вошло-в-туториал)
- [Как запускать](#как-запускать)
- [Что унести в First-Agent](#что-унести-в-first-agent)

---

## Общая философия проекта

- Каждый step — **отдельный запускаемый codebase** со своим `README.md` и
  диаграммой, что делает прогресс осязаемым.
- Tools минимальны: авторы настаивают, что `read`, `write`, `bash` — уже
  достаточно, чтобы агент делал реально полезные вещи.
- Skills — это **lazy-loaded capabilities**: агент подгружает `SKILL.md`
  только когда нужно, экономит контекст и tool registry.
- Весь рантайм построен вокруг **event bus**. Это разблокирует channels,
  cron, subagent dispatch, post-message-back и concurrency control без
  переписывания ядра.
- LLM-провайдер абстрагируется через [LiteLLM](https://docs.litellm.ai/docs/providers):
  OpenAI, Anthropic, Gemini, Qwen, Grok, MiniMax, Z.ai и любые
  OpenAI-compatible endpoints.

---

## Phase 1 — Capable Single Agent (steps 00–06)

Цель фазы: довести одного агента до состояния, когда он **сам по себе**
способен болтать, пользоваться tools, учиться новым skills, помнить
разговоры и ходить в web.

### Step 00 — Chat Loop

> All agents start with a simple chat loop.

Простейший цикл: читаем ввод пользователя → добавляем в историю → зовём LLM →
показываем ответ → повторяем.

**Key components:**

- `ChatLoop` — принимает пользовательский ввод, рендерит ответ.
- `LLM Call` — отправляет всю историю сообщений провайдеру, возвращает ответ.
- `Session` — хранит message history. LLM всегда видит её целиком.

Минимум, на котором держится всё остальное. Никакой магии: это обычный цикл
вокруг `acompletion(...)` из LiteLLM.

### Step 01 — Tools

> Simple tools are more powerful than you think. Read, Write, Bash is enough.

Даём агенту способ **действовать**, а не только отвечать текстом.

**Key components:**

- `Stop Reason` — chat loop может остановиться по `end_turn` или `tool_use`.
- `Tools` — реестр tools плюс исполнение tool calls.
- `Tool Calling Loop` — агент зовёт tool → результат складывается в историю →
  LLM продолжает разговор до `end_turn`.

Каждый tool описывается `name`, `description`, `parameters`, и экспортирует
`get_tool_schema()` — это и есть то, что уходит в LLM как function schema.

### Step 02 — Skills

> Extend your agent with `SKILL.md`.

Skills — это **ленивые** capabilities, которые подгружаются в контекст
только когда реально нужны. Открытый стандарт, см.
[официальную документацию Anthropic по Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).

**Key components:**

- `SkillDef` — определение skill: id, name, description, content.
- `SKILL.md` — формат файла: YAML frontmatter + markdown body.
- `skill` tool — динамический tool: перечисляет доступные skills и
  подгружает содержимое по требованию.

**Два подхода к skills:**

- **Tool Approach** (этот туториал): отдельный `skill` tool, который
  list'ит и load'ит skills. Discovery и loading — self-contained.
- **System Prompt Approach** (как в OpenClaw): метаданные skills
  инжектятся в system prompt, агент читает `SKILL.md` обычным `read`
  tool. Никакого специализированного skill tool не нужно — tool registry
  остаётся меньше.

Второй вариант красиво ложится на [Step 13 — Multi-Layer Prompts](#step-13--multi-layer-prompts).

### Step 03 — Persistence

> Save your conversations.

Сессии начинают переживать перезапуски.

**Key components:**

- `.history/index.jsonl` — JSONL-индекс всех сессий с метаданными.
- `.history/sessions/{id}.jsonl` — JSONL-хранилище сообщений конкретной
  сессии.

JSONL даёт append-only запись и простое восстановление без SQL и миграций.
Для research-агента это идеальный trade-off: «почти база данных» без базы
данных.

### Step 04 — Slash Commands

> Direct user control over sessions.

Детерминированные команды прямо из чата: `/help`, `/skills`, `/session`.

**Key components:**

- `Command` — базовый класс (async `execute`).
- `CommandRegistry` — регистрация и диспатч команд.
- Набор дефолтных команд.

**Важное дизайн-решение:** добавлять slash command в session history или
нет — открытый вопрос. Команды — это user controls, а не контент разговора.
Оба подхода легитимны, зависит от use case.

### Step 05 — Compaction

> Pack your history and carry on...

Длинные разговоры рано или поздно упираются в context window. Compaction
решает это автоматически.

**Key components:**

- `Token Estimation` — через `litellm.token_counter`.
- `Truncation Strategy` — сначала режем большие tool results, затем
  суммаризируем старые сообщения.
- `Context Compaction` — суммаризация старых сообщений и запуск новой
  сессии с этим summary в первых промптах.
- Команды `/compact` (ручной запуск) и `/context` (показать использование).

Алгоритм шага ровно такой:

- Контекст превысил threshold?
- Обрезать oversized tool result.
- Всё ещё overflow?
- Суммаризировать старые сообщения.
- Rollover в новую сессию с summary как bootstrap.

### Step 06 — Web Tools

> Your agent wants to see the bigger world.

LLM знает, как писать Python, но не знает свежие changelog'и и новости. Web
tools это чинят.

**Key components:**

- `WebSearchProvider` — абстракция над провайдерами поиска.
- `WebReadProvider` — абстракция над «прочитай URL».
- Tools `websearch` и `webread` поверх этих провайдеров.

Это буквально «just two new tools», но они снимают главный потолок capable
single agent'а.

---

## Phase 2 — Event-Driven Architecture (steps 07–10)

Цель фазы: сделать агента пригодным не только к CLI. Рефакторинг под event
bus — самый крупный шаг во всей серии.

### Step 07 — Event-Driven

> Expose your agent beyond CLI.

Главный архитектурный сдвиг. Message sources отделяются от исполнения
агента через event bus.

**Key components:**

- `EventBus` — центральный pub/sub.
- `Events` — `InboundEvent`, `OutboundEvent`.
- `Workers` — фоновые таски, которые подписываются на события.
- `AgentWorker` — принимает `InboundEvent`, исполняет agent session,
  публикует `OutboundEvent`.

На этом шаге с точки зрения пользователя ничего не меняется («nothing
should be different»). Но именно он открывает дорогу channels, cron, и
subagent dispatch.

### Step 08 — Config Hot Reload

> Edit without restart.

Правим config — изменения подхватываются на лету.

**Key components:**

- `ConfigReloader` — смотрит за workspace через `watchdog`.
- `Config Merging` — runtime config перекрывает user config через deep
  merge.

Без рестарта можно менять модели, токены, включать/выключать channels и
tools. Для research-агента, где итерация — основная активность, это
экономит минуты на каждом цикле.

### Step 09 — Channels

> Talk to your agent from on your phone.

Теперь агент доступен из Telegram, Discord и любой другой платформы.

**Key components:**

- `EventSource` — абстракция над источником события (CLI, Telegram,
  Discord).
- `Channel` — абстракция над платформой: `run` / `reply` / `stop`.
- `ChannelWorker` — поднимает каналы, публикует `InboundEvent`.
- `DeliveryWorker` — подписан на `OutboundEvent`, доставляет ответ в
  правильный канал.
- `Event Persistence` — outbound events пишутся на диск атомарно (`tmp` +
  `fsync` + `rename`), на старте event bus восстанавливает pending'и —
  сообщения не теряются.

Маппинг «источник → сессия» хранится как `platform-telegram:chat_id:user_id
→ session_id` в `config.runtime.yaml`. Первое сообщение создаёт сессию,
остальные переиспользуют.

Flow outbound persistence:

- `EventBus.publish()` — кладёт событие в asyncio queue.
- `_persist_outbound()` — атомарно пишет `OutboundEvent` на диск.
- `_notify_subscribers()` — рассылает подписчикам.
- После успешной доставки `DeliveryWorker` зовёт `eventbus.ack(event)`,
  который удаляет persisted файл.

### Step 10 — WebSocket

> Want to interact with your agent programmatically?

Программный доступ поверх WebSocket.

**Key components:**

- `WebSocketWorker` — держит соединения и транслирует события.
- WebSocket handle в FastAPI-приложении с endpoint `/ws`.

Это тот же channel pattern, только для кастомных клиентов — веб-UI,
скрипты, другие сервисы.

---

## Phase 3 — Autonomous & Multi-Agent (steps 11–15)

Цель фазы: превратить агента из reactive-чатбота в автономного игрока,
который сам стартует задачи, сам зовёт подагентов и сам пишет вам первым.

### Step 11 — Multi-Agent Routing

> Route right job to right agent.

На одном процессе — несколько агентов, каждое сообщение идёт к
подходящему.

**Key components:**

- `AgentLoader` — discovery агентов (`<workspace>/agents/<agent_id>/AGENT.md`).
- `RoutingTable` — регулярки, матчащие source → agent, с автоматическим
  расчётом tier'а специфичности.
- `Binding` — одна строка таблицы routing'а.
- Slash commands `/route`, `/bindings`, `/agents` для управления.

Алгоритм:

- **Tiered Routing Rules** — ищем совпадение, начиная с самых специфичных
  rules.
- **Default Fallback** — если ничего не совпало, уходим на глобального
  default-агента.

### Step 12 — Cron + Heartbeat

> An agent works while you are sleeping.

Агент умеет расписания.

**Key components:**

- `CRON.md` + `CronDef` — описание cron job в workspace.
- `CronWorker` — каждую минуту проверяет, пора ли что-то запустить.
- `DispatchEvent` / `DispatchResultEvent` — внутренние события для
  диспатча и результата.
- `Cron-Ops Skill` — создать / list / удалить cron реализовано как
  **skill**, чтобы не раздувать tool registry.

Cron vs. Heartbeat в OpenClaw:

- **HEARTBEAT** — один на агента, крутится в main session через
  равные интервалы без привязки к времени.
- **CRON** — много, фоновых, с настоящими cron-выражениями.

### Step 13 — Multi-Layer Prompts

> More context, more context, more context.

System prompt собирается из **слоёв**, а не лежит одним куском.

**Key components:**

- `AgentDef` с `soul_md` extension.
- `PromptBuilder` — собирает все слои в финальный system prompt.

Типовой workspace:

- `agents/<agent_id>/AGENT.md` — identity, capabilities, behavioural
  guidelines + YAML frontmatter под config.
- `agents/<agent_id>/SOUL.md` — personality layer, тон и характер.
- `BOOTSTRAP.md` — гайд по структуре workspace: какие директории, какие
  path template'ы у agents/skills/crons/memories.
- `AGENTS.md` — список доступных агентов и паттерны делегирования.

Архитектура расширяемая: можно добавить **memory layer**, который будет
инжектить релевантные воспоминания (предпочтения юзера, текущие проекты,
история) в начало system prompt'а.

### Step 14 — Post Message Back

> Your agent wants to speak to you.

Агент может **инициировать** сообщения сам — например, когда отработал
cron.

**Key components:**

- `post_message_tool` — factory, создающая tool, если включены channels.
- `DeliveryWorker` — он же из Phase 2 занимается доставкой `OutboundEvent`
  в нужный channel.

Важно: `post_message` доступен только внутри cron job, не в интерактивной
сессии. Это намеренное ограничение, чтобы агент не начал вас спамить
посреди обычного диалога.

### Step 15 — Agent Dispatch

> Your agent wants friends to work with!

Агенты умеют делегировать работу друг другу.

**Key components:**

- `subagent_tool` — factory, генерирующий dispatch tool с динамической
  schema (список доступных subagents).

Механика через event bus:

1. **Publish.** Главный агент зовёт `subagent_dispatch`, публикует
   `DispatchEvent` с task и session info.
2. **Subscribe.** Вешается временный handler на `DispatchResultEvent`,
   фильтрующий по session id.
3. **Await.** Главный агент ждёт future, который резолвнется, когда
   subagent опубликует результат.
4. **Cleanup.** Хэндлер отписывается.

**Альтернативные multi-agent паттерны** (на заметку):

- **Shared Task Lists** — агенты не общаются напрямую, а через общую
  очередь задач. Кто свободен, тот и берёт.
- **Tmux / Screen Sessions** — tmux skill учит агента запускать
  параллельные процессы; «мульти-агентность» достигается сбоку.

---

## Phase 4 — Production & Scale (steps 16–17)

Цель фазы: то, без чего нельзя переходить от демо к живому сервису.

### Step 16 — Concurrency Control

> Too many Pickle are running at the same time?

Не даём агенту съесть всю машину и rate-лимит провайдера.

**Key components:**

- `AgentDef.max_concurrency` — лимит на агента в config'е.
- Semaphore-based concurrency control — блокируется, когда лимит
  достигнут.

Гранулярности, из которых можно выбирать:

- **By Agent** (показано в туториале) — ограничиваем per-agent.
- **By Source** — ограничиваем per-user / per-client, защита от abuse.
- **By Priority** — разные лимиты для разных priority levels, для
  high-priority можно зарезервировать capacity.

### Step 17 — Memory

> Remember me!

Долговременная память, доступная между сессиями.

**Key components:**

- Memory agent — специализированный агент, отвечающий за работу с
  памятью (в туториале это `cookie`).
- Обращаемся к нему через subagent dispatch из [Step 15 — Agent Dispatch](#step-15--agent-dispatch).

**Альтернативные подходы к памяти:**

| Подход | Описание |
|---|---|
| Specialized Agent (этот туториал) | Отдельный memory agent, вызов через dispatch. |
| Direct Tools | Memory tools прямо в главном агенте. |
| Skill-Based | Использовать CLI-tools (grep, etc.) через skill. |
| Vector Database | Семантический поиск по embeddings. |

---

## Что намеренно не вошло в туториал

Из [`GAP.md`](https://github.com/czl9707/build-your-own-openclaw/blob/main/GAP.md):

- **Template Substitution** — `{{variable}}` в `AGENT.md` / `SKILL.md` есть
  в picklebot, но в туториал не перенесено. Пути предлагается хардкодить
  или брать из config.
- **HTTP API Endpoints** — полноценного REST API нет, только WebSocket
  endpoint `/ws`. REST можно добавить потом, он не обучает core concepts.

---

## Как запускать

1. Скопировать config-пример:

    ```bash
    cp default_workspace/config.example.yaml default_workspace/config.user.yaml
    ```

2. Вписать API key — см.
   [PROVIDER_EXAMPLES.md](https://github.com/czl9707/build-your-own-openclaw/blob/main/PROVIDER_EXAMPLES.md).
   Поддерживаются OpenAI, Anthropic, Gemini, Qwen, Grok, MiniMax, Z.ai и
   любые OpenAI-compatible endpoints через LiteLLM.

3. Зайти в папку нужного шага и запустить CLI:

    ```bash
    cd 00-chat-loop
    uv run my-bot chat
    ```

4. Двигаться по шагам строго по порядку — каждый шаг собран как
   самостоятельный codebase, который **дополняет** предыдущий, а не
   переписывает его.

---

## Что унести в First-Agent

Короткий список идей, которые напрямую применимы к нашему проекту:

- **JSONL persistence** ([Step 03 — Persistence](#step-03--persistence)) —
  самый дешёвый способ получить «почти базу данных» для session history
  без SQL.
- **Skills как lazy-loaded `SKILL.md`** ([Step 02 — Skills](#step-02--skills))
  — ровно тот паттерн, который мы уже видим в Devin. Разумно
  переиспользовать.
- **Event bus как ядро** ([Step 07 — Event-Driven](#step-07--event-driven))
  — если хотим когда-то выйти за CLI, проще сразу закладывать
  event-driven архитектуру, чем рефакторить позже.
- **Multi-layer prompts**
  ([Step 13 — Multi-Layer Prompts](#step-13--multi-layer-prompts)) —
  кандидат на отдельный ADR: как мы собираем system prompt (identity +
  soul + workspace + memory layer + runtime context).
- **Concurrency control per agent**
  ([Step 16 — Concurrency Control](#step-16--concurrency-control)) —
  простой семафор на `AgentDef.max_concurrency`, must-have перед любым
  «деплоем куда-то».
- **Memory через dedicated subagent**
  ([Step 17 — Memory](#step-17--memory)) — один из четырёх вариантов, и
  пока самый понятный: изолированный контекст, отдельные tools, доступ
  через dispatch.

Для привязки к нашему процессу см. [`workflow.md`](./workflow.md) и
[`architecture.md`](./architecture.md). Когда доберёмся до конкретных
решений — оформляем их как ADR в [`../knowledge/adr/`](../knowledge/adr/).
