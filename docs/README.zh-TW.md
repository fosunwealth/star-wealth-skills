# 星財富（復星財富）技能市場

七個面向港股與美股的投研、交易與行情插件，按 [Agent Plugins 1.0.0](https://agent-plugins.org) 打包。Cursor 與 Grok Bot 都能直接載入，不需要轉換。

[English](../README.md) | [简体中文](./README.zh-CN.md) | **繁體中文**

## 插件清單

| 插件 | 版本 | 做什麼 |
|:--|:--|:--|
| [biopharma-data-hub](../biopharma-data-hub/) | 1.1.6 | 一隻生物醫藥標的的公開管線、審批、專利與文獻拉取，加上上游追蹤。 |
| [biopharma-strategy](../biopharma-strategy/) | 1.1.6 | 四步式生物醫藥研究筆記，帶重要性過濾。 |
| [fosun-wealth-star-ai](../fosun-wealth-star-ai/) | 1.2.0 | 港股、美股、A 股行情、K 線、ETF、IPO 日程與財務報表，走一個託管連接器；也可以把整句話交給 Star AI。 |
| [fw-deep-research](../fw-deep-research/) | 3.7.57 | 為一隻港美股產出一份可互動的 HTML 深度研究報告。 |
| [fw-trade-skill](../fw-trade-skill/) | 2.0.6 | 港股與美股下單，紙面或實盤，必須逐筆確認。 |
| [hk-ipo-analysis](../hk-ipo-analysis/) | 4.12.18 | 港股 IPO 列表，或一份帶五因子評分與中籤檔位的 HTML 打新報告。 |
| [tech-hardware-research](../tech-hardware-research/) | 2.5.4 | 科技硬件標的或賽道的 HTML 研究筆記：供應鏈、指標與陷阱。 |

七個裡有五個是自帶腳本的唯讀研究插件。`fosun-wealth-star-ai` 自己不持有行情邏輯：它帶十個唯讀行情工具，外加 `ask_star_ai`，會把請求交給 Star AI，能取到本人持倉與交易流程，那些動作受該服務自己的逐筆確認約束。`fw-trade-skill` 自己下單，不拿到明確的「是」就不發。

## 安裝

### Cursor

1. 開啟 **Dashboard → Plugins & MCPs**，把這個倉庫加為團隊市場（**Add Marketplace → Import from Repo**）。
2. 設定 **Marketplace Access** 與 **Plugin Installation**。預設關閉，讓成員自己決定裝不裝。
3. 成員從 **Customize** 裡安裝插件。

### Grok Bot

1. 用同一個 Cursor 帳號登入 Grok Bot 桌面應用。
2. 側欄開啟 **Connect apps**，安裝這個團隊市場允許的插件。
3. 需要密鑰的插件，把密鑰存進 Bot 的密鑰庫（**Settings → Secrets**）。不要把密鑰貼進對話。

`fosun-wealth-star-ai` 不需要密鑰。它的卡片上是 **Authorize**：瀏覽器會開啟我們的 OAuth 授權頁，使用者用手機號碼加短訊碼登入，票據由宿主保管。

## 發佈前本機檢查

```bash
cp -R fw-deep-research ~/.cursor/plugins/local/fw-deep-research
```

然後在 Cursor 裡執行 **Developer: Reload Window**，在 **Customize** 裡啟用這個插件。要用複製，不要用符號連結。

## 首次執行

每個技能在第一次需要時自己安裝依賴。

| 插件 | 首次安裝 |
|:--|:--|
| 四個走 REST 網關的技能 | `python3 -m pip install -r requirements.txt` |
| `fosun-wealth-star-ai` | 不需要，連接器在伺服器端執行 |
| `fw-deep-research` | `python3 -m pip install -r scripts/requirements.txt`，然後 `npm install` |
| `hk-ipo-analysis` | `npm install` |
| `fw-trade-skill` | `bash install.sh` |

有兩個技能透過一個 Streamable HTTP MCP 網關取數：`https://aiapi.fosunhanig.com/ai-mcp-research/mcp`。宿主詢問 MCP 伺服器位址時填它。另外四個技能用 HTTPS 直接呼叫各自的網關，不需要 MCP 條目。

`fosun-wealth-star-ai` 是唯一在自己 `mcp.json` 裡宣告 MCP 伺服器的插件：`https://aiapi.fosunhanig.com/ai-fin-agent/mcp`。宿主從 `WWW-Authenticate` 挑戰裡發現它的授權伺服器，並用動態註冊給自己登記，所以倉庫裡沒有寫死任何 OAuth 客戶端。

## 格式

- 根目錄 `plugin.json` 是可移植的 [Agent Plugins 1.0.0](https://agent-plugins.org/plugin-authors/manifest) 清單。它的 schema 只收自己定義的欄位。
- 根目錄 `.cursor-plugin/marketplace.json` 是 Cursor 讀的多插件市場清單。它列出全部七個插件的名稱與來源；某個插件目錄沒出現在裡面，市場就會把它藏起來。
- 每個插件的 `.cursor-plugin/plugin.json` 補上 Cursor 額外要求的欄位：圖示路徑與元件路徑。
- `mcp.json` 遵循 Agent Plugins 的 MCP schema，它對伺服器條目只收 `type`、`url`、`headers`。所以 `fosun-wealth-star-ai` 只寫位址，別的一律不寫。
- 每個 `skills/<名稱>/SKILL.md` 遵循 [Agent Skills 規範](https://agentskills.io/specification)。frontmatter 只放 `name`、`description`、`license`、`allowed-tools`、`metadata`、`compatibility`，`metadata` 裡只放字串。

## 校驗這個倉庫

```bash
bash scripts/check.sh
```

腳本按官方 JSON Schema 校驗每一份清單，用官方技能校驗器跑七個技能，再掃一遍密鑰、建置產物與只給宿主看的說明。它印出 `PASS`，或者直接點名要改哪幾行。

## 安全

- 所有密鑰都留在倉庫外面：宿主密鑰庫，或者安裝腳本寫的那個檔案。倉庫裡只有範本。
- `fosun-wealth-star-ai` 用 OAuth 2.1 加 PKCE 對接我們自己的授權伺服器。倉庫裡不存客戶端密鑰、API key 或票據。
- 研究類技能不下單。本倉庫的任何內容都不構成投資建議。
- `fw-trade-skill` 在下單、改單、撤單前必須拿到明確確認，第一次實盤下單前會展示風險提示。

## 授權

Apache-2.0。見 [LICENSE](../LICENSE) 與 [NOTICE](../NOTICE)。
