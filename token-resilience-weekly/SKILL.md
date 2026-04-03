---
name: "token-resilience-weekly"
description: "生成代币韧性周报，以 ETH/SOL 为基准筛选大盘承压期间表现抗跌的代币并按韧性分级。当用户提到韧性周报、抗跌分析、resilience report、token resilience、相对强度筛选、代币强弱对比、谁在扛住大盘下跌、哪些币比大盘强，或者想知道一组代币中谁最抗跌、谁最弱势时，使用此 Skill。也适用于每周定期执行（周日/周一）或大盘明显回调后的复盘场景。"
---

## Overview

以 ETH/SOL 等基准代币的周均日涨跌幅为参照，逐一比较 watchlist 中目标代币的同期表现，按周均超额收益、下跌天抗跌度、上涨天跟涨度三个维度进行韧性分级（T1/T2/弱势/中性），并输出逐日行为标注和结构化周报。

## Demand Context

源自 @Guolier8 的相对强度筛选框架：当大盘（ETH/SOL）周均日跌幅为 -1% 左右时，逐币比较目标代币的同期表现。周均日收益为正的代币标记为韧性 T1（如 TAO +2.43%），微跌但远优于基准的标记为 T2（如 HYPE -0.28%），跌幅显著超过基准的标记为弱势警示（如 STORY -4.05%）。除周均值外，还关注逐日行为模式——如"跌时极小、涨时跟上"的教科书级韧性特征。

方法论归属：@Guolier8，本 Skill 基于其公开分析框架构建。

## Features (Data Inputs)

### 必填参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| watchlist | list[string] | 待分析的代币列表（symbol） | ["TAO","SPEC","KAITO","HYPE","IO","STORY","DRIFT"] |

### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| benchmarks | list[string] | ["ETH","SOL"] | 基准代币，用于计算市场均值 |
| time_range | string | "7d" | 分析时间窗口，支持 "7d" 或 "2026-03-21~2026-03-27" 格式 |
| t1_threshold | float | 0.0 | T1 韧性阈值：周均日收益 >= 此值为 T1 |
| t2_threshold_ratio | float | 0.5 | T2 韧性阈值：跌幅 < 基准均值绝对值 x 此比例 |
| weak_threshold_ratio | float | 2.0 | 弱势警示阈值：跌幅 > 基准均值绝对值 x 此倍数 |

## Entry Conditions

满足以下任一条件时触发本 Skill：

1. 用户主动请求韧性周报（如 `/token-resilience-weekly ["TAO","KAITO","HYPE"]`）
2. 每周定期执行周期到达（推荐周日或周一）
3. 大盘出现明显回调（BTC/ETH 周内跌幅超过 5%），需评估哪些代币扛住了下跌

## Exit Conditions

满足以下条件时 Skill 执行完成：

1. 已完成全部 6 个分析步骤
2. 已输出所有代币的韧性分级结果（T1 / T2 / 弱势 / 中性）
3. 已输出结构化周报（含逐日涨跌幅矩阵、关键日标注、总结叙述）

## Action Specification

### Step 1: 获取基准代币行情数据

调用 `ant_spot_market_structure`，参数：
- query_type: `coins_markets`
- ids: benchmarks 列表对应的 CoinGecko id（ETH -> ethereum, SOL -> solana）
- sparkline: true

从返回的 sparkline 数据中提取近 7 天的价格序列。计算每个基准代币的每日涨跌幅：

```
daily_change_pct = (当日价格 - 前日价格) / 前日价格 * 100%
```

计算周均日涨跌幅 = 所有日涨跌幅的平均值。

记录：每个基准代币的 `daily_changes[]` 和 `avg_daily_change`。

计算基准均值 `benchmark_avg` = 所有基准代币 `avg_daily_change` 的平均值。

sparkline 数据的时间粒度可能不是精确的每日收盘价，结果中注明"数据基于 sparkline 近似值，与 CoinGecko 官方每日收盘价可能存在细微差异"。

### Step 2: 获取目标代币行情数据

对 watchlist 中每个代币，调用 `ant_spot_market_structure`，参数：
- query_type: `coins_markets`
- ids: 代币对应的 CoinGecko id
- sparkline: true

用与 Step 1 相同的方法计算每个目标代币的每日涨跌幅和周均日涨跌幅。

需要将用户输入的 symbol（如 TAO、KAITO）映射到 CoinGecko id。常见映射：
- TAO -> bittensor
- SPEC -> spectral
- KAITO -> kaito
- HYPE -> hyperliquid
- IO -> io-net
- STORY -> story-protocol
- DRIFT -> drift-protocol

如果映射不确定，先调用 `ant_spot_market_structure` 的 `coins_list` 查询确认。

记录：每个目标代币的 `daily_changes[]` 和 `avg_daily_change`。

### Step 3: 韧性指标计算

对每个目标代币，基于 Step 1 和 Step 2 的数据计算三个韧性维度：

1. **周均超额收益** = 代币 `avg_daily_change` - `benchmark_avg`

2. **下跌天抗跌度**：筛选基准下跌的日期（benchmark_avg 当日为负），计算代币在这些天的平均跌幅与基准平均跌幅的比值。比值 < 1 表示抗跌，比值越小越抗跌。

3. **上涨天跟涨度**：筛选基准上涨的日期，计算代币在这些天的平均涨幅与基准平均涨幅的比值。比值 > 1 表示弹性强。

4. **韧性综合评分** = 周均超额收益 x 0.5 + (1/抗跌度) x 0.3 + 跟涨度 x 0.2（归一化到 0-100）

记录：`excess_return`、`downside_ratio`、`upside_ratio`、`resilience_score`

### Step 4: 韧性分级

根据阈值将代币分入四个等级：

- **韧性 T1**：`avg_daily_change` >= `t1_threshold`（默认 0，即周均日收益为正）
- **韧性 T2**：`avg_daily_change` < 0，但 `|avg_daily_change|` < `|benchmark_avg|` x `t2_threshold_ratio`
- **弱势警示**：`|avg_daily_change|` > `|benchmark_avg|` x `weak_threshold_ratio`
- **中性**：不属于以上任何类别

在每个等级内部，按 `resilience_score` 从高到低排序。

### Step 5: 逐日行为标注

对 T1 和 T2 代币重点分析，对弱势代币也进行标注：

- 标注单日涨幅 > 5% 的异动日，附带日期和涨幅值
- 标注连续正收益天数 >= 2 的反弹序列
- 对弱势代币标注连续下跌天数和反弹力度（反弹日涨幅是否超过下跌日跌幅的 50%）
- 识别"教科书级韧性"模式：基准下跌日代币跌幅极小（< 基准跌幅 x 0.3）且基准上涨日代币涨幅 >= 基准涨幅

### Step 6: 综合评估与输出

汇总所有分析结果，使用以下模板生成结构化周报：

```
# 代币韧性周报 | {report_period}

## 基准行情
{benchmark_name}: 周均日跌 {avg_daily_change}%（逐一列出每个基准）

## 韧性 T1（正收益）
（按 resilience_score 从高到低排列）
  ${symbol}  {avg_daily_change}%  | {daily_behavior_note}

## 韧性 T2（微跌但优于基准）
  ${symbol}  {avg_daily_change}%  | {daily_behavior_note}

## 弱势警示
  ${symbol}  {avg_daily_change}%  | 跌幅约 ETH 的 {ratio} 倍，{weakness_note}

## 中性表现
  ${symbol}  {avg_daily_change}%

## 逐日涨跌幅矩阵
| 代币 | Day1 | Day2 | Day3 | Day4 | Day5 | Day6 | Day7 | 周均 |
|------|------|------|------|------|------|------|------|------|
（所有代币 + 基准）

## 结论
总结本周韧性赢家、弱势标的、下周关注要点。

## 免责声明
本分析基于 @Guolier8 的相对强度筛选方法论，不构成投资建议。
韧性是回顾性指标，不能预测未来走势。
数据基于 MCP sparkline 近似值，与精确每日收盘价可能存在细微差异。
```

## Risk Parameters

### 数据局限性

- sparkline 数据的时间粒度可能为小时级而非精确的每日收盘价，会导致涨跌幅计算与 CoinGecko 官方数据存在偏差
- 小市值代币可能存在流动性不足导致的价格失真，单笔大额交易就能造成几个百分点的波动
- 7 天窗口较短，单日异常事件（如某币单日 +21%）会显著拉偏周均值，解读时需结合逐日矩阵

### 该 Skill 不做的事

- 不预测未来走势——韧性是回顾性指标，T1 代币下周可能转弱
- 不解释韧性的原因（如"AI 叙事驱动"需要人工判断）
- 不自动推荐应该追踪哪些代币（watchlist 需人工维护）
- 不替代深度基本面分析

### 需要人工判断的环节

- watchlist 的选择和维护（哪些代币值得追踪）
- 韧性原因的归因分析（叙事、资金面、技术面等）
- T1 代币是否值得加仓的投资决策
- 弱势代币是否为"假摔"（短期洗盘）还是真正走弱的判断
- 单日异常事件是否为一次性事件（如空投、漏洞）还是持续趋势

## 首次安装提示

```
目标用户：投研人员、中长线交易员、基金组合管理者
使用场景：每周定期执行（推荐周日/周一），或在大盘出现明显回调时触发
如何使用：/token-resilience-weekly ["TAO","SPEC","KAITO","HYPE","IO","STORY","DRIFT"]
```
