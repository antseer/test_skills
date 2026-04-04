---
name: "polymarket-quant-signal"
description: "Polymarket量化多因子信号系统——六层过滤器同时扫描预测市场正期望值机会。当用户提到Polymarket、预测市场信号、EV缺口扫描、量化多因子过滤、KL散度检测、贝叶斯信号聚合、Kelly仓位计算、Stoikov执行价格、prediction market EV gap、polymarket quant signal、资金费率EV偏离时使用。适用于想在Polymarket预测市场中寻找BTC/ETH相关市场的正期望值套利机会，或想跟踪特定量化钱包绩效的用户。"
metadata:
  generated_at: "2026-04-04 07:30:00"
---

# Polymarket 量化多因子信号系统

## Overview

六因子量化过滤框架，扫描Polymarket预测市场与BTC/ETH期货市场之间的概率定价偏差，输出是否满足全绿执行条件（ALL_GREEN）的最终信号，并给出Kelly最优仓位和Stoikov最优执行保留价。

## Demand Context

方法论来源：@NFTCPS 在 Polymarket 上运行的量化交易机器人策略（原推文：https://x.com/NFTCPS/status/2036033303799791744）。核心思路是六个量化过滤器同时满足才下单，每隔数秒同步运行：LMSR定价偏离 → EV缺口量化 → KL散度联动检测 → 贝叶斯实时更新 → Kelly仓位优化 → Stoikov执行控制。

原作者本人指出其历史绩效数据存在选择性偏差，实际复现需谨慎验证。方法论归属 @NFTCPS，本 Skill 为量化实现参考，不构成投资建议。

## Features (Data Inputs)

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| symbol | string | 否 | 基础资产（用于KL散度和资金费率扫描） | BTC |
| market_slug | string | 否 | Polymarket市场标识符，如 "will-btc-exceed-100k-by-march-2026" | 跳过Step 5 |
| trader_address | string | 否 | 目标跟单钱包地址（Polygon链） | 跳过Step 0 |
| short_window_min | int | 否 | KL散度短周期窗口（分钟） | 5 |
| long_window_min | int | 否 | KL散度长周期窗口（分钟） | 15 |
| kl_threshold | float | 否 | KL散度触发阈值 | 0.10 |
| funding_zscore_threshold | float | 否 | 资金费率Z-score触发阈值 | 2.0 |
| ev_min_edge | float | 否 | 最小正期望值边际（Polymarket隐含概率差） | 0.05 |
| kelly_scale | float | 否 | Kelly系数缩放比例（建议0.2-0.5） | 0.25 |
| risk_aversion | float | 否 | Stoikov模型风险厌恶系数γ | 0.10 |

### MCP 数据源映射

| 数据需求 | MCP 工具 | query_type | 覆盖度 |
|----------|----------|------------|--------|
| BTC期货价格历史（多分辨率） | ant_futures_market_structure | futures_price_history | 覆盖 |
| BTC资金费率历史序列 | ant_futures_market_structure | futures_funding_rate_aggregated | 覆盖 |
| BTC未平仓量OI | ant_futures_market_structure | futures_oi_aggregated | 覆盖 |
| Taker主动买卖流（方向信号） | ant_market_indicators | taker_flow_aggregated | 覆盖 |
| 市场情绪评分 | ant_market_sentiment | coin_detail | 覆盖 |
| 价格波动率代理（布林带） | ant_market_indicators | boll | 覆盖 |
| Polymarket市场隐含概率 | 外部API | gamma-api.polymarket.com | 需外部访问 |
| Polygon链地址PnL分析 | ant_address_profile | pnl_summary | 需验证 |
| Polygon链地址交易记录 | ant_address_profile | transactions | 需验证 |

Polymarket外部API端点：`GET https://gamma-api.polymarket.com/markets?slug={market_slug}`，返回字段 `outcomePrices[0]` 即YES代币价格（0-1范围）。

## Entry Conditions

满足以下任一条件时触发本 Skill：

1. 用户提到 Polymarket、预测市场分析、EV缺口扫描、量化信号过滤
2. 用户提到 KL散度跨周期检测、贝叶斯信号聚合、Kelly仓位、Stoikov执行价
3. 用户想判断某个BTC/ETH Polymarket市场当前是否有正期望值机会
4. 用户想分析特定Polygon钱包的跟单价值
5. 用户提到 prediction market quant / polymarket quant signal / EV gap detection

## Exit Conditions

满足以下任一条件时完成分析并输出信号看板：

1. 完成全部8个步骤，输出六因子综合信号报告
2. 在Step 1数据采集阶段遇到MCP访问错误，降级为可用因子的局部分析
3. 六因子全部为红（NO_SIGNAL），输出当前市场状态说明和建议等待条件
4. 用户明确要求终止分析

## Action Specification

按以下顺序执行分析，每步产出作为下一步输入。

### Step 0: 目标钱包画像分析（仅在提供 trader_address 时执行）

1. 调用 `ant_address_profile`（query_type: `pnl_summary`, address=trader_address, chain=polygon），获取历史盈亏汇总
2. 调用 `ant_address_profile`（query_type: `transactions`, address=trader_address, chain=polygon），获取历史交易记录
3. 统计胜率、平均盈亏比、活跃时段分布、主要交易标的
4. 识别是否存在策略性模式（如特定时段集中交易、特定EV范围偏好）
5. 输出钱包绩效摘要：总PnL、胜率、交易频率、主要活跃时段
6. 注意：ant_address_profile 对Polymarket合约的解析能力需运行时验证，若返回空数据则标注"链上合约解析不支持"并跳过

### Step 1: 基础市场数据采集

1. 调用 `ant_futures_market_structure`（query_type: `futures_price_history`, symbol=BTC, exchange=binance），获取BTC期货价格历史
2. 调用 `ant_futures_market_structure`（query_type: `futures_funding_rate_aggregated`, symbol=BTC），获取过去30天资金费率序列
3. 调用 `ant_futures_market_structure`（query_type: `futures_oi_aggregated`, symbol=BTC），获取OI趋势数据
4. 将价格序列按 `short_window_min`（默认5min）和 `long_window_min`（默认15min）分段，为Step 2的KL散度计算准备两组价格变动分布
5. 输出：BTC价格序列（按两个时间粒度）、资金费率时间序列（近30天）、OI趋势方向

### Step 2: KL散度跨周期背离检测

这一步实现"5分钟和15分钟市场走势突然脱钩，赌它回归"的量化核心：

1. 基于Step 1的价格序列，计算两个周期的价格变动百分比序列
2. 将两组收益率序列离散化为概率分布 P（短周期）和 Q（长周期）
3. 计算KL散度：KL(P‖Q) = Σ P(x) · log(P(x)/Q(x))，加入平滑项 ε=1e-10 防止零除
4. 判断触发条件：KL值 > `kl_threshold`（默认0.10）
5. 判断方向：若P均值 > Q均值，方向为 BULLISH_REVERT（短期超买，预计向下回归）；反之为 BEARISH_REVERT
6. 输出：kl_divergence数值、kl_triggered（bool）、kl_direction

### Step 3: 资金费率EV缺口扫描（LMSR代理指标）

资金费率极端偏离是CeFi市场"情绪把价格推偏真实概率"的最佳代理指标：

1. 使用Step 1获取的过去30天资金费率序列，计算均值μ和标准差σ
2. 获取当前最新资金费率（序列末位）
3. 计算 Z-score = (当前资金费率 - μ) / σ
4. 判断方向：Z-score > +`funding_zscore_threshold` → 市场过度偏多 → EV方向为SHORT；Z-score < -threshold → EV方向为LONG；否则为NEUTRAL
5. 输出：funding_rate_zscore数值、ev_direction（LONG/SHORT/NEUTRAL）

### Step 4: 贝叶斯信号聚合

整合多维度信号，动态更新方向概率估计：

1. 调用 `ant_market_indicators`（query_type: `taker_flow_aggregated`, symbol=BTC），获取Taker主动买卖净流向和成交量
2. 调用 `ant_market_sentiment`（query_type: `coin_detail`, coin=bitcoin），获取市场情绪评分（0-100）
3. 构建先验概率 P_prior：以Step 2（KL方向）和Step 3（资金费率方向）的信号一致性加权平均
   - 两者方向一致：P_prior = 0.60
   - 两者方向相反：P_prior = 0.50（中性，贝叶斯更新将决定方向）
4. 构建似然信号向量：
   - Taker净买入率 L1 = (buy_volume - sell_volume) / total_volume，范围[-1, 1]
   - 成交量异常倍数 L2 = 当前成交量 / 近30日均量，截断至[0.5, 3.0]
   - 情绪归一化 L3 = sentiment_score / 100，范围[0, 1]
5. 贝叶斯更新：P_posterior = normalize(likelihood_score × P_prior)，其中 likelihood_score = (1 + L1) × L2 × L3
6. 触发条件：P_posterior > 0.60 且方向与Step 3一致
7. 输出：p_bayes（后验概率）、bayes_confirmed（bool）

### Step 5: Polymarket EV缺口精确计算（仅在提供 market_slug 时执行）

将模型概率与Polymarket隐含概率对比，精确测量EV缺口：

1. 调用外部API：`GET https://gamma-api.polymarket.com/markets?slug={market_slug}`，获取YES代币当前价格
2. 提取 `outcomePrices[0]` 作为 p_market（市场隐含概率，0-1范围）
3. 计算EV缺口：ev_gap = p_bayes - p_market（正数代表模型认为概率被低估，买YES有正EV）
4. 触发条件：abs(ev_gap) > `ev_min_edge`（默认0.05）
5. 若未提供market_slug，跳过此步骤，以Step 3资金费率EV方向作为替代，p_market设为null，ev_gap设为null
6. 输出：p_market（或null）、ev_gap（或null）、ev_gap_triggered（bool或null）

### Step 6: Kelly仓位计算

根据概率优势计算最优仓位比例：

1. 若Step 5有效（p_market != null）：赔率 b = (1 - p_market) / p_market（二元市场标准赔率）
2. 若Step 5跳过：用资金费率Z-score映射隐含赔率，b = 1.0（保守估计）
3. 计算理论Kelly系数：f* = (b × p_bayes - (1 - p_bayes)) / b
4. 计算实际仓位：f_actual = f* × `kelly_scale`（默认0.25）
5. f* <= 0 时，数学上无正期望，标注 NO_SIGNAL
6. 输出：kelly_fraction_theoretical（f*）、kelly_fraction_actual（f_actual）、kelly_triggered（bool）

### Step 7: Stoikov最优执行价格计算

确定不追高的最优入场保留价：

1. 调用 `ant_market_indicators`（query_type: `boll`, symbol=BTC），获取当前布林带数据
2. 提取布林带带宽，计算σ = (upper_band - lower_band) / 2（价格波动率代理）
3. 计算最优保留价：r = mid_price - q × γ × σ²，其中 mid_price=当前市场中间价，q=f_actual，γ=`risk_aversion`（默认0.10）
4. 判断当前价格是否在可执行区间：
   - 做多方向：当前价格 <= r → price_in_range = true
   - 做空方向：当前价格 >= r → price_in_range = true
5. 输出：r_optimal（最优保留价）、current_price、price_in_range（bool）

### Step 8: 六因子综合评分与最终决策

汇总全部过滤器结果，输出最终信号状态：

六因子通过条件（ALL_GREEN需全部满足）：
- KL散度触发：kl_divergence > kl_threshold
- 资金费率Z-score超阈值：abs(funding_rate_zscore) > funding_zscore_threshold
- 贝叶斯后验概率：p_bayes > 0.60
- EV缺口：ev_gap > ev_min_edge（若无Polymarket数据，此因子标注为BYPASSED）
- Kelly系数：kelly_fraction_theoretical > 0
- 执行价格在区间内：price_in_range = true

信号状态规则：
- 全部6因子通过 → ALL_GREEN（立即执行条件）
- EV因子因无market_slug被BYPASSED，其余5因子全通过 → ALL_GREEN_NO_EV（条件执行）
- 3-5个因子通过 → PARTIAL_N（N = 通过数量，监控等待）
- 少于3个因子通过 → NO_SIGNAL（当前无机会）

## 输出约束

- 总文字输出不超过 300 字
- 优先用表格、数字替代文字描述
- 结论先行：第一行给出信号状态（ALL_GREEN / PARTIAL_N / NO_SIGNAL）
- 超过300字的细节内容须在"详细因子分析"折叠块中提供

## 报告结构

始终使用此模板输出最终报告：

```
=== Polymarket 量化多因子信号报告 ===
分析时间: {timestamp} UTC
分析标的: {symbol} | 目标市场: {market_slug 或 "未提供"}

━━━━━ 六因子过滤结果 ━━━━━

因子          数值              阈值     状态
KL散度        {kl_divergence}   >{kl_threshold}  {触发/未触发}
资金费率Z     {z_score}         >{threshold}     {触发/未触发}
贝叶斯概率    {p_bayes}         >0.60            {触发/未触发}
EV缺口        {ev_gap}          >{ev_min_edge}   {触发/跳过/未触发}
Kelly系数     {f*}              >0               {触发/未触发}
执行价格区间  {price_in_range}  —                {在区间/等待}

━━━━━ 综合评估 ━━━━━

信号状态: {ALL_GREEN / PARTIAL_N / NO_SIGNAL}
建议方向: {LONG / SHORT / WAIT}
建议仓位: {f_actual × 100}% 账户净值
执行条件: {执行保留价 r_optimal} USDT
```

## Risk Parameters

| 约束项 | 参数 | 说明 |
|--------|------|------|
| Kelly缩放系数 | kelly_scale (默认0.25) | 建议0.2-0.5，防止仓位过重 |
| 最小EV门槛 | ev_min_edge (默认0.05) | 过滤低质量机会，覆盖gas成本 |
| KL散度阈值 | kl_threshold (默认0.10) | 过低则误触发过多 |
| 资金费率Z阈值 | funding_zscore_threshold (默认2.0) | 2.0对应约95%历史分位 |
| 贝叶斯后验门槛 | 0.60（固定） | 低于此值信号可靠性不足 |
| Stoikov风险厌恶 | risk_aversion (默认0.10) | 越高保留价越保守 |

重要限制：
- 本 Skill 仅输出信号，不执行实际Polymarket交易
- 在极端市场波动期（如重大黑天鹅事件），所有阈值需人工上调后再参考信号
- Polymarket外部API需网络访问，存在延迟和访问限制
- ant_address_profile 对Polymarket合约地址的解析能力需运行时验证

## 首次安装提示

```
目标用户：量化交易员、DeFi投研人员、预测市场参与者
使用场景：BTC相关Polymarket预测市场中寻找六因子全绿的正期望值入场机会
如何使用：/polymarket-quant-signal --symbol=BTC --market_slug=will-btc-exceed-100k-by-march-2026
生成时间：2026-04-04 07:30:00
```

## 示例

**示例 1：完整六因子扫描**
输入：`/polymarket-quant-signal --symbol=BTC --market_slug=will-btc-exceed-100k-by-june-2026`
输出：六因子看板 + Polymarket EV缺口精确计算 + Kelly仓位 + Stoikov执行价

**示例 2：无Polymarket市场（退化模式）**
输入：`/polymarket-quant-signal --symbol=BTC`
输出：五因子看板（EV缺口标注为BYPASSED）+ 资金费率EV方向替代 + Kelly仓位

**示例 3：跟单画像分析**
输入：`/polymarket-quant-signal --symbol=BTC --trader_address=0xabc...123`
输出：钱包绩效摘要（胜率、PnL、活跃时段）+ 六因子信号看板
