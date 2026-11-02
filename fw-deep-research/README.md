# fw-deep-research

One interactive HTML research report for a named Hong Kong or US stock: business, valuation, financials, and catalysts. Objective only. No orders.

**中文名**：港美股专业投研分析

你给这个技能一只港股或美股，它产出一份带图表的 HTML 深度研报：生意模式、估值、财报、机构资金、催化剂。所有数字都要答一句「所以呢」，全程不喊单。

## What it does

This plugin is one Agent Skill. The model reads `skills/fw-deep-research/SKILL.md` when your request matches, then runs the scripts that ship with it.

## Try it

- "Take a look at NVIDIA for me."
- "Can I buy NVIDIA?"
- "Write a deep research report on Tencent (00700)."

## Setup

1. Install the plugin from your team marketplace. In Cursor open **Customize**; in Grok Bot open **Connect apps**.
2. Add the requirements below. Keep every key in the host secret store and out of this repository.
- `FINTRUST_API_KEY` in the host secret store. `FINTRUST_PRESENT_DIR` sets where the finished HTML lands.
3. Run the first-run install command the skill prints on its first turn.

## Host requirements

| Need | Required | Notes |
| --- | --- | --- |
| python3 + `pip install -r scripts/requirements.txt` | Yes | Runs the pipeline in `scripts/`. |
| node + npm (`npm install`) | Yes | Renders the charts inline. Without echarts the report cannot be built. |
| `https://aiapi.fosunhanig.com/ai-mcp-research/mcp` | Yes | The data gateway. Add it as a Streamable HTTP MCP server in your host. |
| host `westock-data` / `neodata` | No | They only fill facets the MCP left empty. A missing one thins those facets; the report still renders. |
| host `WebSearch` / `WebFetch` | No | Only for the last openable public sources. The report renders without them. |

## Safety

Read-only research. The skill never places an order. Nothing here is investment advice.

## Layout

```text
fw-deep-research/
├── plugin.json                 # Agent Plugins 1.0.0 manifest
├── .cursor-plugin/plugin.json  # Cursor manifest, adds the logo
├── assets/icon.png
├── README.md
└── skills/fw-deep-research/
    └── SKILL.md                # plus scripts/ references/ assets/
```

## License

MIT. See [../LICENSE](../LICENSE).
