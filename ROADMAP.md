# Roadmap

Source: Greg Isenberg, [Making the most AI pilled company is the whole game](https://x.com/gregisenberg/status/2121331227009364340) (13 Nov 2026). The lines below follow that playbook. They are grouped the way this repository will take them on.

**Phase 1 (steps 1–8) is in this repository.** Later phases are outlined so the next change has a place to land. They are not built.

The brain is markdown in the private `openco-data` git repository. A future backend could replace the markdown files and git history. Phase 1 does not add one.

## Phase 1 — Brain, steps 1–8

The scaffold is here. `make setup` creates the private repo. `scripts/intake` files notes as a pull request. `scripts/validate` and the data repo's own CI enforce dates, sources, and append-only history. [AGENTS.md](AGENTS.md) is the instruction file.

| Step | What the playbook asks for | Where it lives |
| --- | --- | --- |
| 1 | A second brain: one folder of markdown on how you think, write, and decide (Obsidian). | Notion is the default (Commonplace book). `me/` is the markdown fallback, with `.obsidian/` so the data repo opens as a vault. `scripts/export-notion` snapshots pages to `me/notion/`. |
| 2 | Voice notes through the day. An agent files every fact, story, and decision. | `inbox/` plus `scripts/intake`, which opens a pull request. |
| 3 | A company brain: customers, calls, numbers, pricing, playbooks, and past decisions with the reason. | `customers/`, `calls/`, `pricing.md`, `playbooks/`, `decisions/`. |
| 4 | Record every call and meeting. Transcripts go straight into the brain. | `scripts/import-granola` writes `calls/`. The CSV column names are not documented, so the script takes a generic transcript. |
| 5 | A facts file: the only company claims an agent is allowed to say. | `facts.md`, one dated line with a source. [AGENTS.md](AGENTS.md) requires a citation. |
| 6 | A voice file: best posts (target 50), posts you hate (target 20), and words you never use. | `voice.md`. The em dash is the first banned word. The counts are the target, not a checker quota. |
| 7 | Keep it in git so every change has history. | openco-data is its own git repo. Its CI blocks edits of past dated entries. This public repo's history is the setup only. |
| 8 | One instruction file. Read it before any task, never overwrite, always date. | [AGENTS.md](AGENTS.md), with [CLAUDE.md](CLAUDE.md) pointing at it. |

The examples shipped in the skeleton are marked EXAMPLE. Replace nothing; append real dated entries in the private repo.

## Phase 2 — Brain and capture, steps 1–6, 9, and 11

The repo side of these steps is in the phase 2 change: `templates/data`,
the data-repo CI, `scripts/intake`, `scripts/import-granola`, and
`docs/setup/`. What is still manual, or not verified by running the
tool, is called out in those setup pages.

9. Give agents memory across sessions so they stop starting from zero (claude-mem, mem0). The plain fallback is `memory/`. Tool install steps are documented and were not run.
10. Pipe ads, analytics, CRM, and payments into one warehouse agents can query (Airbyte into ClickHouse). Not built. It waits for real data.
11. Feed that warehouse data nobody else has. That is the part a competitor cannot download. Intake and the Granola importer are the repo-side routes for notes and calls. Keeping them fed is manual.

Step 10 stays later. Exports and warehouse credentials stay out of this public repo.

## Phase 3 — Skills, steps 12–21

Not built, except the folder shape. This repo has `skills/example-make-tea/` as a fake shareable skill. openco-data has `skills/` for skills you are not publishing.

12. Do not start from zero. Install public skill libraries first (anthropics/skills, obra/superpowers, mattpocock/skills, addyosmani/agent-skills).
13. Add marketing skills too (coreyhaines31/marketingskills, Cody Schneider's graphed skills for static ads and UGC, boringmarketing skills).
14. Map every workflow and rank it by money made or saved.
15. Do each workflow once out loud and record it.
16. Turn the recording into a skill: when to use it, the steps, the checks, the mistakes to avoid.
17. One skill per job. Small and boring beats one giant prompt.
18. Connect tools with MCPs so agents can act, not only advise (Gmail, Slack, Stripe, Linear, Notion, PostHog, Supabase).
19. Give agents a browser.
20. Give agents a computer of their own for tools with no API.
21. Give the best skills away in public. That is the new lead magnet.

Automation from this repo: skills stay files in git. A later `scripts/publish-skill` copies one skill from openco-data into `skills/` here after a human chooses to publish it. The workflow map is a dated log in the private repo, same append-only rule as the facts file.

## Phase 4 — Agents, steps 22–30

Not built. Configuration would be added under an `agents/` directory in this repo. Logs and budgets that contain real figures would append to openco-data.

22. Run an orchestrator that stays on. It manages one agent per project, and each of those runs sub-agents.
23. Use coding agents for the building.
24. Wrap them so they plan, test, and remember.
25. Manage the fleet in one place. Every agent gets a job, a budget, and a log.
26. Put skills on triggers: daily, weekly, on every new lead, on every cancellation.
27. Route models. An expensive model plans and checks. Cheap models do the volume.
28. Cut the token bill with shorter outputs and smaller tool results.
29. Run a local model for data that cannot leave the machine.
30. Track cost per job. If a job costs more than it earns, fix it or stop it.

Automation from this repo: checked-in config for the orchestrator, the routes, and the triggers, plus a script that appends a cost line to a private log and fails the check when a job's cost is above its return.

## Phase 5 — Factory, steps 31–37

Not built. The build line would be GitHub Actions and scripts in this repo. The case library would live in openco-data so the cases can be real.

31. Build the line: spec, then builder agents in parallel git worktrees, then test, then review, then deploy.
32. Send design through the same line, and use a skill to strip anything that looks generated.
33. Turn every annoying task into an internal tool the day it shows up.
34. Turn every customer request into a pull request before a human reads it.
35. Give reviewer agents a named bar and reject until the answer is yes.
36. Keep 50 real cases with the right answer. Rerun them when a new model ships and switch to the winner.
37. Humans approve, own the outcome, and talk to customers.

Automation from this repo: one workflow file per stage, reading the bar and the cases from the private repo, and opening a pull request a human merges.

## Phase 6 — Loop, steps 38–41

Not built. Write-back would append to the private logs. A Friday job in this repo would open the playbook diff for a human to approve.

38. Every finished job writes back what worked, what failed, and what to stop doing.
39. Support tickets, analytics, and social comments flow in every night.
40. Every Friday an agent rewrites the playbooks from the week's results, and a human approves the diff.
41. Every month, rank everything by profit per human hour. Kill one thing and double one thing.

Automation from this repo: scheduled GitHub Actions that only append dated entries, and a pull request for playbook edits so the append-only check still passes on the old file (the change is a new dated playbook, not an edit of the old one).

## Phase 7 — Growth, steps 42–49

Not built. Scripts and published skills would be added here. Leads, ad accounts, and customer records stay in openco-data.

42. Research with agents before spending.
43. Let outbound run: find the leads, enrich them, verify them, send.
44. Send prospects finished work instead of a pitch.
45. Run ads in a loop: write the creative, publish it, kill the losers, scale the winners.
46. Let agents make the creative too: images, video, voice, and music.
47. Turn every finished job into content: the story, the number, and the prompt.
48. Every customer makes the brain smarter for the next one.
49. Once it works, point it at a new niche. Same agents, new context.

Automation from this repo: one script or skill per loop, with the private repo as the only place a lead, a spend figure, or a customer is written. Step 49 is a new private brain (another data repo) pointed at by `OPENCO_DATA_REPO`, using this same public setup.
