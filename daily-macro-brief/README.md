# daily-macro-brief

宏观日简报生成器 — 用链上 + 宏观数据每天帮你做一份跨资产 Risk-On/Off 研判报告

---

## 这个工具做什么？

你是加密研究员、宏观交易员或者 KOL，每天早上需要快速搞清楚：今天宏观是什么情绪？BTC 在做 Risk-On 还是 Risk-Off？哪些事件驱动了市场？

这个工具帮你：

1. **自动拉数据** — 通过 Antseer MCP 采集 BTC/ETH 价格、资金费率、OI、ETF 资金流向、稳定币供应、市场情绪、Smart Money 流向，以及宏观经济指标（CPI、联邦基金利率、美联储资产负债表）
2. **跨资产分析** — 结合原油、标普 500、美债收益率、VIX（需外部数据源，详见下方说明）计算 BTC 的风险相关性
3. **生成结构化简报** — 输出 5 个标准章节：今日焦点、关键事件、信号解读、历史类比、资产含义，外加 0–10 分的 Risk-On/Off 评分

灵感来源：@0xcryptowizard 于 2026-03-09 发布的每日宏观简报系统。方法论归属原作者。

---

## 怎么用？

**最简单的方式（今天的简报）：**

```
/daily-macro-brief
```

**指定日期：**

```
/daily-macro-brief 2026-03-08
```

**指定关注资产：**

```
/daily-macro-brief focus_assets=BTC,ETH,SOL
```

**完整参数示例：**

```
/daily-macro-brief date=2026-03-08 focus_assets=BTC,ETH language=zh historical_compare=true risk_score_enabled=true
```

### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| date | 日期字符串 | 否 | 当天 | 简报日期，格式 YYYY-MM-DD |
| focus_assets | 列表 | 否 | BTC, ETH | 重点关注的加密资产 |
| include_sections | 列表 | 否 | 全部 5 个 | 指定只输出哪些章节 |
| language | zh / en | 否 | zh | 输出语言 |
| historical_compare | true/false | 否 | true | 是否包含历史情境类比 |
| risk_score_enabled | true/false | 否 | true | 是否输出 Risk-On/Off 评分 |

---

## 会输出什么？

下面是一个完整的模拟输出示例（基于原作者 2026-03-08 案例）：

```
Daily Macro Brief | 2026-03-08
Risk Score: 2.5 / 10  [极度 Risk-Off]
主导叙事: 地缘风险驱动滞胀定价，信用市场开始交易衰退场景

**今日焦点**
地缘政治风险（伊朗局势）成为主导市场的核心变量，影响已从避险情绪蔓延至大宗商品
（铝、原油）和通胀预期。市场正从对利率的单一关注，转向对"滞胀"情景的定价。

**关键事件**
1. 伊朗冲突升级 → 原油/铝价至多年高位 [通胀预期↑] 🔴
2. 中国 CPI 走高（节日+油价效应） → 输入性通胀担忧↑ [Risk-Off] 🔴
3. 中国国债期货年内最大跌幅 → 利率市场对通胀即时反应 [利率↑] 🔴
4. 高收益债利差加速走阔 → 信用市场开始定价衰退 [Risk-Off] 🔴
5. BTC 与原油负相关走势 → 被重新定价为高贝塔风险资产 [加密↓] 🔴

**信号解读**
- 流动性结构分化: 联储扩表被逆回购抵消，净流动性中性但结构性收紧
- 衰退交易深化: 国债收益率↓ + 高收益利差↑ 并存 → 强衰退信号
- VIX 异常收缩: 地缘冲击背景下 VIX 偏低，可能低估尾部风险

**历史类比**: 2018 Q4 (相似度 82%)
- 标普 500 在 Q4 下跌约 14%，高收益利差走阔 >200bps
- 油价先涨后跌，需求衰退预期最终主导

**资产含义**
- 股票: 滞胀担忧 + 信用收紧 → 盈利&估值双重承压，周期股/未盈利成长股更脆弱
- 利率: 短端通胀预期↑ + 长端衰退担忧↓ → 收益率曲线扁平化/倒挂风险
- 加密: 高贝塔风险资产属性主导，独立叙事暂退，短期难摆脱风险偏好约束
- 大宗商品: 地缘溢价支撑油价短期，但衰退预期形成长期压力

---
数据时间戳: 2026-03-08T07:30:00+08:00
数据来源: Antseer MCP + 外部补充数据
```

---

## 什么时候用？什么时候不适合？

**适合这些场景：**
- 每天早上开盘前做宏观环境扫描（建议北京时间 07:00–08:00）
- 在写研究报告或 KOL 推文前，快速整理当天的宏观框架
- 需要判断当前市场是 Risk-On 还是 Risk-Off，并找到可类比的历史阶段
- 需要一个标准化的跨资产分析模板，每天保持输出一致性

**不适合这些场景：**
- 需要实时分钟级数据（本工具面向每日粒度）
- 需要具体的买卖建议或仓位比例（本工具只提供分析框架）
- 需要对非美市场（A 股、港股、日债）做深度分析（当前数据源以美国宏观为主）
- 完全替代人工判断——历史类比的适用性和主导叙事的优先级仍需人工 review

---

## 前置依赖

### 为什么需要装 MCP？

这个工具需要实时的加密市场数据和宏观经济指标才能工作。MCP（Model Context Protocol）服务器是数据来源 — 把它理解成"给 Claude 接上 Antseer 数据管道"。不装的话，Claude 拿不到链上数据，分析就跑不起来。

### MCP 服务安装

#### Antseer MCP 服务

**Claude Code (CLI)**

```bash
claude mcp add --transport http --scope user antseer https://mcp.antseer.xyz/mcp
```

**OpenClaw / Claw**

在设置页面添加 MCP 服务器，填写：
- 名称：`antseer`
- URL：`https://mcp.antseer.xyz/mcp`
- 传输类型：`http`

**OpenCode**

在配置文件 `opencode.json` 中添加：

```json
{
  "mcpServers": {
    "antseer": {
      "type": "http",
      "url": "https://mcp.antseer.xyz/mcp"
    }
  }
}
```

**通用 MCP 客户端**

任何支持 MCP 协议的客户端均可接入，核心参数：
- MCP 端点：`https://mcp.antseer.xyz/mcp`
- 传输类型（Transport）：`http`
- 作用域（Scope）：`user`（推荐，跨项目共享）

安装完成后，**重启你的 Agent 客户端**以激活 MCP 服务。

### 外部数据补充（原油 / 标普 / 美债 / VIX）

Antseer MCP 目前覆盖加密资产和部分宏观指标，以下传统资产需要外部数据源：

| 数据 | 建议来源 | 获取方式 |
|------|----------|----------|
| 原油价格 (WTI) | Yahoo Finance | Ticker: `CL=F` |
| 标普 500 | Yahoo Finance | Ticker: `^GSPC` |
| 美债 10Y 收益率 | FRED API | Series: `DGS10` |
| 美债 2Y 收益率 | FRED API | Series: `DGS2` |
| VIX 波动率指数 | Yahoo Finance | Ticker: `^VIX` |
| 高收益债利差 | FRED API | Series: `BAMLH0A0HYM2` |

如果你没有接入上述外部数据源，这个工具会在报告中明确标注哪些字段缺失，并用已有数据做尽量完整的分析。

---

## 免责声明

- 本工具生成的分析基于历史和实时数据，**不能预测未来市场走势**。
- 5 section 分析框架和 Risk-On/Off 评分方法论归属原作者 **@0xcryptowizard**（https://x.com/0xcryptowizard/status/2030860218557677963）。
- 历史情境类比仅供参考，相似度评分为启发式计算，不构成统计保证。
- **不构成任何投资建议。** 所有输出仅为分析参考，投资决策请结合自身风险承受能力并咨询专业人士。
