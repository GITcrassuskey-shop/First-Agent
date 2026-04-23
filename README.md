# First-Agent

Репозиторий, в котором я собираю **собственного LLM-агента** вместе с
[devin.ai](https://devin.ai). Этот README — единый ориентир: что за проект, где
он сейчас, куда движется и что именно предстоит исследовать перед тем, как
писать код.

> **Статус:** `research → start of module creation`.
> Первый код ещё не написан. Сначала — исследование и проектирование.

---

## 1. Зачем это

**First-Agent** — учебно-исследовательский проект по созданию автономного
LLM-агента. Цель — пройти весь путь от формулировки задачи до работающего
прототипа: выбрать модель, придумать архитектуру, собрать минимальный набор
инструментов, завести память между сессиями, написать первый модуль и
раскрутиться оттуда итеративно.

Опора — экосистема Devin (как референс для хороших практик) и официальные
гайды Cognition:

- [When to use Devin](https://docs.devin.ai/essential-guidelines/when-to-use-devin)
- [Coding Agents 101](https://devin.ai/agents101)
- [docs.devin.ai](https://docs.devin.ai)

---

## 2. Текущее состояние

- [x] Репозиторий создан.
- [x] Базовая вики про работу с Devin собрана (см. [`docs/`](./docs/README.md)).
- [x] Слот под долговременную память (ADR, промпты, обзор) создан
      ([`knowledge/`](./knowledge/README.md)).
- [ ] Написано/согласовано видение проекта (заполнить
      [`knowledge/project-overview.md`](./knowledge/project-overview.md)).
- [ ] Проведено исследование по ключевым развилкам (см. §4).
- [ ] Принят ADR-0001 (см. §4, раздел «Большие решения»).
- [ ] Поднят тулинг (lint/types/tests/CI/pre-commit, `Makefile`).
- [ ] Написан первый модуль.

Нулевое, но важное: **не пишем код, пока не закрыты первые шесть пунктов.** Это не
перфекционизм — это про то, чтобы у агента (и у меня) был нормальный
feedback-loop с самого старта.

---

## 3. Scope — что входит и что не входит

### В scope (v0.1)

- Сформулировать, какую именно задачу решает мой агент (узко, осмысленно).
- Выбрать LLM-провайдера/модель под эту задачу.
- Спроектировать минимальный набор инструментов (shell / file / …).
- Спроектировать систему памяти (session + persistent + procedural).
- Реализовать один сквозной модуль end-to-end c тестами.
- Собрать eval-набор из 10–30 кейсов и регулярно на нём мерить.

### Вне scope (v0.1)

- Production-деплой, мульти-тенантность, биллинг.
- Собственный веб-UI (CLI достаточно).
- Обучение/дообучение моделей.
- Поддержка нескольких LLM-провайдеров одновременно.
- Агент-общего-назначения «на всё». v0.1 решает одну конкретную задачу.

---

## 4. План исследования (перед тем, как писать код)

Этот раздел — то, что я хотел видеть в README в первую очередь. Пять пунктов,
каждый завершается артефактом в репо.

### Ш1. Определить задачу

Одна фраза формата «мой агент делает X для Y, успех меряется Z». Положить в
[`knowledge/project-overview.md`](./knowledge/project-overview.md) (§1–3).

**Артефакт:** заполненный project-overview (проблема, пользователи, метрики
успеха).

### Ш2. Выбрать LLM и провайдера

Сравнить минимум двух кандидатов (напр. OpenAI GPT-class vs Anthropic Claude
vs локальная модель). Критерии — см.
[`docs/architecture.md § Выбор LLM`](./docs/architecture.md#выбор-llm):
контекст, качество кода, надёжность tool-use, следование инструкциям,
цена vs качество.

**Артефакт:** `knowledge/research/llm-selection.md` (шаблон заметки —
[T1 в docs/prompting.md](./docs/prompting.md#t1--research--summarise-into-a-note)).

### Ш3. Выбрать стиль оркестрации

Основные кандидаты:

- **ReAct** (thought → action → observation, простой цикл).
- **Plan-and-Execute** (сначала весь план, потом исполнение).
- **Hand-rolled state machine** — явный конечный автомат под нашу доменную задачу.
- Готовые фреймворки: LangGraph, CrewAI, ручная оркестрация.

Стратегия — не спорить в вакууме, а воспользоваться T3 из playbook: попросить
Devin набросать два минимальных прототипа и сравнить по latency/читаемости/
тестируемости.

**Артефакт:** `knowledge/research/orchestration.md` + решение, записанное как
ADR-0001 в [`knowledge/adr/`](./knowledge/adr/).

### Ш4. Спроектировать набор инструментов и формат tool-call

Минимум: `shell`, `read_file`, `write_file`, `list_dir`. Расширения: `http_get`,
`search`, `vector_lookup` — по мере нужды. Решить формат вызова (JSON schema /
XML / функции провайдера) и как мокать инструменты в тестах.

**Артефакт:** `knowledge/research/tools-and-toolcall.md`.

### Ш5. Спроектировать память

Три слоя памяти — см.
[`docs/architecture.md § Архитектура памяти`](./docs/architecture.md#архитектура-памяти):

- **Session memory:** просто в процессе.
- **Persistent knowledge:** файл/БД? JSON/SQLite/embeddings?
- **Procedural memory:** `SKILL.md`-подобные файлы?
- **Episodic memory:** логи сессий + инструмент «посмотри, как я решал похожее».

Решить, что запускаем в v0.1 (почти наверняка — только session + минимальный
persistent), остальное — в roadmap.

**Артефакт:** `knowledge/research/memory.md` + ADR-0002.

---

## 5. После исследования — Scaffolding и первый модуль

Подробнее в [`docs/workflow.md`](./docs/workflow.md). Коротко:

1. **Scaffolding.** `pyproject.toml`, `ruff` + `mypy`/`pyright` + `pytest`,
   CI на GitHub Actions, `Makefile`, `pre-commit`. До этого шага модули не
   пишем — у Devin не будет фидбек-лупа.
2. **Первый модуль.** Один сквозной слайс агента: принять задачу → дернуть
   LLM → сделать один tool-call → вернуть результат. С тестами, с мокнутым
   LLM, с типами.
3. **Далее — итеративно.** Каждый модуль = отдельный PR. Каждый PR обновляет
   `CHANGELOG.md`. Каждое значимое решение = ADR.

---

## 6. Структура репозитория

```
.
├── README.md                       # этот файл
├── AGENTS.md                       # короткий гайд для AI-агента в этом репо
├── docs/                           # вики (5 файлов, см. docs/README.md)
│   ├── README.md
│   ├── architecture.md             # трёхслойная модель + паттерны агента
│   ├── workflow.md                 # Research → Scaffolding → Module
│   ├── prompting.md                # шаблоны T1–T5 и anti-patterns
│   ├── devin-reference.md          # справочник по Devin
│   └── glossary.md
├── knowledge/                      # долговременная память проекта
│   ├── README.md
│   ├── project-overview.md         # stub — заполнить в research-фазе
│   ├── adr/                        # Architecture Decision Records
│   │   ├── README.md
│   │   └── 0000-template.md
│   ├── prompts/                    # переиспользуемые промпты
│   │   ├── README.md
│   │   └── research-topic.md
│   └── research/                   # (создастся при первом research-PR)
└── (код появится позже в src/)
```

---

## 7. Как работать с этим репо

- Прочитать `README.md` (вот этот).
- Открыть `docs/README.md` и пройтись по пяти файлам вики.
- Заполнить `knowledge/project-overview.md` — базовый якорь для всех будущих сессий.
- Запускать каждое исследование отдельной Devin-сессией по шаблону T1.
- Любое значимое решение → ADR из шаблона `knowledge/adr/0000-template.md`.
- Мелочи, которые Devin должен помнить, — превращаем в Knowledge notes в Devin UI
  (5 seed-заметок уже описаны в
  [`docs/devin-reference.md`](./docs/devin-reference.md#1-knowledge-notes--долговременная-память)).

---

## 8. Полезные ссылки

**Официальные:**

- [docs.devin.ai](https://docs.devin.ai)
- [When to use Devin](https://docs.devin.ai/essential-guidelines/when-to-use-devin)
- [Coding Agents 101](https://devin.ai/agents101)

**Внутри репо:**

- [docs/architecture.md](./docs/architecture.md) — архитектура агента.
- [docs/workflow.md](./docs/workflow.md) — фазы R → S → M.
- [docs/prompting.md](./docs/prompting.md) — промпт-шаблоны.
- [docs/devin-reference.md](./docs/devin-reference.md) — справочник по Devin.
- [docs/glossary.md](./docs/glossary.md) — глоссарий.
- [knowledge/README.md](./knowledge/README.md) — как устроена память проекта.

---

*Статус документа — draft. Правим по ходу исследования.*
