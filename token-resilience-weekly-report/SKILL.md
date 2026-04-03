---
name: "token-resilience-weekly-report"
description: "生成代币韧性周报，通过双向贝塔不对称性分析量化哪些代币在大盘承压周内「涨时超涨、跌时超抗跌」，按 T1/T2/弱势/中性分级并输出结构化 Markdown 报告。当用户提到韧性周报、本周哪些币抗跌、代币韧性分析、韧性排行、resilience report、which tokens held up、token strength analysis、market resilience scan、双向 alpha、上涨超额、下跌少跌时，使用此 Skill。适用于每周定期复盘（周一复盘上周）或大盘单周跌幅超过 5% 的事件驱动触发场景。"
---

## Overview

以 BTC/ETH/SOL 为市场基准，计算各目标代币在大盘上涨日的超额收益（upside_alpha）和大盘下跌日的超额抗跌量（downside_alpha），两者之和为韧性得分（resilience_score），据此将代币分入 T1/T2/弱势警示/中性四个等级，生成结构化 Markdown 周报。

## Demand Context

方法论来源：@Guolier8（https://x.com/Guolier8/status/2039953528643535218）。原作者在大盘承压一周内（2026.03.21–03.27，ETH 周均日收益 -1.02%，SOL -1.08%）识别出超越市场的代币韧性，核心定义为"当 BTC/ETH 反弹时涨得更多、回调时跌得更少"。

这是一种**双向贝塔不对称性**分析。真正有韧性的代币不仅净收益跑赢，还在上涨日超涨、下跌日超抗跌，形成"上有弹性、下有支撑"的格局。T1 为周均正收益且双向均跑赢；T2 为至少一侧跑赢；弱势警示为跌幅相对基准超过设定倍数阈值。

方法论归属：@Guolier8，本 Skill 基于其公开分析框架构建。

## Features (Data Inputs)

### 必填参数

| 参数名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| symbols | list[str] | 待分析代币列表（ticker） | ["TAO", "SPEC", "KAITO", "HYPE", "IO", "STORY", "DRIFT"] |

### 可选参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| benchmarks | list[str] | ["BTC", "ETH", "SOL"] | 市场基准代币 |
| week_start | date | 上周一 | 分析周开始日期（ISO 格式，如 "2026-03-21"） |
| week_end | date | 上周日 | 分析周结束日期（ISO 格式，如 "2026-03-27"） |
| t1_min_return | float | 0.0 | T1 门槛：周均日收益最低值（%） |
| t2_min_return | float | -0.5 | T2 门槛：允许的最小周均日收益（%） |
| weak_multiplier | float | 2.0 | 弱势警示门槛（相对基准超跌倍数） |
| include_narrative | bool | false | 是否为 T1 代币查询叙事催化剂注释 |

## Entry Conditions

满足以下任一条件时触发：

1. 用户明确请求韧性周报（如 `/token-resilience-weekly-report TAO KAITO HYPE IO STORY`）
2. 周期性执行：每周一复盘上一周（周一触发，分析上周一至上周日）
3. 事件驱动：大盘单周跌幅超过 5%，需快速识别抗跌标的

## Exit Conditions

以下条件全部满足时 Skill 执行完成：

1. 完成全部 6 个分析步骤（基准数据获取 → 代币数据获取 → 韧性指标计算 → 代币分级 → 可选叙事识别 → 报告生成）
2. 输出所有代币的韧性分级（T1 / T2 / 弱势警示 / 中性）
3. 输出完整格式化周报（含分级列表、关键日期标注、一句话结论）

## Action Specification

### Step 1: 获取基准市场每日表现

调用 `ant_spot_market_structure`，参数：
- query_type: `coins_markets`
- ids: benchmarks 对应的 CoinGecko ID（BTC→bitcoin, ETH→ethereum, SOL→solana）
- include_sparkline_7d: true
- vs_currency: "usd"

从 sparkline 数据提取近 7 天日收盘价（每 24 小时取最后一个价格点近似）。计算：

```
daily_return[d] = (price[d] - price[d-1]) / price[d-1] × 100
benchmark_avg   = mean(daily_return[0..6])
up_days         = {d | BTC daily_return[d] > 0}   ← 市场上涨日
down_days       = {d | BTC daily_return[d] < 0}   ← 市场下跌日
bench_up_avg    = mean(ETH_daily_return[d] for d in up_days + BTC_daily_return[d] for d in up_days) / 2
bench_down_avg  = mean(ETH_daily_return[d] for d in down_days + BTC_daily_return[d] for d in down_days) / 2
```

输出：各基准每日收益序列、市场上涨日/下跌日集合、各基准周均日收益。

注：sparkline 为小时级近似，与 CoinGecko 标准每日收盘价可能存在 1-3% 误差，报告中注明。

### Step 2: 获取各代币每日价格数据

合并进同一批次的 `ant_spot_market_structure` 调用，减少请求次数：
- query_type: `coins_markets`
- ids: symbols 对应的 CoinGecko ID 列表
- include_sparkline_7d: true
- price_change_percentage: ["7d", "24h"]

常见 ticker → CoinGecko ID 映射（内置）：

| ticker | CoinGecko ID |
|--------|--------------|
| TAO | bittensor |
| SPEC | spectral |
| KAITO | kaito |
| HYPE | hyperliquid |
| IO | io-net |
| STORY | story-protocol |
| DRIFT | drift-protocol |
| BTC | bitcoin |
| ETH | ethereum |
| SOL | solana |

如果 ticker 不在上述映射中，调用 `ant_meme`（query_type: `search_pairs`, query: ticker）查询 CoinGecko ID。

用与 Step 1 相同的方法提取每日收盘价并计算每日涨跌幅。

### Step 3: 计算韧性核心指标

对每个目标代币计算双向贝塔不对称性：

```
up_days_return_token   = mean(token_daily_return[d] for d in up_days)
down_days_return_token = mean(token_daily_return[d] for d in down_days)

upside_alpha   = up_days_return_token - bench_up_avg     # 正值 = 上涨日跑赢
downside_alpha = down_days_return_token - bench_down_avg # 正值 = 下跌日少跌（因两者均为负数，少跌则差值为正）

resilience_score  = upside_alpha + downside_alpha
weekly_avg_return = mean(token_daily_return[0..6])
```

upside_alpha 和 downside_alpha 的直观解释：
- upside_alpha > 0：大盘上涨时，该代币涨得比基准更多
- downside_alpha > 0：大盘下跌时，该代币跌得比基准更少
- 两者均正为真正的双向韧性

### Step 4: 代币韧性分级

按以下规则分级（同一等级内按 resilience_score 降序排列）：

- **T1 韧性最强**：weekly_avg_return >= t1_min_return 且 resilience_score > 0（涨跌双向均跑赢）
- **T2 轻微跑赢**：weekly_avg_return >= t2_min_return 且（upside_alpha > 0 或 downside_alpha > 0）（至少一侧跑赢）
- **弱势警示**：weekly_avg_return <= benchmark_avg × weak_multiplier（跌幅相对基准超过倍数阈值，注意 benchmark_avg 为负值时乘以倍数使结果更负）
- **中性**：不满足以上任何条件的其余代币

### Step 5: （可选）叙事催化剂识别

仅当 include_narrative=true 时执行。

对每个 T1 代币调用 `ant_market_sentiment`：
- query_type: `coin_detail`
- coin: {symbol}

从返回的情绪标签和热度话题中，识别分析周内是否有异常正面情绪信号，生成简短叙事注释（如 "AI 叙事独立行情"、"DePIN 板块护盘"、"空投预期支撑"）。

叙事注释由 AI 生成，可能存在误判，仅供参考，需人工验证。

### Step 6: 生成综合韧性周报

使用以下模板生成完整 Markdown 周报：

```
## 报告结构模板

# 代币韧性周报 | {week_start}–{week_end}

大盘承压一周。{benchmark_summary（各基准周均日收益）}，多数山寨跟跌且放大了跌幅。

---

## 韧性 T1 — 超额正收益，涨跌双向跑赢

${symbol}  周均: {weekly_avg_return:+.2f}% | 韧性得分: {resilience_score:+.2f} | 上涨超额: {upside_alpha:+.2f}% | 下跌少跌: {downside_alpha:+.2f}%
           {key_date_highlight}  {narrative_note（如有）}

## 韧性 T2 — 轻微跑赢，至少一侧超额

$symbol  周均: {weekly_avg_return:+.2f}% | {一侧超额说明}

## 弱势警示 — 跌幅超市场 {weak_multiplier}x

$symbol  周均: {weekly_avg_return:+.2f}% | 跌幅约基准的 {ratio:.2f}× | {weakness_note}

## 中性表现

$symbol  周均: {weekly_avg_return:+.2f}%

---

## 逐日涨跌幅矩阵（%）

| 代币   | Day1 | Day2 | Day3 | Day4 | Day5 | Day6 | Day7 | 周均  |
|--------|------|------|------|------|------|------|------|-------|
| ETH    | ...  | ...  | ...  | ...  | ...  | ...  | ...  | -1.02 |
| SOL    | ...  | ...  | ...  | ...  | ...  | ...  | ...  | -1.08 |
| $TAO   | ...  | ...  | ...  | ...  | ...  | ...  | ...  | +2.43 |
（所有分析代币均列出）

---

一句话结论：以 CoinGecko 每日收盘价（sparkline 近似）计算涨跌幅，当 BTC/ETH 反弹时涨得更多、回调时跌得更少 — 这就是「韧性」。本周 {T1 代币列表} 是这个定义下的赢家。下周重点观察它们能否在企稳后率先突破。

数据来源：CoinGecko 日收盘价（通过 ant_spot_market_structure sparkline 近似，与精确日收盘价可能存在 1–3% 误差）
```

## Risk Parameters

### 数据局限性

- sparkline 数据为小时级近似，与 CoinGecko 标准每日收盘价存在轻微误差（1-3%），影响精确分级判断
- 小市值/低流动性代币价格可能因单笔大额交易失真，出现虚假韧性或虚假弱势信号
- 7 天窗口较短，单日异常事件（如代币上市首周、空投日）会显著拉偏周均值，须结合逐日矩阵解读
- 跨时区日收盘价取样点可能导致各代币存在数小时偏差

### 该 Skill 不做的事

- 不预测未来走势：韧性是回顾性描述性指标，T1 代币下周可能立即转弱
- 不深度解释韧性原因：叙事注释为可选辅助，不保证准确性
- 不提供链上资金流向分析（需配合 ant_smart_money 等其他工具）
- 不覆盖未上架 CoinGecko 的长尾代币
- 不支持跨周累积分析（当前窗口固定 7 天）

### 需要人工判断的环节

- watchlist 的选择和维护（哪些代币值得纳入分析）
- 叙事催化剂注释的准确性验证（AI 生成叙事可能误判板块归因）
- 异常单日暴涨的真实性评估（防止流动性极低导致的虚假信号）
- T1/T2 分级阈值的周期性校准（不同市场环境下最优参数不同）
- T1 代币是否值得加仓的最终投资决策

### 免责声明

本分析方法论归属原作者 @Guolier8，Skill 基于其公开框架构建。分析结果基于历史数据，不能预测未来走势。不构成投资建议。

## 首次安装提示

```
目标用户：投研人员、中长线交易员、量化基金分析师
使用场景：每周一复盘上周大盘承压期间的代币韧性，或在大盘单周跌幅 >5% 后事件驱动触发
如何使用：/token-resilience-weekly-report TAO SPEC KAITO HYPE IO STORY DRIFT
```
