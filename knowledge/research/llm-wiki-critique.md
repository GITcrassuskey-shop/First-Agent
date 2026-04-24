---
title: "Research — Критика Karpathy's LLM Wiki и выводы для First-Agent"
source:
  - "https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f"
  - "https://foundanand.medium.com/the-hidden-flaw-in-karpathys-llm-wiki-e3a86a94b459"
  - "https://dev.to/jgravelle/a-radical-diet-for-karpathys-token-eating-llm-wiki-59ng"
  - "https://ranjankumar.in/llm-wiki-synthesis-time-decision-rag-agentic-memory"
  - "https://github.com/ChavesLiu/second-brain-skill/blob/main/README.en.md"
  - "https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2"
  - "https://www.dougengelbart.org/content/view/110/460/"
compiled: "2026-04-24"
chain_of_custody: >
  For any specific claim (numbers, exact wording, benchmark results,
  directory layouts), cite the original URL listed in `source:`.
  Karpathy's gist and the critique posts are the authoritative texts —
  this note summarizes and critiques, it is not a source of truth for
  their specifics.
claims_requiring_verification:
  - "jDocMunch benchmark numbers (19.9× / 95%)"
  - "qmd feature list (BM25 + vector + LLM rerank, MCP server)"
  - "Karpathy-reported wiki scale (~100 articles, 400K words)"
---

# Research — Критика Karpathy's LLM Wiki и выводы для First-Agent

> **Статус:** research note, 2026-04-24.
> **Scope:** разобрать критику [LLM Wiki-паттерна Карпатого][k-gist] (апрель
> 2026) и извлечь то, что применимо к *памяти/знанию* нашего собственного
> агента — не к персональной вики пользователя.
>
> **Важное уточнение о preconditions.** Пользователь в постановке задачи
> сообщил, что в репо «уже есть знание из оригинального LLM Wiki gist». По
> факту в репо **нет прямых заимствований из gist'а Карпатого** (`grep`
> по `knowledge/` + `docs/` по ключам `karpathy|llm.?wiki|second.?brain|engelbart`
> даёт 0 совпадений содержания). Поэтому документ **не обновляет
> существующее «знание из gist»**, а **добавляет новое**: критический
> разбор паттерна + выводы, которые точечно применимы к уже
> зафиксированным у нас вещам (трёхслойная архитектура агента в
> [`docs/architecture.md`](../../docs/architecture.md) и память проекта
> в [`knowledge/`](../README.md)).
>
> **Связь с текущей фазой.** Наш этап — «создать роли агента»
> ([`agent-roles.md`](./agent-roles.md)). Этот документ не про роли; он про
> **субстрат**, на котором работают роли — персистентное знание агента.
> Пересечение одно: роль *Critic* получает дополнительный материал (см.
> §7).

[k-gist]: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

---

## 0. TL;DR

1. **Паттерн Карпатого — компиляция знаний** (raw-source → LLM-writer →
   wiki-pages → index.md) — *корректен на персональной шкале* (до ~100
   страниц, один ревьюер) и некорректен «в лоб» для команд и для **памяти
   автономного агента**. У всех трёх авторов-критиков один и тот же
   диагноз, просто под разными именами.
2. **Основной дефект — размытая chain of custody.** LLM-написанные
   summary индексируются наравне с первоисточниками; через серию
   перезаписей summary становится «источником», а оригинал перестаёт
   запрашиваться. Это *не* традиционная RAG-галлюцинация: системы,
   сверяющие wiki↔wiki, не видят рассинхрон wiki↔source. Пример с
   «2 %-дисконтом по контракту» (Lahoti / Kumar) иллюстративен, но
   структурно — это знакомый «эффект каскадного пересказа».
3. **Второй дефект — token-scaling.** `index.md` как основной
   навигационный объект ломается на ~50–100K токенов (это согласуется с
   известной деградацией long-context моделей — «lost in the middle», Liu
   et al. 2024). Решение: не **грузить** wiki, а **искать** по ней. Gist
   Карпатого это, кстати, прямо признаёт: «past a few hundred pages —
   возьми qmd» (гибридный BM25+vector поиск). Часть критики Gravelle — это
   straw-man поверх того, что и так сказано.
4. **Что хорошего в критике.** Она формализует три вещи, которых в
   исходном паттерне нет: (a) **синтез-тайм** как архитектурное решение
   (ingest-time vs query-time), (b) **стратификация корпуса** по
   стабильности, (c) **provenance-метаданные** (source, confidence,
   superseded_by). Это переводится в прямые рекомендации по
   `knowledge/`-слою нашего агента.
5. **Что сомнительно.** «Query-time всегда побеждает на большой шкале»
   (Lahoti) — абсолютизм; нужен гибрид. jDocMunch-бенчмарк (Gravelle) —
   корпоративный, сравнивается со **страшилкой** (загрузить весь wiki в
   контекст), которую Карпатый сам не рекомендует. Цифры 19.9× —
   маркетинговые. Экспоненциальная Ebbinghaus-decay (rohitg00) —
   метафора, а не измеренная механика для KB.
6. **Engelbart (1998, OHS Framework)** — не про вики и не про LLM, а про
   **open hyperdocument system** с типизированными объектами,
   адресуемыми на уровне абзаца/элемента, и про *bootstrapping* — тулы
   улучшают тулы. Для нас это философский якорь, не спецификация; его
   влияние ограничено §8 ниже.
7. **Что тащим в First-Agent** — см. §9 (приоритизированный список).
   Ключевые: provenance-frontmatter на заметках в `knowledge/`, явное
   разделение «stable vs volatile» в памяти агента, supersession вместо
   перезаписи, и *routing-раздел* в `AGENTS.md`.

---

## 1. Что такое оригинальный LLM Wiki Карпатого (факты)

Нужно зафиксировать исходную спецификацию, иначе критику нельзя оценить.
Ниже — прямые цитаты из [gist'а][k-gist] без интерпретации.

**Суть паттерна (цитата):** «Instead of just retrieving from raw documents
at query time, the LLM **incrementally builds and maintains a persistent
wiki** — a structured, interlinked collection of markdown files that sits
between you and the raw sources.»

**Архитектура — три слоя:**

- `raw/` — immutable source documents, LLM только читает.
- `wiki/` — LLM-generated markdown, LLM *единолично* пишет и
  поддерживает.
- `schema` — файл типа `CLAUDE.md` / `AGENTS.md`: конвенции, формат
  страниц, workflow для ingest/query/lint.

**Операции:**

- **Ingest.** Новый source → LLM читает → пишет summary + обновляет
  10–15 связанных страниц → обновляет `index.md` и `log.md`.
- **Query.** Читать `index.md` → найти релевантные страницы →
  синтезировать ответ с цитатами. «Good answers can be filed back into the
  wiki as new pages» — явное разрешение петли **вики ест свои выходы**.
- **Lint.** Periodic health-check: противоречия, stale claims, orphan
  pages, недостающие cross-references.

**Навигация — два spec-файла:**

- `index.md` — content-oriented каталог, LLM обновляет на каждом ingest.
- `log.md` — chronological append-only: ingest/query/lint с префиксами.

**Масштаб по словам автора.** «Работает сюрприз-хорошо на moderate scale
(~100 sources, сотни страниц) и избавляет от embedding-based RAG
infrastructure». Явный потолок.

**Что он сам признаёт:**

- «At some point you may want to build small tools» → упоминает
  [qmd][qmd] (Tobi Lütke) — **гибридный BM25/vector search с LLM
  re-ranking** как MCP-сервер. То есть **автор изначально допускает
  переход в RAG** на больших шкалах.
- «This document is intentionally abstract. It describes the idea, not a
  specific implementation.» — явное self-caveat: это **идея-файл**, не
  prod-спецификация.
- Ссылка на Vannevar Bush's Memex (1945) как идейного предка.

[qmd]: https://github.com/tobi/qmd

Без этих двух признаний большая часть критики превращается в
«нашли у спецификации то, чего спецификация сама не утверждает».

---

## 2. Источники — что говорят авторы

### 2.1. Anand Lahoti — «The Hidden Flaw» ([Medium][s-lahoti])

**Тезис.** LLM-авторская прозы, проиндексированная наравне с raw, создаёт
**knowledge base poisoning**: суммарные статьи становятся источниками,
ссылаются друг на друга, lint-проход проверяет только
internal consistency. Ground truth постепенно отваливается, и *это нельзя
детектировать изнутри системы*.

**Иллюстрация.** Контракт: «net-30, 2% discount if paid within 10 days».
LLM пишет summary-страницу: «standard agreements use net-30 with
early-payment discounts». 2%/10 дней теряются. Через полгода связанная
страница *Vendor Agreements* тоже пишется без процента. Lint: обе
страницы согласованы между собой → проходит. Contract всё ещё в raw/, но
его никто не запрашивает.

**Предлагает.** Жёстко разделить **write-time synthesis** (ingest-time,
Карпатый) и **query-time synthesis** (RAG классический). Для команд —
только query-time. LLM при ingest извлекает **структуру** (сущности,
связи, tagging с source span), но **не пишет прозу как источник**.

**Что сильно.** Диагноз точный. Механика дрейфа описана правдоподобно и
без эзотерики. Не требует доверия к конкретным цифрам.

**Что слабо.** «Write-time всегда проигрывает на team scale» —
абсолютизация. В реальности: архитектура компилируется один раз ревьюером,
контракты — никогда. Хороший compromise есть в работе Kumar (см. ниже).

[s-lahoti]: https://foundanand.medium.com/the-hidden-flaw-in-karpathys-llm-wiki-e3a86a94b459

### 2.2. J. Gravelle — «A Radical Diet» ([dev.to][s-gravelle])

**Тезис.** Ошибка — **паттерн доступа**, а не структура. Пользователи
грузят весь wiki (или хотя бы `index.md`) в контекст, потому что так
«проще». Это ломается на ~50–100K токенов; long-context модели
деградируют на ~200–300K. Фикс: не загружать, а **искать** — как в базе
данных.

**Цифры.** Автор продвигает свой инструмент jDocMunch (MCP-сервер для
поиска по секциям markdown): 1,874 vs 37,245 токенов, reduction 95%,
ratio 19.9×.

**Что сильно.** Принцип верен и подтверждается литературой:
- «Lost in the Middle» ([Liu et al., 2024][paper-lost-middle]) —
  деградация attention у моделей при длинном контексте.
- Любая зрелая RAG/indexing-библиотека (LlamaIndex, Weaviate, Haystack)
  годами делает ровно это: search-then-fetch, без materialization.

**Что слабо.**
- **Straw-man.** Baseline — «load full wiki» — это **не** то, что
  Карпатый рекомендует. Gist прямо указывает на qmd (search) past 100
  pages. 19.9× «reduction» сравнивает правильный паттерн с вариантом,
  который автор паттерна сам отговаривает.
- **Vendor benchmark.** 7-page corpus, 5 queries. Методика не опубликована
  в воспроизводимом виде.
- **Промо.** Последняя треть поста — инсталляция jDocMunch. Это нормально
  для dev.to, но учитывать при взвешивании.

**Что берём.** Тезис «wiki — это датасет, не документ» + «cost ∝ answer
complexity, not wiki size» — это именно то, как должна работать
**память агента**. Наше — §9.4.

[s-gravelle]: https://dev.to/jgravelle/a-radical-diet-for-karpathys-token-eating-llm-wiki-59ng
[paper-lost-middle]: https://arxiv.org/abs/2307.03172

### 2.3. Ranjan Kumar — «Synthesis-Time Decision» ([ranjankumar.in][s-kumar])

Самая проработанная из трёх критик. Явно фиксирует **Synthesis Horizon** —
масштаб, после которого ingest-time модель ломается структурно (индекс не
помещается в контекст → ingest не может определить, какие страницы
обновлять → ошибки компаундятся быстрее, чем их ловит lint).

**Ключевая идея — corpus-stratified synthesis.** Одному корпусу одну
политику не выбирают. Стратифицируем:

| Слой | Что туда кладём | Synthesis time |
|---|---|---|
| `wiki/architecture/` | стабильное: архитектурные решения, ADR | ingest-time (компилируется один раз, ревьюер) |
| `wiki/concepts/` | стабильное: глоссарий, паттерны | ingest-time |
| `raw/contracts/` | authoritative: контракты, легал, финансы | query-time, цитируются дословно |
| `raw/meeting-notes/` | dynamic: протоколы | query-time |

**Routing layer в schema-файле** (`CLAUDE.md` / `AGENTS.md`) становится
отдельной обязанностью: классифицировать вопрос → направить к нужному
корпусу. Правило цепочки: «если в ответе участвует конкретное число/дата/
процент, всегда верифицируй против `raw/`, даже если в wiki есть значение».

**Provenance-frontmatter.** У wiki-страницы:

```yaml
---
title: "Payment Terms — Compiled Overview"
source: "raw/contracts/vendor-master-2025.pdf"
compiled: "2026-03-15"
chain_of_custody: "DO NOT USE for specific amounts or deadlines — query raw source"
claims_requiring_verification:
  - "Early payment discount percentage"
  - "Payment due dates"
---
```

**Write-governance для multi-agent/multi-session.** Explicit rules: не
перезаписывать страницу силenter, старое содержимое → в `history/` с
`superseded_by` + timestamp; противоречия → отдельный `conflicts/` файл
для человеческого разбора.

**Что сильно.** Всё конструктивно: каждый пункт — прямая спецификация.
Цитируется DokuWiki-автор Gutmans с точным вопросом про атрибуцию правок
в multi-agent среде — валидная проблема, которую Lahoti только намечает.

**Что слабо.** «Cross the horizon → degrades to RAG without governance RAG
provides» — немного кликбейтно. RAG-фреймворки governance-инструментов
сами по себе не дают; их тоже надо настраивать. Но главный thrust —
верный.

[s-kumar]: https://ranjankumar.in/llm-wiki-synthesis-time-decision-rag-agentic-memory

### 2.4. ChavesLiu — `second-brain-skill` ([GitHub][s-chaves])

Это **не критика**, а имплементация-референс: упаковка паттерна Карпатого
в Claude Code Skill. Слэш-команды (`/wiki init`, `/wiki ingest`, `/wiki
query`, `/wiki lint`, `/wiki wipe`). Natural-language-mode: «ingest this
article» → автоматически запустит `ingest`.

**Полезное для нас.** Конкретная директорная раскладка `wiki/`:

```text
wiki/
├── index.md
├── log.md
├── overview.md
├── conventions.md
├── sources/
├── entities/
├── concepts/
└── analyses/
```

«`conventions.md` — your preferences» — отдельный файл для пользовательских
настроек вики, отделён от `CLAUDE.md`/`AGENTS.md` (технические
конвенции). Полезное разделение.

**Чего там нет.** Ни одного из улучшений из §2.1–2.3. Это именно
«packaging», а не эволюция.

[s-chaves]: https://github.com/ChavesLiu/second-brain-skill/blob/main/README.en.md

### 2.5. rohitg00 — «LLM Wiki v2» ([gist, форк][s-rohit])

Самое объёмное расширение. Не критика по тону — «everything in the
original still applies», но добавляется восемь систем:

1. **Memory lifecycle.**
   - **Confidence scoring** — у каждого факта счётчик источников и дата
     последнего подтверждения.
   - **Supersession** — новый факт явно замещает старый с timestamp,
     старое не удаляется а помечается stale.
   - **Forgetting** — Ebbinghaus exponential decay: редко-используемые
     факты deprioritized.
   - **Consolidation tiers:** working → episodic → semantic → procedural.
     Факт *повышается* по мере накопления подтверждений.
2. **Knowledge graph поверх pages.** Типизированные сущности (person,
   project, library, concept, file, decision), типизированные связи
   («uses», «depends on», «contradicts», «caused», «fixed», «supersedes»).
3. **Hybrid search.** BM25 + vectors + graph traversal, слияние через
   reciprocal rank fusion. `index.md` остаётся как human-readable каталог,
   но не primary LLM search.
4. **Automation hooks** (event-driven): on-new-source, on-session-start
   (инжект релевантного контекста), on-session-end (compress observations),
   on-query (file-back threshold), on-memory-write (contradiction check),
   on-schedule (periodic lint/consolidation/retention decay).
5. **Quality & self-correction.** Score на каждом LLM-написанном куске;
   self-healing lint (не предлагает, а чинит, что может); contradiction
   resolution с автоматическим предложением победителя (newer source /
   authority / support count).
6. **Multi-agent mesh sync** + shared/private scoping.
7. **Privacy/governance.** Filter-on-ingest для PII; audit trail для всех
   операций; bulk ops с reversal.
8. **Crystallization.** Конец research-сессии → автоматически
   дистиллирован в структурированный digest (question / findings / entities
   involved / lessons) и включается в базу как first-class source.

**Что сильно.**
- Когнитивная таксономия памяти (working/episodic/semantic/procedural) —
  общее место в agent-literature: Generative Agents ([Park et al. 2023][p-park]),
  MemGPT ([Packer et al. 2023][p-memgpt]), Reflexion ([Shinn et al. 2023][p-reflexion]).
  Использовать как framing-device — легитимно.
- Hybrid search + RRF — state-of-practice, реализовано в Weaviate,
  Elasticsearch, LlamaIndex.
- Supersession / confidence — воспроизводит patterns из Truth Maintenance
  Systems (Doyle 1979) и TMS в классическом ИИ.

**Что слабо.**
- Экспоненциальный Ebbinghaus-decay для KB — **метафора**, не
  измеренная механика. У Эббингауза кривая про заучивание бессвязных
  слогов людьми. Перенос на «architecture decisions decay slowly, transient
  bugs decay fast» — интуитивно звучит, но ни одна цитата этого не
  измеряет для KB. В v0.1 — брать как эвристику, не как формулу.
- Продвижение *agentmemory* — коммерческого продукта. Текст его не
  скрывает, и принципы ценны и без него, но стоит помнить.
- «Всё автоматизировать» — классический build-up на ровном месте. Для
  v0.1 агента автоматизация нужна для 1–2 хуков, не для восьми.

[s-rohit]: https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2
[p-park]: https://arxiv.org/abs/2304.03442
[p-memgpt]: https://arxiv.org/abs/2310.08560
[p-reflexion]: https://arxiv.org/abs/2303.11366

### 2.6. Douglas Engelbart — OHS Framework, 1998 ([dougengelbart.org][s-engelbart])

**Контекст.** Engelbart — автор «Augmenting Human Intellect» (1962) и
демо «The Mother of All Demos» (1968, прототипы мыши, hypertext,
real-time collaborative editing). «OHS Framework» — 1998, с соавторами
Harvey Lehtman и Christina Engelbart. Документ — иерархическая
спецификация **Open Hyperdocument System**:

- **Elementary objects** — атомарные единицы (текст, графика, формулы,
  код). Адресуемы по любой гранулярности, не только по файлу.
- **Mixed-object documents** — документы как coherent bundles разнородных
  объектов (ср. MIME).
- **Shared objects** — объекты, доступные для backlinking из других
  документов.
- **Typed links** — ссылки с типом отношения, не только URL.
- **Bootstrapping Community** — люди и тулы сами улучшают собственные
  тулы для улучшения собственных тулов. Эволюция «знание → тул → знание»
  как первоклассный процесс.

**Что из этого применимо к LLM Wiki-дискуссии.**
- **Typed links / typed relationships** — ровно то, что rohitg00
  предлагает под именем «knowledge graph». Engelbart зафиксировал это за
  28 лет до LLM Wiki.
- **Fine-grained addressing.** Engelbart требует адресуемости на уровне
  абзаца/объекта, не только файла. Современные MCP-серверы поиска по
  секциям (qmd, jDocMunch) это же и делают.
- **Bootstrapping.** Наиболее важный философский тезис для First-Agent:
  агент должен **улучшать свою собственную память и свои собственные
  промпты**. Это выходит за рамки памяти как склада; память становится
  результатом работы самого агента, меняющим его же поведение.

**Что неприменимо.** OHS Framework — 1998, не предполагал LLM-writer в
петле. Проблемы chain-of-custody / drift у него нет, потому что не было
автора, который генерирует текст поверх других текстов. Engelbart —
**фрейм**, не решение конкретно наших проблем.

[s-engelbart]: https://www.dougengelbart.org/content/view/110/460/

---

## 3. Кросс-резка: единая картина критики

У трёх критик (Lahoti, Gravelle, Kumar) один диагноз и три разных имени:

| Имя | Автор | О чём |
|---|---|---|
| Knowledge base poisoning | Lahoti | LLM-summary индексируется как источник; source drift |
| Token-bloat / index-bottleneck | Gravelle | Доступ «загрузи wiki» не масштабируется |
| Synthesis Horizon + chain-of-custody fracture | Kumar | Обобщение: где происходит синтез, и где теряется provenance |

Совпадение — не случайность. Все трое указывают на **одну и ту же пару
обязательств паттерна**:

1. **Provenance.** Каждый факт должен уметь показать свой источник на
   уровне конкретного span'а.
2. **Доступ по запросу, не по загрузке.** Размер артефакта не должен
   линейно влиять на стоимость одного вопроса.

Эти обязательства — *имплицитно* в gist'е Карпатого (он упоминает
source citations и рекомендует qmd для поиска), но не зафиксированы как
first-class обязанности схемы. В результате реализации паттерна в
большинстве случаев этих двух обязательств не соблюдают.

---

## 4. Фактчек

### 4.1. Что верно

- **Деградация long-context моделей реальна.** «Lost in the Middle» (Liu
  et al., 2024) подтверждает: recall теряется в середине длинного
  контекста. Это не «ничего не работает» — это «качество падает не
  линейно». Эффект хорошо воспроизводится.
- **Karpathy действительно описывает ~100 sources, 400K слов** — это
  цитируется Lahoti и Kumar, и подтверждается gist'ом (автор явно пишет
  «moderate scale, ~100 sources, hundreds of pages»).
- **qmd реально существует** ([github.com/tobi/qmd][qmd]), сделан
  Tobi Lütke, описан как hybrid BM25/vector search с LLM re-ranking и
  MCP-интерфейсом. Связка «wiki past 100 pages → qmd» — в самом gist'е.
- **Ingest реально трогает 10–15 страниц** — цитируется Kumar как
  утверждение Карпатого; в gist'е **буквально** стоит «a single source
  might touch 10-15 wiki pages».
- **Knowledge graph + typed relationships** — классика ИИ. Ссылки на
  Engelbart (typed links), DBpedia, WordNet, семантический веб. Engelbart
  как самый ранний источник — корректен.
- **Working/episodic/semantic/procedural memory** — стандартная
  таксономия из CogSci (Tulving, Atkinson-Shiffrin). Применение к LLM
  agent memory — стандартная практика (Generative Agents, MemGPT,
  Voyager).

### 4.2. Что сомнительно или overstated

- **«Query-time always wins at team scale» (Lahoti).** Overclaim.
  На практике архитектурная документация прекрасно компилируется один раз
  с ревью человеком; контракты — да, query-time. Kumer это и исправляет
  через стратификацию — но у самого Lahoti тезис звучит как absolutism.
- **jDocMunch-цифры 95% / 19.9× (Gravelle).** Нерепрезентативны. Baseline
  «загрузить весь wiki» — тот baseline, который Карпатый сам отговаривает.
  Правильный baseline был бы: «Карпатовский wiki + qmd поверх». По такому
  сравнению никаких 19.9× мы бы не увидели — оба подхода делают
  search-then-fetch, разница была бы в деталях реализации.
- **Ebbinghaus-decay для KB-фактов (rohitg00).** Метафора, не измерение.
  Применять как *эвристику* можно («decay = f(time, reinforcement)»), но
  не как «исторически валидированная экспонента».
- **«Shumailov model collapse → wiki drift» — расхожий, но неточный
  аналог.** Shumailov et al. (Nature 2024) о **training** на
  рекурсивно-генерируемых данных. В LLM Wiki нет дообучения — только
  retrieval. Структурная аналогия валидна (feedback loop ест свои
  выходы), но это не «тот же самый эффект».
- **«LLM Wiki — это современный Engelbart».** Верно лишь частично.
  Engelbart требовал типизации и fine-grained addressing, которых в
  исходном Wiki-паттерне нет. Критики, требующие типизированного графа
  (rohitg00) и routing (Kumar), на самом деле ближе к Engelbart'у, чем
  сам gist.

### 4.3. Чего критики не замечают

- **У паттерна есть важная честная оговорка «this is an idea file».**
  Никто из трёх критиков этого явно не цитирует. Часть критики ломится в
  открытую дверь.
- **Карпатый специально пишет «personal» во всех примерах.** Его кейсы —
  persistent **personal** knowledge base. Lahoti/Kumar честно расширяют на
  team, но их критика справедлива *к экстраполяции*, не к original
  claim'у.
- **Human-in-the-loop как часть дизайна.** В gist'е прямо: «I have the
  LLM agent open on one side and Obsidian open on the other. The LLM
  makes edits based on our conversation, and I browse the results in real
  time — following links, checking the graph view». Ревью не опциональное
  — оно часть паттерна. Критика «drift незаметен» относится к setup'ам,
  где это ревью выкинули.

---

## 5. Применимость к **памяти LLM-агента**, а не к wiki для человека

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
  Память агента растёт по *каждой сессии* — быстрее и с большим долем
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
  [`agent-roles.md §3.2`](./agent-roles.md) — у нас уже есть слот
  «skills → skill.md → shell-вызов» из разбора graphify.
- **Episodic memory уникальна для агента.** Лог сессий (что делал, что
  сработало, что нет) — наш аналог того, что Карпатый зовёт `log.md`, но
  с добавкой reflexion: какие выводы сделаны, что войдёт в semantic
  memory. Это паттерн из [Reflexion (Shinn et al. 2023)][p-reflexion],
  уже зафиксированный у нас в agent-roles (Critic role).

---

## 6. Что брать, что не брать

Сведу всё в три списка.

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

### 6.2. Заглядываем (позже, может понадобится)

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
| N6 | Native knowledge-graph граф до v0.1 | YAGNI до первого модуля |

---

## 7. Как это сочетается с `agent-roles.md`

Прямые пересечения с [minimum role set v0.1][roles-v01]:

- **Critic (Reflexion-style).** Главный бенефициар: после каждой сессии
  Critic обязан не только оценить решение, но и **предложить, что
  сохранить в `knowledge/`**, в каком слое (stable/volatile), с
  каким frontmatter'ом. Это расширение роли, не новая роль.
- **Executor.** При чтении `knowledge/` обязан *уважать chain_of_custody*:
  если заметка помечена «query raw source for specific claims», он идёт в
  raw (в нашем случае — в `docs/` или первоисточник). То есть в промпте
  Executor'а появится строка «follow chain_of_custody frontmatter, do not
  cite summary pages as authoritative for specific claims».
- **Planner / Task Specifier.** Без изменений — они работают на input'е
  пользователя, не на `knowledge/`.

Новых ролей *не добавляем*. Добавится обязанность у Critic и ограничение
у Executor.

[roles-v01]: ./agent-roles.md#5-набор-ролей-для-first-agent

---

## 8. Engelbart как фрейм (не спецификация)

Самая ценная часть Engelbart'а для нашего проекта — не OHS-сertификации,
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

Этот раздел — **исполняемая часть**: что именно я меняю в репо в рамках
этого PR (помимо добавления данной заметки).

### 9.1. `docs/architecture.md` — секция «Архитектура памяти»

- Добавить **cognitive-taxonomy-колонку** к уже существующей таблице
  (session / persistent / procedural / episodic → working / semantic /
  procedural / episodic).
- Добавить **subsection «Provenance и chain of custody»** (10–15 строк) —
  принцип, применимый к персистентной памяти.
- Добавить **subsection «Стабильное vs volatile знание»** (10–15 строк)
  — политика синтеза, со ссылкой на данную заметку.

### 9.2. `knowledge/README.md` — conventions

- Расширить раздел «Conventions» frontmatter-схемой для заметок в
  `research/` (поля `source`, `compiled`, `chain_of_custody`,
  `claims_requiring_verification`).
- Усилить пункт supersession: «never silently overwrite; old content
  → `> Status: superseded by …` + link».
- Добавить короткую подсекцию «Routing» — где искать разный тип
  знания.

### 9.3. `AGENTS.md` — routing-section

- Добавить раздел **«Query Routing»**: какие вопросы к каким директориям.
- Добавить правило **chain-of-custody**: если в ответе участвует
  конкретная цифра/дата/решение — идти в первоисточник (gist, статью,
  код) и цитировать *оттуда*, а не из summary-заметки.

### 9.4. Принцип «search, not load» (T5)

Это пока не код — принципа достаточно в architecture.md. Когда появится
модуль памяти (§memory-research, README шаг 5), он пойдёт как ADR:
«knowledge-access = search-then-fetch, never materialize».

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

---

## 10. Открытые вопросы

Чтобы не повторять паттерн «вики поглощает источники», фиксирую вопросы
*без* ответов:

1. **Где граница volatile / stable для нашего проекта?** Прямо сейчас:
   `knowledge/adr/` — stable; `knowledge/research/` — semi-stable (обновляется
   при significant findings); логи сессий пока нет. Нужен ли нам отдельный
   слой `knowledge/episodic/` или `knowledge/sessions/` для сырых
   session-digest'ов?
2. **Как решаем, что заметка устарела?** Сейчас — субъективно. Нужен ли
   явный цикл review (квартальный? per-module?) или триггер-based (когда
   ссылающаяся ADR меняется)?
3. **Где Critic (роль из `agent-roles.md`) пишет свои digest'ы?**
   Отдельный файл на сессию? Append к `log.md`? Решать при
   проектировании роли — сейчас просто регистрирую вопрос.
4. **Переход на qmd-like поиск — когда и на чём?** Не ранее первого
   модуля памяти. Триггер: README.md / index'ы перестают помещаться в
   контекст одной сессии.

---

## Sources

Критика и расширения:

- [s-lahoti]: Anand Lahoti. *The Hidden Flaw in Karpathy's LLM Wiki*.
  Medium, 2026-04 — [foundanand.medium.com][s-lahoti]
- [s-gravelle]: J. Gravelle. *A Radical Diet for Karpathy's Token-Eating
  LLM Wiki*. dev.to, 2026-04-12 — [dev.to][s-gravelle]
- [s-kumar]: Ranjan Kumar. *LLM Wiki Is Not a RAG Replacement — It's a
  Synthesis-Time Decision*. 2026-04-20 — [ranjankumar.in][s-kumar]
- [s-chaves]: ChavesLiu. *Second Brain Skill*. GitHub — [github.com/ChavesLiu][s-chaves]
- [s-rohit]: rohitg00. *LLM Wiki v2*. GitHub Gist (fork of karpathy/llm-wiki)
  — [gist.github.com/rohitg00][s-rohit]

Первоисточник:

- [k-gist]: Andrej Karpathy. *llm-wiki.md*. GitHub Gist, 2026-04-04 —
  [gist.github.com/karpathy][k-gist]

Исторический фрейм:

- [s-engelbart]: H. Lehtman, D. Engelbart, C. Engelbart. *Technology
  Template Project: OHS Framework*. Bootstrap Alliance, 1998 —
  [dougengelbart.org][s-engelbart]
- Vannevar Bush. *As We May Think*. The Atlantic, 1945.

Поддерживающая литература:

- [paper-lost-middle]: Liu et al. *Lost in the Middle: How Language
  Models Use Long Contexts*. TACL / arXiv 2307.03172, 2024.
- [p-park]: Park et al. *Generative Agents: Interactive Simulacra of
  Human Behavior*. arXiv 2304.03442, 2023.
- [p-memgpt]: Packer et al. *MemGPT: Towards LLMs as Operating Systems*.
  arXiv 2310.08560, 2023.
- [p-reflexion]: Shinn et al. *Reflexion: Language Agents with Verbal
  Reinforcement Learning*. arXiv 2303.11366, 2023.
- Tulving, E. *Episodic and Semantic Memory*. 1972 (таксономия working /
  episodic / semantic / procedural).
- Doyle, J. *A Truth Maintenance System*. AI 12(3), 1979 (супресессия и
  belief revision).
- Shumailov et al. *AI models collapse when trained on recursively
  generated data*. Nature, 2024 (training-side analog drift-эффекта;
  именно training, не retrieval).

Инструменты, упомянутые в критике:

- [qmd] (Tobi Lütke) — hybrid BM25/vector search + LLM re-ranking для
  markdown, как MCP.
- jDocMunch — sections-search MCP (vendor-self-benchmark; см. §2.2).
