# Wispr Flow

Setup does not install Wispr. You use it when you want voice notes,
then you drop the markdown into your data repo.

The iOS help page, read on 15 Nov 2026, says Copy and Share send raw
Markdown. It does not write into a git folder.

1. Dictate the note.
2. Copy the raw Markdown.
3. Save it in your data repo as `inbox/YYYY-MM-DD-slug.md`, with `date`
   in the front matter. The shape is in [docs/ingestion.md](../ingestion.md).
4. From this checkout, run `python3 scripts/intake`.

Desktop Scratchpad and Notetaker were not fully checked here. Do not
point a third-party database exporter at your data repo until you have
checked that tool yourself.
