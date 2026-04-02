---
name: "预测市场 Bonding Curve 套利验证器"
description: "分析跨预测市场平台套利可行性，模拟 Bonding Curve 份额稀释效应对实际收益的影响"
strategy_agent: "analysis"
version: "1.0.0"
created_at: "2026-04-02T00:00:00Z"
skill_lifecycle: "draft"
author: "creator-agent"
---

# 预测市场 Bonding Curve 套利验证器

## Overview

当两个预测市场平台对同一事件持不同赔率时，交易员往往认为可以通过跨平台对冲锁定无风险利润。然而当其中一个平台使用 Bonding Curve 机制定价时，后来者的资金流入会稀释早期参与者的份额占比，导致"赔率不等于实际收益率"。本 Skill 通过五步分析流程（静态 PnL 计算、Bonding Curve 稀释模拟、动态 PnL 矩阵、提前退出路径分析、综合判定）量化这一效应，输出结构化的套利可行性评估报告。

核心洞察来源于对 Polymarket 与 42 平台跨平台套利案例的分析：Bonding Curve 预测市场中的赔率是动态的，池子 TVL 增长后早期参与者份额被稀释，静态套利模型不再成立。

## Demand Context

加密货币交易员和预测市场玩家在发现跨平台赔率差异时，需要快速验证套利是否真正可行。传统套利分析假设赔率固定，但 Bonding Curve 机制打破了这一前提。用户需要一个"计算器模式"的工具，输入两个平台的赔率、金额、池子 TVL 等参数，即可获得考虑稀释效应后的真实 PnL 分析和策略建议。

该需求来自对 @Wuhuoqiu 推文分析框架的泛化：揭示 Bonding Curve 预测市场中"赔率不等于实际收益"的认知误区，并将其工具化为可复用的验证流程。

目标用户：Crypto 交易员、预测市场玩家、DeFi 投研人员。

## Features (Data Inputs)

| Feature | Source | Description |
|---------|--------|-------------|
| event_description | 用户输入 | 预测事件描述（如"某项目是否在年底前发币"） |
| platform_a_name | 用户输入 | 平台 A 名称（如 Polymarket） |
| platform_a_odds | 用户输入 | 平台 A 当前赔率/概率（如 0.63 表示 Yes 63%） |
| platform_a_bet_amount | 用户输入 | 平台 A 下注金额（USD） |
| platform_a_pricing_model | 用户输入 | 平台 A 定价模型（AMM / OrderBook / Fixed），默认 AMM |
| platform_b_name | 用户输入 | 平台 B 名称（如 42） |
| platform_b_pool | 用户输入 | 平台 B 具体池子名称（如 No Token Launch） |
| platform_b_odds | 用户输入 | 平台 B 当前赔率（如 10 表示 1:10） |
| platform_b_bet_amount | 用户输入 | 平台 B 下注金额（USD） |
| platform_b_pool_tvl | 用户输入 | 平台 B 池子当前 TVL（USD） |
| platform_b_pricing_model | 用户输入 | 平台 B 定价模型（BondingCurve / AMM / Fixed），默认 BondingCurve |
| time_horizon | 用户输入 | 事件结算时间范围，默认 "6 months" |
| pool_growth_scenarios | 用户输入 | 池子 TVL 增长倍数列表，默认 [2, 5, 10] |
| token_spot_price | ant_spot_market_structure | 相关代币现货价格（如涉及代币发行事件） |
| market_sentiment | ant_market_sentiment | 市场情绪指标，辅助判断事件概率变化方向 |

**MCP 覆盖度**：核心预测市场数据（赔率、TVL、Bonding Curve 参数）均需用户手动输入；仅代币价格和市场情绪可通过 Antseer MCP 获取。v1 以"计算器模式"交付。

## Entry Conditions

```yaml
entry_conditions:
  trigger_scenario:
    - condition: cross_platform_odds_divergence
      description: "用户发现两个预测市场平台对同一事件赔率存在差异，且至少一个平台使用 Bonding Curve 定价"
  required_inputs:
    - condition: event_description
      operator: "not_empty"
      description: "必须提供预测事件描述"
    - condition: platform_a_odds
      operator: "between"
      range: [0.01, 0.99]
      description: "平台 A 概率值在 1%-99% 之间"
    - condition: platform_b_odds
      operator: ">"
      threshold: 1.0
      description: "平台 B 赔率大于 1:1"
    - condition: platform_b_pool_tvl
      operator: ">"
      threshold: 0
      description: "平台 B 池子 TVL 必须大于 0"
```

## Exit Conditions

```yaml
exit_conditions:
  analysis_complete:
    - condition: all_five_steps_executed
      description: "五步分析流程全部完成，综合判定已输出"
  early_termination:
    - condition: static_pnl_negative_both_scenarios
      description: "静态分析下两个场景均为负收益，直接判定 NOT_VIABLE 无需继续"
    - condition: invalid_input_detected
      description: "输入参数校验失败（如概率超出范围、金额为负），终止并返回错误"
```

## Action Specification

```yaml
action:
  mode: "on_demand"
  description: "用户触发后执行完整五步分析流程"
  steps:
    - step: validate_inputs
      description: "校验所有输入参数的格式和范围合法性"
    - step: static_pnl_calculation
      description: "Step 1 - 在当前赔率下计算理想化套利收益（假设赔率固定不变）"
      logic: |
        场景 A（事件发生）: 平台 A 盈利 = bet_a * (1/prob_a - 1); 平台 B 亏损 = -bet_b
        场景 B（事件不发生）: 平台 A 亏损 = -bet_a; 平台 B 盈利 = bet_b * odds_b
      output: "static_pnl object"
    - step: bonding_curve_dilution_simulation
      description: "Step 2 - 模拟池子 TVL 增长后用户实际持有份额的变化"
      logic: |
        对每个 growth_scenario 倍数:
          new_tvl = pool_tvl * multiplier
          user_share = bet_amount / (pool_tvl + bet_amount) 在入场时锁定的份额
          diluted_share = bet_amount / new_tvl（保守线性近似）
          estimated_payout = new_tvl * diluted_share * odds_factor
      output: "dilution_table list"
    - step: dynamic_pnl_recalculation
      description: "Step 3 - 将稀释效应代入套利模型重新计算真实 PnL"
      logic: |
        对每个 TVL 增长场景:
          平台 B 实际赔付 = 池子总赔付 * 用户稀释后份额%
          重新计算两个事件场景的净收益
          对比静态 vs 动态的 PnL 差异
      output: "dynamic_pnl_matrix list"
    - step: early_exit_analysis
      description: "Step 4 - 评估在事件结算前沿 Bonding Curve 卖出的收益"
      logic: |
        如果池子 TVL 增长（事件概率向有利方向变化），早期参与者可沿曲线卖出
        估算卖出收益 = f(entry_price, current_curve_price, share)
        对比提前退出 vs 持有到期的收益路径
      output: "early_exit_comparison object"
    - step: comprehensive_verdict
      description: "Step 5 - 汇总所有场景输出综合评估"
      logic: |
        动态 PnL 在所有合理 TVL 场景均为正 -> VIABLE（罕见）
        仅在 TVL 低增长场景为正 -> CONDITIONAL（需监控池子资金变化）
        多数场景为负 -> NOT_VIABLE（稀释效应吞噬利润）
      output: "verdict enum + risk_warnings list + strategy_suggestion string"
```

## Risk Parameters

```yaml
risk_parameters:
  model_assumptions:
    - name: "线性稀释近似"
      description: "Bonding Curve 公式因平台而异，本模型使用线性近似做保守估计，实际曲线可能更陡或更缓"
      mitigation: "用户应对照目标平台的具体 Bonding Curve 公式校准结果"
    - name: "赔率固定假设（平台 A）"
      description: "AMM/OrderBook 平台的赔率也可能在持仓期间变化"
      mitigation: "建议用户在分析时使用当前实时赔率并留意滑点"
  platform_risks:
    - name: "结算规则差异"
      description: "不同平台的事件结算定义和争议解决机制可能不同"
      mitigation: "进入套利前确认两个平台对同一事件的结算规则一致"
    - name: "智能合约风险"
      description: "链上预测市场平台存在合约漏洞或管理员密钥风险"
      mitigation: "优先选择经过审计的平台，控制单笔套利仓位上限"
    - name: "流动性风险"
      description: "Bonding Curve 池子流动性不足时卖出滑点可能极大"
      mitigation: "监控池子 TVL 和深度，设定最低流动性阈值"
  position_limits:
    max_single_bet_pct: 0.05
    description: "单次套利金额不超过总资金的 5%"
  data_limitations:
    - "Antseer MCP 不覆盖预测市场赔率和 TVL 数据，核心数据需用户手动输入"
    - "Bonding Curve 公式因平台而异（42、Polymarket、Azuro 各不相同），通用模型仅做近似估计"
    - "池子 TVL 变化受 KOL 喊单等非结构化因素驱动，难以精确建模"
  disclaimer: "本 Skill 为分析工具，不构成投资建议。预测市场套利涉及平台规则风险、流动性风险和智能合约风险。"
```
