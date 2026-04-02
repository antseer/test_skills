---
name: "Prediction Market Cross-Platform Arbitrage Analyzer"
description: "分析预测市场跨平台套利在 Bonding Curve 动态机制下的实际可行性与风险，输出情景盈亏矩阵和套利可行性评级"
strategy_agent: "analysis"
version: "1.0.0"
created_at: "2026-04-02T15:02:30Z"
skill_lifecycle: "draft"
author: "creator-agent"
---

# Prediction Market Cross-Platform Arbitrage Analyzer

## Overview

本 Skill 用于评估预测市场跨平台套利策略在 Bonding Curve 动态定价机制下的真实可行性。当用户发现两个预测市场平台（如 Polymarket 与 42 平台）对同一事件存在赔率差异时，本 Skill 通过五步分析流程——双平台赔率快照、Bonding Curve 份额稀释模拟、情景盈亏矩阵、市场情绪评估、综合可行性判定——揭示静态套利假设的潜在失效点，输出量化的风险评估和策略建议。

核心洞察：Bonding Curve 机制下，后进场者以更高价格买入并占据更大池子份额，导致先行者的赔付股份权益被持续稀释。名义赔率并非实际赔率，任何套利分析都必须从静态赔率对比升级为动态赔率模拟。

## Demand Context

- **来源**: 推文分析 ([@Wuhuoqiu](https://x.com/Wuhuoqiu/status/2027651617680441749))
- **核心问题**: 跨预测市场套利（如在 Polymarket 买 Yes + 在 42 平台买 No）看似存在无风险收益窗口，但 Bonding Curve 的份额稀释效应会使实际赔率远低于入场时的名义赔率
- **方法论**: 将静态赔率对比升级为动态赔率模拟，考虑池子规模变化、Bonding Curve 参数、市场情绪对资金流入流出的影响
- **目标用户**: 预测市场交易员、DeFi 套利者、Crypto 投研人员
- **触发词**: 预测市场套利、prediction market arbitrage、bonding curve 套利分析、跨平台对冲、polymarket 套利

## Features (Data Inputs)

### 用户输入参数（核心定价数据）

| 参数名 | 类型 | 必填 | 说明 | 默认值 | 示例值 |
|--------|------|------|------|--------|--------|
| platform_a | string | 是 | 平台 A 名称（采用 Bonding Curve 机制的平台） | -- | 42 |
| platform_b | string | 是 | 平台 B 名称（对手方平台） | -- | Polymarket (Opinion) |
| event_description | string | 是 | 预测事件描述 | -- | "某项目是否在年底前发币" |
| pool_a_name | string | 是 | 平台 A 的目标池子名称 | -- | "No Token Launch" |
| pool_a_current_tvl | number | 是 | 平台 A 目标池子当前 TVL (USD) | -- | 4000 |
| pool_a_entry_tvl | number | 否 | 进场时池子的 TVL (USD)，用于回溯分析 | -- | 1500 |
| pool_a_odds | string | 否 | 平台 A 当前赔率 | -- | 1:10 |
| platform_b_probability | number | 是 | 平台 B 对应事件的当前概率 (%) | -- | 63 |
| platform_b_position_cost | number | 是 | 在平台 B 的头寸成本 (USD) | -- | 5000 |
| user_investment | number | 是 | 用户在平台 A 的投入金额 (USD) | -- | 500 |
| time_horizon | string | 否 | 套利的时间窗口 | 1 year | "到 2026 年底" |
| bonding_curve_type | string | 否 | Bonding Curve 类型（linear / exponential / logarithmic） | exponential | exponential |

### MCP 数据源（辅助情绪与趋势数据）

| 数据需求 | MCP 工具 | query_type | 推荐参数 | 覆盖度 |
|----------|----------|------------|----------|--------|
| 相关代币市场情绪 | `ant_market_sentiment` | `coin_detail` | coin={相关代币符号} | 完全覆盖 |
| 社交话题热度 | `ant_market_sentiment` | `topics_list` | topic={事件相关话题} | 完全覆盖 |
| 相关协议 TVL | `ant_protocol_tvl_yields_revenue` | `protocol_tvl` | protocol={预测市场协议名} | 部分覆盖（协议级 TVL，非子池级） |

### 不可自动获取的数据（需用户手动输入）

- 预测市场平台赔率/概率（需从 Polymarket API 或 42 平台页面获取）
- Bonding Curve 精确参数（需从平台智能合约或文档提取）
- 预测市场池子历史 TVL 变化（需通过平台 API 或 Dune Analytics 追踪）
- 预测市场头寸实时价格（需从对应平台 API 获取）

## Entry Conditions

本 Skill 为分析工具型（非自动交易型），以下条件触发分析流程：

```yaml
entry_conditions:
  - condition: cross_platform_odds_gap_exists
    description: "用户发现两个预测市场平台对同一事件存在赔率差异"
    operator: "=="
    value: true
  - condition: platform_a_uses_bonding_curve
    description: "至少一个平台采用 Bonding Curve 定价机制"
    operator: "=="
    value: true
  - condition: user_has_core_pricing_data
    description: "用户能提供双方平台的基本定价数据（赔率/概率、TVL、头寸成本）"
    operator: "=="
    value: true
```

## Exit Conditions

分析完成后输出最终评估报告。以下条件决定报告中的策略建议：

```yaml
exit_conditions:
  feasibility_positive:
    description: "所有情景下净损益 > 0"
    rating: "feasible"
    recommendation: "套利可行（低风险），可按计划执行"
  feasibility_conditional:
    description: "多数情景净损益 > 0 但存在亏损情景"
    rating: "conditionally_feasible"
    recommendation: "套利有条件可行，需设止损线并监控池子规模"
  feasibility_negative:
    description: "稀释后实际赔率 < 盈亏平衡赔率"
    rating: "not_feasible"
    recommendation: "套利不可行，静态假设已失效"
  feasibility_directional:
    description: "中途退出为最优策略"
    rating: "not_arbitrage"
    recommendation: "实质为方向性交易 + 择时退出，非无风险套利"
```

## Action Specification

### Step 1: 双平台赔率快照采集

**目标**: 获取两个平台对同一事件的当前定价/概率数据，建立静态基线。

**数据来源**:
- 用户输入: `pool_a_current_tvl`, `pool_a_odds`, `platform_b_probability`, `platform_b_position_cost`
- MCP 辅助: `ant_protocol_tvl_yields_revenue` (query_type: `protocol_tvl`, protocol={预测市场协议名}) -- 获取协议级 TVL 作为背景参考

**分析逻辑**:
1. 记录当前时刻的静态赔率差：平台 A 赔率 vs 平台 B 隐含赔率
2. 计算平台 B 隐含赔率: `1 / (platform_b_probability / 100)`
3. 计算理论静态套利空间: `user_investment x pool_a_odds_ratio - platform_b_position_cost`

**输出**: 双平台赔率对比表、静态套利空间 (USD)

### Step 2: Bonding Curve 份额稀释模拟

**目标**: 模拟在不同池子规模下，用户初始投入的份额占比和实际赔率变化。

**数据来源**:
- 用户输入: `bonding_curve_type`, `pool_a_entry_tvl`, `pool_a_current_tvl`, `user_investment`

**分析逻辑**:

根据 Bonding Curve 类型计算用户份额：

**指数型 (exponential)** -- 最常见的 Bonding Curve 模型：
```
price(supply) = base_price * e^(k * supply)
用户获得的 token 数 = (1/k) * ln((entry_tvl + user_investment) / entry_tvl)
总 token 供应量在池子规模 S 时 = (1/k) * ln(S / base_tvl)
用户份额占比 = 用户 token 数 / 总 token 供应量
实际赔率 = 用户份额占比 x 池子总赔付 / 用户投入成本
```

**线性型 (linear)**:
```
price(supply) = base_price + k * supply
用户获得的 token 数 = (sqrt(entry_tvl + user_investment) - sqrt(entry_tvl)) / sqrt(k/2)
```

**对数型 (logarithmic)**:
```
price(supply) = base_price * ln(1 + k * supply)
```

模拟场景：池子从当前 TVL 膨胀到 2x、5x、10x 时的份额占比和实际赔率变化。

**输出**: 份额稀释曲线表（池子规模 -> 份额占比 -> 实际赔率 -> 实际赔付）

### Step 3: 情景分析 -- 事件结果 x 退出时机矩阵

**目标**: 构建二维情景矩阵，分析不同事件结果和退出时机下的盈亏。

**数据来源**: Step 1 和 Step 2 的输出

**分析逻辑**:

构建 3x3 情景矩阵（事件结果 x 市场情景）：

| | 乐观（池子不涨） | 中性（池子涨到 2-5x） | 悲观（池子涨到 10x+） |
|---|---|---|---|
| **事件发生** | 平台 A 归零 + 平台 B 获利 | 平台 A 归零 + 平台 B 获利 | 平台 A 归零 + 平台 B 获利 |
| **事件未发生 + 持有到结算** | 按当前份额赔付 | 按稀释份额赔付 | 按严重稀释份额赔付 |
| **中途退出（沿曲线卖出）** | 部分回本 | 部分回本 | 部分回本 |

计算每个格子的净损益 = 平台 A 收益/损失 + 平台 B 收益/损失 - 总投入成本

**输出**: 3x3 情景盈亏矩阵 (USD)，标注盈利/亏损状态

### Step 4: 市场情绪与资金流动趋势评估

**目标**: 评估市场对该事件的情绪走向，预判池子资金流入流出趋势。

**数据来源**:
- MCP: `ant_market_sentiment` (query_type: `coin_detail`, coin={相关代币}) -- 获取代币级情绪数据
- MCP: `ant_market_sentiment` (query_type: `topics_list`) -- 搜索事件相关话题热度

**分析逻辑**:
1. 如果市场情绪转向"事件不会发生" -> 平台 A 的 No 池子将吸引更多资金，份额稀释加速，不利于套利
2. 如果市场情绪转向"事件会发生" -> No 池子资金流出，份额占比可能回升，有利于套利者
3. 结合社交热度趋势判断短期内池子规模变化方向
4. 高社交热度通常意味着更多资金涌入，加速稀释

**输出**: 市场情绪评估（看多/中性/看空事件发生）、池子规模变化预测方向、情绪对套利策略的影响判断

### Step 5: 综合评估 -- 套利可行性判定

**目标**: 汇总所有中间结果，输出最终的套利可行性评估。

**判断标准**:
- 所有情景下净损益 > 0 -> 套利可行（低风险）
- 多数情景下净损益 > 0 但存在亏损情景 -> 套利有条件可行（需设止损）
- 稀释后实际赔率 < 盈亏平衡赔率 -> 套利不可行（静态假设失效）
- 中途退出为最优策略 -> 非套利，实质为方向性交易 + 择时退出

**计算盈亏平衡池规模**: 找到使"事件未发生 + 持有到结算"情景下净损益 = 0 的池子 TVL 值。

**输出结构**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| event_description | string | 预测事件描述 |
| static_arbitrage_spread | number | 静态套利空间 (USD) |
| current_share_pct | number | 用户当前在池中的份额占比 (%) |
| diluted_share_pct | number | 模拟稀释后的份额占比 (%) |
| nominal_odds | string | 入场时的名义赔率 |
| effective_odds | string | 稀释后的实际赔率 |
| scenario_matrix | object | 3x3 情景盈亏矩阵 |
| breakeven_pool_size | number | 盈亏平衡时的池子规模 (USD) |
| feasibility_rating | enum | feasible / conditionally_feasible / not_feasible / not_arbitrage |
| recommended_strategy | string | 推荐策略（持有到期/中途退出/不参与） |
| risk_warnings | list[string] | 风险提示列表 |
| market_sentiment | string | 当前市场情绪方向 |

## Risk Parameters

```yaml
risk:
  # 分析层面的风险参数
  bonding_curve_dilution:
    description: "Bonding Curve 份额稀释风险 -- 池子规模膨胀导致先行者权益被后来者稀释"
    severity: "high"
    mitigation: "设置池子 TVL 上限监控，超过盈亏平衡规模时触发退出信号"

  settlement_rule_mismatch:
    description: "两平台结算规则差异风险 -- 结算时间、条件定义、边界情况处理可能不同"
    severity: "high"
    mitigation: "在执行前逐条核对两个平台的结算规则文档，确认事件定义完全一致"

  liquidity_risk:
    description: "Bonding Curve 卖出滑点风险 -- 沿曲线卖出时实际收到的金额可能低于理论值"
    severity: "medium"
    mitigation: "模拟中途退出时加入 5-10% 的滑点折扣"

  timing_risk:
    description: "时间价值风险 -- 长周期套利窗口内市场条件可能剧变"
    severity: "medium"
    mitigation: "定期（周/月）重新运行分析，更新池子规模和市场情绪数据"

  platform_risk:
    description: "平台运营风险 -- 预测市场平台可能下线、修改规则或遭遇安全事件"
    severity: "medium"
    mitigation: "分散头寸，避免在单一平台投入过大比例资金"

  data_accuracy:
    description: "数据准确性风险 -- 核心定价数据依赖用户手动输入，可能存在延迟或错误"
    severity: "low"
    mitigation: "建议用户在执行前从平台实时获取最新数据并二次确认"

  model_assumption:
    description: "模型假设风险 -- Bonding Curve 模型可能与平台实际实现存在差异"
    severity: "medium"
    mitigation: "用户应提供平台公开的 Bonding Curve 参数，而非依赖默认假设"
```

## Limitations

- 本 Skill 不能预测预测市场的赔率走向（市场博弈结果不可预测）
- 无法精确计算 Bonding Curve 卖出收益（需平台合约的精确公式和参数）
- 不覆盖所有预测市场平台（每个平台的机制不同，需针对性适配）
- 不替代用户对事件本身的判断（事件是否会发生需用户自行评估）
- Antseer MCP 不直接覆盖预测市场平台数据，核心定价数据需用户手动输入
- 市场情绪数据仅作辅助参考，不直接反映预测市场池子的资金动态

## Disclaimer

本 Skill 基于推文内容自动生成，分析方法论归属原作者 @Wuhuoqiu。不构成投资建议。预测市场交易存在本金全损风险，请在充分了解平台机制后参与。
