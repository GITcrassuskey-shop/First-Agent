# AGENTS.md

Короткая инструкция для AI-агентов (Devin и подобных), работающих в этом репо.

## Project Overview

**First-Agent** — исследовательский проект по созданию собственного LLM-агента.
Стадия: `research → start of module creation`. Кода в `src/` пока нет — сначала
идёт research-фаза с заметками и ADR. Подробности — в [`README.md`](./README.md).

## Repository Structure

- [`README.md`](./README.md) — единый обзор проекта (на русском).
- [`AGENTS.md`](./AGENTS.md) — этот файл.
- [`docs/`](./docs/README.md) — вики по работе с Devin (6 файлов).
  - `architecture.md` — архитектура LLM-агента.
  - `workflow.md` — процесс Research → Scaffolding → Module.
  - `prompting.md` — шаблоны промптов (T1–T5).
  - `devin-reference.md` — справочник по Devin.
  - `glossary.md`.
  - `agent creation github.md` — конспект туториала
    [build-your-own-openclaw](https://github.com/czl9707/build-your-own-openclaw).
- [`knowledge/`](./knowledge/README.md) — долговременная память проекта
  (project-overview, ADR, переиспользуемые промпты).

## Working in This Repo

- Всё документация — Markdown. ATX-заголовки (`#`, `##`), fenced code blocks с
  указанием языка, строки желательно ≤ 120 символов.
- Новые документы кладём в правильную подпапку:
  - Справочная/гайдовая дока → `docs/`.
  - Проектные артефакты (решения, исследование, промпты) → `knowledge/`.
- При добавлении нового файла в `docs/` — обновляем
  [`docs/README.md`](./docs/README.md).
- При значимом архитектурном решении — создаём ADR из шаблона
  [`knowledge/adr/0000-template.md`](./knowledge/adr/0000-template.md).

## Development Workflow

- Ветки: `devin/<timestamp>-<slug>` от `main`.
- Все изменения — через Pull Request.
- Коммит-сообщения описательные, по-английски, настоящее время
  (`docs: add architecture note`, `adr: pick orchestration style`).
- В `main` ничего не пушим напрямую.

## Query Routing

Когда нужно ответить на вопрос по проекту — **ищи по правильной папке**,
не загружай всё подряд в контекст.

| Тип вопроса | Куда идти первым | Верификация |
|---|---|---|
| Архитектура, трёхслойная модель, паттерны | [`docs/architecture.md`](./docs/architecture.md) | ADR |
| Принятое решение и причины | [`knowledge/adr/`](./knowledge/adr/) | — |
| Процесс, workflow, как работать с Devin | [`docs/workflow.md`](./docs/workflow.md), [`docs/devin-reference.md`](./docs/devin-reference.md) | — |
| Результат исследования (critique, сравнение, landscape) | [`knowledge/research/`](./knowledge/research/) | Первоисточники из `source:` во frontmatter заметки |
| Конкретное число / дата / цитата | **Первоисточник** (URL / код / gist), не summary-заметка | — |
| Термины | [`docs/glossary.md`](./docs/glossary.md) | — |

**Chain-of-custody rule.** Если в ответе участвует конкретная цифра,
дата, имя или решение — идти в первоисточник (URL, код, gist) и
цитировать *оттуда*. Не цитировать summary в `knowledge/research/` как
«авторитетный источник» для специфики; summary — это *указатель на
источник*, не сам источник. Обоснование и разбор failure mode — в
[`knowledge/research/llm-wiki-critique.md`](./knowledge/research/llm-wiki-critique.md).

**Supersession, не overwrite.** Устаревшую заметку не перезаписывать
молча. Пометить её `> **Status:** superseded by <link>` и оставить для
аудита.

## Testing Guidelines

- Пока что кода нет, поэтому CI не настроен. Проверять:
  - Markdown-ссылки ведут куда надо.
  - Документы читаются в GitHub-рендере (нет съехавших таблиц и т.п.).
- Когда появится `src/` — `make lint / typecheck / test`
  (см. [`docs/workflow.md`](./docs/workflow.md), фаза S).

## Code Style (будущий)

- Python 3.11+, полные type-хинты.
- `ruff check` + `ruff format`.
- `mypy --strict` (или `pyright`) на модули.
- `pytest`; LLM-клиент и сеть в тестах — мокаются.
- Промпты — отдельными файлами в `src/<module>/prompts/`, не в Python-строках.
