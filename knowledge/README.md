# Knowledge

Durable project knowledge for First-Agent. Everything here is:

1. **Committed** to the repo so it is versioned and reviewable.
2. **Cross-referenced** from Devin Knowledge notes where useful (see
   [`docs/devin-reference.md`](../docs/devin-reference.md#1-knowledge-notes--долговременная-память)).

## Layout

```
knowledge/
├── README.md                 # this file
├── project-overview.md       # one-page product + scope snapshot
├── adr/                      # architecture decision records
│   ├── README.md
│   └── 0000-template.md
├── prompts/                  # reusable prompts
│   ├── README.md
│   └── research-topic.md
└── research/                 # (created on demand) research notes
```

## Conventions

- One concept per file.
- Markdown only. Keep under ~250 lines — split if longer.
- Link to source URLs for any non-obvious claim.
- When a file is superseded, don't delete — mark it `> **Status:** superseded by …` and add the replacement link.

## What goes where

| If it is… | Put it in… |
|---|---|
| A decision we made (and why) | `knowledge/adr/` |
| Background research / literature summary | `knowledge/research/` |
| A reusable prompt | `knowledge/prompts/` |
| Project-wide context (mission, scope, users) | `knowledge/project-overview.md` |
| How-to / guide / reference | `docs/` (not here) |
