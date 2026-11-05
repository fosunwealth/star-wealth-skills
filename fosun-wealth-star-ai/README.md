# fosun-wealth-star-ai

Hong Kong, US and China A-share market data, and the whole Star AI assistant, over one hosted connector.

港股、美股、A 股行情，加上整个 Star AI 助手，走同一个托管连接器。

## What it is · 它是什么

**EN** — Two ways in. Ten read-only market tools answer single lookups. `ask_star_ai` hands a whole request to Star AI, which runs its own tools: quotes, K-lines, ETFs, IPO calendars, financial statements, deep research reports, your own positions, and the trading flows it guards with a per-order confirmation.

**中文** — 两个入口。十个只读行情工具回答单点查询。`ask_star_ai` 把整句话交给 Star AI，由它自己调工具跑完整流程：行情、K 线、ETF、IPO 日历、财报、深度研报、你名下的持仓，以及每次都要你确认才发出去的交易流程。

## What this plugin contains · 插件里有什么

| File · 文件 | What it is · 是什么 |
|:--|:--|
| `plugin.json` | Agent Plugins 1.0.0 manifest · 标准清单 |
| `.cursor-plugin/plugin.json` | Cursor manifest with the logo path · Cursor 清单，带图标路径 |
| `mcp.json` | One Streamable HTTP MCP server · 一个 MCP 服务地址 |
| `skills/fosunwealth/SKILL.md` | How the model should use the tools · 模型怎么用这些工具 |
| `assets/logo.svg` | Plugin icon · 插件图标 |

There is no server code here, and nothing runs locally. The tools live behind the MCP URL — the same shape Gmail uses in Grok Bot: the host holds the connection, the plugin holds the instructions.

这里没有服务端代码，本地也不运行任何东西。工具在 MCP 地址后面——和 Gmail 在 Grok Bot 里的形态一样：宿主保存连接，插件只保存说明。

## Setup · 安装与授权

1. Install the plugin from the marketplace. In Cursor open **Customize**; in Grok Bot open **Connect apps**.
   从市场安装插件。Cursor 打开 **Customize**，Grok Bot 打开 **Connect apps**。
2. Choose **Authorize** on the plugin card. A browser opens on `aiapi.fosunhanig.com`.
   在插件卡片上点 **Authorize**，浏览器打开 `aiapi.fosunhanig.com`。
3. Sign in with your Fosun Wealth mobile number and the SMS code. The host keeps the token, so this happens once per host.
   用星财富手机号加短信验证码登录。票由宿主保管，每台宿主只需做一次。

No API key goes into a chat, and no key is stored in this repository.

不要把 API key 贴进对话，仓库里也不存任何密钥。

## What you can ask · 能问什么

- "How is Tencent Holdings doing right now — price, volume, turnover?"
  「腾讯控股现在走势怎么样，价格、成交量、成交额多少？」
- "Show me the last 20 daily K-line bars for Apple."
  「给我苹果最近 20 根日 K。」
- "Which Hong Kong IPOs open for subscription this month?"
  「这个月有哪些港股 IPO 开始认购？」
- "Do I hold any semiconductor names, and how are they doing?"
  「我持仓里有半导体吗，最近表现如何？」

## Boundaries · 边界

- The ten market-data tools are read-only: they place no orders and change nothing.
  十个行情工具只读：不下单、不改任何东西。
- `ask_star_ai` reaches the rest of Star AI, including your own positions and the trading flows. An order or a cancellation goes out only after Star AI shows the details and you confirm that one.
  `ask_star_ai` 能用到 Star AI 的其余能力，包括你名下的持仓与交易流程；下单或撤单必须由 Star AI 展示明细、你确认那一笔之后才发出。
- Fund transfers and account changes are not available here.
  转账和账户变更不在这里提供。
- Every figure comes from the connector's tool output. When a source is down, the answer says so instead of filling the gap.
  每个数字都来自连接器的工具返回。数据源不可用时，回答会明说，而不是把空白补上。
- Market data and research summaries are for reference only and are not investment advice.
  行情与研究摘要仅供参考，不构成投资建议。

## Licence · 许可

MIT, for the plugin files in this directory. The hosted service behind the MCP URL is not part of this repository and is not covered by this licence.

本目录内的插件文件为 MIT 许可。MCP 地址背后的托管服务不属于本仓库，也不在此许可范围内。
