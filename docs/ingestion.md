# Filing inbox notes

From the public openco checkout, after `make setup`:

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
decision: Keep the demo tea time
why: The fictional staff takes a break then.
supersedes:

Keep the demo tea time at 16:00 example time.
```

`date` is `YYYY-MM-DD`. A decision slug is lowercase. `supersedes` may
be empty, or it may name the earlier decision file. Sections you do not
need can be left out.

The fact line intake writes looks like:

```text
- 2026-11-15 | source: inbox/filed/2026-11-15-some-note.md | The sentence.
```

The source is required. CI fails a fact line that has no source.
