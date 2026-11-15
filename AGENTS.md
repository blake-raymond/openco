# Instructions

Read this file before any task.

openco is the public setup. The company brain lives in a private git
repository, usually named `openco-data`. Find it in this order:

1. `OPENCO_DATA_REPO`
2. `.openco/data-repo` (written by `make setup`, not committed)

If neither exists, do not invent company facts. Say that the data repo
is not configured.

## Read before acting

Before a task that touches the company, read:

- this file
- `facts/FACTS.md` in the private repo
- `voice/best.md`, `voice/hate.md`, and `voice/never-use.md` when the task is writing in the founder's voice
- [docs/ingestion.md](docs/ingestion.md) when the task files a voice note or a transcript

Entries in the public `templates/openco-data/` tree are examples. An
example contains the word EXAMPLE. Do not treat it as true, and do not
cite it as a company fact.

## Claims

Before you state a fact about the company, its customers, its numbers,
or its prices, cite the heading in `facts/FACTS.md` it came from, for
example `facts/FACTS.md` section `2026-11-15 - example-office-hours`.

If the sentence is not an entry in that file, say you do not have a
fact for it. Do not invent the claim, and do not fill the gap from a
customer note, a playbook, or a transcript. Those can point at a fact.
They are not a second facts file.

## Do not overwrite

Do not overwrite an existing entry. Append a new dated entry at the end
of the log, or add a new dated file. Always date it.

Logs:

- `facts/FACTS.md`
- `stories/STORIES.md`
- `company-brain/decisions/DECISIONS.md`
- `voice/best.md`
- `voice/hate.md`
- `voice/never-use.md`

A heading is `## YYYY-MM-DD - slug`. The slug is lowercase and unique
in that file.

Record files (transcripts, second-brain notes, customers, numbers,
prices, playbooks) use the file name `YYYY-MM-DD-slug.md` and the same
date in frontmatter. After one is committed, leave it alone. A
correction is a new file.

Commit those changes in the private repository. Do not commit the
private repository, its notes, or a copy of them into this public one.

## Filing notes

Put a voice note in the private `inbox/voice-notes/` or a meeting
transcript in `inbox/transcripts/`, then run:

```bash
python3 scripts/ingest path/to/note.md
```

Ingest appends facts, stories, and decisions and commits in the private
repository. It refuses to file a slug that is already present.

## Skills

Shareable skills live in `skills/` in this repository. Proprietary
skills live in `skills/` in the private repository. Do not copy a
private skill here unless a human has decided to publish it.

## Private data

No real customers, numbers, transcripts, credentials, or personal notes
belong in this public repository. The checker rejects common secret and
contact patterns. Read [docs/private-data.md](docs/private-data.md).

## Instruction log

Append a dated line when these instructions change. Do not rewrite an
earlier line.

- 2026-11-15: Initial phase 1 instructions. The brain is markdown in the private git repo. This public repo is the setup and the checks.
