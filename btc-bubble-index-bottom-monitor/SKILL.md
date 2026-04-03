---
name: "btc-bubble-index-bottom-monitor"
description: "比特币泡沫指数底部监控 — 综合链上与市场数据计算近似泡沫指数，识别周期底部区域"
strategy_agent: "monitoring_agent"
version: "1.0.0"
created_at: "2026-04-03T03:40:00Z"
skill_lifecycle: "draft"
author: "creator-agent"
source_prd: "prd_20260403_033424_16c7b1"
---

# 比特币泡沫指数底部监控 (BTC Bubble Index Bottom Monitor)

## Overview

本 Skill 通过综合 6 个维度的链上与市场数据，计算一个 0-100 的近似比特币泡沫指数，用于识别比特币周期底部区域。当泡沫指数跌至 10 附近时，历史上（2022 年至今）每次都对应着比特币的阶段性底部，向下空间极其有限。

核心逻辑：将价格偏离度、MVRV 比率、NVT 比率、市场情绪、交易所资金流向、ETF 资金流向等维度归一化至 0-100 区间后加权求和，得出综合泡沫指数。指数越低表示市场越接近底部，指数越高表示泡沫程度越大。

适用场景：定期巡检（每日/每周）及价格大幅下跌时的事件驱动触发。

## Demand Context

来源推文：https://x.com/monkeyjiang/status/2039295737066860605

作者 @monkeyjiang 观察到比特币泡沫指数跌至 10 附近时精准预示底部区域，该规律在 2022 年至今的 4 年中没有失效。同时作者指出，随着比特币市场体量增长，泡沫指数的跌幅在逐渐缩小——意味着每轮周期底部的泡沫指数可能逐步抬高。

本 Skill 基于可获取的底层链上和市场数据尝试近似还原该指数的核心逻辑，并非原版"比特币泡沫指数"的精确复现。

## Features (Data Inputs)

| Feature | MCP Tool | query_type | Parameters | Weight | Description |
|---------|----------|------------|------------|--------|-------------|
| current_price | ant_spot_market_structure | simple_price | ids=bitcoin | - | BTC 当前价格（USD） |
| market_data | ant_spot_market_structure | coins_markets | - | - | 市值、交易量等市场快照数据 |
| price_deviation_pct | ant_spot_market_structure | coins_markets | - | 25% | 价格偏离 MA200 的百分比 |
| mvrv_ratio | ant_token_analytics | mvrv | asset=bitcoin | 25% | MVRV 比率（Market Value / Realized Value） |
| nvt_ratio | ant_token_analytics | nvt | asset=bitcoin | 15% | NVT 比率（Network Value to Transactions） |
| sentiment_score | ant_market_sentiment | coin_detail | coin=bitcoin | 15% | 市场情绪评分 |
| exchange_netflow | ant_fund_flow | exchange_netflow | asset=bitcoin | 10% | 交易所 BTC 净流量 |
| etf_fund_flow | ant_etf_fund_flow | btc_etf_flow | - | 10% | BTC ETF 资金流 |

辅助数据：

| Feature | MCP Tool | query_type | Parameters | Description |
|---------|----------|------------|------------|-------------|
| exchange_reserve | ant_fund_flow | exchange_reserve | asset=bitcoin | 交易所 BTC 储备量（辅助判断吸筹/抛压） |

## Analysis Flow

### Step 1: 获取 BTC 当前价格与历史价格

调用 `ant_spot_market_structure`（simple_price, ids=bitcoin）获取当前价格，调用 `ant_spot_market_structure`（coins_markets）获取市值、交易量等。计算 200 日均线（MA200），得出价格偏离度 = (当前价格 - MA200) / MA200。

输出：当前价格、MA200、价格偏离度百分比。

### Step 2: 获取链上估值指标（MVRV）

调用 `ant_token_analytics`（mvrv, asset=bitcoin）获取 MVRV 比率。MVRV < 1 表示市场整体亏损（底部特征），MVRV > 3.5 表示严重高估（顶部特征）。

输出：当前 MVRV 值、历史分位数排名。

### Step 3: 获取 NVT 比率

调用 `ant_token_analytics`（nvt, asset=bitcoin）获取 NVT 比率。NVT 极低说明链上交易活跃度相对市值偏高，可能预示底部；NVT 极高可能预示泡沫。

输出：当前 NVT 值、信号判断。

### Step 4: 获取市场情绪数据

调用 `ant_market_sentiment`（coin_detail, coin=bitcoin）获取情绪评分。情绪极度恐惧（低分）通常对应底部区域，极度贪婪（高分）对应泡沫区域。

输出：情绪评分、情绪状态标签。

### Step 5: 获取交易所资金流向

调用 `ant_fund_flow`（exchange_netflow, asset=bitcoin）和 `ant_fund_flow`（exchange_reserve, asset=bitcoin）。持续净流出（负值）表示投资者提币囤币，通常为底部吸筹信号；净流入为抛压信号。

输出：近 7 日/30 日净流量趋势、交易所储备变化率。

### Step 6: 获取 ETF 资金流向

调用 `ant_etf_fund_flow`（btc_etf_flow）获取机构通过 ETF 渠道的资金流入流出。ETF 持续净流入表示机构在底部区域买入，为底部确认信号之一。

输出：近期 ETF 净流量、累计持仓变化。

### Step 7: 综合计算泡沫指数

将 Step 1-6 的所有中间结果综合为一个 0-100 的泡沫指数近似值。每个维度归一化到 0-100 区间（0=极度低估/底部，100=极度高估/泡沫），按权重加权求和。

### Step 8: 历史验证与趋势分析

对比历史上泡沫指数触及底部阈值时的价格表现，统计 30/90/180 天后的价格变化，观察底部值是否逐周期抬高，计算历史胜率。

## Signal Conditions

信号等级基于综合泡沫指数值划分：

```yaml
signal_conditions:
  bottom_signal:
    - condition: bubble_index
      operator: "<="
      threshold: 10  # 可通过 bubble_threshold 参数调整
      label: "底部信号"
      description: "当前处于底部区域，向下空间有限"

  undervalued:
    - condition: bubble_index
      operator: "range"
      min: 10
      max: 30
      label: "偏低估"
      description: "接近底部但尚未触发强信号"

  neutral:
    - condition: bubble_index
      operator: "range"
      min: 30
      max: 70
      label: "中性区间"
      description: "无明显方向信号"

  overvalued:
    - condition: bubble_index
      operator: "range"
      min: 70
      max: 90
      label: "偏高估"
      description: "需警惕回调"

  bubble_warning:
    - condition: bubble_index
      operator: ">="
      threshold: 90
      label: "泡沫警告"
      description: "严重高估，注意风险"
```

## Composite Index Calculation

```yaml
composite_index:
  name: "bubble_index"
  range: [0, 100]
  method: "weighted_sum"
  normalization: "min_max_to_0_100"
  dimensions:
    - name: "price_deviation"
      source: "price_deviation_pct"
      weight: 0.25
      mapping: "价格显著低于 MA200 → 低分（底部），显著高于 → 高分（泡沫）"
    - name: "mvrv_ratio"
      source: "mvrv_ratio"
      weight: 0.25
      mapping: "MVRV < 1 → 低分（底部），MVRV > 3.5 → 高分（泡沫）"
    - name: "nvt_ratio"
      source: "nvt_ratio"
      weight: 0.15
      mapping: "NVT 极低 → 低分（链上活跃），NVT 极高 → 高分（泡沫）"
    - name: "market_sentiment"
      source: "sentiment_score"
      weight: 0.15
      mapping: "极度恐惧 → 低分（底部），极度贪婪 → 高分（泡沫）"
    - name: "exchange_flow"
      source: "exchange_netflow"
      weight: 0.10
      mapping: "持续净流出 → 低分（吸筹/底部），持续净流入 → 高分（抛压/泡沫）"
    - name: "etf_flow"
      source: "etf_fund_flow"
      weight: 0.10
      mapping: "机构净流入 → 中低分（底部吸筹），机构净流出 → 中高分"
```

## Action Specification

```yaml
action:
  type: MONITOR_AND_ALERT
  triggers:
    - event: "bubble_index_below_threshold"
      condition: "bubble_index <= bubble_threshold"
      actions:
        - generate_report: true
        - send_alert: "alert_enabled == true"
        - alert_channel: "telegram"
        - alert_priority: "high"
        - alert_message: "比特币泡沫指数触及底部阈值，当前处于底部区域"

    - event: "bubble_warning"
      condition: "bubble_index >= 90"
      actions:
        - generate_report: true
        - send_alert: "alert_enabled == true"
        - alert_channel: "telegram"
        - alert_priority: "high"
        - alert_message: "比特币泡沫指数进入泡沫区域，注意风险"

    - event: "scheduled_check"
      schedule: "daily"
      actions:
        - generate_report: true
        - send_alert: false
```

## Risk Parameters / Limitations

```yaml
risk_parameters:
  data_delay: "链上指标（MVRV、NVT）通常存在 T+1 数据延迟"
  sample_size: "历史验证样本量有限（2022 至今约 3-4 次底部信号），统计显著性不足"
  weight_calibration: "各维度权重为经验设定，建议通过历史回测优化"
  threshold_drift: "随比特币体量增长，底部阈值可能需上调（泡沫指数跌幅逐周期缩小）"
  scope_limitation: "当前仅支持 BTC，不适用于山寨币"
  timeframe: "中长周期指标，不适用于短线交易决策"
  black_swan: "宏观黑天鹅事件可能使历史规律暂时失效，需人工评估"
  historical_price_gap: "MA200 计算需要足够长的历史 K 线数据，coins_markets 提供当前快照，首次运行建议缓存历史价格"
  approximation_notice: "本指数为多维度近似还原值，非原版比特币泡沫指数的精确复现"
```

## Output Structure

关键输出字段：

| Field | Type | Description |
|-------|------|-------------|
| bubble_index | number | 综合泡沫指数（0-100） |
| signal_level | string | 信号等级: bottom / undervalued / neutral / overvalued / bubble |
| current_price | number | BTC 当前价格（USD） |
| ma200 | number | 200 日均线价格 |
| price_deviation_pct | number | 价格偏离 MA200 的百分比 |
| mvrv_ratio | number | 当前 MVRV 比率 |
| nvt_ratio | number | 当前 NVT 比率 |
| sentiment_score | number | 市场情绪评分 |
| exchange_netflow_7d | number | 近 7 日交易所净流量 |
| etf_netflow_7d | number | 近 7 日 ETF 净流量 |
| dimension_scores | object | 各维度得分明细（price_deviation, mvrv, nvt, sentiment, exchange_flow, etf_flow） |
| historical_hit_rate | number | 历史信号胜率（百分比） |
| assessment | string | 综合文字评估 |
| timestamp | string | 数据时间戳（ISO 8601） |

输出示例：

```
======================================================
  比特币泡沫指数底部监控报告
======================================================

  综合泡沫指数: 8.3 / 100
  信号等级: [底部信号]

------------------------------------------------------
  BTC 当前价格: $63,500
  200日均线:     $72,800
  价格偏离度:    -12.8%
------------------------------------------------------
  各维度评分:
  +-- 价格偏离度 (25%):   6/100  <-- 显著低于长期均线
  +-- MVRV 比率 (25%):    9/100  <-- MVRV=0.92, 市场整体亏损
  +-- NVT 比率 (15%):     12/100 <-- 链上活跃度相对偏高
  +-- 市场情绪 (15%):     8/100  <-- 极度恐惧
  +-- 交易所净流量 (10%): 5/100  <-- 持续大额净流出（吸筹）
  +-- ETF 资金流 (10%):   11/100 <-- 近期小幅净流入
------------------------------------------------------
  历史验证:
  +-- 过去 4 次触发底部信号
  +-- 30 天后平均涨幅: +18.5%
  +-- 90 天后平均涨幅: +42.3%
  +-- 历史胜率: 100% (4/4)
------------------------------------------------------
  综合评估:
  泡沫指数 8.3 已跌破阈值 10，触发底部信号。
  当前 BTC 价格 $63,500 处于历史底部区域。
  多项链上指标（MVRV<1、交易所持续净流出、情绪极度恐惧）
  共同确认底部特征。向下空间有限，中长期配置价值显著。

  注意: 本指数为近似还原值，非原版比特币泡沫指数。
  仅供参考，不构成投资建议。
======================================================
```

## Input Parameters

| Parameter | Type | Required | Description | Default | Example |
|-----------|------|----------|-------------|---------|---------|
| asset | string | No | 目标资产（当前仅支持 BTC） | bitcoin | bitcoin |
| bubble_threshold | number | No | 泡沫指数触发底部信号的阈值 | 10 | 10 |
| lookback_days | number | No | 回看历史天数，用于计算指标和验证历史规律 | 365 | 365 |
| ma_period | number | No | 长期均线周期（天），用于价格偏离度计算 | 200 | 200 |
| alert_enabled | boolean | No | 是否在指数触及阈值时发送告警 | true | true |
