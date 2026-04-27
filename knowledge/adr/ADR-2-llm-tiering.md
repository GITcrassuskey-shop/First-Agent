# ADR-2 — LLM tiering & access

- **Status:** accepted
- **Date:** 2026-04-27
- **Deciders:** project owner (`0oi9z7m1z8`), Devin (drafting)

## Context

FA's value proposition (see
[`project-overview.md`](../project-overview.md) §1) includes
**routing different agent roles to different LLM tiers** instead of
defaulting one model to everything. The user has stated a budget
mix of approximately:

- 60 % top-tier OSS (GLM 5.1 / Kimi 2.6 / Xiaomi Mimo 2.5)
- 30 % mid-tier OSS (Nemotron 3 Super / Qwen 3.6 27B)
- 10 % elite (Anthropic Claude latest available)

We need to decide **how roles map to tiers**, **how access is
configured**, and **what fallback behaviour** is acceptable.

User answers in PR-#17 follow-up (Q2 + Q3):

- Q2 (role routing): "Multi-LLM static routing: Planner=top-tier OSS,
  Coder=mid-tier OSS, Debug/elite=Claude — config-driven, всегда так."
- Q3 (access): "Mix: per-model в config (некоторые local, некоторые
  через OpenRouter, elite через Anthropic)."

## Options considered

### Option A — Single-LLM, role by prompt

- Pros: simplest; one provider; predictable cost.
- Cons: cannot leverage tier mix; loses FA's stated value.

### Option B — Static role routing (chosen)

Each role pinned to a tier in config; never auto-escalates.

- Pros:
  - Predictable cost: a Coder turn never silently calls Anthropic.
  - Predictable behaviour: same role + same input → same provider.
  - Simple to debug — rerun a turn against its known tier.
- Cons:
  - No graceful degradation when the pinned model is down (must be
    handled by per-role fallback chain in config).
  - Hard tasks routed to Coder fail loudly instead of escalating.
    User-stated preference accepts this.

### Option C — Hybrid dynamic routing with hard-task detector

Mid-tier by default, escalate to top-tier or elite on a detector
signal (e.g. complexity heuristic, stuck-loop detector).

- Pros: cost-optimised; auto-recovery for hard cases.
- Cons: detector reliability is a research problem of its own; not
  appropriate for v0.1; costs become unpredictable.

## Decision

We will choose **Option B (static role routing)** with the following
concrete mapping for v0.1:

| Role | Tier | Default model | Provider |
|---|---|---|---|
| **Planner** | top-tier OSS | GLM 5.1 (or Kimi 2.6 / Mimo 2.5 — config-pickable) | AnyProvider API key / OpenRouter |
| **Coder** | mid-tier OSS | Nemotron 3 Super (or Qwen 3.6 27B) | AnyProvider API key / OpenRouter |
| **Debug / elite** | top tier | DIFFERENT top-tier OSS / top tier from AnyProvider API key | AnyProvider API key / OpenRouter |
| **Eval (LLM-as-judge)** | top-tier OSS | DIFFERENT model ; isolated config slot so judge can be version-pinned | AnyProvider API key / OpenRouter |

Configuration lives in a single YAML/TOML file (e.g.
`~/.fa/models.yaml`) with one block per role:

```yaml
planner:
  primary:   { provider: openrouter, model: "z-ai/glm-5.1" }
  fallback:  { provider: AnyProvider, model: "GLM-5.1-Air" }
coder:
  primary:   { provider: AnyProvider, model: "Nemotron-3-Super-49B" }
  fallback:  { provider: openrouter, model: "qwen/qwen3-coder-27b" }
debug:
  primary:  { provider: any, model: "claude-opus-4-7-20260301" }
  fallback: { provider: any, model: "claude-sonnet-4-7-20260301" }
judge:
  primary: { provider: openrouter, model: "z-ai/kimi 2.6", pinned: true }
```

> **Note on model slugs.** The strings above (`z-ai/glm-5.1`,
> `claude-opus-4-7-20260301`, etc.) are illustrative of the
> *shape* of the config, not authoritative slugs at any given
> date. Provider catalogs change; pick the actual current slug
> from OpenRouter / Anthropic / vLLM at config time. The
> *decision* is the table above (which tier each role lives in
> and how `primary → fallback` chains); the *implementation*
> resolves slugs to whatever is current.

- "primary → fallback" chain per role; **no cross-tier escalation**
  on failure.
- Anthropic is the only mandatory remote in v0.1 (for Debug). Coder
  is preferentially local (vLLM); Planner can be either. This matches
  the user's "remote API ≈ 99 %" tolerance while leaving headroom
  for local-only Coder if vLLM is configured.

## Consequences

- **Positive:** Cost predictability — a Coder turn cannot silently
  hit Anthropic. Token-efficiency metric in
  [`project-overview.md`](../project-overview.md) §3 becomes
  meaningful.
- **Positive:** Per-role evaluation is straightforward — swap one
  block of config to A/B-test models on a role.
- **Positive:** The `judge:` role being version-pinned mitigates
  R5 (eval baseline drift) from `project-overview.md` §7.
- **Negative:** No auto-escalation means a Coder failure on a hard
  task surfaces as a hard error; the **user must explicitly invoke
  Debug** (or rewrite the prompt). v0.2 may revisit this if the
  pattern shows real friction.
- **Negative:** Three providers (Anthropic + OpenRouter + local vLLM)
  triples auth surface area and failure modes (R3 in
  `project-overview.md` §7). Mitigated by per-role fallback chain.
- **Follow-up work this unlocks:**
  - `src/fa/llm/router.py` — minimal role-based dispatcher reading
    `~/.fa/models.yaml`.
  - Provider adapters: `provider_client.py`, `openrouter_client.py`,
    `vllm_local_client.py` (one thin wrapper per provider).
  - Secrets policy: `~/.fa/secrets.env` (chmod 600), never committed.
  - Decision deferred to a future ADR: how to express token / cost
    budgets per role in the same config.

## References

- [`project-overview.md`](../project-overview.md) §6 (key constraints — LLM providers).
- [`research/memory-architecture-design-2026-04-26.md`](../research/memory-architecture-design-2026-04-26.md) §1 bullet 2 (mixed-LLM design constraint).
- [`research/agent-roles.md`](../research/agent-roles.md) §5.1 (Planner / Executor / Critic minimum-set rationale; Coder maps to Executor here).
- PR #17 review (`https://github.com/GITcrassuskey-shop/First-Agent/pull/17`) — Q2 + Q3 verbatim answers.
