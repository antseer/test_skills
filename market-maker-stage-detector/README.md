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

> Real analysis of RAVE (RaveDAO) on BSC — April 2026.

```
🔴 RAVE | BSC | MCap $250.4M | FDV $26.0M
Stage: Pumping (PUMPING) | Confidence 75% (3/4)
Suggestion: Do not chase — only $137K liquidity, exit slippage will be severe.
```

### Risk Signals

| Level | Signal — Evidence |
|-------|-------------------|
| 🔴 HIGH | Extreme chip concentration — Top 4 addresses hold 80.2%, #3 and #4 share GnosisSafeProxyFactory |
| 🔴 HIGH | Fresh wallet with massive holdings — #4 wallet created yesterday (4/9), immediately received 11.3% of supply ($2.96M) |
| 🔴 HIGH | Liquidity-to-mcap mismatch — $137K LP vs $250M mcap, Vol/LP = 33.8x |
| 🔴 HIGH | Abnormal fresh wallet inflow — +$8.48M net inflow, possible wash trading or retail FOMO |
| 🟡 MED | Smart Money selling — Smart Trader net sold $26.7K |
| 🟡 MED | Bot-dominated trading — Vault Bot (0x238a) single address contributed $4.18M volume |

### Chip Distribution

| # | Address | Share | 24h Change | Notes |
|---|---------|-------|------------|-------|
| 1 | 0xf073..06fa | 36.7% | 0 | Funded from Binance Hot Wallet, 30d no movement |
| 2 | 0x2d81..ecab | 20.1% | 0 | Isolated wallet, 30d no movement |
| 3 | 0x6020..74b0 | 12.1% | 0 | Gnosis Safe, deployed 2025-12-04 |
| 4 | 0x0a1f..90d7 | 11.3% | +2.8M tokens | **Gnosis Safe, created yesterday (4/9)** |
| 5 | 0x73d8..46db | 8.9% | -247K | Binance DEX/CEX Trading Bot |

Top 4 combined: **80.2%**

Related wallets: #3 and #4 both created via GnosisSafeProxyFactory (0x4e1dcf) — likely same team, combined 23.4%.

### Fund Flow

| Group | Net Flow | Direction |
|-------|----------|-----------|
| Fresh Wallets | +$8,479,235 | 🟢 Massive inflow |
| Top PnL Traders | +$480,444 | 🟢 Buying |
| Smart Trader | -$26,685 | 🔴 Selling |
| Exchange | -$553,021 | 🔴 Outflow |

Fresh wallet surge of $8.48M is the standout signal — could be retail FOMO or maker-fabricated buy pressure. Smart Trader already exiting small positions.

### Signal Matching

```
✅ Price surged >20%: +239% in 24h
✅ Large order concentration: Vault Bot single address drove $4.18M volume
✅ Volume concentrated in specific hours: 6h volume $3.57M = 77% of 24h
❌ Turnover >30%: Actual 17.8%, below threshold
```

Pumping in progress — few addresses driving volume, chips not yet widely distributed. If holding, set stop-profit now; if not holding, chasing is high risk.

Additional warning: Smart Trader selling + 1h price already pulling back -3.5% — early signs of transition from pumping to distribution.

> Disclaimer: For reference only, not investment advice. Related wallet detection may have gaps — verify high-concentration entities manually.

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
