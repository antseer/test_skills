---
name: "polymarket-survival-strategy-evaluator"
description: "Polymarket 存活策略评估与仓位管理计算器。当用户提到 Polymarket 策略评估、预测市场仓位计算、Kelly 公式、EV 计算、prediction market edge、polymarket strategy check、保险模型、贝叶斯套利、体育量化时使用。也适用于用户想检验自己的 Polymarket 策略是否属于历史存活类型，或需要计算任意市场的期望值和 Kelly 仓位，或想知道自己的交易是否具备结构性优势。"
---

# Polymarket 存活策略评估与仓位管理计算器

## Overview

基于蒙特卡洛回测（10000次模拟，97% 死亡率）的方法论，识别策略类型并预警高死亡率模式，计算期望值（EV）和 Kelly 仓位，通过四条件存活检验，给出 ALL CLEAR / PROCEED WITH CAUTION / DO NOT TRADE 的操作建议。

## Demand Context

方法论来源：@NFTCPS 推文（2026-03-23），基于蒙特卡洛模拟研究框架：每个策略从 1 万美元起始，亏损 80% 即视为死亡，跑 10000 个模拟赛季，统计生死比例。

核心结论：Polymarket 不奖励"猜对"，奖励"猜对了 + 下注大小也对了"—— EV × Kelly 的双重正确。

**四类高死亡率策略（禁区）：**
- 动量交易：94.2% 死亡（LMSR 机制下 edge 已被即时吸收）
- 新闻/直觉驱动：91.7% 死亡（公开信息早已 price in）
- 跟单大户：88.3% 死亡（入场时滞导致 edge 衰减为零）
- 纯价差套利：79.1% 死亡（滑点和 LMSR 冲击完全侵蚀利润）

**三类历史存活策略：**
- 保险模型：存活率 71.4%（在 88-98 美分买入 NO，收取风险溢价）
- 体育/事件量化：存活率 68.9%（融合气象/疲劳/历史分布的统计定价）
- 贝叶斯事件套利：存活率 64.2%（突发消息后 3-5 分钟抢先更新概率）

方法论归属：@NFTCPS，Polymarket 蒙特卡洛生存分析。

## Features (Data Inputs)

| 优先级 | 参数名 | 类型 | 必填 | 说明 | 默认值 | 示例值 |
|--------|--------|------|------|------|--------|--------|
| #1 | `market` | string | **是** | Polymarket URL 或市场问题描述。系统自动通过 Antseer MCP (`ant_polymarket`) 拉取当前 YES 价格和盘口数据 | — | `"https://polymarket.com/event/btc-100k"` |
| #2 | `your_true_prob` | float | **是** | 你估算的真实概率（0-1之间） | — | `0.05` |
| — | `market_yes_price` | float | 否 | 手动覆盖 YES 价格（当 MCP 无法获取时的 fallback） | 自动获取 | `0.12` |
| — | `bankroll` | float | 否 | 总本金（美元） | `10000` | `10000` |
| — | `strategy_type` | enum | 否 | insurance / sports_quant / bayesian_arb / custom | `custom` | `insurance` |
| — | `market_type` | enum | 否 | crypto / politics / sports / macro / other | `other` | `crypto` |
| — | `edge_description` | string | 否 | 结构性优势描述（为何你的概率优于市场） | — | `"基于链上数据模型，非公开信息推断"` |
| — | `kelly_fraction` | float | 否 | Kelly 分数（1=全Kelly，0.25=1/4 Kelly） | `0.25` | `0.25` |
| — | `max_position_pct` | float | 否 | 单笔最大仓位占本金的比例上限 | `0.05` | `0.05` |

> **最简调用**：只需 `market` + `your_true_prob` 两个参数即可获得完整的 EV + Kelly 计算报告。

### 数据获取流程

```
market URL/名称 → Antseer MCP (ant_polymarket) → 自动获取:
  - market_yes_price（当前 YES 价格）
  - 盘口深度数据（order book bids/asks）
  - 市场元信息（question, volume, liquidity）

若 MCP 无法获取（URL 无效/API 超时）→ 提示用户手动传 --market_yes_price
```

### MCP 数据源映射

| 数据需求 | MCP 工具 | query_type | 覆盖度 |
|----------|----------|------------|--------|
| Polymarket 市场价格与盘口 | ant_polymarket | market_price / order_book | 完整 |
| Polymarket 市场元信息 | ant_polymarket | market_info | 完整 |
| 市场情绪（crypto 类市场辅助参考） | ant_market_sentiment | coin_detail | 部分 |
| 话题热度变化（贝叶斯套利辅助信号） | ant_market_sentiment | topics_list | 部分 |
| EV 计算 | 无（数学公式） | — | 完整 |
| Kelly 仓位计算 | 无（数学公式） | — | 完整 |
| 体育/气象/球员疲劳数据 | 无（需外部 API） | — | 不覆盖 |

**说明：**
- `ant_polymarket` 封装 Polymarket CLOB API（`https://clob.polymarket.com/`），提供市场价格、盘口深度和元信息
- `ant_market_sentiment` 仅对 crypto 相关 Polymarket 市场有参考价值，政治/体育类不覆盖
- 若 `ant_polymarket` 未就绪或查询失败，用户可通过 `--market_yes_price` 手动输入价格作为 fallback

## Entry Conditions

满足以下任一条件时触发本 Skill：

1. 用户提到 Polymarket 策略评估、polymarket strategy check、策略存活率
2. 用户想计算 Polymarket 某个市场的 EV 或 Kelly 仓位
3. 用户提供了 Polymarket 市场 URL 或 market_yes_price + your_true_prob
4. 用户想知道自己的策略是否属于"死亡模式"
5. 用户提到保险模型、贝叶斯套利、体育量化等预测市场策略类型

## Exit Conditions

满足以下任一条件时完成分析并输出报告：

1. 完成全部 6 步分析并输出综合建议（ALL CLEAR / PROCEED WITH CAUTION / DO NOT TRADE）
2. Step 2 计算出 EV < 0 且 Kelly% < 0（负期望，直接输出 DO NOT TRADE）
3. Step 1 识别出明确的死亡模式策略（输出警告后继续完成 EV/Kelly 计算供参考）
4. 用户明确要求终止分析

## Action Specification

按以下 6 个步骤顺序执行。每步产出作为下一步输入。

### Step 0: 数据获取

从 `market` 参数获取市场数据。

1. 若 `market` 是 Polymarket URL，调用 `ant_polymarket`（query_type=market_info）获取市场元信息（question, volume, liquidity）
2. 调用 `ant_polymarket`（query_type=market_price）获取当前 YES/NO 价格，赋值给 `market_yes_price`
3. 调用 `ant_polymarket`（query_type=order_book）获取盘口深度数据，供可视化使用
4. 若 `ant_polymarket` 调用失败或 `market` 非 URL：
   - 检查用户是否手动提供了 `--market_yes_price`
   - 若未提供，提示用户："无法自动获取市场价格，请手动传入 --market_yes_price=0.xx"，中断执行
   - 若已提供，继续后续步骤（盘口数据为空，可视化中盘口深度图显示"数据不可用"）

**输出**：market_yes_price、盘口数据（可选）、市场元信息（可选）

### Step 1: 策略类型识别与死亡风险预警

识别用户策略是否匹配四类高死亡率模式。

1. 读取 `strategy_type`（默认 `custom`）和 `edge_description`（可选）
2. 检查是否符合以下死亡模式：
   - **动量交易特征**：追涨杀跌、基于价格趋势、"最近一直涨/跌"
   - **新闻/直觉驱动**：没有量化模型、"我觉得"、基于公开新闻判断
   - **跟单操作**：复制他人交易、"某大户也在买"、事后跟进
   - **纯价差套利**：仅依赖 LMSR 价差、无独立概率估算
3. `strategy_type = custom` 且有 `edge_description` 时，从描述中判断最接近哪类
4. **降级处理**：`strategy_type = custom` 且无 `edge_description` 时，输出"未提供策略信息，无法评估死亡风险模式。如需此检查请提供 --strategy_type 或 --edge_description"，策略健康状态设为 UNKNOWN，不阻塞后续步骤
5. 若匹配死亡模式，输出 DANGER 警告并说明对应死亡率（继续后续步骤供参考，不强制中断）
6. 若匹配存活策略类型（insurance/sports_quant/bayesian_arb），输出 SAFE 或 WARNING

**输出**：策略健康状态（SAFE / WARNING / DANGER / UNKNOWN）及原因说明

### Step 2: 期望值（EV）计算

计算当前交易机会的期望回报。

1. 根据 `strategy_type` 决定买入方向：
   - `insurance`：通常买 NO，用 `no_price = 1 - market_yes_price` 计算
   - 其他类型：默认买 YES，可根据 `your_true_prob` 与 `market_yes_price` 的关系判断
2. **买 YES 时**：
   ```
   EV_yes = your_true_prob × (1 / market_yes_price - 1) - (1 - your_true_prob)
   Edge = your_true_prob - market_yes_price
   ```
3. **买 NO 时（保险模型）**：
   ```
   no_price = 1 - market_yes_price
   your_true_prob_no = 1 - your_true_prob（your_true_prob 是 YES 概率时）
   EV_no = your_true_prob_no × (1 / no_price - 1) - (1 - your_true_prob_no)
   Edge = your_true_prob_no - no_price
   ```
4. 判断标准：
   - EV > 0.05：显著正期望
   - 0 < EV ≤ 0.05：微弱正期望，谨慎
   - EV ≤ 0：负期望，不应下注

**输出**：EV 数值、Edge 数值、是否满足 Positive EV 条件

### Step 3: Kelly 公式仓位计算

基于 Kelly 准则计算最优仓位大小。

1. 确定胜率和赔率：
   - 买 YES 时：p = your_true_prob，b = (1 - market_yes_price) / market_yes_price
   - 买 NO 时：p = your_true_prob_no，b = market_yes_price / no_price
2. 计算 Kelly 百分比：
   ```
   Kelly% = (p × b - (1 - p)) / b
   ```
3. 应用保守系数和上限：
   ```
   adjusted_kelly% = min(Kelly% × kelly_fraction, max_position_pct)
   suggested_bet_usd = bankroll × adjusted_kelly%
   ```
4. Kelly% < 0 时输出"不应下注"，停止后续仓位计算

**输出**：全 Kelly 仓位%、调整后仓位%、建议下注金额（美元）

### Step 4: 策略类型专项评估

针对不同存活策略类型进行专项可行性检查。

**4a. 保险模型专项（strategy_type = insurance）：**
- 验证 `market_yes_price` 是否在 0.02-0.12 范围（NO 价格 88-98 美分）。超出范围输出警告
- 检查是否为真实的"尾部风险"事件（非单纯低概率噪音）
- 警告：保险模型需要大样本（100+ 笔）才能体现统计优势，单笔结果意义不大
- 若 `market_type = crypto`，调用 `ant_market_sentiment`（coin_detail）获取相关代币情绪作为辅助参考

**4b. 体育/事件量化（strategy_type = sports_quant）：**
- 检查 `edge_description` 是否包含量化模型依据（历史分布、统计模型、外部数据源）
- 缺少量化依据时输出警告，提示：需要气象数据、球员疲劳度、历史分位数等外部数据源
- 说明外部 API 需求（ESPN API、SportsRadar API 等），本 Skill 无法直接获取

**4c. 贝叶斯事件套利（strategy_type = bayesian_arb）：**
- 检查是否有具体的信息优势来源
- 调用 `ant_market_sentiment`（topics_list）监控相关话题热度变化速率，作为辅助信号
- 提醒：3-5 分钟窗口期极短，需要预设触发条件和自动化下单能力

**4d. 自定义策略（strategy_type = custom）：**
- 根据 `edge_description` 内容判断是否有量化依据和结构性优势描述
- 对照存活策略特征给出最接近的类型建议

**输出**：策略类型专项通过/警告清单

### Step 5: 结构性优势评估（四条件核查）

对照四条件存活检验逐项核查。

1. **条件 1 - 正期望值**：来自 Step 2，EV > 0 则通过
2. **条件 2 - Kelly 仓位管理**：来自 Step 3，Kelly% > 0 且调整后仓位有上限则通过
3. **条件 3 - 模型驱动**：`edge_description` 包含量化依据（历史数据、统计模型、量化信号）而非纯直觉则通过
4. **条件 4 - 结构性优势**：`edge_description` 描述了散户无法复制的能力（专有数据、自动化系统、特殊访问）则通过

评级标准：
- 4/4 条件通过 → PASS
- 3/4 条件通过 → CAUTION
- 0-2/4 条件通过 → FAIL

**输出**：四条件逐项通过情况（含 ✅/❌ 标注）、综合评级（PASS/CAUTION/FAIL）

### Step 6: 综合评估与最终建议

汇总所有步骤，给出最终操作建议。

1. 按以下标准判断：
   - **ALL CLEAR**：EV > 0 且 Kelly% > 0 且四条件 PASS 且策略类型 SAFE
   - **PROCEED WITH CAUTION**：部分条件满足（四条件 CAUTION，或 EV 微弱正期望，或策略类型 WARNING）
   - **DO NOT TRADE**：EV ≤ 0 或 Kelly% < 0 或四条件 FAIL 或策略类型 DANGER
2. 给出具体的仓位建议（来自 Step 3）或拒绝理由
3. 列出需要特别注意的风险点

### 报告结构

始终使用此模板输出最终报告：

```
📊 Polymarket 策略评估报告
═══════════════════════════════════════

市场: {market_question}
策略类型: {strategy_type_display}

【策略健康检查】
{SAFE/WARNING/DANGER} — {原因说明}

【期望值计算】
• 市场 YES 价格: {market_yes_price}（买的是 {YES/NO} = {effective_price}）
• 你估算的真实概率: {your_true_prob}
• EV: {ev_value}（{正期望/负期望} {✅/❌}）
• Edge: {edge_value}（概率优势 {+/-}{edge_pct}%）

【Kelly 仓位建议】
• 全 Kelly: {kelly_full_pct}% of bankroll
• {kelly_fraction} Kelly（保守）: {kelly_adjusted_pct}% of bankroll
• 建议下注: ${suggested_bet_usd} / ${bankroll} 本金
• 最大单笔上限（{max_position_pct*100}%）: ${max_position_usd}

【四条件核查】
{✅/❌} 每笔正期望值 (EV = {ev_value})
{✅/❌} Kelly 仓位管理（{kelly_fraction} Kelly = {kelly_adjusted_pct}%）
{✅/❌} 模型驱动（{判断依据}）
{✅/❌} 结构性优势（{判断依据}）

综合评级: {✅/⚠️/❌} {PASS/CAUTION/FAIL}（{score}/4 条件满足）

【建议】
{ALL CLEAR / PROCEED WITH CAUTION / DO NOT TRADE}
{具体操作建议或拒绝原因}

⚠️ 风险提示: {relevant_warnings}
```

## Risk Parameters

| 参数 | 约束 | 说明 |
|------|------|------|
| Kelly 分数 | 默认 0.25（1/4 Kelly） | 保守选择，降低破产概率 |
| 单笔最大仓位 | 默认 5%（max_position_pct） | 防止单笔过度集中 |
| EV 显著性门槛 | > 0.05 为显著正期望 | 微弱正期望（0~0.05）谨慎对待 |
| 保险模型价格范围 | YES 价格 0.02-0.12 | NO 价格需在 88-98 美分区间 |
| 保险模型样本要求 | 100+ 笔 | 单笔保险意义不大，需大样本体现统计优势 |
| 贝叶斯套利窗口 | 3-5 分钟 | 需预设自动化触发，手动操作时间不足 |
| MCP 情绪数据适用范围 | 仅 crypto 类市场 | 政治/体育市场情绪不覆盖 |

**重要边界：**
- 本 Skill 不执行实际交易，仅输出分析建议
- `your_true_prob` 的准确性完全依赖用户自身的概率估算能力，Skill 无法验证
- EV 和 Kelly 计算基于用户输入的概率，结果质量取决于输入质量
- Monte Carlo 结论来自回测（97% 死亡率），实盘情况可能不同
- Polymarket 在部分司法管辖区存在合规限制

## 首次安装提示

```
目标用户：Polymarket 活跃交易者、预测市场研究者、量化策略开发者
使用场景：在 Polymarket 发现交易机会时，评估策略类型、计算 EV 和 Kelly 仓位、判断是否具备结构性优势
如何使用：/polymarket-survival-strategy-evaluator --strategy_type=insurance --market_yes_price=0.05 --your_true_prob=0.03 --bankroll=10000
```

## 示例

**示例 1: 保险模型评估**
输入: `/polymarket-survival-strategy-evaluator --strategy_type=insurance --market_question="Will XYZ token get listed on Binance Q2?" --market_yes_price=0.05 --your_true_prob=0.97 --bankroll=10000 --market_type=crypto`
输出: 买 NO 在 95 美分，EV 计算，Kelly 仓位，四条件核查，综合建议

**示例 2: 贝叶斯套利检查**
输入: `/polymarket-survival-strategy-evaluator --strategy_type=bayesian_arb --market_question="Will Fed cut rates in March?" --market_yes_price=0.35 --your_true_prob=0.60 --bankroll=5000 --edge_description="内部模型基于实时美联储声明 NLP 分析，比市场更新快 2 分钟"`
输出: 话题热度辅助信号 + EV 计算 + 3-5 分钟窗口期警告 + Kelly 仓位

**示例 3: 动量策略警告**
输入: `/polymarket-survival-strategy-evaluator --strategy_type=custom --market_yes_price=0.60 --your_true_prob=0.75 --bankroll=2000 --edge_description="这个市场最近一直在涨，我觉得还会继续"`
输出: DANGER 警告（动量/直觉驱动，死亡率约 91-94%），尽管 EV 计算为正，建议 DO NOT TRADE
