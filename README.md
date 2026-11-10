# Star Wealth (Fosun Wealth) Skill Marketplace

Seven AI research, trading and market-data plugins for Hong Kong and US markets, packaged as [Agent Plugins 1.0.0](https://agent-plugins.org). Cursor and Grok Bot load them without conversion.

**English** | [简体中文](docs/README.zh-CN.md) | [繁體中文](docs/README.zh-TW.md)

## Plugins

| Plugin | Version | What it does |
| --- | --- | --- |
| [biopharma-data-hub](./biopharma-data-hub/) | 1.1.6 | Public pipeline, approval, patent and literature pulls for one biopharma name, plus upstream tracking. |
| [biopharma-strategy](./biopharma-strategy/) | 1.1.6 | A four-step biopharma research note with a materiality filter. |
| [fosun-wealth-star-ai](./fosun-wealth-star-ai/) | 1.2.0 | Hong Kong, US and A-share quotes, K-lines, ETFs, IPO calendars and financial statements over one hosted connector. |
| [fw-deep-research](./fw-deep-research/) | 3.7.57 | One interactive HTML research report for a named Hong Kong or US stock. |
| [fw-trade-skill](./fw-trade-skill/) | 2.0.6 | Hong Kong and US equity orders on paper or live, after an explicit confirmation. |
| [hk-ipo-analysis](./hk-ipo-analysis/) | 4.12.18 | Hong Kong IPO list, or one HTML subscription report with a five-factor score and allotment tiers. |
| [tech-hardware-research](./tech-hardware-research/) | 2.5.4 | One HTML research note for a tech-hardware name or vertical: supply chain, metrics and traps. |

Five of the seven are read-only research that ships its own scripts. `fosun-wealth-star-ai` holds no market logic of its own: it ships ten read-only market tools plus `ask_star_ai`, which hands the whole request to Star AI and can reach positions and the trading flows behind that service's own per-order confirmation. `fw-trade-skill` places its own orders, and it sends nothing without an explicit yes.

`fosun-wealth-star-ai` works differently from the other six, so read its own README before changing it: it ships no scripts, only an MCP URL plus a skill. Its tools live on a server that is not in this repository. That is the same arrangement the Gmail connector uses — the host holds the connection, the plugin holds the instructions — and it is why installing the plugin never exposes server code.

## Install

### Cursor

1. Open **Dashboard → Plugins & MCPs** and add this repository as a team marketplace (**Add Marketplace → Import from Repo**).
2. Set **Marketplace Access** and **Plugin Installation**. Default Off keeps each member in control.
3. Members install a plugin from **Customize**.

### Grok Bot

1. Sign in to the Grok Bot desktop app with the same Cursor account.
2. Open **Connect apps** in the sidebar and install the plugins this team marketplace allows.
3. Add each key in the bot secret store (**Settings → Secrets**). Never paste a key into a chat.

`fosun-wealth-star-ai` needs no key. Its card shows **Authorize** instead: the browser opens our OAuth page, the member signs in with a mobile number and an SMS code, and the host stores the token.

## Local check before publishing

```bash
cp -R fw-deep-research ~/.cursor/plugins/local/fw-deep-research
```

Then run **Developer: Reload Window** in Cursor and enable the plugin under **Customize**. Copy the directory; a symlink is not loaded.

## First run

Each skill installs its own dependencies on the first turn that needs them.

| Plugin | First-run install |
| --- | --- |
| the four REST-gateway skills | `python3 -m pip install -r requirements.txt` |
| `fosun-wealth-star-ai` | none — the connector runs server-side |
| `fw-deep-research` | `python3 -m pip install -r scripts/requirements.txt`, then `npm install` |
| `hk-ipo-analysis` | `npm install` |
| `fw-trade-skill` | `bash install.sh` |

Two skills read data through one Streamable HTTP MCP gateway: `https://aiapi.fosunhanig.com/ai-mcp-research/mcp`. Add it in your host when the host asks for MCP servers by URL. The other four skills call their gateway over HTTPS and need no MCP entry.

`fosun-wealth-star-ai` is the only plugin that declares an MCP server itself, in its own `mcp.json`: `https://aiapi.fosunhanig.com/ai-fin-agent/mcp`. The host discovers its authorization server from the `WWW-Authenticate` challenge and registers itself over dynamic client registration, so nothing about OAuth is hard-coded in this repository.

## Format

- Root `plugin.json` is the portable [Agent Plugins 1.0.0](https://agent-plugins.org/plugin-authors/manifest) manifest. The schema closes its fields to the ones it defines.
- `.cursor-plugin/marketplace.json` at the repository root is what Cursor reads to import a multi-plugin repository. It lists all seven plugins by name and source, and every plugin folder must appear in it or the marketplace hides that plugin.
- Each plugin's `.cursor-plugin/plugin.json` adds what Cursor documents on top: the logo and the component paths.
- `mcp.json` follows the Agent Plugins MCP schema, which closes a server entry to `type`, `url` and `headers`. That is why `fosun-wealth-star-ai` declares the URL and nothing else.
- Each `skills/<name>/SKILL.md` follows the [Agent Skills specification](https://agentskills.io/specification). Frontmatter holds `name`, `description`, `license`, `allowed-tools`, `metadata` and `compatibility` only, and `metadata` holds plain string values.

## Validate this repository

```bash
bash scripts/check.sh
```

The script checks every manifest against the published JSON Schema, runs the official Agent Skills validator on all seven skills, and scans for credential material, build output and host-only instructions. It prints `PASS`, or the exact lines to fix.

## Safety

- Every key stays outside this repository, in the host secret store or in a file the setup script writes. The repository ships templates only.
- `fosun-wealth-star-ai` authenticates with OAuth 2.1 and PKCE against our own authorization server. No client secret, API key or token is stored here.
- The research skills place no orders. Nothing here is investment advice.
- `fw-trade-skill` needs an explicit confirmation before any order, change or cancel, and it shows a risk notice before the first live order.

## License

Apache-2.0. See [LICENSE](./LICENSE) and [NOTICE](./NOTICE).
