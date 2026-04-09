<div align="center">

# Market Maker Stage Detector

Detect which stage a token's market maker is in using 6 on-chain signal dimensions — accumulation, pump, distribution, or exit.

[![X](https://img.shields.io/badge/Follow-%40Antseer__ai-black?logo=x&logoColor=white)](https://x.com/Antseer_ai) [![Telegram](https://img.shields.io/badge/Telegram-AntseerGroup-2CA5E0?logo=telegram&logoColor=white)](https://t.me/AntseerGroup) [![GitHub](https://img.shields.io/badge/GitHub-antseer--dev-181717?logo=github&logoColor=white)](https://github.com/antseer-dev/OpenWeb3Data_MCP) [![Medium](https://img.shields.io/badge/Medium-antseer-000000?logo=medium&logoColor=white)](https://medium.com/@antseer/)

English | [简体中文](README.zh.md)

</div>

## What Does This Tool Do?

When you find a new token and want to know if there's a market maker behind it, and more importantly, what stage they're in, this tool helps you figure it out in minutes.

It analyzes 6 on-chain dimensions:

| Dimension | What It Checks |
|-----------|---------------|
| Chip Concentration | Are a few entities controlling most of the supply? |
| Volume Authenticity | Is the trading volume real or wash-traded? |
| Turnover & Timing | Is volume distributed normally or concentrated in bursts? |
| Large Order Ratio | Are a few big trades driving all the volume? |
| Fund Flow | Are smart money and whales buying or selling? |
| Stage Verdict | Combining all signals to determine: Accumulating, Pumping, Distributing, or Dumped |

Data comes from Antseer's on-chain MCP tools, covering holder analysis, DEX trades, wallet profiling, and smart money tracking.

## Usage

Tell your AI Agent:

```
/market-maker-stage-detector 0x9234e981e395dA3BE7b00B035163571698f8f756 --chain bsc
```

### Parameters

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| `token_address` | Yes | Token contract address or name | — |
| `--chain` | No | Chain name (ethereum / bsc / solana / base / arbitrum) | `ethereum` |

### More Examples

```
/market-maker-stage-detector WALK --chain bsc
/market-maker-stage-detector 0x1234...abcd --chain solana
/market-maker-stage-detector 0xdead...beef
```

## Sample Output

```
Token: WALK | Chain: BSC | MCap: $1.60M
Stage: DISTRIBUTING | Confidence: 72%
Signals: 4/6 matched

Key Findings:
- [HIGH] Chip concentration 78 — 40% in single Vault contract
- [HIGH] Holders +22% but price -5.2% — chips being distributed
- [MED] Vol/Holder $192 (peer median $85) — elevated volume

Suggestion: Do not chase. Consider reducing positions.

Full report: output/mm-report-WALK.html
```

The HTML report includes interactive Chart.js visualizations for all 6 indicators.

## When to Use / When Not to Use

### Suitable

- Pre-buy risk check on any DEX-traded token
- Periodic monitoring of tokens you hold
- Quick diagnosis when a token shows abnormal volume spikes
- Comparing chip structure across multiple tokens

### Not Suitable

- Large-cap tokens like BTC/ETH (designed for small/mid-cap DEX tokens)
- Real-time trading signals (analysis granularity is hourly/daily)
- LP lock detection (requires external tools like DEXScreener)
- Funding wallet tracing (requires Arkham or Nansen)

## Installation

### Install Skill

**Claude Code (CLI)**
```bash
claude skill add antseer/market-maker-stage-detector
```

### Prerequisite: MCP Service

> **What is MCP?** MCP (Model Context Protocol) connects AI Agents to live data. Without MCP, the Agent can't fetch on-chain data and the analysis won't work.

This skill requires the Antseer MCP service:

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user ant-on-chain-mcp https://ant-on-chain-mcp.antseer.ai/mcp
```

**Cowork (Desktop App)**
Go to Settings > MCP Servers > Add:
- Name: `ant-on-chain-mcp`
- URL: `https://ant-on-chain-mcp.antseer.ai/mcp`
- Transport: `http`

After installation, **restart your Agent client** to activate MCP.

## Disclaimer

This tool analyzes historical data and statistical models. It **cannot predict future market movements** and its output is for reference only — **not investment advice**.

The analytical methodology is attributed to @agintender. This tool only integrates and presents it. Users should make independent decisions based on their own judgment and risk tolerance.

---

<div align="center">

Built by [AntSeer](https://antseer.ai) · Powered by AI Agents

</div>
