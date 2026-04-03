---
name: "defi-exchange-tradfi-valuation"
description: "对 DeFi 衍生品协议做 TradFi 对标估值分析。当用户提到估值分析、对标 CME、P/S 倍数、DeFi 交易所估值、Hyperliquid 估值、defi valuation、tradfi comparison 或 P/S ratio 时触发。自动从链上抓取收入/OI/供应数据，对比 TradFi 交易所 P/S 区间，运行 DCF 三情景模型，输出综合估值报告。"
---

# DeFi 交易所对标 TradFi 估值分析

## Overview

以传统交易所 P/S 倍数框架为锚，从链上实时采集 DeFi 衍生品协议的市值、收入、OI 及供应数据，自动计算当前 P/S 倍数、对比 TradFi 基准区间、运行 DCF 三情景估值，输出可量化的低估/合理/高估结论。

方法论来源：@Ru7Longcrypto（2026-03-14），基于 Hyperliquid vs CME 苹果对苹果比较框架。

---

## Demand Context

- **来源推文**: https://x.com/Ru7Longcrypto/status/2032789064282419448
- **作者**: @Ru7Longcrypto
- **核心论点**: 以 P/S 倍数将 Hyperliquid (HYPE) 对标 CME，CME 市值 $1140 亿 / 年收 $65 亿 = 17.5x P/S；HYPE 市值 $125 亿 / 年收 $9.6 亿 = 13x P/S，不仅更便宜且增速远高于 CME，指向显著估值洼地与重新定价空间。
- **适用场景**: DeFi 衍生品协议出现快速增长信号时（新产品上线、OI 突破历史高位、HIP-3 等机制升级），做定期巡检或事件驱动估值评估。
- **目标用户**: 加密投研人员、宏观量化交易员、机构配置团队。

---

## Features (Data Inputs)

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| `symbol` | string | 是 | 待分析协议代币符号 | — |
| `protocol_id` | string | 是 | DeFi Llama / Antseer 协议 ID | — |
| `benchmark_exchanges` | list[string] | 否 | TradFi 对标交易所列表（人工输入 P/S） | `["CME", "ICE", "CBOE"]` |
| `dcf_discount_rate` | float | 否 | DCF 贴现率 | `0.20` |
| `dcf_terminal_multiple` | float | 否 | DCF 终端收入倍数 | `20.0` |
| `revenue_growth_scenarios` | dict | 否 | 三档增速假设 `{bear, base, bull}` | `{bear:0.30, base:0.80, bull:1.50}` |
| `time_horizon_years` | int | 否 | DCF 预测年限 | `3` |
| `chain` | string | 否 | 链名，用于链上查询 | `arbitrum` |

**MCP 数据源（Antseer）**:

| 数据需求 | MCP 工具 | query_type | 覆盖度 |
|----------|----------|------------|--------|
| 代币价格/市值 | `ant_spot_market_structure` | `coins_markets` | 全覆盖 |
| 协议年化收入 (TTM) | `ant_protocol_tvl_yields_revenue` | `protocol_revenue` | 全覆盖 |
| DEX 交易量 | `ant_protocol_tvl_yields_revenue` | `dex_overview` | 全覆盖 |
| 链上永续 OI | `ant_perp_dex` | `perp_dex_position_by_coin` | 全覆盖 |
| 代币解锁/排放 | `ant_token_analytics` | `emissions` / `emission_detail` | 部分覆盖 |
| TradFi P/S 倍数 | — | — | 需人工输入 |
| TAM 日均量（CME/外汇/0DTE） | — | — | 需人工输入 |

---

## Entry Conditions

以下任一条件满足时触发本 Skill：

- 用户输入包含：估值分析、对标 CME、P/S 倍数、DeFi 交易所估值、defi valuation、tradfi comparison、P/S ratio defi
- 协议 OI 突破历史高位（事件驱动场景）
- 协议发布新产品或机制升级公告（如 HIP-3 类事件）
- 用户明确请求分析某 DeFi 协议相对 TradFi 的估值位置

**必要输入**: `symbol` + `protocol_id`（其余参数有默认值）。

---

## Exit Conditions

以下条件满足时输出报告并退出：

- 完成 Step 1-9 全部分析步骤（或标注数据缺失原因）
- 已输出综合估值报告（含 P/S 对比表、DCF 三情景目标价、综合结论）
- 已列出主要风险因素

若关键数据缺失（如 TTM 收入无法获取），在报告中明确标注并给出替代数据建议，仍输出可用的部分结论。

---

## Action Specification

按以下步骤顺序执行分析：

**Step 1 — 代币市值与价格数据**

调用 `ant_spot_market_structure`，query_type: `coins_markets`，参数 `ids=[symbol], vs_currency=usd`。记录 `price`、`market_cap`、`circulating_supply`、`volume_24h`。市值作为 P/S 的分子。

**Step 2 — 协议 TTM 收入与 P/S 计算**

调用 `ant_protocol_tvl_yields_revenue`，query_type: `protocol_revenue`，参数 `protocol=[protocol_id]`。汇总最近 12 个月收入得到 TTM 收入，计算 `P/S = market_cap / ttm_revenue`。

**Step 3 — 链上 OI 追踪**

调用 `ant_perp_dex`，query_type: `perp_dex_position_by_coin`，参数 `symbol=[symbol]`。记录当前总 OI 及 30/90 天 OI 变化幅度，计算增长率。OI 增长率是业务飞轮最直接的验证指标——增长越快，收入增速越可信。

**Step 4 — DEX 交易量趋势**

调用 `ant_protocol_tvl_yields_revenue`，query_type: `dex_overview`，参数 `chain=[chain]`。计算近 30/90 天日均交易量及增速，与 TTM 收入增速交叉验证。

**Step 5 — 代币供应压力**

调用 `ant_token_analytics`，query_type: `emissions`，参数 `asset=[symbol]`，获取解锁计划与验证者排放。计算：
- 年化净稀释 = 年化总排放 - 年化回购销毁
- 净稀释率 = 净稀释 / 流通供应
注意：回购销毁记录 MCP 覆盖有限，若缺失需标注并建议查询 Dune Analytics 或官方公告补全。

**Step 6 — TradFi 基准 P/S 对标**

若用户提供了 TradFi P/S 数据，直接使用。若未提供，使用默认参考区间：CME ~17.5x、ICE ~22x、CBOE ~25x，中位数 22x。计算目标协议相对 TradFi 中位数的折价幅度。TradFi P/S 数据来源：Yahoo Finance / Macrotrends（公开可查，每季度更新）。

**Step 7 — TAM 测算（可选）**

若用户提供 TradFi 基础资产日均交易量，按渗透率假设（保守 0.1% / 中性 0.5% / 乐观 1%）估算 TAM 贡献收入。若未提供，跳过此步并在报告中标注"TAM 分析需人工输入 TradFi 基础量数据"。

**Step 8 — DCF 三情景估值**

使用 Step 2 的 TTM 收入，对每个情景 s（bear / base / bull）计算：

```
year_n_revenue = ttm_revenue * (1 + growth_rate[s])^n
terminal_value = year3_revenue * terminal_multiple
dcf_value = Σ(yearN_revenue / (1+r)^N) + terminal_value / (1+r)^3
target_price = dcf_value / circulating_supply
upside_pct = (target_price / current_price - 1) * 100
```

将当前价格标注到三情景区间中，若当前价低于熊市目标价，标记"尚未定价"。

**Step 9 — 综合估值评估**

按下表汇总信号：

| 维度 | 信号阈值 | 方向 |
|------|----------|------|
| P/S vs TradFi 中位数 | 当前 P/S < TradFi 中位数 | 估值洼地 |
| OI 90 天增长 | > 100% | 业务飞轮强劲 |
| 净稀释率 | < 2%/年 | 供应压力可控 |
| 当前价 vs 熊市目标价 | 当前价 < 熊市目标价 | 安全边际充足 |

输出综合结论：低估 / 合理 / 高估，并说明量化依据。

---

## Risk Parameters

- **DCF 敏感性**: ±20% 增速假设可能导致目标价差异 50% 以上，务必在报告中提示敏感性。
- **数据口径差异**: 协议"收入"与 TradFi 会计收入口径不同，对比结论需标注差异。
- **链上 OI 边界**: 仅含 DEX 永续仓位，不含 CeFi 同类（如 Binance 的 OI）。
- **TradFi P/S 波动性**: TradFi P/S 受宏观环境影响，非固定基准。
- **不提供投资建议**: 输出为估值判断，不为买卖决策。在报告末尾必须附免责声明。
- **TAM 渗透率属主观判断**: 需结合行业经验，不可直接作为量化依据。

---

## 报告结构

始终使用此模板输出报告：

```
=== DeFi 交易所对标 TradFi 估值分析报告 ===
标的: {SYMBOL} ({协议名})  |  分析日期: {日期}

--- 基础估值指标 ---
当前价格:        ${price}
当前市值:        ${market_cap}
TTM 收入:        ${ttm_revenue}
当前 P/S:        {ps_ratio}x

--- TradFi 对标 ---
{对标交易所列表及其 P/S}
TradFi 中位数:   {tradfi_ps_median}x
P/S 折价幅度:    {discount_pct}% (相对 TradFi 中位数)

--- 链上衍生品数据 ---
当前 OI:         ${current_oi}
OI 90天增长:     +{oi_growth_90d}%
DEX 日均交易量:  ${avg_daily_volume}

--- 供应压力 ---
年化排放:        {annual_emission} {symbol}
年化回购销毁:    {annual_buyback_burn} {symbol} [或 "数据需补全"]
净稀释率:        {net_dilution_rate}%/年

--- DCF 情景分析 (贴现率{discount_rate}%, 终端倍数{terminal_multiple}x, {years}年) ---
熊市目标价 ({bear_growth}%增速):   ${dcf_bear_price}  ({upside_bear}% 上行/下行)
基础目标价 ({base_growth}%增速):   ${dcf_base_price}  ({upside_base}% 上行)
牛市目标价 ({bull_growth}%增速):   ${dcf_bull_price}  ({upside_bull}% 上行)

[结论] {综合评定文字}
综合评定: {低估/合理/高估}

--- 主要风险 ---
{风险因素列表}

[免责声明] 本分析基于历史数据，不能预测未来。方法论归属 @Ru7Longcrypto，不构成任何形式的投资建议。
```

---

## 首次安装提示

```
目标用户：加密投研人员、宏观量化交易员、机构配置团队
使用场景：分析 DeFi 衍生品协议相对 TradFi 交易所的估值位置，判断低估/合理/高估
如何使用：/defi-exchange-tradfi-valuation HYPE hyperliquid
```
