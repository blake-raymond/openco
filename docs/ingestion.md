# Filing inbox notes

Setup's voice-notes step sends you here. You do this after `make setup`,
from the public openco checkout:

```bash
python3 scripts/intake
```

Intake reads every markdown note in the private repo's `inbox/` except
`README.md`. It appends facts and stories, writes one new decision file
per decision, and moves the note to `inbox/filed/`. The commit is on a
new branch. It does not commit to main.

If the data repo has an `origin` remote, intake pushes that branch and
opens a pull request against main. Without a remote, it leaves the
branch and tells you. Review the new fact lines before merging.

## Note shape

```markdown
---
date: 2026-11-15
---

What was said.

## Facts

- The sentence an agent would be allowed to repeat.

## Stories

- What happened, as a story.

## Decisions

### keep-tea-time
status: proposed
context: Why this came up.
decision: Keep the demo tea time
why: The fictional staff takes a break then.
```

`date` is `YYYY-MM-DD`. A decision slug is lowercase. `status` is
`proposed`, `accepted`, or `superseded`. Intake writes one file,
`decisions/YYYY-MM-DD-slug.md`, with sections for context, the
decision, and why. The file's `source` is the note or the call. There
is no combined decisions log. Sections you do not need can be left out,
except a decision still needs `decision` and `why`.

The fact line intake writes looks like:

```text
- 2026-11-15 | source: inbox/filed/2026-11-15-some-note.md | The sentence.
```

The source is required. CI fails a fact line that has no source.

A meeting transcript uses the same sections, with `kind: transcript`.
Intake stores the full raw file under `calls/` and points the facts and
decisions at that file. The format is in [docs/setup/calls.md](setup/calls.md).
Do not commit a transcript to this public repository.
