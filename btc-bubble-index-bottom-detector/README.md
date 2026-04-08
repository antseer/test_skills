<div align="center">

# BTC Bubble Index Bottom Detector

BTC Bottom Detector — use on-chain MVRV+NVT data to identify when Bitcoin enters a historical bottom zone

[![X](https://img.shields.io/badge/Follow-%40Antseer__ai-black?logo=x&logoColor=white)](https://x.com/Antseer_ai) [![Telegram](https://img.shields.io/badge/Telegram-AntseerGroup-2CA5E0?logo=telegram&logoColor=white)](https://t.me/AntseerGroup) [![GitHub](https://img.shields.io/badge/GitHub-antseer--dev-181717?logo=github&logoColor=white)](https://github.com/antseer-dev/OpenWeb3Data_MCP) [![Medium](https://img.shields.io/badge/Medium-antseer-000000?logo=medium&logoColor=white)](https://medium.com/@antseer/)

English | [简体中文](README.zh.md)

</div>

---

## What Does This Tool Do?

When you are trying to decide whether Bitcoin has bottomed out after a major drawdown, this tool helps you answer that question by computing a composite "bubble proxy index" from on-chain data and comparing it against historical bottom thresholds.

How it works in three steps:
1. Fetch BTC price, MVRV (Market Value to Realized Value ratio), and NVT (Network Value to Transactions ratio) from Antseer MCP
2. Normalize each indicator over a configurable lookback window and combine them into a single 0-100 Bubble Proxy Index
3. Compare the current index value against the bottom threshold, scan historical signals, and output a structured bottom-detection report

Data sources: Antseer MCP (`ant_spot_market_structure`, `ant_token_analytics`)

The methodology is credited to @monkeyjiang, who observed that a proprietary "Bitcoin Bubble Index" near 10 has coincided with every BTC price bottom since 2022. This skill approximates that signal using publicly available on-chain metrics.

---

## Usage

```
/btc-bubble-index-bottom-detector [symbol] [--bottom_threshold=N] [--lookback_days=N] [--price_target=N] [--include_chart_context=true]
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| symbol | yes | BTC | Asset to analyze (BTC only in this version) |
| bottom_threshold | no | 12 | Upper bound of the "bottom zone" on the 0-100 index |
| lookback_days | no | 1460 | Historical window for normalization (4 years) |
| price_target | no | — | Forward price target in USD; enables risk-reward calculation |
| include_chart_context | no | true | Include textual description of index trend |

**Examples:**

```
/btc-bubble-index-bottom-detector BTC
/btc-bubble-index-bottom-detector BTC --bottom_threshold=10
/btc-bubble-index-bottom-detector BTC --price_target=200000
```

---

## Sample Output

```
=== BTC Bubble Proxy Index — Bottom Detection Report ===

Asset: BTC  |  Analysis Date: 2026-04-08
Current Price: $62,000
Bubble Proxy Index: 9.8 / 100  (threshold: 12)

Signal: Strong Bottom Signal
Signal Strength: 82/100
Index Trend: confirmed  (30-day change: +1.2)

--- Historical Validation (4-year lookback) ---
Signals Found: 3
Avg Return  90d: +47.3%
Avg Return 365d: +198.6%
Median Max Drawdown After Entry: 18.2%

--- Component Scores ---
MVRV (60%): 8/100   [current MVRV: 0.91]
NVT  (40%): 12/100  [current NVT:  28.4]

--- Risk-Reward Analysis (target: $200,000) ---
Potential Upside: +222.6%
Risk-Reward Ratio: 12.2:1
Historical Avg Max Drawdown: 18.2%

Note: This index is a MVRV+NVT proxy, not the original monkeyjiang bubble index.
Methodology credit: @monkeyjiang. Not investment advice.
```

---

## When to Use / When Not to Use

**Good fit:**
- After a 20%+ BTC price drop — want to know if on-chain metrics confirm a bottom
- Periodic cycle monitoring — checking whether BTC is entering accumulation territory
- Building a medium-to-long-term position and need an on-chain confirmation signal
- Validating a buy thesis before sizing in

**Not a good fit:**
- Short-term trading (days or hours) — MVRV and NVT are weekly/monthly cycle indicators, not intraday signals
- Altcoin analysis — data quality for MVRV/NVT is lower for non-BTC assets
- Expecting a precise bottom price — this tool identifies a zone, not a specific price level
- Real-time alerts requiring sub-minute latency — on-chain data typically has T+1 lag

---

## Installation

### Install the Skill

Add this skill to your Claude Code environment. If you are using Claude Code with the AntSeer skill harness:

```bash
# Clone or copy the skill directory into your skills folder
cp -r btc-bubble-index-bottom-detector ~/.claude/skills/
```

### Install AntSeer MCP (Required)

This skill requires the AntSeer OpenWeb3Data MCP server to fetch on-chain data.

**Claude Desktop (`claude_desktop_config.json`):**

```json
{
  "mcpServers": {
    "antseer": {
      "command": "npx",
      "args": ["-y", "@antseer/openweb3data-mcp"]
    }
  }
}
```

**Claude Code (`settings.json`):**

```json
{
  "mcpServers": {
    "antseer": {
      "command": "npx",
      "args": ["-y", "@antseer/openweb3data-mcp"]
    }
  }
}
```

For other MCP-compatible clients, refer to the [AntSeer MCP GitHub](https://github.com/antseer-dev/OpenWeb3Data_MCP) for platform-specific installation instructions.

---

## Disclaimer

This tool is for informational purposes only and does not constitute investment advice. Analysis is based on on-chain metrics (MVRV, NVT) as proxies for the original "Bitcoin Bubble Index" referenced by @monkeyjiang; the proxy may deviate from the original indicator. Historical signals are based on only 3-4 events since 2021 — sample size is small and statistical significance is limited. Past performance does not predict future results. The methodology and framework are attributed to @monkeyjiang; AntSeer does not claim ownership of the original concept. Always conduct your own research before making investment decisions.

---

<div align="center">

Built by [AntSeer](https://antseer.ai) · Powered by AI Agents

</div>
