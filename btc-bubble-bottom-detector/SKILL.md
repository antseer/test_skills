---
name: btc-bubble-bottom-detector
version: "1.0.0"
user-invocable: true
description: |
  BTC 泡沫指数底部探测器。综合 MVRV、NVT Golden Cross、市场情绪、ETF 资金流、
  交易所储备等链上估值指标，判断 BTC 是否处于历史底部区域，输出底部概率评分和建议。
  需要 Antseer MCP 服务器（见 README.md 安装说明）。
  Use when asked to "泡沫指数", "底部检测", "BTC见底了吗", "bubble index", "bottom signal",
  "抄底信号", "BTC底部", "熊市底部", "是否可以抄底", "MVRV底部"
argument-hint: "[目标价] [时间窗口]  例: 200000 2y"
allowed-tools:
  - mcp__ANTSEER_MCP_ID__ant_spot_market_structure
  - mcp__ANTSEER_MCP_ID__ant_token_analytics
  - mcp__ANTSEER_MCP_ID__ant_market_sentiment
  - mcp__ANTSEER_MCP_ID__ant_etf_fund_flow
  - mcp__ANTSEER_MCP_ID__ant_fund_flow
metadata:
  requires:
    mcpServers:
      - name: antseer
        description: "Antseer on-chain data MCP — provides spot price, MVRV, NVT, sentiment, ETF flow, exchange reserve data"
author: mike
license: MIT
---

# BTC 泡沫指数底部探测器

基于 @monkeyjiang 的分析方法论：比特币泡沫指数跌至 10 附近是历史验证的底部信号。
由于原始泡沫指数为第三方专有指标，本 skill 使用 MVRV + NVT Golden Cross + 市场情绪 + ETF 资金流 + 交易所储备组合构建等效的底部检测信号。

历史回测显示 MVRV < 1.0 与泡沫指数 ~10 的底部判定高度重合。

## 输入

`$ARGUMENTS` = 可选参数，格式: `[目标价] [时间窗口]`

- 目标价（数字）: 用户的中长期 BTC 目标价（USD），用于计算风险回报比
- 时间窗口（如 2y / 1y / 6m）: 目标价对应的时间预期

示例:
- `/btc-bubble-bottom-detector` — 仅输出底部评分
- `/btc-bubble-bottom-detector 200000 2y` — 含风险回报分析

## 步骤

### 1. 并行拉取数据

同时发起以下 6 个查询：

**查询 A — BTC 当前价格：**
- 工具: `ant_spot_market_structure`
- query_type: `simple_price`
- ids: `bitcoin`

**查询 B — MVRV 比率：**
- 工具: `ant_token_analytics`
- query_type: `mvrv`
- asset: `btc`
- window: `day`
- limit: `365`

**查询 C — NVT Golden Cross：**
- 工具: `ant_token_analytics`
- query_type: `nvt_golden_cross`
- asset: `btc`
- window: `day`
- limit: `90`

**查询 D — 市场情绪：**
- 工具: `ant_market_sentiment`
- query_type: `coin_detail`
- coin: `bitcoin`

**查询 E — ETF 资金流（近 30 日）：**
- 工具: `ant_etf_fund_flow`
- query_type: `btc_etf_flow`
- limit: `30`

**查询 F — 交易所储备（近 90 日）：**
- 工具: `ant_fund_flow`
- query_type: `exchange_reserve`
- asset: `btc`
- exchange: `binance`
- limit: `90`

### 2. 指标分析与评分

对每项数据进行独立评估，然后汇总为底部概率评分（0-100）：

**MVRV 评分（满分 30）：**
- MVRV < 1.0 → 强底部信号，+30 分
- MVRV 1.0 - 1.5 → 温和底部信号，+15 分
- MVRV > 1.5 → 不在底部，+0 分

**NVT Golden Cross 评分（满分 15）：**
- NVT Golden Cross 处于低位区间（下穿或负值区域）→ +15 分
- NVT Golden Cross 处于中位 → +7 分
- NVT Golden Cross 处于高位 → +0 分

**市场情绪评分（满分 15）：**
- Galaxy Score < 40（恐慌区间）→ +15 分
- Galaxy Score 40-60 → +7 分
- Galaxy Score > 60 → +0 分

**ETF 资金流评分（满分 15）：**
- 近 30 日 ETF 净流入 > 0（机构在底部积累）→ +15 分
- 近 30 日 ETF 净流入接近 0 → +7 分
- 近 30 日 ETF 净流出 → +0 分

**交易所储备评分（满分 10）：**
- 90 日储备趋势下降 > 3%（供应紧缩）→ +10 分
- 90 日储备趋势下降 1-3% → +5 分
- 90 日储备趋势上升或持平 → +0 分

**补充说明：**
- MVRV 权重最高，因为它是最直接的链上估值指标，历史上与底部的相关性最强
- ETF 资金流反映机构行为，是 2024 年后新增的重要底部确认信号
- 交易所储备下降代表长期持有者在提币囤积，是慢变量确认信号

### 3. 信号强度判定

根据总分判定信号强度：
- **70-100 分**: 🟢 **强底部信号** — 多项指标共振确认底部区域
- **40-69 分**: 🟡 **温和底部信号** — 部分指标指向底部，建议结合宏观判断
- **0-39 分**: 🔴 **尚未确认** — 当前不满足底部条件

### 4. 风险回报计算（仅当用户提供目标价时）

- 潜在收益率 = (目标价 - 当前价) / 当前价 × 100%
- 历史同级别底部最大回撤：参考 MVRV 处于相似水平时的历史最大下跌幅度（通常 15-25%）
- 风险回报比 = 潜在收益率 / 历史最大回撤

### 5. 输出格式

用中文输出，严格使用以下格式：

```
=== BTC 底部探测报告 ===
时间: YYYY-MM-DD

当前价格: $XX,XXX
底部评分: XX/100 — 🟢/🟡/🔴 信号强度描述

┌─────────────────────────────────────────────────┐
│ 指标              │ 当前值     │ 信号      │ 得分  │
├─────────────────────────────────────────────────┤
│ MVRV              │ X.XX       │ XX        │ +XX   │
│ NVT Golden Cross  │ XX         │ XX        │ +XX   │
│ 市场情绪          │ XX/100     │ XX        │ +XX   │
│ ETF 30日净流入    │ +/-$X.XB   │ XX        │ +XX   │
│ 交易所储备        │ 90日↓/↑X%  │ XX        │ +XX   │
└─────────────────────────────────────────────────┘

（如有目标价）
风险回报分析:
  目标价: $XXX,XXX (Xy)
  潜在收益: +XXX%
  历史同级别底部最大回撤: -XX%
  风险回报比: X.X:1

历史底部对比:
  简要列出 MVRV 处于相似水平时的历史时间点和对应价格

结论: 一段话总结当前底部状态和建议

⚠️ 免责声明: 本分析基于链上估值指标的历史统计规律，
不能精确预测底部价格或反弹时间。MVRV 等指标在极端行情中可能失效。
ETF 数据存在 T+1 延迟。不构成投资建议。
```

如果底部评分低于 40（尚未确认），仍然输出完整报告，但在结论中明确说明当前不满足底部条件，并指出哪些指标需要进一步恶化才可能触发底部信号。
