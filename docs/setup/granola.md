# Granola (optional)

Granola is not the default call recorder. Grok Bot is. The transcript
that gets stored is the generic file in [calls.md](calls.md), whoever
produced it.

If you already have a Granola export, `scripts/import-granola` can turn
a generic transcript into `calls/YYYY-MM-DD-slug.md` in the private
data repo. It does not commit. Put that file on a branch. Do not commit
it to main, and do not commit it to the public openco repository.

## What was checked

[Exporting notes](https://docs.granola.ai/help-center/sharing/exporting-notes)
was read on 15 Nov 2026. The documented export is a CSV from Settings,
then Profile, then Generate CSV. It includes the title, the note
summary, the transcript, and other details, for notes you own that
have a summary. The page does not name the CSV columns, so the script
does not parse that file.

The public API documents transcript items with speaker, text, start
time, and end time. This script does not call that API.

Pass the generic transcript from [calls.md](calls.md):

```bash
python3 scripts/import-granola path/to/transcript.md
```
