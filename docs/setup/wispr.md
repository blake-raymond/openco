# Wispr Flow

Wispr Flow is the voice dictation tool named in the playbook. This page
is the repo-side setup. It does not install Wispr for you.

## What was checked

The iOS help page [Using Notes in Wispr Flow for iOS](https://docs.wisprflow.ai/articles/3529886556-using-notes-in-wispr-flow-for-ios)
was read on 15 Nov 2026. It says Scratchpad notes can be copied or
shared, and that Copy and Share send raw Markdown, not formatted
output. That page does not describe writing notes into a git folder.

## What to do

1. Dictate the note in Wispr Flow.
2. Copy the raw Markdown.
3. Save it as a new file in the private repo's `inbox/`, named
   `YYYY-MM-DD-slug.md`, with `date` in the front matter. The note shape
   is in [docs/ingestion.md](../ingestion.md).
4. From the public openco checkout, run `python3 scripts/intake`.
5. Review the pull request. Intake does not commit to main.

## Not verified here

Desktop Scratchpad, Notetaker "Copy as Markdown", and any third-party
exporter that reads Wispr's local database were not installed or fully
read for this change. Do not point a database exporter at the data repo
until you have checked that tool yourself. The supported path in this
repo is: copy Markdown into `inbox/`, then run intake.
