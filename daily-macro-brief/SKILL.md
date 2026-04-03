---
name: "daily-macro-brief"
description: "Generate a structured daily macro brief for crypto markets. Use when the user says 'macro brief', 'daily macro', 'today macro', 'how is macro today', 'generate macro report', 'macro daily', or types /daily-macro-brief. Aggregates cross-asset data, crypto market structure, and macro indicators into a 5-section Risk-On/Off scored report."
---

## Overview

Aggregate crypto market structure data (via Antseer MCP), macro economic indicators, and cross-asset price signals into a structured 5-section daily macro brief with a Risk-On/Off score (0–10). Designed for daily use by crypto researchers, macro traders, fund managers, and KOLs.

## Demand Context

Source: @0xcryptowizard (https://x.com/0xcryptowizard/status/2030860218557677963)

The author built a daily macro briefing system that automatically pulls macro data, geopolitical news, and sell-side research each morning, then outputs a structured "Daily Macro Brief" using AI synthesis. This skill replicates and generalizes that methodology into a repeatable Claude workflow.

Method attribution: The 5-section analysis framework and Risk-On/Off scoring logic are derived from @0xcryptowizard's published sample brief (2026-03-08).

## Features (Data Inputs)

### Parameters

| Parameter | Type | Required | Default | Example |
|-----------|------|----------|---------|---------|
| date | string | No | Today (YYYY-MM-DD) | 2026-03-08 |
| focus_assets | array | No | ["BTC", "ETH"] | ["BTC", "ETH", "SOL"] |
| include_sections | array | No | All 5 sections | ["focus", "signals", "asset_implications"] |
| language | string | No | zh | zh / en |
| historical_compare | boolean | No | true | true / false |
| risk_score_enabled | boolean | No | true | true / false |

### MCP Data Sources (Antseer)

| Data | MCP Tool | query_type | Parameters |
|------|----------|------------|------------|
| CPI | ant_macro_economics | cpi | — |
| Federal Funds Rate | ant_macro_economics | federal_funds_rate | — |
| Fed Balance Sheet | ant_macro_economics | us_balance_sheet | — |
| BTC/ETH spot price | ant_spot_market_structure | simple_price | ids: ["bitcoin","ethereum"] |
| Gold token price | ant_precious_metal_tokens | simple_price | coin_id: "paxg" |
| BTC ETF flows | ant_etf_fund_flow | btc_etf_flow | — |
| ETH ETF flows | ant_etf_fund_flow | eth_etf_flow | — |
| BTC funding rate | ant_futures_market_structure | futures_funding_rate_latest | symbol: "BTC" |
| BTC open interest | ant_futures_market_structure | futures_oi_aggregated | symbol: "BTC" |
| BTC long/short ratio | ant_futures_market_structure | futures_long_short_ratio | symbol: "BTC" |
| Stablecoin market cap | ant_stablecoin | mcap | — |
| Market sentiment | ant_market_sentiment | coin_detail | coin: "bitcoin" |
| Smart money flows | ant_smart_money | netflows | chains |

### External Data Sources (No MCP — Use Web or User-Provided)

| Data | Source | Ticker |
|------|--------|--------|
| Crude oil price | Yahoo Finance | CL=F |
| S&P 500 index | Yahoo Finance | ^GSPC |
| US 10Y Treasury yield | FRED API | DGS10 |
| US 2Y Treasury yield | FRED API | DGS2 |
| VIX | Yahoo Finance | ^VIX |
| High yield credit spread | FRED API | BAMLH0A0HYM2 |
| Macro news feed | NewsAPI / The Block / Blockworks RSS | — |

When external data is unavailable, note the gap explicitly in the report and proceed with available data.

## Entry Conditions

Trigger this skill when the user:
- Says "生成宏观简报", "今天宏观怎么样", "macro brief", "daily macro", "宏观日报"
- Types `/daily-macro-brief` with or without a date argument
- Asks for a cross-asset macro overview or Risk-On/Off assessment

## Exit Conditions

The skill is complete when:
- All available MCP data has been collected (Steps 1–3)
- A best-effort attempt at external data has been made (Step 2)
- The final 5-section brief has been rendered in the user's requested language
- Risk-On/Off score (0–10) has been calculated and shown (if risk_score_enabled)

If data collection fails for any single source, log the gap, skip that data point, and continue.

## Action Specification

### Step 1: Collect Macro Economic Indicators

Call `ant_macro_economics` with query_type `cpi`, `federal_funds_rate`, and `us_balance_sheet` (if available).

For each indicator, compute the deviation from prior value and label direction: ↑ / ↓ / →.

Output an internal "macro snapshot" table before proceeding.

### Step 2: Collect Cross-Asset Prices

Call `ant_spot_market_structure` (simple_price for BTC and ETH) and `ant_precious_metal_tokens` (simple_price for PAXG as gold proxy).

For crude oil, S&P 500, VIX, and US Treasury yields: attempt to retrieve via web search or user-provided context. If unavailable, mark as "N/A — external data required" in the brief.

Calculate today's percentage change for each asset. Note whether BTC is moving in correlation or divergence with traditional risk assets.

### Step 3: Collect Crypto Market Structure

Call in sequence:
- `ant_futures_market_structure` — futures_funding_rate_latest (BTC)
- `ant_futures_market_structure` — futures_oi_aggregated (BTC)
- `ant_futures_market_structure` — futures_long_short_ratio (BTC)
- `ant_etf_fund_flow` — btc_etf_flow
- `ant_etf_fund_flow` — eth_etf_flow
- `ant_stablecoin` — mcap
- `ant_market_sentiment` — coin_detail (bitcoin)
- `ant_smart_money` — netflows

Interpret each signal:
- Funding rate above +0.01% per 8h = elevated long leverage
- ETF net inflow = institutional buying pressure
- Stablecoin supply increase = dry powder building (Risk-On signal)
- Smart money net outflow = cautionary signal

### Step 4: Aggregate News and Events (Best-Effort)

Identify the top 5 macro events of the day from available context (web search, user-provided links, or known data). For each event, label the transmission chain: event → asset class → directional impact → color code (red = Risk-Off, green = Risk-On).

If no news feed is available, use the data signals from Steps 1–3 to infer likely macro narratives and note that live news was not available.

### Step 5: Historical Analog Matching (Optional — runs if historical_compare = true)

Compare current macro state (inflation level, yield curve shape, VIX range, credit spread level) to known historical regimes. Use `ant_macro_economics` historical data where available; supplement with FRED data if accessible.

Identify the closest historical analog period. State similarity score as a percentage and cite 2–3 key price/spread data points from that period.

### Step 6: Generate Final Brief

Synthesize Steps 1–5 into the 5-section report format below.

Calculate Risk-On/Off score using this rubric:

| Signal | Risk-On (+) | Risk-Off (-) |
|--------|-------------|--------------|
| BTC price | Up | Down |
| Funding rate | Moderate positive | Negative or extreme positive |
| ETF flow | Net inflow | Net outflow |
| Stablecoin supply | Growing | Shrinking |
| Smart money | Net inflow | Net outflow |
| VIX | Below 20 | Above 25 |
| Credit spread | Tightening | Widening |
| Yield curve | Steepening | Inverting / flattening |

Sum positive signals (each worth +1.25), total out of 10. Round to one decimal place.

## Output Format

Render the report using this template exactly:

```
Daily Macro Brief | {DATE}
Risk Score: {X.X} / 10  [{LABEL}]
主导叙事: {ONE_SENTENCE_DOMINANT_NARRATIVE}

**今日焦点**
{2–3 sentences: core variable driving markets today + transmission path}

**关键事件**
1. {Event} → {Asset class} [Direction] {Color indicator}
2. {Event} → {Asset class} [Direction] {Color indicator}
3. {Event} → {Asset class} [Direction] {Color indicator}
4. {Event} → {Asset class} [Direction] {Color indicator}
5. {Event} → {Asset class} [Direction] {Color indicator}

**信号解读**
- {Signal name}: {1–2 sentence interpretation}
- {Signal name}: {1–2 sentence interpretation}
- {Signal name}: {1–2 sentence interpretation}

**历史类比**: {PERIOD} (相似度 {X}%)
- {2–3 key data points from that period}

**资产含义**
- 股票: {1–2 sentences on equity implication}
- 利率: {1–2 sentences on rates implication}
- 加密: {1–2 sentences on crypto implication}
- 大宗商品: {1–2 sentences on commodities if relevant}

---
数据时间戳: {GENERATED_AT}
数据来源: Antseer MCP + 外部补充数据
```

Risk Score labels:
- 8–10: 极度 Risk-On
- 6–7.9: Risk-On
- 4–5.9: 中性
- 2–3.9: Risk-Off
- 0–1.9: 极度 Risk-Off

If `language = en`, translate all section headers and narrative text to English while preserving the same structure.

If `historical_compare = false`, omit the 历史类比 section.

## Risk Parameters

- This skill provides an analytical framework, not trading advice. State this explicitly in every output.
- Do not invent price data. If a data source is unavailable, mark the field as "N/A" and note the dependency.
- Historical analogs are illustrative, not predictive. The similarity score is a heuristic, not a statistical guarantee.
- Risk-On/Off score is a composite signal, not a position sizing directive.
- Macro news quality depends entirely on the feed quality. Low-signal inputs produce low-signal outputs — note this limitation when news is limited.
- External data (crude oil, VIX, S&P 500, yields) may be stale by hours depending on retrieval method. Note data freshness in the output.

## 首次安装提示

```
目标用户：加密货币投研人员、宏观交易员、Fund Manager、Crypto KOL 内容创作者
使用场景：每日早晨（建议北京时间 07:00–08:00）生成跨资产宏观简报，辅助仓位决策与内容创作
如何使用：/daily-macro-brief 或 /daily-macro-brief 2026-03-08 focus_assets=BTC,ETH,SOL
```
