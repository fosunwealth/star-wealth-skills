# 星财富（复星财富）技能市场

七个面向港股与美股的投研、交易与行情插件，按 [Agent Plugins 1.0.0](https://agent-plugins.org) 打包。Cursor 与 Grok Bot 都能直接加载，不需要转换。

[English](../README.md) | **简体中文** | [繁體中文](./README.zh-TW.md)

## 插件清单

| 插件 | 版本 | 做什么 |
|:--|:--|:--|
| [biopharma-data-hub](../biopharma-data-hub/) | 1.1.6 | 一只生物医药标的的公开管线、审批、专利与文献拉取，加上上游追踪。 |
| [biopharma-strategy](../biopharma-strategy/) | 1.1.6 | 四步式生物医药研究笔记，带重要性过滤。 |
| [fosun-wealth-star-ai](../fosun-wealth-star-ai/) | 1.2.0 | 港股、美股、A 股行情、K 线、ETF、IPO 日历与财报，走一个托管连接器；也可以把整句话交给 Star AI。 |
| [fw-deep-research](../fw-deep-research/) | 3.7.57 | 为一只港美股产出一份可交互的 HTML 深度研报。 |
| [fw-trade-skill](../fw-trade-skill/) | 2.0.6 | 港股与美股下单，纸面或实盘，必须逐笔确认。 |
| [hk-ipo-analysis](../hk-ipo-analysis/) | 4.12.18 | 港股 IPO 列表，或一份带五因子评分与中签档位的 HTML 打新报告。 |
| [tech-hardware-research](../tech-hardware-research/) | 2.5.4 | 科技硬件标的或赛道的 HTML 研究笔记：供应链、指标与陷阱。 |

七个里有五个是自带脚本的只读研究插件。`fosun-wealth-star-ai` 自己不持有行情逻辑：它带十个只读行情工具，外加 `ask_star_ai`，会把请求交给 Star AI，能取到本人持仓与交易流程，那些动作受该服务自己的逐笔确认约束。`fw-trade-skill` 自己下单，不拿到明确的「是」就不发。

## 安装

### Cursor

1. 打开 **Dashboard → Plugins & MCPs**，把这个仓库加为团队市场（**Add Marketplace → Import from Repo**）。
2. 设置 **Marketplace Access** 与 **Plugin Installation**。默认关闭，让成员自己决定装不装。
3. 成员从 **Customize** 里安装插件。

### Grok Bot

1. 用同一个 Cursor 账号登录 Grok Bot 桌面应用。
2. 侧栏打开 **Connect apps**，安装这个团队市场允许的插件。
3. 需要密钥的插件，把密钥存进 Bot 的密钥库（**Settings → Secrets**）。不要把密钥贴进对话。

`fosun-wealth-star-ai` 不需要密钥。它的卡片上是 **Authorize**：浏览器打开我们的 OAuth 授权页，用户用手机号加短信码登录，票由宿主保管。

## 发布前本地检查

```bash
cp -R fw-deep-research ~/.cursor/plugins/local/fw-deep-research
```

然后在 Cursor 里跑 **Developer: Reload Window**，在 **Customize** 里启用这个插件。要用拷贝，不要用软链接。

## 首次运行

每个技能在第一次需要时自己装依赖。

| 插件 | 首次安装 |
|:--|:--|
| 四个走 REST 网关的技能 | `python3 -m pip install -r requirements.txt` |
| `fosun-wealth-star-ai` | 不需要，连接器在服务端运行 |
| `fw-deep-research` | `python3 -m pip install -r scripts/requirements.txt`，然后 `npm install` |
| `hk-ipo-analysis` | `npm install` |
| `fw-trade-skill` | `bash install.sh` |

有两个技能通过一个 Streamable HTTP MCP 网关取数：`https://aiapi.fosunhanig.com/ai-mcp-research/mcp`。宿主问 MCP 服务器地址时填它。另外四个技能用 HTTPS 直接调各自的网关，不需要 MCP 条目。

`fosun-wealth-star-ai` 是唯一在自己 `mcp.json` 里声明 MCP 服务器的插件：`https://aiapi.fosunhanig.com/ai-fin-agent/mcp`。宿主从 `WWW-Authenticate` 挑战里发现它的授权服务器，并用动态注册给自己登记，所以仓库里没有写死任何 OAuth 客户端。

## 格式

- 根目录 `plugin.json` 是可移植的 [Agent Plugins 1.0.0](https://agent-plugins.org/plugin-authors/manifest) 清单。它的 schema 只收自己定义的字段。
- 根目录 `.cursor-plugin/marketplace.json` 是 Cursor 读的多插件市场清单。它列出全部七个插件的名字与来源；某个插件目录没出现在里面，市场就会把它藏起来。
- 每个插件的 `.cursor-plugin/plugin.json` 补上 Cursor 额外要求的字段：图标路径与组件路径。
- `mcp.json` 遵循 Agent Plugins 的 MCP schema，它对服务器条目只收 `type`、`url`、`headers`。所以 `fosun-wealth-star-ai` 只写地址，别的都不写。
- 每个 `skills/<名字>/SKILL.md` 遵循 [Agent Skills 规范](https://agentskills.io/specification)。frontmatter 只放 `name`、`description`、`license`、`allowed-tools`、`metadata`、`compatibility`，`metadata` 里只放字符串。

## 校验这个仓库

```bash
bash scripts/check.sh
```

脚本按官方 JSON Schema 校验每一份清单，用官方技能校验器跑七个技能，再扫一遍密钥、构建产物与只给宿主看的说明。它打印 `PASS`，或者直接点名要改哪几行。

## 安全

- 所有密钥都留在仓库外面：宿主密钥库，或者安装脚本写的那个文件。仓库里只有模板。
- `fosun-wealth-star-ai` 用 OAuth 2.1 加 PKCE 对接我们自己的授权服务器。仓库里不存客户端密钥、API key 或票。
- 研究类技能不下单。本仓库的任何内容都不构成投资建议。
- `fw-trade-skill` 在下单、改单、撤单前必须拿到明确确认，第一次实盘下单前会展示风险提示。

## 许可

MIT。见 [LICENSE](../LICENSE)。
