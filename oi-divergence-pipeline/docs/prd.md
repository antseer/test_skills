# PRD: OI 背离自动狙击管线 (oi-divergence-pipeline)

**版本**: v1.0
**作者**: Alex (Product Manager Agent)
**日期**: 2026-04-04
**状态**: Draft

---

## 1. 问题陈述

### 当前痛点

现有 `oi-divergence` skill 是一个**单币手动查询工具**：用户输入一个币种符号，skill 分析该币种的 1H 价格/OI 背离信号。这个设计有三个根本性限制：

1. **目标选择靠猜**：用户必须先"感觉"某个币有问题，再手动输入查询。但真正有价值的信号往往出现在用户根本没关注的币种上——那些突然暴涨的小币。用户不知道该查谁，也不可能手动遍历几百个合约交易对。

2. **缺乏控盘验证**：OI 背离本身有较高假阳性——自然平仓、套利调仓、对冲调整都会导致价格涨+OI降。@wuk_Bitcoin 崩盘模型的核心前提是"主力控盘"，但当前 skill 完全不验证这一前提。用户已经有 `whale-control` skill 能做控盘检测，但两个 skill 是割裂的。

3. **信号没有优先级**：即使用户手动跑了 10 个币的 OI 背离，也没有统一的排名机制告诉他"先做空哪个"。

### 用户证据

来自 `oi-divergence` 的用户画像报告（`docs/user-persona-report.md`）：

- **优化建议 #5**（原文）："支持多币种批量扫描...增加 ALL 或 TOP10 参数，一次扫描主流币种的 OI 背离状态，输出一张汇总表...从单币工具升级为市场扫描器"
- open interest 话题帖子覆盖 BTC(28条)、ETH(32条)及大量山寨币，用户需要跨币种监控
- "OI 下降+价格上涨=警告信号"在社交讨论中有 58 条验证帖
- 用户痛点已验证："手动翻看 OI 图表+价格图表，肉眼判断背离费时且主观"

### 用户需求本质

用户不是要一个"更好的 OI 背离查询器"，而是要一个**自动化的做空目标发现管线**：
> "帮我从市场里找到那些正在被庄家拉盘、即将砸盘的币，告诉我做空哪个、什么价位进。"

---

## 2. 目标与成功指标

### 目标

| 优先级 | 目标 | 描述 |
|--------|------|------|
| P0 | 自动发现目标 | 从合约市场涨幅榜自动筛选异常拉升的币种，无需手动输入 |
| P0 | 多因子信号确认 | 将 OI 背离 + 控盘检测 + 资金费率 + 爆仓分布组合为复合做空信号 |
| P1 | 信号排名输出 | 按综合评分排序，输出带优先级的做空推荐列表 |
| P1 | 一键执行 | 用户调用一次 skill，完整跑完"发现→过滤→分析→推荐"全流程 |
| P2 | 可调度运行 | 支持作为 scheduled task 定时巡检（每 4 小时） |

### 成功指标

| 指标 | 目标值 | 衡量方式 |
|------|--------|----------|
| 目标发现覆盖率 | 从涨幅榜 Top 50 中筛出 5-15 个候选币 | 每次运行统计 |
| 信号精度（主观） | 输出的"强信号"币种中，>50% 在 24H 内出现 >5% 回调 | 用户回测反馈 |
| 假阳性控制 | 最终推荐列表 ≤ 5 个币种 | 通过多层过滤控制 |
| 单次运行耗时 | < 3 分钟（含所有 API 调用） | 实测 |
| API 调用量 | 每次运行 ≤ 30 次 MCP 调用 | 计数 |

### 非目标

- **不做自动交易执行**：只输出信号和推荐点位，不连接任何交易所 API 下单
- **不做实时推送**：v1 不集成 Telegram/Discord 推送，仅在 Claude Code 会话中输出
- **不替代 whale-control**：pipeline 内部调用 whale-control 的分析逻辑，但不修改该 skill
- **不覆盖现货币种**：仅分析有永续合约交易对的币种
- **不做回测引擎**：不提供历史信号回测功能

---

## 3. 用户故事

### US-1: 自动发现异常拉升币种

**作为**合约交易员，**我想要**一键扫描当前合约市场中异常拉升的币种，**以便**不遗漏任何潜在做空机会。

**验收标准**：
- [ ] 用户调用 `/oi-divergence-pipeline` 或 `/oi-pipeline` 无需任何参数即可启动
- [ ] skill 自动从 `futures_price_change` 获取多时间段涨幅数据
- [ ] 筛选出 4H 涨幅 > 8% 或 24H 涨幅 > 15% 的币种作为候选
- [ ] 输出第一阶段结果："发现 N 个异常拉升币种"及列表

### US-2: 控盘过滤

**作为**交易员，**我想要**自动过滤掉持仓分散的正常币种，只保留疑似被控盘的目标，**以便**聚焦在最可能被操纵的币上。

**验收标准**：
- [ ] 对候选币种检查持仓集中度（复用 whale-control 的 holder 分析逻辑）
- [ ] 仅保留控盘风险等级 >= "关注"(20%+) 的币种
- [ ] 无法获取 holder 数据的币种使用替代信号（OI 分布集中度、Hyperliquid 鲸鱼持仓）
- [ ] 输出过滤结果："N 个币种通过控盘筛选"

### US-3: OI 背离批量分析

**作为**交易员，**我想要**对通过控盘筛选的币种批量执行 OI 背离分析，**以便**发现价格涨+OI跌的做空信号。

**验收标准**：
- [ ] 对每个通过筛选的币种执行完整的 OI 背离分析（复用 oi-divergence 核心逻辑）
- [ ] 背离强度评级：强/中/弱
- [ ] 包含资金费率确认信号
- [ ] 仅强度 >= "中" 的信号进入最终推荐

### US-4: 综合评分与排名输出

**作为**交易员，**我想要**看到一个按做空优先级排序的推荐列表，带具体入场/止损/目标点位，**以便**直接决策执行。

**验收标准**：
- [ ] 综合评分考虑：背离强度(40%) + 控盘程度(25%) + 资金费率偏离(15%) + 涨幅异常度(10%) + 流动性(10%)
- [ ] 最终输出不超过 5 个币种
- [ ] 每个币种包含：入场区间、止损位、目标位、盈亏比
- [ ] 附带一行 TL;DR 摘要（参考用户画像建议 #4）

### US-5: 定时巡检模式

**作为**交易员，**我想要**设置每 4 小时自动运行一次扫描，**以便**即使不主动查询也不遗漏信号。

**验收标准**：
- [ ] 支持通过 scheduled task 创建定时任务
- [ ] 每次运行生成独立报告，包含时间戳
- [ ] 无信号时输出简短"本轮无异常"摘要，不生成完整报告

---

## 4. 方案概览：管线架构

### 4.1 架构选择：单一复合 Skill

**决策**：实现为**一个 SKILL.md 文件**，内部分 5 个阶段（Phase）顺序执行。

**理由**：
- Claude Code skill 不支持 skill 之间的程序化调用（无 `invoke_skill` 机制）
- 但可以在 SKILL.md 中**内联**其他 skill 的分析逻辑（即把 whale-control 和 oi-divergence 的核心步骤写进同一个 SKILL.md）
- 定时执行通过 `scheduled-tasks` MCP 工具实现，与 skill 解耦

### 4.2 管线流程图

```
Phase 1: 目标发现
│  futures_price_change → 涨幅异常币种列表
│  futures_market_snapshot → 补充市值/OI 数据
│
▼ 筛选：4H >8% 或 24H >15%，排除 BTC/ETH
│
Phase 2: 快速预筛（OI 初筛）
│  futures_oi_aggregated (1H, 12根) × N 币种
│  快速排除 OI 同步上涨的币种（正常多头加仓）
│
▼ 保留：价格涨 + OI 不涨或下降
│
Phase 3: 控盘检测（精简版）
│  ant_token_analytics → holders (Top 20)
│  ant_perp_dex → perp_dex_position_by_coin
│  计算持仓集中度 + 鲸鱼仓位占比
│
▼ 保留：集中度 >20% 或鲸鱼持仓显著
│
Phase 4: 深度 OI 背离分析
│  futures_oi_aggregated (1H, 24根)
│  futures_price_history (1H, 24根)
│  futures_funding_rate_oi_weight (1H, 24根)
│  futures_liquidation_aggregated (1H, 24根)
│  完整背离检测 + 强度评级
│
▼ 保留：背离强度 >= "中"
│
Phase 5: 评分排名 & 输出
│  综合评分 → 排序 → Top 5
│  计算入场/止损/目标点位
│  生成结构化报告
```

### 4.3 API 调用量预算

| 阶段 | 调用数 | 说明 |
|------|--------|------|
| Phase 1 | 2 | futures_price_change + futures_market_snapshot |
| Phase 2 | ~8 | 假设 Phase 1 筛出 ~8 个候选，每个 1 次 OI 查询 |
| Phase 3 | ~8 | 假设 Phase 2 保留 ~4 个，每个 2 次（holders + perp_position） |
| Phase 4 | ~12 | 假设 Phase 3 保留 ~3 个，每个 4 次（OI + price + funding + liquidation） |
| Phase 5 | 0 | 纯计算，无 API 调用 |
| **总计** | **~30** | 在合理范围内 |

---

## 5. 技术设计：分阶段详细规范

### Phase 1: 目标发现

**目的**：从合约市场找到异常拉升的币种。

**Step 1.1 — 获取涨幅排行**

调用 `ant_futures_market_structure`:
- query_type: `futures_price_change`
- symbol: 不传（返回所有币种）

此接口返回各币种的多时间段涨跌幅（5m/15m/30m/1h/2h/4h/6h/12h/24h）。

**Step 1.2 — 获取市场快照**

调用 `ant_futures_market_structure`:
- query_type: `futures_market_snapshot`
- per_page: `100`
- page: `1`

获取 OI 总量、24H 成交量等辅助数据。

**Step 1.3 — 筛选逻辑**

```
候选条件（满足任一）：
  - 4H 涨幅 > 8%
  - 24H 涨幅 > 15%
  - 1H 涨幅 > 5% 且 OI 未同步增长

排除条件：
  - BTC、ETH（大盘币种 OI 背离含义不同）
  - 24H 成交量 < $1M（太薄无法交易）
  - 刚上线 < 7 天的交易对（数据不足）
```

**输出**：候选币种列表（预期 5-15 个），包含：symbol、各时段涨幅、OI、成交量。

### Phase 2: OI 快速预筛

**目的**：快速排除 OI 同步上涨的币种（正常多头加仓，非背离）。

对 Phase 1 每个候选币种，调用 `ant_futures_market_structure`:
- query_type: `futures_oi_aggregated`
- symbol: 候选币种
- interval: `1h`
- limit: `12`（只看最近 12 小时，快速判断）

**快速判断逻辑**：
```
计算最近 12 根 K 线的 OI 变化趋势：
  - OI 上涨 > 5% → 排除（多头正常加仓）
  - OI 基本持平（-2% ~ +2%）→ 保留（可疑，需深入分析）
  - OI 下降 > 2% → 保留（强可疑信号）
```

**优化**：此阶段可**并行调用**所有候选币的 OI 查询。

**输出**：通过预筛的币种列表（预期 3-6 个）。

### Phase 3: 控盘检测（精简版）

**目的**：验证崩盘模型的前提条件——是否存在控盘迹象。

> 注意：这里不是完整复制 whale-control 的全部逻辑（那需要 5+ 次 API 调用/币），而是执行一个**精简版控盘检测**，足以判断"有没有控盘嫌疑"。

**Step 3.1 — 链上持仓检测**

对每个候选币种，需要先获取合约地址和链信息。

尝试调用 `ant_meme`:
- query_type: `search_pairs`
- query: 币种符号

获取 token_address 和 chain_id。如果找不到（纯 CEX 币种），跳过链上分析，仅用合约数据。

**Step 3.2 — Holder 集中度**

如果有链上数据，调用 `ant_token_analytics`:
- query_type: `holders`
- token_address: 合约地址
- chain: 链名称
- pagination: `{"page": 1, "per_page": 20}`

只取 Top 20（非 Top 50），减少数据量。

**快速集中度判断**：
```
排除交易所/合约/销毁地址后：
  - Top 5 EOA 持仓 > 40% → 高控盘嫌疑 → 保留
  - Top 5 EOA 持仓 20-40% → 中控盘嫌疑 → 保留
  - Top 5 EOA 持仓 < 20% → 低风险 → 但如果 Phase 2 OI 降幅 > 5%，仍保留
```

**Step 3.3 — 合约鲸鱼持仓（备用信号）**

调用 `ant_perp_dex`:
- query_type: `perp_dex_position_by_coin`
- symbol: 币种符号

检查是否有大户集中做多（为后续砸盘提供动机验证）。

**降级策略**：
- 无链上数据 → 仅用合约鲸鱼仓位判断
- 无合约鲸鱼数据 → 仅用 OI 下降幅度判断（Phase 2 的 OI 降幅 > 5% 即可通过）
- 两者都无 → 降低该币种的最终评分权重

**输出**：通过控盘筛选的币种列表（预期 2-5 个），附带控盘风险等级。

### Phase 4: 深度 OI 背离分析

**目的**：对通过前三层筛选的币种执行完整的 OI 背离分析，复用 `oi-divergence` 的核心逻辑。

对每个候选币种，**并行调用**以下 4 个查询（均使用 `ant_futures_market_structure`）：

**查询 A — 24 根 1H OI：**
- query_type: `futures_oi_aggregated`
- symbol: 币种
- interval: `1h`
- limit: `24`

**查询 B — 24 根 1H 价格：**
- query_type: `futures_price_history`
- symbol: 币种
- exchange: `binance`（失败则尝试 bybit、okx）
- interval: `1h`
- limit: `24`

**查询 C — 24 根 1H OI 加权资金费率：**
- query_type: `futures_funding_rate_oi_weight`
- symbol: 币种
- interval: `1h`
- limit: `24`

**查询 D — 24 根 1H 爆仓数据：**
- query_type: `futures_liquidation_aggregated`（来自 `ant_futures_liquidation` 工具）
- symbol: 币种
- interval: `1h`
- limit: `24`

**背离分析逻辑**（与现有 oi-divergence SKILL.md 一致）：

```
1. 数据对齐：按时间戳对齐 OI 和价格数据

2. 趋势判断：
   - 价格：计算 close 序列 higher highs / higher closes
   - OI：计算 OI close 变化方向

3. 背离判定：
   - 价格涨 + OI 降 = 背离（做空信号）
   - 价格跌 + OI 降 = 正常平仓
   - 价格涨 + OI 涨 = 多头加仓

4. 强度评级：
   - 强：连续 6+ 根 K 线背离，OI 降幅 > 5%
   - 中：连续 3-5 根 K 线背离，OI 降幅 2-5%
   - 弱：连续 2-3 根 K 线背离，OI 降幅 < 2%

5. 辅助确认：
   - 资金费率 > 0.01% → 多头拥挤确认
   - 资金费率持续为正但 OI 降 → 主力平多信号
   - 近期爆仓以多头为主 → 已有人被清算
```

**做空点位计算**：
```
- 入场区间：当前价格附近或最近高点回踩位
- 止损位：OI 开始下降时对应的价格高点上方 1-2%
- 目标位 1：最近 24H 价格低点
- 目标位 2：OI 下降起始点对应的价格位
- 盈亏比：(入场 - 目标) / (止损 - 入场)
```

**输出**：每个币种的完整背离分析结果 + 做空点位。

### Phase 5: 综合评分与输出

**目的**：将多维信号汇总为一个综合评分，按优先级排序输出。

**评分公式**：

```
总分 = 背离分(40%) + 控盘分(25%) + 资金费率分(15%) + 涨幅异常分(10%) + 流动性分(10%)

背离分 (0-100)：
  强 = 100, 中 = 60, 弱 = 30
  加权：连续 K 线数越多加分（每多 1 根 +5，上限 +20）

控盘分 (0-100)：
  庄家盘(>65%) = 100, 高风险(40-65%) = 75, 关注(20-40%) = 40, 健康(<20%) = 10
  无数据 = 25（中性假设）

资金费率分 (0-100)：
  费率 > 0.05% = 100, 0.03-0.05% = 80, 0.01-0.03% = 50, < 0.01% = 20

涨幅异常分 (0-100)：
  24H 涨幅 > 30% = 100, 20-30% = 80, 15-20% = 60, 10-15% = 40, < 10% = 20

流动性分 (0-100)：
  成交量 < $5M = 80（薄，易被操纵）, $5-20M = 60, $20-100M = 40, > $100M = 20
  注意：流动性越低分越高，因为低流动性更容易被控盘砸盘
```

**排序 & 截断**：
- 按总分降序排列
- 输出 Top 5（或全部通过的币种，取较少者）
- 总分 < 40 的币种不输出

---

## 6. 输出格式

```
## OI 背离自动狙击报告

**扫描时间**: 2026-04-04 14:00 UTC
**扫描范围**: 合约市场涨幅榜 Top 100
**管线进度**: 100 个币种 → 12 个异常拉升 → 5 个 OI 可疑 → 3 个控盘确认 → 2 个背离成立

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### TL;DR

⚠️ 发现 2 个做空信号：
1. **SIREN** (评分 87) — 强背离，连续 8 根 K 线价格涨 OI 跌，庄家控盘 88%，建议 $0.265 附近做空
2. **BULLA** (评分 72) — 中背离，连续 4 根 K 线背离，资金费率 0.12% 偏高，建议关注 $0.107 做空

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 信号 #1: SIREN — 评分 87/100

**管线筛选路径**: 24H 涨幅 +22% → OI 12H 降 -8.3% → 控盘 88.5% 🔴庄家盘 → 强背离

| 维度 | 数据 | 评分 |
|------|------|------|
| OI 背离 | 强（连续 8 根，OI 降 -12%） | 100 |
| 控盘程度 | 88.5%（52 个关联地址） | 100 |
| 资金费率 | 0.035%（OI 加权） | 80 |
| 涨幅异常 | 24H +22% | 80 |
| 流动性 | 24H Vol $16.5M | 60 |

#### 数据概览

| 指标 | 起始值 | 当前值 | 变化 | 方向 |
|------|--------|--------|------|------|
| 价格 | $0.217 | $0.265 | +22.1% | 上涨 |
| OI | $8.2M | $7.2M | -12.2% | 下降 |
| 资金费率 | 0.02% | 0.035% | — | 偏高 |

#### 做空建议

- 入场区间: $0.260 - $0.270
- 止损位: $0.278（最近高点上方 2%）
- 目标位 1: $0.230（24H 低点）
- 目标位 2: $0.217（背离起始价格）
- 盈亏比: 约 2.8:1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 信号 #2: BULLA — 评分 72/100

（类似格式）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 未通过筛选的币种（参考）

| 币种 | 24H 涨幅 | 淘汰阶段 | 淘汰原因 |
|------|----------|----------|----------|
| XXX | +18% | Phase 2 | OI 同步上涨 +8% |
| YYY | +12% | Phase 3 | 持仓分散，Top 5 仅 8% |
| ZZZ | +25% | Phase 4 | OI 背离弱（仅 2 根 K 线） |

### 风险提示

- 此分析基于 1H 级别数据，短周期信号可能被更大级别趋势覆盖
- OI 下降不一定代表主力行为，也可能是自然平仓
- 控盘比例基于链上地址聚类推断，非确认
- 建议结合大盘趋势和盘口数据综合判断
- 仅供学习参考，不构成投资建议
```

**无信号时的简短输出**：

```
## OI 背离自动狙击报告

**扫描时间**: 2026-04-04 14:00 UTC
**结果**: 本轮未发现符合条件的做空信号。

管线概况: 100 个币种 → 8 个异常拉升 → 3 个 OI 可疑 → 0 个通过控盘筛选

下次扫描建议: 4 小时后，或当市场出现急涨行情时手动触发。
```

---

## 7. Skill 文件技术规范

### 7.1 Frontmatter

```yaml
---
name: oi-divergence-pipeline
version: "1.0.0"
user-invocable: true
description: |
  OI 背离自动狙击管线。自动从合约涨幅榜发现异常拉升币种，
  经过 OI 预筛 → 控盘检测 → 深度背离分析 → 综合评分，
  输出带优先级的做空推荐列表。无需手动输入币种。
  需要 Antseer MCP 服务器（见 README.md 安装说明）。
  Use when asked to "自动做空扫描", "狙击管线", "pipeline",
  "批量OI背离", "做空雷达", "auto short scan", "oi pipeline",
  "找做空目标", "哪些币要崩"
argument-hint: "（无参数直接运行，或传入自定义涨幅阈值如 '10%'）"
allowed-tools:
  - mcp__ANTSEER_MCP_ID__ant_futures_market_structure
  - mcp__ANTSEER_MCP_ID__ant_futures_liquidation
  - mcp__ANTSEER_MCP_ID__ant_token_analytics
  - mcp__ANTSEER_MCP_ID__ant_meme
  - mcp__ANTSEER_MCP_ID__ant_perp_dex
  - mcp__ANTSEER_MCP_ID__ant_address_profile
metadata:
  requires:
    mcpServers:
      - name: antseer
        description: "Antseer on-chain data MCP"
author: mike
license: MIT
---
```

### 7.2 MCP 工具调用完整映射

| 阶段 | 工具 | query_type | 关键参数 | 并行/串行 |
|------|------|------------|----------|-----------|
| P1 | ant_futures_market_structure | futures_price_change | (无 symbol = 全量) | 并行 |
| P1 | ant_futures_market_structure | futures_market_snapshot | per_page=100 | 并行 |
| P2 | ant_futures_market_structure | futures_oi_aggregated | symbol=各候选, interval=1h, limit=12 | 并行(N个) |
| P3 | ant_meme | search_pairs | query=币种符号 | 串行 |
| P3 | ant_token_analytics | holders | token_address, chain, per_page=20 | 并行 |
| P3 | ant_perp_dex | perp_dex_position_by_coin | symbol=币种 | 并行 |
| P4 | ant_futures_market_structure | futures_oi_aggregated | symbol, interval=1h, limit=24 | 并行(4个/币) |
| P4 | ant_futures_market_structure | futures_price_history | symbol, exchange=binance, interval=1h, limit=24 | 并行 |
| P4 | ant_futures_market_structure | futures_funding_rate_oi_weight | symbol, interval=1h, limit=24 | 并行 |
| P4 | ant_futures_liquidation | futures_liquidation_aggregated | symbol, interval=1h, limit=24 | 并行 |

### 7.3 定时任务配置

用户可通过以下方式设置定时巡检：

```
请帮我设置一个 scheduled task，每 4 小时自动运行 /oi-divergence-pipeline
```

建议 cron 表达式: `17 */4 * * *`（每 4 小时的第 17 分钟，避开整点）

---

## 8. 风险因素与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| API 调用量过大 | 超出 MCP 配额或超时 | 中 | Phase 2 的快速预筛大幅减少后续调用量；严格控制每阶段的候选数上限 |
| 假阳性过高 | 用户信任度下降 | 高 | 三层过滤（涨幅→OI→控盘）+ 多因子评分；仅输出评分 > 40 的信号 |
| 小币种数据缺失 | holder 数据或 OI 数据为空 | 中 | 每个阶段都有降级策略；无数据不阻塞流程，而是降低评分权重 |
| 信号时效性 | 用户看到信号时价格已变 | 中 | 报告标注扫描时间；推荐入场区间而非精确点位；支持定时运行缩短延迟 |
| 大盘系统性暴涨 | 大量币种同时触发涨幅筛选 | 低 | Phase 1 排除 BTC/ETH；涨幅阈值可调；候选上限 15 个 |
| whale-control 逻辑内联维护成本 | skill 更新时需要同步 | 中 | Phase 3 仅使用精简版控盘检测（Top 20 holder + 鲸鱼仓位），不需要完整的地址聚类 |

---

## 9. 实施计划

### 阶段 1: MVP（预计 1 个 skill session）

1. 创建 `skills/oi-divergence-pipeline/` 目录结构
2. 编写 SKILL.md，实现 Phase 1-2-4-5（跳过 Phase 3 控盘检测）
3. 手动测试：运行一次，验证目标发现和 OI 背离批量分析
4. 调整涨幅阈值和 OI 阈值

### 阶段 2: 控盘集成

5. 在 SKILL.md 中增加 Phase 3 精简版控盘检测
6. 实现评分公式中的控盘分权重
7. 端到端测试完整管线

### 阶段 3: 定时 & 优化

8. 编写 README.md 和 setup.sh
9. 测试 scheduled task 集成
10. 基于实际运行结果调参（涨幅阈值、评分权重）

### 文件清单

```
skills/oi-divergence-pipeline/
├── SKILL.md          # 核心 skill 定义（管线全流程）
├── README.md         # 使用文档
├── setup.sh          # MCP UUID 自动配置脚本
└── docs/
    └── prd.md        # 本 PRD 文档存档
```

---

## 10. 与现有 Skill 的关系

| 现有 Skill | 关系 | 说明 |
|------------|------|------|
| oi-divergence | **不修改，逻辑内联** | pipeline 的 Phase 4 内联了 oi-divergence 的核心背离分析逻辑。原 skill 保持独立，用户仍可 `/oi-divergence BTC` 查单币 |
| whale-control | **不修改，精简版内联** | pipeline 的 Phase 3 使用 whale-control 的 holder 分析的精简版（仅 Top 20，不做完整地址聚类）。原 skill 保持独立 |

---

## 11. 开放问题

1. **涨幅阈值是否需要动态调整？** 牛市中 10% 涨幅很常见，需要更高阈值；熊市中 5% 已经异常。是否需要根据 BTC 近期波动率动态设定？ → v1 先用固定阈值，后续迭代。

2. **Phase 3 是否需要完整地址聚类？** 精简版（Top 20 holder 集中度）可能漏掉分散持仓但实际由同一实体控制的情况。但完整聚类（related_wallets 交叉比对）每个币需要 5+ 次 API 调用，太重。 → v1 用精简版，用户可对高评分币种手动跑 `/whale-control` 深入分析。

3. **Hyperliquid 数据权重？** 用户画像报告显示 HL 已取代 Binance 成为 OI 讨论核心场所。pipeline 的 Phase 4 价格数据默认从 Binance 取——是否需要增加 HL 数据？ → v1 通过 `perp_dex_position_by_coin` 获取 HL 鲸鱼数据作为辅助，但 OI 聚合数据已包含 HL。

4. **输出语言？** 现有 skill 全部中文输出，pipeline 保持一致。

---

*本 PRD 由 Alex (Product Manager Agent) 基于 oi-divergence SKILL.md、whale-control SKILL.md、用户画像报告、及 Antseer MCP 工具文档生成。*
