---
title: "Architect/Planner — рефакторинг системного промпта (v2.1, RU)"
compiled: "2026-04-26"
source:
  - knowledge/prompts/architect-fa.md
  - knowledge/prompts/architect-fa-compact.md
  - предыдущие версии Architect prompt (v1.0 и GPT-5.5 refactor) — приложены к
    исходному запросу, в репозиторий не коммитились
chain_of_custody: "Сам системный промпт лежит в knowledge/prompts/architect-fa.md
  и knowledge/prompts/architect-fa-compact.md. Цитаты конкретных правил/полей —
  оттуда. Ссылки на исследования (TDP, GraSP, VeriPlan, Reflexion и т.д.) — из
  attached improvements-research документа, перепроверять по arxiv-URL при
  использовании конкретных чисел."
claims_requiring_verification:
  - "TDP снижает потребление токенов до 82% — цифра из abstract attached
    research; перед цитированием перепроверить по arxiv 2601.07577."
  - "WHO Surgical Safety Checklist снизил смертность на 47% — Haynes et al.,
    NEJM 2009; перепроверить."
  - "Reflexion / Self-Verifying Reflection: формальная гарантия улучшения при
    ограниченных ошибках верификации — теоретический результат, перепроверить
    по оригинальной статье."
---

# Architect/Planner — рефакторинг системного промпта (v2.1)

> **Статус:** active research note. Описывает рефакторинг системного промпта
> для роли Architect/Planner в multi-agent стэке Agent-FA. Конечный артефакт
> рефакторинга — два файла промптов в [`knowledge/prompts/`](../prompts/):
> [`architect-fa.md`](../prompts/architect-fa.md) (full) и
> [`architect-fa-compact.md`](../prompts/architect-fa-compact.md) (compact).
>
> Эта заметка — рассуждение и обоснование: что было плохо в исходных версиях
> промпта, какие принципы дизайна выбраны, почему v2.1 должен работать лучше,
> что осталось нерешённым.
>
> Связанные заметки:
> - [`agent-roles.md`](./agent-roles.md) — структурный ландшафт ролей агентов;
>   v2.1 ложится на роль «Architect / Planner» из его §5.
> - [`agentic-memory-supplement.md`](./agentic-memory-supplement.md) и
>   [`ai-context-os-memm-deep-dive.md`](./ai-context-os-memm-deep-dive.md) —
>   контекст-инжиниринг и память. v2.1 наследует принципы bounded reading и
>   evidence floor оттуда.

## TL;DR

- Исходный системный промпт Architect v1.0 был **процедурно перегружен**:
  10-стейтовый FSM, три параллельных YAML-артефакта (`plan.md`,
  `coder-handoff.yaml`, `debugger-handoff.yaml`), фиксированный словарь
  действий, обязательные секции invariants/edge-cases/regression на каждую
  задачу. Для open-source planner-моделей (Kimi-2.6, GLM-5.1) это превращается
  в process theater: красивые планы, в которых 30% объёма — церемония, а
  команды/файлы галлюцинированы.
- Промежуточный рефакторинг (GPT-5.5) исправил большую часть бюрократии:
  компактный markdown, единый артефакт, evidence section, delta replan.
  Но он перетянут в сторону Terminal-Bench / unattended execution и
  недостаточно учитывает топологию **planner сильнее coder/reviewer**.
- v2.1 решает обе проблемы: (а) обобщён под любые real-repo задачи (код,
  инфра, данные, документация, рефакторинг, конфиг), (б) усилен под более
  слабые downstream-агенты (правило step independence, acceptance taxonomy,
  фиксированный порядок полей шага).
- Итог: **один масштабируемый формат**, **типизированный evidence floor**,
  5-полевый контракт шага, жёсткий запрет галлюцинаций, двухуровневая
  блокировка, локальное восстановление через Delta Plan, и pre-output
  self-check из 11 пунктов. Системные промпты — в
  [`knowledge/prompts/`](../prompts/).

## 1. Контекст и постановка задачи

Architect/Planner — отдельная роль внутри multi-agent стэка Agent-FA.
Её работа: декомпозиция задачи, scoping, control контекста, sequencing,
качество handoff'а в coder/reviewer, обработка failure recovery.

Исходные допущения, повлиявшие на дизайн v2.1:

1. **Planner — top-tier open-source модель** (Kimi-2.6 / GLM-5.1-class через
   API). Хорошо следует stable Markdown-разметке и коротким правилам;
   плохо следует глубоко вложенным YAML-схемам и многослойным FSM.
2. **Coder и Reviewer — более слабые модели.** Они **не достраивают** контекст
   между шагами, **не обобщают** паттерны вида «follow the pattern in X»,
   **тихо роняют** опциональные поля, **не выносят** семантических суждений.
   Любая церемония в плане, требующая инференса, превращается в источник
   ошибок.
3. **Задачи общеинженерные.** Не только Linux+Docker+pytest — также инфра
   (Terraform/Helm), данные (pipelines, schemas), фронтенд, embedded,
   refactor across monorepo, документация (RFC/ADR), конфиги.
4. **Сессии бывают и интерактивные, и unattended.** Бенчмарки и автономные
   запуски без живого пользователя; локальные сессии с пользователем рядом.
   Поведение блокировки должно покрывать оба случая.
5. **Бюджет токенов реальный.** Особенно у coder/reviewer. Architect должен
   выдавать **минимально достаточный** план, а не максимально полный.

## 2. Диагноз исходного промпта v1.0

Что осталось ценного и попало в v2.1:

- Разделение `intent` / `accept` per step.
- Идея bounded reading.
- Идея scope.
- Batched clarification.
- Явный список anti-patterns.
- Декомпозиция ролей Architect/Coder/Reviewer.

Что было сломано — конкретно:

1. **FSM-театр.** 10-стейтовый FSM с entry/exit gates требует от модели
   *симулировать* процесс на каждом шаге. Open-source planner-модели
   следуют стабильным заголовкам, но не enforce'ят семантику gate'ов
   через длинный контекст. Заменено коротким упорядоченным чек-листом.
2. **Три артефакта на один план.** `plan.md` + `coder-handoff.yaml` +
   `debugger-handoff.yaml` повторяют одни и те же поля (target, accept,
   verification) трижды. Любая расхождение — дефект, и стоимость в токенах
   утроенная. Заменено единым форматом.
3. **Scope locked ДО clarification.** Перевёрнутая логика. Уточнение
   регулярно меняет scope. Заменено: scope формируется после recon и
   возможного уточнения, и **ревизуется через Delta Plan** при новых
   уликах.
4. **«Architect specifies WHAT, Coder specifies HOW».** Принцип взят
   слишком буквально. Слабые coder-модели **проваливаются** на чистых
   WHAT'ах. Полезное планирование включает **bounded HOW**: какой паттерн
   использовать, какой регион файла, какой именно command. v2.1 явно
   разрешает bounded HOW и запрещает только код/diff'ы.
5. **«One step = one commit».** Оптимизирует git-гигиену, а не успешность
   задачи. Удалено.
6. **Обязательные `risks`, `edge_cases`, `invariants`,
   `integration_checkpoints`, `regression_tests`, `validation_protocol`
   на каждую задачу.** В 80% случаев — filler. Generic «API stays
   backward compatible», который модель сочиняет ради заполнения схемы,
   активно вредит downstream-агентам. Сделано опциональным; разрешены
   только task-specific риски.
7. **Фиксированный порядок чтения с design docs first.** Stale
   `ARCHITECTURE.md` регулярно врёт. Чтение их первыми тратит контекст
   до того, как planner коснулся кода. Изменено: user-named files →
   affected surface → build/run/verify configs → analogues → conventions →
   specs/RFCs/ADRs только если задача архитектурная или они противоречат
   коду.
8. **«Named file does not exist → insert create step».** Опасный
   default. Если пользователь сказал «отредактируй X», а X нет — это
   улика, что предположения неверны, не разрешение придумать структуру.
   В v2.1 это MUST-block.
9. **«Context budget exceeded → proceed with available context».**
   Поощряет уверенную галлюцинацию. Заменено: либо сужать scope, либо
   искать прицельнее, либо отметить недостающие пункты как `UNKNOWN` и
   продолжить с явной пометкой.
10. **«Re-enter ANALYZE» как стратегия восстановления.** Выбрасывает
    выполненную работу. Заменено Delta Plan'ом с
    `Keep / Invalidate / Replace`.
11. **Action vocabulary из 6 глаголов.** Реальный repo-work включает
    `read`, `search`, `migrate`, `revert`, `install`, `regenerate` и
    т.д. Принуждение к 6 глаголам приводит либо к мисклассификации, либо
    к разбуханию `notes:`. Удалено.
12. **Процесс важнее результата.** Промпт оптимизирован под чистоту
    ролей и исчерпывающую структуру. Каждое правило проходит тест
    «звучит правильно» и проваливает тест «увеличивает ли pass-rate на
    реальных задачах».

Типичные failure modes под v1.0 на сложных задачах:

- Планы выглядят полными, но не grounded в репо: придуманные команды,
  пути файлов, имена тестов.
- Architect блокируется на underspecified user input во время бенчмарка,
  где живого пользователя нет.
- Планы разрастаются до 12-20 шагов, потому что схема награждает полноту.
- После failure'а coder'а — full re-plan теряет валидную работу.
- Validation theater: поле `verifies: tests pass` без пути и без команды.

## 3. Что было в GPT-5.5 рефакторинге

Сильно лучше v1.0:

- Один компактный формат вместо трёх артефактов.
- Evidence section с фактами и путями.
- Заголовок «Direct Coder Handoff» для тривиальных задач.
- Delta Plan для recovery.
- Запрет на изобретение команд, файлов, паттернов.

Оставшиеся слабости (которые v2.1 закрывает):

- **Два формата** (Direct Handoff vs Full Plan) — лишний switch для
  слабого coder'а; не поддерживает in-flight upgrade тривиальной задачи в
  стандартную.
- **Evidence как свободная проза** — нет типизированного floor'а; легко
  пропустить build/run/test/lint/typecheck.
- **Recon priority с уклоном на manifests** — плохо подходит для
  не-кодовых задач (RFC, инфра, данные, doc-only).
- **Decide vs block смещён в сторону unattended** — для интерактивных
  сессий планировщик слишком редко спрашивает, теряя дешёвый round-trip,
  который сэкономил бы часы.
- **Step Independence не закреплена.** Слабый coder читает шаг
  изолированно; «как в S2» провалится. v2.1 делает это hard rule.
- **Acceptance свободна** — разрешает «no regressions», что слабый
  reviewer проверить не может. v2.1 добавляет Acceptance Taxonomy.

## 4. Принципы дизайна v2.1

1. **Plan for the weakest downstream agent.** Coder и reviewer слабее
   planner'а. Planner делает за них когнитивную работу, которую они не
   потянут.
2. **Step independence.** Каждый шаг исполним и проверяем при чтении
   только Evidence + Scope + Assumptions + сам шаг. Никаких
   cross-step pronouns.
3. **Mechanical acceptance.** Каждый `accept:` — литеральный предикат,
   который reviewer может проверить без суждений.
4. **Sticky schema.** Поля шага в фиксированном порядке; пустое поле —
   `-`; никогда не пропускается. Слабые модели роняют опциональные
   поля.
5. **Generalized evidence.** Список `verify_methods` адаптивен: build,
   run, unit-test, integration-test, lint, typecheck, format, CI,
   manual procedure — то, что реально есть в репо.
6. **Two-tier blocking.** MUST-block по безопасности; MAY-block один
   раз на дорогую неоднозначность в интерактивной сессии; иначе —
   решение + assumption.
7. **No invented facts.** Всё процитированное — из recon-evidence или
   labeled assumption.
8. **Smallest correct plan.** Class масштабирует структуру: TRIVIAL →
   1-3 шага; STANDARD → плоский список; LARGE → фазы.
9. **Bounded HOW, no code.** План может называть файлы, регионы,
   функции, команды, ordering rationale; не может содержать код.
10. **Local recovery via Delta Plan.** Сохранять валидную работу;
    переплан только на пострадавший подграф.
11. **Pre-mortem и self-check перед emit.** Внутренний короткий проход
    вместо разросшихся per-step validation полей.
12. **Stable Markdown headings, low schema depth.** OS-модели надёжно
    держат заголовки; глубокая YAML-вложенность дрейфует.

## 5. Структура итогового промпта

Полный промпт — [`knowledge/prompts/architect-fa.md`](../prompts/architect-fa.md).
Compact-вариант — [`knowledge/prompts/architect-fa-compact.md`](../prompts/architect-fa-compact.md).
Здесь — карта секций, чтобы можно было быстро ориентироваться.

- **Operating priorities** — 8-пунктовый приоритет от correctness до
  token efficiency.
- **Hard rules** — жёсткие запреты: no invented facts, no code, no
  cross-step refs, no judgment-based accept.
- **Step 1 — Classify** — TRIVIAL / STANDARD / LARGE; misclassify-down
  OK.
- **Step 2 — Bounded recon** — бюджеты 4 / 8 / 16 reads-or-searches;
  recon priority generalized.
- **Step 3 — Decide vs block** — MUST-block (4 кейса) / MAY-block
  (interactive only) / Otherwise decide.
- **Step 4 — Plan format** — единый формат с разделами Class / Goal /
  Evidence / Scope / Assumptions / Constraints / Plan / Verification /
  Risks / Open questions.
- **Step writing rules** — 7 правил для шагов, ориентированных на
  слабый coder.
- **Acceptance Taxonomy** — 11 шаблонов литеральных предикатов; список
  запрещённых форм.
- **Verification** — focused / regression / manual; всё repo-native.
- **Step 5 — Pre-output self-check** — 11 пунктов, items 3/4/6/7 —
  hard fail.
- **Step 6 — Delta Plan** — Trigger / Keep / Invalidate / Replace /
  Updated verification.
- **Anti-patterns** — список того, что **не** делать.
- **Worked example** — один TRIVIAL пример с заполненными полями
  (формат-якорь).

## 6. Почему v2.1 должен работать лучше

Сравнение с v1.0:

- **Self-contained шаги переживают слабого coder'а.** Самый частый
  failure слабых исполнителей — частичный pattern matching: читают шаг,
  не находят упомянутый паттерн и либо пропускают, либо изобретают.
  Правила `do:` делают шаг полной инструкцией.
- **Mechanical acceptance переживает слабого reviewer'а.** Слабый
  reviewer не может судить «корректно ли это» — может только проверять
  предикаты. Acceptance Taxonomy даёт ему только проверяемые предикаты.
- **Sticky schema переживает field-dropping.** OS-модели под нагрузкой
  роняют опциональные поля. Фиксированный порядок плюс `-` для пустых
  делает дрейф детектируемым и редким.
- **Generalized evidence schema подходит для не-кодовой работы.** Infra
  plans, data plans, doc plans, config plans теперь укладываются в тот
  же формат.
- **Two-tier blocking подходит обоим режимам.** Unattended — decisive
  default; interactive — один batched вопрос когда стоимость оправдана.
- **Hallucination guard enforced** через self-check items 3 и 4 — оба
  hard fail перед emit.
- **Delta Plan делает recovery хирургическим.** Никакого «restart
  ANALYZE»-расхода.
- **No cross-step references.** Убирает доминирующий failure mode
  слабых coder'ов.

Сравнение с GPT-5.5:

- Step Independence Rule и field-order discipline — самый большой
  выигрыш качества плана для слабых downstream-агентов.
- Acceptance Taxonomy превращает «observable» в список конкретных форм
  предикатов; GPT-5.5 оставлял это implicit.
- Generalized recon priority и `verify_methods` делают промпт пригодным
  для доменов, где GPT-5.5 был неудобен.
- Two-tier blocking убирает bias GPT-5.5 в сторону unattended-only
  поведения.

## 7. Связь с improvements-research

Из приложенного исследовательского документа (12 предложенных улучшений)
в v2.1 включены — в облегчённой форме — следующие, и явно отвергнуты
другие:

**Включено (в облегчённой форме):**

- **DAG вместо линейного списка** (TDP, GraSP). Реализация: поле `deps:
  [Sx]` на шаг. Без явных graph-схем — слабые модели их не держат.
- **Pre-mortem** (Klein 1998). Реализация: один внутренний проход в
  Step 5; в план попадают только task-specific риски, без generic
  filler'а.
- **WHO checklist** (Haynes 2009). Реализация: один pre-output
  self-check из 11 пунктов вместо 6 yes/no на каждый шаг.
- **WBS hierarchy** — условно. Реализация: phases в LARGE-задачах; не
  по умолчанию для STANDARD.
- **Self-Verifying Reflection.** Реализация: pre-output self-check;
  items 3/4/6/7 — hard fail перед emit.

**Отвергнуто (с причиной):**

- **Формальная верификация / model checking** (VeriPlan). Это работа
  кода (структурный валидатор плана в orchestrator'е), не промпта.
  Помечено как Phase-2 follow-up в §11.
- **Critical Path.** Поле `estimated_complexity` не калиброванно у LLM;
  CP, построенный на таких оценках, хуже, чем его отсутствие.
- **Типизированные рёбра зависимостей** (GraSP). Schema bloat; planner
  может выразить тип зависимости в `do:` когда это важно.
- **OODA loop как named framework.** Имя добавляет нагрузку без
  выигрыша; заменено явным циклом probe → plan → execute → replan.
- **Design by Contract per step.** `pre`/`post`/`invariant` — filler в
  90% случаев; одного `accept` достаточно.
- **Confidence scoring.** LLM-калибровка слабая; цифры вводят в
  заблуждение даже когда выглядят авторитетно.
- **Explicit context budget meter.** Модель не считает токены; правила
  «stop when next read won't change …» работают надёжнее цифр.

## 8. Two-tier blocking — тонкости

`MUST block` — четыре кейса: contradictory requirements, irreversible
action with ambiguous intent, falsified user-stated precondition,
missing creds/network/service. Эти кейсы блокируют **всегда**, в любой
сессии.

`MAY block` — только в **interactive** сессии, при выполнении всех
условий: один ответ меняет scope/order/approach, и default-rework
дороже, чем стоимость одного round-trip'а. Все вопросы — в одно
сообщение.

Otherwise — decisive default, log в `Assumptions`, при необходимости
добавить verify-шаг, который поймает неверное предположение.

Калибровка «default-rework vs round-trip» остаётся открытой проблемой;
см. §10.

## 9. Acceptance Taxonomy — почему именно так

Слабый reviewer-агент способен:

- Запустить команду и проверить exit code.
- Прочитать файл и проверить наличие/отсутствие подстроки.
- Запустить тест и проверить pass/fail.
- Сравнить два литерала.

Слабый reviewer-агент **не способен**:

- Прочитать diff и судить «соответствует ли намерению».
- Проверить семантическую корректность.
- Проверить cross-file invariants.
- Оценить side effects.

Поэтому `accept:` ограничен 11 шаблонами из первого списка. Запрещённые
формы («tests pass», «no regressions», «works», «user can <X>» без
скриптованной проверки) — все из второго.

Если шаг **реально** требует multi-predicate acceptance — разбить на
несколько шагов, или выписать предикаты пронумерованным списком, где
каждый пункт независимо вписывается в taxonomy.

## 10. Failure modes, которые не закрываются промптом

- Промпт не гарантирует, что слабая модель сделает аккуратный recon.
  Плохой recon → плохой план, независимо от структуры.
- Self-check — это LLM-on-LLM верификация. Planner может «подмахнуть»
  чек-лист. Реальная валидация — на коде (CI gate или структурный
  валидатор плана).
- Качество `accept:` ограничено качеством тестов в репо. Если тесты
  тонкие, проходящий `accept` всё равно может скрыть дефект.
- Field-order discipline держится, пока planner остаётся в режиме
  промпта. Длинные распыляющие user-промпты могут деградировать
  следование схеме.
- Two-tier blocker требует от planner'а оценить «стоимость default vs
  стоимость round-trip». Калибровка модель-зависима.
- Step Independence увеличивает токенную стоимость на шаг (паттерны
  inline'ятся). На очень длинных планах — реальный hit бюджета.
  Смягчается Class scaling и smallest-plan principle.
- Manual verification («посмотри в браузере») всё ещё требует человека
  или сильной vision-модели. Слабый reviewer не справится.
- Acceptance Taxonomy — меню, не парсер. Креативный planner может
  написать accept, который выглядит таксономически, но им не является.
  Без code-side валидации не предотвратить.
- Задачи, требующие deployment или долго-живущего сервиса, нуждаются в
  инфраструктуре за пределами промпта.

## 11. Что дальше (опционально, не блокирует использование)

- **Phase 2 — структурный валидатор плана.** Pydantic-модель,
  отражающая v2.1-схему, плюс CI-gate в orchestrator'е. Перевод hard
  rules в machine-checked гарантии (acyclic deps, in-scope targets,
  taxonomic accept).
- **Few-shot library.** Отдельная директория с одним worked example на
  каждый класс задач (code, infra, docs, refactor). Orchestrator
  инжектит 1-2 примера после системного промпта в зависимости от
  domain'а задачи. Сейчас в промпте один пример; до 3+ примеров
  выделять отдельный файл преждевременно.
- **JSON-schema variant** для tool-calling planner'ов. Имеет смысл
  только когда orchestrator парсит и роутит структурный output, и
  когда подтверждено, что Kimi/GLM стабильно выдают JSON чище, чем
  Markdown в этом стэке. Сейчас отложено.
- **Калибровка two-tier blocking.** На реальных interactive сессиях —
  собрать примеры, где MAY-block сработал/не сработал, и подкрутить
  условие.
- **Coder и Reviewer system prompts.** Эти роли — отдельные документы;
  должны зеркалить контракт Architect'а (читают именно те поля, что
  emit'ит planner; reviewer проверяет именно те предикаты, что в
  Acceptance Taxonomy).

## 12. Sources

Первоисточники, на которые опирается дизайн (для chain-of-custody при
цитировании конкретных чисел):

- Task-Decoupled Planning (Li et al., 2026) — https://arxiv.org/abs/2601.07577
- GraSP — Graph-Structured Skill Compositions (Xia et al., Tencent, 2026) —
  https://arxiv.org/html/2604.17870v1
- Chasing Progress, Not Perfection (Huang et al., 2025) —
  https://arxiv.org/html/2412.10675v1
- VeriPlan (Lee et al., 2025) — https://arxiv.org/abs/2502.17898
- Structured Decomposition for LLM Reasoning (Sadowski & Chudziak, 2026) —
  https://arxiv.org/pdf/2601.01609
- Self-Verifying Reflection (Yu et al., 2025) — https://arxiv.org/abs/2510.12157
- Pre-mortem analysis (Klein, 1998) — Harvard Business Review, 2007.
- WHO Surgical Safety Checklist — Haynes et al., NEJM, 2009.
- Design by Contract (Meyer, 1986) — Eiffel/Ada/SPARK literature.
- Claude Code architectural analysis (arxiv 2604.14228v1) — приведено как
  Tier-1 в исходном документе architect-prompt-explained; перепроверять
  по самому arxiv-PDF при цитировании.

Цифры из abstract'ов (например, «-82% токенов» у TDP, «-47%
смертности» у WHO checklist) — перед использованием в принятии решений
перепроверить по первоисточнику. См. `claims_requiring_verification` во
frontmatter.
