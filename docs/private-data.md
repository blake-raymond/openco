# Your data repo

The public openco repository is safe to clone. Your notes go in the
private repository you name when you run `make setup`.

Setup creates that GitHub repository as private, copies the template,
adds the remote, pushes, and enables checks. You do not create the
remote first. The name and path are stored in `.openco/setup-state.json`
and `.openco/data-repo`, both gitignored. Later scripts read that path.

Never commit these to the public repository:

- customers, calls, numbers, prices, or transcripts
- the facts file, voice file, stories, or decision files once they contain real entries
- proprietary skills
- the second brain once it contains real notes
- `.env` files, keys, tokens, or the `.openco/` directory

`scripts/validate` rejects tracked files that look like keys, private
keys, phone numbers, email addresses outside `example.com`,
`example.org`, and `example.net`, or a transcript file.
