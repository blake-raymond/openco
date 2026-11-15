# MCP tools

Agents act through MCP servers. This repo ships the shape of the
config, not the credentials and not a guessed install command.

Copy `config/mcp.example.json` and fill `command` and `args` from that
server's own docs. Leave secrets empty in the json file. Put the real
values in `.env`, which is gitignored.

The named servers are the ones the playbook calls for:

| Server | Secret env name | When |
| --- | --- | --- |
| GitHub | `GITHUB_TOKEN` | repos and pull requests |
| Gmail | `GMAIL_CREDENTIALS` | mail |
| Calendar | none in the example | the calendar you already use |
| Slack | `SLACK_TOKEN` | when you use Slack |
| Notion | `NOTION_TOKEN` | the second brain |
| Linear | `LINEAR_API_KEY` | when you use Linear |
| Stripe | `STRIPE_SECRET_KEY` | when you take payment |
| PostHog | `POSTHOG_API_KEY` | when you have a product to measure |
| Supabase | `SUPABASE_ACCESS_TOKEN` | when you use Supabase |

Grok Bot may already be connected to some of these. A coding agent on
a clean machine still needs the command from the official server docs.
This page does not pin package names, because those change and were
not re-checked as installable here.

The check fails if `config/mcp.example.json` contains a token-shaped
string or a non-empty secret value.
