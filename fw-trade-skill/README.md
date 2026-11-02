# fw-trade-skill

Hong Kong and US equity orders on paper or live, after an explicit confirmation. One gateway. No research reports.

**中文名**：港美股智能交易

这个技能在港股和美股上走完下单全流程：先查账户、资金、持仓，再下单、改单、撤单，每一步都要你点头。它真的能下实盘单，所以第一次下实盘单之前它会给你看一段风险提示。

## What it does

This plugin is one Agent Skill. The model reads `skills/fw-trade-skill/SKILL.md` when your request matches, then runs the scripts that ship with it.

## Try it

- "Check my US paper account holdings and available cash."
- "Buy 1 share of AAPL in my paper account."
- "Cancel my open paper order for 00700."

## Setup

1. Install the plugin from your team marketplace. In Cursor open **Customize**; in Grok Bot open **Connect apps**.
2. Add the requirements below. Keep every key in the host secret store and out of this repository.
3. Run the first-run install command the skill prints on its first turn.

## Host requirements

| Need | Required | Notes |
| --- | --- | --- |
| python3 3.9+ | Yes | `install.sh` builds a pinned Python 3.13 virtual environment with `uv`. |
| `uv` | Yes | `install.sh` downloads it from `astral.sh` when it is missing and checks it against a SHA-256 recorded in the script. |
| `https://openapi.fosunxcz.com` | Yes | The only order and market gateway. No gateway means no order, change, cancel, account or quote. |
| a Star Wealth trading credential (`fosun.env`) | Yes | `fosun-env-setup` creates and repairs it. `FOSUN_ENV_PATH` sets the path. |

## Safety

This skill can place paper or live orders. It sends nothing without an explicit yes, and it shows a risk notice before the first live order.

## Layout

```text
fw-trade-skill/
├── plugin.json                 # Agent Plugins 1.0.0 manifest
├── .cursor-plugin/plugin.json  # Cursor manifest, adds the logo
├── assets/icon.png
├── README.md
└── skills/fw-trade-skill/
    └── SKILL.md                # plus scripts/ references/ assets/
```

## License

MIT. See [../LICENSE](../LICENSE).
