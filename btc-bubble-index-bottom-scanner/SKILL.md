---
name: "btc-bubble-index-bottom-scanner"
description: "综合链上估值（MVRV、NVT）、技术指标（RSI、MACD）、ETF 资金流向和市场情绪，判断比特币是否处于熊市底部区域。当用户提到 BTC 底部信号、比特币泡沫指数、btc bubble index bottom、比特币估值底、链上底部判断、btc bottom signal、熊市底部判断，或想评估当前 BTC 入场时机、计算不同入场价格的收益风险比时，使用此 Skill。也适用于行情大跌后的快速底部诊断，或定期（周/月）跟踪底部信号变化趋势。"
---

## Overview

综合 MVRV、NVT 链上估值指标、RSI/MACD 技术面、ETF 机构资金流向和市场情绪四个维度，评估 BTC 是否处于历史底部区间，输出信号强度评级和收益风险比对照表，辅助中长线投资者做底部入场决策。

## Demand Context

源自 @monkeyjiang 的推文分析（https://x.com/monkeyjiang/status/2039295737066860605）：作者使用"比特币泡沫指数"（Bitcoin Bubble Index）作为判断熊市底部的核心工具，指出自 2022 年起，每当该指数跌至 10 附近，比特币就会形成阶段性底部，且随着市场成熟化，底部的极端低估程度在历次熊市中有所收敛。作者将 6 万美金区间定性为熊市底部，并用收益风险比框架说明"5 万与 6 万入场几乎等价，关键是是否在底部区间入场"。

由于"比特币泡沫指数"原始数据源未公开（可能来自 CryptoQuant 或 Glassnode），本 Skill 使用 MVRV Z-Score 作为最佳代理指标（两者结构高度相似），并配合 NVT、RSI、MACD、ETF 资金流和情绪数据进行多维交叉验证。

方法论归属：@monkeyjiang，本 Skill 基于其公开分析框架构建。

## Features (Data Inputs)

### 可选参数（均有默认值）

| 参数 | 类型 | 默认值 | 说明 | 示例 |
|------|------|--------|------|------|
| symbol | string | BTC | 分析目标资产符号（当前仅支持 BTC） | BTC |
| bottom_threshold | float | 10 | 泡沫指数底部判断阈值，MVRV 处于历史低分位时对应此区间 | 10 |
| lookback_years | int | 4 | 历史数据回溯年数，用于验证阈值有效性（覆盖 2022-至今） | 4 |
| price_targets | list | [200000] | 未来目标价格列表（USD），用于计算收益倍数 | [200000] |
| time_range | string | 1y | 技术指标分析时间范围 | 1y |

### 数据来源（MCP 工具）

| 数据维度 | MCP 工具 | query_type | 参数 |
|----------|----------|------------|------|
| MVRV 链上估值 | ant_token_analytics | mvrv | asset=BTC |
| NVT 链上估值 | ant_token_analytics | nvt | asset=BTC |
| 当前价格 | ant_spot_market_structure | simple_price | ids=bitcoin |
| RSI 技术指标 | ant_market_indicators | rsi | symbol=BTCUSDT |
| MACD 技术指标 | ant_market_indicators | macd | symbol=BTCUSDT |
| ETF 资金流向 | ant_etf_fund_flow | btc_etf_flow | — |
| 市场情绪 | ant_market_sentiment | coin_detail | coin=bitcoin |

## Entry Conditions

满足以下任一条件时触发本 Skill：

1. 用户主动请求底部扫描（如 `/btc-bubble-index-bottom-scanner`）
2. 市场出现大幅下跌（单日 -10% 以上）需快速判断是否触底
3. 定期底部追踪（建议每周或每月执行一次）

## Exit Conditions

满足以下条件时 Skill 执行完成：

1. 已完成全部 7 个分析步骤的数据采集与计算
2. 已输出综合底部信号评级（强底部信号 / 弱底部信号 / 非底部区间）
3. 已输出收益风险比对照表
4. 已输出结构化报告并附上人工验证提示

## Action Specification

### Step 1: 获取链上估值指标（MVRV）

调用 `ant_token_analytics`，参数：
- query_type: `mvrv`
- asset: `BTC`

提取当前 MVRV 比率（Market Value to Realized Value）。计算 MVRV 在过去 `lookback_years` 年历史数据中的百分位排名（`mvrv_percentile`）。

判断标准：
- MVRV 比率 < 1.0，或历史分位 < 20%：链上估值处于极度低估区间，视为底部信号
- MVRV 比率 1.0-1.5，或历史分位 20-40%：低估区间，弱底部信号
- MVRV 比率 > 2.0，或历史分位 > 60%：中高估值，非底部区间

记录：`mvrv_value`、`mvrv_percentile`、`mvrv_signal`（bottom / weak / neutral / high）

### Step 2: 获取链上估值指标（NVT）

调用 `ant_token_analytics`，参数：
- query_type: `nvt`
- asset: `BTC`

提取当前 NVT 比率（Network Value to Transactions Ratio）。与历史同期对比，判断链上交易活跃度相对于市值是否偏高（NVT 高说明市值高于链上活动支撑）。

判断标准：
- NVT 处于历史低分位（< 25%）：链上交易活跃，支撑估值，底部信号增强
- NVT 处于历史高分位（> 75%）：市值高于交易活跃度支撑，注意高估风险

记录：`nvt_value`、`nvt_percentile`、`nvt_signal`

### Step 3: 获取当前价格与技术指标

依次调用以下三个工具：

**3a. 价格数据**
调用 `ant_spot_market_structure`，参数：
- query_type: `simple_price`
- ids: `bitcoin`

提取：`current_price`（当前 USD 价格）

**3b. RSI 指标**
调用 `ant_market_indicators`，参数：
- query_type: `rsi`
- symbol: `BTCUSDT`

判断标准：
- RSI < 30：超卖，底部信号
- RSI 30-40：接近超卖，弱底部信号
- RSI > 50：中性或强势

记录：`rsi_value`、`rsi_signal`

**3c. MACD 指标**
调用 `ant_market_indicators`，参数：
- query_type: `macd`
- symbol: `BTCUSDT`

判断标准：
- MACD 柱状图由负转正，且价格仍处于低位：底背离形成，底部信号
- MACD 柱状图持续为负且扩大：下跌动能未止
- MACD 柱状图由正转负（价格高位）：顶背离，非底部信号

记录：`macd_signal`（底背离 / 顶背离 / 无信号）、`macd_momentum`

### Step 4: ETF 资金流向验证

调用 `ant_etf_fund_flow`，参数：
- query_type: `btc_etf_flow`

提取近 30 日 BTC ETF 累计净流量和最近 7 日趋势方向。

判断标准：
- 近 30 日净流入为正且呈加速趋势：机构认可底部区域，增强底部信号
- 近 30 日净流入为正但减速：中性
- 近 30 日净流出：降低信号置信度（机构仍在撤离，谨慎对待）

记录：`etf_30d_flow`（USD）、`etf_7d_trend`（流入加速 / 流入减速 / 净流出）、`etf_signal`

### Step 5: 市场情绪验证

调用 `ant_market_sentiment`，参数：
- query_type: `coin_detail`
- coin: `bitcoin`

提取当前情绪评分和情绪标签。

判断标准：
- 情绪评分处于极端恐慌区间（通常 < 25）：历史上底部伴随极端恐慌，信号增强
- 情绪评分中性（25-60）：弱信号
- 情绪评分贪婪区间（> 60）：不符合底部特征

记录：`sentiment_score`、`sentiment_label`（极度恐慌 / 恐慌 / 中性 / 贪婪 / 极度贪婪）、`sentiment_signal`

### Step 6: 收益风险比计算

基于 Step 3a 获取的 `current_price` 和输入参数 `price_targets`，计算潜在收益倍数：

```
upside_pct = (target_price - current_price) / current_price × 100
```

生成对照表，对比不同入场价格的潜在收益差异。参照推文原始框架：展示 5 万、6 万（或实际当前价格）与目标价之间的收益差，说明"底部区间内不同入场点的机会成本"。

若 `price_targets` 包含多个目标价，分别计算并按目标价从低到高排列。

### Step 7: 综合评估与报告输出

汇总 Step 1-6 所有信号，统计满足底部条件的维度数量，按以下标准评定：

**评级标准：**
- **强底部信号（高置信）**：满足以下全部条件
  - MVRV 历史分位 < 25%
  - RSI < 35 或 MACD 底背离
  - ETF 近 30 日净流入
  - 情绪评分处于恐慌区间（< 35）
- **弱底部信号（中置信）**：满足上述条件中的 2-3 项
- **非底部区间**：满足条件不足 2 项，或 MVRV 历史分位 > 50%

**置信度计算（`signal_confidence`，0-1）：**
- 基础分：满足条件数 / 4 × 0.6
- MVRV 分位加权：(1 - mvrv_percentile/100) × 0.2
- ETF 流入加权：etf 净流入为正 ? +0.1 : 0
- 情绪加权：sentiment_score < 25 ? +0.1 : 0

**使用以下模板输出结构化报告：**

```
=== BTC 底部信号分析报告 ===
分析时间: {analysis_timestamp}
当前价格: ${current_price}

链上估值指标
├── MVRV 比率: {mvrv_value}（历史 {mvrv_percentile}% 分位）{mvrv_signal_icon}
├── NVT 比率: {nvt_value}（历史 {nvt_percentile}% 分位）
└── 判断: {mvrv_summary}

技术面
├── RSI(14): {rsi_value} → {rsi_label}
└── MACD: {macd_signal}

机构资金 (ETF)
└── 近 30 日净流量: {etf_30d_flow} → {etf_7d_trend}

市场情绪
└── 情绪评分: {sentiment_score} → {sentiment_label}

综合评级: {bottom_signal_rating}（置信度 {signal_confidence}）
注: "比特币泡沫指数"原始数据建议对照 CryptoQuant/Glassnode 人工验证（搜索 "BTC Bubble Index" 或 "MVRV Z-Score"）

收益风险比（参考目标价格）
┌──────────────┬────────────────┬────────────────┐
│ 入场价格     │ 目标价         │ 潜在收益       │
├──────────────┼────────────────┼────────────────┤
{upside_table_rows}
└──────────────┴────────────────┴────────────────┘
{upside_summary}
```

## Risk Parameters

### 边界约束

- 本 Skill 仅适用于 BTC（MVRV/NVT 数据覆盖有限，不适用于山寨币）
- 无法直接获取"比特币泡沫指数"原始数值，需借助 CryptoQuant 或 Glassnode 人工验证
- 不预测底部精确价格或精确时间，只判断"是否处于底部区域"
- 无法覆盖黑天鹅事件（监管打压、交易所暴雷等结构性风险）

### 数据局限性

- MVRV/NVT 为链上滞后指标，不能反映场外 OTC 及 CEX 内部流动
- ETF 资金流数据通常有 1 日延迟
- 市场情绪指标主观性较强，历史有效性因周期而异
- 技术指标（RSI、MACD）在单边下跌趋势中可能持续处于超卖区间，须配合链上数据综合判断

### 需要人工判断的环节

- 对照原始"比特币泡沫指数"数据源（CryptoQuant/Glassnode）确认指数是否跌至 10 附近
- 宏观环境判断（美联储利率周期、全球流动性）需结合宏观指标综合评估
- 最终入场决策及仓位管理

## 首次安装提示

```
目标用户：中长线投资者 / 投研人员 / 资产配置顾问
使用场景：熊市巡检时判断是否处于底部区域；行情大跌后快速判断是否触底；定期（周/月）评估入场时机
如何使用：/btc-bubble-index-bottom-scanner
```
