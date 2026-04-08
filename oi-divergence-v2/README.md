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
2. **Cross-validates manipulation** using 3 conditions (pass 2 of 3): huge price spike + top-50 futures volume + sudden K-line breakout after weeks of silence
3. **Detects OI divergence** at 5-minute granularity — price holds up but open interest is dropping, meaning the whale is closing longs while keeping the price propped up
4. **Generates short signals** with entry, stop-loss, take-profit levels and risk controls

| Capability | Description |
|------------|-------------|
| Auto Target Discovery | Scans entire Binance futures market — no manual coin input needed |
| 3-Condition Cross-Validation (2/3) | 24H gain >50% + Futures Vol Top 50 + Sudden pump pattern (pass 2 of 3) |
| 5-Min OI Divergence | Dual-layer detection: 30min rolling window + bar-by-bar analysis |
| Extreme Risk Control | Liquidation price = 10x entry price; first-wave signals warn 1/4 position + wide stop |

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
## Output Format

Strictly follow the format below. Output in two separate pushes. Do not add extra fields or modify the format.

### Push 1: Candidate Screening

When screening is complete, list all candidates that passed the filters:

OI Divergence Screening Complete

1. {SYMBOL}
24H Change: +{change}%
Futures Volume Rank: #{rank}
30D Avg Daily Volatility: {volatility}%
Filter: {N}/3 passed (Cond1✓ Cond2✓/✗ Cond3✓/✗)

List each candidate in descending order by price change. If no candidates found, skip this push.

### Push 2: Short Signal

Only output for candidates that pass OI divergence verification. One entry per symbol:

OI Divergence Short Signal:
- Contract: {SYMBOL}
- Entry Range: ${low} - ${high}
- Stop Loss: ${stop_loss}
- Take Profit: ${take_profit}
- Risk/Reward: {X}:1
- Liquidation Price: > ${liq_price} (10x entry price, guard against market maker squeeze)

⚠️ First-wave signal: this is the first divergence in the 8H window. Whale-manipulated coins may pump again — recommend 1/4 position + wide stop.

Note: {One paragraph highlighting key risks, including but not limited to: OI recovery trend, signal invalidation conditions, abnormal funding rate, etc.}

If no candidates pass OI divergence verification, do not output Push 2.
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
