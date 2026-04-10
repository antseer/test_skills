# Skill 需求文档: 庄家阶段识别器

## 1. 来源推文
| 字段 | 内容 |
|------|------|
| 推文 URL | https://x.com/agintender/status/2041837904255971403 |
| 作者 | danny @agintender |
| 发布时间 | 2026-04-08 19:17 |
| 核心主题 | 通过 6 个链上信号指标判断 Token 背后庄家所处阶段（吸筹/拉升/出货/已跑） |

## 2. 推文分析方法论提炼

作者提出的核心论点是：每个 Token 背后都有庄家，关键不是"有没有庄"而是"庄在哪个阶段"。围绕这个问题，作者构建了一套 6 维链上信号框架：

**第一层：筹码结构分析（信号 1-2）。** 通过关联钱包合并计算真实筹码集中度（而非简单看 Top 10 Holders），并结合 funding wallet 溯源判断是否多个钱包实为同一实体。同时用"24h 成交量 / Holder 总数"衡量成交量真实度，识别对倒刷量行为。

**第二层：流动性与换手分析（信号 3-5）。** 监控 DEX LP 的增减和锁定状态判断庄家是否在抽流动性准备跑路；用"24h Vol / 市值"并按小时拆分识别集中刷量时段；通过大单占比（Top 10% 交易额占总成交量比例）或基尼系数量化交易额集中度。

**第三层：阶段判断（信号 6）。** 综合前 5 个指标的计算结果，对比"地址/账户增长率"与"价格变化率"的关系，判断庄家所处阶段：吸筹（价格低位横盘 + 大地址缓慢买入 + 钱包数无明显变化）、拉升（价格涨但钱包数增长远低于涨幅）、出货（价格横盘/微跌但钱包数增长 — 庄在高位派发给散户）、已跑（价格跌 + 钱包数不减 — 散户被套）。

> 注：推文后半部分关于做空机制和 youcanshortit.com 的内容属于产品推广，不纳入 Skill 方法论范围。

## 3. Skill 定义
| 字段 | 内容 |
|------|------|
| Skill 名称 | 庄家阶段识别器 |
| 英文 ID | market-maker-stage-detector |
| 适用场景 | 买入前对目标 Token 做庄家控盘分析；定期巡检持仓标的的庄家阶段变化；发现异常放量/拉升时快速诊断 |
| 目标用户 | 链上投研人员、交易员、MEME 币猎手 |
| 触发词 | "庄家分析", "控盘检测", "筹码分析", "有没有庄", "庄在哪个阶段", "market maker detection", "whale control analysis", "chip concentration" |

## 4. 输入参数（通用化）
| 参数名 | 类型 | 必填 | 说明 | 默认值 | 示例值 |
|--------|------|------|------|--------|--------|
| token_address | string | 是 | 代币合约地址 | — | `0x9234e981e395dA3BE7b00B035163571698f8f756` |
| chain | string | 是 | 所在区块链 | — | `bsc` |
| symbol | string | 否 | 代币符号（用于 CeFi 数据查询） | 自动从链上获取 | `WALK` |
| time_range | string | 否 | 分析时间窗口 | `7d` | `24h`, `7d`, `30d` |
| concentration_threshold | number | 否 | 筹码集中度预警阈值（合并后单实体持仓占比） | `10%` | `15%` |
| vol_holder_threshold | number | 否 | Vol/Holder 异常阈值（美元） | `2000` | `2500` |

## 5. 分析流程（Step-by-Step）

### Step 1: 代币基础信息获取
- **描述**: 获取代币当前价格、市值、24h 交易量、Holder 数等基础数据
- **所需数据**: 代币价格、市值、交易量、持有人数
- **MCP 工具**: `ant_meme` — query_type: `token_info`, 参数: chain_id, token_addresses
- **分析逻辑**: 记录基础数据作为后续计算的输入
- **输出**: 基础数据面板（price, mcap, volume_24h, holders_count）

### Step 2: 筹码集中度分析
- **描述**: 获取 Top Holders 列表，识别关联钱包并合并计算真实持仓集中度
- **所需数据**: Top Holders 地址及持仓量、地址间关联关系
- **MCP 工具**:
  - `ant_token_analytics` — query_type: `holders`, 参数: token_address, chain
  - `ant_address_profile` — query_type: `related_wallets`, 参数: address（对 Top 10 地址逐一查询）, chain
  - `ant_address_profile` — query_type: `counterparties`, 参数: address, chain（验证交易对手关系）
- **分析逻辑**:
  1. 获取 Top 50 Holders
  2. 对 Top 10-20 地址查询关联钱包
  3. 将有直接转账关系的地址合并为"同一实体"
  4. 重新计算合并后的持仓占比
  5. 如果任一实体合并后持仓 > concentration_threshold，标记"筹码高度集中"
- **输出**: 实体级持仓分布表、集中度评分

### Step 3: 成交量真实度检测
- **描述**: 计算 Vol/Holder 比率，判断是否存在刷量行为
- **所需数据**: 24h 成交量、Holder 总数
- **MCP 工具**: Step 1 已获取数据，无需额外调用
- **分析逻辑**:
  1. 计算 `vol_per_holder = volume_24h / holders_count`
  2. 如果 vol_per_holder > vol_holder_threshold，标记"疑似刷量"
  3. 参考同类市值代币的 vol_per_holder 中位数做横向对比
- **输出**: Vol/Holder 比率 + 异常标记

### Step 4: 换手率与时段分析
- **描述**: 计算换手率（24h Vol / MCap），并通过 DEX 交易记录分析时段分布
- **所需数据**: 24h 成交量、市值、DEX 交易记录（含时间戳）
- **MCP 工具**:
  - `ant_token_analytics` — query_type: `dex_trades`, 参数: token_address, chain, date_range
- **分析逻辑**:
  1. 计算 `turnover_rate = volume_24h / mcap`
  2. 将 DEX 交易按小时分桶，计算每小时成交量
  3. 计算时段成交量标准差，识别异常尖峰时段
  4. 计算净买入量（buy_volume - sell_volume）
  5. 如果某几小时成交量 > 均值的 3 倍，标记"集中刷量时段"
- **输出**: 换手率、时段分布图、异常时段标记、净买入量

### Step 5: 大单占比分析
- **描述**: 分析交易金额分布，计算大单集中度
- **所需数据**: DEX 交易记录（含金额）
- **MCP 工具**: Step 4 已获取 dex_trades 数据
- **分析逻辑**:
  1. 将所有交易按金额排序
  2. 计算 Top 10% 交易占总成交量的比例
  3. 计算基尼系数（Gini coefficient）量化交易额集中度
  4. 如果 Top 10% 占比 > 60%，标记"少数地址驱动"
- **输出**: 大单占比百分比、基尼系数、驱动地址列表

### Step 6: 资金流向情报
- **描述**: 获取 Smart Money 和大户对该代币的操作方向
- **所需数据**: Smart Money 买卖信号、资金流向
- **MCP 工具**:
  - `ant_token_analytics` — query_type: `flow_intelligence`, 参数: token_address, chain
  - `ant_token_analytics` — query_type: `who_bought_sold`, 参数: token_address, chain, buy_or_sell="BUY"
  - `ant_token_analytics` — query_type: `who_bought_sold`, 参数: token_address, chain, buy_or_sell="SELL"
- **分析逻辑**:
  1. 统计 Smart Money / 大户 / 交易所的净买卖方向
  2. 对比大户买入 vs 卖出的地址数和金额
  3. 识别"聪明钱在买散户在卖"或"聪明钱在卖散户在买"的信号
- **输出**: 资金流向摘要、Smart Money 操作方向

### Step 7: 庄家阶段综合判断
- **描述**: 综合 Step 2-6 的所有中间结果，判断庄家当前所处阶段
- **所需数据**: 前 6 步的所有中间结果
- **MCP 工具**: 无需额外调用，纯逻辑判断
- **分析逻辑**:

  **吸筹阶段信号:**
  - 价格低位横盘或微跌
  - 筹码集中度在缓慢提升（合并后大户持仓增加）
  - Holder 数变化不大
  - Smart Money 有小额买入信号
  - 成交量不高，换手率偏低

  **拉升阶段信号:**
  - 价格显著上涨（如 >30%）
  - Holder 增长率远低于价格涨幅（如价格涨 30% 但 Holder 只涨 5%）
  - 大单占比高（少数地址驱动）
  - 成交量集中在特定时段

  **出货阶段信号（最危险）:**
  - 价格横盘或微跌
  - Holder 数明显增长（>15-20%）— 筹码在从大户流向散户
  - 大户持仓占比在下降
  - Smart Money 出现卖出信号
  - 换手率升高但价格不涨

  **已跑阶段信号:**
  - 价格持续下跌
  - Holder 数不减少甚至增加（散户被套不割肉）
  - 大户持仓占比显著降低
  - 成交量萎缩

- **判断标准**: 匹配信号数量最多的阶段作为判断结果，给出置信度
- **输出**: 庄家阶段判断 + 置信度 + 关键依据

## 6. Antseer MCP 数据映射
| 数据需求 | MCP 工具 | query_type | 推荐参数 | 覆盖度 |
|----------|----------|------------|----------|--------|
| 代币价格/市值/交易量 | ant_meme | token_info | chain_id, token_addresses | ✅ |
| Top Holders 列表 | ant_token_analytics | holders | token_address, chain | ✅ |
| 关联钱包识别 | ant_address_profile | related_wallets | address, chain | ⚠️ |
| 地址间交易对手 | ant_address_profile | counterparties | address, chain | ✅ |
| DEX 交易记录 | ant_token_analytics | dex_trades | token_address, chain | ✅ |
| 资金流向情报 | ant_token_analytics | flow_intelligence | token_address, chain | ✅ |
| 谁在买/谁在卖 | ant_token_analytics | who_bought_sold | token_address, chain, buy_or_sell | ✅ |
| Funding wallet 溯源 | — | — | — | ❌ |
| LP 锁定状态检测 | — | — | — | ❌ |
| LP 深度变化监控 | ant_protocol_tvl_yields_revenue | protocol_tvl | protocol | ⚠️ |
| 地址标签（识别交易所/机器人） | ant_address_profile | labels | address, chain | ✅ |
| Smart Money 操作 | ant_token_analytics | flow_intelligence | token_address, chain | ✅ |

**覆盖度统计**: ✅ 8 项 / ⚠️ 2 项 / ❌ 2 项

**未覆盖项说明**:
- ⚠️ **关联钱包识别**: `related_wallets` 能提供部分关联信息，但精度不如专业工具（如 Bubblemaps 的气泡图）。建议: 用 `counterparties` 交叉验证转账关系，组合使用可达到较好效果。
- ⚠️ **LP 深度变化**: Antseer 没有直接的 LP 深度监控工具。`protocol_tvl` 可提供协议级别的 TVL 变化，但无法精确到单个交易对的 LP 深度。建议: 通过 `dex_trades` 的交易滑点间接推断流动性变化。
- ❌ **Funding wallet 溯源**: 追溯多个钱包的初始 gas 费来源需要多层链上交易回溯，Antseer 目前不支持。建议替代方案: Arkham Intelligence、Nansen、或手动通过区块浏览器追溯。
- ❌ **LP 锁定状态**: 需要查询合约的 LP token 锁定情况（如 Unicrypt、PinkSale 等锁仓合约），Antseer 无此功能。建议替代方案: DEXScreener、GeckoTerminal 的 LP 锁定标记，或直接查询锁仓合约。

## 7. 输出结构

**输出形式**: 结构化报告 + 阶段判断仪表盘

**关键输出字段**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| token_info | object | 代币基础信息（价格、市值、交易量、Holder 数） |
| chip_concentration | object | 筹码集中度分析（合并后实体持仓分布、集中度评分） |
| volume_authenticity | object | 成交量真实度（Vol/Holder 比率、异常标记） |
| turnover_analysis | object | 换手分析（换手率、时段分布、异常时段） |
| large_order_ratio | object | 大单占比（Top 10% 占比、基尼系数） |
| fund_flow | object | 资金流向（Smart Money 方向、大户买卖统计） |
| stage_verdict | object | 阶段判断（阶段名称、置信度、关键依据列表） |
| risk_signals | array | 风险信号列表（每个信号含 level、description） |
| recommendation | string | 操作建议（"当前阶段对散户友好/不友好，建议..."） |

**输出示例（基于推文原始案例）**:

```
=== 庄家阶段识别报告 ===

代币: WALK | 链: BSC | 市值: $1.6M
CA: 0x9234e981e395dA3BE7b00B035163571698f8f756

--- 筹码结构 ---
  LP 占比: 57% (PancakeSwap V3) + 3% (V2)
  Vault 占比: 40% (youcanshortit.com 借空池)
  Dev 持仓: 0%
  集中度评分: 高（60% 流动性由单一协议控制）

--- 成交量真实度 ---
  Vol/Holder: $XXX（待实际数据填充）
  判定: 待分析

--- 换手分析 ---
  24h 换手率: XX%
  异常时段: 无/有（XX:00-XX:00 成交量异常）

--- 大单占比 ---
  Top 10% 交易占比: XX%
  基尼系数: 0.XX

--- 资金流向 ---
  Smart Money: 净买入/净卖出
  大户动向: ...

--- 阶段判断 ---
  当前阶段: [吸筹/拉升/出货/已跑]
  置信度: XX%
  关键依据:
    1. ...
    2. ...
    3. ...

--- 风险信号 ---
  [HIGH] 40% 代币在单一借空池中，存在集中抛售风险
  [MED]  LP 未锁定状态未知（需外部验证）

--- 建议 ---
  当前阶段对散户 [友好/不友好]。
  建议: ...
```

## 8. 边界与约束

**该 Skill 能做什么:**
- 快速量化 Token 的筹码集中度、成交量真实度、换手合理性等关键指标
- 通过多维信号交叉验证判断庄家所处阶段
- 识别刷量、对倒、集中控盘等异常行为
- 提供 Smart Money / 大户的操作方向作为辅助判断

**该 Skill 不能做什么:**
- 无法保证 100% 准确识别所有庄家钱包（庄家可通过复杂拆分规避）
- 无法追溯 funding wallet 来源（需外部工具辅助）
- 无法检测 LP 锁定状态（需外部数据源）
- 不提供交易信号或买卖建议 — 仅提供阶段判断和风险信号
- 不适用于 CEX 上市的大盘币（BTC/ETH 等），主要针对链上 DEX 交易的中小市值代币

**数据局限性:**
- 关联钱包识别依赖 `related_wallets` 和 `counterparties` 的覆盖精度，可能存在漏报
- DEX 交易数据可能有延迟，实时性取决于 MCP 数据源更新频率
- 基尼系数和大单占比的计算基于采样的 DEX 交易记录，非全量数据
- 不同链的数据覆盖度不同，EVM 链覆盖较好，其他链可能有缺失

**需要人工判断的环节:**
- 关联钱包合并后的"实体"划分 — 自动合并可能出错，建议人工复核高持仓实体
- 阶段判断的最终确认 — 多维信号可能出现矛盾信号，需人工权衡
- LP 锁定状态 — 需人工通过 DEXScreener 或区块浏览器验证
- 推文提到的"庄家阶段"是简化模型，真实市场远比四阶段复杂

**免责声明:**
本需求文档基于 @agintender 推文内容自动生成，分析方法论归属原作者。
生成的 Skill 为 v1 草稿，建议 review 后再用于生产环境。
不构成投资建议。
