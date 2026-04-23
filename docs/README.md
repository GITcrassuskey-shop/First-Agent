# Документация First-Agent

Небольшая, опрятная вики по работе с devin.ai над проектом First-Agent.
«Less is more» — пять файлов, каждый со своей ролью.

| Файл | Когда читать |
|---|---|
| [architecture.md](./architecture.md) | Проектируем агента. Трёхслойная модель, паттерны, соображения по LLM/памяти/восстановлению. |
| [workflow.md](./workflow.md) | Наш текущий день-за-днём процесс: **Research → Scaffolding → Module**, с критериями выхода из каждой фазы. |
| [prompting.md](./prompting.md) | Пишем промпт для Devin. Основы, шаблоны T1–T5, anti-patterns. |
| [devin-reference.md](./devin-reference.md) | Что Devin умеет, когда его звать, как устроена его память (Knowledge/Skills/Playbooks), MCP, scheduled sessions. |
| [glossary.md](./glossary.md) | Незнакомый термин. |

Долговременная память проекта (ADR, промпты, обзор) — в [`../knowledge/`](../knowledge/README.md).

## Принципы этой вики

1. Менее — лучше. Если два файла пересекаются — сливаем.
2. Если расходимся с официальными доками Devin — правим у себя.
3. Если нашли что-то, что Devin должен помнить между сессиями — кладём в
   [`../knowledge/`](../knowledge/) **и** создаём Knowledge note в Devin UI
   (см. [devin-reference.md § Knowledge notes](./devin-reference.md#1-knowledge-notes--долговременная-память)).
