# BTC Bubble Index Bottom Monitor

## What This Skill Does

This skill calculates an approximate Bitcoin Bubble Index (0-100) by combining 6 dimensions of on-chain and market data, and identifies when Bitcoin enters a cyclical bottom zone.

When the composite index drops to or below 10, it signals that Bitcoin is in a bottom area with very limited downside -- a pattern that has held consistently since 2022.

## How to Use

**Trigger words:** 泡沫指数, bubble index, 底部检测, bottom detection, BTC底部, 比特币泡沫, 周期底部判断

**Usage modes:**
- Scheduled daily/weekly check (automated patrol)
- Event-driven trigger when BTC price drops significantly

**Input parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| asset | bitcoin | Target asset (currently BTC only) |
| bubble_threshold | 10 | Index threshold for bottom signal |
| lookback_days | 365 | Historical lookback period in days |
| ma_period | 200 | Moving average period for price deviation |
| alert_enabled | true | Send alerts when threshold is hit |

## Example Output

The skill produces a structured report with:
- Composite bubble index value (0-100)
- Signal level: bottom / undervalued / neutral / overvalued / bubble
- Per-dimension scores with weights
- Historical validation statistics (hit rate, average returns)
- Text assessment summarizing the findings

Signal levels:
- Index <= 10: Bottom signal (historically reliable since 2022)
- 10-30: Undervalued
- 30-70: Neutral
- 70-90: Overvalued
- >= 90: Bubble warning

## Data Sources

All data is sourced via Antseer MCP tools:

| Data | MCP Tool | query_type |
|------|----------|------------|
| BTC price | ant_spot_market_structure | simple_price |
| Market cap, volume | ant_spot_market_structure | coins_markets |
| MVRV ratio | ant_token_analytics | mvrv |
| NVT ratio | ant_token_analytics | nvt |
| Market sentiment | ant_market_sentiment | coin_detail |
| Exchange netflow | ant_fund_flow | exchange_netflow |
| Exchange reserve | ant_fund_flow | exchange_reserve |
| BTC ETF flow | ant_etf_fund_flow | btc_etf_flow |

## Limitations and Disclaimers

- This is an **approximate** reconstruction of the Bitcoin Bubble Index, not the exact original indicator referenced in the source tweet.
- On-chain metrics (MVRV, NVT) may have T+1 data delay.
- Historical validation sample is small (approximately 3-4 bottom signals since 2022), so statistical significance is limited.
- Dimension weights are empirically set and may need backtesting optimization.
- The bottom threshold may need upward adjustment over time as Bitcoin market cap grows (the index floor tends to rise each cycle).
- Only supports BTC; not applicable to altcoins.
- This is a mid-to-long cycle indicator, not suitable for short-term trading decisions.
- Black swan events (e.g., sudden regulatory changes) may temporarily invalidate historical patterns.
- **Not investment advice.**

## Source

Based on methodology from @monkeyjiang: https://x.com/monkeyjiang/status/2039295737066860605
