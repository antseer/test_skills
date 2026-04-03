---
name: "token-resilience-screener"
description: "分析代币相对基准（ETH/BTC）的7日韧性，按 T1/T2/弱势警示分级，输出结构化 Markdown 韧性周报。当用户提到韧性分析、抗跌筛选、领涨标的、本周最强币、resilience scan、outperformer screener、weekly resilience report、哪些币这周抗跌、代币相对强度分析、周度韧性排行时，使用此 Skill。适用于每周末（周日收盘后）定期执行，或大盘明显下行时的临时韧性筛查。"
---

## Overview

以 ETH/BTC 为主基准，对用户提供的代币列表计算7日窗口内的相对强度得分（韧性得分），综合「抗跌超额天数」与「跟涨超额天数」进行加权，将代币分为 T1（强韧性）、T2（弱韧性）、弱势警示三级，输出可直接发布的 Markdown 格式韧性周报。

## Demand Context

方法论来源：@Guolier8（https://x.com/Guolier8/status/2039953528643535218）。原作者在大盘承压一周（2026.03.21–03.27，ETH 周均日涨幅 -1.02%，SOL -1.08%）中，通过识别「涨时超涨、跌时超抗跌」的代币，提炼出相对强度（Relative Strength）分级框架。

韧性的核心定义：**当 BTC/ETH 反弹时涨得更多、回调时跌得更少**。韧性不等于绝对收益为正；弱势市场中负收益但跌幅远小于基准的代币同样具备下周率先反弹的结构性优势。

方法论归属：@Guolier8，本 Skill 基于其公开分析框架构建。

## Features (Data Inputs)

### 必填参数

| 参数名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| symbols | list[string] | 待分析代币列表（CoinGecko ID 格式） | ["tao", "kaito", "hype", "injective", "story", "drift"] |
| start_date | string | 分析起始日（YYYY-MM-DD） | "2026-03-21" |
| end_date | string | 分析结束日（YYYY-MM-DD） | "2026-03-27" |

### 可选参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| benchmark | string | "ethereum" | 主基准代币 CoinGecko ID |
| vs_secondary | string | "solana" | 附加对比基准（辅助参照） |
| t1_min_avg | float | 0.0 | T1 的最低周均日涨幅阈值（%）；0.0 表示周均须为正收益 |
| t2_max_drawdown_ratio | float | 0.5 | T2 条件：周均跌幅不超过基准均值的 N 倍（如 0.5 表示跌幅不超过基准的 50%） |
| weak_drawdown_ratio | float | 2.5 | 弱势警示触发倍数（周均跌幅超过基准 N 倍，如 2.5 表示跌幅超过基准的 2.5 倍） |

### 数据来源

| 数据类型 | 来源 | 备注 |
|---------|------|------|
| 历史日线收盘价（指定日期区间） | CoinGecko Public API `/coins/{id}/market_chart/range` | 免费 API key 覆盖，每代币一次请求 |
| 近7日滚动涨幅（快速近似） | `ant_spot_market_structure` coins_markets，`price_change_percentage="7d"` | 固定滚动窗口，无法精确对齐任意日期区间 |
| 市场情绪 / 叙事标签 | `ant_market_sentiment` coin_detail | 可选，Step 5 叙事增强 |
| 技术指标 RSI（辅助趋势判断） | `ant_market_indicators` rsi | 可选，辅助点评 |

## Entry Conditions

满足以下任一条件时触发：

1. 用户明确请求韧性筛查，提供代币列表和分析周期（如 `/token-resilience-screener tao kaito hype 2026-03-21 2026-03-27`）
2. 用户提及关键词：韧性分析、抗跌筛选、领涨标的、本周最强币、resilience scan、outperformer、weekly resilience report
3. 周期性定时执行：每周日收盘后自动触发，分析过去7天数据
4. 事件驱动：大盘单周跌幅超过5%，需快速识别抗跌标的

## Exit Conditions

以下条件全部满足时 Skill 执行完成：

1. 完成全部6个分析步骤（基准数据 → 代币数据 → 相对强度计算 → 分级分类 → 可选叙事增强 → 周报生成）
2. 所有 symbols 均有韧性分级结果（T1 / T2 / 弱势警示 / 观察区间）
3. 输出完整 Markdown 格式韧性周报，含逐日涨跌幅矩阵、一句话点评、下周重点观察建议

## Action Specification

### Step 1: 获取基准历史日线数据

调用 CoinGecko Market Chart Range API：

```
GET https://api.coingecko.com/api/v3/coins/{benchmark}/market_chart/range
  ?vs_currency=usd
  &from={unix_timestamp(start_date)}
  &to={unix_timestamp(end_date + 1day)}
  &interval=daily
```

对 benchmark 和 vs_secondary 各调用一次。从返回的 `prices` 数组提取日收盘价序列（每24小时最后一个价格点）。

计算每日涨跌幅：
```
r_t = (P_t - P_{t-1}) / P_{t-1} × 100
```

对整个分析周期求均值得到周均日涨幅（benchmark_avg）。

同时统计「基准上涨日集合 up_days」和「基准下跌日集合 down_days」，用于 Step 3 的超额收益拆分。

快速近似方案（当 CoinGecko 历史 API 不可用时）：调用 `ant_spot_market_structure` 的 `coins_markets`，ids=[benchmark, vs_secondary]，price_change_percentage="7d"，取 `price_change_percentage_7d / 7` 作为近似周均日涨幅。注明此为近似值，日期对齐可能偏差1-3个百分点。

### Step 2: 批量获取代币历史日线数据

对 symbols 列表中每个代币，调用相同的 CoinGecko Market Chart Range API：

```
GET https://api.coingecko.com/api/v3/coins/{symbol}/market_chart/range
  ?vs_currency=usd
  &from={unix_timestamp(start_date)}
  &to={unix_timestamp(end_date + 1day)}
  &interval=daily
```

注意速率限制：CoinGecko 免费版约 30 req/min，超过10个代币时建议每批次间隔2秒。

计算每个代币的日涨跌幅序列，构建「代币 × 日期」涨跌幅矩阵。

计算每个代币的周均日涨幅：
```
avg_daily_return_i = mean(r_{i,t} for t in [start_date, end_date])
```

### Step 3: 计算相对强度与韧性得分

以基准日涨幅为参考系，计算每个代币每天的超额收益：

```
超额收益 α_{i,t} = r_{token_i,t} - r_{benchmark,t}
```

识别两类超额日：
- 基准上涨日（r_benchmark_t > 0）中 α_{i,t} > 0 → 「跟涨超额日」
- 基准下跌日（r_benchmark_t < 0）中 α_{i,t} > 0 → 「抗跌超额日」（代币跌幅小于基准，差值为正）

计算韧性得分（范围 0–1）：
```
韧性得分 = 抗跌超额天数 / 基准下跌总天数 × 0.6
         + 跟涨超额天数 / 基准上涨总天数 × 0.4
```

权重设计依据：弱势市场中「跌得少」（0.6权重）比「涨得多」（0.4权重）更能体现真正的机构底部承接力。

同时计算每个代币的超额收益均值和最强单日表现（日期 + 涨幅）。

### Step 4: 分级分类

基于周均日涨幅 + 韧性得分，将代币分为三级（同级内按韧性得分降序排列）：

| 等级 | 条件 |
|------|------|
| T1 强韧性 | 周均日涨幅 >= t1_min_avg（默认 0%）且韧性得分 >= 0.6 |
| T2 弱韧性 | 周均日涨幅 < 0 但 >= 基准均值 × t2_max_drawdown_ratio，且韧性得分 >= 0.4 |
| 弱势警示 | 周均日涨幅 <= 基准均值 × weak_drawdown_ratio（注意基准均值为负时，此条件为跌幅的绝对值超过基准绝对值的 2.5 倍） |
| 观察区间 | 不满足以上任一条件 |

边界情况处理：
- 若基准均值为正（上涨周），T2 和弱势警示条件按基准为负的对称逻辑处理，以弱势警示为跌幅最大的一组
- 代币数据缺失（API 无历史数据）：标记为 N/A，从分级中排除，但在报告末尾列出

### Step 5: 补充叙事标签（可选）

对 T1 和 T2 代币，调用 `ant_market_sentiment`：
- query_type: `coin_detail`
- coin: {symbol}

从返回的情绪标签和热度话题中，匹配当周宏观叙事（AI、DePIN、DeFi、Layer2、Gaming 等），生成叙事标签列表（如 ["AI", "Bittensor生态"]）。

叙事标签为辅助参考，可能滞后于实际叙事切换，须人工验证。

如 `ant_market_sentiment` 不可用，跳过此步骤，在报告中注明叙事标签未获取。

### Step 6: 生成韧性周报

使用以下模板生成完整 Markdown 周报：

```
## 报告结构

# 代币韧性周报 | {start_date} – {end_date}

基准: {benchmark_ticker} 周均日涨幅 {benchmark_avg:+.2f}%  /  {vs_secondary_ticker} {vs_secondary_avg:+.2f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━
韧性 T1 | 周均正收益 + 抗跌超额
━━━━━━━━━━━━━━━━━━━━━━━━━━━
${TICKER}  {avg_daily_return:+.2f}%  韧性 {resilience_score:.2f}  [{narrative_note}]  {watch_flag}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
韧性 T2 | 跌幅显著优于基准
━━━━━━━━━━━━━━━━━━━━━━━━━━━
${TICKER}  {avg_daily_return:+.2f}%  韧性 {resilience_score:.2f}  [{narrative_note}]  {watch_flag}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
弱势警示 | 跌幅超过基准 {weak_drawdown_ratio}x
━━━━━━━━━━━━━━━━━━━━━━━━━━━
${TICKER}  {avg_daily_return:+.2f}%  韧性 {resilience_score:.2f}  [跌幅约基准的 {drawdown_ratio:.1f}x]

────────────────────────────
逐日涨跌幅矩阵（%）
| 代币   | {date1} | {date2} | ... | 周均  |
|--------|---------|---------|-----|-------|
| {benchmark_ticker} | r1 | r2 | ... | avg |
| $TICKER | r1 | r2 | ... | avg |

结论: {一句话点评，点名 T1 代币，建议下周观察是否率先突破}

数据来源: CoinGecko 历史日线 /market_chart/range API
方法论归属: @Guolier8 (https://x.com/Guolier8/status/2039953528643535218)
```

下周重点观察标的规则：T1 代币中韧性得分 >= 0.7 的自动标注「⭐ 下周重点」；T2 代币中韧性得分 >= 0.6 的也可标注，由分析师判断。

## Risk Parameters

### 数据局限性

- CoinGecko 免费版速率限制约 30 req/min；分析超过10个代币时，每批请求间隔2秒，总执行时间可能达1-2分钟
- `coins_markets` 的7日滚动涨幅字段为固定窗口，无法精确对齐任意日期区间；若需精确对齐，必须使用历史日线 API
- 叙事标签来自市场情绪接口，可能滞后于实际叙事切换（尤其新兴叙事）
- 7天分析窗口较短，单日异常事件（上市首周、空投日）会显著拉偏周均值，须结合逐日矩阵解读

### 该 Skill 不做的事

- 不自动发现待分析代币：symbols 列表须由用户提供或预设 watchlist
- 不判断是否应该买入：仅分析过去7天相对强度，不做价格预测
- 不分析链上资金流向和持仓结构（需配合 ant_token_analytics 另行分析）
- 不支持超过30天的长周期分析（历史 API 数据获取成本及速率限制）
- 不自动识别单日异动的催化剂（如某代币单日 +21% 的具体原因需人工核查）

### 需要人工判断的环节

- 代币 watchlist 的初始选择（建议预设主流监控列表 + 用户自定义）
- 极端单日事件的定性解读（单日异常暴涨是否有实质性催化剂）
- T2 与弱势边界参数调优（建议首月每周复核分级结果，校准 t2_max_drawdown_ratio 和 weak_drawdown_ratio）
- 周报一句话点评的叙事准确性（机器生成的叙事标签需人工 review）

### 免责声明

分析方法论归属原作者 @Guolier8，本 Skill 基于其公开框架构建。分析结果基于历史价格数据，不能预测未来走势。不构成投资建议。

## 首次安装提示

```
目标用户：投研人员、主观多头交易员、量化策略师
使用场景：每周末（周日收盘后）分析过去7天，识别下周率先反弹的潜在领涨标的
如何使用：/token-resilience-screener tao kaito hype injective story drift 2026-03-21 2026-03-27
```
