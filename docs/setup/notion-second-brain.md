# Notion second brain

When setup reaches Notion, it asks if you want to do it now. If you
say yes, it prints this link and waits for two values. It writes them
to `.env` and does not print them back.

https://developers.notion.com/docs/create-a-notion-integration

That page, read on 15 Nov 2026, is where you create a personal access
token (older screens call it an internal integration): New token, the
Notion API capability, then copy the token once.

Then share your database with that token. The query docs say to open
the database ••• menu, choose Add connections, and select it.
Otherwise a later read returns 404.

Paste the token and the database id at the prompts. The id is the value
you would pass to `GET /v1/databases/{database_id}`, not the whole URL.

If you skip the step, `me/` is the fallback. `SECOND_BRAIN=markdown`
forces that fallback. Setup can resume later.

`scripts/export-notion` only reads Notion and writes `me/notion/` in
your data repo. Do not edit the Notion database from an agent without
approval.
