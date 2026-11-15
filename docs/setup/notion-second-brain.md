# Notion second brain

The default second brain is a Notion database. In this setup that
database is the Commonplace book. The markdown notes in `me/` are only
the fallback, for a checkout that does not have Notion configured.

Nothing in this public repository identifies that database. The token
and the database id stay in a gitignored env file.

## Choose the source

`SECOND_BRAIN` defaults to `notion`.

- `notion`, with both variables below set: agents read Notion. `scripts/export-notion` can snapshot it.
- `notion`, with either variable missing: openco falls back to `me/`.
- `markdown`: use `me/` and do not call Notion.

## Token

Notion's current quickstart creates a personal access token. Older
screens call the same kind of secret an internal integration. Use the
screen your workspace shows.

From [Create a Notion integration / quickstart](https://developers.notion.com/docs/create-a-notion-integration),
read on 15 Nov 2026:

1. Open personal access tokens in the developer portal.
2. Select New token.
3. Enter a name, select the Notion API capability, and create the token.
4. Copy the token once. Notion does not show it again.

On Business and Enterprise plans, creating a token can be turned off.
A workspace owner enables it in Settings, then Connections.

## Share the database

[Query a data source](https://developers.notion.com/reference/query-a-data-source)
says a connection can query a data source only after its parent database
is shared with that connection. Otherwise the query returns 404.

On the database page, open the ••• menu, choose Add connections, and
select the connection you just created.

## Env file

In the public openco checkout, put this in `.env`. That file is
gitignored. Do not commit the token or the database id. Do not paste
them into a note, a pull request, or `me/notion/`.

```bash
SECOND_BRAIN=notion
NOTION_TOKEN=
NOTION_SECOND_BRAIN_DB=
```

`NOTION_SECOND_BRAIN_DB` is the database id you would pass to
`GET /v1/databases/{database_id}`. It is the id in the database link,
not the whole URL.

## Snapshot

From this checkout, after `make setup`:

```bash
python3 scripts/export-notion
```

The script only reads Notion. It uses the public API as documented for
`Notion-Version: 2026-03-11`:

1. `GET /v1/databases/{database_id}` to list `data_sources`.
2. `POST /v1/data_sources/{data_source_id}/query` for the pages.
3. `GET /v1/blocks/{block_id}/children` for each page body.

It writes markdown under `me/notion/` in the private data repo. Commit
that folder on a branch. Do not commit it to main. The data repo CI
allows those snapshot files to change. It still blocks edits to the
dated notes in the rest of `me/`.

The Notion database remains the source. Do not edit it from an agent
without approval. A snapshot is a copy for git history, not a second
place to change the commonplace book.

## Agents

Before a task about how the operator thinks, writes, or decides, read
the database through the Notion connection in the agent (MCP or the
API). If those env vars are unset, read `me/` instead and treat the
shipped examples as fake.
