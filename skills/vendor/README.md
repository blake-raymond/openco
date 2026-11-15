# Vendored skills

`scripts/install-skills` clones the lockfile into this folder at the
pinned commits. The clones are gitignored. Commit the lockfile, not
the trees.

Pinned on 15 Nov 2026, after checking that each repository existed:

| Name | What that commit contains |
| --- | --- |
| anthropics/skills | 20 skills: documents, MCP builder, frontend design, skill-creator, webapp testing, and similar examples. |
| obra/superpowers | 15 skills: brainstorm, plan, execute, TDD, debugging, worktrees, subagents, review. |
| mattpocock/skills | 39 skills: engineering and productivity, plus in-progress and deprecated. |
| addyosmani/agent-skills | 25 skills from spec through ship, with review and test gates. |

Read a pack before you rely on it. The pins are commits that existed
on that date, not a review of every line.
