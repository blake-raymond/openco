---
name: skill-from-recording
description: Turn a recording of someone doing one job out loud into a SKILL.md pull request.
---

# Skill from a recording

Use this when `recordings/` has a transcript of one task done out loud.

## Steps

1. Read the recording. Do not copy private names or numbers into the skill.
2. Draft four sections in the recording, or in a scratch copy: When to use, Steps, Checks, Mistakes. One job only.
3. From the public checkout, run `python3 scripts/skill-from-recording PATH --name slug`.
4. The script commits `skills/<slug>/SKILL.md` in the private data repo on a new branch and opens a pull request. It does not commit to main.
5. Compare the steps to the recording before merging.

## Checks

- The skill has When to use, Steps, Checks, and Mistakes.
- It does not contain a transcript, a customer, or a secret.
- The source line points at the recording file.

## Mistakes

- Do not turn one recording into a giant prompt.
- Do not invent a step the recording did not do.
- Do not put the new skill in the public repo. Publishing is a later choice.
