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
- the latest file in `memory/` before you continue a session. That folder is the memory. Do not install another memory tool for this.
- [docs/ingestion.md](docs/ingestion.md) when the task files an inbox note

## Second brain

The second brain is a Notion database. Here that database is the
Commonplace book. Before a task about how Blake thinks, writes, or
decides, read it through the Notion MCP or the Notion API. Never edit
it without approval.

If `NOTION_TOKEN` and `NOTION_SECOND_BRAIN_DB` are unset, or
`SECOND_BRAIN=markdown`, read `me/` in the private data repo instead.
The notes shipped in `me/` are examples, not the Commonplace book.
`scripts/export-notion` only reads Notion and writes a snapshot under
`me/notion/`. See [docs/setup/notion-second-brain.md](docs/setup/notion-second-brain.md).

Entries marked EXAMPLE are fake. Do not cite one as a company fact.

## Claims

Before you state a fact about the company, its customers, its numbers,
or its prices, cite the `facts.md` line it came from. A line looks like:

```text
- 2026-11-15 | source: calls/YYYY-MM-DD-slug.md | EXAMPLE: ...
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

Full call transcripts live only in the private repo under `calls/`.
They are dated and are not edited later. Facts and decisions taken from
a call use that call file as their source. Do not commit a transcript
to this public repository.

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
- 2026-11-15: The second brain defaults to the Notion Commonplace book. `me/` is the fallback. Snapshot updates under `me/notion/` are allowed. Do not edit Notion without approval.
- 2026-11-15: `memory/` is the memory. claude-mem and mem0 stay optional and unverified. Call transcripts are generic files in the private `calls/` folder. Grok Bot is the primary recorder. Granola is optional. Do not commit transcripts to this public repo.
