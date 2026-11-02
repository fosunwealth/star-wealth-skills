---
name: nl-echarts
description: Chart runtime embedded in fw-deep-research. The parent fills chart_contracts and calls render-echarts.mjs. Do not install this as its own skill.
---

# nl-echarts (embedded)

The filename must stay `subSKILL.md`. Do not add `SKILL.md` here.

Chart titles are English. The contract is `categories` / `series` / `ohlc` / `unit` / `decimals` / `title` / `caption`. Parent `--render-all` calls `render-echarts.mjs` in this directory with `--format html`. A slug outside `suggested_chart_slugs` is not rendered. No JS `function` inside an option. No SVG, `show_widget`, or CDN. HTML stays local: `script src="./echarts.min.js"`.
