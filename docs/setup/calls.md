# Calls

Setup asks whether to install Granola or to use your agent. Your agent
is the path that installs nothing. You drop the transcript it writes
into your data repo. A new company does not start by importing old calls.

The full raw transcript stays only in your data repo, under `calls/`,
as `YYYY-MM-DD-slug.md`. Do not edit it after it is committed. Do not
commit a transcript to the public openco repository.

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
status: proposed
context: The fictional staff is only there during that window.
decision: Keep the demo phone window
why: The fictional staff is only there during that window.
```

`date` is `YYYY-MM-DD`. `title` is one line. `kind` is `transcript`.
Each speaker turn is `Name: words`.

Drop the file in `calls/` or in `inbox/`. Then run `python3 scripts/intake`
from this checkout. Intake stores the full text in `calls/` and points
facts and decisions at that file. It commits on a branch, not on main.

Granola is optional. See [granola.md](granola.md).
