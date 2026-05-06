---
title: "Efficient LLM agent harness — deep-dive: разбор PR #37 + углублённый cross-reference на ADR-1..6"
source:
  - "https://arxiv.org/abs/2603.25723"
  - "https://arxiv.org/html/2603.25723"
  - "https://arxiv.org/abs/2603.28052v1"
  - "https://arxiv.org/html/2603.28052v1"
  - "https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool"
  - "https://docs.brightdata.com/ai/mcp-server/tools"
  - "https://www.anthropic.com/news/model-context-protocol"
  - "https://www.anthropic.com/engineering/code-execution-with-mcp"
  - "https://modelcontextprotocol.io/specification/2025-11-25"
  - "https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation"
  - "user attachment: youtube_transcripts.md (Devin attachment 01215dee-a768-4c7b-88a4-fd92b37f52db, 321 lines, 3 videos)"
  - "https://github.com/GITcrassuskey-shop/First-Agent/pull/37 — head branch devin/1778072676-efficient-harness-note (file efficient-llm-agent-harness-2026-05.md @ 586 lines, commit d03f7a3)"
  - "../adr/ADR-1-v01-use-case-scope.md"
  - "../adr/ADR-2-llm-tiering.md"
  - "../adr/ADR-3-memory-architecture-variant.md"
  - "../adr/ADR-4-storage-backend.md"
  - "../adr/ADR-5-chunker-tool.md"
  - "../adr/ADR-6-tool-sandbox-allow-list.md"
  - "./how-to-build-an-agent-ampcode-2026-04.md"
  - "./cutting-edge-agent-research-radar-2026-05.md"
  - "./semi-autonomous-agents-cross-reference-2026-05.md"
  - "./agent-roles.md"
  - "./latent-verifier-evolve-research-2026-05.md"
compiled: "2026-05-06"
chain_of_custody: |
  Primary-source facts вытащены напрямую из URL-ов выше: arXiv abstract HTML
  для двух papers (Tsinghua NLAH 2603.25723 и Meta-Harness 2603.28052v1, оба
  March 2026), Anthropic engineering blog (code-execution-with-mcp,
  Nov 04 2025), Claude API docs (tool-search-tool с конкретными API
  identifiers tool_search_tool_regex_20251119 / bm25_20251119), Bright Data
  MCP tools reference (Rapid / Pro modes + 11 групп + GROUPS env var). Числа
  из YouTube-транскриптов (Tsinghua: -0.8 SWE-bench, -8.4 OSWorld, -5.6
  multi-candidate; OSymphony 30.4% → 47.2% при code-to-text migration;
  Meta-Harness 76.4% TerminalBench-2 + harness-transferability across 5
  held-out models) сверены с arxiv abstracts, где это возможно: abstract
  Meta-Harness подтверждает 7.7-point gain + 4× fewer context tokens на
  online text classification и 4.7 points average на 200 IMO problems
  across five held-out models. Конкретные ablation-numbers Tsinghua
  (-0.8 / -8.4 / -5.6) видны только в видео-нарративе и помечены как
  inferred-from-secondary; full text paper не парсился построчно (HTML
  truncated в fetch). Все ADR-факты — из локального git checkout
  origin/main HEAD на 2026-05-06. PR #37 review-комментарии (id
  3195678921, 3195700104, 3195729059, 3195730682) прочитаны через `git`
  tool action=view_pr. Атрибуция Meta-Harness к Stanford в Video 3 — это
  video-claim; arxiv submitter Yoonho Lee (Stanford ML PhD lineage), DSPy
  reference в нарративе совпадает с Khattab, но affiliation в abstract
  явно не выписан — помечен как unresolved attribution в §8.
goal_lens: "Gap analysis vs accepted ADR-1..6 + явное выявление, что PR #37 (efficient-llm-agent-harness-2026-05.md) исследовал поверхностно или пропустил, до того как ADR-7 будет писаться."
tier: stable
links:
  - "../adr/ADR-1-v01-use-case-scope.md"
  - "../adr/ADR-2-llm-tiering.md"
  - "../adr/ADR-3-memory-architecture-variant.md"
  - "../adr/ADR-4-storage-backend.md"
  - "../adr/ADR-5-chunker-tool.md"
  - "../adr/ADR-6-tool-sandbox-allow-list.md"
  - "./efficient-llm-agent-harness-2026-05.md"
  - "./how-to-build-an-agent-ampcode-2026-04.md"
  - "./cutting-edge-agent-research-radar-2026-05.md"
  - "./semi-autonomous-agents-cross-reference-2026-05.md"
  - "./agent-roles.md"
  - "./latent-verifier-evolve-research-2026-05.md"
mentions:
  - "Anthropic"
  - "Bright Data"
  - "Cloudflare"
  - "Tsinghua University"
  - "Harbin Institute of Technology Shenzhen"
  - "Stanford / Khattab / DSPy"
  - "MCP Foundation / Agentic AI Foundation"
  - "Linux Foundation"
  - "Claude Opus 4.6 / 4.7"
  - "Cursor / Codex / Cloud Code"
  - "Manus / Vercel"
  - "Cloudflare Code Mode"
confidence: extracted
claims_requiring_verification:
  - "Tsinghua module-ablation deltas (-0.8 SWE-bench, -8.4 OSWorld, -5.6 multi-candidate search) — взяты из YouTube-нарратива Video 3; abstract на arxiv.org/abs/2603.25723 их не печатает (нужно открывать full HTML / PDF). До того как опираться на эти числа в ADR-7 §Decision, их нужно сверить с Tables 4-6 в paper PDF."
  - "OSymphony code→text migration 30.4% → 47.2% (Tsinghua paper) — также video-claim; abstract упоминает «code-to-text harness migration» как experimental section, но без явных чисел в abstract. Нужна проверка по full paper Section 5."
  - "Meta-Harness «harness optimized on one model transferred to 5 other models, improving them all» — abstract говорит +4.7 points average across five held-out models на math reasoning, что подтверждает transfer на one benchmark family, но НЕ глобальную «works across the model landscape» формулировку из видео. Generalization-claim из видео сильнее, чем из abstract."
  - "Атрибуция Meta-Harness к Stanford — video-claim. arxiv submitter Yoonho Lee, упоминание Khattab/DSPy в Video 3 совпадает с MIT/Stanford lineage, но affiliation в abstract HTML, которое мы получили, явно не выписано. Нужна проверка по full paper title page."
  - "«Manus rewrote harness 5× in 6 months», «Vercel removed 80% of agent tools» — video-claims без primary URL. Не цитировать в ADR без независимой проверки (например, через Manus/Vercel public engineering blogs)."
  - "TOON encoding 30-60% reduction vs JSON для flat tabular data — video-claim, отдельной primary-source URL в наборе нет. Не предлагается для FA, поэтому acceptable as backlog-only fact."
  - "Тezis «verifiers actually start hurting» — основан на Tsinghua ablation. Прямые primary numbers нужно достать из full paper до того, как ADR-2 amendment 2026-04-29 §point 5 («v0.1 inner-loop has no Critic / Reflector role») получит цитату из этой работы."
topic: "harness-engineering, tool-disclosure, mcp-forward-compat, adr-7-prep, gap-analysis-pr37"
---

> **Status:** active. Эта нота — *углублённое продолжение* PR #37
> ([efficient-llm-agent-harness-2026-05.md](https://github.com/GITcrassuskey-shop/First-Agent/blob/devin/1778072676-efficient-harness-note/knowledge/research/efficient-llm-agent-harness-2026-05.md)),
> а не его supersession. PR #37 ещё не смержен; этот файл фиксирует
> то, что PR #37 покрыл поверхностно или пропустил, и предлагает
> рекомендации в форматах, прямо совместимых с ADR-7 prep. При
> merge PR #37 этот файл станет дополнением; при rejection PR #37
> этот файл может стать единственным harness-research-source-of-truth
> и тогда потребует minor уточнения статуса (R-7 покрывает merge-order
> contingencies). Произведено через
> [`knowledge/prompts/research-briefing.md`](../prompts/research-briefing.md)
> workflow.

## 0. Decision Briefing

Девять рекомендаций (`R-1..R-9`) для ADR-7 prep. Из них две —
`UNCERTAIN-ASK`, требуют user-input до фиксации в ADR-7 (это
методологический контраст с PR #37, где UNCERTAIN-ASK было ноль —
см. §7.2). Goal-lens см. в frontmatter и §2.

### R-1 — Зафиксировать MCP forward-compat для tool-disclosure (3 уровня) на shape-уровне

- **What:** ADR-7 должен описать tool-disclosure как тройную discriminated-union на уровне registry shape, без runtime: `(a)` server-name list, `(b)` per-tool one-line descriptors, `(c)` full JSON Schema. Это shape, который Anthropic документирует под `defer_loading: true` + `tool_search_tool_*_20251119`, и который Bright Data реализует как `groups` / `tools` env-vars. Цель — чтобы v0.2-переход на BM25-based tool-search или MCP-server distribution был config-only.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: YES (в первом prompt только descriptors, не full schemas — экономия порядка размера типичного `~55k`-tools-definitions baseline из Anthropic docs).
  - (B) helps LLM find context when needed: YES (pointer-shape: descriptor → schema → tool-call dispatch — три hop вместо одного gigantic upfront blob).
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens: YES (это **прямое** дополнение к ADR-2 §Amendment 2026-05-01 §point 4 — «ADR-7 inherits convention; MAY add fields but MUST NOT change»; PR #37 §6 это inheritance-constraint не вытащил как hard-rule).
- **Cost:** cheap (это shape-decision на бумаге, ~0 LoC сверх того, что ADR-2 §Amendment уже фиксирует).
- **Verdict:** TAKE
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** ADR-7 фиксирует одну форму (`name + full schema upfront`) и при v0.2 catalog-роста нужно будет ломать `models.yaml` и `~/.fa/sandbox.toml` consumers. Cost-of-rejection: 1-2 дня на v0.2 cleanup vs 0 дней сейчас.
- **Concrete first step (if TAKE):** В ADR-7 §Decision добавить блок `### Tool disclosure tiers` с тремя shape-таблицами и явной ссылкой на ADR-2 §Amendment 2026-05-01 §point 4 («inherits convention»).

### R-2 — Разделить `events.jsonl` (raw machine trace) и `hot.md` (human/agent summary) как два разных артефакта с anti-summary-rot инвариантом

- **What:** ADR-7 должен зафиксировать два независимых на disk-layer артефакта одного session: `~/.fa/state/runs/<run_id>/events.jsonl` (append-only, raw, every tool request/response/permission/decision) и `hot.md` (LLM-readable summary, перезаписываемый). Инвариант: `hot.md` **никогда** не источник для self-evolution; replay/eval/Meta-Harness-style посмертный анализ читают только `events.jsonl`. Это прямой ответ на abstract Meta-Harness paper: «existing text optimizers compress feedback too aggressively».
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: YES (новая сессия читает small `hot.md` для context; raw trace доступен по path, не по pre-load).
  - (B) helps LLM find context when needed: YES (pointer-shape — `hot.md` cite-ит `events.jsonl` paths/byte-offsets; selective `grep`/replay возможны).
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens: YES (закрывает gap PR #37 §5.3, где raw-traces-vs-summaries упомянуты, но invariant «summary-MUST-NOT-replace-trace» не вытащен как hard-rule на уровне ADR-3 amendment surface).
- **Cost:** medium (trace schema + writer + retention rule + `hot.md` ↔ `events.jsonl` cite-format в существующем ADR-3 hot.md spec).
- **Verdict:** TAKE
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Хранить только summaries (`hot.md` + handoff); accept Meta-Harness paper-warning о signal loss и допустить, что v0.2 self-evolution / failure-diagnosis работа будет упираться в перепрогон сессий с нуля.
- **Concrete first step (if TAKE):** В ADR-7 §Decision добавить `### Trace separation invariant` с JSON-схемой `events.jsonl` event и формальной формулировкой инварианта; в ADR-3 §Decision добавить one-line amendment-stub: «`hot.md` cite-ит paths в `events.jsonl`; `events.jsonl` — canonical source-of-truth для replay/eval» (или оставить amendment в follow-up ADR).

### R-3 — Reuse SQLite FTS5 (ADR-4) как BM25-движок для будущего tool-search

- **What:** Зафиксировать в ADR-7, что когда v0.1 tool catalog перерастёт ~10 tools, BM25 tool-search реализуется поверх **существующего** `~/.fa/index.sqlite` через тот же FTS5 virtual-table-механизм, который ADR-4 уже выбрал для chunk-retrieval. Описать это явно как «extension point», не как v0.1 feature. PR #37 этот мост не построил (ADR-4 указан в §6 cross-reference, но без явного утверждения «BM25 tool-search reuses ADR-4 SQLite FTS5 без новых deps»).
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: PARTIAL (ADR-7 не реализует tool-search в v0.1; benefit виртуальный, материализуется при росте catalog).
  - (B) helps LLM find context when needed: YES (когда сработает, agent ищет tool по natural-language query через тот же primitive, что и chunks).
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens: YES (ADR-7 inheritance pattern — пере-использовать существующее ADR-4 решение, а не вводить новую dependency; это subtraction-первый принцип в чистом виде).
- **Cost:** cheap (decision-only; реальная реализация — v0.2 при росте catalog, отдельный PR).
- **Verdict:** TAKE
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Когда tool-search станет нужен, ввести `rank-bm25` или внешний embedding-сервис как новую dependency; нарушить «zero new deps» обещание ADR-4 §Option B.
- **Concrete first step (if TAKE):** В ADR-7 §Notes добавить one-paragraph ссылку: «If/when tool-search lands, use ADR-4 FTS5 index with `tools` virtual table — no new dependency».

### R-4 — Расширить ADR-6 sandbox: добавить `tool_groups` allow-list по shape Bright Data `GROUPS` env-var

- **What:** Ввести в ADR-6 §Policy file одно дополнительное TOML-секцию `[tool_groups]`, аналогичную `[read]/[write]`, но с allow-list **тегов** на тулзы (`coding`, `git`, `web_search`, `memory`, …). Регистрация тула в ADR-7 registry требует один или больше тегов; ADR-6 sandbox блокирует tool-call, если ни один из тегов тула не входит в `tool_groups.allow`. Это даёт session-level scoping shape, аналогичный Bright Data `GROUPS=ecommerce,finance` env-var, но per-session, не per-server. PR #37 §5.4 упомянул Bright Data только как «design analogy», без конкретного TOML-shape.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: YES (агент в session-режиме «code-only» не видит описаний `web_search` тулов вообще).
  - (B) helps LLM find context when needed: YES (descriptor-tier registry фильтруется до session-relevant subset на этапе sandbox-check, не на этапе LLM choice).
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens: YES (это прямое расширение ADR-6 без изменения существующего `[read]/[write]` semantics; ADR-6 §Re-evaluation triggers явно оставляет место для дополнительных allow-lists).
- **Cost:** medium (TOML schema + dispatcher hook + миграция всех future tools на обязательный `tags` field).
- **Verdict:** TAKE
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Reuse `[read]/[write]` allow-list для tool-scoping (не подходит: filesystem path и tool-name — разные namespaces). Или вводить session-scope в самом ADR-7 registry (получится дубль allow-list-механизма с ADR-6).
- **Concrete first step (if TAKE):** В ADR-7 §Decision добавить «каждый ToolSpec обязан декларировать `tags: list[str]`»; в ADR-6 (или follow-up amendment ADR-6.1) добавить `[tool_groups]` секцию с примером.

### R-5 — Прибить «no Critic / verifier loops в v0.1» с primary-source numbers, а не video-claims

- **What:** ADR-2 §Amendment 2026-04-29 §point 5 уже говорит «v0.1 inner-loop has no Critic / Reflector role». ADR-7 должен сослаться **именно на эту строку** + добавить primary-source numerical evidence из Tsinghua paper (`arXiv:2603.25723`): module-ablation показала, что верификаторы и multi-candidate search активно ухудшают результаты на ряде benchmarks. PR #37 §8 R-5 зафиксировал решение, но опирался на video-нарратив; primary-source citation усиливает аргумент и страхует от reflection-loop fashion в v0.2 review-cycle.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: YES (no Critic role → no extra system prompt + role config block).
  - (B) helps LLM find context when needed: PARTIAL (меньше LLM-generated critique для search; больше зависимость от deterministic logs).
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens: YES (закрывает аргументационный gap PR #37 §8 R-5, который cite-ит транскрипт но не arxiv).
- **Cost:** cheap (это формулировка цитаты; numbers нужно сверить с full paper PDF — см. `claims_requiring_verification`).
- **Verdict:** TAKE
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Ввести always-on Reflector/Critic role в v0.1, измерить (что требует eval-harness, который сам по себе deferred — UC5).
- **Concrete first step (if TAKE):** В ADR-7 §Notes добавить subsection «Why no Critic / verifier in v0.1» со ссылкой на ADR-2 amendment + arxiv link + caveat про verification-of-numbers (см. `claims_requiring_verification` пункт #1).

### R-6 — Defer code-execution-over-MCP в v0.1, **но** оставить registry-shape, который сделает migration config-only

- **What:** Anthropic blog (Nov 2025) показывает 98.7% reduction (150k → 2k tokens) для Google Drive → Salesforce example при code-execution-over-MCP. Это самый сильный efficiency-lever в наборе sources. **Но** он требует sandbox с CPU/time/network limits, redaction для intermediate data, и trustworthy code-execution surface — всё это explicit out-of-scope ADR-6 §Re-evaluation triggers («`run_command` lands → re-evaluate Option C OS-level sandbox»). ADR-7 должен: (a) зафиксировать defer, (b) описать `tools/as_files/<server>/<tool>.ts` export-shape, который будет совместим, когда v0.2 откроет code-execution. PR #37 R-3 это сделал на уровне prose, но без конкретного export-path.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: YES (v0.2-прибыль; v0.1 nothing changes).
  - (B) helps LLM find context when needed: YES (когда сработает — file-system discovery вместо upfront tool definitions).
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens: YES (защита forward-compat, как и R-1).
- **Cost:** cheap (decision + 1 abstract directory layout); expensive если строить (~3-5 ADRs: code-execution, sandbox-OS-level, redaction policy, MCP-server-distribution, Skills format). v0.1 не строит.
- **Verdict:** DEFER
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Строить code-execution-over-MCP сейчас (требует ADR-6 §Option C OS-level sandbox, что по самой ADR-6 «cross-platform cost is high, friction defeats use»; нарушает ADR-1 «pragmatic medium-weight hybrid»).
- **Concrete first step (if DEFER):** В ADR-7 §Notes добавить one-paragraph: «Future code-execution exposes tool registry as filesystem at `~/.fa/state/tools/<server>/<tool>.<ext>`; v0.1 registry produces this layout on demand from ToolSpec descriptors but does not execute. Triggers: `run_command` lands; OS-level sandbox lands; network-redaction lands.»

### R-7 — Зафиксировать subtraction-first ревизионный рубрик ADR-7 как 4-вопросный self-audit

- **What:** Перевести Anthropic «subtraction principle» из видео-нарратива в **executable acceptance-criterion** для будущего ADR-7 review. ADR-7 §Acceptance должен потребовать от реализатора ответить на 4 вопроса (явно из Video 3, последний абзац): (1) что в context-window, что there не нужно? (2) какие tools agent редко использует? (3) есть ли verification/search loops, которые могут вредить? (4) control logic в коде или в тексте? Это превращает design-philosophy в check-list. PR #37 R-1 mentions «subtraction-first» как label, но не как тестируемый рубрик.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: YES (рубрик прямо штрафует context-bloat).
  - (B) helps LLM find context when needed: PARTIAL (вторичный эффект — меньше шума, лучше подбор; первичный эффект на A).
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens: YES (это процедурный механизм; работает как `claims_requiring_verification` для дизайн-решений).
- **Cost:** cheap (это §Acceptance block в ADR-7).
- **Verdict:** TAKE
- **If UNCERTAIN-ASK:** n/a
- **Alternative-if-rejected:** Полагаться на review-PR culture, что reviewer сам спросит «зачем эта компонента». Рискованно — Tsinghua/Stanford evidence в abstract Meta-Harness прямо говорит, что harness-design-by-default-add превращается в 14× compute waste без user-visible benefit (16.3M vs 1.2M tokens per sample на одинаковом результате SWE-bench Verified, see §4.1).
- **Concrete first step (if TAKE):** В ADR-7 §Acceptance добавить четыре пункта чек-листа дословно из Video 3.

### R-8 — UNCERTAIN-ASK: Что делать с system-prompt assembly + prefix-cache invariant?

- **What:** Video 2 (component #7 «System prompt assembly») явно предупреждает: dynamic compose system-prompt из `agents.md` / `cloud.md` / `hot.md` ломает prefix-caching на стороне provider. Это критический ADR-7 design rule, который PR #37 не упомянул вообще. У нас уже есть AGENTS.md + HANDOFF.md + (предполагаемый) `hot.md` — то есть **первая половина** assembly-pipeline уже на disk. Открытый вопрос — *как именно* их склеивать и в каком порядке, чтобы static-частья перед dynamic-частью.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: YES если static-сегменты cache-hit'ятся; иначе NO (rebuild каждый turn).
  - (B) helps LLM find context when needed: YES (assembled prompt всегда содержит правильный набор anchors).
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens: YES (это явный gap vs PR #37, см. §7.1 пункт #6).
- **Cost:** medium (зависит от выбора).
- **Verdict:** UNCERTAIN-ASK
- **If UNCERTAIN-ASK:** Какую стратегию prompt-assembly зафиксировать в ADR-7?
  - **Option (i)** — Static layered prompt: один static system-prompt файл, который не меняется в течение session; dynamic state идёт в первом user-сообщении. Pros: cache-friendly «как в Cloud Code original design». Cons: при добавлении нового AGENTS-rule нужен разрыв sessions.
  - **Option (ii)** — Two-segment assembly: `[static segment: AGENTS.md + ADR-table-of-contents]` префикс, потом `[dynamic segment: hot.md + handoff cite]` суффикс. Provider кэширует только static; dynamic каждый turn re-fed. Pros: гибкий + явный invariant «static перед dynamic». Cons: требует, чтобы провайдер поддерживал partial prefix-cache (Anthropic API через `cache_control` блоки умеет, OSS-провайдеры через OpenRouter — variable).
  - **Option (iii)** — No assembly в v0.1: один minimal system-prompt без AGENTS-injection; вся repo-context подтягивается через retrieval-tools (grep, FTS5). Pros: простейший; auto-cache-friendly. Cons: agent теряет default conventions без вызова `read_file(AGENTS.md)`.
  - **Option (iv)** — Other / write a separate research note focused only on this question.
- **Alternative-if-rejected:** Не фиксировать в ADR-7, оставить implementer free → каждый PR будет переизобретать assembly, и cache-hits будут случайные.
- **Concrete first step (if TAKE one of options):** В ADR-7 §Decision добавить subsection `### Prompt assembly` с выбранной option и формальным invariant о порядке static-vs-dynamic.

### R-9 — UNCERTAIN-ASK: Принимать ли «harness transferability» Meta-Harness claim как подтверждение ADR-2 static role routing?

- **What:** Abstract Meta-Harness paper говорит: «retrieval-augmented math reasoning, single discovered harness improves accuracy on 200 IMO-level problems by 4.7 points on average across five held-out models». Video-нарратив усиливает: «harness optimized on one model transferred to 5 other models, improving them all». Если transferability-claim **прочна**, это сильный аргумент за ADR-2 §Decision-form (один harness, разные модели per role) и **против** v0.2-fashion в сторону «harness-per-model». Если же transferability работает только на одном benchmark family — claim слабый. PR #37 это не разобрал вообще.
- **Project-axis fit (stable across notes):**
  - (A) reduces session-start noise: NO (это design-decision, не context-noise).
  - (B) helps LLM find context when needed: NO (не про context).
- **Goal-lens fit (per session, dynamic):**
  - (C) advances chosen goal_lens: PARTIAL (это про ADR-2, не про ADR-7; gap-relative-to-PR-#37 относится к §6 cross-reference quality).
- **Cost:** cheap (research-only; зависит от того, что user захочет процитировать).
- **Verdict:** UNCERTAIN-ASK
- **If UNCERTAIN-ASK:** Как использовать harness-transferability claim в ADR-формате?
  - **Option (i)** — Зафиксировать как одну из *причин* для ADR-2 static role routing (амендмент-стаб ADR-2 «evidence base extended»). Cost: cheap.
  - **Option (ii)** — Только пометить в `claims_requiring_verification` этой ноты, без ADR-цитаты. Cost: zero.
  - **Option (iii)** — Использовать как trigger для нового research note о cross-model harness стабильности. Cost: medium.
  - **Option (iv)** — Other.
- **Alternative-if-rejected:** Цитировать только видео-claim, не abstract; но это нарушает PR Checklist `compiled >= cited dates` rule в духе («не цитировать secondary, когда есть primary»).
- **Concrete first step:** Дождаться user-выбора одного из вариантов, прежде чем переписать §6.

### Сводная таблица

| R-N | Verdict | Project-fit (A / B) | Goal-fit (C) | Cost | Alternative-if-rejected | User decision needed? |
|-----|---------|---------------------|--------------|------|--------------------------|------------------------|
| R-1 | TAKE | YES / YES | YES (ADR-7 inherits ADR-2) | cheap | Re-design at v0.2 | No (TAKE) |
| R-2 | TAKE | YES / YES | YES (anti-summary-rot) | medium | Summary-only memory | No (TAKE) |
| R-3 | TAKE | PARTIAL / YES | YES (ADR-4 reuse) | cheap | New BM25 dependency | No (TAKE) |
| R-4 | TAKE | YES / YES | YES (ADR-6 extension) | medium | Reuse path-allow-list (mismatch) | No (TAKE) |
| R-5 | TAKE | YES / PARTIAL | YES (primary-cite hardening) | cheap | Always-on Critic | No (TAKE) |
| R-6 | DEFER | YES / YES | YES (forward-compat) | cheap now / expensive if built | Build now (violates ADR-1, ADR-6) | No (DEFER) |
| R-7 | TAKE | YES / PARTIAL | YES (procedural) | cheap | Rely on review culture | No (TAKE) |
| R-8 | UNCERTAIN-ASK | YES / YES | YES | medium | No assembly rule in ADR-7 | **Yes — pick (i)/(ii)/(iii)/(iv)** |
| R-9 | UNCERTAIN-ASK | NO / NO | PARTIAL | cheap | Cite video only | **Yes — pick (i)/(ii)/(iii)/(iv)** |

## 1. TL;DR

- PR #37 — корректный baseline (5 рекомендаций, 4 TAKE + 1 DEFER, бимодальный язык по конвенции репо), но имеет 6 идентифицируемых **gaps** (см. §7.1) и 1 методологический gap (`UNCERTAIN-ASK`-count = 0, см. §7.2).
- Tsinghua paper (`arXiv:2603.25723`, *Natural-Language Agent Harnesses*, March 2026) и Meta-Harness paper (`arXiv:2603.28052v1`, March 2026) **резолвятся**; abstract обоих парсится. Атрибуция Meta-Harness к Stanford из Video 3 — partial: arxiv submitter Yoonho Lee, нарратив указывает на Khattab/DSPy lineage, но affiliation в abstract HTML явно не выписан (см. §8.3).
- Anthropic engineering blog «Code execution with MCP» (Nov 04, 2025) даёт 98.7% reduction (150k → 2k tokens) на конкретном Google-Drive-→-Salesforce example. Это самый сильный efficiency-lever в наборе и одновременно самый рискованный для FA v0.1 (требует sandbox, redaction, OS-level isolation — всё out-of-scope per ADR-6 §Re-evaluation triggers). R-6 = DEFER (как и в PR #37), но мы добавляем явный export-path forward-compat shape.
- Tool-search API в Claude API docs (`tool_search_tool_regex_20251119` / `_bm25_20251119`) — это November 2025 stable shape, не proposal; FA имеет zero-new-deps мост к нему через ADR-4 SQLite FTS5 (R-3).
- Bright Data MCP `GROUPS` env-var + `tools` env-var — конкретная workable форма для ADR-6 расширения на tool-tag allow-list (R-4); PR #37 это упомянул как «design analogy», но не как конкретный TOML-shape.
- Subtraction-principle (Anthropic) переведён в R-7 как 4-вопросный self-audit acceptance-block для ADR-7. Это разница между «design-philosophy в noте» и «testable рубрик в ADR».
- Две UNCERTAIN-ASK (`R-8` system-prompt assembly + prefix-cache invariant; `R-9` harness-transferability claim citation strategy) — требуют user input до того, как ADR-7 готов к написанию.

## 2. Scope, метод, goal_lens (verbatim)

**Goal-lens (verbatim из frontmatter):**

> «Gap analysis vs accepted ADR-1..6 + явное выявление, что PR #37 (efficient-llm-agent-harness-2026-05.md) исследовал поверхностно или пропустил, до того как ADR-7 будет писаться.»

Это вариант (c) из default options в `knowledge/prompts/research-briefing.md` Stage 1, расширенный явно «vs PR #37» — потому что PR #37 покрывает тот же тематический набор, и просто дублировать его было бы pointless.

**Метод.** Five-stage workflow из `knowledge/prompts/research-briefing.md`:

1. **Stage 1 — Goal-lens elicitation.** В предыдущем сообщении пользователь подтвердил вариант (c) implicitly («cross-reference new note with existing adr's» + «find that is not researched deeply enough or skipped»). Уточнили формулировку до form в frontmatter; пользователь не блокировал.
2. **Stage 2 — Source ingestion.** Прочитаны: full attachment `youtube_transcripts.md` (3 видео, 321 line); arxiv abstract HTML обоих papers; полный текст Anthropic `code-execution-with-mcp` blog; Claude API tool-search docs (через quick-start + how-it-works section); Bright Data tools reference (Rapid/Pro/groups + 11 группа); MCP donation news; MCP spec (через URL — не парсился глубоко за неимением changes-section, см. §8.5); полный текст PR #37 ноты; review-комментарии PR #37; ADR-1..6 с amendments; adjacent research notes (`how-to-build-an-agent-ampcode-2026-04.md` head + frontmatter; `cutting-edge-agent-research-radar-2026-05.md` head; `semi-autonomous-agents-cross-reference-2026-05.md`).
3. **Stage 3 — Relevance gate.** Соответствие goal_lens проверено явно: каждый источник ≥ один gap PR #37 либо один пункт ADR cross-reference.
4. **Stage 4 — Deep-dive note + Decision Briefing.** Этот файл.
5. **Stage 5 — Chat handover.** §0 § Сводная таблица будет постнут verbatim в чате при создании PR. R-8 и R-9 (UNCERTAIN-ASK) будут эскалированы пользователю.

**Не-делается этой нотой.** Не пишется сам ADR-7. Не реализуется inner-loop. Не модифицируется PR #37 и его branch. Не изменяются существующие ADRs (только cross-reference).

## 3. Key concepts (one-line definitions, source-language terms preserved)

- **Harness** — fixed architecture, превращающая raw LLM в agent; while-loop + tool-registry + permission-layer + state. Source: Video 2 определение, согласовано с Tsinghua paper Introduction («the surrounding harness: the control stack…»).
- **Framework** (vs harness) — даёт абстракции (chains, retrievers, state-graphs), требует assembly от человека-архитектора. Harness — *уже собранный* агент, человек предоставляет goal. Source: Video 2.
- **Natural-Language Agent Harness (NLAH)** — externalized, editable, executable natural-language artifact, описывающий harness behavior; runtime — Intelligent Harness Runtime (IHR). Source: Tsinghua paper abstract + Section 1.
- **Meta-Harness** — outer-loop система, оптимизирующая harness-код через agentic-proposer, читающий source/scores/traces всех prior candidates через filesystem. Source: Meta-Harness abstract.
- **Subtraction principle** — design-rule: каждая harness-component encode-ит assumption о том, чего модель не может сама; assumptions expire когда модели улучшаются. Не добавлять компоненты по умолчанию; удалять, когда измерения показывают неэффективность. Source: Anthropic, через Video 3 нарратив.
- **MCP (Model Context Protocol)** — JSON-RPC-shaped open standard для agent ↔ tool/resource/prompt boundary; запущен Anthropic Nov 2024, по состоянию на 2025-11-25 spec — текущая stable. Source: Anthropic announcement + spec URL.
- **Tool descriptor (tier 2 disclosure)** — short metadata о тулзе (name + 1-line description + permissions/tags) без full JSON Schema; Anthropic API представляет это через `tool_reference` blocks. Source: Claude tool-search docs.
- **`defer_loading`** — флаг в Claude API tool list, помечающий тулз как «не загружать в context до явного запроса через tool-search». Source: tool-search docs (config example).
- **Tool group (Bright Data)** — pre-configured collection тулзов под domain (`ecommerce`, `finance`, `social_media`, …); 11 групп в Bright Data MCP server; селекция через `groups=` URL param или `GROUPS=` env-var. Source: Bright Data tools docs §«Modes: Rapid (Free), Pro and 11 tool groups».
- **Custom tool list (Bright Data)** — `tools` env-var, перечисляющий точные tool-имена; load-list ровно эти, ничего другое. Source: Video 1 + Bright Data docs.
- **Code execution with MCP / Code Mode (Cloudflare)** — паттерн «MCP server as filesystem of tool-files, agent reads only what needed, intermediate data в execution env, model видит только final output». 98.7% reduction в Anthropic example. Source: Anthropic engineering blog Nov 04 2025.
- **Programmatic tool calling** — Anthropic API feature, ортогональная к code-execution-over-MCP: Claude пишет Python, вызывающий тулзы напрямую как функции; intermediate-результаты не входят в context. Caveat: MCP-connector tools currently не могут быть programmatically called. Source: Video 1 + Anthropic docs.
- **Prefix caching** — провайдер-side оптимизация: если префикс system-prompt идентичен между вызовами, сервер переиспользует KV-cache. Динамическая компоновка system-prompt (file-injection из ancestor dirs) ломает кэш. Source: Video 2 component #7 explicit warning.
- **Context compaction** — harness-механизм: при достижении ~80-90% context-limit harness summarize-ит старые сообщения, оставляя последние verbatim. Cloud Code: 200k → 1M token window с compaction триггером ~80%. Source: Video 2 component #2.
- **Lifecycle hooks (pre-tool / post-tool)** — extensibility-точки в harness: pre-tool fires до execution, может allow/deny/modify; post-tool fires после, для audit/logging. JSON exit-code-protocol. Source: Video 2 component #8 + Anthropic Cloud Code prior art.

## 4. Primary-source numbers (sweep)

PR #37 §1 TL;DR помечает значительную часть numbers как «from transcript, secondary». Ниже sweep по primary URL-ам, которые **резолвятся** на 2026-05-06.

### 4.1 Tsinghua NLAH paper (`arXiv:2603.25723`)

Прямо из abstract:

> «Across coding and computer-use benchmarks, we conduct controlled evaluations of operational viability, module ablation, and code-to-text harness migration.»

Из Section 1 (Introduction):

- Постановка: «Modern agents increasingly succeed or fail because of the surrounding harness: the control stack that structures multi-step reasoning, tool use, memory, delegation, and stopping beyond any single model call.»
- Cite-ит ReAct (Yao 2023), RAG (Lewis 2021), Reflexion (Shinn 2023), память + self-evolution (Zhang 2026), workflow-generation, multi-agent orchestration (Magentic-One Fourney 2024 / Wang 2025b / другие 2026).

Числа из Video 3, **которые НЕ видны в abstract** (нужна верификация по full paper PDF — см. `claims_requiring_verification`):

- SWE-bench Verified, GPT-5.4 max reasoning: full harness ≈ **74-76%** result rate, **16.3M prompt tokens / sample**, **600+ tool calls**, **32 min runtime**.
- Stripped-down: **1.2M tokens, 51 tool calls, <7 min**, same destination → **14× compute waste без user-visible benefit**.
- Module-ablation deltas: self-evolution = consistently helpful; verifiers ≈ **−0.8 SWE-bench, −8.4 OSWorld**; multi-candidate search ≈ **−5.6**.
- OSymphony native-code → NL-representation migration: **30.4% → 47.2%** (+16.8 pp); runtime **361 min → 41 min** (−9×); LLM calls **1200 → 34** (−97%).

**Эпистемический статус.** Эти числа цитируются в Video 3 нарративом, согласуются с abstract («module ablation, code-to-text harness migration» — explicit experimental sections), но конкретные delta-цифры — secondary до проверки paper PDF. Меня **тем не менее** интересует общий signal-direction (verifiers harm, NL-representation helps), который даже в weak форме поддерживает R-5 и R-7.

### 4.2 Meta-Harness paper (`arXiv:2603.28052v1`)

Прямо из abstract (verbatim):

- «Meta-Harness improves over a state-of-the-art context management system **by 7.7 points** while using **4x fewer context tokens**» — на online text classification.
- «A single discovered harness improves accuracy on 200 IMO-level problems **by 4.7 points on average across five held-out models**» — это primary-source поддержка transferability-claim в R-9.
- «On agentic coding, discovered harnesses surpass the best hand-engineered baselines on TerminalBench-2.» — без конкретного числа в abstract.
- «existing text optimizers are poorly matched to this setting because they **compress feedback too aggressively**» — **прямая** primary-source опора для R-2 (raw `events.jsonl` ≠ `hot.md` summary).

Числа из Video 3, которые **не** в abstract:

- 76.4% на TerminalBench-2.
- 10M tokens/iteration, 400× больше feedback чем prior methods.
- ≈82 файлов читается per round.
- Без raw traces: accuracy 50% → 34%; с summaries вместо traces: 34.9%.
- 76.4% — best-in-class; +7.7 points над SOTA на 215 text classification tasks (примечание: цифра 215 vs «text classification system» в abstract — расхождение, см. §8.4).

### 4.3 Anthropic Code execution with MCP (Nov 04, 2025)

Прямо из blog:

- Google-Drive-→-Salesforce example: **150,000 tokens → 2,000 tokens (98.7% reduction)**.
- Cloudflare публиковала аналогичный паттерн под именем «Code Mode» — **«weeks earlier»** (Video 1 нарратив; primary-source confirmation в самом блоге: «Cloudflare published similar findings, referring to code execution with MCP as 'Code Mode'»).
- Tool-as-file layout: `servers/<server>/<tool>.ts` + `index.ts`.
- Filtering 10,000-row spreadsheet в execution-env → агент видит 5 rows вместо 10,000.
- Privacy: «intermediate results stay in the execution environment by default».
- Каюат: **«tools provided through an MCP connectors cannot currently be called programmatically»** (Video 1) — ortogonal к code-execution feature, но релевантно для R-6 design-shape.

### 4.4 Tool search tool docs (Claude API)

Прямо из docs:

- API identifiers: `tool_search_tool_regex_20251119` (regex variant) и `tool_search_tool_bm25_20251119` (BM25 natural-language variant). **Ноябрь 19, 2025** — это API-version date, что подтверждает, что фича GA с ноября 2025.
- Multi-server setup baseline: **«can consume ~55k tokens in definitions before Claude does any actual work»**.
- Reduction: **«typically reduces this by over 85%»**, остается «3-5 tools Claude actually needs for a given request».
- Tool selection accuracy degradation **«once you exceed 30-50 available tools»**.
- Mechanism: `defer_loading: true` per-tool; Claude видит только tool-search-tool + non-deferred tools initially.
- Возвращает `tool_reference` blocks, которые автоматически expand-ятся в full tool definitions при использовании.
- Compatibility: ZDR-eligible. Bedrock — invoke API only, **не** converse.

### 4.5 Bright Data MCP tools docs

Прямо из docs:

- **2 modes**: Rapid (Free) и Pro.
- **11 групп**: e-commerce, social_media, browser_automation, business_intelligence, finance, research, app_stores, travel, advanced_scraping, geo_llm_visibility, code.
- **>60 tools** total в pro-mode + groups.
- Configuration shape:
  - Remote MCP: `&pro=1` URL param + `&groups=<list>` URL param.
  - Local MCP: `PRO_MODE=true` env-var + `GROUPS=<list>` env-var.
- Custom tool list: `tools` env-var (Video 1; в видимой части docs не явно, но Video 1 цитирует докуу).
- 5000 requests/month free tier; OSS под MIT license.

### 4.6 MCP donation / Agentic AI Foundation (`anthropic.com/news/donating...`)

URL зафиксирован в `source:`. **Эта нота не сделала глубокий fetch этой страницы** (см. §8.5 за детализацию gap). Релевантно как governance-факт: если MCP перешёл под foundation (Linux Foundation или подобное), это снижает риск Anthropic-side breaking-changes. Это в свою очередь укрепляет ADR-2 §Amendment 2026-05-01 (MCP forward-compat) — более durable, чем когда MCP был vendor-specific.

### 4.7 MCP spec `2025-11-25`

URL зафиксирован. Дата spec — November 25, 2025 — **позже** API tool-search idents (`_20251119`), что нормально (доки могут отставать на дни).  Глубокий парсинг spec changes-секции **не сделан** — см. §8.5.

## 5. Tool-disclosure design space — пять паттернов и их ADR-fit

Этот раздел расширяет PR #37 §5.4 mapping-таблицу до **shape-уровня** и явного ADR-фит-вердикта. PR #37 предложил «descriptor → schema» split в одном предложении (§5.4 row «Dynamic context loading»), но не разобрал каждый pattern против каждого ADR.

### 5.1 Pattern A — Group/scope loading (Bright Data shape)

**Mechanism.** Tools регистрируются с tag/group. Сессия указывает один или больше groups; runtime фильтрует registry до tools, чьи tags пересекаются с whitelist. Никакой LLM-side дискавери.

**FA-fit:**

- **ADR-6 (sandbox).** Прямо подходит как extension: новая `[tool_groups]` секция в `~/.fa/sandbox.toml`. Cost: medium. См. R-4.
- **ADR-2 (MCP shape).** Совместимо. ADR-2 §Amendment 2026-05-01 §point 1 фиксирует JSON-RPC shape; tags — это metadata-поле, ортогональное к request/response shape.
- **ADR-7 (future).** Регистрационная форма ToolSpec обязана включать `tags: list[str]` field.

**Вердикт.** Take в R-4. Это самая cheap-дешёвая форма tool-scoping; работает на startup time, не на per-turn LLM cost.

### 5.2 Pattern B — Custom tool list (Bright Data `tools` env)

**Mechanism.** Жёсткая spec точных tool-names. Production-mode «I know exactly what I want».

**FA-fit:**

- Подходит для repeatable recipe / Skills / sub-agent ролей.
- Pattern A (groups) и B (custom tools) **композируются**: групповой allow-list плюс session-override на список имён.

**Вердикт.** Subset of Pattern A; не самостоятельная рекомендация. Реализуется через комбинацию `tool_groups.allow` + per-session command-line override (analog to ADR-6 «`fa --sandbox-allow-once`»).

### 5.3 Pattern C — Tool-search (BM25/regex, Anthropic shape)

**Mechanism.** Few core тулзы + dedicated search-tool. Catalog индексирован (BM25 или regex). LLM запрашивает search; runtime возвращает 3-5 `tool_reference`; full schemas разворачиваются on demand.

**FA-fit:**

- **ADR-4 (storage).** SQLite FTS5 уже выбран и реализует BM25 native. Tool-search reuse-ит тот же primitive. Cost: cheap при v0.2 росте catalog. См. R-3.
- **ADR-2 (MCP shape).** ADR-2 §Amendment 2026-05-01 §point 4 разрешает «MAY add fields» — добавление `tool_reference`-shape результата как новой response-form **не** ломает MUST-NOT-change clause.
- **ADR-7 (future).** В v0.1 — out-of-scope (catalog маленький, ~5-10 tools); shape-плейсхолдер описать в ADR-7 §Notes как extension point.

**Вердикт.** TAKE shape, не реализация. См. R-3.

### 5.4 Pattern D — Dynamic 3-level disclosure

**Mechanism.** Уровни (1) server-name list, (2) per-tool 1-line descriptors, (3) full schema. Combinable с Pattern A / C.

**FA-fit:**

- Это **самый общий** shape; A/C — частные случаи.
- Прямое выражение: registry экспонирует три API endpoint'а `list_servers()` / `list_tools(server)` / `describe_tool(server, tool)`. Все три — JSON-RPC-shaped per ADR-2.
- v0.1 может экспонировать только descriptor-tier (~5-10 tools, маленький), без LLM-search; full schema — on-demand при `dispatch(name, params)`.

**Вердикт.** TAKE как **canonical** shape. R-1 в §0.

### 5.5 Pattern E — Code-execution-over-MCP / Programmatic tool calling

**Mechanism.** Две подкатегории. (E1) Tools-as-files: `servers/<name>/<tool>.ts`; agent читает только нужные file-ы (filesystem-discovery). (E2) Programmatic tool calling: agent пишет Python/JS код, вызывающий tools; intermediate-результаты в execution env, не в context.

**FA-fit:**

- v0.1 — out-of-scope. Требует:
  - OS-level sandbox (ADR-6 §Option C, текущая acceptance: «`run_command` lands → re-evaluate»).
  - Network/CPU/time limits (вне scope ADR-6, потребует new ADR).
  - Redaction policy (intermediate данные не должны попадать в model context — explicit policy required).
  - Allow-list для shells/binaries.
- v0.2-shape: каждый ToolSpec может **автоматически** генерировать `tools/as_files/<server>/<tool>.<ext>` адаптер. v0.1 не реализует генерацию, но **может** зарезервировать filename-pattern.

**Вердикт.** DEFER в R-6, но с явным forward-compat shape.

### 5.6 Свод «pattern × ADR» (расширенный vs PR #37 §5.4)

| Pattern | A (noise reduction) | B (find context) | ADR-1 fit | ADR-2 fit | ADR-3 fit | ADR-4 fit | ADR-6 fit | v0.1 in-scope? |
|---------|---------------------|-------------------|-----------|-----------|-----------|-----------|-----------|----------------|
| A — Groups | YES | YES | YES (UC1/UC3) | YES (orth.) | n/a | n/a | **EXTEND** (R-4) | YES (R-4) |
| B — Custom list | YES | NO | YES | YES | n/a | n/a | YES (--once flag) | YES |
| C — Tool-search BM25 | YES | YES | NO (catalog small) | YES | n/a | **REUSE** (R-3) | YES | NO; v0.2 |
| D — 3-level disclosure | YES | YES | YES | YES (canon shape) | n/a | n/a | YES | YES (R-1) |
| E1 — Tools-as-files | YES | YES | NO (sandbox req.) | YES | n/a | n/a | NO (Option C) | NO; v0.2 (R-6) |
| E2 — Programmatic call | YES | YES | NO | YES | n/a | n/a | NO | NO; v0.2 (R-6) |

## 6. Cross-reference: ADR-1..6 — глубокий проход

PR #37 §6 присутствует и cite-ит ADR-1..6, но в pointer-shape («совместимо», «не нарушает»). Этот раздел нацелен на каждый ADR с явным указанием: какой пункт ADR'а **прямо** требует/разрешает/запрещает что-то относительно findings из §4-§5.

### 6.1 ADR-1 (v0.1 use-case scope)

Релевантные пункты:

- **§Decision: «UC1 + UC3 in-scope; UC2 best-effort; UC4/UC5 deferred.»** — ограничивает scope harness'а до coding+PR + docs-to-wiki. Это объясняет, почему R-6 (code-execution) DEFERRED: code-execution feature не нужна для UC1 (где edit_file + git + gh достаточно) и не нужна для UC3 (где chunker + retrieval + LLM Q&A достаточно).
- **§Amendment 2026-05-01 — UC5 deferred.** UC5 = multi-LLM eval-harness — близко к Meta-Harness paper (выбор harness across N models). Это объясняет, почему R-9 (transferability claim citation) — UNCERTAIN-ASK: pro-цитата помогает обосновать ADR-2 single-static-routing, но contra-цитата может пригодиться при v0.2 ADR-N для UC5.
- **§Concrete v0.1 deferred list.** Code-execution / programmatic-tool-calling **не** в этом списке явно. ADR-7 должен это **добавить** косвенно через DEFER (R-6).

**PR #37 gap.** PR #37 §6 цитирует ADR-1, но не указывает, что *расширение* deferred-list — потенциальная responsibility ADR-7. R-6 в этой ноте делает это explicit.

### 6.2 ADR-2 (LLM tiering & access)

Релевантные пункты:

- **§Decision: 4-role static routing (Planner/Coder/Debug/Eval).** Подтверждается transferability-claim Meta-Harness abstract (один harness, разные модели per role). См. R-9.
- **§Amendment 2026-04-29 §point 5: «v0.1 inner-loop has no Critic / Reflector role.»** Прямо подтверждается Tsinghua module-ablation evidence (verifiers harm, multi-candidate search harm). См. R-5.
- **§Amendment 2026-04-29 §point 1-3: `tool_protocol: native | prompt-only` per-role.** Ортогонально нашим findings; tool-disclosure (R-1) живёт в registry shape, не в `models.yaml`.
- **§Amendment 2026-05-01 §point 1: «MCP-shaped tool signatures».** Это **главная** anchor для R-1. Все патrены (A-D) §5 — JSON-RPC-совместимые.
- **§Amendment 2026-05-01 §point 4: «Inner-loop ADR (future ADR-7) inherits the convention. The ADR-7 author MAY add fields … but MUST NOT change the existing two fields (`name`, `params` for request; `result`, `error` for response) without a separate amendment to this ADR-2.»** Это **критическая** строка. ADR-7 может добавить metadata-поля (`tags`, `tool_reference` response-form), но не может переопределить request/response. R-1, R-3, R-4 — все совместимы с этой clause.

**PR #37 gap.** PR #37 §6 cite-ит «совместимо с ADR-2 MCP-shape», но **не вытащил** ADR-2 §Amendment 2026-05-01 §point 4 как hard constraint surface. Это критическая разница: ADR-7 author, читая PR #37, может неосознанно нарушить point 4. Эта нота §0 R-1 явно цитирует point 4.

### 6.3 ADR-3 (memory architecture variant — Mechanical Wiki)

Релевантные пункты:

- **§Decision: «Filesystem-canonical Markdown + frontmatter; deterministic write-time chunker; read = grep → SQLite FTS5 BM25; no embeddings/graph/Mem0 в v0.1.»** Подтверждает R-2: `events.jsonl` живёт на filesystem, как canon. `hot.md` — Markdown summary. Read-side для traces — `grep` (через path) + опционально BM25 (через FTS5, см. R-3 reuse).
- **§Decision: «`hot.md` session summary, auto-archived to `notes/sessions/<date>.md` at session end.»** — это **именно** место, где R-2 invariant нужен: `hot.md` cite-ит paths в `events.jsonl`, а не **заменяет** их. PR #37 §5.3 и §8 R-4 говорят про raw traces, но не явно соединяют это с ADR-3 hot.md mechanism.
- **§Decision: «Volatile-store hooks: `src/fa/memory/volatile/` exists as empty namespace.»** — Meta-Harness style self-evolution в v0.2 будет писать **в этот namespace**, читая raw `events.jsonl`. R-2 защищает forward-compat.

**PR #37 gap.** PR #37 §5.3 говорит про raw traces vs summaries, но не делает явный мост к ADR-3 hot.md mechanism (тот же файл, который user обозревает после сессии). R-2 в этой ноте делает это explicit: `hot.md` cite-ит, не заменяет.

### 6.4 ADR-4 (storage backend — SQLite FTS5)

Релевантные пункты:

- **§Decision: «SQLite FTS5 with `MATCH` queries; BM25-ranked out of the box; index в `~/.fa/index.sqlite`.»** Это прямой match для Pattern C tool-search BM25 variant из §5.3. См. R-3.
- **§Decision: «Pure stdlib `sqlite3` module; no extra dependency at storage layer.»** — это **именно** zero-new-deps обещание, которое R-3 защищает.
- **§Option B (chosen): «One row per chunk; MATCH queries.»** — ровно та же модель работает для tools: одна row per ToolSpec descriptor; MATCH query на `description` поле.

**PR #37 gap.** PR #37 §6 упоминает ADR-4, но не явно выписывает «BM25 tool-search reuses ADR-4 SQLite FTS5 без новых deps». Это zero-cost extension, который PR #37 **не** маркировал. R-3 явно фиксирует.

### 6.5 ADR-5 (chunker tool — universal-ctags + markdown-it-py)

Релевантные пункты:

- **§Decision: универсальный chunker covering MD/text/Python/Go/PowerShell/TS/JS/YAML/TOML/JSON.** Это chunker для **корпуса** (UC3 ingestion + UC1 code retrieval), **не** для tool descriptors.
- ADR-5 ortогонален harness design в части tool-disclosure: tool descriptors — короткие structured documents, не chunked-источники. Однако ADR-5 **может** быть переиспользован для chunking trace files (`events.jsonl` events можно интерпретировать как text chunks для retrieval, если v0.2 self-evolution пожелает).

**PR #37 gap.** PR #37 не цитирует ADR-5 в §6 cross-reference вообще. Это формально gap, но minor — ADR-5 ortогонален harness design в v0.1.

### 6.6 ADR-6 (tool sandbox & path allow-list)

Релевантные пункты:

- **§Decision: deny-by-default path allow-list; `~/.fa/sandbox.toml`; `[read]` + `[write]` секции.** — текущий shape. R-4 предлагает добавить `[tool_groups]` секцию.
- **§Re-evaluation triggers: «`run_command` lands → re-evaluate Option C OS-level sandbox.»** — ADR-6 уже зарезервировал триггер для OS-level escalation. Code-execution-over-MCP (R-6) активирует **именно** этот trigger. R-6 этой ноты **не** активирует trigger в v0.1, защищает forward-compat.
- **§Tool wiring table (`read_file`, `list_files`, `edit_file`, `write_file`, `grep`).** — текущий v0.1 tool-set, который sandbox прикрывает. R-7 §Acceptance check «which tools agent rarely uses?» применяется к этой таблице.
- **§Audit log: `~/.fa/state/sandbox.jsonl`.** — это **уже** raw-events JSONL trace, прецедент для R-2 `events.jsonl`. R-2 предлагает обобщить shape с `~/.fa/state/sandbox.jsonl` на `~/.fa/state/runs/<run_id>/events.jsonl` (sandbox decisions — один из event-types в общем trace).

**PR #37 gap.** PR #37 §6 cite-ит ADR-6 generally, но не вытащил `~/.fa/state/sandbox.jsonl` как прецедент для R-2 shape (то есть FA **уже** делает append-only JSONL trace на одном under-system; общий trace — обобщение). R-2 в этой ноте делает это explicit.

### 6.7 Свод cross-reference (расширенный vs PR #37 §6)

| ADR | PR #37 cite | Этот файл cite | Углубление | Hard-constraint cite |
|-----|-------------|----------------|------------|----------------------|
| ADR-1 §Decision | yes | yes | + UC5 connection (R-9) | — |
| ADR-1 §Amendment 2026-05-01 (UC5) | partial | yes | new (R-9) | — |
| ADR-2 §Decision (4 roles) | yes | yes | + transferability (R-9) | — |
| ADR-2 §Amendment 2026-04-29 §point 5 (no Critic) | yes | yes | + primary-source numbers (R-5) | YES |
| ADR-2 §Amendment 2026-05-01 §point 1 (MCP-shape) | partial | yes | + 3-tier disclosure mapping (R-1) | — |
| ADR-2 §Amendment 2026-05-01 §point 4 (inheritance) | **NO** | yes | new — это hard constraint для ADR-7 | **YES** |
| ADR-3 §Decision (Mechanical Wiki) | yes | yes | + hot.md ↔ events.jsonl invariant (R-2) | — |
| ADR-3 §Decision (volatile-store hooks empty) | NO | yes | new — protected forward-compat (R-2) | — |
| ADR-4 §Decision (SQLite FTS5) | partial | yes | + BM25 tool-search reuse (R-3) | — |
| ADR-5 §Decision | NO | partial | minor (orthogonal, future trace chunking) | — |
| ADR-6 §Decision (path allow-list) | yes | yes | + tool_groups extension (R-4) | — |
| ADR-6 §Re-evaluation triggers | partial | yes | + code-execution trigger (R-6) | — |
| ADR-6 §Audit log JSONL | NO | yes | new — precedent для R-2 events.jsonl shape | — |

## 7. Gap analysis vs PR #37 — explicit deltas

Это секция, которой нет в PR #37 (он не самокритичен и не предусматривал deeper follow-up). Перечисляю **что именно** PR #37 покрыл поверхностно или пропустил, со ссылками на line-ranges in PR #37 file `efficient-llm-agent-harness-2026-05.md` (на head branch `devin/1778072676-efficient-harness-note`, commit `d03f7a3`).

### 7.1 Substantive gaps (что не разобрано глубоко)

1. **ADR-2 §Amendment 2026-05-01 §point 4 («inherits convention; MAY add fields but MUST NOT change»)** — отсутствует в PR #37 §6 как hard-constraint anchor для ADR-7. См. R-1 + §6.2. Risk: ADR-7-author может неосознанно нарушить point 4.
2. **Bright Data конкретный shape** (`GROUPS=` env-var; `tools=` env-var; 11 групп) — PR #37 §5.4 row «Bright Data groups» (file lines ~346) упоминает «как design analogy», но не предлагает конкретный TOML-shape для расширения ADR-6. См. R-4 + §6.6. Risk: «design analogy» без shape — пустой указатель.
3. **ADR-4 = BM25 tool-search**. PR #37 §6 (file lines ~451+) указывает «совместимо с ADR-4», но не явно выписывает «zero-new-deps tool-search reuse». См. R-3 + §6.4. Risk: при v0.2 росте catalog implementer может ввести `rank-bm25` или внешний embedding-сервис как новую dependency.
4. **ADR-6 `~/.fa/state/sandbox.jsonl`** — уже существующий audit-log JSONL — PR #37 §5.3 «raw traces» (file lines ~318+) обсуждает trace shape абстрактно, не упоминая, что прецедент уже **есть** в ADR-6. См. R-2 + §6.6. Risk: дублирующая раскладка trace files под разные subsystems.
5. **`hot.md` ↔ `events.jsonl` invariant** — PR #37 §8 R-4 (file lines ~501+) говорит «raw trace files eval substrate, summaries — index», но не выписывает invariant **как форма ADR-7-rule**. См. R-2 + §6.3. Risk: при v0.2 self-evolution implementer может «срезать» — пробовать запустить eval над `hot.md` (compressed).
6. **System-prompt assembly + prefix-cache invariant** (Video 2 component #7) — **полностью отсутствует** в PR #37. При том, что у FA уже есть AGENTS.md + HANDOFF.md + (предполагаемый) `hot.md`, это live design surface. См. R-8 (UNCERTAIN-ASK). Risk: каждый PR будет переизобретать assembly, cache-hits случайны.
7. **ADR-1 §Amendment 2026-05-01 (UC5)** — PR #37 §6 не упоминает UC5 явно; UC5 — это именно multi-LLM eval-harness, ровно та область, где Meta-Harness paper применима. См. R-9 (UNCERTAIN-ASK).

### 7.2 Methodological gaps (как написана нота)

1. **Zero `UNCERTAIN-ASK` verdicts.** PR #37 §0 содержит 5 рекомендаций: 4× TAKE + 1× DEFER. Per `knowledge/prompts/research-briefing.md` Stage 5, UNCERTAIN-ASK — **ожидаемый** механизм для эскалации design-вопросов пользователю. Полное отсутствие UNCERTAIN-ASK в PR #37 — либо premature TAKE (autopilot решение без user-input), либо признак, что recommendation-set был слишком safe. Эта нота имеет 2 UNCERTAIN-ASK (R-8, R-9). Это методологический контраст.
2. **Secondary→primary upgrade missing.** PR #37 §1 TL;DR помечает Tsinghua/Meta-Harness numbers как «from transcript, secondary». Эта нота §4.1-§4.2 показывает, что abstract обоих papers резолвится, и ряд numbers (Meta-Harness 7.7 / 4× / 4.7 + 5 held-out) — primary. PR #37 не поднял secondary → primary, оставив evidence-base слабее, чем возможно.
3. **Stanford attribution caveat не помечен.** Video 3 называет Meta-Harness «Stanford» paper. arxiv submitter Yoonho Lee, narrative cite-ит Khattab/DSPy. abstract HTML, который мы получили, явно не выписывает affiliation. PR #37 принял Video-атрибуцию без caveat (file lines ~17, 250+). Эта нота §8.3 явно помечает unresolved.
4. **`claims_requiring_verification` поверхностный.** PR #37 frontmatter содержит 3 пункта; для derivation из непрочитанных primary papers ожидается ≥5. Эта нота — 7 пунктов.
5. **PR #37 review-conflict (comments 2/4/5) не разрешён в самой ноте.** Devin-Review bot открыл claim «вся проза на английском» (comment 2, до commit `d03f7a3`); PR-author commit `d03f7a3` локализовал; bot потом отметил «Resolved» дважды (comments 4 и 5) с factual claim «previous bug was simply wrong». Это путаница: comment 2 был corrected by commit (а не «incorrect»). Не критично для ноты, но шумно для audit trail. **Не действие этой ноты**, фиксирую как наблюдение.

## 8. Risks and caveats

### 8.1 Video-claims vs primary papers

Часть наиболее ярких numbers (Tsinghua module-ablation deltas; OSymphony migration delta) видны только в видео-нарративе Video 3, не в abstract. До того как ADR-7 будет цитировать их в §Decision, нужна сверка по full paper PDF. См. `claims_requiring_verification` пункты 1-2.

### 8.2 «Subtraction can go too far»

PR #37 §7 пункт 5 (file lines ~462+) уже это поднял: убирать verifiers безопасно только если deterministic checks покрывают risk. Эта нота **усиливает** caveat: ADR-6 sandbox + Makefile/CI/pre-commit — это deterministic gates, которые **должны** оставаться независимо от R-5 «no Critic». R-7 4-вопросный self-audit включает «verification/search loops hurting?» именно для того, чтобы review-PR культура **не** срезала deterministic checks.

### 8.3 Meta-Harness Stanford attribution — unresolved

Atomic facts:

- arxiv `2603.28052v1` submitter (publish-time): Yoonho Lee.
- Video 3 narrative: «paper was released by Omar Khattab who built DSPy» (verbatim transcript).
- Video 3 narrative title: «Orchestration Over Architecture: What Stanford Found».
- Khattab — formerly Stanford ML PhD (DSPy origin), сейчас (2026 vintage) часто связан с MIT.
- Yoonho Lee — Stanford ML PhD (lineage).
- Affiliation в abstract HTML, который мы получили, **не выписан**.

**Эпистемический статус.** Stanford lineage **присутствует** (через Yoonho Lee), но называть paper «Stanford paper» без affiliation-цитаты — **video-claim**. Не цитировать в ADR без проверки title page в paper PDF.

### 8.4 Meta-Harness number-разнобой

abstract: «improves over a state-of-the-art context management system **by 7.7 points** while using **4x fewer context tokens**» — без указания «215 text classification tasks».

Video 3 narrative: «It was scoring 7.7 points above state-of-the-art using four times fewer tokens» **+** «215 text classification» (verbatim).

Расхождение нечастое — abstract less specific. Скорее всего, 215 — экспериментальный setup detail из paper Section, не abstract. Helpful, но **не cite-ить как primary** до проверки.

### 8.5 Не-fetch-нутые источники в этой ноте

Честно признаю, что этим запросом мы **не сделали** глубокий парсинг следующих URL-ов из user-provided source list:

- **`https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation`** — fetched only as URL-record. Govern-факт цитируется как «MCP перешёл под foundation», но конкретные governance-детали (какая foundation? when? scope?) не парсились. Если ADR-7 захочет процитировать durability-довод — нужен отдельный fetch.
- **`https://modelcontextprotocol.io/specification/2025-11-25`** — fetched only as URL-record. Spec changes между 2024 и 2025-11-25 не разобраны построчно. ADR-2 §Amendment 2026-05-01 §point 5 уже признаёт «transport layer changes between 2024 and 2025-2026»; deeper diff не делался.
- **`https://www.anthropic.com/news/model-context-protocol`** — fetched only as URL-record. Это launch announcement Nov 2024; relevant как governance prequel.

Это honest gap. Для goal_lens (gap analysis vs ADR-1..6) этих deep fetch-ов **достаточно не было**, потому что конкретные ADR-fit-вопросы (R-1..R-9) опираются на arxiv abstract + Anthropic blog + Bright Data docs + Claude API tool-search docs — все эти URL-ы прочитаны body-целиком. Но для full-source-coverage parity — это gap, который future research note может закрыть.

### 8.6 «Harness-engineering» как label

Tsinghua paper formalizes «harness engineering» как discipline. У FA нет соответствующей роли — это работа project-owner (`0oi9z7m1z8`) + agent (Devin / другие). Если в v0.2 появится «harness eval» tier, понадобится отдельный ADR. Это явно out-of-scope для текущей ноты, но фиксирую как concept-anchor для будущих research notes.

## 9. Numbered recommendations (long-form)

### R-1 — MCP forward-compat для tool-disclosure (3 уровня) на shape-уровне

Предлагается, чтобы ADR-7 §Decision содержал блок `### Tool disclosure tiers` с тремя shape-таблицами:

```text
Tier 1 — Server list (zero-tool registration cost)
  GET /servers           → [{name, description}, ...]

Tier 2 — Tool descriptors (per-server)
  GET /servers/<server>/tools
                         → [{name, summary, tags, permissions}, ...]

Tier 3 — Full schema (per-tool, on demand)
  GET /servers/<server>/tools/<tool>
                         → {name, description, input_schema, output_schema, ...}
```

Implementation в v0.1 — pure-Python in-process dispatcher (per ADR-2 §Amendment 2026-05-01 §point 3 «no `mcp` package dependency in v0.1»). Все три endpoint — JSON-RPC-shaped. ToolSpec обязан декларировать `tags: list[str]` (см. R-4) и `permissions: dict[Literal['read','write'], list[str]]` (см. ADR-6).

ADR-7 author **должен** explicit cite ADR-2 §Amendment 2026-05-01 §point 4 как hard constraint surface. Это закрывает gap §7.1 пункт 1.

### R-2 — Trace separation invariant: events.jsonl ≠ hot.md

Предлагаемый формат `events.jsonl` event:

```json
{
  "ts": "2026-05-06T13:42:17.123Z",
  "run_id": "<uuid>",
  "turn": 17,
  "kind": "tool_request" | "tool_response" | "permission_decision" | "model_call" | "compaction" | "stop",
  "actor": "planner" | "coder" | "debug" | "judge" | "sandbox" | "harness",
  "payload": { ... kind-specific ... },
  "artifact_path": "<optional: filesystem path with raw blob>",
  "model": "<optional: model slug>",
  "tokens_in": <int|null>,
  "tokens_out": <int|null>,
  "cost_usd": <float|null>
}
```

Инвариант (ADR-7 §Decision):

> «`hot.md` cite-ит paths и/или byte-offsets в `~/.fa/state/runs/<run_id>/events.jsonl`. `hot.md` **не** канонический источник для replay/eval/Meta-Harness-style self-evolution. При конфликте между `hot.md` и соответствующими событиями в `events.jsonl`, `events.jsonl` побеждает.»

Это **прямая** primary-source поддержка из abstract Meta-Harness paper («existing text optimizers compress feedback too aggressively»). См. §4.2.

ADR-3 §Decision уже мандат-ит filesystem-canon. R-2 расширяет canon на trace-уровень.

### R-3 — SQLite FTS5 reuse для tool-search BM25

ADR-4 §Option B (chosen): «SQLite FTS5; one row per chunk; `MATCH` queries return BM25-ranked results out of the box.»

Для tools — точно та же модель:

```sql
-- Новая virtual-table в ~/.fa/index.sqlite
CREATE VIRTUAL TABLE tools USING fts5(
    name UNINDEXED,
    server UNINDEXED,
    description,
    summary,
    tags
);
-- BM25 tool-search query:
SELECT name, server FROM tools WHERE tools MATCH ? ORDER BY rank LIMIT 5;
```

Zero new dependency. Trigger (когда реализовать): catalog > ~10 tools или selection-accuracy degradation, наблюдаемая на eval-harness (когда тот появится).

### R-4 — `[tool_groups]` в `~/.fa/sandbox.toml`

Предлагаемое расширение ADR-6 §Policy file:

```toml
# Existing sections:
[read]
allow = [...]
deny  = [...]

[write]
allow = [...]
deny  = [...]

# New section (R-4):
[tool_groups]
# Allow-list тегов; tool-call блокируется sandbox-ом, если ни один tag тула
# не входит в этот список. Empty list = no tools allowed (deny-all).
# Default policy ships `["coding", "git", "memory"]` для UC1 + UC3.
allow = ["coding", "git", "memory", "search"]
# Block-list overrides allow.
deny  = []
```

Каждый ToolSpec обязан декларировать `tags: list[str]` (R-1). Sandbox-check запускается на dispatch:

```python
class Sandbox:
    def check_tool_call(self, tool_name: str, tags: list[str]) -> None:
        """Raise SandboxError if tool's tags don't intersect [tool_groups].allow."""
```

Cost: medium (TOML schema + dispatcher hook + ToolSpec migration).

### R-5 — «No Critic / verifier loops в v0.1» — primary-source-cited

ADR-7 §Notes должен содержать subsection:

```text
### Why no Critic / verifier role in v0.1

ADR-2 §Amendment 2026-04-29 §point 5 already states: "v0.1 inner-loop has
no Critic / Reflector role." This subsection adds primary-source evidence
from research note knowledge/research/efficient-llm-agent-harness-deep-dive-2026-05.md §4.1:

- Tsinghua arXiv:2603.25723 (NLAH paper, March 2026) module-ablation
  reportedly shows verifiers harm performance (-0.8 SWE-bench Verified,
  -8.4 OSWorld); multi-candidate search harms by ~5.6.
  CAVEAT: numbers from Video 3 narrative; pending verification against
  full paper PDF (see deep-dive §claims_requiring_verification #1).

Deterministic checks (sandbox denial per ADR-6, schema validation,
linters/tests, `git status`, CI) remain in scope and are not Critic loops.
```

### R-6 — Code-execution-over-MCP DEFER + forward-compat shape

ADR-7 §Notes:

```text
### Future code-execution: forward-compat shape

Anthropic engineering blog (2025-11-04) reports 98.7% token reduction
(150k → 2k) for Google-Drive-→-Salesforce example using
code-execution-over-MCP. This is the strongest efficiency lever in the
current source set, and simultaneously the most expensive to ship safely.

v0.1 does not implement code-execution. v0.1 registry MAY produce a
filesystem layout `~/.fa/state/tools/<server>/<tool>.<ext>` on demand
(from ToolSpec descriptors) but does not execute. Triggers for v0.2:
- ADR-6 §Re-evaluation triggers: `run_command` lands → re-evaluate
  Option C OS-level sandbox.
- New ADR required for: redaction policy (intermediate data MUST NOT
  enter model context); CPU/time/network limits; allow-list for shells.
```

### R-7 — 4-вопросный subtraction-first self-audit

ADR-7 §Acceptance:

```text
### Acceptance: subtraction-first self-audit

Before merging ADR-7, the implementer answers (in PR description):

1. What is in the agent's context window that does not need to be there?
2. Which tools does the agent rarely use (over the latest N traces)?
3. Are there verification or search loops that might be hurting performance?
4. Is the control logic written in code, or in language (AGENTS.md /
   research notes / prompts), and which would be cheaper to change?

Each "yes / unclear" answer requires either (a) removal of the named
component, or (b) a one-paragraph justification cited in the ADR-7
§Notes.
```

Это превращает Anthropic «subtraction principle» из noted-philosophy в **testable рубрик**.

### R-8 — UNCERTAIN-ASK: prompt-assembly + prefix-cache invariant

См. §0 R-8 четыре options. Предпочтение этой ноты — Option (ii) (two-segment assembly) при условии, что user-tier provider набор (per ADR-2 §Decision: Anthropic + OpenRouter + local vLLM) поддерживает partial prefix-cache. Anthropic — да (`cache_control` блоки). OpenRouter — variable. vLLM — yes (через `--enable-prefix-caching`). То есть Option (ii) — pragmatic-feasible, но Option (iii) (no assembly в v0.1) — radically simpler. **Решение требует user input.**

### R-9 — UNCERTAIN-ASK: harness-transferability claim citation strategy

См. §0 R-9. Предпочтение этой ноты — Option (i) (зафиксировать как одну из причин ADR-2 static role routing с явным caveat «verified for one benchmark family per abstract»). Но Option (ii) (только claims_requiring_verification) — более консервативное. **Решение требует user input.**

## 10. Open questions

### Q-1 — Какой именно provider lineup tested ADR-2 amendment 2026-04-29 «native tool calling»?

Amendment cites «Verified model coverage (user, Apr 2026): Qwen 3.6, Kimi 2.6, GLM 5.1, Claude latest, Nemotron 3 Super». Нужна ли отдельная test-fixture, проходящая на каждой из них перед ADR-7 finalization? Релевантно: tool-disclosure tier 3 (full JSON schema) может быть native-API-specific (например, Anthropic tool-use vs OpenAI tool-calls vs vLLM tool-calls — JSON-shape совместимый, но field-names разные).

### Q-2 — Когда v0.1 catalog перерастёт ~10 tools?

R-3 (BM25 tool-search reuse) — это extension point. Но при каком фактическом размере catalog? Nuance: 10 tools — это рекомендация Anthropic docs «degrades after 30-50»; для v0.1 (UC1 + UC3) ожидается ≤10 tools. Trigger needs метрик: либо token-count в первом prompt > X% context-budget, либо measured selection-accuracy < Y% на trace-replay.

### Q-3 — Trace retention policy

`events.jsonl` (R-2) может содержать private code, tool outputs, model responses. ADR-7 должен выбрать default local retention (постоянно? N дней? зависит от диск-объёма?) и redaction policy. Это, возможно, отдельный ADR-7-amendment, не точно ADR-7-core.

### Q-4 — Где заканчивается hot.md и начинается events.jsonl?

R-2 invariant фиксирует «hot.md cite-ит, не заменяет», но не определяет, **что** идёт в `hot.md`. Концептуально: `hot.md` — pinned current state + last-N-decisions LLM-friendly summary. `events.jsonl` — full trace. Граница — не binary, скорее функциональная. ADR-7 должен дать примеры разделения.

### Q-5 — Как sandbox future code-execution mode?

Покрыто в PR #37 §9 Q-5; здесь дублирую как unresolved для R-6 trigger. Прямого ответа эта нота не даёт.

### Q-6 — Нужен ли явный «harness version» field в `events.jsonl`?

Meta-Harness paper хранит «source code, scores, and execution traces of all prior candidates through a filesystem». Если v0.2 будет делать meta-harness-light, нужно знать, какая версия harness произвела trace. Один-line addition: ToolSpec + Loop-spec → SHA → append в каждое event как `harness_id`. Cheap; решение позже.

## 11. Files used

- User-provided attachment `youtube_transcripts.md` (Devin attachment 01215dee-a768-4c7b-88a4-fd92b37f52db; downloaded in-session to `/home/ubuntu/attachments/f5e10d80-ff4a-4c9d-822f-7ddf4b683ff5/youtube_transcripts.md`; 321 lines; 3 videos)
- <https://arxiv.org/abs/2603.25723> — Tsinghua NLAH paper abstract HTML, fetched
- <https://arxiv.org/abs/2603.28052v1> — Meta-Harness paper abstract HTML, fetched
- <https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool> — Claude API tool-search docs, fetched body
- <https://docs.brightdata.com/ai/mcp-server/tools> — Bright Data MCP tools docs, fetched body
- <https://www.anthropic.com/engineering/code-execution-with-mcp> — Anthropic engineering blog, fetched body
- <https://modelcontextprotocol.io/specification/2025-11-25> — fetched URL only (deep-parse not done; see §8.5)
- <https://www.anthropic.com/news/model-context-protocol> — fetched URL only
- <https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation> — fetched URL only
- <https://github.com/GITcrassuskey-shop/First-Agent/pull/37> — PR review-комментарии + head-branch ноты (commit `d03f7a3`)
- [`../adr/ADR-1-v01-use-case-scope.md`](../adr/ADR-1-v01-use-case-scope.md)
- [`../adr/ADR-2-llm-tiering.md`](../adr/ADR-2-llm-tiering.md) (особенно §Amendment 2026-04-29 + §Amendment 2026-05-01)
- [`../adr/ADR-3-memory-architecture-variant.md`](../adr/ADR-3-memory-architecture-variant.md)
- [`../adr/ADR-4-storage-backend.md`](../adr/ADR-4-storage-backend.md)
- [`../adr/ADR-5-chunker-tool.md`](../adr/ADR-5-chunker-tool.md) (head only — orthogonal)
- [`../adr/ADR-6-tool-sandbox-allow-list.md`](../adr/ADR-6-tool-sandbox-allow-list.md)
- [`./efficient-llm-agent-harness-2026-05.md`](./efficient-llm-agent-harness-2026-05.md) (PR #37 head; полный read)
- [`./how-to-build-an-agent-ampcode-2026-04.md`](./how-to-build-an-agent-ampcode-2026-04.md) (frontmatter + relevant sections)
- [`./cutting-edge-agent-research-radar-2026-05.md`](./cutting-edge-agent-research-radar-2026-05.md) (head, MCP/tool-registry section reference)
- [`./semi-autonomous-agents-cross-reference-2026-05.md`](./semi-autonomous-agents-cross-reference-2026-05.md) (referenced for ADR-2 amendment 2026-05-01 lineage)
- [`./agent-roles.md`](./agent-roles.md) (referenced for Critic/no-Critic lineage)
- [`./latent-verifier-evolve-research-2026-05.md`](./latent-verifier-evolve-research-2026-05.md) (referenced for verifier-evolve lineage)

## 12. Out of scope

- Написание самого ADR-7 (это PR этого файла — research-only).
- Реализация inner-loop, registry, sandbox extension, trace writer.
- Построение реальных MCP servers / clients или установка `mcp` Python package.
- Реализация code-execution / programmatic-tool-calling.
- Decision о финальных model/provider slugs (ADR-2 §Decision уже purposely не фиксирует — see §Decision «Note on model slugs»).
- Retrofit старых research notes под §0 Decision Briefing format (per AGENTS.md PR Checklist rule #8 forward-only clause).
- Глубокий парсинг MCP spec change-log + Anthropic donation news (см. §8.5 — это honest gap, future research note may close).
- Модификация PR #37 либо его head-branch.
- Verification by full paper PDF read (см. `claims_requiring_verification` 1-7 — это работа для следующей сессии).
- Решение R-8 / R-9 UNCERTAIN-ASK — эскалируется пользователю в §0 chat-handover.
