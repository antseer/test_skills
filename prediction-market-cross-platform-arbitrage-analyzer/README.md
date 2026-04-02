# Prediction Market Cross-Platform Arbitrage Analyzer

## 简介

评估预测市场跨平台套利策略在 Bonding Curve 动态定价机制下的真实可行性。当两个预测市场平台对同一事件存在赔率差异时，通过五步分析流程输出量化的风险评估和策略建议。

## 使用方式

### 基本调用

```bash
claude -p "使用 prediction-market-cross-platform-arbitrage-analyzer 分析以下套利机会:
- 平台 A: 42 平台, 池子: 'No Token Launch', 当前 TVL: 4000U, 赔率 1:10
- 平台 B: Polymarket, 事件概率: 63%, 头寸成本: 5000U
- 我的投入: 500U (平台 A), 入场时池子 TVL: 1500U
- 事件: 某项目是否在 2026 年底前发币
- Bonding Curve 类型: exponential"
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| platform_a | 是 | Bonding Curve 机制平台名称 |
| platform_b | 是 | 对手方平台名称 |
| event_description | 是 | 预测事件描述 |
| pool_a_name | 是 | 平台 A 目标池子名称 |
| pool_a_current_tvl | 是 | 平台 A 池子当前 TVL (USD) |
| pool_a_entry_tvl | 否 | 进场时池子 TVL (USD)，用于回溯 |
| pool_a_odds | 否 | 平台 A 当前赔率（如 1:10） |
| platform_b_probability | 是 | 平台 B 事件概率 (%) |
| platform_b_position_cost | 是 | 平台 B 头寸成本 (USD) |
| user_investment | 是 | 用户在平台 A 投入 (USD) |
| time_horizon | 否 | 套利时间窗口（默认 1 year） |
| bonding_curve_type | 否 | Bonding Curve 类型（默认 exponential） |

### MCP 数据源依赖

本 Skill 调用以下 Antseer MCP 工具获取辅助数据：

- `ant_market_sentiment` (coin_detail) -- 相关代币的市场情绪
- `ant_market_sentiment` (topics_list) -- 事件相关社交话题热度
- `ant_protocol_tvl_yields_revenue` (protocol_tvl) -- 预测市场协议 TVL 参考

核心定价数据（赔率、概率、TVL）由用户手动输入，因为 MCP 不直接覆盖预测市场平台 API。

## 分析流程

1. **双平台赔率快照** -- 记录静态赔率差和理论套利空间
2. **Bonding Curve 稀释模拟** -- 模拟池子膨胀下份额占比和实际赔率变化
3. **情景分析矩阵** -- 3x3 盈亏矩阵（事件结果 x 市场情景）
4. **市场情绪评估** -- 通过 MCP 获取情绪数据，预判资金流向
5. **综合评估** -- 输出可行性评级和策略建议

## 输出示例

```
事件: 某项目是否在 2026 年底前发币
可行性评级: not_feasible（静态套利假设失效）
原因: 在"事件未发生"情景中，池子规模膨胀导致实际赔付远低于名义赔率
盈亏平衡池规模: 5,500U
推荐策略: 视为方向性交易 + 择时退出，非无风险套利
```

## 适用场景

- 发现 Polymarket 与其他预测市场平台之间的赔率差异
- 评估 Bonding Curve 机制下的动态套利风险
- 对比 "持有到期" vs "中途退出" 的盈亏预期
- 量化份额稀释对实际赔率的影响

## 注意事项

- 本 Skill 为分析工具，不执行自动交易
- Bonding Curve 模型为近似计算，实际结果取决于平台合约实现
- 建议定期重新运行分析以反映最新市场数据
- 不构成投资建议，预测市场交易存在本金全损风险
