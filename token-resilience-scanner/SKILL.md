---
name: "token-resilience-scanner"
description: "大盘承压周期中，扫描候选代币的双向 beta 韧性并生成分层周报。当用户提到代币韧性分析、韧性周报、抗跌筛选、resilience scan、token resilience、which tokens held up、alpha in down market、大盘下行谁在抗跌、哪些代币跑赢基准，或者想识别「大盘反弹时涨得更多、回调时跌得更少」的代币时，使用此 Skill。适用于每周收盘后定期执行，也可在大盘急跌后临时触发快速定位抗跌板块。"
---

## Overview

以 ETH/SOL 等基准代币的日收益序列为参照，对候选代币计算上涨日超额（up_alpha）和下跌日超额（down_alpha），合成综合韧性分，按 T1/T2/弱势三档分层输出，并生成带叙事标签和异动标注的标准化 Markdown 周报。

## Demand Context

源自 @Guolier8 的 alpha 挖掘框架：在 2026.03.21–03.27 大盘承压周（ETH 周均日收益 -1.02%，SOL -1.08%），通过逐日追踪代币涨跌幅，识别「大盘反弹时涨得更多、回调时跌得更少」的双向 beta 韧性代币。核心指标为 CoinGecko 每日收盘价计算的周均日收益率，分层逻辑为 T1（周均正收益）、T2（微跌但远优于基准）、弱势警示（跌幅约基准 3–4 倍、反弹乏力）。

方法论归属：@Guolier8（https://x.com/Guolier8/status/2039953528643535218），本 Skill 基于其公开分析框架构建。

## Features (Data Inputs)

### 必填参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| symbols | list[str] | 待分析代币列表（CoinGecko ID 或 ticker） | ["tao","kaito","hype","spec","io","story","drift"] |

### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| benchmark_symbols | list[str] | ["ethereum","solana"] | 大盘基准代币（CoinGecko ID） |
| time_range | str | "7d" | 分析周期（如 "7d"、"14d"） |
| end_date | str | 今日 | 分析结束日期，格式 YYYY-MM-DD |
| top_n | int | 5 | T1/T2 强势标的输出上限 |
| weak_n | int | 3 | 弱势警示标的输出上限 |
| min_daily_volume_usd | float | 1000000 | 流动性过滤阈值（USD），低于此值跳过 |

## Entry Conditions

满足以下任一条件时触发本 Skill：

1. 用户主动请求韧性扫描（如 `/token-resilience-scanner symbols=["TAO","KAITO","HYPE","IO"] time_range=7d`）
2. 每周定期执行周期到达（推荐周日/周一）
3. 大盘出现急跌（BTC/ETH 单日跌幅超过 5%），需快速定位抗跌板块
4. 用户提及"谁在抗跌"、"alpha in down market"等触发词

## Exit Conditions

满足以下条件时 Skill 执行完成：

1. 已完成全部 6 个分析步骤
2. 已输出所有代币的韧性分级（T1 / T2 / 弱势 / 未分级）
3. 已输出完整 Markdown 周报，含分层表格、下周观察建议和一句话结论

## Action Specification

### Step 1: 获取大盘基准日收益率

调用 `ant_spot_market_structure`，参数：
- query_type: `coins_markets`
- ids: benchmark_symbols（如 `["ethereum","solana"]`）
- vs_currency: `"usd"`
- sparkline: true

从 sparkline 数据中提取近 time_range 天的价格序列。对每个基准代币按日计算：

```
daily_return[t] = (price[t] - price[t-1]) / price[t-1]
```

计算两个基准代币的日收益均值作为大盘日收益序列 `market_return[t]`，以及 `market_avg_daily_return`。

按日标记：`up_days`（market_return > 0）、`down_days`（market_return < 0）。

注意：若 sparkline 粒度不足（非精确每日收盘价），在报告中标注"数据基于 sparkline 近似值"。

记录：`market_return[]`、`up_days[]`、`down_days[]`、`market_avg_daily_return`

### Step 2: 获取候选代币日收益率

对 symbols 列表中每个代币，调用 `ant_spot_market_structure`：
- query_type: `coins_markets`
- ids: 代币 CoinGecko ID
- vs_currency: `"usd"`
- sparkline: true

常见 ticker → CoinGecko ID 映射：
- TAO → bittensor
- SPEC → spectral
- KAITO → kaito
- HYPE → hyperliquid
- IO → io-net
- STORY → story-protocol
- DRIFT → drift-protocol

如果映射不确定，调用 `coins_list` 查询确认。

从返回数据中提取：
- `total_volume`（日均 USD 交易量用于流动性过滤）
- sparkline 价格序列 → 计算 `daily_return[t]`

流动性过滤：若代币日均 USD 交易量 < `min_daily_volume_usd`，标注「流动性不足，跳过」，不纳入后续分析。

记录每个代币的 `daily_return[]`、`avg_daily_return`、异动日（单日涨跌幅绝对值 > 8%）。

### Step 3: 计算双向韧性指标

基于 Step 1 的大盘日分类和 Step 2 的代币日收益，本地计算（无需新 API 调用）：

**上涨日超额（up_alpha）：**
```
up_alpha = mean(token_return[t] - market_return[t] for t in up_days)
```
值越高表示大盘反弹时该代币表现越强。

**下跌日超额（down_alpha）：**
```
down_alpha = mean(token_return[t] - market_return[t] for t in down_days)
```
值越高（越接近 0 或为正）表示大盘下跌时跌得越少。

**综合韧性分（resilience_score）：**
```
resilience_score = up_alpha * 0.5 + down_alpha * 0.5
```

记录：每个代币的 `{symbol, avg_daily_return, up_alpha, down_alpha, resilience_score}`

### Step 4: 分层分类与异动标注

按以下规则分层（优先级从上到下）：

- **T1（强韧性）**：`avg_daily_return > 0` 且 `resilience_score > 0`，取 resilience_score 最高的 top_n 名
- **T2（中等韧性）**：`avg_daily_return < 0` 但 `|avg_daily_return| < |market_avg_daily_return| * 0.5`，且 `down_alpha > 0`
- **弱势警示**：`avg_daily_return < market_avg_daily_return * 2`（跌幅超过大盘 2 倍），取跌幅最深的 weak_n 名
- **未分级（中性）**：不满足上述任一条件

异动日标注：单日涨跌幅绝对值 > 8% 的日期，记录日期 + 涨跌幅字符串（如 "3/24 +8.49%"）。

### Step 5: 补充叙事标签（可选增强）

对 T1/T2 代币，尝试调用 `ant_market_sentiment`：
- query_type: `coin_detail`
- coin: symbol

提取情绪分和话题热度，补充叙事板块标签（AI 叙事、DeFi/Perp、InfoFi、DePIN 等）。

降级处理：若 `ant_market_sentiment` 返回错误或未覆盖该代币，手动根据已知叙事标注（参考：TAO=AI叙事、KAITO=InfoFi、HYPE=DeFi/Perp、IO=DePIN、SPEC=基础设施）。跳过情绪数据，仅输出叙事板块标签。

可选资金流向验证：调用 `ant_fund_flow`，query_type: `exchange_netflow`，asset=symbol。主要覆盖主流资产，山寨币覆盖度待确认，不可用时省略该维度。

### Step 6: 综合评估与报告生成

汇总全部结果，使用以下模板输出完整 Markdown 周报：

```
## 代币韧性周报 | {report_period}

**大盘环境**: ETH 周均日收益 {eth_avg}%，SOL {sol_avg}%，大盘整体{承压/震荡/上行}

---

### 韧性 T1（强势，周均正收益）

| 代币 | 周均日收益 | 上涨日超额 | 下跌日超额 | 韧性分 | 异动日 | 叙事 |
|------|-----------|-----------|-----------|-------|--------|------|
| ${symbol} | {avg_daily_return}% | {up_alpha}% | {down_alpha}% | {resilience_score} | {notable_days} | {narrative} |

### 韧性 T2（跑赢大盘，跌幅极小）

| 代币 | 周均日收益 | 下跌日超额 | 异动日 | 叙事 |
|------|-----------|-----------|--------|------|
| ${symbol} | {avg_daily_return}% | {down_alpha}% | {notable_days} | {narrative} |

### 弱势警示

| 代币 | 周均日收益 | vs 大盘倍数 | 信号 |
|------|-----------|------------|------|
| ${symbol} | {avg_daily_return}% | {ratio}× | {weakness_note} |

---

**下周重点观察**: {next_week_watchlist}

**一句话结论**: 以 CoinGecko 每日收盘价衡量，{conclusion}

---

*方法论归属：@Guolier8。本报告基于历史数据，不构成投资建议。*
*数据基于 Antseer MCP 接口，历史价格使用 sparkline 近似值。*
```

若某分层为空（如无代币达到 T1 标准），输出"本周无符合条件的 T1 代币"而非省略该章节。

## Risk Parameters

### 数据局限性

- sparkline 数据时间粒度可能为小时级而非精确每日收盘价，与 CoinGecko 官方数据存在细微偏差；7 天窗口短，单日异动事件（如 +21%）会显著拉偏周均值
- `ant_market_sentiment` 覆盖币种有限，长尾代币可能返回空数据，需降级到手动叙事标注
- `ant_fund_flow` 主要覆盖 BTC/ETH 等主流资产，山寨币资金流向数据覆盖度不确定
- 流动性过滤基于当前快照的 24h 交易量，若历史某日流动性异常，可能造成误判

### 该 Skill 不能做什么

- 不预测未来价格走势；韧性为回顾性指标，T1 代币下周可能转弱
- 不自动扩展候选池（watchlist 需用户显式传入）
- 不分析 DEX/链上流动性深度，不评估滑点和执行成本
- 不替代基本面研究；叙事标签为辅助信息，不代表项目质量
- 不给出仓位建议；T1/T2 分级仅提供相对强弱排名

### 需要人工判断的环节

- 初始候选代币池的构建（哪些代币值得纳入观察）
- 叙事板块标签的准确性验证（尤其新兴叙事）
- T1 标的是否值得建仓的最终投资决策
- 弱势代币是「假摔/短期洗盘」还是真正走弱的判断

## 首次安装提示

```
目标用户：投研人员、量化策略师、高频关注山寨轮动的交易员
使用场景：每周收盘后（周日/周一）定期执行，或大盘急跌后临时触发定位抗跌板块
如何使用：/token-resilience-scanner symbols=["TAO","KAITO","HYPE","IO","STORY","DRIFT"] time_range=7d
```
