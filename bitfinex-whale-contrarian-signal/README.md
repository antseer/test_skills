<div align="center">

# Bitfinex Whale Contrarian Signal

Monitor Bitfinex margin long positions for extreme changes and generate contrarian trading signals for BTC

[![X](https://img.shields.io/badge/Follow-%40Antseer__ai-black?logo=x&logoColor=white)](https://x.com/Antseer_ai) [![Telegram](https://img.shields.io/badge/Telegram-AntseerGroup-2CA5E0?logo=telegram&logoColor=white)](https://t.me/AntseerGroup) [![GitHub](https://img.shields.io/badge/GitHub-antseer--dev-181717?logo=github&logoColor=white)](https://github.com/antseer-dev/OpenWeb3Data_MCP) [![Medium](https://img.shields.io/badge/Medium-antseer-000000?logo=medium&logoColor=white)](https://medium.com/@antseer/)

English | [简体中文](README.zh.md)

</div>

## What Does This Tool Do?

When Bitfinex whales dramatically increase their margin long positions (buying aggressively on leverage), history shows BTC tends to drop afterward. When they rapidly cut positions (taking profit), BTC tends to rise. This tool monitors those extreme position changes and alerts you to contrarian trading opportunities.

How it works:

1. **Fetches Bitfinex margin long data** -- pulls historical margin long positions from Bitfinex's public API (free, no API key needed)
2. **Calculates 30-day position change rate** -- measures how much the total margin long position has changed over the past 30 days
3. **Identifies extreme signals** -- flags when the change exceeds +15% (whales buying = bearish contrarian) or drops below -10% (whales selling = bullish contrarian)
4. **Backtests and validates** -- computes historical win rates and average returns for each signal type, including out-of-sample validation
5. **Outputs a structured report** -- signal status, historical statistics, and actionable recommendations in under 300 words

Data sources: Bitfinex public API for margin positions, Antseer MCP (`ant_spot_market_structure`, `ant_futures_market_structure`) for BTC price and supplementary data.

Methodology credit: [@leifuchen](https://x.com/leifuchen/status/2041145516637966508), who conducted a systematic quantitative study covering 1,838 days (2021-03 to 2026-04) and discovered that extreme Bitfinex margin position changes are reliable contrarian indicators.

## Usage

```
/bitfinex-whale-contrarian-signal
```

or with parameters:

```
/bitfinex-whale-contrarian-signal BTC --lookback_days=30 --threshold_long=15 --threshold_short=10
```

**Parameters:**

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| symbol | No | Target asset (only BTC supported) | BTC |
| lookback_days | No | Days to calculate position change rate | 30 |
| threshold_long | No | Bullish position change % that triggers bearish signal | 15 |
| threshold_short | No | Bearish position change % (absolute) that triggers bullish signal | 10 |
| forward_window | No | Observation windows after signal trigger | 7d,14d,30d |
| data_start_date | No | Start date for analysis | Earliest available |

## Sample Output

```
===== Bitfinex Whale Contrarian Signal =====
Analysis Time: 2026-04-04
Data Range: 2021-03-24 ~ 2026-04-04 (1838 days)

[Current Status]
  30-Day Position Change: +18.3%
  Signal Status: TRIGGERED -- Bearish Contrarian (Short Signal)
  Signal Strength: Strong (exceeds threshold by 3.3 percentage points)

[Historical Stats (BTC performance after position surge >15%)]
  | Window | Avg Return | Win Rate (Short) | Samples |
  |--------|------------|------------------|---------|
  | 7 day  | -2.1%      | 58%              | 23      |
  | 14 day | -3.8%      | 65%              | 23      |
  | 30 day | -5.4%      | 69%              | 23      |

  Out-of-Sample (2024-2026):
  | Window | Avg Return | Win Rate (Short) | Samples |
  |--------|------------|------------------|---------|
  | 30 day | -3.8%      | 69%              | 11      |

[Recommendation]
  Whales are aggressively adding margin longs. Historically, BTC
  drops an average of 5.4% within 30 days after such signals.
  Consider shorting or reducing long exposure. 30-day short
  win rate: 69%.

[Caution]
  - Signal triggers fewer than 5 times per year on average
  - Limited sample size (23 events over 5 years)
  - Not investment advice; combine with other indicators
```

## When to Use / When Not to Use

**Good fit:**

- You trade BTC futures or spot and want an additional confirmation signal before entering positions
- You want to know when Bitfinex whales are making extreme moves (either accumulating or dumping)
- You run a daily or weekly checkup on BTC market structure and want whale positioning as one data point
- You are a quant researcher validating contrarian signals against Bitfinex margin data

**Not a good fit:**

- You need real-time, sub-hourly signals -- this tool analyzes 30-day rolling changes, not intraday moves
- You trade altcoins -- the research behind this tool only covers BTC; extending to other assets is not validated
- You want a standalone trading strategy -- this signal fires fewer than 5 times per year and should only be used as supplementary confirmation
- You expect precise price targets or entry/exit points -- this tool gives directional probability, not price levels

## Installation

### 1. Install the Skill

Copy the `bitfinex-whale-contrarian-signal` directory into your Claude Code skills directory:

```bash
# macOS / Linux
cp -r bitfinex-whale-contrarian-signal ~/.claude/skills/

# Verify
ls ~/.claude/skills/bitfinex-whale-contrarian-signal/SKILL.md
```

### 2. MCP Dependencies

This skill uses Antseer MCP for BTC price data and supplementary market structure data. Configure the MCP server in your Claude Code settings:

**Claude Desktop (`claude_desktop_config.json`):**

```json
{
  "mcpServers": {
    "antseer-mcp": {
      "command": "npx",
      "args": ["-y", "@anthropic/antseer-mcp"],
      "env": {
        "ANTSEER_API_KEY": "your-api-key"
      }
    }
  }
}
```

**Claude Code (`.claude/settings.json`):**

```json
{
  "mcpServers": {
    "antseer-mcp": {
      "command": "npx",
      "args": ["-y", "@anthropic/antseer-mcp"],
      "env": {
        "ANTSEER_API_KEY": "your-api-key"
      }
    }
  }
}
```

### 3. External Data Source

The core data (Bitfinex margin long positions) comes from Bitfinex's free public API. No API key is required:

```
GET https://api-pub.bitfinex.com/v2/stats1/pos.size:1m:tBTCUSD:long/hist
```

The skill will call this API automatically. No additional setup needed.

## Disclaimer

This tool is for informational and research purposes only. It does not constitute investment advice.

- The analysis methodology is attributed to [@leifuchen](https://x.com/leifuchen/status/2041145516637966508). All intellectual credit belongs to the original author.
- Historical win rates and average returns are based on past data (2021-2026) and do not guarantee future performance.
- The signal fires fewer than 5 times per year with a limited sample size (~23 events). Statistical confidence is inherently constrained.
- Market structure may change over time (e.g., BTC ETF approval, institutional participation), which could alter the effectiveness of this signal.
- Always combine with other indicators and your own judgment. Never risk more than you can afford to lose.

---

<div align="center">

Built by [AntSeer](https://antseer.ai) · Powered by AI Agents

</div>
