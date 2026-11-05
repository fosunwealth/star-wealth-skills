# fosun-wealth-star-ai

Hong Kong, US and China A-share market data, and the whole Star AI assistant, over one hosted connector.

**English** | [简体中文](docs/README.zh-CN.md) | [繁體中文](docs/README.zh-TW.md)

## What it is

Two ways in. Ten read-only market tools answer single lookups. `ask_star_ai` hands a whole request to Star AI, which runs its own tools: quotes, K-lines, ETFs, IPO calendars, financial statements, deep research reports, your own positions, and the trading flows it guards with a per-order confirmation.

## What this plugin contains

| File | What it is |
|:--|:--|
| `plugin.json` | Agent Plugins 1.0.0 manifest |
| `.cursor-plugin/plugin.json` | Cursor manifest with the logo path |
| `mcp.json` | One Streamable HTTP MCP server |
| `skills/fosunwealth/SKILL.md` | How the model should use the tools |
| `assets/logo.svg` | Plugin icon |

There is no server code here, and nothing runs locally. The tools live behind the MCP URL — the same shape Gmail uses in Grok Bot: the host holds the connection, the plugin holds the instructions.

## Setup

1. Install the plugin from the marketplace. In Cursor open **Customize**; in Grok Bot open **Connect apps**.
2. Choose **Authorize** on the plugin card. A browser opens on `aiapi.fosunhanig.com`.
3. Sign in with your Fosun Wealth mobile number and the SMS code. The host keeps the token, so this happens once per host.

No API key goes into a chat, and no key is stored in this repository.

## What you can ask

- "How is Tencent Holdings doing right now — price, volume, turnover?"
- "Show me the last 20 daily K-line bars for Apple."
- "Which Hong Kong IPOs open for subscription this month?"
- "Do I hold any semiconductor names, and how are they doing?"

## Boundaries

- The ten market-data tools are read-only: they place no orders and change nothing.
- `ask_star_ai` reaches the rest of Star AI, including your own positions and the trading flows. An order or a cancellation goes out only after Star AI shows the details and you confirm that one.
- Fund transfers and account changes are not available here.
- Every figure comes from the connector's tool output. When a source is down, the answer says so instead of filling the gap.
- Market data and research summaries are for reference only and are not investment advice.

## Licence

MIT, for the plugin files in this directory. The hosted service behind the MCP URL is not part of this repository and is not covered by this licence.
