# btc-bubble-bottom-detector

BTC 泡沫指数底部探测器 — 用链上估值指标判断 BTC 是否处于历史底部区域

## 功能

调用 `/btc-bubble-bottom-detector` 后，Claude 会：

1. 并行拉取 MVRV、NVT Golden Cross、市场情绪、ETF 资金流、交易所储备 6 项数据
2. 基于评分体系计算底部概率（0-100 分）
3. 判定信号强度：强底部 / 温和底部 / 尚未确认
4. 如提供目标价，计算风险回报比

**理论来源**: @monkeyjiang 的泡沫指数底部分析法
- 比特币泡沫指数跌至 10 附近是历史验证的底部信号
- 本 skill 使用 MVRV + NVT + 情绪 + ETF + 储备组合替代原始泡沫指数

**评分权重**:
- MVRV 比率: 30 分（核心链上估值指标）
- NVT Golden Cross: 15 分（网络价值验证）
- 市场情绪: 15 分（恐慌/贪婪状态）
- ETF 30 日净流入: 15 分（机构行为）
- 交易所储备趋势: 10 分（供应紧缩信号）

## 前置依赖

### MCP 服务安装

本 skill 需要先安装并配置 Antseer MCP 服务器，它提供以下数据工具：
- `ant_spot_market_structure` — BTC 价格数据
- `ant_token_analytics` — MVRV、NVT 链上指标
- `ant_market_sentiment` — 市场情绪数据
- `ant_etf_fund_flow` — ETF 资金流数据
- `ant_fund_flow` — 交易所储备数据

#### Antseer MCP

根据你使用的 Agent 客户端，选择对应的安装方式：

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user ant-on-chain-mcp https://ant-on-chain-mcp.antseer.ai/mcp
```

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

## 安装步骤

### 第 1 步：确认 Antseer MCP 已安装

确保在 Claude Code 中能看到 `ant_spot_market_structure`、`ant_token_analytics` 等工具。

### 第 2 步：克隆 skill

将此目录复制到你的 Claude Code skills 目录：

```bash
cp -r btc-bubble-bottom-detector ~/.claude/skills/
```

### 第 3 步：运行配置脚本

```bash
cd ~/.claude/skills/btc-bubble-bottom-detector
chmod +x setup.sh
./setup.sh
```

脚本会自动检测你的 Antseer MCP UUID 并写入 `SKILL.md`。
如果自动检测失败，按提示手动粘贴 UUID 即可。

> **如何手动找 UUID**：在 Claude Code 中输入 `/tools`，找到工具名
> `mcp__<UUID>__ant_spot_market_structure`，复制 `<UUID>` 部分。

### 第 4 步：使用

```
/btc-bubble-bottom-detector
/btc-bubble-bottom-detector 200000 2y
```

## 输出示例

```
=== BTC 底部探测报告 ===
时间: 2026-04-01

当前价格: $65,000
底部评分: 78/100 — 🟢 强底部信号

┌─────────────────────────────────────────────────┐
│ 指标              │ 当前值     │ 信号      │ 得分  │
├─────────────────────────────────────────────────┤
│ MVRV              │ 0.92       │ 强底部    │ +30   │
│ NVT Golden Cross  │ 低位区间   │ 底部      │ +15   │
│ 市场情绪          │ 32/100     │ 恐慌      │ +15   │
│ ETF 30日净流入    │ +$1.2B     │ 积极      │ +15   │
│ 交易所储备        │ 90日↓3%    │ 供应紧缩  │ +10   │
└─────────────────────────────────────────────────┘

风险回报分析:
  目标价: $200,000 (2y)
  潜在收益: +207%
  历史同级别底部最大回撤: -15%
  风险回报比: 13.8:1

结论: 多项链上估值指标显示 BTC 处于历史底部区域。
MVRV < 1.0 + 机构 ETF 持续净流入 + 交易所储备下降，
与 2022 年以来历次底部的信号模式一致。当前区域适合中长线布局。
```

## 适用范围

- 适用于 BTC 的中长线底部判断
- 不适用于短线交易信号
- 不适用于 BTC 以外的小市值代币

## 免责声明

本 skill 基于链上估值指标的历史统计规律，不能精确预测底部价格或反弹时间。分析方法论归属原作者 @monkeyjiang。不构成投资建议。
