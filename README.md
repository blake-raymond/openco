# openco

Public setup for running a company from markdown and git, following
Greg Isenberg's [49-step playbook](https://x.com/gregisenberg/status/2121331227009364340).

This repository is the part anyone can clone and get the same machine:
the instruction file, the folder layout, the scripts that file notes,
and the checks. The company itself lives in a **private** git
repository this setup creates. Nothing real is stored here. The files
under `templates/data/` are a fake example of that layout.

Phase 1 is the scaffold. Phase 2, on top of it, is the brain layout and
the capture scripts for playbook steps 1–6, 9, and 11. Later steps are
in [ROADMAP.md](ROADMAP.md).

## Set up

You need Python 3.11 or newer and git. No packages to install.

```bash
git clone https://github.com/blake-raymond/openco.git
cd openco
python3 scripts/validate --selfcheck
make setup
```

`make setup` creates `../openco-data`, copies `templates/data` into it,
makes the first commit, and writes the path to `.openco/data-repo`
(gitignored). Use another path with either of these:

```bash
make setup ARGS="--dest /absolute/path/openco-data"
OPENCO_DATA_REPO=../my-openco-data make setup
```

A relative path is resolved from this checkout, not from the shell's
current directory. The destination must sit outside this repository.
Setup will not overwrite a folder that is not already an openco-data
checkout.

Set `git config user.name` and `user.email` before setup. Setup does
not create a GitHub remote. When you want intake to open pull requests,
create a **private** repository, push `main` once, and add it as
`origin`. See [docs/private-data.md](docs/private-data.md).

Open the private repo folder as an Obsidian vault. `.obsidian/` is
already there. `me/` is how you think, write, and decide.

## File a note

The skeleton includes one fake inbox note.

```bash
python3 scripts/intake
```

Intake appends facts and stories, writes decision files, and commits
on a new branch. It does not commit to main. With an `origin` remote it
opens a pull request. The note format is in
[docs/ingestion.md](docs/ingestion.md). The agent instructions are in
[skills/intake/SKILL.md](skills/intake/SKILL.md).

## Calls, voice, and memory

- [docs/setup/granola.md](docs/setup/granola.md) and `python3 scripts/import-granola FILE`
- [docs/setup/wispr.md](docs/setup/wispr.md)
- [docs/setup/memory.md](docs/setup/memory.md)

Granola's CSV export does not document its columns, so the importer
reads a generic transcript and says so. Wispr, claude-mem, and mem0
were not installed here.

## Rules agents follow

[AGENTS.md](AGENTS.md) is the instruction file. [CLAUDE.md](CLAUDE.md)
points at it.

- Read `AGENTS.md` and the private `facts.md` before making a company claim. Cite the line. If it is not there, do not say it.
- Do not overwrite an entry. Append a dated one.
- Always date lines and record files.
- Lines and files marked EXAMPLE are fake.
- Intake does not commit to main.

## Layout

```text
AGENTS.md                         instruction file
CLAUDE.md                         pointer to AGENTS.md
templates/data/                   skeleton copied into the private repo
  .obsidian/                      vault config, so the data repo opens in Obsidian
  me/                             how you think, write, and decide
  customers/  calls/  playbooks/  decisions/
  pricing.md  facts.md  stories.md  voice.md
  memory/  learnings/  inbox/
  scripts/check.py                front matter, fact sources, append-only
  .github/workflows/check.yml     CI for the private repo
scripts/intake                    file inbox notes as a pull request
scripts/import-granola            generic transcript to calls/
skills/intake/                    skill for that filing step
docs/setup/                       Wispr, Granola, memory
```

## Checks

```bash
make check
```

That runs `python3 scripts/validate --selfcheck`. It checks the public
tree and the template, builds a temporary openco-data repo, files the
sample note onto a branch, and rejects an edit to an old fact.

## What this is not

There is no database. The brain is markdown plus git. A future backend
could replace that. This phase does not add one.
