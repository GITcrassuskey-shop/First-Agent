# Prompts Library

Reusable prompts for recurring First-Agent tasks. Keep prompts short, versioned, and
reviewable — think of each file as a small contract with Devin.

## Rules

- **One prompt per file.** Filename: `<verb>-<slug>.md` (e.g. `research-topic.md`, `scaffold-module.md`).
- **Front-matter** at the top with purpose and inputs (see template).
- **Idempotent.** Running the same prompt twice should produce equivalent output, not
  compound on itself.
- **Link, don't paste.** Reference files/URLs; don't embed long excerpts.
- **No secrets.** Ever.

## Template

```markdown
---
purpose: <one-sentence description>
inputs:
  - <variable name>: <what to fill in>
last-reviewed: YYYY-MM-DD
---

[Objective]
...

[Context]
...

[Approach]
...

[Constraints]
...

[Acceptance]
...

[Out of scope]
...
```

## Index

| File | Purpose |
|---|---|
| [`research-topic.md`](./research-topic.md) | Research `<topic>` and produce a structured note. |
| [`ingest-youtube-video.md`](./ingest-youtube-video.md) | Turn a YouTube URL into a canonical research note via the tiered ingestion workflow. See [`docs/video-ingestion.md`](../../docs/video-ingestion.md). |
