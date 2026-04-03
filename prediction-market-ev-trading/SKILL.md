---
name: "prediction-market-ev-trading"
description: "预测市场正期望值(+EV)量化交易分析工具。当用户提到 Polymarket、预测市场、+EV 交易、Kelly 公式仓位管理、预测市场套利、prediction market arbitrage、多数据源交叉验证策略、赔率定价效率分析、Brier Score 校准时使用。也适用于用户想评估任何预测市场（天气、体育、政治、经济、crypto）的交易机会，或需要构建概率模型与市场定价对比的量化框架时。"
---

# 预测市场 +EV 量化交易分析

## Overview

通过多数据源交叉验证构建独立概率模型，与预测市场（Polymarket 等）定价对比发现正期望值(+EV)交易机会，并用 Kelly 公式进行科学仓位管理，配合自校准机制持续优化策略参数。

## Demand Context

方法论来源: @NFTCPS 的 Polymarket 天气预测市场量化交易策略。核心思路是同时接入多个独立数据源（如 ECMWF、HRRR、METAR），通过交叉比对降低单一数据源偏差，基于预测概率与市场定价的差异计算 +EV，用 Kelly 公式自动计算最优仓位。策略包含自校准闭环：每积累一定预测样本后自动回测准确率，动态调整模型参数。

这套方法论本质上是通用的预测市场套利框架，可推广到天气、体育、政治、经济、crypto 等各品类。

## Features (Data Inputs)

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| market_category | string | 是 | 预测市场品类: weather / sports / politics / economics / crypto | - |
| market_id | string | 否 | 具体市场 ID 或 Polymarket 市场链接 | 全部活跃市场 |
| data_sources | list[string] | 是 | 外部数据源列表（至少 2 个独立源） | - |
| target_cities | list[string] | 否 | 目标城市/事件列表 | 全部可用市场 |
| kelly_fraction | float | 否 | Kelly 公式缩放系数（0-1） | 0.5 |
| ev_threshold | float | 否 | 最低 +EV 阈值，低于此值不交易 | 0.05 |
| calibration_window | int | 否 | 自校准触发的最小预测次数 | 30 |
| max_position_size | float | 否 | 单笔最大下注比例（占总资金） | 0.1 |
| backtest_mode | bool | 否 | 是否启用回测模式（模拟资金） | true |
| time_range | string | 否 | 分析时间范围 | 7d |

### MCP 数据源映射

本 Skill 核心数据需求（预测市场赔率、天气数据、结算结果）无法通过现有 MCP 覆盖，需外部 API。当分析 crypto 品类预测市场时，可借助以下 MCP 工具提供辅助数据:

| 数据需求 | MCP 工具 | query_type | 覆盖度 |
|----------|----------|------------|--------|
| Crypto 代币价格 | ant_spot_market_structure | simple_price | 部分 |
| Crypto 价格历史 | ant_futures_market_structure | futures_price_history | 部分 |
| 技术指标 (RSI/MACD) | ant_market_indicators | rsi / macd | 部分 |
| 市场情绪 | ant_market_sentiment | coin_detail | 部分 |
| 宏观经济数据 | ant_macro_economics | cpi / federal_funds_rate | 部分 |

未覆盖的关键数据源需用户自行提供或通过外部 API 获取:
- 预测市场合约列表/赔率: Polymarket CLOB API (`https://clob.polymarket.com`)
- 天气预测数据: ECMWF API、NOAA HRRR、METAR (aviationweather.gov)
- 预测市场结算结果: Polymarket API 或链上合约事件 (UMA Oracle)

## Entry Conditions

满足以下任一条件时触发本 Skill:

1. 用户明确提到预测市场分析、Polymarket、+EV 交易、预测市场套利
2. 用户想评估某个事件的概率与市场定价是否存在偏差
3. 用户需要构建多数据源交叉验证的概率模型
4. 用户提到 Kelly 公式仓位管理或 Brier Score 校准
5. 用户想扫描预测市场上的正期望值交易机会

## Exit Conditions

满足以下任一条件时完成分析并输出报告:

1. 已完成全部 7 个分析步骤并生成综合策略报告
2. 在 Step 1 市场扫描阶段未发现符合条件的活跃市场（输出空结果说明）
3. 在 Step 3 EV 计算阶段未发现任何正 EV 机会（输出当前市场定价效率评估）
4. 用户明确要求终止分析

## Action Specification

按以下 7 个步骤顺序执行分析。每步产出作为下一步输入。

### Step 1: 市场扫描与筛选

扫描目标预测市场平台上的活跃市场，筛选流动性和交易量达标的候选市场。

1. 获取用户指定的 `market_category` 对应的活跃合约列表
2. 对每个合约提取: 市场 ID、当前赔率（隐含概率）、交易量、流动性深度、结算时间
3. 按以下条件过滤:
   - 交易量 > 品类平均值的 50%
   - 流动性足够支撑目标仓位规模
   - 结算时间在合理范围内（不过近也不过远）
4. 排除已接近结算（< 2小时）或流动性极低的长尾市场
5. 输出候选市场列表

如果用户未提供实际市场数据，使用模拟数据演示分析框架，并明确标注为模拟。

### Step 2: 多源数据采集与交叉验证

对每个候选市场的标的事件，从至少 2 个独立数据源获取预测数据并交叉比对。

1. 根据 `market_category` 确定适用的数据源:
   - 天气市场: ECMWF、HRRR、METAR
   - Crypto 市场: 使用 `ant_spot_market_structure`（simple_price）、`ant_market_indicators`（rsi/macd）、`ant_market_sentiment`（coin_detail）
   - 经济事件: 使用 `ant_macro_economics`（cpi/federal_funds_rate）+ 外部宏观数据
   - 体育/政治: 需用户提供数据源或使用公开赔率数据
2. 获取各数据源的预测值或概率分布
3. 计算加权平均概率，初始权重等权分配（后续由自校准调整）
4. 计算数据源间的标准差作为一致性评分:
   - 标准差 < 0.1: 高一致性，置信度 High
   - 标准差 0.1-0.2: 中等一致性，置信度 Medium
   - 标准差 > 0.2: 低一致性，置信度 Low，降低仓位或跳过
5. 输出每个市场的模型预测概率及置信区间

### Step 3: 正期望值 (+EV) 计算

将模型预测概率与市场当前赔率对比，计算每笔交易的期望值。

1. 对每个候选市场，用以下公式计算 EV:
   ```
   EV = (模型预测概率 x 赔率) - 1
   ```
   其中赔率 = 1 / 市场隐含概率
2. 筛选 EV > `ev_threshold`（默认 0.05 即 5%）的交易机会
3. 按 EV 大小降序排列
4. 为每笔机会标注置信度等级（基于 Step 2 的数据源一致性）
5. 输出正 EV 交易机会列表: 市场名称、方向（买 YES/NO）、EV 值、置信度

如果没有发现正 EV 机会，输出当前市场定价效率评估（说明市场定价与模型预测的偏差分布）。

### Step 4: Kelly 公式仓位计算

对每笔正 EV 交易，用 Kelly 公式计算最优仓位大小。

1. 对每笔交易应用 Kelly 公式:
   ```
   f = (b x p - q) / b
   ```
   其中 b = 赔率（净赔率）, p = 模型预测概率, q = 1 - p
2. 乘以 `kelly_fraction`（默认 0.5，即半 Kelly）降低波动性
3. 限制单笔仓位不超过 `max_position_size`（默认总资金的 10%）
4. 检查总持仓比例，确保不超过总资金的 50%
5. 如果是回测模式（`backtest_mode=true`），以 $1000 模拟资金计算具体金额
6. 输出每笔交易的建议仓位: 占比和金额

### Step 5: 执行记录与结果追踪

记录每笔交易的完整数据链，形成数据闭环。

1. 为每笔建议交易生成记录条目，包含:
   - 数据源预测值（各源独立值）
   - 模型综合概率
   - 市场赔率（交易时刻）
   - EV 值
   - Kelly 计算的仓位
   - 实际建议金额
2. 按品类/城市/时间段聚合统计
3. 如有历史交易记录，计算累计 PnL（盈亏）
4. 输出结构化交易日志

因为本 Skill 不执行实际交易，此步骤记录的是建议交易的追踪框架。用户需自行记录实际执行情况和结算结果。

### Step 6: 自校准与参数优化

当积累足够预测样本后，回测模型准确率并调整参数。

1. 检查是否有历史交易日志（需用户提供或从之前的分析中累积）
2. 当某品类/城市的预测次数达到 `calibration_window`（默认 30）时触发校准:
   - 计算各数据源的历史准确率
   - 重新分配数据源权重（准确率高的数据源获得更高权重）
   - 计算 Brier Score 评估概率校准度:
     ```
     Brier Score = (1/N) x SUM(预测概率 - 实际结果)^2
     ```
   - Brier Score < 0.2: 校准良好
   - Brier Score 0.2-0.25: 可接受但需关注
   - Brier Score > 0.25: 模型预测能力不足，建议更换或增加数据源
3. 根据校准结果动态调整:
   - 数据源权重
   - EV 阈值（准确率低时提高阈值以减少交易频率）
   - Kelly 缩放系数（波动大时降低系数）
4. 对持续亏损的市场/品类，建议降低仓位或暂停

如果是首次运行无历史数据，跳过校准，使用默认参数并明确说明。

### Step 7: 综合评估与策略报告

汇总全部分析结果，输出综合策略评估报告。

1. 汇总各步骤产出，生成报告包含:
   - 策略概况: 覆盖市场数、数据源、扫描时间
   - 当日最佳交易机会表格（按 EV 排序）
   - 校准统计（各品类/城市的准确率和 Brier Score）
   - 数据源权重分布
2. 根据以下标准判断策略健康度:
   - 整体 ROI > 0 且 Brier Score < 0.25: 策略有效，继续运行
   - ROI < 0 但 Brier Score < 0.25: 概率校准良好但仓位管理需优化
   - Brier Score > 0.25: 模型预测能力不足，需更换/增加数据源
3. 输出策略建议（继续/调整/暂停）

### 报告结构

始终使用此模板输出最终报告:

```
=== 预测市场 +EV 交易机会扫描报告 ===
品类: {market_category} | 平台: {platform} | 扫描时间: {timestamp}

策略概况:
- 覆盖市场: {market_count} 个
- 数据源: {data_sources}（{source_count}源交叉验证）
- 校准状态: {calibrated_count}/{total_count} 已完成校准

当日最佳交易机会:
| 市场 | 市场价格 | 模型概率 | EV | 置信度 | Kelly 仓位 | 建议金额 |
|------|----------|----------|------|--------|------------|----------|
| ... | ... | ... | ... | ... | ... | ... |

校准统计（最近 {calibration_window} 次预测）:
- {market}: 准确率 {accuracy}%, Brier Score {brier}

数据源权重（经校准调整）:
- {source}: {weight}%

策略健康度: {health_status}
建议: {recommendation}
```

## Risk Parameters

| 参数 | 约束 | 说明 |
|------|------|------|
| 单笔最大仓位 | max_position_size (默认 10%) | 防止单笔过度集中 |
| 总持仓上限 | 50% | 保持充足现金缓冲 |
| Kelly 缩放 | kelly_fraction (默认 0.5) | 半 Kelly 降低破产概率 |
| EV 下限 | ev_threshold (默认 5%) | 过滤低质量机会 |
| 数据源最低数量 | 2 个独立源 | 交叉验证的最低要求 |
| 流动性门槛 | 品类动态调整 | 排除无法实际执行的市场 |
| 高分歧处理 | 数据源标准差 > 0.2 时降仓或跳过 | 避免在不确定性过高时下注 |
| 亏损熔断 | 连续亏损达阈值暂停该品类 | 自校准未完成前的安全网 |

重要边界:
- 本 Skill 仅输出交易建议，不执行实际交易
- 正 EV 策略在短期内仍可能亏损，需足够样本量才能体现统计优势
- 模型质量完全依赖外部数据源的准确性
- Polymarket 在部分司法管辖区可能存在合规限制

## 首次安装提示

```
目标用户：量化交易员 / 预测市场参与者 / DeFi 研究员 / 数据驱动型投资者
使用场景：在 Polymarket 等预测市场上寻找正期望值交易机会，评估市场定价效率，构建多数据源交叉验证的量化策略
如何使用：/prediction-market-ev-trading weather --data_sources=ECMWF,HRRR,METAR
```

## 示例

**示例 1: 天气市场分析**
输入: `/prediction-market-ev-trading weather --data_sources=ECMWF,HRRR,METAR --target_cities=NYC,London,Tokyo`
输出: 三个城市的天气预测市场 +EV 机会列表，含 Kelly 仓位建议

**示例 2: Crypto 预测市场分析**
输入: `/prediction-market-ev-trading crypto --data_sources=spot_price,technical_indicators,sentiment --market_id=BTC_100k_March`
输出: BTC 价格预测市场的 EV 计算，结合链上数据和市场情绪的交叉验证

**示例 3: 纯回测模式**
输入: `/prediction-market-ev-trading weather --backtest_mode=true --time_range=30d`
输出: 过去 30 天模拟交易的 PnL 统计和 Brier Score 校准报告
