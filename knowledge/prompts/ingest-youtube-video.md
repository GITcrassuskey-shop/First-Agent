---
purpose: Ingest a YouTube video and produce a structured research note.
inputs:
  - url: full YouTube URL (e.g. "https://www.youtube.com/watch?v=qUqcLNcP5Tc")
  - slug: kebab-case filename stem (e.g. "hermes-agent-architecture")
  - tier: "auto" (default), "0", "1", or "2" — see docs/video-ingestion.md
last-reviewed: 2026-04-23
---

[Objective]
Turn a single YouTube video at <url> into a canonical research note at
`knowledge/research/<slug>.md`, following the layered workflow in
[`docs/video-ingestion.md`](../../docs/video-ingestion.md).

[Context]
- Workflow reference: `docs/video-ingestion.md` (Tier 0 / 1 / 2).
- Reference implementation: `knowledge/research/video-ingestion-poc/ingest.py`.
- Previous example output: `knowledge/research/agent-video-research.md` (synthesis of 5 videos).
- Output contract: `artifacts/<video_id>/` with `meta.json`, `transcript.md`,
  optional `frames/` and `vlm.jsonl`. See §6 of `docs/video-ingestion.md`.

[Approach]
1. **Select tier.** Default `auto`:
   - If `OPENROUTER_API_KEY` set AND OpenRouter balance ≥ $1 → Tier 0
     (Gemini‑via‑OpenRouter, includes visual understanding).
   - Else if `OPENROUTER_API_KEY` set but no balance → Tier 1
     (yt‑dlp + optional VLM free‑tier pass; `GROQ_API_KEY` for ASR fallback).
   - Else → Tier 2 (scraper, no visuals).
   - Record the chosen tier and any fallbacks in `meta.json.tier_used` / `tried_tiers`.
   - On `402 Payment Required` from Tier 0, fall through to Tier 1 automatically.
2. **Run ingestion** via `video-ingestion-poc/ingest.py`:
   ```
   python knowledge/research/video-ingestion-poc/ingest.py <url> --tier <tier> \
     --out-dir artifacts/
   ```
3. **Verify transcript.** `artifacts/<vid>/transcript.md` must contain `[HH:MM:SS]` lines
   covering ≥ 90% of the video duration. Short gaps allowed only if marked
   `[🔇 silence]` or `[🖼️ visual @ ...]`.
4. **Extract concepts.** Read `transcript.md`, then produce the research note with
   the following sections, in order:
   - **TL;DR** (≤ 3 sentences).
   - **Source** (URL, duration, channel, tier used).
   - **Key concepts** (bullet list; each item: one-line description + `[HH:MM:SS]` anchor).
   - **Ranking matrix** with columns `concept | applicability (1-5) | sota-tier usefulness (1-5) | note`.
     Reuse conventions from `agent-video-research.md`.
   - **How it fits First-Agent** (short; 3–5 bullets tying concepts to
     `docs/architecture.md` or future modules).
   - **Open questions**.
5. **Open a draft PR** titled `research: ingest <slug>`.

[Constraints]
- Markdown only. Note ≤ 350 lines.
- Cite every non-obvious technical claim with a `[HH:MM:SS]` timestamp back to the video.
- Do **not** commit `artifacts/` — it is local, potentially large, and covered by `.gitignore`
  (add the rule if missing).
- Do **not** paste raw transcript chunks into the note; summarize.
- No API keys or cookies in the repo, ever.
- If Tier 0 fails, document the failure mode in the note's **Open questions**.

[Acceptance]
- `knowledge/research/<slug>.md` exists with all required sections.
- Each **Key concept** has a clickable `[HH:MM:SS]` timestamp linking back to the YouTube
  video (`https://youtube.com/watch?v=<id>&t=<sec>s`).
- Ranking matrix has ≥ 5 concepts scored on both axes.
- PR is in **draft** state; human marks ready-for-review after sanity check.

[Out of scope]
- Changes to other research notes.
- Modifying the ingestion workflow itself (that is
  [`docs/video-ingestion.md`](../../docs/video-ingestion.md)) — open a separate PR if needed.
- Synthesizing multiple videos into one note — that is a follow-up task (see
  `agent-video-research.md` for an example).
