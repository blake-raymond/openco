# Private data

The public openco repository is safe to clone and to publish. The
private repository, `openco-data` by default, is where real notes go.

Never commit these to the public repository:

- customers, calls, numbers, prices, or transcripts
- the facts file, voice file, stories, or decision files once they contain real entries
- proprietary skills
- the second brain once it contains real notes
- `.env` files, keys, tokens, or the `.openco/` pointer (it is gitignored)

`make setup` refuses to create the private repo inside this checkout.
`scripts/validate` rejects tracked files that look like keys, private
keys, phone numbers, or email addresses outside `example.com`,
`example.org`, and `example.net`.

Create the GitHub remote for openco-data as a private repository
yourself. Setup does not create a GitHub repo and does not add a remote.
From the private checkout:

```bash
git remote add origin https://github.com/YOUR_ACCOUNT/openco-data.git
git push -u origin main
```

Use your own account and keep that repository private.
