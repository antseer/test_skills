# token-resilience-weekly 用户画像报告

**日期**: 2026-04-03
**方法**: Skill 功能推导（社交数据验证不可用）
**目的**: 指导 skill 优化方向

---

## 数据来源

- Skill 文档分析: `/home/ubuntu/steve/auto-skill-creator/skills_workflow/_data/skills/generated/token-resilience-weekly/SKILL.md`
- PRD 文档: `/home/ubuntu/steve/auto-skill-creator/data/prd/prd_20260403_083544_76ba21_prd.md`
- ant_market_sentiment 搜索: **不可用**（MCP 工具未在当前环境中加载）
- 计划搜索关键词: token resilience, relative strength crypto, altcoin outperformance, market correction crypto, alpha generation

---

## Skill 功能摘要

| 维度 | 内容 |
|------|------|
| 核心功能 | 以 ETH/SOL 为基准，对 watchlist 中代币进行周度韧性分级（T1/T2/弱势/中性），输出结构化周报 |
| 输入/输出 | 输入：代币 watchlist + 可选基准/阈值参数；输出：含分级表、逐日涨跌幅矩阵、行为标注的结构化报告 |
| MCP 工具依赖 | `ant_spot_market_structure`（coins_markets with sparkline, simple_price） |
| 知识门槛 | 中高 — 需理解相对强度概念、基准比较逻辑、T1/T2 分级含义、日均涨跌幅计算 |
| 操作门槛 | 中等 — 需手动维护 watchlist，可选参数较多但有合理默认值 |
| 使用频率 | 中频：每周 1 次定期 + 大盘急跌时事件驱动 |
| 决策类型 | 仓位配置决策 / 投研报告生产 |

---

## 用户画像

### 画像 1: "组合交易员"

**验证状态**: 部分验证（基于 PRD 来源推文推导，无社交数据验证）

| 维度 | 画像 | 验证 |
|------|------|------|
| 身份 | 中长线加密货币交易员，持有 5-20 个代币的组合仓位 | 部分验证 — PRD 来源推文面向此类用户 |
| 经验 | 有经验（intermediate），熟悉基本市场概念但不一定会写代码 | 无法验证 |
| 资金量 | $10K - $500K | 无法验证 |
| 核心需求 | 在大盘承压时快速识别哪些持仓最抗跌、哪些拖后腿，为仓位调整提供数据支撑 | 部分验证 — 推文分析框架直接对应此需求 |
| 工具习惯 | CoinGecko、TradingView、CoinGlass、Excel/Google Sheets | 无法验证 |
| 使用频率 | 每周 1 次 + 大盘急跌时额外触发 | 部分验证 — PRD 明确定义此触发场景 |
| 痛点 | 手动逐币比较耗时、缺乏系统化分级框架、数据采集重复劳动 | 部分验证 — 推文展示的手动分析流程证实了自动化需求 |

**数据支撑**: PRD 来源推文（@Guolier8）展示了完整的手动分析流程：逐币拉取 CoinGecko 收盘价、计算周均日涨跌幅、与 ETH/SOL 比较、手动分级。这一流程的存在本身证实了自动化的需求。推文的分级输出格式（T1/T2/弱势）直接面向持仓管理决策。

---

### 画像 2: "投研分析师"

**验证状态**: 部分验证

| 维度 | 画像 | 验证 |
|------|------|------|
| 身份 | 投研人员或基金分析师，负责定期出具市场分析报告 | 部分验证 — PRD 明确将投研人员列为目标用户 |
| 经验 | 专业（advanced），熟悉量化分析方法和编程工具 | 无法验证 |
| 资金量 | 管理或服务 $1M+ 资金 | 无法验证 |
| 核心需求 | 快速生成带量化指标的代币强弱对比报告，减少数据处理时间 | 部分验证 — skill 输出格式高度契合研报需求 |
| 工具习惯 | Dune Analytics、CoinGecko API、Python/Jupyter、Notion | 无法验证 |
| 使用频率 | 每周 1 次固定产出 | 部分验证 — 周报产出节奏与 skill 设计匹配 |
| 痛点 | 每周 2-4 小时手动数据处理、逐日行为标注工作量大、报告格式重复难以模板化 | 部分验证 — skill 的逐日矩阵和自动标注功能直接解决此痛点 |

**数据支撑**: Skill 输出包含完整的结构化周报模板（基准行情 + 分级表 + 逐日矩阵 + 总结叙述），这是典型的投研报告章节格式。PRD 中的输出示例直接可作为研报素材使用。

---

## 社交数据验证发现

| 关键词 | 帖子量 | 讨论者类型 | 粉丝中位数 | 内容类型 | 关键发现 |
|--------|--------|-----------|-----------|---------|---------|
| token resilience | N/A | N/A | N/A | N/A | ant_market_sentiment 不可用 |
| relative strength crypto | N/A | N/A | N/A | N/A | ant_market_sentiment 不可用 |
| altcoin outperformance | N/A | N/A | N/A | N/A | ant_market_sentiment 不可用 |
| market correction crypto | N/A | N/A | N/A | N/A | ant_market_sentiment 不可用 |
| alpha generation | N/A | N/A | N/A | N/A | ant_market_sentiment 不可用 |

**社交验证总结**: 由于 ant_market_sentiment MCP 工具在当前环境中不可用，所有社交数据验证步骤均未能执行。画像完全基于 skill 文档和 PRD 推导。以下信号值得注意：

1. PRD 来源推文（@Guolier8）本身作为社交信号，证明该分析方法论在中文 crypto 社区有自然讨论
2. 相对强度分析是传统金融的成熟方法论（如 Relative Strength Index, Mansfield RS），迁移到 crypto 领域的需求逻辑成立
3. 建议在 ant_market_sentiment 可用时补充验证，重点关注 "token resilience" 和 "relative strength crypto" 的讨论热度

---

## 关键场景

### 场景 1: 每周定期韧性复盘
- **触发**: 每周日或周一，对持仓或关注列表运行韧性分析
- **频率**: 每周 1 次
- **价值**: 系统化替代手动逐币比较，节省 1-3 小时/周

### 场景 2: 大盘急跌后快速评估
- **触发**: BTC/ETH 周内跌幅超过 5%
- **频率**: 每月 1-3 次
- **价值**: 在市场恐慌时提供数据化的冷静判断

### 场景 3: 板块轮动分析
- **触发**: 将同一赛道代币作为 watchlist 进行板块内对比
- **频率**: 每周或事件驱动
- **价值**: 识别板块内领头羊和落后者

### 场景 4: 投研周报生产
- **触发**: 研究员需要在周报中加入代币强弱对比章节
- **频率**: 每周 1 次
- **价值**: 自动生成结构化数据，研究员聚焦归因分析

---

## 市场规模估算

| 层级 | 估算 | 说明 |
|------|------|------|
| TAM | ~200 万 | 活跃的加密货币中长线交易者和投研人员 |
| SAM | ~20 万 | 使用量化工具或定期产出分析报告的用户 |
| SOM | ~2-5 万 | 已使用 Claude Code 或类似 AI 工具的分析用户 |
| 置信度 | **中等** | 需求逻辑成立但缺少社交数据验证 |

---

## 竞争格局

| 竞品 | 重叠度 | 差异化 |
|------|--------|--------|
| CoinGecko Portfolio | 基础持仓追踪 | 本 Skill 提供相对于基准的韧性分级，非绝对涨跌幅 |
| TradingView RS 指标 | 技术分析相对强度 | 本 Skill 聚焦周度组合级别，非单币 K 线指标 |
| 手动 Excel 分析 | 完全相同逻辑 | 全流程自动化，2-4 小时缩短至分钟级 |
| Messari/TokenTerminal 周报 | 专业市场报告 | 本 Skill 支持自定义 watchlist 和阈值 |

---

## 优化建议

1. **增加板块预设 watchlist** — watchlist 维护是纯手动环节，增加 AI/DePIN/L2/Meme 等板块预设可降低使用门槛，让不确定追踪什么的用户快速上手。

2. **增加简报模式** — 当前输出需要用户理解 T1/T2 分级，增加一句话结论模式（如"本周 TAO 最强、STORY 最弱"），将 skill 从分析工具升级为决策助手，覆盖更多中级交易者。

3. **增加跨周韧性趋势追踪** — 当前为单次快照，增加"连续 N 周 T1"等趋势标签可提供纵向价值，从周度报告升级为趋势追踪工具，提升用户粘性。

4. **增加数据置信度指标** — sparkline 近似值可能影响专业用户信任度，在报告中标注数据精度和受影响指标，增强研究员和基金分析师的信任度。

5. **结合社交数据提供韧性归因** — 原推文作者会附加归因分析（如"AI叙事驱动"），结合 ant_market_sentiment 为 T1 代币自动附加可能的驱动因素，将 skill 从数据计算工具升级为洞察生成工具。

---

## 方法论说明

本报告采用"推导"方法：从 skill 文档和 PRD 推导目标用户假设。
由于 ant_market_sentiment MCP 工具在当前环境中不可用，社交数据验证步骤未能执行。
画像的验证状态标注为"部分验证"，置信度为中等。
建议在 ant_market_sentiment 可用时补充社交验证，重点验证：
- "token resilience" 和 "relative strength crypto" 的讨论热度
- 讨论者类型是否以交易员和研究员为主
- 是否存在未预见的用户群体
