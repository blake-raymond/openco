# Notion second brain

This is an optional extra, not part of `make setup`. A new company
starts by writing notes in `me/`. `scripts/export-notion` only reads a
Notion database you already have and writes `me/notion/` in your data
repo. Do not use it to import another company's data as the starting point.

If you later choose to point it at your own database, create a token
from the page below and put the token and database id in `.env`. The
script does not print them back.

https://developers.notion.com/docs/create-a-notion-integration

That page, read on 15 Nov 2026, is where you create a personal access
token (older screens call it an internal integration): New token, the
Notion API capability, then copy the token once.

Then share your database with that token. The query docs say to open
the database ••• menu, choose Add connections, and select it.
Otherwise a later read returns 404.

Put `NOTION_TOKEN` and `NOTION_SECOND_BRAIN_DB` in `.env`. The id is
the value you would pass to `GET /v1/databases/{database_id}`, not the
whole URL. `SECOND_BRAIN=markdown` keeps `me/` as the brain.

Do not edit the Notion database from an agent without approval.
