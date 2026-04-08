---
name: "btc-bubble-index-bottom-detector"
description: "Bitcoin bubble index bottom detector — analyzes MVRV and NVT on-chain metrics to build a composite bubble proxy index and detect whether BTC is in a historical bottom zone. Use when the user mentions BTC bottom signal, bubble index, bitcoin bottom detection, 比特币泡沫指数, 底部信号, BTC 是否见底, btc bubble index, bitcoin bottom signal, 泡沫指数分析, or asks if it is a good time to accumulate BTC."
metadata:
  generated_at: "2026-04-08 16:10:34"
---

## Overview

Read MVRV and NVT on-chain data via Antseer MCP, compute a 0-100 composite bubble proxy index, compare it against the configured bottom threshold, and output a structured bottom-detection report — including historical signal validation and optional risk-reward ratio calculation.

## Demand Context

Method source: @monkeyjiang's tweet (https://x.com/monkeyjiang/status/2039295737066860605). Core observation: Bitcoin's "bubble index" has touched approximately 10 at every BTC price bottom since 2022, with no false negatives in four years. A secondary observation: each successive bottom shows a slightly higher absolute index low, suggesting structural market maturation.

The original "bubble index" is a private/third-party metric. This Skill approximates it using MVRV + NVT, both available via Antseer MCP. Outputs are labeled "bubble proxy index" to distinguish from the original.

## Features (Data Inputs)

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| symbol | string | yes | Asset to analyze (currently BTC only) | BTC |
| bottom_threshold | float | no | Upper bound of the "bottom zone" on the 0-100 scale | 12 |
| lookback_days | int | no | Historical lookback window for normalization | 1460 (4 years) |
| price_target | float | no | User's forward price target in USD for risk-reward calculation | none |
| include_chart_context | bool | no | Include textual description of index trend and historical signals | true |

**MCP Data Sources:**

| Data Need | MCP Tool | query_type | Key Parameters |
|-----------|----------|------------|----------------|
| BTC current price | ant_spot_market_structure | simple_price | ids=bitcoin |
| BTC market cap / volume | ant_spot_market_structure | coins_markets | — |
| MVRV time series | ant_token_analytics | mvrv | asset=BTC |
| NVT time series | ant_token_analytics | nvt | asset=BTC |

## Entry Conditions

Trigger this Skill when any of the following apply:

1. User asks about BTC bubble index, bottom detection, or accumulation timing
2. User asks "is BTC at the bottom", "is now a good entry", "比特币底部信号", or similar
3. User wants to validate a buy thesis using on-chain valuation
4. User mentions "泡沫指数", "MVRV bottom", "NVT signal", or "btc bubble index"

## Exit Conditions

1. Bubble proxy index has been computed and a signal label has been assigned
2. Historical signal statistics have been summarized (or marked insufficient if fewer than 3 events)
3. Risk-reward section is included if `price_target` was provided, omitted otherwise
4. If any MCP data source is unavailable, note the gap and compute partial results from available data

## Action Specification

### Step 1: Fetch Current BTC Price and Market Data

Call `ant_spot_market_structure` with `query_type: simple_price, ids=bitcoin`. Record `current_price`.

Call `ant_spot_market_structure` with `query_type: coins_markets` to get `market_cap` and `volume_24h`.

### Step 2: Fetch MVRV and NVT Time Series

Call `ant_token_analytics` with `query_type: mvrv, asset=BTC`. Extract the current MVRV value and its historical series covering at least `lookback_days`.

Call `ant_token_analytics` with `query_type: nvt, asset=BTC`. Extract the current NVT value and its historical series.

### Step 3: Build the Bubble Proxy Index

Normalize each indicator independently using Min-Max over the `lookback_days` window, scaled to 0-100:

```
MVRV_norm = (MVRV_current - MVRV_min) / (MVRV_max - MVRV_min) * 100
NVT_norm  = (NVT_current  - NVT_min)  / (NVT_max  - NVT_min)  * 100
```

Combine with fixed weights that reflect MVRV's higher explanatory power for cycle position:

```
bubble_proxy = MVRV_norm * 0.6 + NVT_norm * 0.4
```

A low score indicates the market is priced near historical lows relative to on-chain fundamentals — the structural equivalent of the "index near 10" condition described in the source tweet.

### Step 4: Identify Historical Bottom Signals

Scan the historical series for periods where `bubble_proxy < bottom_threshold`. For each such period, record:
- Entry date and index value
- BTC price at signal entry
- BTC price 90, 180, and 365 days after signal entry
- Maximum drawdown within 90 days after entry

Compute:
- `historical_signals_count`
- `avg_return_90d`, `avg_return_180d`, `avg_return_365d`
- `avg_max_drawdown` (median across events)

If fewer than 3 historical events exist, flag `low_sample_warning = true` and note statistical significance is limited.

### Step 5: Assess Current State

Determine signal label:

| Condition | Label |
|-----------|-------|
| bubble_proxy <= bottom_threshold AND trend falling or flat | Strong Bottom Signal |
| bubble_proxy <= bottom_threshold * 1.3 AND trend falling | Approaching Bottom |
| otherwise | Not in Bottom Zone |

Trend is "falling" if the 30-day change in bubble_proxy is negative.

Compute `bottom_signal_strength` (0-100):
```
strength = (1 - bubble_proxy / bottom_threshold) * 100
# clamp to [0, 100]
```

### Step 6: Risk-Reward Calculation (if price_target provided)

```
upside_pct = (price_target - current_price) / current_price * 100
risk_reward_ratio = upside_pct / avg_max_drawdown
```

### Step 7: Generate Report

Use the template below. Total text output must not exceed 300 words. Use tables and numbers to replace prose where possible.

```
=== BTC Bubble Proxy Index — Bottom Detection Report ===

Asset: {symbol}  |  Analysis Date: {date}
Current Price: ${current_price}
Bubble Proxy Index: {bubble_proxy:.1f} / 100  (threshold: {bottom_threshold})

Signal: {signal_label}
Signal Strength: {bottom_signal_strength}/100
Index Trend: {index_trend}  (30-day change: {trend_change:+.1f})

--- Historical Validation ({lookback_years}-year lookback) ---
Signals Found: {historical_signals_count}
Avg Return  90d: {avg_return_90d:+.1f}%
Avg Return 365d: {avg_return_365d:+.1f}%
Median Max Drawdown After Entry: {avg_max_drawdown:.1f}%
{low_sample_warning_line}

--- Component Scores ---
MVRV (60%): {MVRV_norm:.0f}/100  [current MVRV: {mvrv_current:.2f}]
NVT  (40%): {NVT_norm:.0f}/100   [current NVT:  {nvt_current:.1f}]

{risk_reward_section}

Note: This index is a MVRV+NVT proxy, not the original monkeyjiang bubble index.
Methodology credit: @monkeyjiang. Not investment advice.
```

## 输出约束

- 总文字输出不超过 300 字
- 优先用表格、数字、百分比替代文字描述
- 结论先行：第一行给出核心信号判断，细节按需展开

## Risk Parameters

- **Proxy deviation**: MVRV + NVT approximation may diverge from the original bubble index; the threshold value 12 is calibrated for this proxy, not the original 10
- **Small sample**: Only 3-4 historical bottom events exist since 2021; treat statistics as directional, not statistically conclusive
- **Data lag**: On-chain metrics may carry T+1 delay; timestamp data in the report
- **BTC only**: MVRV/NVT data quality is highest for BTC; do not apply to altcoins without re-calibration
- **Threshold drift**: The source tweet observed that each cycle's bottom index value is slightly higher; the default threshold of 12 may need upward revision in future cycles
- **Black swan risk**: Regulatory shocks or exchange failures can temporarily break historical patterns

## 首次安装提示

```
目标用户：中长线投资者、投研人员、交易员
使用场景：市场大幅回调后确认底部区域、熊市周期中判断建仓时机、定期监控泡沫指数水位
如何使用：/btc-bubble-index-bottom-detector BTC --bottom_threshold=12 --price_target=200000
生成时间：2026-04-08 16:10:34
```
