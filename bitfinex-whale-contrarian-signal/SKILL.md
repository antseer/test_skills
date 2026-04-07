---
name: "bitfinex-whale-contrarian-signal"
description: "监控 Bitfinex 保证金多头仓位的极端变动，识别巨鲸反向指标信号。当用户提到 Bitfinex 巨鲸、保证金多头、margin long、whale contrarian signal、巨鲸反指、巨鲸抄底、绿叶多头仓位、Bitfinex whale signal、margin long contrarian、巨鲸仓位，或者想判断 Bitfinex 大户加仓/减仓是否值得跟随时，触发此 Skill。也适用于定期巡检 Bitfinex 保证金仓位变化率，或在 BTC 出现剧烈波动后检查巨鲸仓位异动。"
metadata:
  generated_at: "2026-04-07 12:15:00"
---

## Overview

监控 Bitfinex 保证金多头仓位（margin long position）的 30 日变化率，当变化率出现极端偏离（暴涨 >15% 或暴跌 <-10%）时触发反向交易信号，并输出历史回测胜率和操作建议。

方法论来源：@leifuchen（推文 https://x.com/leifuchen/status/2041145516637966508）

---

## Demand Context

原作者对 Bitfinex 保证金多头仓位与 BTC 价格关系进行了 1838 天（2021-03-24 至 2026-04-04）的系统性量化研究，发现两个核心结论：

1. **日常仓位波动无预测力**：滞后交叉相关分析表明 BTC 价格领先仓位变化约 5 天（r = -0.61），仓位是价格的跟随者，不是预测者。样本外 R2 反而下降，线性模型的预测力是过拟合产物。

2. **极端仓位变动是可靠的反向指标**：仓位 30 日涨幅超 15%（巨鲸抄底）后 BTC 30 天内平均下跌 5.4%，做空胜率 69%；仓位 30 日跌幅超 10%（巨鲸止盈）后 BTC 14 天内平均上涨 4.1%，做多胜率 62%。该信号在样本外测试中完美复现。

核心逻辑：巨鲸抄底时做空，巨鲸止盈时做多。信号平均每年触发不到 5 次，适合作为辅助确认而非主策略。

方法论归属：@leifuchen，本 Skill 基于其公开量化研究构建。

---

## Features (Data Inputs)

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `symbol` | string | 否 | `BTC` | 目标币种（当前仅支持 BTC） |
| `exchange` | string | 否 | `Bitfinex` | 目标交易所 |
| `lookback_days` | int | 否 | `30` | 仓位变化率回看天数 |
| `threshold_long` | float | 否 | `15` | 抄底信号阈值：仓位涨幅超过此值(%)触发做空信号 |
| `threshold_short` | float | 否 | `10` | 止盈信号阈值：仓位跌幅超过此值(%)触发做多信号 |
| `forward_window` | string | 否 | `7d,14d,30d` | 信号触发后的观察窗口（逗号分隔） |
| `data_start_date` | string | 否 | 自动取最早可用 | 分析数据起始日期 |

**MCP 数据源**：

| 步骤 | MCP 工具 | query_type | 备注 |
|------|----------|------------|------|
| BTC 当前价格 | `ant_spot_market_structure` | `simple_price` | ids=bitcoin |
| BTC 历史价格 | `ant_futures_market_structure` | `futures_price_history` | symbol=BTC |
| Bitfinex 多空比 | `ant_futures_market_structure` | `futures_long_short_ratio` | 辅助参考 |
| 资金费率 | `ant_futures_market_structure` | `futures_funding_rate_aggregated` | 辅助信号 |
| 聚合 OI | `ant_futures_market_structure` | `futures_oi_aggregated` | 辅助信号 |
| 交易所净流量 | `ant_fund_flow` | `exchange_netflow` | 辅助参考 |
| 鲸鱼转账 | `ant_fund_flow` | `centralized_exchange_whale_transfer` | 辅助参考 |

**外部数据源（核心数据，Antseer MCP 不直接覆盖）**：

| 数据 | 来源 | 接口 |
|------|------|------|
| Bitfinex 保证金多头仓位 | Bitfinex API | `GET /v2/stats1/pos.size:1m:tBTCUSD:long/hist` |
| 备选：TradingView 图表 | TradingView | `BITFINEX:BTCUSDLONGS` |

---

## Entry Conditions

满足以下任一条件时触发本 Skill：

1. 用户主动请求 Bitfinex 巨鲸信号检测（如 `/bitfinex-whale-contrarian-signal` 或 `/bitfinex-whale-contrarian-signal BTC`）
2. 用户提到 Bitfinex 巨鲸仓位、保证金多头、margin long 等关键词
3. 定期巡检：建议每日执行一次，检查 30 日仓位变化率是否接近或超过阈值
4. BTC 价格剧烈波动后，评估巨鲸仓位变化是否出现极端信号

---

## Exit Conditions

满足以下条件时 Skill 执行完成：

1. 已完成 8 个分析步骤（从数据获取到综合评估）
2. 已输出信号状态判定（bearish_contrarian / bullish_contrarian / none）
3. 已输出结构化报告，包含历史胜率统计和操作建议

---

## Action Specification

### Step 1: 获取 Bitfinex 保证金多头仓位数据

获取 Bitfinex BTC 保证金多头仓位的历史时间序列。

数据获取方式：调用 Bitfinex 公开 API：
```
GET https://api-pub.bitfinex.com/v2/stats1/pos.size:1m:tBTCUSD:long/hist?limit=500&sort=1
```

该 API 免费、无需认证。返回格式为 `[timestamp, value]` 数组，value 为多头仓位总量（BTC 单位）。

获取至少 500 天的日频数据，构建时间序列 `[date, margin_long_position]`。

如 API 不可用，提示用户手动提供数据或使用 TradingView `BITFINEX:BTCUSDLONGS` 获取。

### Step 2: 获取 BTC 价格历史数据

调用 `ant_spot_market_structure`，参数：
- query_type: `simple_price`
- ids: `bitcoin`

获取当前 BTC 价格。

调用 `ant_futures_market_structure`，参数：
- query_type: `futures_price_history`
- symbol: `BTC`

获取与 Step 1 同时间段的 BTC 日线收盘价，构建时间序列 `[date, btc_price]`。

### Step 3: 计算仓位变化率

对 Step 1 数据计算 N 日变化率：

```
position_change_pct = (position_today - position_N_days_ago) / position_N_days_ago * 100
```

默认 N = 30（`lookback_days` 参数）。同时计算 7 日、14 日变化率用于辅助分析。

输出新增列：`position_change_7d`, `position_change_14d`, `position_change_30d`。

### Step 4: 计算 BTC 价格变化率

对 Step 2 数据计算 BTC 价格的多窗口前向收益率（forward return）：
- `btc_fwd_return_7d`：信号触发后 7 天的 BTC 收益率
- `btc_fwd_return_14d`：信号触发后 14 天的 BTC 收益率
- `btc_fwd_return_30d`：信号触发后 30 天的 BTC 收益率

这些用于衡量每次信号触发后 BTC 的实际表现。

### Step 5: 极端信号识别与分类

根据阈值识别仓位极端变动事件：

- 仓位 30 日变化率 > `threshold_long`（默认 15%）: 标记为 **抄底信号**（bearish_contrarian，看空 BTC）
- 仓位 30 日变化率 < `-threshold_short`（默认 -10%）: 标记为 **止盈信号**（bullish_contrarian，看多 BTC）

去重规则：同方向信号在 14 天内只保留第一个，避免重复计数。

输出信号列表：`[date, signal_type, position_change_pct]`。

### Step 6: 信号回测与胜率统计

对每个信号事件，查找触发后 7d/14d/30d 的 BTC 收益率。按信号类型分组统计：

| 统计指标 | 说明 |
|----------|------|
| avg_return | 平均收益率 |
| median_return | 中位数收益率 |
| win_rate | 方向胜率（做空信号下跌概率 / 做多信号上涨概率） |
| sample_count | 独立事件数量 |

如果数据量足够（超过 3 年），将数据拆分为训练集和测试集，分别统计样本内和样本外胜率。

### Step 7: 当前状态评估与信号判断

取最新的 30 日仓位变化率，判断当前信号状态：

- 变化率 > `threshold_long` : `signal_active = true`, `signal_type = bearish_contrarian`
- 变化率 < `-threshold_short` : `signal_active = true`, `signal_type = bullish_contrarian`
- 其他情况 : `signal_active = false`, `signal_type = none`

信号强度分级（以 bearish_contrarian 为例）：
- moderate: 超过阈值 0-5 个百分点
- strong: 超过阈值 5-10 个百分点
- extreme: 超过阈值 10 个百分点以上

### Step 8: 综合评估与报告生成

汇总历史统计与当前状态，按下方输出模板生成完整分析报告。

判断标准：
- 仓位 30d 变化 > 15% : 输出做空信号，附历史胜率和平均收益
- 仓位 30d 变化 < -10% : 输出做多信号，附历史胜率和平均收益
- 仓位变化在 -10% ~ 15% 之间 : 无信号，输出"仓位变化在正常范围内，无极端信号"

附加警示：信号每年平均触发不到 5 次，适合作为辅助确认，不宜作为主策略。

同时调用辅助数据源（资金费率、OI、交易所净流量、鲸鱼转账）进行交叉验证，增强报告可信度。

---

## 输出约束

- 总文字输出不超过 300 字
- 优先用表格、数字、百分比替代文字描述
- 结论先行：第一行给出核心判断（信号状态），细节按需展开

---

## 报告结构

始终使用此模板：

```
===== Bitfinex 巨鲸仓位反指信号 =====
分析时间: {YYYY-MM-DD}
数据范围: {start_date} ~ {end_date}（{days}天）

[当前状态]
  30 日仓位变化率: {+/-xx.x%}
  信号状态: {触发/未触发} — {信号类型}
  信号强度: {Moderate/Strong/Extreme}（超过阈值 {x.x} 个百分点）

[历史统计（{信号描述}后的 BTC 表现）]
  | 窗口 | 平均收益 | 胜率 | 样本数 |
  |------|----------|------|--------|
  | 7 天 | {x.x%}   | {xx%}| {n}    |
  | 14 天| {x.x%}   | {xx%}| {n}    |
  | 30 天| {x.x%}   | {xx%}| {n}    |

[样本外验证（如有）]
  | 窗口 | 平均收益 | 胜率 | 样本数 |
  |------|----------|------|--------|
  | 30 天| {x.x%}   | {xx%}| {n}    |

[建议]
  {1-2 句操作建议}

[注意]
  - 该信号平均每年独立触发不到 5 次，适合作为辅助确认
  - 极端信号样本量有限，统计置信度有限
  - 不构成投资建议，需结合其他指标综合判断
```

---

## Risk Parameters

| 约束 | 值 | 说明 |
|------|-----|------|
| 信号触发频率 | 年均不到 5 次 | 极端事件天然稀缺，不适合高频使用 |
| 样本量限制 | 约 23 次（5 年全样本） | 统计置信度有限 |
| 币种限制 | 仅 BTC | 原始研究仅覆盖 BTC/USD，不可外推至其他币种 |
| 交易所限制 | 仅 Bitfinex | 仓位数据特指 Bitfinex margin，不代表全市场 |
| 市场结构变化 | 需持续验证 | 2024 年后 ETF 上市、机构入场可能改变巨鲸行为 |
| 核心数据依赖 | 外部 API | Bitfinex margin 数据不在 Antseer MCP 内，需调用外部接口 |
| 不可做主策略 | 必须辅助确认 | 仅提供辅助信号，需结合资金费率、OI、链上数据等综合判断 |

---

## 首次安装提示

```
目标用户：BTC 交易员、投研人员、量化策略研究者
使用场景：Bitfinex 保证金多头仓位出现极端变动时，判断是否存在反向交易机会
如何使用：/bitfinex-whale-contrarian-signal BTC
生成时间：2026-04-07 12:15:00
```
