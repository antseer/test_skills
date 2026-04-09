<div align="center">

# 庄家阶段识别器

输入任意代币合约地址，用 6 维链上信号判断庄家处于哪个阶段 — 吸筹、拉升、出货、还是已跑。

[![X](https://img.shields.io/badge/关注-%40Antseer__ai-black?logo=x&logoColor=white)](https://x.com/Antseer_ai) [![Telegram](https://img.shields.io/badge/Telegram-AntseerGroup-2CA5E0?logo=telegram&logoColor=white)](https://t.me/AntseerGroup) [![GitHub](https://img.shields.io/badge/GitHub-antseer--dev-181717?logo=github&logoColor=white)](https://github.com/antseer-dev/OpenWeb3Data_MCP) [![Medium](https://img.shields.io/badge/Medium-antseer-000000?logo=medium&logoColor=white)](https://medium.com/@antseer/)

[English](README.md) | 简体中文

</div>

## 这个工具做什么？

你发现了一个新币，想知道背后有没有庄、庄在什么阶段。这个工具帮你几分钟搞定。

它分析 6 个链上维度:

| 维度 | 看什么 |
|------|--------|
| 筹码集中度 | 少数实体是否控制了大部分流通量？ |
| 成交量真实度 | 交易量是真实的还是刷出来的？ |
| 换手率与时段 | 成交量分布是否正常，还是集中爆发？ |
| 大单占比 | 少数大交易是否驱动了全部成交量？ |
| 资金流向 | 聪明钱和大户在买还是在卖？ |
| 综合判断 | 综合所有信号判定: 吸筹、拉升、出货、已跑 |

数据来自 Antseer 链上 MCP（一种给 AI 接上实时链上数据的协议），覆盖持仓分析、DEX 交易、钱包画像、Smart Money 追踪。

## 怎么用？

向你的 AI Agent 发送:

```
/market-maker-stage-detector 0x9234e981e395dA3BE7b00B035163571698f8f756 --chain bsc
```

### 参数说明

| 参数 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `token_address` | Yes | 代币合约地址或名称 | — |
| `--chain` | No | 链名称 (ethereum / bsc / solana / base / arbitrum) | `ethereum` |

### 更多示例

```
/market-maker-stage-detector WALK --chain bsc
/market-maker-stage-detector 0x1234...abcd --chain solana
/market-maker-stage-detector 0xdead...beef
```

## 会输出什么？

```
代币: WALK | 链: BSC | 市值: $1.60M
当前阶段: 出货 (DISTRIBUTING) | 置信度: 72%
信号命中: 4/6

关键发现:
- [HIGH] 筹码集中度 78 — 40% 代币集中在单一 Vault 合约中
- [HIGH] Holder 增长 22% 但价格跌 5.2% — 筹码正在派发
- [MED] Vol/Holder $192 (同类 $85) — 成交量偏高

建议: 不要追涨买入。已持仓者考虑分批减仓。

完整报告: output/mm-report-WALK.html
```

HTML 报告包含 Chart.js 交互式可视化图表，展示全部 6 个指标。

## 什么时候用？什么时候不适合？

### 适合

- 买入前对任何 DEX 交易的代币做风险检查
- 定期监控你持仓的代币
- 某个币突然放量时快速诊断
- 对比多个代币的筹码结构

### 不适合

- BTC/ETH 等大盘币（本工具针对中小市值 DEX 代币）
- 需要实时交易信号（分析粒度是小时/天级别）
- LP 锁定状态检测（需要 DEXScreener 等外部工具）
- Funding wallet 溯源（需要 Arkham 或 Nansen）

## 安装

### 安装 Skill

**Claude Code (CLI)**
```bash
claude skill add antseer/market-maker-stage-detector
```

### 前置依赖: MCP 服务

> **什么是 MCP？** MCP（Model Context Protocol）是给 AI Agent 接上数据管道的协议。不装 MCP 服务，Agent 拿不到实时链上数据，分析就跑不起来。

本 skill 需要先安装 Antseer MCP 服务:

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user ant-on-chain-mcp https://ant-on-chain-mcp.antseer.ai/mcp
```

**Cowork（桌面应用）**
进入 设置 > MCP 服务器 > 添加:
- 名称: `ant-on-chain-mcp`
- URL: `https://ant-on-chain-mcp.antseer.ai/mcp`
- 传输类型: `http`

安装完成后，**重启你的 Agent 客户端**以激活 MCP 服务。

## 免责声明

本工具基于历史数据和统计模型进行分析，**不能预测未来市场走势**，分析结果仅供参考，**不构成任何投资建议**。

分析方法论归属原作者 @agintender，本工具仅做集成和展示。用户应结合自身判断和风险承受能力做出独立决策。使用本工具即视为您已充分知悉上述风险并自愿承担全部责任。

---

<div align="center">

Built by [AntSeer](https://antseer.ai) · Powered by AI Agents

</div>
