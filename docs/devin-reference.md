# Devin — компактный справочник

Одна страница вместо россыпи. Всё, что нужно знать, чтобы эффективно работать с
Devin в этом репозитории: что он умеет, когда его имеет смысл звать, какие
механизмы памяти у него есть, как расширить ему руки через MCP.

Первоисточники (если что-то здесь устарело — правьте сюда):

- <https://docs.devin.ai/essential-guidelines/when-to-use-devin>
- <https://devin.ai/agents101>
- <https://docs.devin.ai> (MCP, playbooks, skills, knowledge, scheduled sessions)

---

## Что такое Devin (коротко)

Автономный AI software engineer от Cognition. Не ассистент-дополняльщик строк,
а полный агент: берёт описание задачи → выдаёт pull request.

У Devin в каждой сессии есть:

- **Shell / Terminal** — полноценный CLI.
- **IDE** — редактор файлов.
- **Browser** — Chrome + CDP, можно скриптовать.
- **Desktop (GUI)** — X-сервер, визуальные проверки, запись экрана.

```
┌─────────────────────────────────────────────┐
│                  Devin Session               │
│                                              │
│   Shell      IDE       Browser    Desktop    │
│                                              │
│   Knowledge  Skills    Playbooks             │
│                                              │
│         MCP (External Integrations)          │
└─────────────────────────────────────────────┘
```

---

## Когда звать Devin

Правило пальца: **если задача заняла бы у вас ≤ 3 часа — Devin скорее всего справится.**
Дольше → разбивайте на несколько сессий.

Перед сессией ответьте на три вопроса:

1. Могу ли я сформулировать чёткие критерии успеха?
2. Достаточно ли контекста (файлы, паттерны, доки, MCP)?
3. Поможет ли декомпозиция?

### Хорошие задачи

- Багфикс с воспроизведением.
- Фича с понятной спецификацией.
- Рефакторинг при наличии тестов.
- Апдейт зависимостей.
- Расширение test coverage.
- Документация и README.
- CI/CD-работа.
- Миграции данных с ясной схемой.

### Плохие задачи (пока что)

- Крупный многошаговый дебаг прод-инцидента.
- Пиксельная точность UI.
- Задачи без критериев завершения.

### Best practices

- **Ask Devin** — используйте до сессии, чтобы зафиксировать подход и контекст.
- **Параллельные Devins** — независимые задачи запускайте одновременно.
- **Slack/Teams-теги** — открывайте сессию прямо из обсуждения.
- **Devin Review + Auto-Fix** — автоматические правки по ревью и CI.
- **Preview-деплой** (Vercel/Netlify/…) — мгновенная визуальная проверка.
- **Scheduled sessions** — рекуррентные задачи (апдейты deps, триаж ошибок).

---

## Инструменты Devin (Execution Layer)

| Возможность | Что это | Как используем в First-Agent |
|---|---|---|
| **Shell** | Bash на VM, state сохраняется между командами в одной сессии | Тесты, lint, билд, скрипты. |
| **Файловые тулы** | Специализированные read/write/edit | Все правки кода и доков. |
| **Browser** | Chromium + CDP на `localhost:29229` | Playwright-логины, QA UI, доки-скрейпинг. |
| **Desktop** | X server `:0` | Ручная UI-проверка. |
| **Screen recording** | Встроенная запись + аннотации | Прикреплять к PR как доказательство. |
| **PR-тулы** | `git_pr` (template/create/update) | Весь код уходит через PR. |
| **CI-тулы** | `pr_checks`, `ci_job_logs` | Ждём CI, смотрим падения. |
| **Secrets** | org/user/repo scope, TOTP | API-ключи, DB creds, тестовые аккаунты. |
| **MCP** | Marketplace + кастом | Notion, Datadog, DB, Figma, Linear… |
| **Scheduled sessions** | Cron-подобные | Еженедельные eval, deps bumps. |
| **Knowledge notes** | Долгосрочная память | Соглашения, «грабли», пути к creds. |
| **Playbooks** | Переиспользуемые рецепты | Канон release-flow, eval-пайплайна. |
| **Managed Devins** | Дочерние сессии | Параллелим A/B-эксперименты. |

---

## Память у Devin

Три типа памяти, которые стоит понимать:

### 1. Knowledge notes — долговременная память

Короткая заметка + *trigger* (ситуация, когда она релевантна). Devin автоматически
подтягивает её в нужный момент.

**Анатомия хорошей заметки:**

```
Name:     короткое searchable-имя
Trigger:  "Когда <ситуация>, это применимо."
Body:     1–5 буллетов или маленький блок кода.
          Делать, а не рассказывать.
          Ссылка на файл/URL вместо вставки содержимого.
Scope:    pinned на repo — если только про First-Agent; org — если шире.
```

**Seed-заметки для First-Agent** (ставим в Devin UI в первую очередь):

- **N1 — Repo conventions.** Trigger: «Когда правишь код в
  `GITcrassuskey-shop/First-Agent`.» Body: Python 3.11+, полные type-хинты,
  `ruff check/format`, `mypy --strict src/` (или pyright), `pytest -q`,
  один модуль на PR, промпты — в `src/<module>/prompts/`, не в Python-строках.
- **N2 — How to run checks.** Trigger: «Когда прогоняешь чек в First-Agent.»
  Body: `make lint`/`make typecheck`/`make test`/`make check`.
- **N3 — Research note conventions.** Trigger: «Когда пишешь research-заметку
  для First-Agent.» Body: путь `knowledge/research/<slug>.md`, секции
  TL;DR / Ключевые концепции / Компромиссы / Открытые вопросы / Источники.
- **N4 — Prompt library.** Trigger: «Когда переиспользуешь промпт для First-Agent.»
  Body: `knowledge/prompts/<verb>-<slug>.md`; предпочитать правку существующего.
- **N5 — Credentials & secrets.** Trigger: «Когда нужны креды для First-Agent.»
  Body: никаких хардкодов, `.env.example`, запросы через `secrets`-тул с
  говорящими именами (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`), TOTP с префиксом
  `_2FA_`.

**Правила хорошего тона:** раз в месяц ревью заметок; при конфликте — слияние,
не два «источника правды»; изменяя соглашение — правьте заметку тем же PR.

### 2. Skills — процедурная память в репозитории

`SKILL.md` — пошаговая инструкция, коммитится в репозиторий (обычно в
`.agents/skills/<slug>/SKILL.md`). Удобно для тестирования, деплоя, кастомных
пайплайнов. First-Agent пока без skill'ов — добавим, когда появятся повторяемые
процедуры.

### 3. Playbooks — переиспользуемые задачи

Многошаговый рецепт на уровне организации. Кандидаты для First-Agent:

- `ship-new-module` — скелет, тесты, доки, changelog, PR.
- `run-eval-suite` — загрузить golden set, прогнать, сравнить, отчёт.
- `cut-release` — bump версии, тег, changelog, анонс.

---

## MCP — расширение возможностей

Model Context Protocol даёт Devin доступ к внешним системам прямо из сессии.
Подключается через MCP Marketplace в настройках организации.

Кандидаты, которые стоит подключить рано:

- **Notion / Google Docs** — research-заметки живут не в репо.
- **Linear / GitHub Issues** — поиск и апдейт тикетов.
- **Vector DB** (Qdrant / pgvector / Pinecone) — когда выберем embedding-хранилище.
- **LLM observability** (LangSmith / Helicone / Arize) — для eval-прогонов.

---

## Devin Review + Auto-Fix

Включается в настройках репо. При включённом Auto-Fix Devin сам:

- Реагирует на комменты ревью.
- Чинит баги, помеченные ревьюером.
- Итерирует на CI-падениях до зелёного.

Для First-Agent держим **оба включёнными**. Финальный апрув — за человеком.

---

## Scheduled sessions — идеи под First-Agent

- **Еженедельный paper/blog sweep.** «Собери топ-постов по `<topic>` с прошлого
  понедельника, сведи в `knowledge/research/weekly/<date>.md`, открой draft PR.»
- **Dependency bumps.** Dependabot-style batch PR.
- **Eval regression.** Прогон агента на фиксированном наборе; diff метрик.
- **Doc freshness.** Раз в неделю проверять ссылки в `docs/` на 404.

---

## Коротко: что делать прямо сейчас (R → S → M)

См. [workflow.md](./workflow.md). TL;DR:

1. Писать research-заметки → PRD → минимум один ADR.
2. Поднять линтер/типы/тесты/CI/pre-commit и `Makefile`.
3. Только после этого — первый модуль.
