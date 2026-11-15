# Calls

Grok Bot joins meetings and writes the transcript. That is the primary
path. Any other recorder or agent can drop the same file. Granola is
optional and is not the default. See [granola.md](granola.md).

The full raw transcript is stored only in the private data repo, under
`calls/`, as `YYYY-MM-DD-slug.md`. Do not edit it after it is committed.
Do not commit a transcript to the public openco repository. The privacy
scan rejects one.

## Generic transcript

```markdown
---
date: 2026-11-15
title: Demo call
kind: transcript
---

Alex Example: The demo company answers calls from 09:00 to 17:00.

Sam Sample: That is the whole fictional meeting.

## Facts

- The demo company answers calls from 09:00 to 17:00 in the example timezone.

## Decisions

### keep-hours
decision: Keep the demo phone window
why: The fictional staff is only there during that window.
supersedes:
```

`date` is `YYYY-MM-DD`. `title` is one line. `kind` is `transcript`.
Each speaker turn is `Name: words`. Facts and decisions are optional.
When they are present, intake copies them out and points their source
at the call file.

## Where to drop it

- `calls/YYYY-MM-DD-slug.md` in the private repo. The file is already
  the stored transcript. Intake will not change it. If it contains
  Facts or Decisions sections, intake appends those and links them back.
- `inbox/YYYY-MM-DD-slug.md` with `kind: transcript`. Intake copies the
  whole file into `calls/` and then files the extracted lines.

From the public checkout:

```bash
python3 scripts/intake
```

Intake commits on a new branch. It does not commit to main.
