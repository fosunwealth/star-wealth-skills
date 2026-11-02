# Star Wealth (Fosun Wealth) Skill Marketplace

Six AI research and trading skills for Hong Kong and US markets, packaged as [Agent Plugins 1.0.0](https://agent-plugins.org). Cursor and Grok Bot load them without conversion.

**中文**：这个仓库装着复星财富（星财富）的六个投研与交易技能。每个技能都按 Agent Plugins 1.0.0 这个公开格式打包，Cursor 和 Grok Bot 都能直接加载。你从团队市场装上一个技能，用一句大白话提问，模型就按技能里写好的流程干活。

## Plugins

| Plugin | Version | What it does |
| --- | --- | --- |
| [biopharma-data-hub](./biopharma-data-hub/) | 1.1.5 | Public pipeline, approval, patent and literature pulls for one biopharma name, plus upstream tracking. |
| [biopharma-strategy](./biopharma-strategy/) | 1.1.5 | A four-step biopharma research note with a materiality filter. |
| [fw-deep-research](./fw-deep-research/) | 3.7.56 | One interactive HTML research report for a named Hong Kong or US stock. |
| [fw-trade-skill](./fw-trade-skill/) | 2.0.5 | Hong Kong and US equity orders on paper or live, after an explicit confirmation. |
| [hk-ipo-analysis](./hk-ipo-analysis/) | 4.12.17 | Hong Kong IPO list, or one HTML subscription report with a five-factor score and allotment tiers. |
| [tech-hardware-research](./tech-hardware-research/) | 2.5.3 | One HTML research note for a tech-hardware name or vertical: supply chain, metrics and traps. |

Five of the six are read-only research. `fw-trade-skill` is the only one that can send an order, and it sends nothing without an explicit yes.

## Install

### Cursor

1. Open **Dashboard → Plugins & MCPs** and add this repository as a team marketplace (**Add Marketplace → Import from Repo**).
2. Set **Marketplace Access** and **Plugin Installation**. Default Off keeps each member in control.
3. Members install a plugin from **Customize**.

### Grok Bot

1. Sign in to the Grok Bot desktop app with the same Cursor account.
2. Open **Connect apps** in the sidebar and install the plugins this team marketplace allows.
3. Add each key in the bot secret store (**Settings → Secrets**). Never paste a key into a chat.

### Local check before publishing

```bash
cp -R fw-deep-research ~/.cursor/plugins/local/fw-deep-research
```

Then run **Developer: Reload Window** in Cursor and enable the plugin under **Customize**. Copy the directory; a symlink is not loaded.

## First run

Each skill installs its own dependencies on the first turn that needs them.

| Skill | First-run install |
| --- | --- |
| the four REST-gateway skills | `python3 -m pip install -r requirements.txt` |
| `fw-deep-research` | `python3 -m pip install -r scripts/requirements.txt`, then `npm install` |
| `hk-ipo-analysis` | `npm install` |
| `fw-trade-skill` | `bash install.sh` |

Two skills read data through one Streamable HTTP MCP gateway: `https://aiapi.fosunhanig.com/ai-mcp-research/mcp`. Add it in your host when the host asks for MCP servers by URL. The other four skills call their gateway over HTTPS and need no MCP entry.

## Format

- Root `plugin.json` is the portable [Agent Plugins 1.0.0](https://agent-plugins.org/plugin-authors/manifest) manifest. The schema closes its fields to the ones it defines.
- `.cursor-plugin/marketplace.json` at the repository root is what Cursor reads to import a multi-plugin repository. It lists all six plugins by name and source, and every plugin folder must appear in it or the marketplace hides that plugin.
- Each plugin's `.cursor-plugin/plugin.json` adds what Cursor documents on top: the logo and the component paths.
- Each `skills/<name>/SKILL.md` follows the [Agent Skills specification](https://agentskills.io/specification). Frontmatter holds `name`, `description`, `license`, `allowed-tools`, `metadata` and `compatibility` only, and `metadata` holds plain string values.

## Validate this repository

```bash
bash scripts/check.sh
```

The script checks every manifest against the published JSON Schema, runs the official Agent Skills validator on all six skills, and scans for credential material, build output and host-only instructions. It prints `PASS`, or the exact lines to fix.

## Safety

- Every key stays outside this repository, in the host secret store or in a file the setup script writes. The repository ships templates only.
- The research skills place no orders. Nothing here is investment advice.
- `fw-trade-skill` needs an explicit confirmation before any order, change or cancel, and it shows a risk notice before the first live order.

## License

MIT. See [LICENSE](./LICENSE).
