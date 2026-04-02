---
name: "预测市场跨平台套利分析器"
description: "分析预测市场跨平台套利机会，包含 Bonding Curve 稀释建模、多情景盈亏模拟、退出路径分析，输出风险评级与操作建议"
strategy_agent: "analysis"
version: "1.0.0"
created_at: "2026-04-02T15:48:27Z"
skill_lifecycle: "draft"
author: "creator-agent"
---

# 预测市场跨平台套利分析器

## Overview

本 Skill 用于评估预测市场跨平台套利策略的真实可行性。当用户发现两个预测市场平台（如 Polymarket/42 与 Opinion）对同一事件的定价存在差异时，通过六步分析流程系统性揭示静态套利假设的失效点。

核心分析逻辑：Bonding Curve 机制下，后进场者以更高价格购入 token 并占据更大池子份额，持续稀释先行者的赔付权益。入场时锁定的名义赔率并非最终结算赔率，任何跨平台套利分析必须从静态赔率比较升级为动态赔率模拟。

六步分析流程：市场状态快照 -> 静态套利计算 -> Bonding Curve 稀释建模 -> 多情景动态盈亏模拟 -> 流动性与退出路径分析 -> 综合评估与风险评级。

## Demand Context

- **来源**: 推文分析 ([@Wuhuoqiu](https://x.com/Wuhuoqiu/status/2027651617680441749))
- **核心问题**: 跨预测市场套利（如在 42 买 No + 在 Opinion 买 Yes）表面存在无风险收益窗口，但 Bonding Curve 的份额稀释效应使实际赔率远低于入场时的名义赔率，导致静态套利假设不成立
- **方法论**: 三层分析框架——Bonding Curve 动态定价分析、多情景 P&L 模拟、一级市场结构类比
- **目标用户**: DeFi 交易员 / 预测市场玩家 / 量化分析师
- **触发词**: 预测市场套利、prediction market arbitrage、Polymarket 对冲、跨平台套利、bonding curve 稀释

## Features (Data Inputs)

### 用户输入参数

| 参数名 | 类型 | 必填 | 说明 | 默认值 | 示例值 |
|--------|------|------|------|--------|--------|
| event_description | string | 是 | 预测事件描述 | -- | "某项目是否在2026年底前发币" |
| platform_a | string | 是 | 平台 A 名称 | -- | "42 (Polymarket)" |
| platform_b | string | 是 | 平台 B 名称 | -- | "Opinion" |
| position_a_type | string | 是 | 平台 A 头寸方向 (YES/NO) | -- | "NO (No Token Launch)" |
| position_b_type | string | 是 | 平台 B 头寸方向 (YES/NO) | -- | "YES (63% 概率发币)" |
| investment_a | number | 是 | 平台 A 投入金额 (USD) | -- | 500 |
| investment_b | number | 是 | 平台 B 投入金额 (USD) | -- | 5000 |
| odds_a_entry | number | 是 | 平台 A 进入时赔率 | -- | 18 |
| prob_b_entry | number | 是 | 平台 B 进入时概率 (0-1) | -- | 0.63 |
| pool_tvl_a | number | 否 | 平台 A 池子当前 TVL (USD) | 0 | 4000 |
| pool_type | string | 否 | 池子定价机制 | "bonding_curve" | "bonding_curve" |
| time_horizon | string | 否 | 事件到期时间 | -- | "2026-12-31" |
| scenarios | list | 否 | 自定义情景参数 | 自动生成 3 个默认情景 | -- |

### Antseer MCP 数据源

| 数据需求 | MCP 工具 | query_type | 覆盖度 |
|----------|----------|------------|--------|
| 协议级 TVL | ant_protocol_tvl_yields_revenue | protocol_tvl | 部分（协议级非池级） |
| 条件代币价格 | ant_meme | token_info | 部分（CTF 代币可能未索引） |
| 链上交易记录 | ant_token_analytics | dex_trades | 部分（预测市场 token 交易模式非标准） |
| 稳定币储备 | ant_stablecoin | mcap | 完全覆盖 |
| 地址余额 | ant_address_profile | current_balance | 完全覆盖 |

### 不可自动获取的数据

- Bonding Curve 合约状态和参数（需链上合约读取）
- 对手平台（Opinion 等）实时定价（需平台 API）
- 预测市场池子参与者数据（需 Subgraph 或事件日志）
- 历史赔率/概率变化序列（需平台 API 或第三方聚合器）

## Entry Conditions

本 Skill 为分析工具型，以下条件触发分析：

```yaml
entry_conditions:
  - condition: cross_platform_odds_gap
    description: "两个预测市场平台对同一事件存在赔率/概率差异"
    operator: "=="
    value: true
  - condition: has_core_pricing_data
    description: "用户可提供双平台基本定价数据（赔率、概率、投入金额）"
    operator: "=="
    value: true
  - condition: event_not_expired
    description: "预测事件尚未到期结算"
    operator: "=="
    value: true
```

## Exit Conditions

分析完成后输出评估报告，以下条件决定最终评级：

```yaml
exit_conditions:
  recommend:
    description: "静态套利 > 0 且稀释后有效赔率 >= 70% 初始赔率"
    rating: "推荐"
    action: "套利机会存在，建议执行并监控池子变化"
  cautious:
    description: "静态套利 > 0 但稀释后有效赔率在 50%-70% 初始赔率之间"
    rating: "谨慎"
    action: "套利空间存在但受稀释侵蚀，需设止损并定期重评"
  not_recommend:
    description: "静态套利 <= 0 或稀释后有效赔率 < 50% 初始赔率"
    rating: "不推荐"
    action: "套利不成立或动态博弈风险过高，建议放弃"
```

## Action Specification

### Step 1: 获取两个平台当前市场状态

**目标**: 采集两个预测市场平台对同一事件的当前定价/TVL/参与度数据，建立分析基准。

**数据来源**:
- 用户输入: `platform_a`, `platform_b`, `event_description`, `pool_tvl_a`, `odds_a_entry`, `prob_b_entry`
- MCP 辅助: `ant_protocol_tvl_yields_revenue` (query_type: `protocol_tvl`) -- 协议级 TVL 作为背景参考

**分析逻辑**:
1. 记录平台 A 的池子 TVL、当前赔率、头寸方向
2. 记录平台 B 的事件概率、用户头寸成本、头寸方向
3. 计算平台 B 的隐含赔率: `1 / prob_b_entry`
4. 输出: 双平台市场状态快照表

### Step 2: 计算静态套利空间

**目标**: 假设赔率和概率不变，计算两种事件结果下的理论套利收益。

**分析逻辑**:
- 场景 A（事件发生）: `pnl_a = -investment_a`, `pnl_b = investment_b * (1/prob_b_entry - 1)`
- 场景 B（事件不发生）: `pnl_a = investment_a * odds_a_entry`, `pnl_b = -investment_b`
- 净损益 = pnl_a + pnl_b（两个场景分别计算）
- 如果两个场景净损益均 > 0，存在静态套利

**输出**: 静态套利矩阵（2x2 场景 P&L 表），标注是否存在静态套利

### Step 3: Bonding Curve 稀释建模

**目标**: 模拟池子 TVL 变化对用户持仓份额和有效赔率的影响。

**分析逻辑**:
- 计算用户在池子中的初始份额: `share = investment_a / entry_tvl`（简化线性近似）
- 指数型 Bonding Curve 份额计算: `tokens = (1/k) * ln((entry_tvl + investment_a) / entry_tvl)`
- 模拟 TVL 增长到 2x、5x、10x 时：
  - 新增资金流入后的总 token 供应量增长
  - 用户 token 数不变，份额占比下降
  - 有效赔率 = 份额占比 * 池子总赔付额 / 用户投入
- 如果有效赔率 < 进入时赔率的 50%，标记"严重稀释警告"

**输出**: 稀释曲线表（TVL | 份额占比 | 有效赔率 | 稀释程度）

### Step 4: 多情景动态 P&L 模拟

**目标**: 在 4 个市场演变场景下模拟组合头寸的盈亏。

**情景设计**:
1. **乐观（事件发生）**: 平台 A 归零，平台 B 获利结算
2. **悲观（事件不发生 + 池子膨胀）**: 平台 A 按稀释后赔率结算，平台 B 全损
3. **中途退出**: 在市场情绪变化时两边同时平仓，平台 A 沿 Bonding Curve 卖出
4. **黑天鹅**: 一个平台出现流动性枯竭或规则变更

**计算**:
- 每个情景: 平台 A P&L + 平台 B P&L = 净 P&L
- 标注最大回撤、资金利用率

**输出**: 多情景 P&L 矩阵

### Step 5: 流动性与退出路径分析

**目标**: 评估中途退出的可行性和滑点成本。

**分析逻辑**:
- 计算沿 Bonding Curve 卖出 investment_a 的预期滑点
- 评估平台 B 的流动性深度（基于概率和交易量）
- 如果预期滑点 > 5%，标记"退出摩擦高"
- 建议最优退出时机：池子 TVL 达到盈亏平衡规模前

**输出**: 退出路径评估（滑点估算、最优退出时机）

### Step 6: 综合评估

**目标**: 汇总所有中间结果，输出套利可行性评级。

**判断标准**:
- 静态套利 > 0 且稀释后有效赔率 >= 70% 初始赔率 -> "推荐"
- 静态套利 > 0 但稀释后有效赔率 50%-70% -> "谨慎"
- 静态套利 <= 0 或有效赔率 < 50% -> "不推荐"
- 额外标注: 平台风险、智能合约风险、结算规则差异风险

**输出字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| event | string | 预测事件描述 |
| static_arbitrage_pnl | object | 静态套利 P&L（场景 A/B） |
| is_static_arb_valid | boolean | 静态套利是否成立 |
| dilution_table | array | TVL 变化 vs 有效赔率 vs 份额占比 |
| effective_odds_current | number | 当前有效赔率 |
| scenarios | array | 多情景 P&L 模拟结果 |
| worst_case_pnl | number | 最差情景净 P&L (USD) |
| best_case_pnl | number | 最佳情景净 P&L (USD) |
| exit_slippage_estimate | number | 中途退出预估滑点 (%) |
| risk_rating | string | 推荐 / 谨慎 / 不推荐 |
| risk_factors | array | 风险因素列表 |
| recommendation | string | 操作建议 |

## Risk Parameters

```yaml
risk:
  bonding_curve_dilution:
    description: "Bonding Curve 份额稀释 -- 池子 TVL 膨胀导致先行者赔付权益被后来者持续稀释"
    severity: "high"
    mitigation: "设定池子 TVL 上限监控，超过盈亏平衡规模时立即退出"

  settlement_rule_mismatch:
    description: "结算规则差异 -- 两个平台对同一事件的定义、结算条件、边界情况处理可能不同"
    severity: "high"
    mitigation: "执行前逐条核对两个平台的结算规则文档，确认事件定义完全一致"

  liquidity_exit_risk:
    description: "退出滑点风险 -- 沿 Bonding Curve 卖出时实际收到金额低于理论值"
    severity: "medium"
    mitigation: "模拟退出时加入 5-10% 滑点折扣，避免在池子深度不足时大额卖出"

  timing_risk:
    description: "时间价值风险 -- 长周期套利窗口内市场条件可能剧变"
    severity: "medium"
    mitigation: "定期（每周/月）重新运行分析，根据最新池子规模和市场情绪更新策略"

  platform_risk:
    description: "平台运营风险 -- 预测市场平台可能下线、修改规则或遭遇安全事件"
    severity: "medium"
    mitigation: "分散头寸，避免在单一平台投入过大比例资金"

  data_accuracy_risk:
    description: "数据准确性 -- 核心定价数据依赖用户手动输入，可能存在延迟或错误"
    severity: "low"
    mitigation: "执行前从平台实时获取最新数据并二次确认"

  model_assumption_risk:
    description: "模型假设 -- 默认 Bonding Curve 参数可能与平台实际实现存在差异"
    severity: "medium"
    mitigation: "用户应提供平台公开的 Bonding Curve 参数，避免依赖默认假设"
```

## Limitations

- 不能自动抓取预测市场平台实时数据（Polymarket/Opinion API 未集成）
- 不能预测市场概率走向（模型是情景模拟，不是价格预测）
- 不能覆盖所有预测市场平台的定价机制（不同平台可能用不同 AMM/订单簿模型）
- 不能评估智能合约层面的安全风险
- Antseer MCP 对预测市场协议覆盖度低（9 项数据需求中仅 2 项完全覆盖）
- Bonding Curve 参数需链上合约读取，当前无自动化方案
- 历史赔率/概率变化数据依赖第三方 API

## Disclaimer

本 Skill 基于推文内容自动生成，分析方法论归属原作者 @Wuhuoqiu。生成的 Skill 为 v1 草稿，建议 review 后用于生产环境。不构成投资建议。预测市场参与涉及本金损失风险，Bonding Curve 机制下赔率非固定。
