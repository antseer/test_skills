---
name: "crash-premeditation-signal-detector"
description: "识别主力高位平多+叠加空单的崩盘预谋信号。当市场出现价格上涨但合约持仓量（OI）持续下滑时，用多维度交叉验证（资金费率、大户多空比、Smart Money 仓位、爆仓墙、Taker 流）判断是否存在预谋砸盘布局。触发词：崩盘预谋信号、OI背离检测、主力出货分析、crash signal、OI divergence、pre-crash detection、砸盘预警"
metadata:
  generated_at: "2026-04-04 09:59:22"
---

# 崩盘预谋模型信号检测

## Overview

检测 CeFi 衍生品市场中主力高位平多、吸引散户/算法做多后悄悄叠加空单的崩盘预谋行为。核心信号是**价格上涨同时 OI 持续下降**，辅以资金费率、大户多空比、Smart Money 合约仓位、爆仓热力图、Taker 流的多维交叉验证，输出 4 级信号评级。

## Demand Context

来源推文：@wuk_Bitcoin（2026-02-01 17:43 UTC）

作者描述了 CeFi 衍生品市场中的典型主力砸盘操作模式，三步流程：
1. 主力高位平多，同时用大量 Maker 买单（托单）维持价格不跌
2. 散户和机构电子盘（量化做市商）因价格稳定而进场做多，为空单提供对手盘
3. 主力撤托单+叠加空单顺势砸盘，触发连锁清算

方法论归属原作者 @wuk_Bitcoin，本 Skill 为自动化实现。

## Features (Data Inputs)

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| symbol | string | 是 | — | 交易对符号，大写，如 BTC、ETH |
| lookback_hours | integer | 否 | 6 | 回溯分析时间窗口（小时） |
| timeframe | string | 否 | 1h | 价格和 OI 数据时间粒度 |
| oi_decline_threshold_pct | float | 否 | 5.0 | 触发预警的 OI 下降幅度阈值（%） |
| price_rise_threshold_pct | float | 否 | 1.0 | 同期价格上涨最低幅度（%），排除横盘噪声 |
| exchanges | list | 否 | ["Binance","Bybit","OKX"] | OI 统计的交易所范围 |

**MCP 数据源映射（Antseer ant-on-chain-mcp）：**

| 数据需求 | MCP 工具 | query_type |
|----------|----------|------------|
| 1H 价格历史 | ant_futures_market_structure | futures_price_history |
| OI 聚合时序 | ant_futures_market_structure | futures_oi_aggregated |
| 资金费率历史 | ant_futures_market_structure | futures_funding_rate_history |
| 大户多空比 | ant_futures_market_structure | futures_long_short_ratio |
| Smart Money 合约仓位 | ant_smart_money | perp_trades |
| 爆仓热力图 | ant_futures_liquidation | futures_liquidation_heatmap |
| Taker 流方向 | ant_market_indicators | taker_flow_aggregated |

## Entry Conditions

触发 Skill 运行的任意条件：
- 用户提供 symbol 并请求崩盘预谋信号分析
- 触发词命中：崩盘预谋信号、OI背离检测、主力出货分析、crash signal、OI divergence、pre-crash detection、砸盘预警
- 定时巡检场景：每小时对主流币对运行
- 事件驱动：价格在 1-4 小时内出现异常拉升

**前置过滤（节省 API 调用）：** 先验证 `price_change_pct >= price_rise_threshold_pct`，不满足则直接返回 `No Signal`，跳过后续步骤。

## Exit Conditions

满足以下任意条件时输出报告并退出：
- 核心条件不满足（价格未涨或 OI 未达下降阈值）→ 输出 `No Signal`
- 完成全部 7 步数据采集与评分 → 输出对应信号评级报告
- 数据获取失败超过 3 个维度 → 标注数据缺失，降级输出可用维度报告

## Action Specification

### Step 1：获取价格走势

调用 `ant_futures_market_structure`（query_type: `futures_price_history`），参数：symbol、exchange=Binance、interval=1h，回溯 lookback_hours。

计算：`price_change_pct = (close_end - close_start) / close_start * 100`

如果 `price_change_pct < price_rise_threshold_pct`，标记 `price_direction=flat_or_down`，直接跳至 Step 8 输出 `No Signal`。

### Step 2：OI 聚合数据与趋势识别

调用 `ant_futures_market_structure`（query_type: `futures_oi_aggregated`），参数：symbol。

计算：
- `oi_change_pct = (oi_end - oi_start) / oi_start * 100`
- `consecutive_decline_count`：窗口内逐小时 OI 下降的连续根数

触发背离条件：`oi_change_pct <= -oi_decline_threshold_pct` 且 `consecutive_decline_count >= 3`，设 `oi_divergence_detected = true`。

核心条件不满足（oi_divergence_detected = false）→ 跳至 Step 8 输出 `No Signal`。

### Step 3：资金费率异常检测

调用 `ant_futures_market_structure`（query_type: `futures_funding_rate_history`），参数：symbol。

取近 3 期资金费率，计算 `avg_funding_rate`：
- 均值 > 0 → `funding_rate_signal = positive_crowded`（+2 分）
- 接近 0 → `neutral`（+0 分）
- 均值大幅负偏 → `short_dominant`（-1 分，空单布局可能接近尾声）

### Step 4：大户多空比变化分析

调用 `ant_futures_market_structure`（query_type: `futures_long_short_ratio`），参数：symbol、exchange=Binance。

判断窗口内多空比变化方向：
- 下降（大户减多）→ `ls_ratio_change = declining`（+2 分）
- 稳定 → `stable`（+0 分）
- 上升 → `rising`（-1 分，与崩盘预谋模型不符）

### Step 5：Smart Money 合约仓位监测

调用 `ant_smart_money`（query_type: `perp_trades`），参数：chains（主要链）。

判断价格上涨期间 Smart Money 合约净方向：
- 净空仓 → `smart_money_perp_direction = net_short`（+3 分）
- 中性 → `neutral`（+0 分）
- 净多仓 → `net_long`（-1 分）

注意：此数据覆盖链上永续合约（GMX、dYdX 等），不含 Binance/OKX 等 CeFi 主力仓位，为辅助参考信号。

### Step 6：爆仓热力图预警

调用 `ant_futures_liquidation`（query_type: `futures_liquidation_heatmap`），参数：symbol。

分析当前价格下方是否存在密集多单爆仓区：
- 存在密集爆仓区 → `liquidation_wall_below = true`（+2 分），记录 `liquidation_concentration_usd`
- 不存在 → `false`（+0 分）

### Step 7：Taker 流方向验证

调用 `ant_market_indicators`（query_type: `taker_flow_aggregated`），参数：symbol。

判断 Taker 流方向：
- 多头主导（散户仍在买入，布局阶段特征）→ `taker_direction = buy_dominant`（+1 分）
- 中性 → `neutral`（+0 分）
- 空头主导（撤托或砸盘已发动）→ `sell_dominant`（-1 分，布局可能已结束）

### Step 8：综合评分与信号评级

汇总 Step 1-7 结果，按以下权重计算得分（满分 10 分）：

| 信号维度 | 权重 | 触发条件 |
|----------|------|---------|
| 价格上涨 + OI 持续下降 | 核心必要条件 | price_change_pct >= 阈值 AND oi_divergence_detected = true |
| 资金费率正向拥挤 | +2 分 | funding_rate_signal = positive_crowded |
| 大户多空比下降 | +2 分 | ls_ratio_change = declining |
| Smart Money 净空仓 | +3 分 | smart_money_perp_direction = net_short |
| 下方爆仓墙密集 | +2 分 | liquidation_wall_below = true |
| Taker 流仍偏多 | +1 分 | taker_direction = buy_dominant |

评级规则：
- 核心条件不满足 → `No Signal`
- 核心满足，得分 0-3 → `Weak（弱信号）` — 继续观察
- 核心满足，得分 4-7 → `Moderate（中等信号）` — 建议减少多单风险敞口
- 核心满足，得分 8+ → `Strong（强信号）` — 高度警惕，主力空单布局可能已接近完成

## 输出约束

- 总文字输出不超过 300 字
- 优先用表格、数字、百分比替代文字描述
- 结论先行：第一行给出核心判断（信号评级 + 得分），细节按需展开

## Output Format

始终使用此模板输出：

```
═══════════════════════════════════════════
崩盘预谋模型信号检测报告
═══════════════════════════════════════════
标的:       {symbol} ({symbol}USDT Perpetual)
分析窗口:   {start_time} → {end_time} UTC ({lookback_hours}h)
生成时间:   {current_time} UTC

─────────────── 信号评级 ───────────────
{signal_emoji} {signal_level}  得分: {score}/10

─────────────── 关键指标 ───────────────
价格变化:      {price_change_pct}%   {direction}
OI 变化:       {oi_change_pct}%      {oi_direction}
连续下降:      {consecutive_decline_count} 小时
资金费率:      {avg_funding_rate}%   ({funding_rate_signal})
大户多空比:    {ls_ratio_change}
Smart Money:  {smart_money_perp_direction}
下方爆仓墙:   {liquidation_wall_below}   ({liquidation_concentration_usd})
Taker 流:     {taker_direction}

─────────────── 结论 ───────────────
{summary}

⚠️ 风险提示: {risk_note}
═══════════════════════════════════════════
```

## Risk Parameters

**该 Skill 能做什么：**
- 基于量化信号识别"价格涨 + OI 跌"的崩盘预谋模型特征
- 多维度交叉验证（7 个数据维度）
- 支持主流合约品种（BTC、ETH 等机构参与度高的品种）
- 可配置回溯窗口和阈值参数

**该 Skill 不能做什么：**
- 无法实时检测订单簿托单（缺乏 L2 订单簿数据）
- 无法预测砸盘精确时间点——仅识别"正在布局"阶段
- 不适用于小市值山寨币（OI 和 Smart Money 数据覆盖有限）
- 无法区分"主力主动出货"与"市场自然去杠杆"（两者均表现为价格涨 + OI 跌）

**数据局限性：**
- OI 数据滞后约 1-5 分钟
- Smart Money perp_trades 仅覆盖链上永续合约，不含 CeFi 主力仓位
- 资金费率通常每 8 小时结算一次，中间时段反映不够及时

**需要人工判断的环节：**
- Weak/Moderate 信号需结合宏观背景（ETF 资金流、BTC 关联走势）做最终判断
- Strong 信号仍不能排除假信号（如流动性自然撤出导致的 OI 下降）

## 首次安装提示

```
目标用户：合约交易员、量化研究员、风控人员
使用场景：BTC/ETH 合约出现价格异常拉升时，快速判断是否存在崩盘预谋布局
如何使用：/crash-premeditation-signal-detector BTC 6
生成时间：2026-04-04 09:59:22
```
