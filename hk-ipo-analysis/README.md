# hk-ipo-analysis

Hong Kong IPO list, or one HTML subscription report with a five-factor score and allotment tiers. Objective only. No orders.

**中文名**：港股新股 IPO 打新分析

这个技能给一份正在招股的港股新股名单，或者给一只新股算五因子评分和分档中签率，最后给你一份 HTML 打新报告。全程客观拆解，不喊单。

## What it does

This plugin is one Agent Skill. The model reads `skills/hk-ipo-analysis/SKILL.md` when your request matches, then runs the scripts that ship with it.

## Try it

- "Which Hong Kong IPOs are open for subscription right now?"
- "Is the hk06700 IPO worth subscribing to?"
- "Run the numbers on the MINIMAX IPO for me."

## Setup

1. Install the plugin from your team marketplace. In Cursor open **Customize**; in Grok Bot open **Connect apps**.
2. Add the requirements below. Keep every key in the host secret store and out of this repository.
- `FINTRUST_API_KEY` in the host secret store. `FINTRUST_ENV_FILE` overrides the `.env` path.
3. Run the first-run install command the skill prints on its first turn.

## Host requirements

| Need | Required | Notes |
| --- | --- | --- |
| python3 3.8+ | Yes | Runs `scripts/main.py` through `run.sh`. |
| node + npm (`npm install`) | Yes | Fetches echarts, which the report inlines. Run it once before the first render. |
| `https://aiapi.fosunhanig.com/ai-mcp-research/mcp` | Yes | The data gateway behind `ipo_list`, `market_snapshot`, `ipo_dify_report`, `deep_profile` and `news_catalysts`. |
| host `westock-data ipo` | No | Fills empty issue-date slots only. Empty slots stay empty and the report still renders. |

## Safety

Read-only research. The skill never places an order. Nothing here is investment advice.

## Layout

```text
hk-ipo-analysis/
├── plugin.json                 # Agent Plugins 1.0.0 manifest
├── .cursor-plugin/plugin.json  # Cursor manifest, adds the logo
├── assets/icon.png
├── README.md
└── skills/hk-ipo-analysis/
    └── SKILL.md                # plus scripts/ references/ assets/
```

## License

MIT. See [../LICENSE](../LICENSE).
