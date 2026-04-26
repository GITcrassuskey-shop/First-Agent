---
title: "Сообщество LLM-Wiki — батч 1: что из этого реально работает в продакшне"
compiled: "2026-04-26"
source:
  - https://github.com/JuliusBrussee/cavemem
  - https://github.com/Larens94/codedna
  - https://github.com/kytmanov/obsidian-llm-wiki-local
  - https://github.com/cablate/llm-atomic-wiki
  - https://github.com/alexdcd/AI-Context-OS
  - https://github.com/agent-creativity/agentic-local-brain
  - "user-dossier: 0.+A+workflow+for+github+repo+analysisprompt.md"
  - "user-dossier: 1.+agentic-patterns-dossier+...+agentic-local-brain.md"
  - "user-dossier: 2.+cavemem_dossier.md"
  - "user-dossier: 3.+codedna_dossier.md"
chain_of_custody:
  - "Досье 1–3 написаны пользователем (MondayInRussian) по его собственному
    workflow-промпту (досье 0). Я их прочёл целиком и сверил с самими
    репозиториями, которые выкачал отдельно 2026-04-23/24."
  - "Все цифры о звёздах/коммитах — на дату фетча; могут устареть."
  - "Спорные числа (см. §6) проверял отдельно: README-первоисточник."
status: research
claims_requiring_verification:
  - "cavemem ~75% token reduction — claim автора, не измеренный бенчмарк;
     коэффициент зависит от домена входов."
  - "CodeDNA +17pp F1 SWE-bench — n=10 patches, DeepSeek 10/0/0;
     signal, не proof."
  - "CodeDNA p=0.040 на n=5 — статистически слабый, рядом с шумом."
  - "obsidian-llm-wiki '79K-line cli.py' в досье 1 — вероятно
     ~7.9K строк или 79KB; фактический размер не проверял."
  - "agentic-local-brain '98.2% protocol adoption' — это метрика
     CodeDNA, в досье склеилась с другим проектом."
  - "Звёзды/контрибьюторы всех шести репо — на дату фетча
     2026-04-23/24; дрифтят во времени."
scope: |
  Часть 2A исследования сообщества вокруг LLM Wiki-паттерна. Шесть проектов:
  cavemem, codedna, obsidian-llm-wiki-local, llm-atomic-wiki, AI-Context-OS,
  agentic-local-brain. Цель — отделить «то, что работает на проде» от
  «модно, но недоказано» в применении к нашему агенту (First-Agent).
  Часть 2B (gbrain, llm-wiki-kit, obsidian-wiki, sparks, mnemovault
  + safishamsi/graphify + сравнение с GraphRAG) — отдельным PR после
  одобрения этого.
related:
  - knowledge/research/llm-wiki-critique.md
  - knowledge/research/llm-wiki-critique-first-agent.md
  - knowledge/research/agent-roles.md
---

# Сообщество LLM-Wiki — батч 1

> **Статус:** research note, 2026-04-26.
> **Что внутри:** разбор шести проектов сообщества, выросших вокруг идеи
> Карпатого о «LLM-вики». Цель — *production-ориентированный* отбор: что
> уже есть в чужой проверенной кодовой базе и что мы можем переиспользовать
> в First-Agent, а что — энтузиазм и YAGNI.

## 1. TL;DR

- **Шесть проектов, два жанра.** Четыре делают *вики/память для человека-
  пользователя* в духе Карпатого (`obsidian-llm-wiki-local`, `llm-atomic-
  wiki`, `AI-Context-OS`, `agentic-local-brain`). Два — *память для
  агента-кодера*, не для человека (`cavemem`, `codedna`). Это две разные
  задачи; смешивать выводы нельзя.
- **Что переиспользуется — это не код, а паттерны.** Все шесть — мелкие
  репозитории (звёзды от 19 до ~290, 1–4 контрибьютора, лицензия MIT в
  большинстве). Ни один пока не «production-grade библиотека для импорта».
  Но конкретные инженерные решения внутри — повторяющиеся, проверенные,
  и часть из них уже подтверждена в research-литературе (см. §4).
- **Кросс-валидация — главный фильтр.** Паттерны, которые независимо
  возникли в 2+ проектах, заведомо ценнее одиночных красивых идей. Топ-7
  таких паттернов в §4.1.
- **Скепсис.** Цифры в README надо читать как маркетинг, не как
  бенчмарк (см. §6). Сами по себе репозитории — это *инженерные эссе*,
  не научные статьи; принимаем их как такие.

## 2. Что я оцениваю и как

Каждый проект — по пяти осям, без галочек ради галочек:

| Ось | Что смотрю |
|---|---|
| **Зрелость** | Звёзды, контрибьюторы, активность коммитов, наличие тестов, ясный CHANGELOG. |
| **Воспроизводимость** | Можно ли запустить локально за час? Есть ли pinned-зависимости? |
| **Доказательная база** | Репо ссылается на бенчмарк/paper, или это design doc? |
| **Применимость к FA** | Работает на агента-исполнителя или на персональную вики? |
| **Стоимость заимствования** | Берём идею (дёшево), модуль (средне) или целый рантайм (дорого)? |

Никаких звёздочек «5/5» — конкретные вердикты в §3.

## 3. Шесть проектов: краткие вердикты

### 3.1 obsidian-llm-wiki-local — *production-ready для своей ниши*

**Что это.** Python CLI (`olw run/watch/maintain/compare/lint`), который
превращает `raw/`-заметки Obsidian в самообновляемую вики через локальную
LLM (Ollama по умолчанию), точно по паттерну Карпатого.

**Почему серьёзно.** ~290 звёзд, **500+ оффлайн-тестов**, multi-provider
factory (Ollama/OpenAI/Groq/vLLM), git-safety-net на каждый авто-edit,
**два уровня моделей** (fast + heavy) — это не пэт-проект на выходные,
а аккуратно собранный CLI. Из всех шести — самый «продакшен».

**Что украсть для FA.**
- Selective recompile: пересчитываем только те концепты, которые ссылаются
  на изменившийся файл, а не всю вики целиком.
- Rejection-as-training: реджект драфта с причиной → причина инжектится
  в next-compile prompt. Прямой путь к compounding quality.
- Two-tier LLM routing: fast-model для классификации/роутинга, heavy для
  генерации. Совпадает с тем, что мы уже планировали в `agent-roles.md`.
- Manual-edit protection: если человек руками поправил wiki-страницу,
  компилятор её больше не трогает. Простое правило, мощный эффект на
  доверие пользователя.

**Скепсис.** Заявление «79K-line cli.py» в досье — это либо опечатка
(скорее всего ~7.9K строк или 79KB), либо признак того, что вся бизнес-
логика свалена в один модуль. Если последнее — это анти-паттерн.

### 3.2 llm-atomic-wiki — *чистая методология, мало кода*

**Что это.** «Метод», а не библиотека: README + `CLAUDE.md` + 6-фазный
пайплайн (skeleton → classify → extract → quality → verify → compile) +
shell-скрипты. Расширяет Карпатого тремя вещами: **atom-слоем** (immutable
source of truth), **топик-ветками** и **двухуровневым линтом**
(programmatic + LLM).

**Почему интересно.** ~110 звёзд. Главная идея — *atoms ≠ wiki*: вики
полностью пересобирается из атомов, атомы из вики не пересобираются.
Это инверсия типичной модели «вики — источник истины» и она ровно
ложится на наш фактчек-параграф в `llm-wiki-critique.md` (chain of
custody, supersession not overwrite).

**Что украсть для FA.**
- **Two-layer lint** (программный → LLM-семантика). Дёшевые detеministic
  чеки прогоняем первыми (regex/bash), дорогой LLM-проход — только на
  чистых файлах. Переиспользуется как принцип во всём First-Agent.
- **CLAUDE.md как «конституция агента»** — формальный документ, который
  любой LLM читает прежде чем что-либо изменить, с *явным* списком «чего
  делать НЕЛЬЗЯ». Это уже частично есть у нас в `AGENTS.md`, можно
  усилить.
- **Parallel-compile naming lock.** Когда N агентов пишут параллельно,
  имена файлов резервируются заранее, агенты заполняют слоты — и не
  именуют файлы сами. Решает класс багов «два агента создали один и тот
  же slug».
- **Segment classification before extraction.** Не извлекаем всё — сначала
  классифицируем (extract/skip/deferred). Убирает шум до того, как мы
  заплатили за токены.

**Скепсис.** Это методология без рантайма. Чтобы её *запустить*, нужен
LLM-агент, читающий `CLAUDE.md` и выполняющий шаги вручную. Реальной
автоматизации внутри репо мало — поэтому из проекта извлекаем именно
схему, а не код.

### 3.3 AI-Context-OS (MEMM) — *самая богатая инженерия, но overengineered*

**Что это.** Десктопное приложение (React+TS фронт + Rust/Tauri бэкенд),
которое превращает локальную папку в «memory layer» с *роутингом
контекста*. Внутри — действительно много инженерии: hybrid scoring (BM25
+ semantic + recency + importance + access frequency + PPR-graph),
Ebbinghaus-modified decay, folder contracts, MCP-сервер на 127.0.0.1:3847.

**Почему интересно.** Единственный проект, где **scoring разложен на
шесть независимых сигналов**, а не свален в одно «cosine + reranker».
Это правильный подход — в research-литературе многосигнальная функция
релевантности у hybrid-RAG систем уже стандарт (Lewis 2020, MS MARCO
leaderboard).

**Что украсть для FA.**
- **L0/L1/L2 progressive loading.** Каждая заметка имеет 3 уровня
  детализации; токен-бюджет распределяется жадно — лучший уровень для
  каждой заметки. Это прямое решение проблемы Lost-in-the-Middle, на
  которую мы ссылались в критике Карпатого.
- **Intent-aware scoring weights.** Debug-запросы → больше BM25 + граф;
  brainstorm → больше importance + recency. Это лучше, чем единая
  «универсальная» retrieval-функция.
- **Two-pass retrieval (seeds → PPR).** Сначала находим топ-5 без графа,
  потом Personalized PageRank пускаем от этих сидов. Не позволяет графу
  «затопить» прямые попадания.
- **Conflict detection by tech-pairs.** Простая эвристика: если в одной
  записи `react`, в другой `vue` — поднимай флаг. Дешёвая страховка.

**Скепсис.** Объём инженерии огромен относительно reach (29 звёзд).
Если бы у этого проекта были тысячи звёзд — это была бы de facto
ссылочная имплементация. Пока — это очень хорошо спроектированный, но
малоиспользуемый артефакт. Брать **паттерны** — да, **зависеть от
кода** — нет.

### 3.4 agentic-local-brain — *хороший SKILL.md паттерн, остальное обычно*

**Что это.** Python-монолит (CLI + FastAPI на 11201 + SQLite + ChromaDB),
который собирает контент из 6 источников (file/web/bookmark/paper/email/
note) и компилирует из него вики. v0.6 добавил mining + KG, v0.7 — LLM
Wiki, v0.8 — backup. ~24 звезды.

**Почему интересно.** Самая аккуратно оформленная **portable skill**:
один `SKILL.md` с YAML-frontmatter, decision-tree для intent recognition
(`файл → FILE`, `URL → WEBPAGE`, `arxiv → PAPER` и т.д.), trigger-keywords
с китайским и английским — устанавливается одной командой `npx skills
add ...` в любой агент-десктоп.

**Что украсть для FA.**
- **3-tier fallback extraction.** User-provided → LLM → algorithmic
  fallback. Система всегда даёт результат, даже без LLM. Это паттерн,
  который мы можем применить к любой generation-стадии у нас.
- **Multi-stage retrieval pipeline.** Query expansion → hybrid retrieval
  (RRF) → LLM rerank → graph context enrichment → token-aware assembly.
  Каждый этап независимо валиден; можно собрать как Lego.
- **Portable SKILL.md как формат распространения умений.** Прямо
  отвечает на наш вопрос «где хранить роли» из `agent-roles.md §8`.
- **Restricted URL fallback.** Если прямой fetch не работает (paywall),
  агент использует свой собственный браузер → temp-файл → collect as file.
  Это не эзотерика, это правильная архитектура fallback'ов.

**Скепсис.** Сам KB-функционал — обычный «RAG поверх ChromaDB». LLM-Wiki
там — ещё одна реализация Карпатого, без новизны. Берём только skill-
формат и pipeline-структуру.

### 3.5 cavemem — *одна сильная идея, инженерно дисциплинированно*

**Что это.** TS-монорепо (apps/, packages/, viewer/), MCP-сервер +
SQLite (FTS5 + vector). Главная фишка — **«caveman grammar»**:
детерминистическая компрессия prose в свои сокращения с сохранением
технических токенов (код, пути, URL, числа) byte-for-byte.

**Почему интересно.** ~150 звёзд. Из всех шести — самая **строгая
монорепо-дисциплина**: declared dependency direction, architecture-guard
тесты падают сборку при нарушении. **Sync write на критическом пути,
async embedding в worker** — именно так должно быть устроено любое
agent-memory с MCP. **Hybrid search: BM25 + cosine с tunable α** — это
ровно то, что нам нужно для долговременной памяти First-Agent.

**Что украсть для FA.**
- **Progressive disclosure MCP API.** `search(q) → [id, score, snippet]`
  возвращает компактные результаты; полные тела достаются отдельным
  `get_observations(ids[])`. Прямая экономия токенов агента.
- **Sync write + async background.** Hooks пишут в SQLite за <150ms,
  worker отдельно считает embeddings. Не блокирует пользователя.
- **Hybrid search с настраиваемым α.** BM25-vector blend — стандарт в
  research-литературе (Reciprocal Rank Fusion, Cormack 2009; ColBERT-style
  late interaction), но здесь уже собрано и работает на SQLite.
- **Privacy at write boundary.** Контент в backticks вырезается *до*
  записи, path-globs исключают директории целиком, no-network-by-default.
  Правильная permission-модель для memory-агента.

**Скепсис.** «~75% token reduction» — это **claim автора, не измеренный
бенчмарк**. Компрессия по словарю работает, но коэффициент зависит от
домена входов; на коде/JSON он будет ниже. Берём идею, но цифру не
повторяем.

### 3.6 codedna — *смелая идея «file is the channel», слабая статистика*

**Что это.** «Протокол» агент↔агент: пишущий агент встраивает в шапку
файла структурированные `exports:`/`used_by:`/`rules:`/`related:`
поля, читающий агент (другая модель, другая сессия) их парсит. Никакой
внешней памяти, retrieval-pipeline или базы — *файл сам несёт контекст*.

**Почему интересно.** ~30 звёзд, но идея отличается от всех остальных.
Это не «вики поверх кода», а **в-source аннотация для inter-agent
communication**. Решает реальный класс проблем — «новый агент не знает,
кто меня импортирует» (reverse dependency declaration).

**Что украсть для FA.**
- **Reverse-dependency in headers.** `used_by:` — это то, чего нет в
  import-statements и что приходится искать globальным grep. Полезно для
  любого агента, работающего с кодовой базой.
- **Holographic property.** Информация повторяется на нескольких уровнях
  (project manifest → file header → function rules), агент работает даже
  при доступе к фрагменту. Нужно для sliding-window context.
- **Rules:-поле для domain-constraints.** Ровно то, что из импортов не
  видно: «MUST filter is_suspended() BEFORE summing». Это *исполнимая
  спецификация*, не комментарий.

**Скепсис.** Цифры в README надо читать с поправкой: «**+17pp F1
SWE-bench · 3 models · 10/0/0 DeepSeek**» — это **n=10 patches на одной
модели**, где на DeepSeek разница 10/0/0 относительно baseline. Это
**signal**, не **proof**. Чтобы поверить, нужны: (а) предзарегистрированный
протокол, (б) 100+ tasks, (в) baseline-протокол с теми же затратами на
prompt-инженерию. Заявленная p=0.040 на n=5 (другой бенчмарк) — это уже
почти шум в статистическом смысле.

## 4. Кросс-резка: что *реально* работает

### 4.1 Tier 1 — паттерны, повторяющиеся в 2+ проектах

| Паттерн | Где встречается | Что закрывает |
|---|---|---|
| **Filesystem-first storage** | все 4 wiki-проекта | Канон в файлах, БД — только индекс. Версионируется git'ом. |
| **L0/L1/L2 progressive detail** | AI-Context-OS, llm-atomic-wiki | Token budget management, mitigates Lost-in-the-Middle. |
| **Programmatic lint → LLM lint** | llm-atomic-wiki, obsidian-llm-wiki | Дёшевые проверки первыми, дорогие — только на «чистом». |
| **Two-tier LLM routing (fast/heavy)** | obsidian-llm-wiki, agentic-local-brain | Cost/latency. Прямо ложится на наш Planner/Executor сплит. |
| **Compile > RAG для стабильного знания** | obsidian, llm-atomic-wiki | Один раз заплатили токенами — навсегда читаем. RAG для long tail. |
| **Adapter-based tool integration** | AI-Context-OS, agentic-local-brain | Один canonical model → разные адаптеры (claude.md, .cursorrules…). |
| **Immutable source layer** | llm-atomic-wiki, AI-Context-OS, cavemem | Raw read-only; знание извлекается, не overwrite'ится. |

Эти семь — **то, что я бы заведомо взял в FA**, не задумываясь. Именно
потому, что они независимо переоткрылись.

### 4.2 Tier 2 — одиночные, но обоснованные

- **Rejection-as-training** (obsidian-llm-wiki) — компонит quality.
- **Parallel-compile naming lock** (llm-atomic-wiki) — закрывает реальный
  баг.
- **Two-pass retrieval (seeds → PPR)** (AI-Context-OS) — антидот graph-
  bias'у.
- **Intent-aware scoring weights** (AI-Context-OS) — debug ≠ brainstorm.
- **Portable SKILL.md** (agentic-local-brain) — формат для распростра-
  нения ролей.
- **3-tier fallback extraction** (agentic-local-brain) — graceful
  degradation.
- **Sync write + async background** (cavemem) — правильная latency-
  модель для memory.
- **Reverse-dependency in headers** (codedna) — `used_by:` решает
  реальный поиск.

### 4.3 Tier 3 — модно, но недостаточно проверено

- **Caveman compression** (cavemem) — идея есть, цифра 75% не
  верифицирована. Применять — после собственного измерения на наших
  данных.
- **Holographic file headers** (codedna) — красиво, но evidence слаб
  (n=10, n=5).
- **Knowledge mining + auto KG** (agentic-local-brain v0.6) — обычно
  generic LLM-граф без дополнительной ценности относительно RAG.
- **Ebbinghaus decay как формула** (AI-Context-OS) — мы уже отметили
  в `llm-wiki-critique.md`: Ebbinghaus — про человека, не про KB.
  Метафора, не закон.

## 5. Что мы реально берём в First-Agent

С маппингом на конкретные файлы репо.

| Что берём | В каком файле/слое FA это применяем |
|---|---|
| Two-layer lint | `knowledge/README.md` — добавить раздел «pre-commit checklist». |
| CLAUDE.md как конституция | усилить `AGENTS.md` явным списком *не делать*. |
| Two-tier LLM routing | `agent-roles.md` §5: Planner=fast, Executor=heavy. |
| L0/L1/L2 progressive detail | `docs/architecture.md` — раздел Memory: ввести три уровня. |
| Filesystem-first canon | уже принято в `knowledge/README.md` — закрепить явно. |
| Rejection-as-training | новый промпт-шаблон в `knowledge/prompts/`. |
| Sync write + async background | `docs/architecture.md` Memory — pattern для будущей реализации. |
| Hybrid search (BM25 + vector + α) | `docs/architecture.md` Retrieval — referенс на cavemem. |
| Portable SKILL.md | `knowledge/prompts/` — проверить, что наши role-prompts можно превратить в SKILL.md формат. |
| Reverse-dependency `used_by:` | optional pattern для будущего code-навигатора FA. |

Я **не вношу эти изменения этим PR** — это research-заметка. Изменения
в `AGENTS.md`/`docs/architecture.md` войдут отдельным «applied findings»
PR после твоего одобрения, как мы делали в Part 1.

## 6. Fact-check и скепсис

- **Cavemem ~75% reduction** — claim, не бенчмарк. Зависит от домена.
  Принимаем как «компрессия работает», не как «всегда 75%».
- **CodeDNA +17pp F1** — n=10 patches, DeepSeek 10/0/0. Signal, не proof.
- **CodeDNA p=0.040 на n=5** — статистически слабый. Не цитируем как
  «доказано».
- **agentic-local-brain «98.2% adoption»** — это про CodeDNA из его
  README, не про сам agentic-local-brain. Не путаем.
- **«79K-line cli.py» в obsidian-llm-wiki** (досье 1) — почти наверняка
  ~7.9K строк или 79KB; такой монолит был бы анти-паттерном.

## 7. Что НЕ берём (и почему)

- **Десктоп-приложение в Tauri** (AI-Context-OS) — у нас нет фронта.
- **ChromaDB** (agentic-local-brain) — лишняя зависимость для v0.1; SQLite-
  vector (как у cavemem) или duckdb-vss достаточно.
- **Каноническая Ebbinghaus-формула decay** — критика остаётся в силе.
- **Полная monorepo-инфраструктура** (cavemem) — у нас docs-only repo;
  применим *принцип* строгой dependency-direction позже, когда будет код.
- **Knowledge mining v0.6** (agentic-local-brain) — generic LLM-KG без
  дополнительной ценности относительно простого RAG в нашей задаче.

## 8. Открытые вопросы для Part 2B

Что нужно решить *до* того, как начнём вторую половину разбора:

1. **Готовы ли мы к v0.1 First-Agent с filesystem-only хранилищем?**
   Если да — `cavemem`-стиль (SQLite-vector, MCP) можно отложить.
2. **Включаем ли паттерн `codedna` (reverse-deps в шапках) в FA?**
   Он работает только на code-base. Если v0.1 — про reasoning-agent, не
   про code-agent, паттерн откладываем.
3. **Применяем ли L0/L1/L2 к нашим knowledge-заметкам прямо сейчас?**
   Это бы потребовало ввести `<L1>`/`<L2>`-маркеры по образцу AI-Context-OS.
   Формат стабильный и не ломает обратную совместимость с обычным MD.

Эти вопросы перекрывают часть открытых из `agent-roles.md §8` (где
хранить роли, язык промптов), и часть из `llm-wiki-critique-first-agent.md
§6 (T2)` (стратификация stable vs volatile). Их можно ответить вместе,
после Part 2B.

## 9. Sources

- [obsidian-llm-wiki-local](https://github.com/kytmanov/obsidian-llm-wiki-local) —
  CLI, ~290⭐, 500+ тестов, multi-provider, git-safety-net.
- [llm-atomic-wiki](https://github.com/cablate/llm-atomic-wiki) —
  методология + scripts, ~110⭐, 6-фазный pipeline.
- [AI-Context-OS](https://github.com/alexdcd/AI-Context-OS) (MEMM) —
  Tauri+Rust, ~29⭐, hybrid scoring, MCP на 3847.
- [agentic-local-brain](https://github.com/agent-creativity/agentic-local-brain) —
  Python+SQLite+ChromaDB, ~24⭐, FastAPI 11201, portable SKILL.md.
- [cavemem](https://github.com/JuliusBrussee/cavemem) — TS monorepo, ~150⭐,
  caveman-compression, MCP, hybrid search.
- [codedna](https://github.com/Larens94/codedna) — Python tool +
  protocol v0.9, ~30⭐, в-source аннотации.

Поддерживающая литература (по которой проверял утверждения):

- Cormack et al. *Reciprocal Rank Fusion outperforms Condorcet*. SIGIR 2009.
- Liu et al. *Lost in the Middle*. NAACL 2024 — для L0/L1/L2 обоснования.
- Lewis et al. *RAG for Knowledge-Intensive NLP*. NeurIPS 2020 — hybrid
  retrieval.
- Karpathy LLM Wiki gist (см. `knowledge/research/llm-wiki-critique-sources.md`).

Досье пользователя:

- `~/attachments/.../0.+A+workflow+for+github+repo+analysisprompt.md`
- `~/attachments/.../1.+agentic-patterns-dossier+...+agentic-local-brain.md`
- `~/attachments/.../2.+cavemem_dossier.md`
- `~/attachments/.../3.+codedna_dossier.md`
