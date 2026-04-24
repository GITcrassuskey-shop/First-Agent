---
title: "Research — Критика Karpathy's LLM Wiki — разбор по источникам"
source:
  - "https://foundanand.medium.com/the-hidden-flaw-in-karpathys-llm-wiki-e3a86a94b459"
  - "https://dev.to/jgravelle/a-radical-diet-for-karpathys-token-eating-llm-wiki-59ng"
  - "https://ranjankumar.in/llm-wiki-synthesis-time-decision-rag-agentic-memory"
  - "https://github.com/ChavesLiu/second-brain-skill/blob/main/README.en.md"
  - "https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2"
  - "https://www.dougengelbart.org/content/view/110/460/"
compiled: "2026-04-24"
chain_of_custody: >
  Все цитаты, формулировки тезисов и цифры — через ссылки `source:`.
  Этот файл — критический пересказ, не первоисточник.
claims_requiring_verification:
  - "jDocMunch benchmark numbers (19.9× / 95%)"
  - "Claim that Karpathy wiki runs at ~100 articles / 400K words"
  - "rohitg00's list of eight extensions matches the current gist revision"
---

# Research — Разбор источников критики LLM Wiki

> **Статус:** research note, 2026-04-24.
> **Parent:** [`llm-wiki-critique.md`](./llm-wiki-critique.md) — содержит
> TL;DR, факты о gist'е, кросс-резку и фактчек.
> **Companion:** [`llm-wiki-critique-first-agent.md`](./llm-wiki-critique-first-agent.md)
> — применимость к First-Agent и списки «берём / не берём».
>
> Этот файл — детальный разбор по каждому из шести источников с одинаковой
> структурой: **Тезис → Иллюстрация → Что сильно → Что слабо → Что берём**.

---

## 2.1. Anand Lahoti — «The Hidden Flaw» ([Medium][s-lahoti])

**Тезис.** LLM-авторская проза, проиндексированная наравне с raw, создаёт
**knowledge base poisoning**: суммарные статьи становятся источниками,
ссылаются друг на друга, lint-проход проверяет только internal
consistency. Ground truth постепенно отваливается, и *это нельзя
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
абсолютизация. В реальности: архитектура компилируется один раз
ревьюером, контракты — никогда. Хороший compromise — в работе Kumar
(см. §2.3).

[s-lahoti]: https://foundanand.medium.com/the-hidden-flaw-in-karpathys-llm-wiki-e3a86a94b459

---

## 2.2. J. Gravelle — «A Radical Diet» ([dev.to][s-gravelle])

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
- **Vendor benchmark.** 7-page corpus, 5 queries. Методика не
  опубликована в воспроизводимом виде.
- **Промо.** Последняя треть поста — инсталляция jDocMunch. Это
  нормально для dev.to, но учитывать при взвешивании.

**Что берём.** Тезис «wiki — это датасет, не документ» + «cost ∝ answer
complexity, not wiki size» — это именно то, как должна работать **память
агента**. Наш такeaway — в [`-first-agent.md T5`][fa-T5].

[s-gravelle]: https://dev.to/jgravelle/a-radical-diet-for-karpathys-token-eating-llm-wiki-59ng
[paper-lost-middle]: https://arxiv.org/abs/2307.03172
[fa-T5]: ./llm-wiki-critique-first-agent.md#61-берём-sound-proven-актуально-для-v01

---

## 2.3. Ranjan Kumar — «Synthesis-Time Decision» ([ranjankumar.in][s-kumar])

Самая проработанная из трёх критик. Явно фиксирует **Synthesis Horizon**
— масштаб, после которого ingest-time модель ломается структурно (индекс
не помещается в контекст → ingest не может определить, какие страницы
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
корпусу. Правило цепочки: «если в ответе участвует конкретное
число/дата/процент, всегда верифицируй против `raw/`, даже если в wiki
есть значение».

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
перезаписывать страницу силенно, старое содержимое → в `history/` с
`superseded_by` + timestamp; противоречия → отдельный `conflicts/` файл
для человеческого разбора.

**Что сильно.** Всё конструктивно: каждый пункт — прямая спецификация.
Цитируется DokuWiki-автор Gutmans с точным вопросом про атрибуцию правок
в multi-agent среде — валидная проблема, которую Lahoti только намечает.

**Что слабо.** «Cross the horizon → degrades to RAG without governance
RAG provides» — немного кликбейтно. RAG-фреймворки governance-инструментов
сами по себе не дают; их тоже надо настраивать. Но главный thrust —
верный.

[s-kumar]: https://ranjankumar.in/llm-wiki-synthesis-time-decision-rag-agentic-memory

---

## 2.4. ChavesLiu — `second-brain-skill` ([GitHub][s-chaves])

Это **не критика**, а имплементация-референс: упаковка паттерна Карпатого
в Claude Code Skill. Слэш-команды (`/wiki init`, `/wiki ingest`,
`/wiki query`, `/wiki lint`, `/wiki wipe`). Natural-language-mode:
«ingest this article» → автоматически запустит `ingest`.

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

«`conventions.md` — your preferences» — отдельный файл для
пользовательских настроек вики, отделён от `CLAUDE.md`/`AGENTS.md`
(технические конвенции). Полезное разделение.

**Чего там нет.** Ни одного из улучшений из §2.1–2.3. Это именно
«packaging», а не эволюция.

[s-chaves]: https://github.com/ChavesLiu/second-brain-skill/blob/main/README.en.md

---

## 2.5. rohitg00 — «LLM Wiki v2» ([gist, форк][s-rohit])

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
   (инжект релевантного контекста), on-session-end (compress
   observations), on-query (file-back threshold), on-memory-write
   (contradiction check), on-schedule (periodic
   lint/consolidation/retention decay).
5. **Quality & self-correction.** Score на каждом LLM-написанном куске;
   self-healing lint (не предлагает, а чинит, что может); contradiction
   resolution с автоматическим предложением победителя (newer source /
   authority / support count).
6. **Multi-agent mesh sync** + shared/private scoping.
7. **Privacy/governance.** Filter-on-ingest для PII; audit trail для
   всех операций; bulk ops с reversal.
8. **Crystallization.** Конец research-сессии → автоматически
   дистиллирован в структурированный digest (question / findings /
   entities involved / lessons) и включается в базу как first-class
   source.

**Что сильно.**

- Когнитивная таксономия памяти (working/episodic/semantic/procedural) —
  общее место в agent-literature: Generative Agents ([Park et al.
  2023][p-park]), MemGPT ([Packer et al. 2023][p-memgpt]), Reflexion
  ([Shinn et al. 2023][p-reflexion]). Использовать как framing-device —
  легитимно.
- Hybrid search + RRF — state-of-practice, реализовано в Weaviate,
  Elasticsearch, LlamaIndex.
- Supersession / confidence — воспроизводит patterns из Truth Maintenance
  Systems (Doyle 1979) и TMS в классическом ИИ.

**Что слабо.**

- Экспоненциальный Ebbinghaus-decay для KB — **метафора**, не
  измеренная механика. У Эббингауза кривая про заучивание бессвязных
  слогов людьми. Перенос на «architecture decisions decay slowly,
  transient bugs decay fast» — интуитивно звучит, но ни одна цитата
  этого не измеряет для KB. В v0.1 — брать как эвристику, не как формулу.
- Продвижение *agentmemory* — коммерческого продукта. Текст его не
  скрывает, и принципы ценны и без него, но стоит помнить.
- «Всё автоматизировать» — классический build-up на ровном месте. Для
  v0.1 агента автоматизация нужна для 1–2 хуков, не для восьми.

[s-rohit]: https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2
[p-park]: https://arxiv.org/abs/2304.03442
[p-memgpt]: https://arxiv.org/abs/2310.08560
[p-reflexion]: https://arxiv.org/abs/2303.11366

---

## 2.6. Douglas Engelbart — OHS Framework, 1998 ([dougengelbart.org][s-engelbart])

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
