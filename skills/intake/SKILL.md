---
name: intake
description: File notes from the private data repo inbox into facts, stories, and decisions as a pull request.
---

# File inbox notes

Use this when a note or a call transcript is sitting in the private data repo's `inbox/` or `calls/`.

A transcript (`kind: transcript`) is copied in full to `calls/YYYY-MM-DD-slug.md`. Facts and decisions from it use that file as their source. Do not edit the call file later, and do not copy it into the public openco repository.

## Steps

1. From the public openco checkout, run `python3 scripts/intake`.
2. Read the new fact lines, story lines, and decision files on the branch.
3. The script commits on a new branch. It does not commit to main.
4. When the data repo has an `origin` remote, the script opens a pull request against main. Merge it only after the lines match the note.

## Checks

- Every new fact line has a date and a source.
- Every new decision file is `decisions/YYYY-MM-DD-slug.md` with `date`, `status`, `source`, and sections Context, Decision, and Why.
- A note marked EXAMPLE does not become a real company claim.

## Mistakes

- Do not merge your own intake pull request without reading it.
- Do not add a fact that was not in the note.
- Do not edit an old fact line to correct it. Append a new line.
