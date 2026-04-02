# 预测市场跨平台套利分析器

Prediction Market Cross-Platform Arbitrage Analyzer

## 功能概述

本 Skill 用于评估预测市场跨平台套利策略的可行性与风险。当两个预测市场平台（如 Polymarket/42 与 Opinion）对同一事件的定价存在差异时，通过六步分析流程揭示套利机会的真实收益与风险。

核心发现：Bonding Curve 机制下，后进场者的资金会稀释先行者的赔付权益，导致入场时的名义赔率无法在结算时维持。静态套利计算在动态博弈环境中往往不成立。

## 分析流程

1. **市场状态快照** -- 采集双平台当前定价/TVL 数据
2. **静态套利计算** -- 假设赔率不变，计算两种事件结果下的理论收益
3. **Bonding Curve 稀释建模** -- 模拟池子 TVL 增长对用户份额和有效赔率的影响
4. **多情景动态 P&L 模拟** -- 在 4 个市场演变场景下计算组合盈亏
5. **流动性与退出路径分析** -- 评估中途退出的滑点和可行性
6. **综合评估** -- 输出风险评级（推荐/谨慎/不推荐）和操作建议

## 使用方法

### Python 调用

```python
from arbitrage_analyzer import run_analysis, format_report

params = {
    "event_description": "某项目是否在2026年底前发币",
    "platform_a": "42 (Polymarket)",
    "platform_b": "Opinion",
    "position_a_type": "NO (No Token Launch)",
    "position_b_type": "YES (63% 概率发币)",
    "investment_a": 500,
    "investment_b": 5000,
    "odds_a_entry": 18,
    "prob_b_entry": 0.63,
    "pool_tvl_a": 4000,
    "pool_type": "bonding_curve",
    "time_horizon": "2026-12-31",
}

result = run_analysis(params)
print(format_report(result))
```

### 命令行

```bash
python arbitrage_analyzer.py
```

直接运行会使用 PRD 中的原始推文案例作为默认输入参数。

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| event_description | string | 是 | 预测事件描述 |
| platform_a | string | 是 | 平台 A 名称 |
| platform_b | string | 是 | 平台 B 名称 |
| position_a_type | string | 是 | 平台 A 头寸方向 |
| position_b_type | string | 是 | 平台 B 头寸方向 |
| investment_a | number | 是 | 平台 A 投入金额 (USD) |
| investment_b | number | 是 | 平台 B 投入金额 (USD) |
| odds_a_entry | number | 是 | 平台 A 进入时赔率 |
| prob_b_entry | number | 是 | 平台 B 进入时概率 (0-1) |
| pool_tvl_a | number | 否 | 平台 A 池子当前 TVL |
| pool_type | string | 否 | 池子定价机制 (默认 bonding_curve) |
| time_horizon | string | 否 | 事件到期时间 |

## 输出

- **risk_rating**: 推荐 / 谨慎 / 不推荐
- **static_arbitrage_pnl**: 两种事件结果下的静态 P&L
- **dilution_table**: TVL 变化 vs 有效赔率 vs 份额稀释
- **scenarios**: 4 个情景下的盈亏模拟
- **exit_slippage_estimate**: 中途退出滑点估算
- **recommendation**: 具体操作建议

## 数据源覆盖

Antseer MCP 对预测市场数据的覆盖有限：
- 完全覆盖: 稳定币储备 (ant_stablecoin)、地址余额 (ant_address_profile)
- 部分覆盖: 协议 TVL、条件代币价格、链上交易记录
- 未覆盖: Bonding Curve 合约状态、对手平台定价、池子参与者数据、历史赔率变化

核心定价数据需用户从平台手动获取并输入。

## 局限性

- 不能自动抓取预测市场平台实时数据
- 不能预测赔率走向（情景模拟不等于价格预测）
- 默认 Bonding Curve 模型参数可能与平台实际实现有差异
- 不覆盖智能合约安全风险评估

## 免责声明

本 Skill 基于推文内容自动生成，分析方法论归属原作者 @Wuhuoqiu。不构成投资建议。预测市场参与涉及本金损失风险。
