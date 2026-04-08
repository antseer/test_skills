<div align="center">

# 庄家控盘币 OI 背离狙击

自动发现庄家控盘标的，用 5 分钟级别 OI 背离精准狙击做空时机

[![X](https://img.shields.io/badge/关注-%40Antseer__ai-black?logo=x&logoColor=white)](https://x.com/Antseer_ai) [![Telegram](https://img.shields.io/badge/Telegram-AntseerGroup-2CA5E0?logo=telegram&logoColor=white)](https://t.me/AntseerGroup) [![GitHub](https://img.shields.io/badge/GitHub-antseer--dev-181717?logo=github&logoColor=white)](https://github.com/antseer-dev/OpenWeb3Data_MCP) [![Medium](https://img.shields.io/badge/Medium-antseer-000000?logo=medium&logoColor=white)](https://medium.com/@antseer/)

[English](README.md) | 简体中文

</div>

---

## 这个工具做什么？

你看到某个小币一天涨了 50% 以上，想知道：这是真的有人在买，还是庄家拉盘准备砸？这个工具自动帮你找到这些币，然后告诉你庄家什么时候开始跑路。

工作原理：

1. **扫描币安合约市场**，找到 24H 涨幅超过 50% 的币种
2. **三条件交叉验证庄家控盘**（满足 2/3 即可）：暴涨 + 合约量 Top 50 + 沉寂多日后突然大阳线
3. **5 分钟级别 OI 背离检测** — 价格撑着不跌但持仓量（OI）在降，说明庄家在高位悄悄平多出货
4. **生成做空建议**，包括入场位、止损位、止盈位和爆仓风控

| 能力 | 说明 |
|------|------|
| 自动发现标的 | 全市场扫描，不需要手动输入币种 |
| 三条件交叉验证（2/3） | 24H 涨幅 50%+ × 合约量 Top 50 × 突然拉升形态（满足 2/3 即可） |
| 5 分钟 OI 背离 | 双层检测：30 分钟滚动窗口 + 逐根 K 线分析 |
| 极端风控 | 爆仓价 = 入场价 × 10；首波信号提示 1/4 仓位 + 宽止损 |

## 怎么用？

向你的 AI Agent 发送：

```
/oi-divergence
```

不需要任何参数，工具自动扫描全市场。

### 参数说明

| 参数 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| *（无）* | — | 全自动运行，无需输入 | — |

工具会自动执行完整流程：市场扫描 → 控盘检测 → OI 背离分析 → 信号生成。

## 会输出什么？

```
## 输出格式

严格按以下格式输出，分两次推送，不要添加额外字段或修改格式。

### 推送1：标的筛选

当筛选完成时，输出所有通过条件的候选币种：

OI背离 标的筛选完成

1. {SYMBOL}
24H涨幅: +{涨幅}%
合约交易量排名: #{排名}
近30D日均波动: {波动率}%
筛选条件: {N}/3 通过（条件1✓ 条件2✓/✗ 条件3✓/✗）

逐个列出，按涨幅降序排列。若无候选币种，本轮不推送。

### 推送2：做空信号

仅对通过OI背离验证的币种输出，每个币种单独一条：

OI背离 做空信号：
- 合约: {SYMBOL}
- 入场区间: ${低} - ${高}
- 止损位: ${止损价}
- 止盈位: ${止盈价}
- 盈亏比: {X}:1
- 爆仓价: > ${爆仓价}（入场价 10x，防止庄家反拉）

⚠️ 首波信号提示: 这是8H窗口内的首次背离，庄家控盘币可能二次拉升，建议1/4仓位+宽止损。

注意: {一段话说明当前关键风险，包括但不限于：OI回升趋势、信号失效条件、资金费率异常等}

若无币种通过OI背离验证，不输出推送2。
```

## 什么时候用？什么时候不适合？

### 适合

- 看到涨幅榜有异常暴涨的币，想知道能不能做空
- 全市场扫描庄家控盘信号，不用自己一个个翻
- 需要具体的入场/止损/止盈点位，而不只是"可能要跌"
- 日常扫描 — 每天看到异常拉升时跑一次

### 不适合

- 分析 BTC、ETH 等大盘币（本工具专注被操控的小币）
- 需要秒级实时信号（最小分析粒度是 5 分钟）
- 替代专业量化回测系统（这是信号扫描器，不是回测引擎）
- 现货市场分析（本工具专注永续合约）

## 安装

### 安装 Skill

**Claude Code (CLI)**
```bash
claude skill add antseer-dev/oi-divergence
```

**Cowork（桌面应用）**
在 Cowork 插件市场搜索 `oi-divergence`，点击安装。

**手动安装**
下载 `.skill` 文件，在 Agent 客户端中导入。

### 前置依赖：MCP 服务

> **什么是 MCP？** MCP（Model Context Protocol）是给 AI Agent 接上数据管道的协议。不装 MCP 服务，Agent 拿不到实时数据，分析就跑不起来。

本 skill 需要先安装并配置以下 MCP 服务：

#### AntSeer On-Chain MCP

根据你使用的 Agent 客户端，选择对应的安装方式：

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user ant-on-chain-mcp https://ant-on-chain-mcp.antseer.ai/mcp
```

**Cowork（桌面应用）**
进入 设置 → MCP 服务器 → 添加：
- 名称：`ant-on-chain-mcp`
- URL：`https://ant-on-chain-mcp.antseer.ai/mcp`
- 传输类型：`http`

**OpenClaw / Claw**
在设置页面添加 MCP 服务器，填写：
- 名称：`ant-on-chain-mcp`
- URL：`https://ant-on-chain-mcp.antseer.ai/mcp`
- 传输类型：`http`

**OpenCode**
在配置文件 `opencode.json` 中添加：
```json
{
  "mcpServers": {
    "ant-on-chain-mcp": {
      "type": "http",
      "url": "https://ant-on-chain-mcp.antseer.ai/mcp"
    }
  }
}
```

**通用 MCP 客户端**
任何支持 MCP 协议的客户端均可接入，核心参数：
- MCP 端点：`https://ant-on-chain-mcp.antseer.ai/mcp`
- 传输类型（Transport）：`http`
- 作用域（Scope）：`user`（推荐，跨项目共享）

安装完成后，**重启你的 Agent 客户端**以激活 MCP 服务。

## 免责声明

本工具基于历史数据和统计模型进行分析，**不能预测未来市场走势**，分析结果仅供参考，**不构成任何投资建议**。

所使用的分析方法论和指标归属其原始作者，本工具仅做集成和展示。用户应结合自身判断和风险承受能力做出独立决策。使用本工具即视为您已充分知悉上述风险并自愿承担全部责任。

---

<div align="center">

Built by [AntSeer](https://antseer.ai) · Powered by AI Agents

</div>
