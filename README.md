# openco

Public setup for running a company from markdown and git, following
Greg Isenberg's [49-step playbook](https://x.com/gregisenberg/status/2121331227009364340).

This repository is the part anyone can clone and get the same machine:
the instruction file, the folder layout, the script that files notes,
and the checks. The company itself — customers, calls, numbers, prices,
transcripts, facts, voice, decisions, and the second brain — lives in a
**private** git repository this setup creates. Nothing real is stored here.
The files under `templates/openco-data/` are a fake example of that layout.

Phase 1 is playbook steps 1–8. Later steps are listed in [ROADMAP.md](ROADMAP.md) and are not built yet.

## Set up

You need Python 3.11 or newer and git. No packages to install.

```bash
git clone https://github.com/blake-raymond/openco.git
cd openco
python3 scripts/validate --selfcheck
make setup
```

`make setup` creates `../openco-data`, copies the skeleton into it,
makes the first commit, and writes the path to `.openco/data-repo`
(gitignored). Use another path with either of these:

```bash
make setup ARGS="--dest /absolute/path/openco-data"
OPENCO_DATA_REPO=../my-openco-data make setup
```

A relative path is resolved from this checkout, not from the shell's
current directory. The destination must sit outside this repository.
Setup will not overwrite a folder that is not already an openco-data
checkout. Run it again and it leaves existing notes alone.

Set `git config user.name` and `user.email` before setup. Those are the
author on the private repo's commits. Setup does not create a GitHub
remote. When you want one, create a **private** repository and add it
from inside openco-data. See [docs/private-data.md](docs/private-data.md).

## File a note

The skeleton includes two fake notes. Filing one shows the path:

```bash
python3 scripts/ingest inbox/examples/2026-11-15-example-morning-note.md
```

Ingest copies the note into `transcripts/` in the private repo, appends
its Facts, Stories, and Decisions to the logs, and commits there. A
second run refuses, because those entries already exist. The note format
is in [docs/ingestion.md](docs/ingestion.md).

Drop a real note in the private `inbox/voice-notes/` or
`inbox/transcripts/` (those folders are gitignored) and pass that path
to the same command.

## Rules agents follow

[AGENTS.md](AGENTS.md) is the instruction file. [CLAUDE.md](CLAUDE.md)
points at it. The rules that matter on every task:

- Read `AGENTS.md` and the private `facts/FACTS.md` before making a company claim. Cite the entry. If it is not there, do not say it.
- Do not overwrite an entry. Append a dated one.
- Always date headings as `## YYYY-MM-DD - slug`, or name a record file `YYYY-MM-DD-slug.md`.
- Lines and files marked EXAMPLE are fake.

## Layout

```text
AGENTS.md                         instruction file
CLAUDE.md                         pointer to AGENTS.md
ROADMAP.md                        all 49 steps
templates/openco-data/            skeleton copied into the private repo
  second-brain/                   step 1, Obsidian vault
  inbox/                          voice notes and transcripts waiting to be filed
  transcripts/                    step 4, raw notes after filing
  facts/FACTS.md                  step 5, the only sayable claims
  stories/STORIES.md              stories filed from notes
  voice/                          step 6, best posts, hated posts, unused words
  company-brain/                  step 3
    customers/ calls/ numbers/ pricing/ playbooks/
    decisions/DECISIONS.md        decisions and why
  skills/                         proprietary skills (private repo only)
skills/example-make-tea/          one fake shareable skill, for the later publish step
scripts/bootstrap                 make setup
scripts/ingest                    file a note into the private repo
scripts/validate                  dated entries, append-only history, no secrets
```

Open `templates/openco-data/second-brain/` as an Obsidian vault to see
the personal notes. In real use, open that folder inside openco-data
instead. Company records do not go in the second brain.

## Checks

```bash
make check
```

That runs `python3 scripts/validate --selfcheck`. It checks the public
tree, builds a temporary openco-data repo, files the sample notes, and
confirms that editing an old fact is rejected. On a pull request it
also checks that committed logs only grow and that committed record
files do not change.

GitHub Actions runs the same command.

## What this is not

There is no database and no plugin layer. The brain is markdown plus
git, which is step 7 of the playbook. A future backend could replace
that. This phase does not add one.
