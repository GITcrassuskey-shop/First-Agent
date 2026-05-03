---
title: "Agent UI research radar for First-Agent v0.2 — May 2026"
source:
  - "https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard"
  - "https://github.com/pyrate-llama/hermes-ui"
  - "https://github.com/EKKOLearnAI/hermes-web-ui/"
  - "https://github.com/lotsoftick/hermes_client"
  - "https://github.com/nesquena/hermes-webui"
  - "https://pi.dev/"
  - "https://pi.dev/packages"
  - "https://pi.dev/packages/context-mode"
  - "https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/extensions.md"
  - "https://github.com/openclaw/openclaw/blob/main/docs/gateway/protocol.md"
  - "https://github.com/openclaw/openclaw/pull/60134"
  - "https://github.com/knightafter/openClaw-web-interface"
  - "https://github.com/23ag1/ClawdOS"
  - "https://github.com/grp06/openclaw-studio"
  - "https://github.com/microsoft/magentic-ui"
  - "https://www.microsoft.com/en-us/research/blog/magentic-ui-an-experimental-human-centered-web-agent/"
  - "https://arxiv.org/abs/2507.22358"
  - "https://arxiv.org/abs/2509.13444"
  - "https://aclanthology.org/2025.acl-long.381/"
  - "./cutting-edge-agent-research-radar-2026-05.md"
  - "../adr/ADR-2-llm-tiering.md"
  - "../adr/ADR-6-tool-sandbox-allow-list.md"
compiled: "2026-05-03"
chain_of_custody: "Primary-source claims are quoted or paraphrased from the URLs in `source`; First-Agent mapping is derived from ADR-2, ADR-6, and the prior cutting-edge radar."
claims_requiring_verification:
  - "Hermes, Pi, OpenClaw, and community UI repositories move quickly; re-check repository READMEs and docs before turning this radar into a v0.2 UI ADR."
  - "Repository star/fork counts and package download counts were observed during May 2026 research and should not be treated as durable facts."
  - "This note is research/backlog input for v0.2 UI, not an accepted product or architecture decision."
superseded_by: ""
---

# Agent UI research radar for First-Agent v0.2 — May 2026

> **Status:** research radar / backlog input. Not an ADR.
>
> Purpose: collect current UI patterns from Hermes Agent UIs, Pi,
> OpenClaw / OpenClaw UI forks, and human-agent-interaction research
> that look relevant to a future First-Agent v0.2 UI.

## 0. Executive summary

The strongest signal is not "make a pretty chat app." Agent UIs are
becoming **control planes** for long-running, tool-using systems:

1. **Start local-first and loopback-only.** Hermes' official dashboard
   defaults to `127.0.0.1`, warns that non-localhost binding is
   dangerous, and keeps data on the user's machine. That matches
   First-Agent's single power-user target.
2. **Do not replace the CLI/TUI too early.** Hermes' dashboard embeds
   the real TUI through a PTY/WebSocket. Pi exposes interactive,
   print/JSON, RPC, and SDK surfaces. v0.2 should treat UI as another
   client over a stable event/control protocol, not as the core agent.
3. **Expose agent state, not only chat.** Hermes community UIs converge
   on sessions, active jobs, tool calls, logs, memory, skills, files,
   models, and cost/token status. For First-Agent, the minimum useful
   UI is chat + session timeline + tool/audit cards + Mechanical Wiki
   browser + sandbox status.
4. **Human-in-the-loop is a first-class UI primitive.** Magentic-UI and
   OpenClaw emphasize plan editing, action approvals, interrupts,
   status indicators, and sensitive-operation guards. This should map
   directly to ADR-6 sandbox denials and future ADR-7 hooks.
5. **A gateway/event stream beats ad-hoc endpoints.** OpenClaw uses a
   Gateway WebSocket protocol as a single control plane for CLI, web
   UI, mobile, and headless nodes. First-Agent v0.2 can start smaller:
   loopback FastAPI + SSE/WebSocket event stream, with a JSON-RPC-ish
   command channel aligned with the tool contract.
6. **Artifacts matter for coding agents.** Hermes UI renders HTML/SVG
   and saved file paths in a sandboxed artifact panel. First-Agent
   should plan for rendered Markdown, diffs, generated files, and test
   outputs as inspectable artifacts.
7. **Avoid productivity-suite scope creep.** ClawdOS shows the appeal
   of tasks, notes, feeds, deliveries, dashboards, and marketplace UI,
   but First-Agent should not become a personal OS in v0.2. Treat those
   as inspiration for later plugins, not core.

Recommended next PRs:

1. ADR prep note: First-Agent v0.2 UI control plane and event schema.
2. Tiny UI glossary update: control plane, event stream, artifact,
   HITL approval, PTY bridge, BFF.
3. Mock trace fixture: one local session rendered as chat + tool cards
   + audit rows, before any frontend implementation.
4. Optional: compare TUI-first vs web-first milestones after ADR-7.

---

## 1. Radar table

| Area | External signal | First-Agent fit | Action |
|---|---|---|---|
| Local dashboard | Hermes dashboard runs on `127.0.0.1:9119`; `--insecure` is explicitly dangerous. | Strong fit for single-user local agent. | v0.2 UI should bind loopback by default. |
| PTY bridge | Hermes dashboard embeds `hermes --tui` through PTY/WebSocket and xterm.js. | Useful if First-Agent gets a TUI before web UI. | Keep CLI/TUI as source of truth until protocol stabilizes. |
| Gateway protocol | OpenClaw uses WebSocket JSON frames with roles/scopes and feature snapshots. | Good long-term shape, too much for v0.2 MVP. | Start with one loopback event stream + command endpoint. |
| BFF/proxy | Hermes Web UI uses Browser → BFF → Hermes Gateway. | Fits Python backend + minimal frontend. | Use backend-for-frontend to hide filesystem/secrets. |
| Sessions | Hermes UIs show multi-session CRUD, search, active indicators, model badges, token rings. | Directly relevant to First-Agent R-S-M sessions. | Build session list and active run timeline early. |
| Tool calls | Hermes UIs show expandable tool call arguments/results. | Critical for trust/debugging. | Render every tool call as an audit card. |
| Memory/wiki | Hermes UIs inspect/edit memory; Pi context-mode indexes events into SQLite FTS5. | Strong match with Mechanical Wiki. | UI should browse/search wiki; edits should remain explicit. |
| Files/artifacts | Hermes UI has file browser and artifact panel; Hermes Client supports uploads. | Useful for generated docs/diffs/tests. | Add artifact pane after basic trace viewer. |
| Skills/tools | Hermes/OpenClaw expose skills/tool catalogs and skill search. | Later fit after tool registry exists. | v0.2 should show available tools; marketplace deferred. |
| Approvals | Magentic-UI/OpenClaw provide action guards and approval flows. | Maps to ADR-6 sandbox and ADR-7 hooks. | Add approval event type before adding broad write tools. |
| Interrupts | Pi supports steering messages while the agent works; Magentic-UI supports co-tasking. | Important for long loops. | Add pause/stop/interject controls to UI contract. |
| Tree history | Pi stores sessions as trees and exports/shares HTML. | Useful for branchable research sessions. | Defer branching UI; log enough parent IDs now. |
| Mobile/remote | Hermes/OpenClaw support phone/messaging/SSH tunnel access. | Nice but risky for v0.2. | Support SSH/Tailscale docs only; no public binding. |
| Product suite | ClawdOS adds tasks, notes, feeds, package tracking, dashboard. | Inspiring but beyond First-Agent core. | Keep out of v0.2 core; revisit as plugins. |
| Research UX | Magentic-UI, DuetUI, AXIS emphasize user control and API-first actions. | Strong design constraints. | Prefer explicit plan/edit/approval affordances over hidden autonomy. |

---

## 2. Hermes Agent UI implementations

### 2.1 Official Hermes dashboard: local control, config, PTY chat

Hermes' official dashboard is a browser UI for managing a Hermes
installation. It starts with `hermes dashboard`, binds to
`127.0.0.1:9119` by default, and states that it runs entirely on the
user's machine with no data leaving localhost.

Important details for First-Agent:

- **Local-first default:** host defaults to `127.0.0.1`; non-localhost
  binding requires `--insecure` and is called dangerous because it can
  expose API keys.
- **Optional web/PTY extras:** the dashboard is not mandatory for the
  core install. Web and PTY dependencies are extras.
- **Status page:** shows version, gateway status, active sessions,
  recent sessions, message counts, token usage, and previews.
- **Chat tab:** embeds the actual Hermes TUI through `/api/pty`, a
  WebSocket, a server-side pseudo-terminal, and xterm.js. Slash
  commands, model picker, tool-call cards, markdown streaming,
  approval prompts, and theming work because the real TUI is running.
- **Config page:** turns config fields into a form UI, including model,
  terminal backend, display, agent, delegation, memory, and approvals.

The main v0.2 lesson: First-Agent does not need to choose between CLI
and web UI. A UI can start as a thin local dashboard and preserve the
CLI/TUI as the canonical interaction surface.

### 2.2 `pyrate-llama/hermes-ui`: single-file UI plus observability

`pyrate-llama/hermes-ui` is a single-file React/HTML app with a
lightweight Python proxy. Its README emphasizes:

- SSE streaming with real-time tokens;
- expandable tool-call visualization;
- message editing and resending;
- pause, interject, and stop controls;
- live stats for sessions, messages, tools, and tokens;
- tabbed terminal logs: Gateway, Errors, Web UI, All;
- file browser for `~/.hermes`;
- memory inspector for memory files;
- skills browser;
- jobs monitor;
- MCP tool browser;
- artifact panel that auto-detects HTML, SVG, code blocks, and saved
  file paths, rendering HTML/SVG in a sandboxed iframe;
- responsive/mobile layout and keyboard shortcuts.

This is close to the shape First-Agent wants eventually: an operator
cockpit, not only a chat transcript. The artifact panel is especially
relevant for coding agents because generated files, diffs, rendered
Markdown, screenshots, and test output all deserve first-class display.

### 2.3 `EKKOLearnAI/hermes-web-ui`: full BFF dashboard

`EKKOLearnAI/hermes-web-ui` is a Vue/TypeScript dashboard with a Koa
BFF (backend-for-frontend) that proxies to Hermes Gateway. It covers:

- real-time SSE chat;
- multi-session management and source grouping;
- active-session indicators;
- session search;
- tool-call detail expansion;
- file upload/download across local, Docker, SSH, and Singularity;
- model selector and model discovery from credential pools;
- usage analytics, cost estimates, cache hit rate;
- scheduled jobs;
- platform channel configuration;
- skills/memory browsing;
- log filtering;
- integrated web terminal through node-pty and xterm.js;
- token/username authentication;
- privacy settings such as PII redaction.

The architecture is explicit:

```text
Browser -> BFF (Koa, :8648) -> Hermes Gateway (:8642)
```

For First-Agent, a BFF is attractive because the browser should never
touch raw secrets, arbitrary filesystem paths, or shell execution
directly. A small Python BFF can enforce ADR-6 path allow-lists and
expose only curated event and command APIs.

### 2.4 `lotsoftick/hermes_client`: CLI-driven streaming without gateway

`lotsoftick/hermes_client` is a React/TypeScript UI that deliberately
avoids requiring Hermes Gateway. Each chat turn invokes the Hermes CLI
and streams stdout to the browser over SSE. Notable patterns:

- UI "agents" map to Hermes profiles;
- cross-app session sync lets terminal sessions appear in the web UI;
- xterm.js drawer hosts real model/config commands;
- file uploads are stored under a client directory and passed to the
  CLI as paths;
- cron, skills, and plugins are surfaced through CLI subcommands;
- conversation state stays under `~/.hermes`; the client invokes CLI
  and reads session JSON, rather than owning the source-of-truth state.

This is a good fallback design for First-Agent if a full gateway is
too early: drive the CLI as a subprocess, stream events, and read
session artifacts from the repository or agent state directory.

### 2.5 `nesquena/hermes-webui`: CLI parity and three-panel layout

`nesquena/hermes-webui` emphasizes "nearly 1:1 parity with Hermes CLI"
from a web UI, with no framework/bundler and a three-panel layout:

```text
left: sessions/navigation
center: chat
right: workspace file browsing
```

It keeps model, profile, and workspace controls in the composer footer
and uses a circular context ring for token usage. The README emphasizes
session projects, tags, tool-call cards, workspace file preview, and
secure SSH-tunnel access.

For First-Agent, the three-panel layout is a strong candidate:

```text
left: sessions / Mechanical Wiki / runs
center: conversation and plan
right: files / diffs / artifacts / audit
```

---

## 3. Pi coding agent UI/product signals

Pi's public positioning is useful because it resists turning every idea
into a core feature. Its principles are relevant to First-Agent:

- **Minimal harness:** Pi says to adapt the harness to workflows, not
  the other way around.
- **Four surfaces:** interactive, print/JSON, RPC, and SDK.
- **Tree-structured history:** sessions are stored as trees; users can
  navigate to a previous point and continue from there.
- **Share/export:** sessions can export to HTML or upload to a GitHub
  gist.
- **Context engineering:** AGENTS.md/SYSTEM.md, compaction, skills,
  prompt templates, dynamic context, and extensions shape what enters
  the context window.
- **Steering while working:** Enter sends an interrupting steering
  message after the current tool; Alt+Enter sends a follow-up.
- **Primitives, not features:** subagents, permission popups, plan
  mode, todos, background bash, and MCP are left to extensions or
  environment-specific tooling.

For First-Agent v0.2 UI, the key Pi lesson is to design around **stable
protocol surfaces** and extension points:

```text
core loop -> event stream -> CLI/TUI/web/RPC clients
```

The UI should not force one hard-coded workflow. It should expose the
same trace and command surfaces that scripts and tests use.

### 3.1 Pi extensions and UI context

Pi extensions can register tools, commands, event handlers, custom
rendering, and custom TUI UI through `ctx.ui`. Example use cases
include permission gates, protected paths, git checkpoints, custom
compaction, interactive tools, stateful todo tools, CI triggers, and
custom renderers.

This supports a First-Agent rule: UI affordances should attach to the
same lifecycle events as hooks and tools. If v0.2 adds "approve this
write," "show this diff," or "ask a question," those should be events
from the inner loop rather than hard-coded frontend special cases.

### 3.2 Pi package ecosystem and context-mode

The Pi package catalog shows what users add when the core is small:

- subagents / parallel orchestration;
- MCP adapters;
- permission systems;
- real-time code feedback;
- markdown previews;
- schedule prompts;
- interactive shells;
- ask-user tools.

`context-mode` is especially relevant. Its package page says raw MCP
tool outputs consume context quickly, then proposes sandbox tools,
SQLite FTS5 session continuity, BM25 retrieval, code-executed analysis,
and output compression. It also exposes diagnostics and an analytics
dashboard.

For First-Agent, this reinforces the Mechanical Wiki direction. The UI
should show **retrieved and indexed state**, not dump every raw event
into the model context or the chat pane.

---

## 4. OpenClaw and OpenClaw UI forks

### 4.1 OpenClaw Gateway protocol

OpenClaw documents its Gateway WebSocket protocol as the single control
plane and node transport. Clients such as CLI, web UI, macOS app,
iOS/Android nodes, and headless nodes connect over WebSocket and
declare role/scope at handshake time.

Important protocol ideas:

- WebSocket text frames with JSON payloads;
- first frame is a `connect` request;
- server sends a challenge;
- clients declare protocol version, client ID/version/platform/mode,
  role, scopes, capabilities, commands, auth, locale, user agent, and
  device identity;
- server responds with negotiated protocol, features, snapshot, policy,
  role/scopes, and optional device token;
- role/scopes include bounded operator permissions such as approvals,
  read, write, and secrets-talk;
- server treats client-provided capabilities as claims and enforces
  allow-lists server-side.

First-Agent does not need that full system for v0.2, but the direction
is correct: UI is a **client** of a typed control plane. Browser trust
should be weaker than backend trust.

### 4.2 OpenClaw Control UI skill search PR

OpenClaw PR #60134 added `skills.search` and `skills.detail` Gateway
RPC methods and Control UI integration: debounced search input, results
list, detail dialog, and install button. The PR explicitly scoped out
existing install/update/status flows and noted Gateway/orchestration,
skills/tool execution, API/contracts, and UI/DX as touched areas.

Lessons for First-Agent:

- adding UI often requires adding control-plane methods, not just
  frontend code;
- search/discovery of skills/tools is a real UX gap;
- PRs should keep a narrow boundary: search/detail before install;
- Gateway schemas, error propagation, and tests are part of UI work.

### 4.3 `knightafter/openClaw-web-interface`: small self-hosted UI

This community UI is a small Next.js/TypeScript interface for OpenClaw:

- real-time streaming;
- Markdown and code rendering;
- skills sidebar;
- local/private operation;
- gateway URL + token entry at runtime;
- SSH tunnel recommendation for remote VPS access;
- no hard-coded secrets in the codebase;
- WebSocket gateway connection.

This is the smallest useful pattern for First-Agent:

```text
chat + markdown + tool/skill sidebar + local gateway connection
```

### 4.4 `grp06/openclaw-studio`: operator dashboard

OpenClaw Studio positions itself as a dashboard to connect to Gateway,
see agents, chat, manage approvals, and configure jobs. Its setup
explicitly distinguishes:

```text
Browser -> Studio
Studio  -> Gateway
```

It supports local/local, cloud/local, and cloud/cloud scenarios, with
Tailscale recommended for remote access.

First-Agent should avoid cloud scenarios in v0.2 but keep the
separation in mind. The UI should be able to point at a local backend
URL and should not assume frontend and agent process are always bundled.

### 4.5 `23ag1/ClawdOS`: personal OS temptation

ClawdOS is useful mostly as a warning. It turns OpenClaw into a full
productivity workspace: tasks, notes, RSS/news, package tracking,
dashboard, skill marketplace, command palette, local intent routing,
rich editor, database, auth, row-level security, and update system.

This is compelling for a personal assistant, but too broad for
First-Agent v0.2. Keep these ideas as plugin candidates:

- task board for agent work queues;
- notes/wiki editor;
- skill/tool marketplace;
- local intent routing for common UI actions.

Do not include them in the first UI milestone. First-Agent's core value
is repository work with traceable knowledge and PRs, not a general
personal OS.

---

## 5. Human-agent UI research

### 5.1 Magentic-UI: transparent, controllable web agents

Magentic-UI is explicitly a human-centered agent UI. Its README and
Microsoft Research blog emphasize:

- reveal the plan before execution;
- let users guide actions;
- request approval for sensitive operations;
- browse websites, execute code, and analyze files;
- support MCP agents;
- support monitoring tasks that span minutes to days;
- evaluate autonomous task completion and interaction capabilities.

The blog lists co-planning, co-tasking, action guards, and plan
learning. The arXiv abstract frames human-in-the-loop systems as a way
to combine oversight/control with AI efficiency and names mechanisms
such as co-planning, co-tasking, multi-tasking, action guards, and
long-term memory.

Mapping to First-Agent:

- **Co-planning:** show the plan before file writes or PR creation.
- **Co-tasking:** support interrupt/steer while tools are running.
- **Action guards:** map ADR-6 sandbox checks and destructive actions
  into UI approval requests.
- **Plan learning:** save good plans as research/prompts later, not in
  v0.2 core.
- **Long-term memory:** show Mechanical Wiki retrievals and allow
  explicit updates.

### 5.2 DuetUI: bidirectional task-oriented interfaces

DuetUI proposes human-agent co-generation of task-oriented interfaces.
Its abstract says users want to shape interfaces rather than relying on
one-shot outputs, and describes a bidirectional context loop: the agent
scaffolds the interface by decomposing the task while user
manipulations steer the agent's next generation step.

For First-Agent, the near-term lesson is modest: do not make all user
control text-only. Plans, file selections, diff approvals, tool
allow-list edits, and acceptance criteria can be structured UI objects.
User edits to those objects should feed back into the agent loop as
explicit events.

### 5.3 AXIS: API-first beats raw UI manipulation

AXIS argues that agents interacting directly with application UIs can
suffer from high latency and low reliability, then prioritizes API
actions over UI actions. Its abstract reports lower task completion
time and cognitive workload while maintaining high accuracy in a Word
environment.

This matters because First-Agent's UI should not encourage the agent to
drive the browser UI to manipulate its own state. The human uses the UI;
the agent uses typed tools and APIs. The UI is observability and
control, not the agent's main tool surface.

---

## 6. Recommended First-Agent v0.2 UI shape

### 6.1 Non-goals

Do **not** start with:

- a public SaaS dashboard;
- multi-user auth and teams;
- mobile apps;
- marketplace;
- personal OS features;
- visual workflow builder;
- browser automation UI;
- generic chat app detached from traces;
- agent controlling the UI as its own primary interface.

### 6.2 MVP surfaces

The smallest useful v0.2 UI should expose:

1. **Session list**
   - current/previous runs;
   - branch/repo;
   - status: idle/running/needs input/failed/done;
   - model/tier if available;
   - timestamps and token/cost estimates when available.
2. **Conversation + plan**
   - user messages;
   - assistant plan;
   - current step;
   - pause/stop/interject;
   - acceptance criteria.
3. **Tool/audit cards**
   - tool name;
   - arguments summary;
   - path(s) touched;
   - sandbox allow/deny;
   - stdout/stderr summary;
   - duration and exit code;
   - expandable raw detail.
4. **Mechanical Wiki browser**
   - list/index entries from `knowledge/llms.txt`;
   - search over docs/research/ADR notes;
   - retrieved context shown with source paths;
   - explicit "add note" or "open file" actions.
5. **Files/artifacts panel**
   - changed files;
   - diffs;
   - rendered Markdown;
   - test/lint output;
   - generated reports/screenshots when present.
6. **Approvals and questions**
   - sandbox escalation request;
   - destructive command approval;
   - missing secret question;
   - user choice prompts.

### 6.3 Backend shape

Start with a local BFF:

```text
Browser
  -> loopback HTTP/SSE or WebSocket BFF
  -> First-Agent session/event store
  -> tool runner / sandbox / Mechanical Wiki
```

Minimum backend endpoints/events:

| Surface | Shape | Notes |
|---|---|---|
| Session list | `GET /api/sessions` | Read-only at first. |
| Event stream | `GET /api/sessions/{id}/events` via SSE | Chat, tool, audit, status, artifact events. |
| User input | `POST /api/sessions/{id}/input` | Message, interrupt, follow-up. |
| Control | `POST /api/sessions/{id}/control` | Pause, stop, resume. |
| Approval | `POST /api/approvals/{id}` | Approve/deny with reason. |
| Wiki search | `GET /api/wiki/search?q=` | Backed by Mechanical Wiki / SQLite FTS. |
| Artifact | `GET /api/artifacts/{id}` | Sanitized content only. |

Use SSE first unless bidirectional streaming or multiplexing requires
WebSocket. OpenClaw's full role/scope protocol can wait.

### 6.4 Event schema sketch

Events should be append-only and replayable:

| Event | Required fields |
|---|---|
| `session.started` | `session_id`, `repo`, `branch`, `cwd`, `ts` |
| `message.created` | `session_id`, `role`, `content`, `parent_id`, `ts` |
| `plan.updated` | `session_id`, `steps`, `current_step`, `ts` |
| `tool.started` | `tool_call_id`, `name`, `args_summary`, `paths`, `ts` |
| `tool.finished` | `tool_call_id`, `status`, `result_summary`, `duration_ms`, `ts` |
| `sandbox.decision` | `tool_call_id`, `decision`, `rule`, `paths`, `reason` |
| `approval.requested` | `approval_id`, `kind`, `summary`, `risk`, `expires_at` |
| `approval.resolved` | `approval_id`, `decision`, `reason`, `ts` |
| `artifact.created` | `artifact_id`, `kind`, `path`, `mime`, `summary` |
| `wiki.hit` | `query_id`, `path`, `title`, `score`, `snippet` |
| `check.finished` | `command`, `status`, `summary`, `log_artifact_id` |
| `session.finished` | `session_id`, `status`, `summary`, `ts` |

These events line up with ADR-6 sandbox needs and future ADR-7 hook
contracts. They also give eval harnesses trace material.

---

## 7. Product recommendation

For v0.2, choose **operator cockpit** over **assistant product**.

Recommended milestone sequence:

1. **Trace viewer first**
   - static HTML or local web page rendering one recorded session;
   - no live control yet;
   - validates event schema and UI layout.
2. **Live local dashboard**
   - loopback server;
   - session list;
   - SSE event stream;
   - tool/audit cards;
   - wiki search.
3. **Human-in-loop controls**
   - pause/stop/interject;
   - approve/deny;
   - plan editing before execution.
4. **Artifacts**
   - diffs, Markdown render, test logs, generated files.
5. **Optional PTY/TUI bridge**
   - only if a terminal UI exists and users want browser access.
6. **Remote access docs**
   - SSH tunnel / Tailscale only;
   - no public bind by default.

Defer:

- teams/auth;
- cloud sync;
- marketplace;
- mobile app;
- productivity suite;
- agent-generated dynamic UI;
- OpenClaw-style multi-device roles/scopes.

---

## 8. Open questions for the project lead

1. Should First-Agent v0.2 UI be **read-only trace viewer first** or
   **live control dashboard first**?
2. Is the preferred frontend stack Python-only/no-build, or is a
   TypeScript/Vite app acceptable?
3. Should a future UI live inside this repo or as a separate
   `first-agent-ui` repo?
4. Should the first backend protocol be SSE + REST, or WebSocket
   JSON-RPC from day one?
5. Should Mechanical Wiki editing be allowed from the UI in v0.2, or
   read-only until audit/versioning is mature?
6. Should the UI show all tool arguments/results by default, or use
   redaction/summary-first cards?
7. Should UI research feed into ADR-7, or wait for an ADR-8 dedicated
   to UI/control plane?

## 9. Proposed next prompt

```text
Write an ADR prep note for First-Agent v0.2 UI/control-plane design.

Inputs:
- knowledge/research/agent-ui-research-radar-v0-2-2026-05.md
- knowledge/research/cutting-edge-agent-research-radar-2026-05.md
- ADR-2 and ADR-6

Scope:
- Do not implement UI.
- Decide between trace-viewer-first and live-dashboard-first options.
- Propose minimal local BFF + event schema.
- Include non-goals and security defaults.
- Keep it as research/pre-ADR, not accepted ADR.
```
