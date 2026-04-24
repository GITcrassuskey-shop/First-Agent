---
title: "Research — LLM Wiki критика: применимость к First-Agent"
source:
  - "./llm-wiki-critique.md"
  - "./llm-wiki-critique-sources.md"
  - "./agent-roles.md"
compiled: "2026-04-24"
chain_of_custody: >
  Этот файл — *применение выводов* к нашему проекту. Все внешние
  утверждения со ссылкой на критиков или литературу — верифицировать
  через parent-заметку llm-wiki-critique.md (§Sources).
claims_requiring_verification: []
---

# Research — LLM Wiki критика: применимость к First-Agent

> **Статус:** research note, 2026-04-24.
> **Parent:** [`llm-wiki-critique.md`](./llm-wiki-critique.md) — TL;DR,
> факты, фактчек.
> **Companion:** [`llm-wiki-critique-sources.md`](./llm-wiki-critique-sources.md)
> — разбор источников.
>
> Этот файл — «что из всего этого мы тащим в First-Agent»: применимость
> к памяти *LLM-агента* (не вики для человека), списки «берём / заглядываем
> / не берём», пересечения с ролями агента, Engelbart-фрейм, список
> конкретных правок и шаблон frontmatter'а.

---

## 5. Применимость к памяти LLM-агента, а не к wiki для человека

Это самая важная часть для First-Agent. В Wiki Карпатого wiki — для
**человека**, LLM — это писарь. В нашем случае wiki — для **агента**
(Planner, Executor, Critic из [`agent-roles.md`](./agent-roles.md)), LLM
— и писарь, и читатель. Это ломает ряд аргументов и обостряет другие.

### 5.1. Что усугубляется для агентской памяти

- **Feedback-loop жёстче.** У пользователя Wiki открыт Obsidian; он
  ловит дрейф глазом. У нашего агента глаз нет. Любой drift в
  `knowledge/` → агент тупит в будущих сессиях, и мы заметим это не по
  виду заметки, а по *регрессу поведения*. То есть provenance и
  supersession не опция, а обязательство.
- **Scale mismatch.** Персональный wiki растёт по гигабайтам страниц.
  Память агента растёт по *каждой сессии* — быстрее и с большим долей
  LLM-авторства. Токен-бюджет важнее.
- **Multi-agent write.** У нас любые две параллельные Devin-сессии — уже
  multi-agent: они обе могут трогать `knowledge/`. «Last-write-wins»
  неприемлем. Supersession и explicit conflict-файл нужны.

### 5.2. Что ослабляется

- **Human curation.** У Karpathy — must-have. У агента в проде — not
  scalable. Но у нас, пока First-Agent в research-фазе, человек ревьюит
  PR'ы. Используем это окно, чтобы заложить механику и не зависеть от
  ревью, когда выйдем из фазы.
- **Obsidian graph view.** Для нас визуальный граф не нужен — агенту
  нужен *tool* для traversal'а, не картинка.

### 5.3. Что уникально для агентов и чего нет в критике

- **Procedural memory уникальна для агента.** У человеческого wiki
  процедура = «как я обычно делаю X» — заметка в тексте. У агента
  процедура = **исполнимый SKILL**, тестируемый, версионируемый. См.
  [`agent-roles.md`](./agent-roles.md) — у нас уже есть слот «skills →
  skill.md → shell-вызов» из разбора graphify.
- **Episodic memory уникальна для агента.** Лог сессий (что делал, что
  сработало, что нет) — наш аналог того, что Карпатый зовёт `log.md`,
  но с добавкой reflexion: какие выводы сделаны, что войдёт в semantic
  memory. Это паттерн из Reflexion (Shinn et al. 2023), уже
  зафиксированный у нас в agent-roles (Critic role).

---

## 6. Что брать, что не брать

### 6.1. Берём (sound, proven, актуально для v0.1)

| # | Идея | Источник | Куда |
|---|---|---|---|
| T1 | **Provenance-frontmatter** на каждой заметке в `knowledge/research/`: `source`, `compiled`, `chain_of_custody`, `claims_requiring_verification` | Kumar | [`knowledge/README.md`](../README.md), [template](#template-provenance-frontmatter) ниже |
| T2 | **Стратификация корпуса.** Стабильное (архитектура, ADR, паттерны) vs volatile (заметки сессий, логи). Разная политика синтеза. | Kumar | [`docs/architecture.md`](../../docs/architecture.md) §Архитектура памяти |
| T3 | **Supersession вместо silent overwrite.** Когда заметка заменяется — старая уходит в `> Status: superseded by …`, новая линкуется. | Lahoti, Kumar, rohitg00 | Уже частично есть в [`knowledge/README.md §Conventions`][knw-readme] — доусилить |
| T4 | **Cognitive-taxonomy mapping** нашей 4-слойной памяти на working/episodic/semantic/procedural. Не меняет структуру, меняет *язык* — в будущих ADR это облегчит решения. | rohitg00, Park 2023, MemGPT | `docs/architecture.md` §Архитектура памяти (таблица) |
| T5 | **Доступ — search, не load.** Для будущего модуля памяти: никогда не грузим весь `knowledge/` в контекст; всегда search → fetch(section). | Gravelle, Karpathy (qmd), Liu et al. 2024 | ADR-тема для `knowledge/adr/` (пока — как принцип в architecture.md) |
| T6 | **Routing-раздел в `AGENTS.md`.** Явно: «если вопрос про архитектуру — смотри `docs/architecture.md`; если про решение — `knowledge/adr/`; если про research — `knowledge/research/`». Не стиль, а поиск. | Kumar | [`AGENTS.md`](../../AGENTS.md) — добавить секцию |
| T7 | **Schema как продукт.** Принять: `AGENTS.md` и `knowledge/README.md` — это *первоклассные артефакты*, а не комментарии. Эволюционируют через PR как код. | rohitg00, ChavesLiu | Уже принято де-факто; зафиксировать в `knowledge/README.md` |

[knw-readme]: ../README.md

### 6.2. Заглядываем (позже, может понадобиться)

| # | Идея | Когда |
|---|---|---|
| L1 | **Confidence scoring** на фактах | Когда `knowledge/research/` превысит ~30 заметок и ручной аудит станет дорогим |
| L2 | **Typed knowledge graph** | Когда понадобится «покажи всё, от чего зависит модуль X» — не раньше первого модуля |
| L3 | **Hybrid BM25 + vector + graph search** | Когда `index.md`/README-списки перестанут помещаться в контекст |
| L4 | **Retention decay** для episodic memory | Когда лог сессий перестанет быть обозримым |
| L5 | **Crystallization** (end-of-session auto-digest) | После первой серии реальных сессий с агентом — когда будет что дистиллировать |
| L6 | **Write-governance multi-agent** с conflict-файлами | Когда регулярно появятся параллельные сессии, пишущие в пересекающиеся зоны |

### 6.3. Не берём (сомнительно / преждевременно / не наше)

| # | Идея | Почему нет |
|---|---|---|
| N1 | Ebbinghaus-exponential decay как формула | Метафора, не измерение; heuristic хватит |
| N2 | jDocMunch как «решение» | Конкретный vendor, своя MCP-зависимость; если понадобится поиск — возьмём qmd или ripgrep+FAISS, не привяжемся |
| N3 | Self-healing lint, автоматически *меняющий* заметки | Усиливает ровно ту проблему, от которой лечится (LLM-авторство без ревью). В нашем workflow лечит PR-ревью. |
| N4 | Автоматический contradiction resolver | Слишком много ложных срабатываний; до v0.2 — только human-reviewed |
| N5 | «LLM Wiki убивает RAG» (коллективный тезис твиттера-2026) | Ложная дихотомия; наш подход — hybrid с явным routing |
| N6 | Native knowledge-graph до v0.1 | YAGNI до первого модуля |

---

## 7. Как это сочетается с `agent-roles.md`

Прямые пересечения с minimum role set v0.1 из
[`agent-roles.md`](./agent-roles.md):

- **Critic (Reflexion-style).** Главный бенефициар: после каждой сессии
  Critic обязан не только оценить решение, но и **предложить, что
  сохранить в `knowledge/`**, в каком слое (stable/volatile), с
  каким frontmatter'ом. Это расширение роли, не новая роль.
- **Executor.** При чтении `knowledge/` обязан *уважать chain_of_custody*:
  если заметка помечена «query raw source for specific claims», он идёт
  в raw (в нашем случае — в `docs/` или первоисточник). То есть в
  промпте Executor'а появится строка «follow chain_of_custody frontmatter,
  do not cite summary pages as authoritative for specific claims».
- **Planner / Task Specifier.** Без изменений — они работают на input'е
  пользователя, не на `knowledge/`.

Новых ролей *не добавляем*. Добавится обязанность у Critic и ограничение
у Executor.

---

## 8. Engelbart как фрейм (не спецификация)

Самая ценная часть Engelbart'а для нашего проекта — не OHS-сертификации,
а **bootstrapping-петля**. Применительно к First-Agent она звучит так:

> Агент, который мы строим, должен быть способом улучшать собственные
> промпты, собственную память и собственные скиллы. Если мы собираем
> систему, которая работает **над** агентом, а не **вместе с ним** — мы
> застреваем в ручной поддержке той самой «bookkeeping», которую Karpathy
> предлагал автоматизировать.

Конкретная переводимая импликация — одна, но важная:

- **Bootstrapping как non-goal v0.1.** Это мишень, а не фича первого
  модуля. Но каждое решение в `knowledge/` нужно проверять вопросом:
  «А можно ли это решение в будущем доверить самому агенту?». Если ответ
  «нет, никогда» — скорее всего, мы закрепили ручное обязательство за
  человеком без необходимости.

В OHS Framework есть интересный technical-детал — **typed links между
абзацами**, не между файлами. Это усиливает аргумент rohitg00 за
typed graph (§6.2, L2), но не меняет приоритет.

---

## 9. Конкретные правки в существующие файлы

Этот раздел — **исполняемая часть**: что именно меняется в репо в рамках
PR с этой заметкой (помимо добавления самих трёх файлов).

### 9.1. `docs/architecture.md` — секция «Архитектура памяти»

- Добавить **cognitive-taxonomy-колонку** к уже существующей таблице
  (session / persistent / procedural / episodic → working / semantic /
  procedural / episodic).
- Добавить **subsection «Provenance и chain of custody»** (10–15 строк)
  — принцип, применимый к персистентной памяти.
- Добавить **subsection «Стабильное vs volatile знание»** (10–15 строк)
  — политика синтеза, со ссылкой на данную заметку.

### 9.2. `knowledge/README.md` — conventions

- Расширить раздел «Conventions» frontmatter-схемой для заметок в
  `research/` (поля `source`, `compiled`, `chain_of_custody`,
  `claims_requiring_verification`).
- Усилить пункт supersession: «never silently overwrite; old content →
  `> Status: superseded by …` + link».
- Добавить короткую подсекцию «Routing» — где искать разный тип знания.

### 9.3. `AGENTS.md` — routing-section

- Добавить раздел **«Query Routing»**: какие вопросы к каким
  директориям.
- Добавить правило **chain-of-custody**: если в ответе участвует
  конкретная цифра/дата/решение — идти в первоисточник (gist, статью,
  код) и цитировать *оттуда*, а не из summary-заметки.

### 9.4. Принцип «search, not load» (T5)

Это пока не код — принципа достаточно в architecture.md. Когда появится
модуль памяти (README шаг 5), он пойдёт как ADR: «knowledge-access =
search-then-fetch, never materialize».

---

## Template: provenance-frontmatter

Применяется к заметкам в `knowledge/research/` и к будущим
summary-заметкам, которые агент будет писать сам.

```yaml
---
title: "<title>"
source:
  - "<url or repo path>"
  - "<url or repo path>"
compiled: "<YYYY-MM-DD>"
chain_of_custody: "<короткая строка: где искать первоисточник
  для конкретных фактов>"
claims_requiring_verification:
  - "<claim 1>"
  - "<claim 2>"
superseded_by: "<path to replacement, if any>"
---
```

Поле `source` — обязательное. Остальные — при необходимости.
`chain_of_custody` обязателен, если заметка синтезирует несколько источников
и/или содержит числа/даты/имена, на которые кто-то может сослаться.
