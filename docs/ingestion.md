# Filing voice notes and transcripts

Run this from the public openco checkout after `make setup`.

```bash
python3 scripts/ingest inbox/examples/2026-11-15-example-morning-note.md
```

That sample is fake. A real note goes in the private repo first, where
`inbox/voice-notes/` and `inbox/transcripts/` are gitignored:

```bash
python3 scripts/ingest inbox/voice-notes/2026-11-15-some-note.md
```

Paths are tried as given, then inside the private repo.

## Note shape

```markdown
---
date: 2026-11-15
kind: voice-note
key: some-note
---

What was said, in your own words.

## Facts

### some-fact
title: One line title
category: claim

The sentence an agent would be allowed to say after a human is willing
to keep it. category is claim, story, number, or pricing.

## Stories

### some-story
title: One line title

What happened, as a story.

## Decisions

### some-decision
title: One line title
because: The reason, in one line.

What was decided.
```

`kind` is `voice-note` or `meeting`. `key` is a lowercase slug. Sections
you do not need can be left out. A note with no sections is still
archived.

## What ingest writes

- `transcripts/YYYY-MM-DD-key.md` — the note, unchanged
- new entries at the end of `facts/FACTS.md`, `stories/STORIES.md`, and `company-brain/decisions/DECISIONS.md`

Then it commits those files in the private repository. It does not
commit anything in the public repository. Running it again on the same
note fails, because the transcript and the slugs already exist.

Filing does not make a new fact true by itself. The facts file is the
allow-list. Read it before repeating a claim. Example entries are
marked EXAMPLE and are not company truth.
