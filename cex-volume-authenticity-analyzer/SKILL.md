---
name: "cex-volume-authenticity-analyzer"
description: "评估 CEX 交易量真实性，识别刷量水分。当用户提到交易所刷量、CEX 交易量真实性、fake volume、volume authenticity、交易所水分分析、CEX 哪家数据最真实、选所上币参考、月度巡检交易量、资金效率比率，或者想对比不同交易所交易量可信度时，触发本 Skill。使用 Hyperliquid 链上基准建立诚实交易阈值，量化识别 Binance、OKX、Bybit 等主流 CEX 的可疑交易量，并重算调整后市场份额。"
metadata:
  generated_at: "2026-04-04 03:18:18"
---

## Overview

以 Hyperliquid 链上 DEX 的资金效率比率（日均交易量/核心储备）为基准，对 Binance、OKX、Bybit 等主流 CEX 计算相同比率，超过阈值的部分定义为可疑交易量，剔除后重新计算调整市场份额，揭示真实市场集中度。

## Demand Context

本 Skill 源自 @agintender（2026-03-30）提出的方法论：CEX 刷量成本极低（做市商免手续费、VIP 返佣机制），直接比较各 CEX 公布的交易量毫无意义。作者引入 Hyperliquid 作为"链上可审计的诚实基准"——Hyperliquid 每笔交易需真实 USDC 保证金和 gas 费，是当前市场中伪造成本最高的交易量来源。

核心指标：**日均交易量 / 核心储备（BTC+ETH+USDT+USDC）**，称为资金效率比率。Hyperliquid 基准值约 1.44x（$2,068亿30天总量 ÷ 30 ÷ $48.8亿 TVL）。考虑 CEX 资金用途更多元，附加 15% 宽容系数，可信阈值为 **1.66x**。超出阈值的比率对应的交易量即为可疑水分。

方法论归属：@agintender。来源推文：https://x.com/agintender/status/2038490939082346930

## Features (Data Inputs)

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| exchanges | list[str] | 是 | — | 需分析的 CEX 列表，如 ["Binance","OKX","Bybit","Bitget","Gate.io","MEXC","KuCoin","HTX"] |
| benchmark_dex | str | 否 | "Hyperliquid" | 链上基准 DEX 名称 |
| time_range_days | int | 否 | 30 | 分析时间窗口（天） |
| tolerance_pct | float | 否 | 15 | CEX 宽容系数（%），用于放宽阈值 |
| reserve_assets | list[str] | 否 | ["BTC","ETH","USDT","USDC"] | 计算储备分母的核心资产列表 |

**MCP 工具覆盖度**：

| 数据需求 | MCP 工具 | 覆盖状态 |
|----------|----------|----------|
| Hyperliquid TVL | ant_protocol_tvl_yields_revenue (protocol_tvl) | 完整 |
| Hyperliquid 30天交易量 | ant_protocol_tvl_yields_revenue (dex_overview) | 部分（需验证历史累计支持） |
| CEX 核心资产储备 | ant_fund_flow (exchange_reserve) | 完整 |
| CEX 链上净流量（辅助验证）| ant_fund_flow (exchange_netflow) | 完整 |
| 实时价格折算储备 | ant_spot_market_structure (simple_price) | 完整 |
| 各 CEX 30天现货交易量 | — | 不覆盖（需 Newhedge API 或人工录入）|
| 各 CEX 30天衍生品交易量 | ant_futures_market_structure (futures_oi_aggregated) | 部分（OI 非累计量）|

## Entry Conditions

当以下任意条件满足时触发本 Skill：

- 用户询问"哪家交易所的交易量最真实"、"CEX 刷量怎么检测"、"volume authenticity"
- 用户想做选所参考或上币尽调，需要量化交易量可信度
- 用户想定期（月度）巡检主流 CEX 水分并追踪时序变化
- 用户提到 Hyperliquid 基准法、资金效率比率、fake volume 检测方法
- 用户想了解剔除刷量后的真实市场份额分布

## Exit Conditions

本 Skill 完成当：

- Step 1-7 全部执行完毕，生成包含所有交易所的评估表格
- 每家 CEX 的资金效率比率、可疑交易量估算和真实市场份额已计算
- 报告包含基准参数、评级说明和局限性声明

遇到以下情况提前退出并说明原因：

- 无法获取任何 CEX 储备数据（MCP 工具全部失败）
- 用户未提供 exchanges 列表且无法从上下文推断

## Action Specification

按以下 7 个步骤顺序执行。若某 MCP 调用失败，记录失败原因并继续——部分结果优于无结果。

### Step 1: 获取基准 DEX 数据（Hyperliquid）

调用 `ant_protocol_tvl_yields_revenue`，参数 query_type 设为 `protocol_tvl`，protocol 设为 `"hyperliquid"`，获取当前 TVL 作为储备基准。

同时调用 `ant_protocol_tvl_yields_revenue`，参数 query_type 设为 `dex_overview`，chain 设为 `"hyperliquid"`，尝试获取近期 DEX 交易量概览。

若 dex_overview 无法返回精确的 30 天累计历史数据，降级方案：使用 DefiLlama 公开 API `https://api.llama.fi/overview/derivatives?excludeTotalDataChart=false&dataType=dailyVolume` 补充，或使用推文案例中的参考值（$2,068亿/30天，TVL $48.8亿）并明确标注数据来源为历史参考值。

计算基准比率：

```
benchmark_ratio = (total_volume_30d / time_range_days) / tvl
threshold = benchmark_ratio * (1 + tolerance_pct / 100)
```

记录：`benchmark_ratio`（如 1.44）、`threshold`（如 1.66）、数据来源标注。

### Step 2: 获取各 CEX 核心资产储备

对每家 CEX，分别调用 `ant_fund_flow`，参数 query_type 设为 `exchange_reserve`，asset 依次设为 `"BTC"`、`"ETH"`、`"USDT"`、`"USDC"`，exchange 设为当前交易所名称。

同时调用 `ant_spot_market_structure`，参数 query_type 设为 `simple_price`，ids 设为 `"bitcoin,ethereum,tether,usd-coin"`，获取实时价格用于储备折算。

将四种资产的储备量按实时价格折算为 USD，汇总得到 `total_reserve_usd`。同时记录 BTC 储备率（储备量/用户存款量）用于后续超额储备修正判断。

若某资产储备数据获取失败，使用可用资产估算并在报告中注明缺失项。

记录：各交易所 `total_reserve_usd`、`btc_reserve_ratio`。

### Step 3: 获取各 CEX 30 天交易量数据

**衍生品交易量**：调用 `ant_futures_market_structure`，参数 query_type 设为 `futures_oi_aggregated`，symbol 设为 `"BTC"`，获取各交易所 OI 数据作为规模参考。

注意：`futures_oi_aggregated` 返回实时持仓量（OI），非30天累计交易量。若用户未提供历史交易量数据，在报告中明确标注此局限性，并建议用户从 CoinGlass 获取各交易所的月度衍生品交易量快照后手动提供。

**现货交易量**：当前 MCP 无覆盖。优先使用用户提供的数据；若无，向用户说明需从 Newhedge 或 CoinGecko Exchanges API 获取，并给出接口参考。v1 版本支持用户以 CSV 格式粘贴数据（格式：exchange,spot_30d,deriv_30d）。

汇总：

```
total_volume_30d[exchange] = spot_volume_30d + deriv_volume_30d
```

记录：各交易所 `spot_volume_30d`、`deriv_volume_30d`、`total_volume_30d`，以及数据来源和可信度备注。

### Step 4: 计算资金效率比率

此步骤为纯计算，不调用 MCP 工具。

对每家 CEX 计算：

```
daily_avg_volume = total_volume_30d / time_range_days
daily_avg_spot   = spot_volume_30d  / time_range_days
daily_avg_deriv  = deriv_volume_30d / time_range_days

total_ratio = daily_avg_volume / total_reserve_usd
spot_ratio  = daily_avg_spot   / total_reserve_usd
deriv_ratio = daily_avg_deriv  / total_reserve_usd
```

记录：各交易所三个比率值。

### Step 5: 可疑交易量识别与量化

此步骤为纯计算。

```python
if total_ratio > threshold:
    suspicious_ratio      = total_ratio - threshold
    suspicious_volume_30d = suspicious_ratio * total_reserve_usd * time_range_days
    authenticity_pct      = (total_volume_30d - suspicious_volume_30d) / total_volume_30d
else:
    suspicious_volume_30d = 0
    authenticity_pct      = 1.0
```

根据 `total_ratio` 与阈值的关系，赋予 `authenticity_label`：

| total_ratio 范围 | 评级 |
|-----------------|------|
| ≤ benchmark_ratio | 高度可信 |
| benchmark_ratio ~ threshold | 正常范围 |
| threshold ~ threshold×1.5 | 灰色地带 |
| > threshold×1.5 | 高度可疑 |

**超额储备修正**（定性步骤）：若某交易所 `btc_reserve_ratio > 150%`，在 note 字段中注明"BTC 储备明显超额，部分储备可能来自自营资金，可疑水分判定偏保守"，不自动调整数值，由用户结合背景信息判断。

记录：各交易所 `suspicious_volume_30d`、`authenticity_pct`、`authenticity_label`、`note`。

### Step 6: 市场份额重新计算

此步骤为纯计算。

```
adjusted_volume[exchange] = total_volume_30d - suspicious_volume_30d
adjusted_total            = sum(adjusted_volume.values())

reported_share[exchange]  = total_volume_30d[exchange] / sum(total_volume_30d.values())
adjusted_share[exchange]  = adjusted_volume[exchange]  / adjusted_total
share_delta[exchange]     = adjusted_share[exchange]   - reported_share[exchange]
```

记录：各交易所 `reported_share`、`adjusted_share`、`share_delta`。

### Step 7: 综合评估与报告生成

汇总 Step 1-6 的所有中间结果，调用 `ant_fund_flow`，参数 query_type 设为 `exchange_netflow`，对高度可疑（评级为"灰色地带"或"高度可疑"）的交易所验证链上净流量是否与交易量异常相符。

按「报告结构」章节的模板输出完整报告。

## 报告结构

始终使用此模板输出评估报告：

```
=== CEX 交易量真实性评估报告 ===
分析周期: {start_date} ~ {end_date} ({time_range_days}天)
基准 DEX: {benchmark_dex} | 基准比率: {benchmark_ratio}x | 可信阈值: {threshold}x
数据来源: 储备={数据源}, 现货量={数据源}, 衍生品量={数据源}

| 交易所 | 核心储备 | 报告30天总量 | 总比率 | 评级 | 可疑交易量估算 |
|--------|---------|------------|-------|------|--------------|
| {exchange} | ${reserve} | ${volume} | {ratio}x | {label} | ${suspicious}（约{pct}%）|

=== 市场份额对比（样本内） ===
| 交易所 | 报告份额 | 调整后份额 | 变化 |
|--------|---------|-----------|------|
| {exchange} | {reported_share}% | {adjusted_share}% | {share_delta:+.1f}pp |

=== 关键发现 ===
{2-3 条核心发现，每条不超过 30 字}

=== 局限性说明 ===
{3 条局限性，包含数据来源约束和方法论边界}
```

## 输出约束

- 总文字输出不超过 300 字（不含表格数字）
- 优先用表格、数字、百分比替代文字描述
- 结论先行：第一个表格给出所有交易所的核心结论，细节按需展开
- 关键发现不超过 3 条，每条不超过 30 字
- 默认只输出摘要；若用户要求，可补充各交易所的详细储备和分步计算数据

## Risk Parameters

- **适用交易所范围**：本 Skill 适合有公开 Proof of Reserves 的主流 CEX。无 PoR 披露的交易所无法获取储备数据，自动跳过并说明
- **基准 Hyperliquid 偏高风险**：Hyperliquid 是纯合约平台，资金效率天然高于多业务线的 CEX，使得整体估算偏保守，实际水分可能更多
- **储备数据自我披露风险**：储备数据来自交易所官方 PoR，若储备被低报，比率会被高估（误判更多水分）；若被高报，则比率会被低估（遗漏真实水分）
- **现货量数据依赖外部来源**：Newhedge 为商业数据，CoinGecko 精度较低。v1 支持用户手动录入，但数据质量影响分析结论
- **高比率不等于系统性造假**：0 手续费活动、做市商激励、平台刷量返佣等正常商业行为也会拉高比率，需结合业务背景人工判断
- **月度快照局限性**：单月数据可能受激励活动、上新币种等影响产生噪音，建议结合多月趋势判断
- **不提供单笔刷量证据**：本 Skill 仅为统计学层面的异常信号，不能作为法律层面的欺诈证据
- **样本代表性**：分析结论仅覆盖用户提供的交易所列表，不代表全市场

## 首次安装提示

```
目标用户：投研人员、量化交易员、项目方（选所上币决策）、监管/合规研究者
使用场景：月度巡检主流 CEX 交易量水分，或在选所上币时快速量化评估各交易所可信度
如何使用：/cex-volume-authenticity-analyzer exchanges=["Binance","OKX","Bybit","Bitget","Gate.io","MEXC","KuCoin","HTX"]
生成时间：2026-04-04 03:18:18
```
