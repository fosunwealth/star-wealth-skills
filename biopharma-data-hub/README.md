# biopharma-data-hub

Public pipeline, approval, patent and literature pulls for one biopharma name, plus upstream tracking. Objective only. No orders.

**中文名**：生物医药专业投研数据源

你问一句「帮我看看康方生物」，这个技能就把全球临床管线、中美欧三地审批、专利护城河和前沿临床文献一次拉齐。它还往前追 BD 与审批的上游信号，这些信号比公告早几天到几周。全程只给客观拆解，不喊单。

## What it does

This plugin is one Agent Skill. The model reads `skills/biopharma-data-hub/SKILL.md` when your request matches, then runs the scripts that ship with it.

## Try it

- "Take a look at Akeso for me."
- "Using the Akeso tracking config, show me the latest approval or BD signals."
- "Pull the ClinicalTrials.gov, FDA and EMA records for zanubrutinib."

## Setup

1. Install the plugin from your team marketplace. In Cursor open **Customize**; in Grok Bot open **Connect apps**.
2. Add the requirements below. Keep every key in the host secret store and out of this repository.
- `FINTRUST_API_KEY` in the host secret store. `FINTRUST_ENV_FILE` overrides the `.env` path.
3. Run the first-run install command the skill prints on its first turn.

## Host requirements

| Need | Required | Notes |
| --- | --- | --- |
| python3 | Yes | Runs the scripts under `skills/biopharma-data-hub/`. |
| Network access to `fintrustskill.com` and `aiapi.fosunhanig.com` | Yes | Key check and the research gateway. |
| `http://aiapi.fosunhanig.com/ai-mcp-research/mcp` | No | The scripts call the REST gateway directly. Add the MCP server only if your host prefers tools over scripts. |

## Safety

Read-only research. The skill never places an order. Nothing here is investment advice.

## Layout

```text
biopharma-data-hub/
├── plugin.json                 # Agent Plugins 1.0.0 manifest
├── .cursor-plugin/plugin.json  # Cursor manifest, adds the logo
├── assets/icon.png
├── README.md
└── skills/biopharma-data-hub/
    └── SKILL.md                # plus scripts/ references/ assets/
```

## License

MIT. See [../LICENSE](../LICENSE).
