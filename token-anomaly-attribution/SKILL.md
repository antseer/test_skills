---
name: "token-anomaly-attribution"
description: "代币异动归因分析 — 当代币出现暴涨暴跌（默认阈值 15%/24h）时，系统拆解价格异动根因，判断信号质量与行情持续性，给出追入/等待/规避建议。触发词：归因分析、涨跌原因、为什么涨、为什么跌、帮我分析异动、行情持续性、token anomaly analysis、price surge attribution、price crash attribution、为什么暴涨、为什么暴跌。"
---

## Overview

对出现显著价格异动的加密货币代币，执行 8 步结构化归因框架，从大盘 Beta、鲸鱼行为、Smart Money、社交情绪、ETF 资金流、衍生品结构 6 个量化维度进行分析，最终输出信号质量评级（A/B/C）和操作建议。

## Demand Context

源自 @Guolier8 的代币暴涨暴跌归因框架（https://x.com/Guolier8/status/2039996241762001198）：散户面对价格异动时往往凭情绪跟单，核心问题不是"涨了多少"而是"为什么涨/跌"——找到原因才能判断行情持续性和操作策略。

原作者构建了两层清单式归因框架：

**暴涨 9 类驱动**: 大盘带飞、产品技术升级、合作推动、品牌重塑、ETF 通过、销毁回购、预期上所、影响人喊单、上市公司购买。

**暴跌 7 类风险**: 黑客攻击、鲸鱼出走、大盘拖累、交易所下架、产品停滞、丑闻信息、上市公司卖出。

框架核心逻辑：先剔除大盘 Beta 影响，再从产品、生态、资本、合规、链上行为等维度逐一排查 alpha 因素，判断是否存在"多重利好叠加"的持续性信号。多因子叠加（信号质量 A）使涨势更具持续性；单一短期事件驱动（信号质量 C）回撤风险高。

方法论归属：@Guolier8，本 Skill 基于其公开推文框架实现量化验证维度，非量化维度（合作公告、安全事件等）保留为人工核查清单。

## Features (Data Inputs)

### 必填参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| symbol | string | 代币符号 | HYPE |

### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| chain | string | auto | 所在链（链上分析用）：hyperliquid / ethereum / solana |
| token_address | string | — | 合约地址（精确链上分析用），填写后可获取 Holders 和 Flow Intelligence 数据 |
| time_range | string | 24h | 分析时间窗口：24h / 7d / 30d |
| price_change_threshold | float | 15 | 异动判定阈值（%），绝对值超过此值才触发深度归因分析 |
| analysis_mode | string | auto | surge（仅分析上涨因素）/ dump（仅分析下跌因素）/ auto（根据实际方向自动判断） |

## Entry Conditions

满足以下任一条件时触发本 Skill：

1. 用户主动请求归因分析（如 `/token-anomaly-attribution HYPE`）
2. 代币在 time_range 内价格变化绝对值超过 price_change_threshold
3. 用户询问"为什么涨/跌"、"行情能持续吗"、"该追吗"、"帮我分析异动"等问题
4. 用户提供代币符号并提及 pump / dump / 暴涨 / 暴跌 / 异动等关键词

## Exit Conditions

满足以下条件时 Skill 执行完成：

1. 已完成全部 8 个分析步骤（数据不支持的步骤已注明原因并跳过）
2. 已输出归因因素评估表（含量化确认项和待核实项）
3. 已输出信号质量评级（A / B / C / Uncertain）
4. 已输出行动建议（追入 / 持仓等待 / 规避风险 / 数据不足无法判断）
5. 已列出后续跟踪指标（3-5 项）

## Action Specification

### Step 1: 价格异动确认

调用 `ant_spot_market_structure`，参数：
- query_type: `coins_markets`
- symbols: `[symbol]`

计算在 time_range 内的涨跌幅 = (当前价 - 时间窗口起始价) / 时间窗口起始价 × 100%。

若绝对值 < price_change_threshold，输出提示"异动幅度未达阈值"并询问用户是否继续分析；若达到阈值，触发后续步骤。

若 analysis_mode 为 `auto`，根据涨跌幅正负自动判断 surge / dump。

记录：`price_change_pct`、`direction`（surge / dump）、`threshold_triggered`（bool）

---

### Step 2: 大盘 Beta 剔除

调用 `ant_spot_market_structure`，参数：
- query_type: `coins_markets`
- ids: `["bitcoin", "ethereum"]`

提取 BTC 和 ETH 在同一时间窗口的涨跌幅，计算大盘 Beta 贡献率。

判断逻辑：
- 若 BTC 同期涨跌幅 > 80% × 代币涨跌幅：大盘带飞/拖累是主因，标注"大盘 Beta 驱动"
- 若代币涨跌幅显著超出大盘（超出 10 个百分点以上）：存在个币 alpha/风险，is_idiosyncratic = true

记录：`btc_change_pct`、`eth_change_pct`、`beta_attribution_pct`（估算大盘贡献率 %）、`is_idiosyncratic`（bool）

---

### Step 3: 链上鲸鱼行为检测

若提供了 token_address，调用（3a）和（3b）：

**(3a)** `ant_token_analytics`，query_type: `holders`，参数: token_address, chain
- 提取 Top 10 Holders 持仓集中度在时间窗口内的变化

**(3b)** `ant_token_analytics`，query_type: `flow_intelligence`，参数: token_address, chain
- 检测链上大额资金流向

**(3c)** `ant_fund_flow`，query_type: `exchange_netflow`，参数: asset=symbol
- 代币从链上流入/流出中心化交易所的净额（正=流入交易所=抛压，负=流出交易所=积累）

**(3d)** `ant_fund_flow`，query_type: `centralized_exchange_whale_transfer`，参数: symbol
- 大额鲸鱼转账记录（转入交易所 = 抛售预警）

分析逻辑：
- 前 10 Holders 持仓集中度显著增加 + 交易所净流出 → 鲸鱼积累，正向信号
- 大额转入交易所 + 持仓集中度减少 → 鲸鱼出走，抛售信号

若无 token_address，仅基于 (3c) 和 (3d) 进行判断，并注明数据局限。

记录：`whale_action`（accumulate / distribute / neutral）、`exchange_netflow`（正负值）

---

### Step 4: Smart Money 动向

调用：
- `ant_smart_money`，query_type: `netflows`，参数: chains（若 chain 为 auto，尝试 eth 和 hyperliquid）
- `ant_smart_money`，query_type: `holdings`，参数: chains

分析逻辑：
- Smart Money 净流入 + 持仓增加 → 强看涨信号
- Smart Money 净流出 + 持仓减少 → 警示信号，尤其在价格高位

若数据不覆盖目标代币，注明并跳过，标记 `smart_money_direction: unavailable`。

记录：`smart_money_direction`（Bullish / Neutral / Bearish / unavailable）、`smart_money_netflow_scale`（大 / 中 / 小）

---

### Step 5: 社交情绪与叙事检测

调用：
- `ant_market_sentiment`，query_type: `coin_detail`，参数: coin=symbol
- `ant_market_sentiment`，query_type: `topic_detail`，参数: topic=symbol

分析逻辑：
- 社交热度在时间窗口内急速拉升（>3 倍历史均值）→ 可能存在 KOL 喊单/叙事驱动
- 社交热度先于价格上涨：叙事驱动（持续性取决于基本面跟进）
- 社交热度滞后于价格上涨：情绪末段效应，短期风险高

记录：`sentiment_score`（0-100）、`social_spike`（bool，是否异常飙升）、`sentiment_driver_rating`（高 / 中 / 低）

---

### Step 6: ETF 与机构资金流检测

仅当 symbol 为 BTC 或 ETH 时执行此步骤，否则跳过并标记 `etf_signal: 不适用`。

调用（BTC）：`ant_etf_fund_flow`，query_type: `btc_etf_flow`
调用（ETH）：`ant_etf_fund_flow`，query_type: `eth_etf_flow`

分析逻辑：
- ETF 净流入显著增加且同步代币涨幅 → 机构资金驱动，持续性强
- ETF 净流出 → 增加下行风险

记录：`etf_netflow`、`etf_signal`（正向 / 中性 / 负向 / 不适用）

---

### Step 7: 衍生品市场杠杆检测

调用：

**(7a)** `ant_futures_market_structure`，query_type: `futures_oi_aggregated`，参数: symbol
**(7b)** `ant_futures_market_structure`，query_type: `futures_funding_rate_current`，参数: symbol
**(7c)** `ant_futures_market_structure`，query_type: `futures_long_short_ratio`，参数: symbol

分析逻辑：
- OI 大增 + 资金费率极端（>0.1% 或 <-0.05%）→ 杠杆过热，注意回调风险
- 价格↑ + OI↑ + 资金费率正值适中（0.01%-0.05%）→ 健康上涨结构
- 资金费率与价格走势背离 → 潜在反转信号

记录：`oi_change_pct`、`funding_rate_current`（%）、`long_short_ratio`、`leverage_risk`（High / Medium / Low）

---

### Step 8: 综合归因评估与报告输出

汇总 Step 1-7 全部量化结果，结合需人工核实的事件性因素，输出结构化归因报告。

**信号质量评级标准：**

| 评级 | 条件 | 含义 |
|------|------|------|
| A（多因子叠加） | ≥3 个正向驱动因素同时生效 | 涨势/跌势持续性较高 |
| B（单因子驱动） | 1-2 个明确驱动因素 | 持续性待观察，需跟踪后续指标 |
| C（情绪/噪音） | 主要由社交热度或 KOL 喊单驱动，缺乏链上基本面支撑 | 短期，高回调风险 |
| Uncertain（不确定） | 关键数据缺失，无法可靠判断 | 建议等待更多数据 |

**量化因素清单（逐项评估）：**

| # | 因素 | 量化工具 | 信号方向 |
|---|------|---------|---------|
| 1 | 大盘 Beta 贡献率 | ant_spot_market_structure | 高 Beta = 市场因素；低 Beta = 个币 alpha |
| 2 | 鲸鱼行为 | ant_token_analytics + ant_fund_flow | 积累=正 / 出走=负 |
| 3 | 交易所净流向 | ant_fund_flow | 净流出=正 / 净流入=负 |
| 4 | Smart Money | ant_smart_money | Bullish=正 / Bearish=负 |
| 5 | 社交情绪热度 | ant_market_sentiment | 适度热=辅助 / 急速拉升=风险 |
| 6 | ETF 资金流 | ant_etf_fund_flow | 净流入=正（仅BTC/ETH） |
| 7 | 杠杆结构 | ant_futures_market_structure | 健康=正 / 过热=风险 |

**需人工核实的非量化因素（以下事项 MCP 数据源不支持自动验证）：**
- 产品/技术升级（主网/测试网上线、重大提案）— 建议核查官方 GitHub/Discord
- 机构合作/平台接入公告 — 建议核查官方 PR/新闻稿
- 预期上所信息 — 建议确认官方消息来源，非二手信息
- 黑客攻击/安全漏洞 — 建议查阅 Rekt.news、Immunefi
- 上市公司持仓变动 — 建议查阅 SEC 文件、官方公告
- 品牌重塑/叙事焕新 — 结合社交话题量变化和新闻人工判断

**输出报告，使用以下模板：**

```
## {symbol} 代币异动归因分析报告

**分析时间**: {date}  **时间窗口**: {time_range}  **分析模式**: {analysis_mode}

### 价格背景
- {symbol} {time_range} 涨跌幅: {price_change_pct}%
- BTC 同期涨跌幅: {btc_change_pct}%
- 大盘 Beta 贡献率: ~{beta_attribution_pct}%  {is_idiosyncratic ? "✦ 存在明显个币 Alpha" : "→ 主要为大盘联动"}

### 已量化确认的驱动因素

| 因素类别 | 信号来源 | 具体表现 | 评级 |
|----------|----------|----------|------|
（逐行列出，每行对应一个量化维度，✅ = 正向确认，⚠️ = 需核实，❌ = 反向信号）

**量化数据摘要**
| 指标 | 数值 | 信号含义 |
|------|------|---------|
| 鲸鱼行为 | {whale_action} | — |
| 交易所净流量 | {exchange_netflow} | — |
| OI 变化 | {oi_change_pct}% | — |
| 当前资金费率 | {funding_rate_current}% | — |
| 多空比 | {long_short_ratio} | — |
| Smart Money 方向 | {smart_money_direction} | — |
| 情绪评分 | {sentiment_score}/100 | — |
| ETF 资金流 | {etf_netflow} | — |

### 需人工核实的驱动因素（以下事项需自行核查）
（列出本次分析中识别出的待核实项目，含核查建议来源）

### 综合信号质量: {A / B / C / Uncertain}
{signal_quality_explanation}

### 行动建议: {追入 / 持仓等待 / 规避风险 / 数据不足无法判断}
{action_rationale}

### 后续跟踪指标
（列出 3-5 个具体可追踪的指标或事件节点）

---
数据截止: {data_freshness}
免责声明：分析方法论归属 @Guolier8，基于历史数据不构成投资建议。最终操作决策需结合个人风险偏好自行判断。
```

**行动建议判断逻辑（surge 方向）：**
- 量化因素中 ≥3 项正向，无重大风险信号 → 追入（小仓试探）
- 量化因素支持但存在待核实非量化事项 → 持仓等待（等核实再决策）
- RSI > 75 或资金费率过热（>0.1%）→ 规避风险（追高风险大）
- 信号质量 A 且核实后基本面实锤 → 追入

**行动建议判断逻辑（dump 方向）：**
- 鲸鱼出走 + Smart Money 撤离 → 规避风险（减仓或离场）
- 资金费率极负（<-0.05%）+ OI 上升 → 持仓等待（空头过载，可能反弹）
- 大盘拖累（Beta 驱动为主）→ 持仓等待（等 BTC 企稳）

## Risk Parameters

### 数据局限性

- 链上数据通常存在 1-30 分钟延迟，极端行情时效性有限
- 社交情绪数据通常存在 1-4 小时滞后
- Smart Money 标签动态变化，存在标注偏差
- 无 token_address 时，holders 和 flow_intelligence 分析无法执行，降低鲸鱼判断准确度
- 链上数据覆盖主流链（Ethereum、BSC、Solana 等），部分新兴链覆盖有限
- ETF 数据仅覆盖 BTC 和 ETH

### 该 Skill 不做的事

- 不自动获取治理提案、合作公告、上架/下架等非结构化信息
- 不实时检测安全漏洞或黑客攻击（需接入 Rekt.news 等外部源）
- 不获取上市公司（如 MicroStrategy）实时持仓变动
- 不预测具体价格走势和回撤幅度
- 不提供自动交易执行能力

### 需要人工判断的环节

- 安全事件确认（协议漏洞/黑客攻击）
- 合作/集成公告真实性核实
- 上所/下架预期可信度评估
- KOL 身份可信度与其持仓情况
- 最终操作决策（Skill 提供参考方向，不替代人工判断）

## 首次安装提示

```
目标用户：加密货币交易员、投研人员、量化策略研究者
使用场景：代币短时间内涨跌幅超过阈值（默认 15%/24h）时，快速拆解驱动因素、判断信号质量与可持续性
如何使用：/token-anomaly-attribution HYPE --time_range=24h --price_change_threshold=15
```
