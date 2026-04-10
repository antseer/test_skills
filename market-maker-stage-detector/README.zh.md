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

> 以下为 RAVE (RaveDAO) 在 BSC 链上的真实分析输出 — 2026 年 4 月。

```
🔴 RAVE | BSC | 市值 $250.4M | FDV $26.0M
阶段: 拉升 (PUMPING) | 置信度 75% (3/4)
建议: 不建议追高 — 流动性仅 $137K，退出时滑点将非常严重。
```

### 风险信号

| 级别 | 信号 — 数据依据 |
|------|-----------------|
| 🔴 HIGH | 筹码极端集中 — Top 4 地址控制 80.2%，#3 和 #4 共享 GnosisSafeProxyFactory |
| 🔴 HIGH | 新建钱包大额持仓 — #4 钱包昨天 (4/9) 刚创建，立即持有 11.3% 供应量 ($296 万) |
| 🔴 HIGH | 流动性与市值严重不匹配 — $137K LP vs $250M 市值，Vol/LP = 33.8x |
| 🔴 HIGH | Fresh Wallets 异常涌入 — +$848 万净流入，疑似刷量或诱导散户 |
| 🟡 MED | Smart Money 卖出 — Smart Trader 净卖出 $26.7K |
| 🟡 MED | Bot 主导交易 — Vault Bot (0x238a) 单地址贡献 $4.18M 交易量 |

### 筹码分布

| # | 地址 | 占比 | 24h 变动 | 备注 |
|---|------|------|----------|------|
| 1 | 0xf073..06fa | 36.7% | 0 | 由 Binance Hot Wallet 出金，30d 零变动 |
| 2 | 0x2d81..ecab | 20.1% | 0 | 孤立钱包，30d 零变动 |
| 3 | 0x6020..74b0 | 12.1% | 0 | Gnosis Safe 多签，2025-12-04 创建 |
| 4 | 0x0a1f..90d7 | 11.3% | +280 万枚 | **Gnosis Safe，昨天 (4/9) 新建** |
| 5 | 0x73d8..46db | 8.9% | -24.7 万 | Binance DEX/CEX Trading Bot |

Top 4 合计: **80.2%**

关联钱包: #3 和 #4 均通过 GnosisSafeProxyFactory (0x4e1dcf) 创建 — 可能同一团队，合并持仓 23.4%。

### 资金流向

| 群体 | 净流向 | 方向 |
|------|--------|------|
| Fresh Wallets | +$8,479,235 | 🟢 大量涌入 |
| Top PnL 交易者 | +$480,444 | 🟢 买入 |
| Smart Trader | -$26,685 | 🔴 卖出 |
| Exchange | -$553,021 | 🔴 流出交易所 |

Fresh Wallets 涌入 $848 万是最突出的信号 — 可能是新散户 FOMO 追涨，也可能是庄家用新钱包制造虚假买盘。Smart Trader 已在小规模卖出。

### 信号匹配

```
✅ 价格显著上涨 (>20%): 24h +239%
✅ 大单占比高: Vault Bot 单地址主导 $4.18M 交易量
✅ 成交量集中在特定时段: 6h 交易量 $3.57M 占 24h 的 77%
❌ 换手率高 (>30%): 实际 17.8%，未达阈值
```

庄家正在拉升价格。少数地址驱动交易量，筹码未大量散出。已持仓注意止盈，未持仓追高风险大。

额外警告: Smart Trader 已在卖出、1h 价格回落 -3.5%，出现从拉升向出货过渡的早期信号。

> 免责声明: 本分析仅供参考，不构成投资建议。关联钱包识别可能有漏报，请自行做好风险管理。

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
