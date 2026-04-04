---
name: "oi-price-divergence-crash-detector"
description: "识别合约市场「价格上涨 + OI 持续下降」的背离信号，检测主力预谋崩盘三阶段（洗盘期、布空期、砸盘期）的早期迹象。当用户提到 OI 背离、崩盘预警、主力平多、价格托盘、合约异动、OI divergence、crash signal、short setup、合约做空信号时触发。适用于合约交易员、量化研究员和风控人员进行定期巡检或手动触发分析。"
metadata:
  generated_at: "2026-04-04 09:05:34"
---

## Overview

检测合约市场中"价格上涨 + OI 连续下降"的背离形态，结合资金费率、多空比、Smart Money 动向和爆仓热力图，输出综合预警等级，识别主力预谋崩盘的早期阶段。

方法论来源：@wuk_Bitcoin（推文 https://x.com/wuk_Bitcoin/status/2018017280685469758）

---

## Demand Context

原始推文描述了主力操控合约市场的**三阶段崩盘预谋模型**：

1. **洗盘期**：主力高位悄悄平多单，同时用挂单托价，制造"行情平稳"假象。OI 开始连续数小时下降，价格横盘或小幅拉升。
2. **布空期**：主力清空多单后继续托价，吸引散户和机构量化策略入场做多（充当对手盘），同时悄悄建立空单。
3. **砸盘期**：撤掉托价挂单，顺势砸盘 + 持续加空，触发连锁爆仓，彻底崩盘。

核心识别信号：**1H 级别价格上涨 + OI 连续下降**（5min 噪声太大，4H 发现信号太晚）。

---

## Features (Data Inputs)

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `symbol` | string | 是 | — | 合约交易对，如 `BTC`、`ETH`、`SOL` |
| `interval` | string | 否 | `1h` | K 线时间粒度，推荐 1H（推文指定） |
| `lookback_hours` | int | 否 | `6` | 回溯分析时间窗口（小时数） |
| `oi_decline_threshold_pct` | float | 否 | `3.0` | 触发单根 K 线背离标记的 OI 下降阈值（%） |
| `exchange` | string | 否 | `aggregated` | 指定交易所或聚合，可选 `binance`、`okx`、`bybit`、`aggregated` |
| `include_funding_rate` | bool | 否 | `true` | 是否分析资金费率辅助确认 |
| `include_liquidation_heatmap` | bool | 否 | `true` | 是否加载爆仓热力图数据 |

**MCP 数据源（ant-on-chain-mcp）**：

| 步骤 | MCP 工具 | query_type |
|------|----------|------------|
| 价格历史 | `ant_futures_market_structure` | `futures_price_history` |
| 聚合 OI | `ant_futures_market_structure` | `futures_oi_aggregated` |
| 资金费率 | `ant_futures_market_structure` | `futures_funding_rate_history` |
| 账户多空比 | `ant_futures_market_structure` | `futures_long_short_account_ratio` |
| Taker 多空比 | `ant_futures_market_structure` | `futures_long_short_taker_size_ratio` |
| 爆仓热力图 | `ant_futures_liquidation` | `futures_liquidation_heatmap` |
| Smart Money | `ant_smart_money` | `perp_trades` |
| 链上鲸鱼预警 | `ant_perp_dex` | `perp_dex_whale_alert` |

---

## Entry Conditions

以下任一条件满足时触发：
- 用户输入包含关键词：OI 背离、崩盘预警、主力平多、价格托盘、合约异动、布空
- 用户输入包含英文关键词：OI divergence、crash signal、short setup、oi price divergence、futures anomaly
- 用户提供 `symbol` 参数并请求合约信号分析
- 定期巡检任务（每 1-4 小时自动触发）

---

## Exit Conditions

满足以下条件时输出报告并退出：
- 所有 8 个步骤的数据均已获取（或数据源返回空/超时时标记为"未触发"）
- 综合预警等级已计算完毕
- 结构化报告已输出（总字数不超过 300 字主摘要）

---

## Action Specification

### Step 1：获取 1H 价格与 OI 历史数据

调用 `ant_futures_market_structure`（query_type: `futures_price_history`），参数传入 `symbol`、`interval=1h`、`exchange`。
再调用 `ant_futures_market_structure`（query_type: `futures_oi_aggregated`），参数传入 `symbol`。

对两组时序数据按时间戳对齐，计算每根 K 线：
- `oi_change_pct = (oi[t] - oi[t-1]) / oi[t-1] * 100`
- `price_direction`：收盘价 ≥ 开盘价为 `+1`，否则为 `-1`

### Step 2：识别背离区间

遍历每根 K 线，满足以下条件时标记 `divergence_flag = True`：
- `price_direction >= 0`（价格平或上涨）
- `oi_change_pct < -oi_decline_threshold_pct`（OI 下降超过阈值）

统计连续 `divergence_flag = True` 的 K 线数量（`consecutive_divergence_bars`）和累计 OI 跌幅（`total_oi_decline_pct`）。

**核心预警触发条件**：连续 ≥ 3 根 1H K 线出现背离，且累计 OI 下降 ≥ 5%。

### Step 3：资金费率趋势分析（辅助确认，+1 分）

调用 `ant_futures_market_structure`（query_type: `futures_funding_rate_history`），参数传入 `symbol`。

判断背离窗口内资金费率走向：
- 从正值下降或转负 → `funding_rate_trend = 下行`，信号置信度 +1
- 持续正值 → `funding_rate_trend = 中性/上行`

### Step 4：多空比分析（辅助确认，+1 分）

调用 `ant_futures_market_structure`（query_type: `futures_long_short_account_ratio`），参数传入 `symbol`。

在背离区间内，如账户多空比（Long Account Ratio）上升，表明散户在接盘，信号置信度 +1。

### Step 5：爆仓热力图分析（辅助确认，+1 分）

调用 `ant_futures_liquidation`（query_type: `futures_liquidation_heatmap`），参数传入 `symbol`。

识别当前价格以下最密集的多头爆仓区域。如密集区在当前价格 -3% ~ -10% 范围内，信号置信度 +1（存在清晰砸盘目标）。

### Step 6：Smart Money 合约动向（辅助确认，+2 分）

调用 `ant_smart_money`（query_type: `perp_trades`）。

背离窗口内 Smart Money 如果净空（空单开仓或多单平仓），信号置信度 +2（最强确认信号）。

### Step 7：链上鲸鱼空单预警（辅助确认，+1 分）

调用 `ant_perp_dex`（query_type: `perp_dex_whale_alert`）。

过滤出与 `symbol` 相关的大额空单开仓预警，出现则信号置信度 +1（CeFi + DeFi 协同做空）。

### Step 8：综合评分与预警等级

汇总 Step 2-7 的信号分数：

| 信号 | 权重 | 触发条件 |
|------|------|----------|
| 连续背离 K 线 ≥ 3 根 | 核心（必须） | 背离 K 线数 ≥ 3 |
| 累计 OI 跌幅 ≥ 5% | 核心（必须） | 累计跌幅 ≥ 5% |
| 资金费率下行 | +1 | 窗口内费率趋势为负 |
| 散户多空比上行 | +1 | 散户多头比例增加 |
| 清晰爆仓密集区 | +1 | 距当前价 -3% ~ -10% |
| Smart Money 净空 | +2 | SM 净空方向 |
| 链上鲸鱼空单 | +1 | 同期大额空单预警 |

**预警等级**：
- 高危预警（总分 ≥ 5）：强烈符合崩盘预谋模型，建议注意仓位风险
- 中等预警（总分 3-4）：部分信号吻合，需持续关注后续 K 线发展
- 低风险（总分 < 3）：当前信号不显著，模型暂不触发

核心信号（连续背离 + OI 跌幅）若均未触发，则直接输出"低风险，无背离信号"，不进入辅助步骤。

---

## Output Constraints

- 总文字输出不超过 300 字
- 优先用表格、数字、百分比替代文字描述
- 结论先行：第一行给出预警等级，细节按需展开

---

## Output Format

始终使用此模板：

```
═══════════════════════════════════════════════
  合约 OI 背离崩盘预谋信号识别器
  交易对: {SYMBOL}  |  分析窗口: {START} - {END} UTC
═══════════════════════════════════════════════

{ALERT_EMOJI} 预警等级: {LEVEL}（总分: {SCORE}/7）

核心背离信号:
  ├─ 连续背离 K 线: {N} 根 1H K 线
  ├─ 累计 OI 下降: {OI_DECLINE}%（从 ${OI_START} → ${OI_END}）
  └─ 价格区间: ${PRICE_START} → ${PRICE_END}（{PRICE_CHG}%）

辅助确认信号:
  ├─ {资金费率状态}
  ├─ {散户多空比状态}
  ├─ {爆仓密集区状态}
  ├─ {Smart Money 状态}
  └─ {链上鲸鱼状态}

风险提示:
  {一句话判断，≤ 50 字}

免责声明: 本分析仅供参考，不构成投资建议。
```

---

## Risk Parameters

**适用范围**：
- 主流合约交易对（BTC、ETH、SOL 等 CeFi 主要合约）
- 1H 级别信号最优；4H 为补充，5min 噪声过大不推荐

**不适用场景**：
- MEME 等低流动性币种（OI 基数小，信号噪声大）
- 现货市场（本 Skill 仅针对合约市场）

**数据局限**：
- OI 数据聚合上报延迟通常 5-15 分钟
- Smart Money 标签由算法识别，存在误标风险
- 爆仓热力图为估算值，非实际清算位
- 订单簿深度（托价挂单直接证据）暂未覆盖

**需人工判断的环节**：
- 背景市场环境（牛市整理 vs 真正顶部，背景不同则解读不同）
- 多个信号矛盾时（如 OI 背离显著但 Smart Money 净多）需综合研判
- 从信号出现到真正砸盘可能间隔数小时至数天

---

## 首次安装提示

```
目标用户：合约交易员、量化研究员、风控人员
使用场景：BTC 合约 OI 异常时快速判断主力是否在高位平多布空，识别崩盘预谋信号
如何使用：/oi-price-divergence-crash-detector BTC 1h 6
生成时间：2026-04-04 09:05:34
```
