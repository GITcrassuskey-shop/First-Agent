---
title: "Сообщество LLM-Wiki — батч 2: gbrain, sparks, obsidian-wiki, llm-wiki-kit, mnemovault, graphify + сравнение с research-backed GraphRAG"
compiled: "2026-04-23"
source:
  - https://github.com/garrytan/gbrain
  - https://github.com/MauricioPerera/llm-wiki-kit
  - https://github.com/Oshayr/LLM-Wiki
  - https://github.com/ar9av/obsidian-wiki
  - https://github.com/yogirk/sparks
  - https://github.com/kimsiwon-osifa7878/mnemovault
  - https://github.com/safishamsi/graphify
  - https://gist.github.com/agent-creativity/a4e090f888a516b313ddd1302e51c286
  - https://github.com/microsoft/graphrag
  - https://github.com/HKUDS/LightRAG
  - https://github.com/OSU-NLP-Group/HippoRAG
  - https://github.com/gusye1234/nano-graphrag
  - "user-dossier: 4.gbrain_dossier.md"
  - "user-dossier: 5.llm-wiki-kit_dossier.md"
  - "user-dossier: 6.obsidian-wiki_dossier.md"
  - "user-dossier: 7.sparks_dossier.md"
chain_of_custody:
  - "Досье 4–7 написаны пользователем (MondayInRussian); прочёл целиком,
    сверил с первоисточниками (репозитории, README, релизы) на 2026-04-23."
  - "Досье 5 у автора было неполным (репозиторий не открывался); я перепроверил
    первоисточник — MauricioPerera/llm-wiki-kit доступен и описан ниже из README."
  - "GraphRAG-имплементации описаны по их README + paper-абстрактам; глубокое
    чтение кода НЕ проводил — указываю это явно в §4 и §9."
  - "Все цифры о звёздах/коммитах — на дату фетча 2026-04-23."
status: research
claims_requiring_verification:
  - "gbrain ‘17 888 страниц / 4 383 человека / 723 компании / 21 cron’ — цифры из
     own-blog Garry Tan, не воспроизводимый бенчмарк."
  - "graphify ‘71.5x fewer tokens per query vs reading raw files’ — claim из
     README, методология бенчмарка не описана; принимаем как порядок-величины."
  - "Microsoft GraphRAG ‘global queries’ требуют LLM-вызова на каждое сообщество
     при индексации; стоимость на корпусе >50K токенов нелинейна."
  - "LightRAG ‘до 99% дешевле GraphRAG’ — claim из abstract paper; зависит от
     модели и корпуса."
  - "HippoRAG ‘single-step multi-hop’ — на бенчмарке MuSiQue/2WikiMultiHop;
     генерализуется не на любой домен."
  - "nano-graphrag ‘~800 LoC’ — на момент v0.0.x; репо растёт."
  - "agent-creativity gist — long-form блог об agentic-local-brain
     (уже в batch-1), не отдельный проект; в синтезе используется как
     supplement, не как primary source."
  - "Звёзды/контрибьюторы всех репо дрейфуют во времени; на момент фетча см. §3, §4."
scope: |
  Часть 2B исследования сообщества вокруг LLM-Wiki-паттерна и его сравнение
  с research-backed GraphRAG-реализациями. Пять community-проектов
  (gbrain, llm-wiki-kit, obsidian-wiki, sparks, mnemovault), плюс
  agent-creativity gist (как первоисточник нарратива agentic-local-brain),
  плюс safishamsi/graphify как граф-ориентированный community-проект.
  Потом сравнение с Microsoft GraphRAG, LightRAG, HippoRAG, nano-graphrag.
  Цель — выбрать минимальный набор паттернов, который мы реально применим
  в First-Agent, и понять, в какой момент имеет смысл переходить от
  filesystem-канона к графовой памяти.
related:
  - knowledge/research/llm-wiki-community-batch-1.md
  - knowledge/research/llm-wiki-critique.md
  - knowledge/research/llm-wiki-critique-first-agent.md
  - knowledge/research/agent-roles.md
---

# Сообщество LLM-Wiki — батч 2 + GraphRAG

> **Статус:** research note, 2026-04-23.
> **Что внутри:** разбор пяти community-проектов (gbrain, llm-wiki-kit,
> obsidian-wiki, sparks, mnemovault), плюс safishamsi/graphify как
> graph-ориентированного представителя сообщества, плюс gist
> agent-creativity, плюс сравнение всего этого с research-backed
> GraphRAG (Microsoft GraphRAG, LightRAG, HippoRAG, nano-graphrag).
> Цель — отделить, что на самом деле даёт ROI в нашей задаче, от моды.

## 1. TL;DR

- **Пять community-проектов, три жанра.** `gbrain` и `graphify` —
  *типизированные графы знаний с детерминированной экстракцией*; sparks —
  *runtime-разделение «механика vs семантика»*; `obsidian-wiki` и
  `llm-wiki-kit` — *чистая методология/каркас вики*; `mnemovault` —
  «вики с веб-UI» как product-окрашенная демонстрация.
- **GraphRAG ≠ wiki.** Все четыре GraphRAG-реализации решают проблему
  *читающей стороны* (как извлечь и ответить), а LLM-Wiki-проекты —
  проблему *пишущей стороны* (как вырастить и поддерживать канон).
  `gbrain` и `graphify` это объединяют.
- **Доказательность ранжирована.** Tier-1 (≥2 независимых источников):
  filesystem-first канон, hot-cache (~500 слов), mechanical/semantic split,
  write-time extraction, link-typed graph, hybrid search.
  Tier-2: dual-level retrieval (LightRAG), PPR-based reasoning (HippoRAG),
  EXTRACTED/INFERRED honesty (graphify), maturity lifecycle (sparks).
  Tier-3 (один source, недоказан): hierarchical community summaries
  (Microsoft GraphRAG) для малых корпусов, multi-pass LLM-extraction для
  личной памяти.
- **Главный вывод для First-Agent.** До корпуса ≈100K токенов graph-RAG
  стратегия overkill; начинаем с filesystem + hot.md + BM25/vector hybrid.
  Когда (и если) корпус вырастет — берём паттерн `gbrain` (write-time
  extraction типизированных рёбер) или паттерн HippoRAG (PPR) до
  Microsoft GraphRAG; LightRAG — самый прагматичный middle ground.

## 2. Методология (кратко, повтор из batch-1)

Оси оценки: зрелость (звёзды, тесты, активность), воспроизводимость
(open license, локальный запуск), доказательная база (paper/бенчмарк vs
блог автора), применимость к FA, стоимость. Tier-ранжирование — по
*повторяемости паттерна* в независимых проектах, не по звёздам.

## 3. Пять community-проектов + graphify + gist

### 3.1. gbrain (garrytan, 11.5K⭐, MIT)

**Источник:** [garrytan/gbrain](https://github.com/garrytan/gbrain). Описание
(GitHub About): «Garry’s Opinionated OpenClaw/Hermes Agent Brain».
Стек: TypeScript, PGLite (локально) / Postgres + pgvector (продакшн),
MCP-сервер с 30+ tools.

**Что внутри (по досье 4 + код).** Типизированный knowledge graph с
*детерминированной экстракцией на write-time*: каждая страница при
сохранении пропускается через regex-парсер, который вытягивает entity-
references и создаёт типизированные рёбра (`attended`, `works_at`,
`invested_in`, `founded`, `advises`). LLM на этом этапе **не** дёргается.
Поверх — тонкий TS-harness и ~29 markdown-skill-файлов (workflows для
ingest, search, decision-log и т.п.). Trust boundary через
`OperationContext.remote`. Hybrid search (BM25 + vector + graph).

**Скепсис.** Цифры «17 888 страниц / 4 383 человека / 723 компании /
21 cron» (досье 4) — из блога Garry Tan, не воспроизводимый бенчмарк.
Это сильный *signal* (production-нагрузка YC-президента), но не proof
для нашего домена.

**Что берём:** *write-time extraction*, *thin harness + fat skills*,
*trust boundary через OperationContext*. Отказываемся от: PGLite для
v0.1 (filesystem проще), MCP-сервера до тех пор, пока нет агентов-
клиентов (преждевременный API).

> **Дополнено 2026-04-26.** Operations contract (`src/core/operations.ts`
> как single source of truth для CLI+MCP), `RESOLVER.md` skill
> dispatcher, always-on parallel skills, `llms.txt`/`llms-full.txt`
> documentation protocol — разобраны отдельно в
> [`agentic-memory-supplement.md` §4](./agentic-memory-supplement.md).

### 3.2. llm-wiki-kit (MauricioPerera, 10⭐, MIT)

**Источник:** [MauricioPerera/llm-wiki-kit](https://github.com/MauricioPerera/llm-wiki-kit).
Описание: «LLM-maintained markdown wiki on a git-native substrate.
Obsidian-compatible, three-layer retrieval (grep + BM25 + embeddings),
explicit supersession. Built on js-doc-store, js-vector-store, js-git-store».

**Что важно.** Это самая близкая к нашему `llm-wiki-critique-first-agent.md`
эталонная реализация. Три уровня retrieval (grep → BM25 → embeddings)
точно совпадают с тем, что мы вычитали в критике Карпатого: дёшево
проверяем сначала, дорогой LLM — последним. **Explicit supersession**
(не overwrite) — это уже принято у нас в `knowledge/README.md` и AGENTS.md.

**Скепсис.** 10 звёзд, маленький community, активность низкая.
Это *demonstration*, не production. Принимаем как валидацию архитектуры,
не как готовый компонент.

**Что берём:** *three-layer retrieval* как явный pattern в
`docs/architecture.md` (если ещё не там — добавить). Отказываемся от:
Deno/Cloudflare-workers стека (наш план — Python).

> **Замечание о досье 5.** Пользовательское досье 5 пометило этот проект
> как «недоступный». Я перепроверил: репо открывается, README читается;
> это просто маленький, тихий проект, не битый. Для синтеза использую
> README первоисточника, не placeholder из досье.

### 3.3. obsidian-wiki (Ar9av, 697⭐, MIT)

**Источник:** [Ar9av/obsidian-wiki](https://github.com/ar9av/obsidian-wiki).
Описание: «Framework for AI agents to build and maintain an Obsidian
wiki using Karpathy’s LLM Wiki pattern». Topics: agent-skills, llm-tools.

**Что внутри (по досье 6).** *Pure skill framework* — никакого runtime,
никаких скриптов; markdown-инструкции, которые агент выполняет напрямую.
Поддержка 15+ агентов (Claude Code, Cursor, Codex, Gemini CLI, Kiro,
Trae, Hermes, и т.д.) через симлинки: `.skills/` — каноническое
определение, `.claude/skills/`, `.cursor/skills/` — per-agent
зеркала. Ключевой компонент: **`hot.md`** — ~500-словная сессионная
сводка, обновляемая операциями записи и читаемая первой при чтении
(*hot cache*). Page schema с обязательным frontmatter (title, category,
tags, sources, created, updated). Ingest-workflow: ingest → classify →
connect → track. Skill routing table мапит intent → skill.

**Скепсис.** «15+ агентов» — это symlink-комбинаторика, а не
содержательная адаптация под каждого. Реальная переносимость зависит
от того, насколько ты не ушёл за пределы общих markdown-skill
конвенций. Но идея *одного канонического source-of-truth и тонких
агентских зеркал* — здравая.

**Что берём:** *hot.md cache* (~500 слов) как обязательный артефакт
сессии; *intent → skill routing table*; *ingest → classify → connect →
track* как явный 4-шаг workflow. Отказываемся от: зацикленности на
Obsidian как UI — у нас нет фронта.

### 3.4. sparks (yogirk, 9⭐, MIT)

**Источник:** [yogirk/sparks](https://github.com/yogirk/sparks). Описание:
«Knowledge base runtime for AI agents — a single Go binary that any
harness can drive».

**Что внутри (по досье 7).** Один Go-бинарник, который реализует
*mechanical/semantic separation*: детерминированная работа (парсинг,
скан, индексация) — внутри бинарника; семантическая (синтез,
суждение) — у агента. Трёхслойная модель:
`raw/` (append-only, immutable) → `wiki/` (агент-поддерживаемый
derived view) → `sparks.db` (SQLite-manifest, регенерируется,
*disposable*). Три adapter-surface (CLI, MCP stdio с 11 tools, HTTP
viewer) вызывают одно ядро бизнес-логики (*thin adapter discipline +
guard tests*). Page types через YAML-frontmatter (entity, concept,
summary, synthesis, collection). Maturity lifecycle (seed → working →
stable → historical). Ingest-протокол: `sparks ingest --prepare` (JSON
manifest) → агент действует → `sparks ingest --finalize` (архивация,
скан, коммит).

**Скепсис.** 9 звёзд, маленький community, активность низкая. Но
архитектурная дисциплина ярко сформулирована, README местами лучше,
чем у gbrain. Это *эталонный пример того, как правильно разделить
бинарник и агента*, даже если конкретно sparks никто не использует.

**Что берём:** *mechanical/semantic split*, *append-only source +
derived view + disposable manifest*, *page-type ontology*, *maturity
lifecycle*, *ingest --prepare/--finalize as protocol*, *thin adapter
discipline + guard tests*. Отказываемся от: Go (наш план — Python);
SQLite-manifest на v0.1 (jsonl-файла достаточно).

> **Дополнено 2026-04-26.** Contract-in-binary + multi-harness
> `init --agent X`, hint-not-classify pattern, architecture guard
> test, SQLite WAL + concurrent-ingest lock — разобраны отдельно
> в [`agentic-memory-supplement.md` §5](./agentic-memory-supplement.md).

### 3.5. mnemovault (kimsiwon-osifa7878, 10⭐, MIT)

**Источник:** [kimsiwon-osifa7878/mnemovault](https://github.com/kimsiwon-osifa7878/mnemovault).
Описание: «MnemoVault: An Intelligent Memory Vault — a local LLM-wiki
web app». Демо: [mnemovault.rofauna.com](https://mnemovault.rofauna.com/).
Корейский README дополнительно (`README_KR.md`) — явный сигнал, что
аудитория не western-only.

**Что внутри.** Web-app (Next.js-подобная по структуре `src/` + `public/` +
`content/`); хранит контент в `content/` как markdown (как Obsidian).
По README — упор на «portable, inspectable, easy to version with Git».
Идея: вики *как UI-product*, не как dev-tool.

**Скепсис.** 10 звёзд. Это product-prototype, не reference-architecture.
Главная ценность — наблюдение, что «filesystem-canon + git» работает
и в product-форме, без скрытых баз данных.

**Что берём:** валидация принципа «git-versionable markdown как
canonical store, всё остальное — view»; пример minimalist-схемы для
content/. Отказываемся от: web-app слоя — для FA нерелевантен на v0.1.

### 3.6. graphify (safishamsi, 35K⭐, MIT)

**Источник:** [safishamsi/graphify](https://github.com/safishamsi/graphify),
ветка v5, 205 коммитов. Описание: «AI coding assistant skill. Type
`/graphify` in Claude Code, Codex, OpenCode, Cursor, Gemini CLI or
Google Antigravity — it reads your files, builds a knowledge graph,
and gives you back structure». PyPI package: `graphifyy`.

**Что внутри (по README первоисточника).** Трёхпроходная pipeline:

1. **Детерминированный AST-pass.** Извлечение структуры из кода
   (классы, функции, импорты, call-graph, docstrings, rationale-comments) —
   *без LLM-вызовов*.
2. **Whisper-транскрипция.** Видео/аудио локально через faster-whisper с
   domain-aware prompt; транскрипты кэшируются.
3. **Claude subagents в параллель** по docs, papers, images,
   transcripts — извлекают концепты, отношения, design-rationale.

Результаты сливаются в **NetworkX-граф**, кластеризуются **Leiden
community detection** (по топологии, *без эмбеддингов*),
экспортируются как `graph.html` (interactive), `GRAPH_REPORT.md`
(plain-language), `graph.json` (queryable persistent state).
Каждое отношение помечено `EXTRACTED` (найдено в источнике),
`INFERRED` (разумное обобщение Claude-ом), `AMBIGUOUS` — *honest
audit trail*. Поддержка install под 12+ агентов (Claude Code, Codex,
OpenCode, Copilot CLI, VS Code, Aider, Trae, Gemini CLI, Hermes, Kiro
и др.). Утилиты: `graphify clone <github-url>`, `graphify merge-graphs`,
`build_merge()` (incremental), `deduplicate_by_label()`, *shrink guard*
(не перезаписывать `graph.json` меньшим графом).

**Скепсис.** «71.5x fewer tokens per query vs reading raw files» — claim
из README, методология бенчмарка не указана. 35K звёзд — это много, но
не все звёзды из production-использования; часть — из вирусного
recent-launch. Дисциплина (`EXTRACTED`/`INFERRED`/`AMBIGUOUS` как
тэги, shrink-guard, dedup-by-label) — лучшее, что я видел в community.

**Что берём:** *EXTRACTED / INFERRED / AMBIGUOUS-таги на каждом
выводе* (это и есть chain-of-custody, который у нас уже есть в
`AGENTS.md`); *shrink-guard на критичные артефакты* (никогда не
перезаписывать большой граф меньшим без явного флага); *Leiden-
clustering as graph-topology operation* (но только когда у нас будет
граф достаточного размера). Отказываемся от: трёхпроходного pipeline
до того, как у нас будет хотя бы 100 страниц.

### 3.7. agent-creativity gist (5⭐)

**Источник:** [build-agentic-local-brain.md](https://gist.github.com/agent-creativity/a4e090f888a516b313ddd1302e51c286).
Это long-form блог-нарратив автора `agentic-local-brain` (уже разобран
в батче-1). Не отдельный проект, а *narrative supplement* — описание
того, как и зачем строилась `agentic-local-brain`. Полезен для
контекста (мотивация: «5 точек коллекции — Wechat, DingTalk,
закладки, read-later, локальные файлы — без единой точки входа»),
но реальные паттерны те же, что в `agentic-local-brain` репо.

**Что берём:** ничего нового сверх batch-1; используем как *evidence*,
что problem-formulation о фрагментации знания у разных пользователей
сходится.

## 4. Research-backed GraphRAG: четыре подхода

> **Дисклеймер.** Я опирался на README + paper-абстракты + сводные
> сравнения, не на полное чтение кода каждой имплементации. Это
> уровень «обзорный», не «глубокий аудит».

### 4.1. Microsoft GraphRAG (32.5K⭐, MIT, paper Edge et al., arXiv:2404.16130)

**Идея.** LLM извлекает entities + relations + claims из чанков
текста → строится граф → Leiden-кластеризация в *иерархию сообществ*
→ для каждого сообщества LLM генерирует summary → запросы:
*global* (агрегат по community-summaries) и *local* (по entity-
neighborhood). Решает класс «query-focused summarization»: «расскажи
мне общее про этот корпус», который обычный chunk-based RAG не тянет.

**Стоимость.** Нелинейная по корпусу: индексация требует LLM-вызова на
*каждый* кластер на *каждом уровне* иерархии. На 50K+ токенах корпуса
это сотни долларов на одну индексацию OpenAI-класса.

**Когда это нужно.** Корпус большой (≥100K токенов), и нужны *глобальные*
вопросы стиля «какие основные темы здесь?», «сколько было упоминаний
X в рамках Y?». Для FA на стадии research — overkill.

### 4.2. LightRAG (HKUDS, 34.3K⭐, EMNLP 2025, paper arXiv:2410.05779)

**Идея.** Упростить Microsoft GraphRAG: dual-level retrieval (low-level:
конкретные entities; high-level: темы/concepts), *incremental graph
update* (не пересобирать на каждый ingest), широкая поддержка vector-
DB и LLM-провайдеров. Авторы заявляют существенное снижение стоимости
относительно Microsoft GraphRAG; abstract упоминает «99% reduction»
для ряда конфигураций (claim).

**Когда это нужно.** Хочется графовых ответов, но не хочется платить
GraphRAG-цену. Самый прагматичный вариант для среднего размера
корпуса (10K — 1M токенов).

### 4.3. HippoRAG (OSU-NLP, 3.4K⭐, NeurIPS 2024, paper arXiv:2405.14831)

**Идея.** Вдохновлено hippocampal indexing theory из нейронаук. Граф
строится по passages + entities + edges. Ответ на multi-hop вопрос
ищется через **Personalized PageRank (PPR)** — single-step, без
итеративной retrieval-then-LLM-then-retrieval цепочки. Заявленный
выигрыш: лучше recall на multi-hop benchmarks (MuSiQue, HotpotQA,
2WikiMultiHop) при сравнимой стоимости.

**Когда это нужно.** Задача — *multi-hop reasoning* (где ответ требует
склейки 2–3 фактов). Для FA на стадии research — пока нет; но как
потенциальный апгрейд читающей стороны при появлении сложных
аналитических задач — записываем в backlog.

### 4.4. nano-graphrag (gusye1234, 3.8K⭐, MIT)

**Идея.** Минимальная hackable-реимплементация Microsoft GraphRAG в
~800 LoC ядра. Образовательный/референсный проект: «прочитай
исходники за один присест, поменяй любую часть, не утонув в
DataShaper-абстракциях оригинала».

**Когда это нужно.** Когда нужно *понять* GraphRAG, поэкспериментировать
с заменой LLM/эмбеддера/storage. Не production. Для FA — отличный
референс, если/когда мы решим экспериментировать с graph-RAG.

## 5. Сравнительная таблица

| Что | gbrain | graphify | sparks | obsidian-wiki | llm-wiki-kit | mnemovault | MS GraphRAG | LightRAG | HippoRAG | nano-graphrag |
|---|---|---|---|---|---|---|---|---|---|---|
| Доминирующий слой | **Write+Read** | **Write+Read (читать)** | **Write** | **Write** | **Write+Read** | **UI** | **Read** | **Read** | **Read** | **Read** |
| Граф | Typed, write-time | NetworkX + Leiden | Нет (frontmatter ontology) | Нет | Нет (vector+BM25+grep) | Нет | LLM-extracted, Leiden | Dual-level + incremental | Passage+PPR | Mini-Leiden |
| Стоимость indexing | Низкая (regex) | Средняя (Whisper+Claude subagents) | Низкая (mechanical) | Нулевая (markdown) | Низкая (BM25+embed) | Низкая | **Высокая** | Средняя | Средняя | Средняя |
| Open license | MIT | MIT | MIT | MIT | MIT | MIT | MIT | MIT | MIT | MIT |
| Зрелость (⭐) | 11.5K | 35K | 9 | 697 | 10 | 10 | 32.5K | 34.3K | 3.4K | 3.8K |
| Применимо к FA v0.1 | Частично (write-time pattern) | Нет (overkill) | Да (mechanical/semantic) | Да (hot.md, ingest) | Да (3-layer) | Нет | Нет | **Backlog** | Backlog | Reference only |

## 6. Tier-1/2/3 паттерны

**Tier 1 (≥2 независимых проекта, готовы к применению):**

1. **Filesystem-first markdown canon.** sparks, obsidian-wiki, mnemovault,
   llm-wiki-kit. Уже принят у нас.
2. **Hot-cache (~500 слов сессионная сводка).** obsidian-wiki + наш
   `llm-wiki-critique` (mid-session memory tier).
3. **Mechanical/semantic split.** sparks (явно), gbrain (write-time
   extraction = mechanical). Должно быть ядром нашего будущего runtime.
4. **Write-time link extraction (regex / detect references).** gbrain;
   также эта же идея в `codedna` (batch-1, `used_by:`). Tier-1 точно.
5. **Hybrid retrieval (BM25 + vector + ?).** llm-wiki-kit, gbrain,
   `cavemem` (batch-1). Tier-1.
6. **Three-layer retrieval (grep → BM25 → embeddings).** llm-wiki-kit
   явно; то же в `obsidian-llm-wiki-local` (batch-1).
7. **Append-only raw + derived view.** sparks (явно), косвенно
   mnemovault (filesystem-canon + git-history).

**Tier 2 (один сильный source, valid но не cross-validated):**

8. **EXTRACTED / INFERRED / AMBIGUOUS-таги на каждом выводе.** graphify.
   Очень здравая идея; у нас уже есть концепт chain-of-custody, это
   та же идея на уровне утверждения.
9. **Maturity lifecycle (seed → working → stable → historical).** sparks.
10. **Ingest-protocol с двумя фазами (prepare/finalize).** sparks.
11. **Dual-level retrieval (low-level entity vs high-level theme).**
    LightRAG.
12. **PPR-based multi-hop reasoning.** HippoRAG. Сильная идея, но
    задача-специфична (multi-hop).

**Tier 3 (один источник, недоказан или контекст-зависим):**

13. **LLM-extracted hierarchical community summaries.** Microsoft
    GraphRAG. Дорого, оправдано только на больших корпусах.
14. **Multimodal Whisper + Claude-subagents pipeline.** graphify.
    Впечатляюще, но не нужно для текстовой research-вики.
15. **Auto-generated collections (Quotes, Bookmarks, Books, …).** sparks.
    Идея ок; реализация — over-engineering для нашего scope.

## 7. Применимость к First-Agent

С маппингом на конкретные файлы/слои.

| Паттерн | Где в FA это применить | Tier | Когда |
|---|---|---|---|
| Three-layer retrieval (grep→BM25→embeddings) | `docs/architecture.md` (Memory) | T1 | После v0.1 кода |
| Hot.md (~500 слов сводка) | `knowledge/hot.md` (новый файл) | T1 | Можно завести уже сейчас |
| Mechanical/semantic split | `docs/architecture.md` (Runtime) | T1 | При проектировании скелета |
| Write-time link extraction | `src/<core>/links.py` (будущий) | T1 | После v0.1 |
| Append-only raw + derived view | `knowledge/raw/` + `knowledge/wiki/` | T1 | Можно завести структуру сейчас |
| EXTRACTED/INFERRED-таги | расширение frontmatter в `knowledge/` | T2 | После batch-2 review |
| Maturity lifecycle (seed → … → historical) | расширение frontmatter | T2 | После v0.1 |
| Ingest --prepare/--finalize | будущий CLI/script в `tools/` | T2 | При появлении ingest-нагрузки |
| Dual-level retrieval (LightRAG) | `docs/architecture.md` (Retrieval) | T2 | Когда корпус ≥10K токенов |
| PPR multi-hop (HippoRAG) | research-backlog | T2 | Когда появятся multi-hop задачи |
| MS GraphRAG hierarchical communities | НЕ берём для v0.1 | T3 | ≥100K токенов корпус |
| Whisper + Claude-subagents pipeline | НЕ берём | T3 | — |

**Не берём (явно):**

- Полный graph-pipeline до того, как у нас вообще есть корпус.
- Web-UI слой (mnemovault) — у нас нет фронта.
- ChromaDB / PGLite / Postgres+pgvector — для v0.1 файлов достаточно.
- Multi-agent install matrix (graphify, obsidian-wiki) — у нас один
  основной агент (Devin).

## 8. Итоговый вывод: какой подход для First-Agent

**Прагматичный путь развития памяти FA:**

1. **Сейчас (research-стадия).** Filesystem-canon (✓ есть),
   provenance-frontmatter (✓ есть), supersession-вместо-overwrite
   (✓ есть). Добавить `knowledge/hot.md` как обязательную сессионную
   сводку и явно описать `raw/` vs `wiki/` (sparks-стиль) в архитектуре.
2. **Как только появится `src/`.** Mechanical/semantic split: тонкий
   Python-runtime (mechanical) + skill-markdowns с workflow’ами
   (semantic). Hybrid retrieval: grep → BM25 → embeddings (как
   llm-wiki-kit). Hot-cache в runtime, не только в файле.
3. **Когда корпус доходит до ≈10K токенов.** Add: write-time link-
   extraction (gbrain-style), EXTRACTED/INFERRED-таги на выводах
   (graphify-style). Dual-level retrieval (LightRAG-вдохновлённое):
   разделить low-level entity-search и high-level theme-search.
4. **Когда корпус ≥100K токенов И появятся multi-hop задачи.**
   Эксперимент с HippoRAG (PPR over passage-graph) или LightRAG
   как готовой библиотеки. Microsoft GraphRAG не берём, кроме как
   референс — слишком дорого индексировать. nano-graphrag — для
   изучения и hacking-экспериментов.

**Чего избегаем:** копировать MS GraphRAG-дизайн «в лоб», строить
graph-pipeline до того, как есть корпус, делать MCP/HTTP-серверы до
того, как есть клиенты, лепить web-UI просто потому что у `mnemovault`
он есть.

**Главное.** Большинство community-LLM-Wiki-проектов решают одну и ту
же задачу (canon + ingest + hot-cache + hybrid retrieval), и решают её
похоже. GraphRAG — это другой класс задач (query-focused summarization,
multi-hop reasoning), и берётся он *поверх* уже работающей вики, а не
вместо неё. На стадии FA «исследование + начало модулей» нам нужна
вики-сторона; graph-сторона — следующий шаг, и вход в неё лучше через
LightRAG/HippoRAG, а не через Microsoft GraphRAG.

## 9. Fact-check и скепсис

- **graphify «71.5x fewer tokens per query»** — claim из README, без
  публикованной методологии. Принимаем как порядок-величины.
- **gbrain «17 888 страниц»** — production у одного пользователя
  (Garry Tan); не воспроизводимо для других.
- **LightRAG «99% reduction»** — abstract paper, зависит от
  конфигурации и корпуса.
- **HippoRAG «single-step multi-hop»** — на конкретных бенчмарках;
  generalization не гарантирована.
- **nano-graphrag «~800 LoC»** — растёт по мере добавления фич, на
  момент v0.0.x.
- **35K звёзд graphify** — недавний viral-launch, не steady-state.
- **agent-creativity gist** — это long-form блог об agentic-local-brain
  (уже в batch-1), а не отдельный проект.
- **Глубину чтения GraphRAG-имплементаций** ограничил уровнем README+
  abstract; глубокий код-аудит — отдельная задача, если решим
  применять конкретную библиотеку.

## 10. Sources

Community-проекты: [gbrain](https://github.com/garrytan/gbrain) (TS,
11.5K⭐) · [llm-wiki-kit](https://github.com/MauricioPerera/llm-wiki-kit)
(TS/Deno, 10⭐) · [obsidian-wiki](https://github.com/ar9av/obsidian-wiki)
(skill-fw, 697⭐) · [sparks](https://github.com/yogirk/sparks) (Go, 9⭐) ·
[mnemovault](https://github.com/kimsiwon-osifa7878/mnemovault) (web-app,
10⭐) · [graphify](https://github.com/safishamsi/graphify) (Python, 35K⭐) ·
[Oshayr/LLM-Wiki](https://github.com/Oshayr/LLM-Wiki) (36⭐, упомянут в
досье 5; глубоко не разобран) ·
[agent-creativity gist](https://gist.github.com/agent-creativity/a4e090f888a516b313ddd1302e51c286)
(long-form блог об agentic-local-brain — уже в batch-1).

Research-backed GraphRAG: [microsoft/graphrag](https://github.com/microsoft/graphrag)
(32.5K⭐; Edge et al., *From Local to Global*, arXiv:2404.16130, 2024) ·
[LightRAG](https://github.com/HKUDS/LightRAG) (34.3K⭐; Guo et al.,
arXiv:2410.05779, EMNLP 2025) ·
[HippoRAG](https://github.com/OSU-NLP-Group/HippoRAG) (3.4K⭐;
Gutiérrez et al., arXiv:2405.14831, NeurIPS 2024) ·
[nano-graphrag](https://github.com/gusye1234/nano-graphrag) (3.8K⭐,
референс-имплементация MS GraphRAG).

Карта связи с предыдущим research:
[batch-1](./llm-wiki-community-batch-1.md) ·
[critique](./llm-wiki-critique.md) ·
[critique-first-agent](./llm-wiki-critique-first-agent.md).

Досье пользователя: `~/attachments/.../4.gbrain_dossier.md`,
`5.llm-wiki-kit_dossier.md`, `6.obsidian-wiki_dossier.md`,
`7.sparks_dossier.md`.
