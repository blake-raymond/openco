# Granola

Setup does not install Granola. Grok Bot is the recorder you use.
Granola is optional.

If you already have an export, `scripts/import-granola` can turn a
generic transcript into `calls/YYYY-MM-DD-slug.md` in your data repo.
It does not commit. Intake, or a branch you open yourself, is how that
file gets reviewed. Do not commit the transcript to the public
repository.

The export page, read on 15 Nov 2026, says you generate a CSV from
Settings, then Profile. The CSV includes the title, summary, transcript,
and other details. It does not name the columns, so the script does not
parse that file. Use the generic transcript in [calls.md](calls.md).

```bash
python3 scripts/import-granola path/to/transcript.md
```
