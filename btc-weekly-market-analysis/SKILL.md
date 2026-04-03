---
name: "btc-weekly-market-analysis"
description: "BTC 周度综合市场分析 — 宏观流动性 × ETF资金 × 衍生品结构 × 链上数据 → 短中期情景推演与周报生成。当用户提到 BTC周报、BTC市场分析、BTC weekly analysis、本周BTC怎么样、BTC宏观面分析、BTC多空判断、比特币周度报告、本周行情分析时使用。也适合定期（周日/周一）自动触发生成上周市场总结。"
---

## Overview

按五层递进框架（宏观 → 机构资金 → 市场结构 → 链上 → 价格判断）对 BTC 进行多维度周度分析，调用 Antseer MCP 工具采集数据，生成结构化 Markdown 周报，包含关键信号、情景路径和关键观察变量清单。

方法论归属原作者 @Guolier8（推文：https://x.com/Guolier8/status/2039989943213404528）。

## Demand Context

来源推文核心主题：BTC 多维度周度市场分析，宏观流动性 × ETF资金 × 衍生品结构 × 链上数据 → 短中期情景推演。

作者构建了"宏观 → 机构资金 → 市场结构 → 链上 → 价格判断"的五层递进分析框架。核心逻辑：先锚定外生宏观变量（流动性环境、地缘风险），再追踪机构资金行为（ETF流出/流入），然后用衍生品市场结构验证情绪（资金费率、期权偏斜、OI），最后通过链上数据确认资金归宿（鲸鱼持仓、交易所存量、稳定币活跃度），综合得出短中期价格区间预判。

## Features (Data Inputs)

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| symbol | string | 是 | 分析的主标的代币 | BTC |
| start_date | string | 否 | 分析周期开始日期（YYYY-MM-DD） | 上周一 |
| end_date | string | 否 | 分析周期结束日期（YYYY-MM-DD） | 上周日 |
| include_eth_etf | boolean | 否 | 是否纳入 ETH ETF 资金流分析 | true |
| whale_threshold | integer | 否 | 鲸鱼地址定义阈值（BTC数量） | 1000 |
| whale_lookback_days | integer | 否 | 鲸鱼净增减持统计窗口（天） | 14 |
| fear_greed_threshold | integer | 否 | 极端恐慌判断阈值（低于此值触发概率统计） | 20 |

**MCP 数据源映射：**

| 数据需求 | MCP 工具 | query_type | 覆盖度 |
|----------|----------|------------|--------|
| 宏观利率（Fed） | ant_macro_economics | federal_funds_rate | ✅ |
| 通胀数据（CPI） | ant_macro_economics | cpi | ✅ |
| 黄金价格（代理） | ant_precious_metal_tokens | simple_price, coin_id=paxg | ✅ |
| BTC ETF 资金流 | ant_etf_fund_flow | btc_etf_flow | ✅ |
| ETH ETF 资金流 | ant_etf_fund_flow | eth_etf_flow | ✅ |
| 资金费率（永续） | ant_futures_market_structure | futures_funding_rate_aggregated | ✅ |
| 合约持仓量 OI | ant_futures_market_structure | futures_oi_aggregated | ✅ |
| 多空比 | ant_futures_market_structure | futures_long_short_ratio | ✅ |
| 爆仓数据 | ant_futures_liquidation | futures_liquidation_aggregated | ✅ |
| 交易所 BTC 存量 | ant_fund_flow | exchange_reserve | ✅ |
| 交易所 BTC 净流量 | ant_fund_flow | exchange_netflow | ✅ |
| 稳定币总市值 | ant_stablecoin | mcap | ✅ |
| 鲸鱼净增减持 | ant_token_analytics | flow_intelligence / holders | ⚠️ 需聚合计算 |
| 盈利供应比例 | ant_token_analytics | mvrv | ⚠️ 近似推算 |
| BTC 价格/K线 | ant_spot_market_structure | coins_markets | ✅ |
| Fear & Greed Index | ant_market_sentiment | coin_detail | ✅ |
| 技术指标 | ant_market_indicators | boll / macd | ⚠️ 需确认字段 |
| 期权 put/call 偏斜 | 无 MCP 覆盖 | — | ❌ 需外部 API |
| Brent 原油价格 | 无 MCP 覆盖 | — | ❌ 需外部数据 |

## Entry Conditions

满足以下任一条件时触发本 Skill：

1. 用户主动请求 BTC 周报、本周行情分析或 BTC 多空判断
2. 用户提问"本周 BTC 怎么样"、"BTC 宏观面如何"、"BTC weekly analysis"等
3. 定期自动触发（建议每周日/周一运行，分析上一周数据）
4. 宏观事件触发（如 Fed 决议日后，主动更新宏观信号层）

当 `start_date` 和 `end_date` 未指定时，自动推算为"上周一至上周日"。

## Exit Conditions

1. 已完成全部 7 个分析步骤（宏观 / 地缘 / ETF / 衍生品 / 链上 / 价格结构 / 综合研判）
2. 已生成完整结构化周报（含信号汇总表、情景路径表、关键观察变量清单）
3. 若某 MCP 数据源不可用，在对应章节标注"数据暂不可用"并继续其余分析
4. 若 Fear & Greed 指数低于 `fear_greed_threshold`，附加历史统计概率说明

## Action Specification

### Step 1: 宏观流动性环境评估

调用 `ant_macro_economics`（query_type: `federal_funds_rate`）获取当前 Fed 利率水平和近期路径。

调用 `ant_macro_economics`（query_type: `cpi`）获取最新通胀数据（CPI/PCE）。

判断宏观信号：
- 利率高位且通胀上修 → 鹰派信号（偏空宏观环境）
- 利率下行路径清晰且通胀受控 → 鸽派信号（偏多宏观环境）
- 利率持平、通胀数据混合 → 中性信号

评估 DXY（若 `ant_macro_economics` 支持则调用，否则基于利率路径推断强弱方向）。

记录输出：宏观流动性信号（鹰派 / 中性 / 鸽派）+ 关键数据点（利率数值、通胀读数）。

### Step 2: 地缘政治与外生风险评估

调用 `ant_precious_metal_tokens`（query_type: `simple_price`, coin_id: `paxg`）获取黄金 token 价格作为黄金代理。

分析 BTC 与黄金联动：
- 黄金涨而 BTC 未跟涨 → BTC 失去避险属性，外生风险溢价主导
- 黄金与 BTC 同涨 → 流动性宽松预期主导
- 黄金跌而 BTC 跌幅更大 → Risk-off 情绪主导

若有外部宏观新闻（用户提供或已知事件），纳入分析上下文：油价 > $90 视为通胀压力加剧；地缘冲突升级纳入悲观情景权重。

输出：地缘风险信号（高 / 中 / 低）+ BTC vs 黄金相对表现描述。

### Step 3: ETF 资金流向分析

调用 `ant_etf_fund_flow`（query_type: `btc_etf_flow`）获取分析周期内 BTC ETF 各产品日度净流量。

若 `include_eth_etf=true`，同步调用 `ant_etf_fund_flow`（query_type: `eth_etf_flow`）。

分析步骤：
1. 计算周内每日净流量，识别最大单日流出（极端信号）
2. 判断各大产品贡献（IBIT 主导还是尾部产品集体流出）
3. 检测背离信号：ETF 大量流入日 BTC 是否同步站稳关键位，若否 → 标记"借流动性出货"警告
4. 若 BTC+ETH ETF 同日大额净流出（合计超 $200M）→ 标记"机构资金全面转向"信号

计算并输出：周净流量（美元汇总）、资金方向（净流入 / 净流出 / 混合）、ETF 背离信号（有 / 无）。

### Step 4: 衍生品市场结构诊断

调用 `ant_futures_market_structure`（query_type: `futures_funding_rate_aggregated`, symbol: BTC）获取资金费率。

调用 `ant_futures_market_structure`（query_type: `futures_oi_aggregated`, symbol: BTC）获取合约持仓量 OI。

调用 `ant_futures_market_structure`（query_type: `futures_long_short_ratio`, symbol: BTC）获取多空比。

调用 `ant_futures_liquidation`（query_type: `futures_liquidation_aggregated`, symbol: BTC）获取爆仓数据。

判断逻辑：
- 资金费率 < 0.01% → 偏空（正常牛市为 0.03%）；< 0 → 做空情绪极端
- OI 单周下降 > 3% → 去杠杆进行中
- 多头爆仓为主 → 拉盘受阻；空头爆仓为主 → 短期反弹动能
- 期权数据（若无 MCP 覆盖）在报告中标注"数据缺失，建议参考 Laevitas / Deribit"

输出：衍生品情绪（偏多 / 中性 / 偏空）、OI 变化百分比、资金费率数值、爆仓方向统计。

### Step 5: 链上资金结构分析

调用 `ant_fund_flow`（query_type: `exchange_reserve`, asset: BTC）获取交易所 BTC 存量。

调用 `ant_fund_flow`（query_type: `exchange_netflow`, asset: BTC）获取交易所净流量（净流出 → 减少抛压）。

调用 `ant_stablecoin`（query_type: `mcap`）获取 USDT/USDC 总市值（衡量场外资金体量）。

调用 `ant_token_analytics`（query_type: `mvrv`, asset: bitcoin）获取 MVRV 近似推算盈利供应状态。

尝试调用 `ant_token_analytics`（query_type: `flow_intelligence` / `holders`, token: BTC, chain: bitcoin）：
- 按持仓量分层，筛选 > `whale_threshold` BTC 的地址
- 计算 `whale_lookback_days` 天窗口内的净增减持（正为增持，负为减持）
- 若无法直接分层，在报告中标注"鲸鱼数据为估算值"

综合判断供需对比：
- 卖压评级：交易所存量趋势 + 大户净流量方向
- 买力评级：稳定币总量变化 + 场外资金活跃度

若盈利供应率（MVRV 近似）< 60% → 接近早期熊市区间；< 55% → 深度底部警戒线。

输出：链上供需信号（卖压 高/中/低 × 买力 强/中/弱）+ 关键数值。

### Step 6: 价格结构与关键位分析

调用 `ant_spot_market_structure`（query_type: `coins_markets`）获取 BTC 当周价格区间（OHLCV）。

尝试调用 `ant_market_indicators`（query_type: `boll` 或 `macd`, symbol: BTC）获取技术指标数据。

分析步骤：
1. 识别当周价格高低点，计算周涨跌幅
2. 标注关键支撑位（从当前价格向下依次列出 3 个）
3. 标注关键压力位（从当前价格向上依次列出 3 个，含短期持有者成本基准）
4. 评估近期涨跌驱动：结合 OI 和 ETF 数据判断是"真实需求"还是"被动对冲"驱动
5. 若价格日收盘站稳某关键位以上超过 3 日 → 标记为有效突破；若未能站稳 → 标记为假突破

输出：价格结构判断（强势突破 / 震荡筑底 / 弱势下行）+ 关键支撑/压力位表格。

### Step 7: 综合研判与情景推演

汇总 Step 1-6 的信号，按以下框架生成综合判断：

**信号计数（偏空信号数量统计）：**
- 宏观鹰派 → +1 偏空
- ETF 周净流出 → +1 偏空
- 资金费率低（< 0.01%）→ +1 偏空
- 链上买力弱（稳定币持平或下降）→ +1 偏空
- 如果偏空信号 >= 3 → 短期方向：偏弱震荡
- 如果有日收盘站稳关键位且 ETF 回流 → 短期方向：突破确认

**中期情景路径（1-3个月）：**
- 乐观情景：触发条件（地缘缓和 / 通胀下修 / 降息预期回升）→ 目标区间 → 概率估算（30-40%）
- 悲观情景：触发条件（冲突升级 / 持续通胀 / 流动性收紧）→ 目标区间 → 概率估算（40-50%）
- 极端情景：触发条件（系统性风险 / 黑天鹅）→ 目标区间 → 概率估算（10-20%）

**统计辅助（若 Fear & Greed < `fear_greed_threshold`）：**
- 标注历史统计：F&G 极端恐慌区间的 30 日正收益概率（参考历史数据）
- 结合鲸鱼净增减持信号，对比历史相似时期（如 2023 Q4 底部）

**关键观察变量清单（至少 5 条）：**
- ETF 是否重新大额净流入
- 宏观利率路径是否出现转折信号
- 盈利供应率是否跌破 55% 警戒线
- Fear & Greed 是否跌破 fear_greed_threshold
- 价格日收盘是否站稳下一关键阻力位

生成完整结构化周报（见「报告结构」）。

## 报告结构

始终使用以下模板输出：

```
## {symbol} 周度市场分析报告 — {start_date} ~ {end_date}

### 综合结论（先行）
{本周价格走势摘要，一句话核心判断，短期偏向}
**短期（1-2周）：{short_term_bias}。中期：{中期关键变量}。**

### 一、宏观信号 {信号图标} {macro_signal}
| 指标 | 数值 | 信号 |
|------|------|------|
| Fed 利率 | {rate} | {comment} |
| 通胀（CPI/PCE） | {cpi} | {comment} |
| DXY | {dxy_estimate} | {comment} |
| 黄金（PAXG）本周涨跌 | {gold_pct}% | {comment} |

### 二、ETF 资金 {信号图标} {etf_direction}
| 日期 | BTC ETF 净流量 | 备注 |
|------|---------------|------|
{etf_daily_table}
| 周合计 | **{etf_weekly_netflow_usd}** | {direction_note} |
{eth_etf_row if include_eth_etf}
**背离信号**: {etf_divergence_flag 描述}

### 三、衍生品结构 {信号图标} {derivatives_sentiment}
| 指标 | 数值 | 基准/信号 |
|------|------|---------|
| 资金费率 | {funding_rate}% | 正常牛市 0.03%+ |
| OI | {oi_value}（{oi_change_pct}%）| {去杠杆/增杠杆} |
| 多空比 | {long_short_ratio} | {偏多/偏空} |
| 爆仓（多头/空头） | {liq_long}/{liq_short} | {方向信号} |

### 四、链上结构 {信号图标} 供需评估
| 指标 | 数值 | 信号 |
|------|------|------|
| 鲸鱼（>{whale_threshold} BTC）{whale_lookback_days}天净增减持 | {whale_net_accumulation} BTC | {增持/减持信号} |
| 交易所 BTC 存量变化 | {exchange_reserve_change} BTC | {抛压信号} |
| 稳定币总量（USDT+USDC） | ${stablecoin_mcap_usd}B | {买力信号} |
| MVRV 近似盈利供应率 | ~{supply_in_profit_pct}% | {周期位置信号} |
| Fear & Greed 指数 | {fear_greed_index} | {情绪标签} |

**核心矛盾**: {卖压vs买力综合描述}

### 五、价格结构
- 支撑: {key_supports 列表，降序排列，以 → 分隔}
- 压力: {key_resistances 列表，升序排列，以 → 分隔}
- 本周价格区间: {low} ~ {high}（周涨跌 {pct}%）
- 近期驱动判断: {真实需求/被动对冲}

### 六、综合判断
**短期（1-2周）: {short_term_bias}，参考区间 {range}**
- 突破确认条件: {condition}

**中期（1-3月）情景路径:**
| 情景 | 触发条件 | 目标区间 | 概率估计 |
|------|---------|---------|---------|
| 乐观 | {scenario_bull_trigger} | {scenario_bull_target} | ~{prob_bull}% |
| 悲观 | {scenario_bear_trigger} | {scenario_bear_target} | ~{prob_bear}% |
| 极端 | {scenario_extreme_trigger} | {scenario_extreme_target} | ~{prob_extreme}% |

**关键观察变量:**
{key_watch_variables 编号列表}

{if fear_greed_index < fear_greed_threshold}
**统计参考（F&G 极端恐慌区间）：**
- F&G < {fear_greed_threshold} 历史正收益概率（30日）：参考历史数据约 65-70%
- 当前鲸鱼增持信号：结合历史相似周期（如 2023 Q4 底部）对比

*免责声明：本报告由 AI 自动生成，基于历史数据不能预测未来走势。方法论归属原作者 @Guolier8。不构成投资建议。*
```

## Risk Parameters

- **数据部分覆盖**: 期权 put/call 偏斜（Deribit）、Brent 原油价格、BTC-SPX 滚动相关性无 MCP 覆盖，报告中标注数据缺失并给出外部数据源建议
- **鲸鱼数据精度**: 持仓分层计算为估算值，非直接输出字段，存在聚合误差；明确标注"估算值"
- **盈利供应率近似**: MVRV 只能近似推断供应盈利状态，精度低于 Glassnode SOPR/UTXO in profit 专项数据
- **情景概率主观性**: 乐观/悲观/极端情景概率为基于信号计数的经验估算，分析师应基于额外信息主观调整
- **黑天鹅失效**: 监管突发、交易所暴雷等极端事件可能使历史规律暂时失效，框架无法覆盖
- **统计样本有限**: F&G 极端恐慌区间的历史统计基于有限样本，显著性不足时在报告中明确标注
- **分析窗口依赖**: 当 start_date/end_date 未指定时，自动推算上周区间，时区以 UTC 为基准

## 首次安装提示

```
目标用户：加密货币投研人员、宏观量化交易员、机构资产配置团队、高净值个人投资者
使用场景：每周定期（建议周日/周一）生成 BTC 上周市场总结报告，或主动查询特定时间段 BTC 市场状态
如何使用：/btc-weekly-market-analysis BTC --start_date=2026-03-22 --end_date=2026-03-28
```
