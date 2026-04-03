---
name: "oi-divergence-monitor"
description: "检测加密货币永续合约价格与未平仓量(OI)的背离信号。当用户提到 OI 背离、价格与持仓量矛盾、合约市场微观结构分析、多头离场信号、OI divergence、永续合约健康度检查，或者想判断价格上涨是否有杠杆资金支撑时，使用此 Skill。也适用于定期巡检(每4-8小时)或价格快速拉升后的风险评估场景。"
---

## Overview

检测指定加密货币的现货价格与永续合约未平仓量(OI)之间的背离关系，并通过资金费率、爆仓数据、多空比三个维度交叉验证信号可靠性，输出量化的背离强度评分和结构化分析报告。

## Demand Context

源自 @EmberCN 的衍生品市场分析方法论：当现货价格上涨创新高但永续合约 OI 反而下降时，说明多头在高位主动平仓离场，市场上涨缺乏杠杆资金支撑，这是一个经典的衍生品市场微观结构看空信号。该方法论通过"信号检测 + 多维验证 + 历史参照"的框架提升信号置信度。

方法论归属：@EmberCN，本 Skill 基于其公开分析框架构建。

## Features (Data Inputs)

### 必填参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| symbol | string | 目标代币符号 | BTC |

### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| time_range | string | 24h | 观察时间窗口 |
| oi_change_threshold | float | -3.0 | OI 下降幅度阈值(%)，低于此值视为显著下降 |
| funding_rate_threshold | float | 0.02 | 资金费率偏低阈值(%)，低于此值视为做多意愿弱 |
| liquidation_window | string | 4h | 爆仓数据观察窗口 |
| price_change_threshold | float | 1.0 | 价格上涨幅度阈值(%)，高于此值视为显著上涨 |

## Entry Conditions

满足以下任一条件时触发本 Skill：

1. 用户主动请求 OI 背离检测（如 `/oi-divergence-monitor BTC`）
2. 定期巡检周期到达（建议每 4-8 小时执行一次）
3. 价格在短时间内快速拉升，需评估上涨可持续性

## Exit Conditions

满足以下条件时 Skill 执行完成：

1. 已完成全部 7 个分析步骤
2. 已输出信号等级判定（strong / moderate / weak / none）
3. 已输出结构化报告（含各维度数据和建议操作）

## Action Specification

### Step 1: 获取现货价格变动

调用 `ant_spot_market_structure`，参数：
- query_type: `simple_price`
- ids: `{symbol}`（如 `bitcoin` 对应 BTC）

提取当前价格和 24h 价格变化百分比。判断价格涨幅是否超过 `price_change_threshold`。

记录：`price_current`、`price_change_pct`、`price_rising = true/false`

### Step 2: 获取永续合约 OI 数据

调用 `ant_futures_market_structure`，参数：
- query_type: `futures_oi_aggregated`
- symbol: `{symbol}`

提取聚合 OI 数据和 OI 变化百分比。判断 OI 变化是否低于 `oi_change_threshold`（即 OI 显著下降）。

记录：`oi_current`、`oi_change_pct`、`oi_declining = true/false`

### Step 3: 检测价格-OI 背离

将 Step 1 和 Step 2 结果交叉比对：
- 如果 `price_rising == true` 且 `oi_declining == true`，标记 `divergence_detected = true`
- 计算背离强度：`divergence_intensity = abs(price_change_pct) + abs(oi_change_pct)`

如果 `divergence_detected == false`，直接输出 `signal_level: none`，跳到 Step 7 生成报告。因为核心背离不成立时，后续验证步骤没有意义。

### Step 4: 资金费率验证

调用 `ant_futures_market_structure`，参数：
- query_type: `futures_funding_rate_latest`（优先）或 `futures_funding_rate_history`
- symbol: `{symbol}`

提取当前资金费率。判断是否低于 `funding_rate_threshold`：
- 低于阈值：标记 `funding_weak = true`，说明做多意愿不强，增强背离信号可信度
- 高于阈值：标记 `funding_weak = false`

记录：`funding_rate`、`funding_weak`

### Step 5: 爆仓数据验证

调用 `ant_futures_liquidation`，参数：
- query_type: `futures_liquidation_aggregated`（优先）或 `futures_liquidation_history`
- symbol: `{symbol}`

提取多单爆仓金额和空单爆仓金额。计算多空爆仓比：
- 多单爆仓 > 空单爆仓 * 1.5：标记 `long_squeezed = true`，说明多头正在被清洗
- 否则：标记 `long_squeezed = false`

记录：`long_liquidation`、`short_liquidation`、`liq_ratio`、`long_squeezed`

### Step 6: 多空比辅助验证

调用 `ant_futures_market_structure`，参数：
- query_type: `futures_long_short_ratio`（优先）或 `futures_long_short_history`
- symbol: `{symbol}`

提取当前多空比和变化趋势。此步骤为辅助信号，不参与核心评级计算，但在报告中展示供参考。

记录：`long_short_ratio`、`ls_trend`

### Step 7: 综合评估与报告输出

根据三个验证维度（资金费率、爆仓数据、多空比下降趋势）的通过情况评定信号等级：

**信号评级标准：**
- **strong（强背离）**：核心背离成立 + 至少 2 个验证维度通过（如资金费率偏低 + 多单爆仓高）。短期回调概率较高。
- **moderate（中等背离）**：核心背离成立 + 1 个验证维度通过。需关注但不构成强信号。
- **weak（弱背离）**：核心背离成立但无验证维度通过。信号可靠性不足，仅供参考。
- **none（无背离）**：核心背离不成立。

**背离评分计算（divergence_score, 0-100）：**
- 基础分 = `min(divergence_intensity * 5, 40)`
- 资金费率验证通过 +20 分
- 爆仓数据验证通过 +20 分
- 多空比下降趋势 +10 分
- 背离强度加权 +10 分（按 `divergence_intensity` 线性映射）

**输出结构化报告，使用以下模板：**

```
# {symbol} OI 背离信号监测报告

## 信号概要
- 信号等级：{signal_level}
- 背离评分：{divergence_score}/100
- 分析时间：{timestamp}

## 价格与 OI 数据
| 指标 | 数值 | 判定 |
|------|------|------|
| 当前价格 | ${price_current} | — |
| 价格涨幅 | {price_change_pct}% | {price_rising ? "上涨" : "未上涨"} |
| 当前 OI | ${oi_current} | — |
| OI 变化 | {oi_change_pct}% | {oi_declining ? "下降" : "未下降"} |

## 验证维度
| 维度 | 数据 | 判定 |
|------|------|------|
| 资金费率 | {funding_rate}% | {funding_weak ? "偏低(看空增强)" : "正常"} |
| 多单爆仓 | ${long_liquidation} | {long_squeezed ? "多头被清洗(看空增强)" : "正常"} |
| 空单爆仓 | ${short_liquidation} | — |
| 多空比 | {long_short_ratio} | {ls_trend} |

## 建议
{recommendation}

## 免责声明
本分析基于 @EmberCN 的衍生品市场微观结构方法论，不构成投资建议。
信号基于历史统计规律，不能保证未来表现。具体操作决策需结合基本面和个人风险偏好。
```

## Risk Parameters

### 信号局限性

- OI 数据为全市场聚合数据，无法区分套保仓位和投机仓位，可能高估或低估真实的投机杠杆变化
- 资金费率反映结算时点状态，盘中可能剧烈波动，单一时点读数可能不够准确
- 爆仓数据可能存在交易所上报延迟，尤其在极端行情时延迟更明显
- 不同交易所的 OI 统计口径存在差异，聚合数据会平滑这些差异

### 该 Skill 不做的事

- 不预测具体回撤幅度和目标价位
- 不提供自动交易执行能力
- 不做历史信号回测统计
- 不分析背离产生的根本原因（如宏观事件、监管消息）

### 需要人工判断的环节

- 信号触发后的具体操作决策（减仓比例、对冲方式、止损设置）
- 是否存在重大基本面事件可能导致信号失效（如 ETF 审批、监管政策）
- 背离持续时间和强度的综合判断

## 首次安装提示

```
目标用户：合约交易员、投研人员、量化策略开发者
使用场景：定期巡检（每4-8小时）或价格快速拉升时触发，检测价格-OI背离信号
如何使用：/oi-divergence-monitor BTC
```
