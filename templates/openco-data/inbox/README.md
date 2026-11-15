# Inbox

Drop a new voice note in `voice-notes/` or a meeting transcript in
`transcripts/`. Those two folders are gitignored so a raw note is not
committed by accident.

From the public openco checkout, run:

```bash
python3 scripts/ingest inbox/voice-notes/your-note.md
```

Ingest copies the note into `transcripts/`, appends any Facts, Stories,
and Decisions sections to the logs, and commits that in this private
repository. The sample notes in `examples/` are fake and already
committed so you can try the command once.
