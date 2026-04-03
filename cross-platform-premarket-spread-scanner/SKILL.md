---
name: "cross-platform-premarket-spread-scanner"
description: "扫描同一代币在多个盘前市场（ASP、Binance Pre-market、Polymarket）之间的价差，识别跨平台套利机会，并给出空投持仓的对冲仓位建议。当用户提到盘前套利、price spread、pre-market arbitrage、TGE 套利、盘前价差、跨平台对冲、空投对冲、airdrop hedge 等关键词时触发。适用于代币空投查询上线、TGE 公告发布、多平台盘前同时开放报价的时间窗口。"
---

# Cross-Platform Premarket Spread Scanner（跨平台盘前价差套利扫描）

## Overview

在同一代币于多个盘前市场（ASP/Binance/Polymarket）同时报价时，计算各平台两两价差，评估套利可执行性，结合空投持仓量输出对冲仓位建议，最终给出 A/B/C/D 套利评级与执行计划。

方法论来源：@BTC_Alert_ 对 $EDGEX 空投盘前套利分析（2026-03-20）。

---

## Demand Context

- 代币在 TGE 前往往同时在多个预测/盘前市场报价，各平台流动性和参与者结构不同导致价差显著。
- 空投猎人持有隐式多头（待发空投），通过"高价平台做空 + 低价平台做多"可锁定无风险价差，同时对冲持仓风险。
- 关键时间窗口：空投查询界面上线 → TGE 交割，通常 7 天内。

---

## Features (Data Inputs)

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| symbol | string | 是 | 目标代币符号，如 "EDGEX" | — |
| platforms | array | 否 | 要扫描的盘前平台 | ["ASP", "Binance", "Polymarket"] |
| min_spread_pct | float | 否 | 触发报警的最小价差百分比（相对低价平台） | 15 |
| reference_token | string | 否 | 历史类比参考代币，如 "OPN" | — |
| airdrop_amount_est | float | 否 | 预估空投数量；0 表示跳过仓位计算 | 0 |
| time_range | string | 否 | 价差监控时间窗口 | "24h" |
| fdv_breakeven | float | 否 | 盈亏平衡 FDV 估算（美元） | — |

**数据来源映射：**

| 数据需求 | MCP 工具 | query_type | 覆盖度 |
|----------|----------|------------|--------|
| TGE/解锁时间节点 | ant_token_analytics | emissions, asset=symbol | 完整 |
| 代币解锁批次详情 | ant_token_analytics | emission_detail, asset=symbol | 完整 |
| 代币情绪分数 | ant_market_sentiment | coin_detail, coin=symbol | 部分（新代币可能缺失） |
| 参考代币历史价格 | ant_spot_market_structure | coins_markets, ids=ref_token | 部分（仅已上线代币） |
| ASP 盘前价格 | WebFetch / Aspecta AI REST API | — | 外部 |
| Binance 盘前价格 | WebFetch / Binance API（-PRE 后缀） | — | 外部 |
| Polymarket 隐含价格 | WebFetch / Polymarket Gamma API | — | 外部 |
| Order Book 深度 | WebFetch / 各平台 Depth API | — | 外部 |

---

## Entry Conditions

以下任意一项满足时开始扫描：

- 用户明确提供 `symbol` 并请求盘前价差或套利分析
- 代币 TGE 日期在未来 7 天内（通过 `ant_token_analytics` 确认）
- 用户提到"盘前套利"、"pre-market arb"、"价差扫描"、"TGE 套利"、"空投对冲"等关键词

以下情况**跳过**本 Skill：
- 代币已完成 TGE 并在现货交易所上线（盘前市场已关闭）
- 用户仅请求链上持仓查询或基本面研究，与盘前价差无关

---

## Exit Conditions

输出完整套利扫描报告后退出，包含：

1. 价格矩阵（各平台当前报价）
2. 最优价差对（做空腿/做多腿）
3. 实际可套利价差（扣除手续费和滑点）
4. FOMO 风险等级
5. 对冲仓位建议（如提供 `airdrop_amount_est`）
6. 历史类比结论（如提供 `reference_token`）
7. 套利评级（A/B/C/D）+ 执行计划

---

## Action Specification

### Step 1：盘前触发信号识别

调用 `ant_token_analytics`（query_type: `emissions`, asset=symbol），确认 TGE 是否在未来 7 天内。

- 若 TGE 已过且代币已上线现货，停止流程并告知用户盘前窗口已关闭。
- 若 TGE 在 7 天内，标记为"高时效窗口"，继续执行。
- 若无法获取 TGE 日期（新代币），记录"TGE 日期未知"并继续，以用户提供信息为准。

### Step 2：多平台盘前价格采集

依次获取各平台价格（按优先顺序尝试）：

**ASP（Aspecta AI）价格：**
使用 `WebFetch` 访问 `https://aspecta.ai` 或其 REST API，搜索 symbol 对应盘前市场价格。若无法直接获取，使用 `WebSearch` 搜索 `"{symbol} ASP premarket price site:aspecta.ai"` 作为备选。

**Binance Pre-market 价格：**
使用 `WebFetch` 调用 Binance API：`https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}PRE-USDT`。若 404，尝试 `{SYMBOL}-PRE`。

**Polymarket 隐含价格：**
使用 `WebFetch` 访问 `https://gamma-api.polymarket.com/markets?keyword={symbol}` 获取相关市场，提取最高流动性市场的当前均衡价格（以 USDC 计）。

价格采集失败时，在报告中注明"数据获取失败"并跳过该平台，不中断流程。

对每对平台计算：
```
spread_pct = (price_high - price_low) / price_low × 100
```
找出价差最大的平台对。只有 `spread_pct >= min_spread_pct` 才进入后续分析。

### Step 3：流动性深度评估

对做空腿和做多腿平台各自获取 Order Book 深度（目标执行量：10,000 USDT）：

- **Binance**：`WebFetch` 调用 `https://api.binance.com/api/v3/depth?symbol={SYMBOL}PRE-USDT&limit=20`
- **ASP**：`WebFetch` 尝试获取，或使用"薄流动性"作为保守默认值
- **Polymarket**：通过 gamma-api 获取各 outcome 的流动性

计算预期滑点，得出"实际可套利价差"：
```
executable_spread = nominal_spread - slippage_both_legs - fees_both_legs
```

若 `executable_spread <= 0`，标记为"不可执行"，但仍输出分析，不终止报告。

### Step 4：社区情绪 FOMO 校验

调用 `ant_market_sentiment`（query_type: `coin_detail`, coin=symbol）获取情绪分和社交提及量趋势。

FOMO 判断标准：
- 情绪分 > 75 或 24h 提及量增长 > 200% → 高 FOMO
- 情绪分 50-75 或增长 100-200% → 中等 FOMO
- 其余 → 低 FOMO

若 `ant_market_sentiment` 无数据（新代币），使用 `WebSearch` 搜索 `"{symbol} TGE airdrop twitter"` 作为定性补充，基于结果给出保守估算。

高 FOMO 时，做空腿建议止损价 = 当前高价平台报价 × 1.3。

### Step 5：历史类比走势对比（可选）

若提供 `reference_token`：

调用 `ant_spot_market_structure`（query_type: `coins_markets`, ids=reference_token）获取参考代币历史价格。

提取参考代币 TGE 前 7 天的价格走势（如有），与当前 symbol 盘前价格结构进行定性对比：
- 当前价格处于参考代币同期高位/中位/低位
- 走势相似度：High / Medium / Low

若参考代币数据不可用（盘前历史不在 MCP 覆盖范围），明确说明"历史盘前数据不可获取，以下对比基于已上线后的价格数据"。

### Step 6：代币解锁与空投仓位计算

若 `airdrop_amount_est > 0`：

调用 `ant_token_analytics`（query_type: `emission_detail`, asset=symbol）确认 TGE 交割批次时间。

计算：
```
airdrop_implicit_long_value = airdrop_amount_est × price_short_platform
hedge_ratio = min(1.0, target_arb_capital / airdrop_implicit_long_value)
max_safe_position_usd = airdrop_implicit_long_value × hedge_ratio
```

避免超对冲（hedge ratio > 1.0 意味着做空头寸超过空投隐式多头，风险敞口反转方向）。

若 `airdrop_amount_est = 0`，跳过仓位计算，输出"未提供空投量，仓位建议基于用户自定义风险偏好"。

### Step 7：综合套利评级与执行建议

根据以下矩阵输出评级：

| 条件 | A（立即执行） | B（条件执行） | C（观望） | D（放弃） |
|------|--------------|--------------|----------|----------|
| 实际可套利价差 | > min_spread | > min_spread | 不足 | 不足或极差 |
| FOMO 风险 | Low/Medium | High | 任意 | Extreme |
| 流动性 | 充足 | 薄 | — | 极差 |

输出执行建议：
- 做空平台 + 开空价格
- 做多平台 + 开多价格
- 建议仓位（USDT，双腿各）
- 止损价位（高 FOMO 时必须给出）

---

## Risk Parameters

- `min_spread_pct`：默认 15%，低于此阈值意味着手续费+滑点大概率吃掉价差
- 流动性薄时（ASP 尤其如此），建议分批入场，单笔不超过 5,000 USDT
- hedge ratio 上限 1.0，超对冲将导致方向性风险敞口反转
- 高 FOMO（> 75 分）时强制止损，止损位 = 做空平台当前价 × 1.3
- cc 风险（代币未能成功上线现货）是尾部风险，无法量化，需人工判断
- 本 Skill 不执行交易，所有建议均为参考，用户自行决策

---

## 首次安装提示

```
目标用户：空投猎人、套利交易员、专业投研人员
使用场景：代币 TGE 前 7 天内，多平台盘前价差显著时
如何使用：/cross-platform-premarket-spread-scanner EDGEX --platforms ASP,Binance,Polymarket --airdrop_amount_est 200000 --reference_token OPN
```

---

## 输出报告模板

始终使用以下模板：

```
=== 跨平台盘前价差套利扫描报告 ===
代币: ${symbol} | 扫描时间: {scan_time} UTC

【触发信号】
  TGE 日期: {tge_date}
  时效窗口: {tge_within_7d}

【价格矩阵】
  {platform_1}: ${price_1}
  {platform_2}: ${price_2}
  {platform_3}: ${price_3}（如有）

【最优价差对】
  做空: {short_platform} @ ${short_price}
  做多: {long_platform} @ ${long_price}
  名义价差: ${spread_usd}（{spread_pct}%）
  预估双腿手续费+滑点: ${cost}
  实际可套利价差: ${executable_spread} {is_executable_indicator}

【FOMO 校验】
  情绪分: {sentiment_score}/100（{fomo_label}）
  FOMO 风险等级: {fomo_level}
  建议止损（做空腿）: ${stop_loss}（如适用）

【解锁与仓位】（如提供 airdrop_amount_est）
  TGE 交割日期: {tge_delivery_date}
  空投预估量: {airdrop_amount_est} {symbol}
  空投隐式多头价值: ~${airdrop_value}
  推荐对冲比例: {hedge_ratio}
  最大安全仓位: ${max_safe_position_usd} USDT 双腿各

【历史类比】（如提供 reference_token）
  参考代币 ${reference_token}: 走势相似度 {similarity}
  当前 {symbol} 定价对应 {reference_token} 同期 {position_vs_ref}

【综合评级】: {grade}（{grade_label}）
{grade_rationale}

【执行建议】
  做空腿: {short_platform} 开空 {symbol}，{position_size} USDT 等值
  做多腿: {long_platform} 做多 {symbol}，{position_size} USDT 等值
  止损 ({short_platform} 空仓): ${stop_loss}
  预期收益: ${expected_profit_per_unit}/枚 × 建议仓位

【风险提示】
  1. {risk_note_1}
  2. {risk_note_2}
  3. cc 风险（代币 listing 取消/推迟）可能打破盘前转现货预期，需人工评估
  4. 本报告仅供参考，不构成投资建议，套利交易存在市场风险

【免责声明】
  分析方法论归属原作者 @BTC_Alert_，本 Skill 基于其公开推文内容自动生成。
  不构成投资建议。
```
