---
name: "cex-volume-anomaly-signal"
description: "检测 CEX 换手量极端异常以识别资产底部区域信号。当用户提到换手量底部信号、交易量极端分析、CEX volume bottom signal、交易量与历史对比、底部出清信号、这波量能跟上轮比吗，或者在市场大幅下跌期间想判断某资产是否进入历史换手量极端区间时，触发本 Skill。"
---

## Overview

通过 CEX 换手量与历史压力事件（3AC 暴雷、FTX 暴雷、LUNA 崩盘等）对比，结合 ETF 稀释修正、净流量验证和跨资产底部时序分析，生成多维度加权的底部信号评分（0-100），辅助判断资产是否处于底部区域。

## Demand Context

本 Skill 源自交易员 @Michael_Liu93（2026-02-23）的 ETH 底部建仓方法论。其核心观察是：币安平台上 ETH 的换手量已与 2022 年 FTX 暴雷时期持平，而在 ETH CEX 交易量已被 ETF 资金流和机构渠道稀释的背景下，还原稀释因素后实际市场压力程度与 3AC 事件相当。

作者同时运用跨周期资产底部时序规律：上轮周期中 ETH 在 3AC 暴雷（2022 年 6 月，约 $880）时已触底，而 BTC 则在 4 个月后 FTX 暴雷（2022 年 11 月）才触底——山寨资产在去杠杆周期中往往先于 BTC 完成底部定价。

CEX 换手量达到历史极端值通常伴随恐慌性出货尾声（市场出清信号），为短期反弹提供统计支撑。本 Skill 将上述方法论通用化，适用于分析任意主流资产在市场压力期间的底部信号强度。

方法论归属：@Michael_Liu93。

## Features (Data Inputs)

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| symbol | string | 是 | -- | 目标资产符号，如 ETH、BTC、SOL |
| exchange | string | 否 | binance | 主要观察的中心化交易所 |
| lookback_days | integer | 否 | 7 | 当前换手量统计窗口（天） |
| benchmark_events | list | 否 | ["3AC","FTX"] | 历史压力事件名称，用于基准比较 |
| etf_adjustment | boolean | 否 | true | 是否对 CEX 量进行 ETF/机构渠道稀释调整 |
| comparison_asset | string | 否 | BTC | 用于跨资产时序对比的参照标的 |
| time_range | string | 否 | 2022-01-01 至今 | 历史数据拉取范围 |

**内置历史事件日期映射表**（分析中直接引用，无需用户提供）：

| 事件名 | 日期窗口 | 资产影响 |
|--------|---------|---------|
| 3AC | 2022-05-01 ~ 2022-07-15 | ETH/BTC/山寨 |
| FTX | 2022-11-01 ~ 2022-12-15 | ETH/BTC/山寨 |
| LUNA | 2022-05-01 ~ 2022-05-20 | 山寨/ETH |
| 2020-3.12 | 2020-03-01 ~ 2020-03-20 | ETH/BTC |

## Entry Conditions

当以下任意条件满足时触发本 Skill：

- 用户提到"换手量底部信号"、"交易量极端分析"、"CEX volume bottom signal"、"底部出清信号"、"这波量能跟上轮比吗"
- 市场出现大幅下跌（近 30 天跌幅 >30%），用户想量化底部信号强度
- 用户提供资产名称并询问"当前换手量是否与历史压力事件相当"
- 用户观察到某资产 CEX 交易量异常放大，想判断是否为出清信号

## Exit Conditions

本 Skill 完成当：

- 生成包含 7 个步骤全部结果的结构化分析报告
- 底部信号综合评分（0-100）和信号等级（强/中/弱/无）已计算完毕
- 报告包含明确的操作建议和风险提示

遇到以下情况提前退出并说明原因：

- 目标资产无历史 CEX 数据（小市值代币、新上线资产）
- MCP 工具调用全部失败且无法获取任何数据

## Action Specification

按以下 7 个步骤顺序执行。每步结果传递给下一步。若某 MCP 调用失败，记录失败原因并继续执行——部分分析结果优于无分析结果。

### Step 1: 获取当前 CEX 交易量

调用 `ant_spot_market_structure`，参数 query_type 设为 `coins_markets`，传入 symbol 作为过滤条件。

同时调用 `ant_market_indicators`，参数 query_type 设为 `taker_flow_aggregated`，传入 symbol，获取主动买卖方向分布。

计算 lookback_days 内的日均成交量（current_avg_volume）和累计成交量（current_total_volume）。这两个值是后续所有对比计算的分子。

### Step 2: 计算 ETF 稀释修正因子

若 etf_adjustment 为 true（默认），执行以下操作：

- symbol 为 ETH 时：调用 `ant_etf_fund_flow`，参数 query_type 设为 `eth_etf_flow`
- symbol 为 BTC 时：调用 `ant_etf_fund_flow`，参数 query_type 设为 `btc_etf_flow`
- symbol 为其他资产时：跳过此步，稀释系数 D 记为 0

计算 ETF 日均资金流规模与 CEX 现货日均量的比值，即稀释系数 D。

调整后等效压力量 = current_avg_volume × (1 + D)，即还原被分流至 ETF/机构渠道的隐性交易压力。

这一修正的意义在于：ETF 渠道吸纳了原本会流向 CEX 现货市场的大量需求，使得表面上的 CEX 量显得"偏低"——还原后才能与历史压力事件（ETF 规模更小时）公平对比。

记录：etf_daily_avg_flow、dilution_factor（D）、adjusted_volume。

### Step 3: 建立历史压力事件基准

对 benchmark_events 中每个事件：

1. 从内置日期映射表中提取该事件的日期窗口
2. 调用 `ant_spot_market_structure`，参数 query_type 设为 `coins_markets`，传入 symbol 和对应的历史日期范围，获取该事件期间的历史成交量数据
3. 计算该事件窗口内的日均量 = benchmark_volume[event]

历史期的 ETF 规模远小于当前，若需对历史量同步做稀释还原，可按事件发生时 ETF AUM 占当前 AUM 的比例估算修正幅度（此为可选精细化步骤）。

记录：benchmark_volumes（各事件日均量字典）、benchmark_dates（各事件日期窗口）。

### Step 4: 换手量极端性评分

此步骤为纯计算，不调用 MCP 工具。

对每个历史事件，计算：ratio[event] = adjusted_volume / benchmark_volumes[event]

判断逻辑：
- ratio >= 0.9 → 当前量已达到或超过该历史事件水平（显著压力信号）
- ratio 在 0.7~0.9 → 接近但未达到历史水平（中等压力）
- ratio < 0.7 → 明显低于历史压力水平

同时计算 historical_percentile：当前量在历史数据中的百分位排名。
- percentile >= 95 → 极端换手（历史 top 5%），标记 extreme_flag = true

记录：volume_ratios（各事件对比比率）、historical_percentile、extreme_flag。

### Step 5: 跨资产底部时序分析

分别对 symbol 和 comparison_asset（默认 BTC）调用 `ant_spot_market_structure`，参数 query_type 设为 `coins_markets`，获取各历史压力事件期间的价格数据，提取价格低点日期。

同时调用 `ant_market_indicators`，参数 query_type 设为 `rsi`，传入 symbol，获取当前超卖程度作为辅助参考。

计算各历史事件中两个资产的底部时序差：lead_lag[event] = comparison_asset 底部日期 - symbol 底部日期（正值表示 symbol 先于 comparison_asset 触底）。

当前周期判断逻辑：若 symbol 的 CEX 量已达极端，且 comparison_asset 的量尚未达到同等极端水平，则推断 symbol 可能处于先行底部区间，与历史时序模式吻合。

记录：historical_timing（各事件底部时序记录）、timing_pattern（symbol 先于/晚于/同步于 comparison_asset）、current_timing_signal。

### Step 6: 交易所资金流向验证

调用 `ant_fund_flow`，参数 query_type 设为 `exchange_netflow`，传入 asset=symbol 和 exchange 参数。

同时调用 `ant_fund_flow`，参数 query_type 设为 `exchange_reserve`，传入 asset=symbol 和 exchange 参数。

解读净流向数据：
- exchange_netflow < 0（净流出）且量极端 → 抛售出清信号强，市场正在主动去杠杆
- exchange_reserve 同步持续下降 → 恐慌性提币，底部信号可信度提升
- 量大但无净流出 → 更可能是高频交易/做市商行为，底部信号可信度降低，需在报告中注明

记录：netflow_direction（净流入/净流出/中性）、reserve_trend（上升/下降/平稳）、outflow_confirmation（布尔值）。

### Step 7: 综合评估与底部信号评分

此步骤为纯推理，不调用 MCP 工具。汇总前 6 步所有中间结果，应用以下加权评分模型：

| 信号维度 | 权重 | 触发条件 |
|---------|------|---------|
| 换手量历史极端（top 5%） | 35 分 | historical_percentile >= 95 |
| 换手量达历史压力事件水平 | 25 分 | 任一 volume_ratios[event] >= 0.9 |
| CEX 净流出确认 | 20 分 | outflow_confirmation = true |
| 跨资产时序信号吻合 | 20 分 | timing_pattern = symbol 先于 comparison_asset |

综合得分 = 各维度满足时得满分，按比例计算部分满足情况。

**信号等级判断**：
- 80-100 分：强底部信号（历史极端换手 + 净流出 + 时序吻合）
- 60-79 分：中等底部信号（部分指标满足）
- 40-59 分：弱信号（量异常但缺乏净流出或时序支撑）
- 0-39 分：无显著底部信号

生成结构化分析报告（见「报告结构」章节）。

## 报告结构

始终使用此模板输出分析报告：

```
## {SYMBOL} CEX 换手量底部信号分析报告
**分析日期**: {date}  **目标资产**: {symbol}  **参考交易所**: {exchange}

### 换手量现状
| 指标 | 数值 |
|------|------|
| 近 {lookback_days} 日日均现货量 | ${current_avg_volume} |
| ETF 稀释系数 | {dilution_factor}（约 {D%} 流量被 {SYMBOL} ETF 吸纳）|
| 调整后等效压力量 | ${adjusted_volume} |
| 历史百分位 | {historical_percentile}%（{extreme_flag 时标注：极端区间}）|

### 历史压力事件对比
| 事件 | 时间 | 彼时日均量 | 当前/彼时 比率 | 信号 |
|------|------|-----------|--------------|------|
| {event} | {dates} | ${benchmark_volume} | {ratio} | {达到/接近/未达到} |

### 资金流向
- CEX 净流向: {netflow_direction}（{netflow_value}/day，过去 {lookback_days} 日均值）
- 交易所储备: {reserve_trend}（{reserve_change_pct} MoM）
- 净流出确认: {true 时 ✅ / false 时 ❌}

### 跨资产时序
- 历史模式: {symbol} {先于/晚于} {comparison_asset} 约 {lead_lag} 触底（{event} 周期）
- 当前信号: {symbol} 量 {已/未} 达极端，{comparison_asset} 历史百分位 {percentile}%
- 时序信号: {current_timing_signal}

### 综合评分
**底部信号得分: {score}/100 — {signal_level}**

触发因子:
{key_factors 列表，满足项 ✅，未满足项 ❌}

**建议**: {recommendation}

**数据局限性**: {data_limitations 列表}
```

**分析示例（基于 @Michael_Liu93 原始案例）**：

```
## ETH CEX 换手量底部信号分析报告
分析日期: 2026-02-23  目标资产: ETH  参考交易所: Binance

### 换手量现状
近7日日均现货量: ~$18.5B | ETF 稀释系数: 0.22 | 调整后等效压力量: ~$22.6B | 历史百分位: 97.3%（极端区间）

### 历史压力事件对比
3AC 暴雷（2022-06）: 彼时 ~$21.8B，比率 1.04 ✅ 已超越
FTX 暴雷（2022-11）: 彼时 ~$19.2B，比率 0.96 ≈ 持平

### 资金流向
CEX 净流向: 净流出（-12,400 ETH/day）| 交易所储备: 持续下降（-2.3% MoM）| 净流出确认: ✅

### 综合评分
底部信号得分: 83/100 — 强信号
建议: 换手量极端值通常对应恐慌性出货尾声，具备较强短期反弹概率。建议分批建仓控制风险。
```

## Risk Parameters

- **适用资产范围**：本 Skill 适合主流资产（ETH、BTC、SOL 等）。小市值代币流动性不足，CEX 量信号失真，不建议使用
- **ETF 稀释仅覆盖 ETH 和 BTC**：其他资产跳过 Step 2，稀释系数记为 0
- **历史事件日期边界为预设值**：不同分析者对事件窗口界定可能不同，分析结论对窗口选择有一定敏感性
- **换手量数据可能含刷量**：建议优先使用 Binance 数据，中小交易所数据可信度较低
- **暗池/OTC 交易量不可观测**：ETF 资金流仅作为机构渠道分流的代理指标，可能低估实际稀释效果
- **历史类比需结合宏观判断**：当前宏观环境（加息周期、监管事件）可能使历史模式的适用性下降，最终入场决策需结合人工判断
- **底部信号不等于绝对底部**：本 Skill 提供"反弹概率较高的统计参考"，不预测绝对底部价格或时间点
- **不提供杠杆/仓位建议**：仓位规模和风控策略由用户自行决定

## 首次安装提示

```
目标用户：中长线交易员、加密货币投研人员、家族办公室/资管机构分析师
使用场景：市场大幅下跌期间，评估特定资产 CEX 换手量是否已进入历史极端区间，辅助判断底部信号强度
如何使用：/cex-volume-anomaly-signal ETH
```
