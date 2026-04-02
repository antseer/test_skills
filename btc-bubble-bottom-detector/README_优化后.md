# btc-bubble-bottom-detector

BTC 泡沫指数底部探测器 — 用链上估值指标判断 BTC 是否处于历史底部区域

## 这个工具做什么？

你在看 BTC 行情的时候，心里可能会想：**现在这个价格到底算不算便宜？是不是可以开始买了？**

这个工具帮你回答这个问题。它不是猜涨跌，而是去链上查数据——看看 BTC 目前的"估值"在历史上算高还是低。

具体来说，它会：

1. **拉取 5 项核心数据**：链上估值指标 MVRV（简单理解：BTC 当前市价 vs 所有人的平均买入成本，低于 1 说明大部分人在亏钱，历史上这往往对应底部）、NVT 指标（类似股票的市盈率）、市场情绪评分、机构 ETF 资金流向、交易所 BTC 储备变化
2. **给每项数据打分**，汇总成一个 0-100 的"底部概率评分"
3. **判定信号强度**：强底部 / 温和底部 / 尚未确认
4. 如果你告诉它你的目标价（比如 20 万美元），它还会算一个**风险回报比**

**理论来源**: @monkeyjiang 的泡沫指数底部分析法 — 比特币泡沫指数跌至 10 附近是历史验证的底部信号。本工具用 MVRV + NVT + 情绪 + ETF + 储备的组合来替代原始泡沫指数。

## 怎么用？

在 Claude Code 中输入：

```
/btc-bubble-bottom-detector
```

就这么简单。工具会自动去拉数据、分析、出报告。

如果你有一个心理目标价，可以一起告诉它：

```
/btc-bubble-bottom-detector 200000 2y
```

这表示"我觉得 BTC 两年内能到 20 万美元"，工具会额外计算一个风险回报比。

**参数说明**：
| 参数 | 是否必填 | 含义 | 示例 |
|------|----------|------|------|
| 目标价 | 可选 | 你认为 BTC 未来能到的价格（美元） | 200000 |
| 时间窗口 | 可选 | 你觉得多久能到目标价 | 2y（2年）、1y、6m |

两个参数都不填也完全没问题，工具照样给你出底部评分报告。

## 会输出什么？

一份结构清晰的底部探测报告，长这样：

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
  目标价: $200,000 (2年)
  潜在收益: +207%
  历史同级别底部最大回撤: -15%
  风险回报比: 13.8:1

结论: 多项链上估值指标显示 BTC 处于历史底部区域。
MVRV < 1.0 + 机构 ETF 持续净流入 + 交易所储备下降，
与 2022 年以来历次底部的信号模式一致。当前区域适合中长线布局。
```

**评分权重说明**（为什么这么分配）：
- MVRV 比率：30 分 — 核心链上估值指标，历史上跟底部相关性最强
- NVT Golden Cross：15 分 — 类似"市盈率"的网络价值验证
- 市场情绪：15 分 — 大家都恐慌的时候往往是底部
- ETF 30 日净流入：15 分 — 机构在偷偷买入是重要信号
- 交易所储备趋势：10 分 — 大户把币从交易所提走 = 不打算卖

## 什么时候用？什么时候不适合？

**适合：**
- BTC 大跌之后，你想知道"到底了没" — 比如跌到 6 万、5 万，你犹豫要不要买
- 定期巡检（每周/每月看一次），跟踪底部信号是否在累积
- 你是中长线投资者，想找一个数据支撑的"入场区间"，而不是靠感觉

**不适合：**
- 想做短线交易 — 这个工具看的是"大周期底部"，不适合判断明天涨还是跌
- 想分析 BTC 以外的小币种 — 链上指标在小市值代币上统计意义不够
- 想精确抄到最低点 — 它只能告诉你"这个区域大概率是底部"，不能告诉你"最低是 58,327 美元"

## 前置依赖

### 为什么需要装 MCP？

这个工具需要实时的链上/市场数据才能工作。MCP（Model Context Protocol）服务器是数据来源 — 把它理解成"给 Claude 接上数据管道"。不装的话，Claude 拿不到数据，分析就跑不起来。

本工具需要以下数据（全部由 Antseer MCP 提供）：
- `ant_spot_market_structure` — BTC 实时价格
- `ant_token_analytics` — MVRV、NVT 等链上估值指标
- `ant_market_sentiment` — 市场情绪数据
- `ant_etf_fund_flow` — ETF 资金流数据
- `ant_fund_flow` — 交易所 BTC 储备数据

### MCP 服务安装

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

### 第 4 步：试一下

```
/btc-bubble-bottom-detector
/btc-bubble-bottom-detector 200000 2y
```

## 免责声明

本工具基于链上估值指标（MVRV、NVT 等）的历史统计规律进行分析，**不能精确预测底部价格或反弹时间**。底部区域可能持续数周到数月。MVRV 等指标在极端行情（黑天鹅事件）中可能失效，ETF 数据存在 T+1 延迟。分析方法论归属原作者 @monkeyjiang。**不构成投资建议。**

## License

MIT
