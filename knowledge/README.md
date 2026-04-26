# Knowledge

Durable project knowledge for First-Agent. Everything here is:

1. **Committed** to the repo so it is versioned and reviewable.
2. **Cross-referenced** from Devin Knowledge notes where useful (see
   [`docs/devin-reference.md`](../docs/devin-reference.md#1-knowledge-notes--долговременная-память)).

## Layout

```
knowledge/
├── README.md                 # this file
├── project-overview.md       # one-page product + scope snapshot
├── adr/                      # architecture decision records
│   ├── README.md
│   └── 0000-template.md
├── prompts/                  # reusable prompts
│   ├── README.md
│   └── research-topic.md
└── research/                 # (created on demand) research notes
```

## Conventions

- One concept per file.
- Markdown only. Keep under **~500 lines**; split if much longer. Раньше
  здесь стояло ~250 — повышено сознательно: исследовательские заметки часто
  ложатся в 300–450 строк без потери связности, а более жёсткий лимит
  заставлял дробить файлы там, где это вредит читаемости. Если файл
  стабильно лезет за 500 — это сигнал, что внутри живут две разные темы;
  тогда расщепляем по теме, а не по объёму.
- Link to source URLs for any non-obvious claim.
- **Never silently overwrite.** When a file is superseded: mark the old
  file with `> **Status:** superseded by <link>` at the top, add a
  `superseded_by:` field to its frontmatter if present, and keep the old
  content for audit. See the critique-driven rationale in
  [`research/llm-wiki-critique.md`](./research/llm-wiki-critique.md).

### Provenance-frontmatter (для `research/` и любых summary-заметок)

Любая заметка, которая *синтезирует* несколько источников или содержит
конкретные числа/даты/имена, должна нести frontmatter:

```yaml
---
title: "<title>"
source:
  - "<url or repo path>"
compiled: "<YYYY-MM-DD>"
chain_of_custody: "<где искать первоисточник для конкретных фактов>"
claims_requiring_verification:
  - "<claim 1>"
superseded_by: "<path, if any>"
---
```

Минимум — `source` и `compiled`. `chain_of_custody` обязателен, если в
заметке есть числа, даты, цитаты или решения, на которые кто-то может
сослаться. Цель — не потерять связь между LLM-написанной summary и
первоисточником. Подробнее — в
[`research/llm-wiki-critique-first-agent.md §9`](./research/llm-wiki-critique-first-agent.md#9-конкретные-правки-в-существующие-файлы).

## What goes where

| If it is… | Put it in… |
|---|---|
| A decision we made (and why) | `knowledge/adr/` |
| Background research / literature summary | `knowledge/research/` |
| A reusable prompt | `knowledge/prompts/` |
| Project-wide context (mission, scope, users) | `knowledge/project-overview.md` |
| How-to / guide / reference | `docs/` (not here) |

## Routing — куда агент смотрит за ответом

| Тип вопроса | Первичный источник | Вторичный / верификация |
|---|---|---|
| «Какая у нас архитектура X?» | `docs/architecture.md` | ADR в `knowledge/adr/` |
| «Какое решение приняли по Y и почему?» | `knowledge/adr/` | — |
| «Что мы нашли при исследовании Z?» | `knowledge/research/<Z>.md` | Первоисточники из `source:` frontmatter |
| Конкретное число / дата / цитата | **Всегда** первоисточник (`source:` заметки), а не summary | — |
| Процедура / how-to | `docs/` | Будущие `SKILL.md` |

Это же правило зафиксировано в [`AGENTS.md`](../AGENTS.md#query-routing).
