# Memory

`memory/` in the private data repo is the memory. Read the latest file
there at the start of a session. When a session ends, add a new dated
file. Do not edit an old one.

```markdown
---
date: 2026-11-15
---

# Where we stopped

One short paragraph. Company claims in here also belong in facts.md.
```

This needs no account and no daemon. It is the path to use now.

## Optional tools

claude-mem and mem0 are not installed and were not verified here. Do
not switch the memory to either of them unless you have tried it
yourself. Keep writing `memory/` even if you experiment.

### claude-mem

[Claude-Mem's introduction](https://docs.claude-mem.ai/introduction) was
read on 15 Nov 2026. It says the tool works with Claude Code, Codex,
Cursor, OpenCode, and 11 more agents, and that the install command is
`npx claude-mem install`. Inside Claude Code it also documents the
plugin marketplace commands. The page says to restart Claude Code, and
lists Cursor among supported IDEs. That Cursor claim was not checked
in this repo.

### mem0

Mem0's Claude Code plugin page, [docs.mem0.ai/integrations/claude-code](https://docs.mem0.ai/integrations/claude-code),
describes a Claude Code plugin that needs a Mem0 API key. It was not
installed here. This repo does not claim it works in Cursor or Grok Bot.

Do not put API keys in either repository. Do not treat a memory tool's
recall as a fact. A company claim still has to be a line in `facts.md`.
