---
name: "narrative-driven-token-discovery"
description: "扫描链上与社交媒体热点叙事匹配的代币，评估叙事生命周期阶段和代币基本面，输出综合信号评分。当用户提到叙事发现、narrative discovery、叙事匹配、narrative match、热点代币扫描、trending narrative scan、MEME 叙事交易、社交热点代币、新闻驱动交易，或者想知道某个热点话题有没有对应链上代币、某个叙事处于什么阶段时，使用此 Skill。"
metadata:
  generated_at: "2026-04-09 05:43:47"
---

## Overview

根据用户输入的热点叙事关键词，扫描链上与该叙事名称/符号匹配的代币，通过社交热度、持仓分布、Smart Money 进场状态、交易活跃度四个维度评估代币质量，并判断叙事所处生命周期阶段（萌芽/爆发/高潮/衰退），输出综合信号评分和操作建议。

## Demand Context

源自 @thecryptoskanda 对顶尖 MEME 交易员 @Clukz 的交易方法论拆解：以实时社交/新闻推送作为信号源，秒级在链上代币列表中找到与当前热点叙事匹配的代币，以极快速度进场，然后按预设策略阶梯式退出。核心链条为：信号源 -> 秒级验证 -> 预设买入 -> 分批卖出。

本 Skill 将该方法论中"信号源 -> 代币匹配 -> 多维评估"的部分自动化，从实时推送模式改为主动查询模式，适用于任何"社交热点 -> 链上代币"的匹配场景。

方法论归属：@thecryptoskanda（拆解）和 @Clukz（原始交易方法）。

## Features (Data Inputs)

### 必填参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| narrative_keyword | string | 当前热点叙事的关键词（中英文均可） | Aliens, UFO, DOGE, 伊朗 |

### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| chain | string | solana | 目标链，限定扫描范围 |
| time_window | string | 24h | 叙事热度评估时间窗口 |
| min_liquidity_usd | number | 10000 | 最小流动性过滤阈值（USD） |
| min_social_score | number | 无 | 最小社交热度分数阈值 |
| top_n | number | 10 | 返回匹配代币数量上限 |

## Entry Conditions

满足以下任一条件时触发本 Skill：

1. 用户主动请求叙事代币扫描（如 `/narrative-driven-token-discovery Aliens`）
2. 社交媒体出现突发热点话题，用户想快速了解有无对应链上代币
3. 用户看到某条新闻/推文后想评估叙事交易机会

## Exit Conditions

满足以下条件时 Skill 执行完成：

1. 已完成全部 6 个分析步骤
2. 已输出叙事生命周期阶段判断（emerging / exploding / peaking / fading）
3. 已输出每个匹配代币的综合信号评分和操作建议

## Action Specification

### Step 1: 叙事信号捕获与验证

调用 `ant_market_sentiment`，参数：
- query_type: `topics_list`（获取热门话题列表）

再调用 `ant_market_sentiment`，参数：
- query_type: `topic_detail`
- topic: `{narrative_keyword}`

分析逻辑：
1. 检查 narrative_keyword 是否出现在热门话题列表中
2. 获取该话题的社交热度得分、讨论量趋势、情绪分布
3. 如果话题未出现在热门列表中，标注为"早期/小众叙事"，继续后续步骤

记录：`narrative_heat_score`（0-100）、`narrative_trend`（rising/stable/declining）、`sentiment`（positive/neutral/negative）

### Step 2: 叙事关联代币扫描

调用 `ant_meme`，参数：
- query_type: `search_pairs`
- query: `{narrative_keyword}`

同时调用 `ant_meme`，参数：
- query_type: `trending_tokens`

分析逻辑：
1. 用 narrative_keyword 搜索链上代币对，获取名称/符号包含关键词的代币列表
2. 获取当前 trending 代币列表，检查是否有交集（交集代币标注"热门重叠"）
3. 按流动性 >= min_liquidity_usd 过滤，排除极低流动性代币
4. 对每个匹配代币记录：地址、名称、符号、链、当前价格、流动性、创建时间

记录：匹配代币候选列表（最多 top_n 个），按流动性降序排序

如果无匹配代币，直接输出"未找到匹配代币"并结束。

### Step 3: 代币基本面快速评估

对每个候选代币逐一检查：

调用 `ant_meme`，参数：
- query_type: `token_info`
- chain_id: `{chain}`
- token_addresses: `{候选代币地址}`

调用 `ant_token_analytics`，参数：
- query_type: `holders`
- token_address: `{地址}`
- chain: `{chain}`

调用 `ant_token_analytics`，参数：
- query_type: `dex_trades`
- token_address: `{地址}`
- chain: `{chain}`

分析逻辑：
1. 获取代币详情：市值、创建时间、持仓者数量
2. 检查 Top Holders 集中度：前 10 持仓者占比 > 80% 标注 `high_risk`，否则 `normal`
3. 检查近期 DEX 交易：买卖比、交易频率、大额交易数量
4. 代币年龄评估：创建 < 1h 为 `极早期`，< 24h 为 `早期`，> 7d 为 `成熟`

记录：`holder_concentration`、`trade_activity`（high/medium/low）、`token_age_stage`

### Step 4: Smart Money 信号交叉验证

调用 `ant_smart_money`，参数：
- query_type: `dex_trades`
- chains: `{chain}`

调用 `ant_token_analytics`，参数：
- query_type: `who_bought_sold`
- token_address: `{地址}`
- chain: `{chain}`
- buy_or_sell: `buy`

分析逻辑：
1. 获取近期 Smart Money DEX 交易，筛选是否包含候选代币
2. 如有 Smart Money 买入记录，标注 `entered`，记录买入时间和金额
3. 如 Smart Money 正在卖出，标注 `exiting`
4. 无记录则标注 `not_entered`
5. Smart Money 买入 + 社交热度上升 = 高信心信号

记录：`smart_money_status`（entered/not_entered/exiting）

### Step 5: 叙事生命周期阶段判断

综合 Step 1 的社交热度趋势 + Step 2/3 的代币数据 + 交易量变化，判断叙事所处生命周期阶段：

- **萌芽期（emerging）**：社交热度刚起、代币刚创建 < 1h、交易量低。高风险高回报窗口。
- **爆发期（exploding）**：社交热度加速上升、价格快速上涨、交易量放大。最佳发现窗口（原推文中 @Clukz 的目标阶段）。
- **高潮期（peaking）**：社交热度见顶、价格创新高但涨速放缓、开始出现获利了结。谨慎进场，适合分批出场。
- **衰退期（fading）**：社交热度下降、价格回落、交易量缩减。不建议进场。

记录：`narrative_lifecycle`、`lifecycle_confidence`（0-100）

### Step 6: 综合评估与信号输出

汇总所有维度，为每个候选代币计算综合评分（composite_score, 0-100）：

**评分计算：**
- 叙事热度得分权重：25%（基于 narrative_heat_score）
- 流动性评分权重：20%（按 min_liquidity_usd 线性映射）
- 持仓健康度权重：20%（concentration = normal 得满分，high_risk 得 0 分）
- Smart Money 信号权重：20%（entered = 满分，not_entered = 50%，exiting = 0 分）
- 交易活跃度权重：15%（high = 满分，medium = 60%，low = 20%）

**信号强度判定：**
- **强信号（strong）**：composite_score >= 70 且叙事处于萌芽/爆发期 且 holder_concentration = normal
- **中等信号（moderate）**：composite_score 40-69，或叙事处于爆发期但 Smart Money 未进场
- **弱信号（weak）**：composite_score < 40，或叙事处于衰退期，或 holder_concentration = high_risk

**建议操作：**
- strong -> `enter`（关注进场机会）
- moderate -> `watch`（观察等待）
- weak -> `avoid`（回避）

## 输出约束

- 总文字输出不超过 300 字
- 优先用表格、数字、百分比替代文字描述
- 结论先行：第一行给出叙事生命周期阶段和最优候选代币信号，细节按需展开

## 报告结构

始终使用此模板：

```
=== 叙事驱动代币发现报告 ===
叙事关键词: {narrative_keyword}
叙事热度: {narrative_heat_score}/100 ({narrative_trend})
生命周期阶段: {narrative_lifecycle}

| 代币 | 链 | 价格 | 流动性 | 年龄 | SM状态 | 综合评分 | 信号 |
|------|------|------|--------|------|--------|----------|------|
| {symbol} | {chain} | {price} | {liquidity} | {age} | {sm_status} | {score} | {signal} |

{对每个 strong/moderate 信号的代币给出 1-2 行解读}

免责声明：本分析基于链上数据和社交信号自动生成，
不构成投资建议。MEME 代币风险极高，可能归零。
方法论归属 @thecryptoskanda / @Clukz。
```

## Risk Parameters

### 信号局限性

- 代币搜索基于名称/符号文本匹配，可能遗漏名称不直接包含关键词但叙事相关的代币（如搜索"Aliens"可能遗漏叫"ET"的代币）
- `ant_market_sentiment` 的话题数据覆盖度取决于 LunarCrush 数据源，对非英语/非主流叙事可能覆盖不足
- Smart Money 标签依赖数据提供商的分类标准，可能存在误判
- 极早期代币（创建 < 5 分钟）可能尚未被 MCP 数据源索引
- 本 Skill 是主动查询模式，无法做到原推文中 @Clukz 的"秒级"响应速度

### 该 Skill 不做的事

- 不替代实时新闻推送流（如 Uxento）——用户需自行判断热点并输入关键词
- 不执行交易（不包含买入/卖出功能）
- 不做代币图片/Logo 的视觉匹配
- 不预测价格走势，仅评估叙事阶段和链上信号
- 不提供止盈/止损具体价位建议

### 需要人工判断的环节

- 叙事关键词的选择：用户需自行判断当前热点叙事并提供准确关键词
- 代币与叙事的"真实关联性"：文本匹配可能产生误匹配，需人工确认
- 最终进场决策：Skill 提供信号和评分，但进场时机、仓位大小、止损策略需交易员自行决定
- 叙事可持续性判断：数据可以显示当前热度，但叙事是否会持续需要结合对事件本身的理解

## 首次安装提示

```
目标用户：MEME/山寨币交易员、链上叙事追踪者、投研人员
使用场景：社交媒体出现突发热点话题时，快速扫描链上是否有匹配叙事的代币并评估交易机会
如何使用：/narrative-driven-token-discovery Aliens
生成时间：2026-04-09 05:43:47
```
