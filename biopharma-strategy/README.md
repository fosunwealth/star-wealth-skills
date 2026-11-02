# biopharma-strategy

A four-step biopharma research note, or upstream tracking that keeps only material events. Objective only. No orders.

**中文名**：生物医药投研策略

你问一句「康方生物值不值得追」，这个技能用四步拆给你看：管线盘点看能力，审批催化剂看潜力，专利护城河看持续性，前沿文献看最新信号。它再加一道重大性过滤，只留真正影响股价的事件。

## What it does

This plugin is one Agent Skill. The model reads `skills/biopharma-strategy/SKILL.md` when your request matches, then runs the scripts that ship with it.

## Try it

- "Is Akeso worth chasing?"
- "Only show me the Akeso BD deals or approvals from recent weeks that actually matter."
- "Set up twice-daily catalyst tracking for Innovent."

## Setup

1. Install the plugin from your team marketplace. In Cursor open **Customize**; in Grok Bot open **Connect apps**.
2. Add the requirements below. Keep every key in the host secret store and out of this repository.
- `FINTRUST_API_KEY` in the host secret store. `FINTRUST_ENV_FILE` overrides the `.env` path.
3. Run the first-run install command the skill prints on its first turn.

## Host requirements

| Need | Required | Notes |
| --- | --- | --- |
| python3 | Yes | Runs the scripts under `skills/biopharma-strategy/`. |
| Network access to `fintrustskill.com` and `aiapi.fosunhanig.com` | Yes | Key check and the research gateway. |
| `http://aiapi.fosunhanig.com/ai-mcp-research/mcp` | No | The scripts call the REST gateway directly. Add the MCP server only if your host prefers tools over scripts. |

## Safety

Read-only research. The skill never places an order. Nothing here is investment advice.

## Layout

```text
biopharma-strategy/
├── plugin.json                 # Agent Plugins 1.0.0 manifest
├── .cursor-plugin/plugin.json  # Cursor manifest, adds the logo
├── assets/icon.png
├── README.md
└── skills/biopharma-strategy/
    └── SKILL.md                # plus scripts/ references/ assets/
```

## License

MIT. See [../LICENSE](../LICENSE).
