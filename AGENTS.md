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
- `facts.md` in the private repo
- `voice.md` when the task is writing in the founder's voice
- the latest file in `memory/` when you need the last session
- [docs/ingestion.md](docs/ingestion.md) when the task files an inbox note

Entries marked EXAMPLE are fake. Do not cite one as a company fact.

## Claims

Before you state a fact about the company, its customers, its numbers,
or its prices, cite the `facts.md` line it came from. A line looks like:

```text
- 2026-11-15 | source: calls/2026-11-15-example-seed.md | EXAMPLE: ...
```

Cite the date and the source. If the sentence is not a line in that
file, say you do not have a fact for it. Do not invent the claim, and
do not fill the gap from a customer note, a playbook, a call, or a
memory file. Those can be the source of a fact. They are not a second
facts file.

## Do not overwrite

Do not overwrite an existing entry. Append a new dated line, or add a
new dated file. Always date it.

Lines in `facts.md`, `stories.md`, `pricing.md`, and `voice.md` stay
as they were committed. A correction is a new line.

A decision is a new file in `decisions/` with front matter `date`,
`decision`, `why`, and `supersedes`. `supersedes` names the earlier
file, or it is empty. Do not edit the earlier file.

Record files in `me/`, `customers/`, `calls/`, `playbooks/`, `memory/`,
and `learnings/` use the file name `YYYY-MM-DD-slug.md` and the same
date in front matter. After one is committed, leave it alone.

## Filing notes

Drop a note in the private `inbox/`, then run:

```bash
python3 scripts/intake
```

Intake opens a pull request. It does not commit to main. See
[skills/intake/SKILL.md](skills/intake/SKILL.md).

## Skills

Shareable skills live in `skills/` in this repository. Do not copy
private notes here.

## Private data

No real customers, numbers, transcripts, credentials, or personal notes
belong in this public repository. The checker rejects common secret and
contact patterns. Read [docs/private-data.md](docs/private-data.md).

## Instruction log

Append a dated line when these instructions change. Do not rewrite an
earlier line.

- 2026-11-15: Initial phase 1 instructions. The brain is markdown in the private git repo. This public repo is the setup and the checks.
- 2026-11-15: Phase 2 layout. Facts are lines in facts.md. Decisions are files under decisions/ with date, decision, why, and supersedes. Intake opens a pull request and does not commit to main.
