# Granola

`make setup` can install Granola, or you can use your agent and drop
transcripts in `calls/`. The install is opt-in. On macOS, when `brew`
is installed, the verified command is `brew install --cask granola`
(Homebrew cask `granola`, checked 2026-11-15, macOS only). Every other
OS gets the official download page, https://www.granola.ai/download.
There is no verified Linux package.

`scripts/import-granola` is an optional extra for a transcript you
already have. It is not part of setup, and a new company does not
start by importing one.

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
