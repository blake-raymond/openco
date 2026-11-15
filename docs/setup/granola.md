# Granola

Granola is the call recorder named in the playbook. This page is the
repo-side setup. It does not install Granola or call its API.

## What was checked

[Exporting notes](https://docs.granola.ai/help-center/sharing/exporting-notes)
was read on 15 Nov 2026. The documented export is:

1. Click the workspace name, then Settings.
2. Open Settings, then Profile, then Generate CSV.
3. Granola emails a download link. The link lasts 24 hours, and an
   account can generate one export every 24 hours.
4. The CSV includes the title, the note summary, the transcript, and
   other basic details, for notes you own that have a summary.

The page does not name the CSV columns. `scripts/import-granola` does
not guess them. If you pass it a CSV, it stops and points you here.

The public API documents a transcript as a list of items with speaker,
text, start time, and end time. This script does not call that API.

## Generic transcript

Until the CSV columns are written down, save a meeting as this
markdown and pass the file to the importer:

```markdown
---
date: 2026-11-15
title: Demo call
---

Alex Example: The demo company answers calls from 09:00 to 17:00.

Sam Sample: That is the whole fictional meeting.
```

`date` is `YYYY-MM-DD`. `title` is one line. Each speaker turn is
`Name: words`.

From the public openco checkout:

```bash
python3 scripts/import-granola path/to/transcript.md
```

That writes `calls/YYYY-MM-DD-slug.md` in the private data repo. It
does not commit. Put the file on a branch and open a pull request.
Do not commit it to main.

A fact that quotes the call still has to be a line in `facts.md` whose
source is that call file. Intake does not read `calls/` by itself.
