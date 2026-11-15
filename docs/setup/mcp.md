# MCP tools

Setup asks if you want the official pages for the servers below. It
prints those pages. It does not run an installer, and it does not guess
a package name. Calendar has no verified page, so setup skips it.

You put real values in `.env`. `config/mcp.example.json` keeps every
secret and every command empty. The check fails if that file contains a
token. Connecting a server happens in your agent, from the official page.

| Server | Official page | Secret env name |
| --- | --- | --- |
| GitHub | https://github.com/github/github-mcp-server | `GITHUB_TOKEN` |
| Gmail | https://developers.google.com/workspace/gmail/api/guides/configure-mcp-server | `GMAIL_CREDENTIALS` |
| Calendar | none verified | none |
| Slack | https://slack.com/help/articles/48855576908307-Guide-to-MCP-in-Slack | `SLACK_TOKEN` |
| Notion | https://developers.notion.com/guides/mcp/get-started-with-mcp | `NOTION_TOKEN` |
| Linear | https://linear.app/docs/mcp | `LINEAR_API_KEY` |
| Stripe | https://docs.stripe.com/mcp | `STRIPE_SECRET_KEY` |
| PostHog | https://posthog.com/docs/model-context-protocol | `POSTHOG_API_KEY` |
| Supabase | https://supabase.com/docs/guides/ai-tools/mcp | `SUPABASE_ACCESS_TOKEN` |

PostHog's page documents `npx @posthog/wizard mcp add`. That command is
interactive, so setup prints it and does not run it. Stripe's page
documents an installer too. Setup prints the page and does not run the
installer.

Grok Bot may already be connected to some of these. Notion here is a
tool. It is not how the second brain gets imported.
