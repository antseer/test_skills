---
name: "btc-bubble-index-bottom-signal"
description: "比特币底部信号分析 — 综合 MVRV、NVT、市场情绪、周线RSI、ETF资金流五维指标，打分判断 BTC 是否处于熊市底部区域，并计算中长期风险收益比。当用户提到比特币底部、BTC泡沫指数、BTC是否见底、bitcoin bubble index、BTC bottom signal、现在适合抄底吗、BTC链上估值时使用。"
---

## Overview

综合链上估值指标（MVRV、NVT）、市场情绪、技术面（周线RSI）和机构行为（ETF资金流），按权重打分输出 0-100 的底部信号综合得分，并判断信号等级（Strong / Moderate / Weak / No Signal）。同时基于用户输入的目标价计算风险收益比，辅助中长期仓位决策。

## Demand Context

方法论来源：@monkeyjiang（https://x.com/monkeyjiang/status/2039295737066860605）提出的"比特币泡沫指数"底部识别框架。核心观察是：自2022年以来，每当该指数从高位回落至10附近，比特币价格便进入历史性底部区域，4年内无一次失效。随着比特币市值与成熟度持续增长，底部最低值呈"逐周期抬高"的结构性特征。

原版泡沫指数为第三方综合指标，Antseer MCP暂无直接对应工具。本Skill以MVRV + NVT + 情绪指数 + RSI + ETF资金流作为代理组合，分析框架等价但具体数值存在差异，输出中标注"代理指标分析"以区分原版。

## Features (Data Inputs)

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| symbol | string | 否 | 分析目标资产，当前版本主要支持BTC | BTC |
| bubble_index_threshold | float | 否 | 泡沫指数底部阈值，低于此值视为底部区域 | 10 |
| time_range | string | 否 | 历史对比时间窗口 | 4y |
| price_target_usd | float | 否 | 用于计算风险收益比的中长期目标价 | 200000 |

**MCP 数据源：**

| 数据需求 | MCP 工具 | query_type | 参数 |
|----------|----------|------------|------|
| BTC当前价格 | ant_spot_market_structure | simple_price | ids=bitcoin |
| BTC市值/供应 | ant_spot_market_structure | coins_markets | — |
| MVRV链上估值 | ant_token_analytics | mvrv | asset=BTC |
| NVT比率 | ant_token_analytics | nvt | asset=BTC |
| 市场情绪指数 | ant_market_sentiment | coin_detail | coin=bitcoin |
| 周线RSI | ant_market_indicators | rsi | symbol=BTCUSDT |
| 布林带位置 | ant_market_indicators | boll | symbol=BTCUSDT |
| BTC ETF资金流 | ant_etf_fund_flow | btc_etf_flow | — |

## Entry Conditions

满足以下任一条件时触发本Skill：

1. 用户主动查询 BTC 是否处于底部区域、泡沫指数分析、抄底信号
2. 用户询问"BTC是否见底"、"现在适合抄底吗"、"bitcoin bubble index"等
3. 定期周期性巡检（建议每周一次）自动触发
4. 链上指标出现异动时作为二次验证
5. BTC价格出现大幅下跌（日跌幅超过5%）后的底部评估

## Exit Conditions

1. 已成功获取全部5个维度数据并输出综合底部信号得分和等级
2. 已完成风险收益比估算并输出结构化报告
3. 若任一MCP数据源不可用，在报告中标注缺失维度并基于可用数据给出部分评估
4. 报告已包含综合结论与使用建议

## Action Specification

### Step 1: 获取BTC当前价格与基础市场数据

调用 `ant_spot_market_structure`（query_type: `simple_price`, ids=bitcoin）获取实时价格。
调用 `ant_spot_market_structure`（query_type: `coins_markets`）获取市值、24h成交量、流通供应量。

记录 `current_price`、`market_cap`、`volume_24h` 作为分析基准，后续与历史底部价格区间对比。

### Step 2: 获取链上核心估值指标

调用 `ant_token_analytics`（query_type: `mvrv`, asset=BTC）获取MVRV比率（市场价值/实现价值）。
调用 `ant_token_analytics`（query_type: `nvt`, asset=BTC）获取NVT比率（网络价值/链上交易量）。

MVRV底部判断：MVRV < 1 表示市场整体持仓亏损，是熊市底部的强信号。
NVT底部判断：NVT处于历史低位时，链上结算量相对市值偏高，通常对应底部区域。

计算MVRV和NVT的历史百分位（基于time_range指定窗口的历史时间序列）：
- 百分位 < 25th 视为底部区域，满足底部信号条件
- 若历史数据不足，退回使用MVRV绝对值（< 1.0触发）作为判断依据

输出：`mvrv_current`、`nvt_current`、`mvrv_historical_percentile`、`nvt_historical_percentile`

### Step 3: 获取市场情绪指标

调用 `ant_market_sentiment`（query_type: `coin_detail`, coin=bitcoin）获取情绪评分和社交热度。

情绪标签判断（与恐贪指数逻辑一致）：
- 0-25：extreme_fear（极度恐慌）
- 26-45：fear（恐慌）
- 46-55：neutral（中性）
- 56-75：greed（贪婪）
- 76-100：extreme_greed（极度贪婪）

底部信号条件：情绪标签为 extreme_fear 或 fear 时满足。

极度恐慌与链上估值低位共振，是底部区域的强确认信号——两者同时出现时历史胜率显著提升。

### Step 4: 获取技术面辅助指标

调用 `ant_market_indicators`（query_type: `rsi`, symbol=BTCUSDT）获取周线RSI。
调用 `ant_market_indicators`（query_type: `boll`, symbol=BTCUSDT）获取布林带位置。

判断逻辑：
- 周线RSI < 35：超卖信号，满足底部条件
- 价格在布林带下轨附近（boll_position: below_lower）：技术面低位信号

RSI是滞后指标，不单独作为入场依据，但与链上指标共振时信号更可靠。

### Step 5: 获取ETF资金流向

调用 `ant_etf_fund_flow`（query_type: `btc_etf_flow`）获取BTC现货ETF近期资金流向。

流向趋势判断：
- `inflow`：近7日ETF净流入（机构在底部区域布局，底部确认信号）
- `stable`：近7日ETF流出止跌或趋于平稳（底部确认信号有所减弱）
- `outflow`：近7日ETF持续净流出（机构尚未进场，底部尚未最终确认）

底部信号条件：ETF流向为 stable 或 inflow 时满足（连续3日转正才确认为inflow）。

底部区域往往伴随ETF持续流出后出现止跌迹象；ETF已开始净流入时底部信号最强。

### Step 6: 综合评估与底部信号打分

汇总Step 2-5的结果，按以下权重计算底部信号综合得分：

| 指标 | 底部信号条件 | 权重 |
|------|------------|------|
| MVRV | < 1.0 或历史分位 < 25th pct | 30% |
| NVT | < 历史25th percentile | 20% |
| 市场情绪 | extreme_fear 或 fear | 20% |
| 周线RSI | < 35 | 15% |
| ETF流向 | stable 或 inflow | 15% |

综合得分 = Σ（各指标达到底部条件 ? 该权重×100 : 0）

信号等级判断：
- 得分 >= 70：Strong（强底部信号）
- 得分 50-69：Moderate（中度底部信号）
- 得分 30-49：Weak（弱底部信号）
- 得分 < 30：No Signal（无底部信号）

若某指标数据不可用，将其权重按比例分配给其他可用指标，并在报告中标注。

### Step 7: 风险收益比估算

基于 `current_price` 和 `price_target_usd`（默认200000 USD）计算：

```
upside_ratio = (price_target_usd - current_price) / current_price
current_vs_target_gap_pct = upside_ratio * 100
```

类比原作者方法论：若当前价格为5万和6万，上行至20万的空间差异约23%，在底部区域的精确择时意义相对有限，长期风险收益比均属较优。当 upside_ratio >= 2.0 时，可在报告中注明"底部区域布局的风险收益比显著"。

### Step 8: 生成报告

始终使用以下模板输出：

```
=== 比特币底部信号分析报告 ===
分析时间: {signal_timestamp} UTC
分析资产: {symbol}

底部信号评级: {bottom_signal_grade}（综合得分 {bottom_signal_score}/100）

核心指标快照:
  当前价格:        ${current_price} USD
  MVRV 比率:       {mvrv_current}（历史{time_range} {mvrv_percentile}th percentile）
  NVT 比率:        {nvt_current}（历史{time_range} {nvt_percentile}th percentile）
  市场情绪:        {sentiment_label}（指数 {sentiment_score}/100）
  周线 RSI:        {rsi_weekly}
  ETF 资金流:      近7日净流向: {etf_flow_7d}，近30日: {etf_flow_30d}（{etf_flow_trend}）

底部信号得分明细:
  MVRV 底部条件    {pass/fail}（{30 or 0}分）
  NVT  底部条件    {pass/fail}（{20 or 0}分）
  情绪底部条件     {pass/fail}（{20 or 0}分）
  周线RSI < 35     {pass/fail}（{15 or 0}分）
  ETF止跌/流入     {pass/fail}（{15 or 0}分）

风险收益估算:
  目标价:     ${price_target_usd} USD
  上行空间:   +{current_vs_target_gap_pct}%（约{upside_ratio}倍）
  区间布局提示: {timing_note}

综合结论:
{analysis_summary}

注意: 本分析基于MVRV/NVT/情绪/RSI/ETF的代理指标组合，非原版比特币泡沫指数。
方法论归属原作者 @monkeyjiang。基于历史数据，不能预测未来，不构成投资建议。
```

## Risk Parameters

- **样本量有限**: 2022年至今底部信号仅触发3-4次，历史验证统计显著性有限，不应过度依赖历史胜率
- **数据延迟**: ETF资金流数据存在T+1延迟；MVRV/NVT链上指标可能存在T+1延迟，报告中标注数据时间戳
- **阈值漂移**: 随比特币体量增长，泡沫指数底部阈值可能逐周期抬高，默认值10未来可能需上调
- **情绪时间尺度**: 情绪指数反映短期（日级）情绪，与链上指标的中长期底部判断时间尺度不完全一致
- **单一资产限制**: 当前版本仅针对BTC优化，山寨币无等效链上历史分位数据
- **宏观事件失效**: 美联储政策急变、交易所暴雷等黑天鹅事件可能使历史规律暂时失效，此时技术底部信号不可靠
- **近似偏差**: 本指标组合是对原版泡沫指数的近似还原，存在系统性偏差，具体数值不可与原版直接对比
- **ETF止跌判断**: "止跌"vs"短暂停流"边界模糊，建议观察连续3日转正才确认为inflow

## 首次安装提示

```
目标用户：中长期BTC持仓者、加密货币投研人员、家办/机构配置分析师
使用场景：定期（每周一次）巡检BTC是否处于熊市底部区域，或BTC大跌后快速评估是否值得加仓
如何使用：/btc-bubble-index-bottom-signal BTC --price_target_usd=200000
```
