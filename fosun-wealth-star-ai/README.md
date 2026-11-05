# fosun-wealth-star-ai

Explore Hong Kong, US, and China A-share market quotes, K-lines, ETFs, IPOs, and financial reports with Fosun Wealth Star AI, over one hosted connector. Or hand a whole request to Star AI: it reaches your own positions, and places an order only after you confirm that order.

**中文名**：星财富 Star AI 连接器

你问一只港股、美股或 A 股，它从星财富的数据服务取代码、实时行情、K 线、ETF 指标、IPO 日历和财报。你也可以把整句话交给 Star AI：它跑完整流程，能查你自己名下的持仓，也能在你逐笔确认之后下单。

## What this plugin contains

| File | What it is |
| --- | --- |
| `plugin.json` | Agent Plugins 1.0.0 manifest. Cursor and Grok Bot both read it. |
| `.cursor-plugin/plugin.json` | The Cursor manifest, with the logo path. |
| `mcp.json` | One Streamable HTTP MCP server, by URL. |
| `skills/fosunwealth/SKILL.md` | How the model should use the tools. |
| `assets/logo.svg` | The plugin icon. |

There is no server code here, and there is nothing to run locally. The tools live behind the MCP URL, the same shape Gmail uses: the host holds the connection, the plugin holds the instructions.

## Setup

1. Install the plugin from the marketplace. In Cursor open **Customize**; in Grok Bot open **Connect apps**.
2. Choose **Authorize** (or **Authenticate**) on the plugin card. A browser opens on `aiapi.fosunhanig.com`.
3. Sign in with your Fosun Wealth mobile number and the SMS verification code. The host keeps the token; this browser step happens once per host.

No API key goes into a chat, and no key is stored in this repository.

## What you can ask

- "How is Tencent Holdings doing right now — price, volume, turnover?"
- "Show me the last 20 daily K-line bars for Apple."
- "What is the fund size of the Tracker Fund of Hong Kong (02800.HK)?"
- "Which Hong Kong IPOs open for subscription this month?"
- "Compare the latest quarterly revenue and net income of Apple and Microsoft."

## Boundaries

- The ten market-data tools are read-only: they place no orders and change nothing.
- `ask_star_ai` reaches the rest of Star AI, including your own positions and the trading flows. An order or a cancellation goes out only after Star AI shows the details and you confirm that one. Fund transfers and account changes are not available here.
- Every figure comes from the connector's tool output. When a source is down, the answer says so instead of filling the gap.
- Market data and research summaries are for reference only and are not investment advice.

## Licence

MIT, for the plugin files in this directory. The hosted service behind the MCP URL is not part of this repository and is not covered by this licence.
