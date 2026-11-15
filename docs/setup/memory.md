# Agent memory

Playbook step 9 is memory across sessions. This repo does not install a
memory product. It gives you a plain folder, and names two tools whose
docs were read but not run.

## Plain fallback

`memory/` in the private data repo is markdown any agent can read.
Before a task, read the latest file there. When a session ends, add a
new dated file. Do not edit an old one.

```markdown
---
date: 2026-11-15
---

# Where we stopped

One short paragraph. Company claims in here also belong in facts.md.
```

This needs no account and no daemon. It is the path that works today.

## claude-mem

[Claude-Mem's introduction](https://docs.claude-mem.ai/introduction) was
read on 15 Nov 2026. It says the tool works with Claude Code, Codex,
Cursor, OpenCode, and 11 more agents, and that the install command is:

```bash
npx claude-mem install
```

Inside Claude Code it also documents:

```text
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

The same page says to restart Claude Code, and lists Cursor among
supported IDEs. It was not installed for this change, and it was not
checked inside Cursor. Treat the Cursor claim as documented by that
project, not as something this repo has verified.

If you install it, keep using `memory/` as well until a new session
actually resumes without a re-brief.

## mem0

Mem0's Claude Code plugin page, [docs.mem0.ai/integrations/claude-code](https://docs.mem0.ai/integrations/claude-code),
describes a Claude Code plugin that needs a Mem0 API key and:

```bash
claude plugin marketplace add mem0ai/mem0
claude plugin install mem0@mem0-plugins --scope user --config api_key="$MEM0_API_KEY"
```

That page was not installed or re-run here. It is written for Claude
Code. This repo does not claim it works in Cursor or Grok Bot.

## What not to do

Do not put API keys in the data repo or in this public repo. Do not
treat a memory tool's recall as a fact. If it is something an agent is
allowed to say about the company, it has to be a line in `facts.md`.
