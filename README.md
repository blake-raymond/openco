# openco

Public setup for running a company from markdown and git, following
Greg Isenberg's [49-step playbook](https://x.com/gregisenberg/status/2121331227009364340).
Your notes live in a private git repository you name. Nothing real is stored here.

## Quickstart

```bash
git clone https://github.com/blake-raymond/openco.git
cd openco
make setup
```

That one command checks git, Python, and `gh auth status`, asks you to
confirm the owner and name of your data repo, creates it private on
GitHub, copies the template, pushes, and turns on checks. Then it offers
Notion, calls, memory, skill packs, and MCP. Run it again to resume.
`make setup ARGS="--check"` shows what is done and what is missing.

The rest of this file is reference.

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

Grok Bot writes call transcripts. Drop that generic file in the private
repo's `inbox/` or `calls/`. The format is [docs/setup/calls.md](docs/setup/calls.md).
Full transcripts stay in the private `calls/` folder. Facts and
decisions link back to them. The public repo's check rejects a
transcript committed here.

`memory/` is the memory. [docs/setup/memory.md](docs/setup/memory.md)
keeps claude-mem and mem0 as optional notes that were not verified.
Wispr setup is [docs/setup/wispr.md](docs/setup/wispr.md). Granola is an
optional importer, [docs/setup/granola.md](docs/setup/granola.md), not
the default.

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
scripts/install-skills            clone the four pinned skill packs
scripts/intake                    file inbox notes and transcripts as a pull request
scripts/skill-from-recording      turn one recording into a private skill PR
scripts/import-granola            optional Granola path, not the default
routines/                         prompt, schedule, and trigger for each routine
tools/                            template for a tool that removes an annoyance
config/mcp.example.json           MCP shape, secrets left empty
skills/intake/                    skill for that filing step
docs/setup/                       calls, Wispr, memory, Notion, optional Granola
```

## Checks

```bash
make check
```

That runs `python3 scripts/validate --selfcheck`. It checks the public
tree and the template, builds a temporary data repo, files the
sample note onto a branch, and rejects an edit to an old fact.

## What this is not

There is no database. The brain is markdown plus git. A future backend
could replace that. This phase does not add one.
