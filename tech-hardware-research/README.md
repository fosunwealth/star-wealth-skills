# tech-hardware-research

One HTML research note for a tech-hardware name or vertical: supply chain, metrics, and traps. Objective only. No orders.

**中文名**：科技硬件行业研究

你问一句「半导体该怎么研究」，这个技能把六个科技硬件赛道的研究框架一次给全：产业链地图、核心跟踪指标、调研问题库、专家访谈不许问的清单，还有七个财务造假信号。

## What it does

This plugin is one Agent Skill. The model reads `skills/tech-hardware-research/SKILL.md` when your request matches, then runs the scripts that ship with it.

## Try it

- "How do I research semiconductors?"
- "Map the optical-module supply chain."
- "Set up a research workspace for TSMC."

## Setup

1. Install the plugin from your team marketplace. In Cursor open **Customize**; in Grok Bot open **Connect apps**.
2. Add the requirements below. Keep every key in the host secret store and out of this repository.
- `FINTRUST_API_KEY` in the host secret store. `FINTRUST_ENV_FILE` overrides the `.env` path.
3. Run the first-run install command the skill prints on its first turn.

## Host requirements

| Need | Required | Notes |
| --- | --- | --- |
| python3 | Yes | Runs the scripts under `skills/tech-hardware-research/`. |
| Network access to `fintrustskill.com` and `aiapi.fosunhanig.com` | Yes | Key check only. The framework itself ships in `references/`. |
| host `WebSearch` / `WebFetch` | No | Fills the public sources for a named vertical. The framework works without them. |

## Safety

Read-only research. The skill never places an order. Nothing here is investment advice.

## Layout

```text
tech-hardware-research/
├── plugin.json                 # Agent Plugins 1.0.0 manifest
├── .cursor-plugin/plugin.json  # Cursor manifest, adds the logo
├── assets/icon.png
├── README.md
└── skills/tech-hardware-research/
    └── SKILL.md                # plus scripts/ references/ assets/
```

## License

Apache-2.0. See [../LICENSE](../LICENSE) and [../NOTICE](../NOTICE).
