<div align="center">

# OI Divergence Short Sniper

Auto-discover whale-manipulated coins and snipe short entries with 5-minute OI divergence detection

[![X](https://img.shields.io/badge/Follow-%40Antseer__ai-black?logo=x&logoColor=white)](https://x.com/Antseer_ai) [![Telegram](https://img.shields.io/badge/Telegram-AntseerGroup-2CA5E0?logo=telegram&logoColor=white)](https://t.me/AntseerGroup) [![GitHub](https://img.shields.io/badge/GitHub-antseer--dev-181717?logo=github&logoColor=white)](https://github.com/antseer-dev/OpenWeb3Data_MCP) [![Medium](https://img.shields.io/badge/Medium-antseer-000000?logo=medium&logoColor=white)](https://medium.com/@antseer/)

English | [简体中文](README.zh.md)

</div>

---

## What Does This Tool Do?

When a small-cap coin suddenly pumps 50%+ in a day, you want to know: is this real buying, or is a whale manipulating the price to dump on retail? This tool automatically finds those setups and tells you when the whale starts exiting.

How it works:

1. **Scans Binance futures** for coins that pumped 50%+ in 24 hours
2. **Cross-validates manipulation** using 3 conditions: huge price spike + top-20 futures volume + sudden K-line breakout after weeks of silence
3. **Detects OI divergence** at 5-minute granularity — price holds up but open interest is dropping, meaning the whale is closing longs while keeping the price propped up
4. **Generates short signals** with entry, stop-loss, take-profit levels and risk controls

| Capability | Description |
|------------|-------------|
| Auto Target Discovery | Scans entire Binance futures market — no manual coin input needed |
| 3-Condition Cross-Validation | 24H gain >50% + Futures Vol Top 20 + Sudden pump pattern |
| 5-Min OI Divergence | Dual-layer detection: 30min rolling window + bar-by-bar analysis |
| Extreme Risk Control | Liquidation price set at 10x+ entry to survive whale counter-pumps |

## Usage

Send to your AI Agent:

```
/oi-divergence
```

No parameters needed. The tool automatically scans the entire market.

### Parameters

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| *(none)* | — | Fully automated, no input required | — |

The tool runs a complete pipeline: market scan → manipulation detection → OI divergence analysis → signal generation.

## Sample Output

```
## Whale-Manipulated Coin OI Divergence Short Sniper Report

Scan Time: 2026-04-06 14:30 UTC
Data Source: Binance (only)
Filter Results: 247 coins → 3 with 24H >50% → 2 confirmed futures-driven → 1 K-line pattern match → 1 OI divergence

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### TL;DR

⚠️ Found 1 whale-manipulation short signal:
1. **SIRENUSDT** (Strong divergence) — 24H +85%, Futures Vol Top 5, OI declining

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### Signal #1: SIRENUSDT — Strong Divergence

#### Target Profile
| Dimension | Data |
|-----------|------|
| 24H Gain | +85% |
| Futures 24H Vol Rank | #3 |
| Spot vs Futures Vol Ratio | 0.2:1 |
| 30D Avg Daily Volatility | 3.1% |
| Latest Daily Candle Gain | +62% |

#### OI Divergence Data
| Metric | 8H Ago | Current | Change |
|--------|--------|---------|--------|
| Price | $0.0042 | $0.0078 | +85.7% |
| OI | $18.2M | $14.1M | -22.5% |
| Funding Rate | 0.015% | 0.028% | — |

Divergence Strength: Strong
30min Window Divergences: 6 consecutive windows
5min Bar Divergences: 18 bars (quasi-continuous)
OI Cumulative Drop: -22.5%
Peak Boost: Yes (price at 8H high)

#### Short Suggestion

- Contract: SIRENUSDT
- Entry Zone: $0.0774 - $0.0782
- Stop Loss: $0.0081 (1.5% above 8H high)
- Take Profit 1: $0.0052 (24H low)
- Take Profit 2: $0.0068 (divergence start price)
- Risk/Reward: 3.2:1
- Liquidation Price: > $0.078 (controlled at 10x+ entry)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### Filtered Out Coins

| Coin | 24H Gain | Eliminated At | Reason |
|------|----------|---------------|--------|
| ALPACAUSDT | +55% | Condition 2 | Futures vol not in Top 20 |
| MOVEUSDT | +70% | Condition 3 | High 30D volatility, not a sudden pump |

### Risk Warning

- 5-minute level signals have short validity windows — act promptly
- Whales may pump again before dumping — wait for confirmation
- Liquidation at 10x+ entry is extreme risk control — keep position size minimal
- For educational purposes only, not investment advice
```

## When to Use / When Not to Use

### Good For

- Hunting short opportunities on pump-and-dump coins before the crash
- Screening the entire Binance futures market for whale manipulation signals
- Getting concrete entry/exit levels backed by quantitative OI analysis
- Daily scan routine — run once when you see unusual pumps on the leaderboard

### Not For

- Trading BTC/ETH or other large-cap coins (this tool focuses on manipulated small-caps)
- Real-time tick-by-tick execution (minimum analysis cycle is 5 minutes)
- Replacing a professional quant backtesting system (this is a signal scanner, not a backtester)
- Spot market analysis (this tool is exclusively for perpetual futures)

## Installation

### Install the Skill

**Claude Code (CLI)**
```bash
claude skill add antseer-dev/oi-divergence
```

**Cowork (Desktop App)**
Search for `oi-divergence` in the Cowork plugin marketplace and click Install.

**Manual Install**
Download the `.skill` file and import it in your Agent client.

### Prerequisites: MCP Service

> **What is MCP?** MCP (Model Context Protocol) is the protocol that connects AI Agents to data pipelines. Without the MCP service installed, the Agent cannot access real-time data, and analysis won't work.

This skill requires the following MCP service:

#### AntSeer On-Chain MCP

Choose the installation method for your Agent client:

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user ant-on-chain-mcp https://ant-on-chain-mcp.antseer.ai/mcp
```

**Cowork (Desktop App)**
Go to Settings → MCP Servers → Add:
- Name: `ant-on-chain-mcp`
- URL: `https://ant-on-chain-mcp.antseer.ai/mcp`
- Transport: `http`

**OpenClaw / Claw**
Add MCP server in settings:
- Name: `ant-on-chain-mcp`
- URL: `https://ant-on-chain-mcp.antseer.ai/mcp`
- Transport: `http`

**OpenCode**
Add to your `opencode.json` config:
```json
{
  "mcpServers": {
    "ant-on-chain-mcp": {
      "type": "http",
      "url": "https://ant-on-chain-mcp.antseer.ai/mcp"
    }
  }
}
```

**Any MCP-compatible Client**
- Endpoint: `https://ant-on-chain-mcp.antseer.ai/mcp`
- Transport: `http`
- Scope: `user` (recommended, shared across projects)

After installation, **restart your Agent client** to activate the MCP service.

## Disclaimer

This tool analyzes historical data and statistical models. It **cannot predict future market movements** and its output is for reference only — **not investment advice**.

All analytical methodologies and indicators are attributed to their original authors. This tool only integrates and presents them. Users should make independent decisions based on their own judgment and risk tolerance. By using this tool, you acknowledge these risks and accept full responsibility.

---

<div align="center">

Built by [AntSeer](https://antseer.ai) · Powered by AI Agents

</div>
