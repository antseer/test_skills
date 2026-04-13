---
name: whale-position-contrarian-signal
version: "1.0.0"
user-invocable: true
description: |
  交易所巨鲸仓位反向信号分析。监控交易所（Bitfinex、Binance等）的仓位极端变化
  （OI、多空比、保证金多头），基于统计回测生成反向操作信号。
  需要 Antseer MCP 服务器（见 README.md 安装说明）。
  Use when asked to "巨鲸仓位", "whale position", "Bitfinex margin longs",
  "保证金多头信号", "巨鲸反向指标", "whale contrarian", "大户持仓异动",
  "OI极端变化", "仓位背离", "鲸鱼做多做空信号", "巨鲸反向", "大户反指",
  "whale position signal", "巨鲸见顶", "鲸鱼做反", "contrarian signal"
argument-hint: "BTC（默认）/ ETH / SOL"
allowed-tools:
  - mcp__ANTSEER_MCP_ID__ant_futures_market_structure
  - mcp__ANTSEER_MCP_ID__ant_spot_market_structure
  - mcp__ANTSEER_MCP_ID__ant_futures_liquidation
  - mcp__ANTSEER_MCP_ID__ant_fund_flow
metadata:
  requires:
    mcpServers:
      - name: antseer
        description: "Antseer on-chain data MCP — provides futures market structure, spot market data, liquidation data, and fund flow data"
  generated_at: "2026-04-07 06:22:44"
author: antseer
license: MIT
---

## Overview

监控交易所仓位数据的极端变化（30天变化率超过阈值），基于历史回测的胜率统计，生成反向操作信号（巨鲸大幅抄底时考虑做空，巨鲸大幅止盈时考虑做多）。

## Demand Context

方法论来源：@leifuchen 对 Bitfinex 保证金多头仓位与 BTC 价格的 1838 天量化回测分析。核心发现：日常仓位变化无可用信号，但极端事件（30天仓位涨幅超15%或跌幅超10%）具有统计显著的反向操作价值。仓位大涨>15%时做空胜率69%（30天窗口），仓位大跌>10%时做多胜率62%（14天窗口）。原始分析使用 Bitfinex Margin Longs 数据，本 Skill 通用化为支持 OI、多空比等替代指标。

## Features (Data Inputs)

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| symbol | string | 是 | 目标代币符号 | BTC |
| exchange | string | 是 | 目标交易所 | bitfinex |
| lookback_days | int | 是 | 历史回看天数 | 180 |
| position_type | string | 否 | 仓位类型：futures_oi / long_short_ratio | futures_oi |

**内部常量（不暴露为参数）：**
- rolling_window = 30 天
- increase_threshold = 15%（仓位大涨阈值）
- decrease_threshold = 10%（仓位大跌阈值）
- signal_eval_windows = [14, 30] 天

## Entry Conditions

满足以下任一条件时触发：

1. 用户明确请求巨鲸仓位分析、whale position signal、保证金多头信号等关键词
2. 用户询问某币种是否出现仓位极端信号或反向操作机会
3. 用户提到 Bitfinex margin longs、大户持仓异动、OI 极端变化
4. 定期巡检模式：用户要求每日/每周检查仓位信号

## Exit Conditions

1. 输出完整的信号分析报告（含当前状态、历史回测、置信度评级）
2. 若无极端信号，输出"当前无可操作信号"及距离阈值的距离
3. 数据获取失败时，说明失败原因并给出替代建议

## Action Specification

按以下步骤执行分析，所有步骤使用祈使句。每一步的 MCP 调用失败时，说明原因并跳到下一步可用数据。

### Step 1: 获取历史价格数据

调用 `ant_futures_market_structure`，参数：
- query_type: `futures_price_history`
- symbol: symbol（默认 BTC）
- exchange: 用户指定的交易所（默认 bitfinex）

如果期货价格不可用，降级调用 `ant_spot_market_structure`：
- query_type: `coins_markets`
- ids: 对应的 CoinGecko ID（如 bitcoin）

提取每日收盘价序列，计算日收益率。

### Step 2: 获取交易所仓位数据

根据 position_type 选择数据源：

**futures_oi（默认）**：调用 `ant_futures_market_structure`
- query_type: `futures_oi_aggregated`
- symbol: symbol（默认 BTC）

**long_short_ratio**：调用 `ant_futures_market_structure`
- query_type: `futures_long_short_account_ratio` 或 `futures_long_short_top_position_ratio`
- symbol: symbol（默认 BTC）

提取每日仓位快照序列。

### Step 3: 计算仓位滚动变化率

对 Step 2 的仓位序列，逐日计算 **30 天**（固定窗口）的百分比变化：

```
position_change_pct = (current - value_N_days_ago) / value_N_days_ago * 100
```

### Step 4: 获取辅助验证数据

调用以下 MCP 工具获取辅助数据（任一失败不影响主流程）：

- `ant_futures_market_structure` / query_type: `futures_funding_rate_current` — 资金费率
- `ant_futures_liquidation` / query_type: `futures_liquidation_aggregated` — 爆仓数据
- `ant_fund_flow` / query_type: `exchange_reserve` — 交易所储备变化
- `ant_fund_flow` / query_type: `centralized_exchange_whale_transfer` — 鲸鱼大额转账

这些数据用于信号的交叉验证，提升置信度。

### Step 5: 极端信号检测

从滚动变化率中筛选超阈值事件（阈值为固定常量）：

- `position_change_pct > 15%` --> 标记 **WHALE_ACCUMULATION**（巨鲸抄底，反向信号：考虑做空）
- `position_change_pct < -10%` --> 标记 **WHALE_DISTRIBUTION**（巨鲸止盈，反向信号：考虑做多）

记录每个信号的触发日期和变化幅度。

### Step 6: 信号回测评估

对 Step 5 的每个历史信号，计算触发后 **[14, 30] 天**（固定窗口）内的价格变化：

- WHALE_ACCUMULATION --> 反向做空，后续价格下跌则信号正确
- WHALE_DISTRIBUTION --> 反向做多，后续价格上涨则信号正确

统计：总信号数、正确数、胜率、平均收益率。

### Step 7: 当前状态判断

计算最新 30 天的仓位变化率：

- 若触发极端信号 --> 输出信号类型 + 历史胜率 + 建议反向操作方向
- 若未触发 --> 输出当前变化率 + 距离阈值的百分比距离

### Step 8: 综合输出

按「输出格式」章节的模板输出报告。信号强度判定：

| 条件 | 信号强度 |
|------|---------|
| 触发极端信号 + 历史胜率 > 60% + 辅助指标确认 | HIGH |
| 触发极端信号 + 历史胜率 > 60% | MEDIUM |
| 触发极端信号 + 历史胜率 <= 60% | LOW |
| 未触发极端信号 | NEUTRAL |

## 输出约束

- 总文字输出不超过 300 字
- 优先用表格、数字、百分比替代文字描述
- 结论先行：第一行给出核心判断，细节按需展开
- 超出 300 字的内容拆分为"摘要"（默认输出）+"详细报告"（用户追问时展开）

## 输出格式

始终使用此模板：

```
=== 交易所巨鲸仓位反向信号分析 ===
代币: {symbol} | 数据源: {exchange} {position_type} | 分析日期: {date}

-- 当前信号 --
  30天仓位变化率: {change_pct}%
  信号状态: {WHALE_ACCUMULATION / WHALE_DISTRIBUTION / NEUTRAL}
  建议方向: {SHORT / LONG / HOLD}
  信号强度: {HIGH / MEDIUM / LOW / NEUTRAL}

-- 历史回测 --
  | 信号类型 | 窗口 | 次数 | 胜率 | 平均收益 |
  |---------|------|------|------|---------|
  | ACCUMULATION->做空 | 30天 | {n} | {rate}% | {return}% |
  | DISTRIBUTION->做多 | 14天 | {n} | {rate}% | {return}% |

-- 辅助验证 --
  资金费率: {funding_rate}
  近24h爆仓: {liquidation_summary}
  交易所储备变化: {reserve_change}

-- 风险提示 --
  本信号为统计概率判断，非确定性预测。
  建议结合其他指标综合判断，不构成投资建议。
  方法论来源: @leifuchen
```

**示例输出：**

输入: `/whale-position-contrarian-signal BTC`

```
=== 交易所巨鲸仓位反向信号分析 ===
代币: BTC | 数据源: Bitfinex futures_oi | 分析日期: 2026-04-07

-- 当前信号 --
  30天仓位变化率: +18.7%
  信号状态: WHALE_ACCUMULATION（巨鲸大幅加仓）
  建议方向: SHORT（考虑做空）
  信号强度: HIGH

-- 历史回测 --
  | 信号类型 | 窗口 | 次数 | 胜率 | 平均收益 |
  |---------|------|------|------|---------|
  | ACCUMULATION->做空 | 30天 | 23 | 69% | -4.2% |
  | DISTRIBUTION->做多 | 14天 | 18 | 62% | +3.1% |

-- 辅助验证 --
  资金费率: +0.012%（偏多，支持反向做空逻辑）
  近24h爆仓: 多头爆仓 $4.2M > 空头 $1.8M
  交易所储备变化: +1,200 BTC（7日净流入）

-- 风险提示 --
  本信号为统计概率判断，非确定性预测。
  建议结合其他指标综合判断，不构成投资建议。
  方法论来源: @leifuchen
```

## Risk Parameters

| 风险维度 | 约束 |
|---------|------|
| 数据覆盖 | Bitfinex Margin Longs 在 MCP 中无直接覆盖，默认使用 OI/多空比作替代 |
| 阈值敏感性 | 默认阈值（涨15%/跌10%）来自 BTC 回测，其他币种可能需要调整 |
| 样本量 | 极端信号天然稀缺，回测样本量可能不足以支撑统计显著性 |
| 时效性 | MCP 数据更新频率影响信号实时性，建议至少每日检查一次 |
| 替代指标偏差 | OI/多空比与 Margin Longs 行为特征有差异，实际胜率可能与原回测不同 |
| 信号非确定性 | 历史胜率约60-70%意味着仍有30-40%的反向案例，严格控制仓位 |

## 首次安装提示

```
目标用户：中高频交易员、量化研究员、投研分析师
使用场景：定期巡检交易所仓位极端变化，捕捉巨鲸反向操作信号
如何使用：/whale-position-contrarian-signal BTC
生成时间：2026-04-07 06:22:44
```
