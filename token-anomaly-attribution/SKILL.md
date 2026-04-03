---
name: "token-anomaly-attribution"
description: "代币异动归因框架分析 — 当代币出现大幅涨跌（单日超过10%）时，逐维度排查涨跌原因，判断行情性质与操作策略。触发词：归因分析、涨跌原因、为什么涨、为什么跌、异动排查、attribution analysis、why is it pumping、why is it dumping、token anomaly、为什么暴涨、为什么暴跌、行情持续性。"
---

## Overview

对出现显著价格异动的加密货币代币，运行 9 步结构化归因框架，从市场 Beta、鲸鱼行为、交易所资金流、衍生品结构、Smart Money、社交情绪、ETF 资金流、技术指标 8 个维度进行量化分析，最终输出持续性评级和操作建议方向。

## Demand Context

源自 @Guolier8 的代币暴涨暴跌结构化归因框架：散户面对价格异动时往往凭情绪跟单，核心问题不是"涨了多少"而是"为什么涨/跌"——找到原因才能判断行情持续性和操作策略。

原作者构建了两层清单式归因框架：对"暴涨"列出 9 大驱动因素（大盘带飞、产品升级、合作推动、品牌重塑、ETF 通过、销毁回购、上所预期、KOL 喊单、上市公司买入），对"暴跌"列出 7 大风险因素（黑客攻击、鲸鱼出走、大盘拖累、交易所下架、产品停滞、丑闻信息、上市公司卖出）。框架核心逻辑：先定性归因，再判断信号持续性——大盘带飞是短期共振，多重基本面共鸣才是持续性行情的依据。

方法论归属：@Guolier8，本 Skill 基于其公开推文框架实现量化验证维度，非量化维度（公告、安全事件等）保留为人工核查清单。

## Features (Data Inputs)

### 必填参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| symbol | string | 代币符号 | HYPE |

### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| direction | enum | auto | 异动方向：pump / dump / auto（自动判断） |
| time_range | string | 7d | 分析时间窗口：24h / 7d / 30d |
| chain | string | auto | 链名称，链上分析时使用，如 hyperliquid / eth |
| token_address | string | — | 合约地址，精确获取链上持仓数据 |
| threshold_pct | float | 10.0 | 价格异动阈值（%），超过此值才执行深度分析 |

## Entry Conditions

满足以下任一条件时触发本 Skill：

1. 用户主动请求归因分析（如 `/token-anomaly-attribution HYPE`）
2. 代币在 time_range 内价格变化超过 threshold_pct
3. 用户询问"为什么涨/跌"、"行情能持续吗"、"该追吗"等问题
4. 用户提供代币符号并提及 pump / dump / 暴涨 / 暴跌等关键词

## Exit Conditions

满足以下条件时 Skill 执行完成：

1. 已完成全部 9 个分析步骤（或因数据不支持而跳过步骤时已注明原因）
2. 已输出归因因素评估表（含信号强度和持续性评级）
3. 已输出综合行情持续性评级（high / medium-high / medium / low）
4. 已输出建议操作方向（chase / hold / wait / exit / verify_first）
5. 已列出需人工核查的非量化因素和后续跟踪观察点

## Action Specification

### Step 1: 价格异动确认与市场背景对比

调用 `ant_spot_market_structure`，参数：
- query_type: `coins_markets`
- symbols: `[symbol, BTC]`

提取目标代币与 BTC 在 time_range 内的价格变化百分比。

计算联动关系：
- 若 |target_chg - BTC_chg| < 5%：归因权重向市场因素倾斜，方向标记为 `market_driven`
- 若 |target_chg - BTC_chg| >= 10%：个币独立行情，深入排查个币因素，标记 `is_idiosyncratic = true`

如果 direction 为 `auto`，根据 target_chg 正负自动判断 pump / dump。

记录：`price_change_pct`、`btc_change_pct`、`market_beta`（两者变化量之比）、`is_idiosyncratic`、`direction`

### Step 2: 链上鲸鱼与大户持仓变化

若提供了 token_address，调用：
- `ant_token_analytics`，query_type: `holders`，参数: token_address, chain
- `ant_token_analytics`，query_type: `flow_intelligence`，参数: token_address, chain

同时调用：
- `ant_fund_flow`，query_type: `centralized_exchange_whale_transfer`，参数: symbol

分析逻辑：
- 鲸鱼集中增持 + 价格上涨 → 筹码集中信号，持续性较强
- 鲸鱼转入交易所 + 价格下跌 → 主动出货，抛压信号
- 若无 token_address，仅使用鲸鱼大额转账数据，并注明数据局限

记录：`whale_action`（accumulate / distribute / neutral）、`whale_exchange_inflow`

### Step 3: 交易所资金净流量分析

调用：
- `ant_fund_flow`，query_type: `exchange_netflow`，参数: asset=symbol
- `ant_fund_flow`，query_type: `exchange_reserve`，参数: asset=symbol

分析逻辑：
- 净流出（代币流出交易所）→ 持有意愿增强，偏多信号
- 净流入（代币流入交易所）→ 潜在抛售压力，偏空信号

记录：`exchange_netflow_7d`、`reserve_change_pct`、`exchange_flow_signal`（bullish / bearish / neutral）

### Step 4: 衍生品结构分析

调用：
- `ant_futures_market_structure`，query_type: `futures_oi_aggregated`，参数: symbol
- `ant_futures_market_structure`，query_type: `futures_funding_rate_history`，参数: symbol

分析组合逻辑：
- 价格↑ + OI↑ + 资金费率正值偏高（>0.05%）→ 多头过热，警惕回调
- 价格↑ + OI↓ + 资金费率转负 → 空头补仓推动，技术性反弹
- 价格↓ + OI↑ + 资金费率大幅负值 → 做空集中，短期反弹空间

记录：`oi_change_pct`、`funding_rate_avg`、`leverage_signal`（overleveraged_long / overleveraged_short / neutral）

### Step 5: Smart Money 行为追踪

调用：
- `ant_smart_money`，query_type: `netflows`，参数: chains（若 chain 为 auto，尝试 eth 和 hyperliquid）
- `ant_smart_money`，query_type: `holdings`，参数: chains
- `ant_smart_money`，query_type: `dex_trades`，参数: chains

分析逻辑：
- Smart Money 净流入 + 持仓增加 → 强看涨信号
- Smart Money 集体减持 → 警示信号，尤其在价格高位

若数据不覆盖目标代币，注明并跳过，标记 `smart_money_direction: unavailable`。

记录：`smart_money_direction`（inflow / outflow / neutral / unavailable）、`smart_money_conviction`（high / medium / low）

### Step 6: 市场情绪与社交热度

调用：
- `ant_market_sentiment`，query_type: `coin_detail`，参数: coin=symbol
- `ant_market_sentiment`，query_type: `topics_list`，参数: topic=symbol

分析逻辑：
- 情绪急剧拉升但价格已高 → 情绪顶部风险，KOL 喊单末段，短期持续性低
- 情绪低迷但链上资金流入 → 低吸机会，情绪尚未发酵，中期持续性较高

记录：`sentiment_score`（0-100）、`sentiment_trend`（rising / falling / stable）、`social_spike`（bool，情绪是否异常飙升）

### Step 7: ETF 资金流分析

仅当 symbol 为 BTC 或 ETH 时执行此步骤，否则跳过并标记 `etf_signal: na`。

调用（BTC）：`ant_etf_fund_flow`，query_type: `btc_etf_flow`
调用（ETH）：`ant_etf_fund_flow`，query_type: `eth_etf_flow`

分析逻辑：ETF 持续净流入 → 机构入场信号；连续净流出 → 机构撤离警告。

记录：`etf_netflow_7d`、`etf_signal`（institutional_inflow / institutional_outflow / na）

### Step 8: 技术指标确认

调用：
- `ant_market_indicators`，query_type: `rsi`，参数: symbol
- `ant_market_indicators`，query_type: `macd`，参数: symbol

分析逻辑：
- RSI > 75：超买区间，追涨风险高，pump 场景下持续性降级
- RSI < 30：超卖区间，恐慌割肉需审慎，dump 场景下或有技术性反弹
- MACD 金叉：趋势转多，支持 pump 归因；死叉：趋势转空

记录：`rsi_14`、`macd_signal`（bullish_cross / bearish_cross / neutral）

### Step 9: 综合归因评估与报告输出

汇总 Step 1-8 全部中间结果，按以下框架打分输出结构化报告。

**涨势归因权重评估：**

| 归因因素 | 可量化信号 | 持续性评级 |
|---------|-----------|----------|
| 大盘带飞 | market_beta 高，is_idiosyncratic=false | 低（随市） |
| 鲸鱼增持 / Smart Money 流入 | Step 2、5 确认 | 高 |
| ETF 机构买入 | Step 7 确认 | 高 |
| 交易所净流出（惜售） | Step 3 确认 | 中高 |
| 资金费率健康（未过热） | Step 4 确认，leverage_signal=neutral | 中 |
| 情绪热度急升（KOL 效应） | Step 6 确认，social_spike=true | 低（短期） |

**跌势归因风险等级：**

| 归因因素 | 可量化信号 | 风险等级 |
|---------|-----------|---------|
| 鲸鱼出走 / Smart Money 撤离 | Step 2、5 确认 | 高 |
| 大盘拖累 | market_beta 高，is_idiosyncratic=false | 中（等 BTC 企稳） |
| 资金费率极负（空头超载） | Step 4 确认，leverage_signal=overleveraged_short | 中（反弹可能） |
| 交易所净流入（抛压） | Step 3 确认 | 中高 |
| 协议安全事件 | 无法量化，需人工确认 | 极高 |
| 交易所下架 | 无法量化，需人工确认 | 高 |

**输出报告，使用以下模板：**

```
## {symbol} 异动归因分析报告

分析时间窗口: {time_range}  |  价格变化: {price_change_pct}%  |  异动方向: {direction}

### 市场背景
- BTC 同期表现: {btc_change_pct}%
- 联动系数 (β): {market_beta} → {is_idiosyncratic ? "个币独立行情，非市场普涨/跌带动" : "与大盘高度联动，市场因素为主"}

### 归因因素评估

| # | 归因因素 | 信号强度 | 数据来源 | 持续性 |
|---|---------|---------|---------|-------|
（逐项列出已确认和待核实的归因因素，✅ = 量化确认，⚠️ = 待核实，❌ = 反向信号）

**量化数据摘要**
| 指标 | 数值 | 含义 |
|------|------|------|
| 鲸鱼行为 | {whale_action} | — |
| 交易所净流量(7d) | {exchange_netflow_7d} | — |
| OI 变化 | {oi_change_pct}% | — |
| 资金费率 | {funding_rate_avg}% | — |
| Smart Money 方向 | {smart_money_direction} | — |
| RSI(14) | {rsi_14} | — |
| 情绪评分 | {sentiment_score}/100 | — |
| ETF 资金流(7d) | {etf_netflow_7d} | — |

**需人工核查的非量化因素**（以下事项数据源不支持自动验证，建议人工确认）:
- 是否有重要合作/集成公告？
- 是否有协议升级/治理提案？
- 是否有交易所上架/下架预期？
- 是否发生安全事件/黑客攻击？
- 是否有上市公司持仓变动？

### 行情持续性评级: {sustainability_rating}
### 建议操作方向: {action_suggestion}
（chase=追入 / hold=持有观察 / wait=等待确认 / exit=减仓 / verify_first=先核实再操作）

### 后续跟踪观察点
（列出 3-5 个具体可追踪的指标或事件节点）

---
免责声明：分析方法论归属 @Guolier8，基于历史数据不构成投资建议。最终操作决策需结合个人风险偏好。
```

**操作建议判断逻辑：**
- pump 场景，量化因素中 >=3 项支持，无重大风险信号 → `chase`（可小仓追入）
- pump 场景，量化因素支持但存在非量化待核实事项 → `verify_first`
- pump 场景，RSI>75 或资金费率过热 → `wait`
- dump 场景，量化因素显示短期超卖（RSI<30, 资金费率极负）→ `hold`（不追跌）
- dump 场景，鲸鱼出走 + Smart Money 撤离 → `exit`

## Risk Parameters

### 数据局限性

- 链上数据存在 1-30 分钟延迟，极端行情时效性有限
- 小市值代币的 Smart Money 和 holders 数据覆盖不完整
- ETF 资金流数据仅覆盖 BTC 和 ETH
- 无 token_address 时，holders 和 flow_intelligence 分析无法执行，降低鲸鱼判断准确度
- 社交情绪可间接推断 KOL 效应，但无法精确识别具体 KOL 喊单行为

### 该 Skill 不做的事

- 不自动获取治理提案、合作公告、上架/下架等非结构化信息
- 不实时检测安全漏洞或黑客攻击
- 不获取上市公司（如 MicroStrategy）实时持仓
- 不预测具体价格走势和回撤幅度
- 不提供自动交易执行能力

### 需要人工判断的环节

- 安全事件确认（协议漏洞/黑客攻击）
- 合作/集成公告真实性核实
- 上所/下架预期的可信度评估
- 最终操作决策（Skill 提供参考方向，不替代人工判断）

## 首次安装提示

```
目标用户：加密货币交易员、投研人员、个人投资者
使用场景：代币出现单日 >10% 大幅涨跌时触发，快速排查涨跌原因，判断是否追单或离场
如何使用：/token-anomaly-attribution HYPE --direction=pump --time_range=7d
```
