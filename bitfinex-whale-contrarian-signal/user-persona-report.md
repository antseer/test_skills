# Bitfinex 巨鲸仓位反指信号 用户画像报告

**日期**: 2026-04-07
**方法**: Skill 功能推导 + 社交数据验证（受限）
**目的**: 指导 skill 优化方向

---

## 数据来源

- Skill 文档分析：`/home/ubuntu/steve/auto-skill-creator/skills_workflow/_data/skills/generated/bitfinex-whale-contrarian-signal/SKILL.md`
- PRD 文档分析：`/home/ubuntu/steve/auto-skill-creator/data/prd/prd_20260407_121311_0bdd35_prd.md`
- ant_market_sentiment 搜索关键词：bitfinex, whale, margin trading, contrarian, open interest
- 各关键词数据量：全部未能执行（MCP 权限未开放）
- 间接数据源：PRD 源推文（@leifuchen）、TradingView 图表代码存在性、CoinGlass 数据面板存在性

---

## Skill 功能摘要

| 维度 | 内容 |
|------|------|
| 核心功能 | 监控 Bitfinex 保证金多头仓位 30 日变化率，当出现极端偏离（>15% 或 <-10%）时触发反向交易信号 |
| 输入/输出 | 输入：币种（默认 BTC）、阈值参数（可选）；输出：信号状态 + 历史胜率统计 + 操作建议 |
| 依赖数据 | 核心：Bitfinex margin long API（外部）；辅助：BTC 价格、资金费率、OI、交易所净流量（Antseer MCP） |
| 知识门槛 | 中高 -- 需理解 margin long position、变化率、反向指标、胜率/回测概念 |
| 操作门槛 | 低 -- 一键运行，参数全有默认值；但输出解读需要一定经验 |
| 使用频率 | 日常巡检（每日 1 次）+ 信号触发深度使用（年均 3-5 次） |
| 决策类型 | 交易决策（辅助确认），不适合作为主策略 |

---

## 用户画像

### 画像 1: "BTC 波段交易员"

**验证状态**: 无法验证（MCP 权限受限，基于文档推导）

| 维度 | 画像 | 验证 |
|------|------|------|
| 身份 | 中高经验 BTC 合约/现货交易员，主做中线波段（数天到数周） | 无法验证 |
| 经验 | 2-5 年加密交易经验，熟悉基本的链上和交易所数据 | 无法验证 |
| 资金量 | $50K - $500K | 无法验证 |
| 核心需求 | 在 BTC 关键转折点获取辅助确认信号，避免追涨杀跌 | 无法验证 |
| 工具习惯 | CoinGlass、TradingView、Bitfinex 官网、Coinalyze | 无法验证 |
| 使用频率 | 每日巡检 1 次，信号触发时深度使用（年均 3-5 次） | 无法验证 |
| 痛点 | Bitfinex margin 数据分散，缺乏自动阈值告警；手动计算变化率耗时；信号频率低导致人工盯盘性价比极低 | 无法验证 |

**数据支撑**: TradingView 存在专用图表代码 BITFINEX:BTCUSDLONGS，CoinGlass 有 Bitfinex margin 数据面板，说明该数据有稳定的交易者关注群体。

---

### 画像 2: "量化策略研究者"

**验证状态**: 无法验证（MCP 权限受限，基于文档推导）

| 维度 | 画像 | 验证 |
|------|------|------|
| 身份 | 量化策略研究者或投研分析师，机构或独立研究者 | 无法验证 |
| 经验 | 5 年以上金融/量化经验，熟悉统计检验和回测方法论 | 无法验证 |
| 资金量 | 管理规模 $1M+（机构或个人量化） | 无法验证 |
| 核心需求 | 验证 Bitfinex margin long 极端变动作为 alpha 因子的有效性 | 无法验证 |
| 工具习惯 | Python/Jupyter、Bitfinex API、CoinGlass API、Dune Analytics | 无法验证 |
| 使用频率 | 策略开发阶段每周多次，上线后低频监控 | 无法验证 |
| 痛点 | 需自行对接 API 和清洗数据；样本量有限统计检验困难；多因子交叉验证数据整合繁琐 | 无法验证 |

**数据支撑**: PRD 源推文本身就是典型量化研究输出（滞后交叉相关、Granger 因果检验、样本内外分割回测），方法论复杂度表明作者和目标受众均为量化导向用户。

---

## 社交数据验证发现

| 关键词 | 帖子量 | 讨论者类型 | 粉丝中位数 | 内容类型 | 关键发现 |
|--------|--------|-----------|-----------|---------|---------|
| bitfinex | N/A | N/A | N/A | N/A | MCP 权限未开放 |
| whale | N/A | N/A | N/A | N/A | MCP 权限未开放 |
| margin trading | N/A | N/A | N/A | N/A | MCP 权限未开放 |
| contrarian | N/A | N/A | N/A | N/A | MCP 权限未开放 |
| open interest | N/A | N/A | N/A | N/A | MCP 权限未开放 |

---

## 竞品分析

| 竞品 | 重叠度 | 差异化 |
|------|--------|--------|
| CoinGlass Bitfinex Margin 面板 | 高 | 仅展示原始数据，不提供极端信号识别和历史胜率回测 |
| TradingView BTCUSDLONGS | 部分 | 需手动计算和编写 Pine Script |
| Whale Alert | 低 | 关注链上转账而非交易所内部 margin 仓位 |
| Coinalyze OI/Funding | 低 | 聚焦期货指标，本 Skill 聚焦现货杠杆 margin 仓位 |

---

## 优化建议

1. **降低外部 API 依赖风险** -- 内置 Bitfinex API 调用 + 本地缓存 + 降级方案
2. **增加预警渐近模式** -- 阈值 70%/80% 时输出预警，与高频 Skill 联动
3. **增加简报模式** -- 一句话结论 + 信号灯，降低入门门槛
4. **探索 ETH 支持** -- v2 版本在完成 ETH 回测验证后扩展
5. **增强交叉验证** -- 自动调用资金费率、交易所净流量等辅助数据

---

## 方法论说明

本报告采用"推导 + 验证"方法。本次分析中 ant_market_sentiment MCP 权限未开放，社交数据验证未能完成，所有画像基于文档分析和间接证据推导，置信度有限。
