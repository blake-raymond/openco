# MCP tools

When setup reaches MCP, it points you here and does not write secrets.
You put real values in `.env`. `config/mcp.example.json` keeps every
secret empty. The check fails if that file contains a token.

Copy the example and fill `command` and `args` from that server's own
docs. Package names were not pinned here.

| Server | Secret env name | When you use it |
| --- | --- | --- |
| GitHub | `GITHUB_TOKEN` | repos and pull requests |
| Gmail | `GMAIL_CREDENTIALS` | mail |
| Calendar | none in the example | the calendar you already use |
| Slack | `SLACK_TOKEN` | Slack |
| Notion | `NOTION_TOKEN` | the second brain |
| Linear | `LINEAR_API_KEY` | Linear |
| Stripe | `STRIPE_SECRET_KEY` | payments |
| PostHog | `POSTHOG_API_KEY` | product analytics |
| Supabase | `SUPABASE_ACCESS_TOKEN` | Supabase |

Grok Bot may already be connected to some of these. A coding agent on
a clean machine still needs the command from the official server docs.
