<div align="center">

# Narrative-Driven Token Discovery

Scan on-chain tokens matching social media narrative hotspots, assess lifecycle stage, and generate trading signals.

[![X](https://img.shields.io/badge/Follow-%40Antseer__ai-black?logo=x&logoColor=white)](https://x.com/Antseer_ai) [![Telegram](https://img.shields.io/badge/Telegram-AntseerGroup-2CA5E0?logo=telegram&logoColor=white)](https://t.me/AntseerGroup) [![GitHub](https://img.shields.io/badge/GitHub-antseer--dev-181717?logo=github&logoColor=white)](https://github.com/antseer-dev/OpenWeb3Data_MCP) [![Medium](https://img.shields.io/badge/Medium-antseer-000000?logo=medium&logoColor=white)](https://medium.com/@antseer/)

English | [简体中文](README.zh.md)

</div>

## What Does This Tool Do?

When a trending topic explodes on social media — say "Trump declassifies UFO files" or "Elon tweets about DOGE" — MEME traders race to find on-chain tokens that match the narrative. This tool automates that discovery process.

Here is how it works:

1. **Validate the narrative** — Check whether your keyword is actually trending on social media and how hot it is (rising, stable, or declining).
2. **Scan for matching tokens** — Search on-chain token pairs whose name or symbol matches your keyword, filter by minimum liquidity, and cross-reference with trending token lists.
3. **Assess token fundamentals** — For each candidate, check holder concentration (are the top 10 wallets holding 80%+?), DEX trading activity, and token age.
4. **Cross-verify with Smart Money** — Check if known Smart Money wallets have already bought in. Smart Money entry + rising social buzz = high confidence signal.
5. **Determine lifecycle stage** — Combine social trend, price action, and volume to classify the narrative as emerging, exploding, peaking, or fading.
6. **Output signal report** — Deliver a composite score (0-100) and action recommendation (enter / watch / avoid) for each matched token.

Data sources: AntSeer MCP tools (`ant_market_sentiment`, `ant_meme`, `ant_token_analytics`, `ant_smart_money`).

Methodology attribution: @thecryptoskanda (analysis) and @Clukz (original trading method).

## Usage

```
/narrative-driven-token-discovery Aliens
```

**Parameters:**

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| narrative_keyword | Yes | Trending narrative keyword (English or Chinese) | -- |
| chain | No | Target blockchain | solana |
| time_window | No | Social heat evaluation window | 24h |
| min_liquidity_usd | No | Minimum liquidity filter (USD) | 10000 |
| min_social_score | No | Minimum social heat score threshold | -- |
| top_n | No | Max number of matched tokens to return | 10 |

**More examples:**

```
/narrative-driven-token-discovery DOGE
/narrative-driven-token-discovery UFO --chain=solana --top_n=5
/narrative-driven-token-discovery Iran --time_window=4h --min_liquidity_usd=50000
```

## Sample Output

```
=== Narrative-Driven Token Discovery Report ===
Narrative Keyword: Aliens / UFO
Narrative Heat: 78/100 (rising)
Lifecycle Stage: exploding

| Token    | Chain  | Price  | Liquidity | Age  | SM Status   | Score | Signal   |
|----------|--------|--------|-----------|------|-------------|-------|----------|
| ALIENS   | Solana | $0.012 | $85,000   | 2h   | entered     | 82    | strong   |
| UFO      | Solana | $0.003 | $32,000   | 45m  | not_entered | 58    | moderate |
| XFILES   | Solana | $0.001 | $8,000    | 15m  | not_entered | 35    | weak     |

ALIENS — Consider entry.
  Narrative in explosion phase + Smart Money entered + sufficient liquidity.
  Caution: token age only 2h, extreme volatility expected.

UFO — Watch and wait.
  High narrative match but no Smart Money entry, moderate liquidity.

XFILES — Avoid.
  Liquidity below $10,000 threshold. No Smart Money validation.

Disclaimer: This analysis is auto-generated from on-chain data and social signals.
Not investment advice. MEME tokens carry extreme risk and may go to zero.
Methodology by @thecryptoskanda / @Clukz.
```

## When to Use / When Not to Use

**Good fit:**
- A breaking news headline just dropped and you want to know if there are matching tokens on-chain
- You spotted a trending topic on Twitter/X and want a quick multi-dimensional assessment before trading
- You want to check whether Smart Money has already entered a narrative-related token
- You need to determine if a narrative is still in its early stage or already fading

**Not a good fit:**
- You need real-time push notifications for new tokens (this tool is query-based, not a live feed)
- You want to execute trades automatically (this tool only produces signals, no exchange integration)
- You are looking for precise price targets or stop-loss levels
- The narrative is in a non-English language that may not be well covered by the social data source (LunarCrush)
- The token you are interested in is extremely new (< 5 minutes old) and may not yet be indexed

## Installation

### Skill Installation

Add this skill to your Claude Code environment:

```bash
claude skill add narrative-driven-token-discovery
```

### MCP Dependencies

This skill requires the following AntSeer MCP services for real-time data access.

#### antseer-sentiment (Social Sentiment Data)

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user antseer-sentiment https://mcp.antseer.com/sentiment
```

**OpenClaw / Claw**

In settings, add an MCP server:
- Name: `antseer-sentiment`
- URL: `https://mcp.antseer.com/sentiment`
- Transport: `http`

**OpenCode**

Add to `opencode.json`:
```json
{
  "mcpServers": {
    "antseer-sentiment": {
      "type": "http",
      "url": "https://mcp.antseer.com/sentiment"
    }
  }
}
```

#### antseer-meme (MEME Token Data)

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user antseer-meme https://mcp.antseer.com/meme
```

**OpenClaw / Claw**

In settings, add an MCP server:
- Name: `antseer-meme`
- URL: `https://mcp.antseer.com/meme`
- Transport: `http`

**OpenCode**

Add to `opencode.json`:
```json
{
  "mcpServers": {
    "antseer-meme": {
      "type": "http",
      "url": "https://mcp.antseer.com/meme"
    }
  }
}
```

#### antseer-token-analytics (Token On-Chain Analytics)

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user antseer-token-analytics https://mcp.antseer.com/token-analytics
```

**OpenClaw / Claw**

In settings, add an MCP server:
- Name: `antseer-token-analytics`
- URL: `https://mcp.antseer.com/token-analytics`
- Transport: `http`

**OpenCode**

Add to `opencode.json`:
```json
{
  "mcpServers": {
    "antseer-token-analytics": {
      "type": "http",
      "url": "https://mcp.antseer.com/token-analytics"
    }
  }
}
```

#### antseer-smart-money (Smart Money Tracking)

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user antseer-smart-money https://mcp.antseer.com/smart-money
```

**OpenClaw / Claw**

In settings, add an MCP server:
- Name: `antseer-smart-money`
- URL: `https://mcp.antseer.com/smart-money`
- Transport: `http`

**OpenCode**

Add to `opencode.json`:
```json
{
  "mcpServers": {
    "antseer-smart-money": {
      "type": "http",
      "url": "https://mcp.antseer.com/smart-money"
    }
  }
}
```

**General MCP Clients**

Any MCP-compatible client can connect. Core endpoints:
- Sentiment: `https://mcp.antseer.com/sentiment`
- MEME: `https://mcp.antseer.com/meme`
- Token Analytics: `https://mcp.antseer.com/token-analytics`
- Smart Money: `https://mcp.antseer.com/smart-money`
- Transport: `http`
- Scope: `user` (recommended, shared across projects)

After installation, **restart your agent client** to activate the MCP services.

## Disclaimer

- This skill is built on the trading methodology publicly shared by @thecryptoskanda (analysis) and @Clukz (original method). All methodology credit belongs to the original authors.
- Analysis results are generated from historical on-chain data and social signals. They cannot predict future market movements.
- This does not constitute investment advice. Trading decisions should incorporate your own risk tolerance and fundamental analysis.
- MEME tokens are extremely high-risk assets that can lose 100% of their value. Never invest more than you can afford to lose.
- Token search is text-based (name/symbol matching) and may miss tokens that are thematically related but do not contain the keyword in their name.

---

<div align="center">

Built by [AntSeer](https://antseer.ai) · Powered by AI Agents

</div>
