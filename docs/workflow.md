# Рабочий процесс — research → scaffolding → module

Это руководство «день за днём» для текущей фазы First-Agent:
выбор агента сделан, идёт research, скоро начнётся написание модулей.

Процесс делится на **три фазы**. Не пропускайте — они идут именно в этом порядке.

---

## Bootstrap pattern: создавайте `llms.txt` сразу

Когда заводите новый LLM-агентский проект (свой или форк First-Agent для другой задачи) — **первым делом** создайте `knowledge/llms.txt` (или `llms.txt` в корне) по convention'у [llmstxt.org](https://llmstxt.org/).

Это hand-maintained URL-индекс ваших docs/ и knowledge/ как raw-ссылок (GitHub raw, GitLab raw, etc.). Любой LLM-агент (Devin, Claude, GPT через web-fetch) за один HTTP-запрос получает карту проекта — и не должен crawl'ить репо или принимать список файлов руками.

Пример из этого репо: [`knowledge/llms.txt`](../knowledge/llms.txt).

Затраты: 30 минут один раз + одна строка в `AGENTS.md` PR-чек-листе про обновление при изменении структуры. Возврат: десятки минут трения, сэкономленных в каждой будущей сессии. Drift — реален, поэтому:

1. Правило в PR-чек-листе: «если структура `docs/` или `knowledge/` изменилась, обнови `llms.txt`».
2. Опционально, после Phase S: pre-commit hook или CI-проверка, которая регенерирует `llms.txt` из дерева.

Подробнее про convention — [llmstxt.org](https://llmstxt.org/), про rationale — [`knowledge/research/agentic-memory-supplement.md` §4 «gbrain»](../knowledge/research/agentic-memory-supplement.md).

---

## Фаза R — Research

**Цель:** выйти с письменным, отревьюенным планом того, что и как будем строить.

### Шаги

1. **Сформулировать вопрос.** Одно предложение проблемы + 3–5 подвопросов.
   Кладём в `knowledge/research/_open-questions.md`.
2. **Скоупим через Ask Devin.** Показываем существующий код и краткое описание;
   получаем высококонтекстный промпт для исследовательских сессий.
3. **Запускаем параллельные research-сессии** (по сессии на подвопрос).
   Используем шаблон [T1 — Research & summarise](./prompting.md#t1--research--summarise-into-a-note).
   Результат каждой — файл в `knowledge/research/<slug>.md`.
4. **Консолидируем.** Одна сессия (или человек) сводит заметки в
   `knowledge/research/_consolidated.md` с рекомендацией.
5. **Пишем PRD** — шаблон [T4 — Co-develop a PRD](./prompting.md#t4--co-develop-a-prd).
   Вывод: `docs/prd/<slug>.md`. Обязательно ревью человеком до выхода из фазы R.

### Критерии выхода из фазы R

- [ ] Проблема сформулирована и принята.
- [ ] PRD существует и отревьюен.
- [ ] Минимум один ADR (`knowledge/adr/NNNN-*.md`) фиксирует «большое решение»
      (фреймворк, стиль оркестрации, модель).
- [ ] Открытые вопросы, не закрытые research'ем, явно помечены как *deferred*.

---

## Фаза S — Scaffolding (обязательно перед первым модулем)

Прежде чем писать первый модуль, убедимся, что у Devin есть feedback-loop
(см. [architecture.md § Паттерн 1](./architecture.md#п1--feedback-loop-самый-важный)).

### Шаги

1. **Выбрать язык** (скорее всего — типизированный Python 3.11+).
   Создать `pyproject.toml`.
2. **Добавить lint + type + test.**
   - `ruff` — lint и format.
   - `mypy --strict` или `pyright` — типы.
   - `pytest` (+ `pytest-asyncio`, если идём в async).
3. **CI** — минимальный workflow на GitHub Actions: lint/types/tests на каждом PR.
4. **`Makefile`** (или `justfile`) с `make lint / test / typecheck / run`.
5. **Pre-commit** — `.pre-commit-config.yaml` с ruff, eol, whitespace, markdownlint.
6. **Knowledge note** в Devin со ссылкой на Makefile — шаблон в
   [devin-reference.md § Knowledge Notes](./devin-reference.md#knowledge-notes).
7. **`llms.txt` auto-generator.** Скрипт, который регенерирует
   [`knowledge/llms.txt`](../knowledge/llms.txt) из текущего дерева
   `docs/` + `knowledge/`, плюс хук в pre-commit и CI-проверка
   `git diff --exit-code knowledge/llms.txt` после регенерации.
   Снимает риск drift'а из manual maintenance — сейчас
   `AGENTS.md` §PR Checklist #7 ловит drift только если человек
   не забыл; pre-commit ловит автоматически. Зависимость: после
   шагов 1–5 (нужен Python проект + pre-commit + CI). Пока этого
   нет — действует ручное правило #7.

### Критерии выхода из фазы S

- [ ] `make test` проходит (хотя бы smoke-тест) и возвращает 0.
- [ ] CI зелёный на `main`.
- [ ] Pre-commit установлен и работает.
- [ ] Knowledge note «как запускать проверки» живёт.

---

## Фаза M — Module creation (итеративная)

Теперь можно писать модули. Цикл на каждый модуль:

```text
┌────────────────────────────────────────────────────────┐
│  1. Если решение новое — черновик ADR в knowledge/adr/ │
│  2. Промптим Devin шаблоном T2 (scaffold) → draft PR   │
│  3. Человеческое ревью → request changes / merge       │
│  4. Новые «грабли» — в Knowledge notes                 │
│  5. Обновить индекс docs/README.md, если появился док  │
└────────────────────────────────────────────────────────┘
```

### Раскладка одного модуля

```text
src/<module_name>/
  __init__.py
  <module_name>.py        # один публичный класс/функция
  types.py                # pydantic/dataclass I/O типы
  prompts/                # промпты как .md/.jinja2 файлы
  README.md               # за что отвечает модуль
  tests/
    test_<module>.py
```

### Правила для PR по модулю

- Один модуль — один PR. Мелкие PR мержатся быстрее.
- Без нетипизированного кода. Никогда.
- Все сетевые/LLM-вызовы — через инъекцию зависимостей и мокаются в тестах.
- Каждый промпт — отдельный файл в `prompts/`, в Python-строки не зашиваем.
- Каждый PR обновляет `CHANGELOG.md` (или у нас есть генератор).

---

## Anti-patterns для этой фазы

- ❌ Писать первый модуль до того, как появились lint/test/types.
  Агент теряет фидбек-луп.
- ❌ Оставлять research-заметки на чьём-то ноутбуке. Коммитим.
- ❌ Пропустить PRD «потому что и так ясно». Если ясно — то за 10 минут пишется.
- ❌ Одна сессия = research + scaffolding + реализация. Разделяйте.
