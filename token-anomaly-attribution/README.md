# token-anomaly-attribution

代币异动归因框架分析 — 用链上数据和衍生品结构排查代币暴涨暴跌的真实原因，帮你判断"该追、该跑还是等等看"

---

## 这个工具做什么？

你遇到过这种情况吗：某个代币突然暴涨 30%，刷屏都是"要上天了"，你追进去结果被套在山顶。或者暴跌 20%，你恐慌割了，结果是假摔。

问题不在于你胆子大还是小，而在于你不知道**为什么涨/跌**。原因不同，操作策略完全相反：

1. **大盘带飞**？那 BTC 一回调你也跟着跌，跑得越快越好
2. **鲸鱼增持 + Smart Money 流入**？那是真有资金在推，持续性强
3. **KOL 喊单 + 情绪爆炸**？那是末段效应，追进去大概率站岗

这个工具帮你做的是：用 Antseer MCP 的链上数据，自动跑完 9 个分析维度，10 分钟内给你一份结构化归因报告。

---

## 怎么用？

```
/token-anomaly-attribution HYPE
```

带参数版本：
```
/token-anomaly-attribution HYPE --direction=pump --time_range=7d --chain=hyperliquid --token_address=0x... --threshold_pct=15
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| symbol | 是 | — | 代币符号，如 HYPE、BTC、ETH |
| direction | 否 | auto | 异动方向：pump（涨）/ dump（跌）/ auto（自动判断） |
| time_range | 否 | 7d | 分析时间窗口：24h / 7d / 30d |
| chain | 否 | auto | 链名称：hyperliquid / eth / bsc 等 |
| token_address | 否 | — | 合约地址，填了可以拿到更精确的持仓数据 |
| threshold_pct | 否 | 10.0 | 价格异动阈值（%），低于此值会提示"异动幅度不显著" |

---

## 会输出什么？

```markdown
## HYPE 异动归因分析报告

分析时间窗口: 7d  |  价格变化: +35%  |  异动方向: pump

### 市场背景
- BTC 同期表现: +5%
- 联动系数 (β): 0.14 → 个币独立行情，非市场普涨带动

### 归因因素评估

| # | 归因因素 | 信号强度 | 数据来源 | 持续性 |
|---|---------|---------|---------|-------|
| 1 | 产品升级（HIP-4 预测市场基础设施） | ⚠️ 待核实 | 需查项目公告 | 高（如落地） |
| 2 | 合作推动（Ripple Prime 接入） | ⚠️ 待核实 | 需查新闻源 | 高 |
| 3 | 销毁/回购（手续费回购 HYPE） | ✅ 链上确认 | flow_intelligence | 中高 |
| 4 | 预期上所（韩国交易所） | ⚠️ 待核实 | 需查交易所公告 | 低（事件驱动） |
| 5 | Smart Money 净流入 | ✅ 链上确认 | ant_smart_money | 高 |
| 6 | 鲸鱼未见集中出货 | ✅ 链上确认 | ant_token_analytics | — |
| 7 | 资金费率健康（未过热，0.012%） | ✅ 衍生品确认 | futures_funding_rate | — |

**量化数据摘要**
| 指标 | 数值 | 含义 |
|------|------|------|
| 鲸鱼行为 | accumulate | 持续增持 |
| 交易所净流量(7d) | -12,400 HYPE | 净流出，持有意愿强 |
| OI 变化 | +18% | OI 随价格上升，结构健康 |
| 资金费率 | 0.012% | 正常区间，未过热 |
| Smart Money 方向 | inflow | 净流入 |
| RSI(14) | 68 | 偏高但未进超买区 |
| 情绪评分 | 74/100 | 较热，注意是否已到顶 |
| ETF 资金流(7d) | N/A | 非 BTC/ETH，跳过 |

**需人工核查的非量化因素**:
- HIP-4 提案是否通过？（治理数据无法自动获取）
- Ripple Prime 合作公告是否官方确认？
- 韩国交易所上架时间是否确定？

### 行情持续性评级: MEDIUM-HIGH
### 建议操作方向: verify_first（等待公告核实后再入场，或小仓试探）

### 后续跟踪观察点
1. HIP-4 提案最终通过时间
2. 交易量能否维持近 7 日高位（建议每 24h 检查一次）
3. 特拉华州 ETF 注册进展
4. 资金费率是否持续走高（>0.05% 开始过热预警）
5. 鲸鱼是否出现大额转入交易所行为

---
免责声明：分析方法论归属 @Guolier8，基于历史数据不构成投资建议。
```

---

## 什么时候用？什么时候不适合？

### 适合的场景

- 代币单日涨跌超过 10%，想快速了解涨跌原因
- 朋友圈/群里突然爆出某个代币暴拉，想判断是真信号还是拉盘割韭菜
- 持仓代币出现异动，判断是否需要减仓或加仓
- 定期做投研报告，需要量化的链上数据支撑

### 不适合的场景

- 稳定币（USDT、USDC）— 没有价格异动可分析
- 刚上线的新代币（< 30 天）— 链上历史数据不足
- 想要精确预测明天会涨多少 — 这个工具告诉你"为什么"，不预测"多少"
- 极端市场崩盘时刻 — 链上数据延迟可能导致分析滞后 30 分钟以上

---

## 前置依赖

### 为什么需要装 MCP？

这个工具需要实时的链上和市场数据才能工作。MCP（Model Context Protocol，模型上下文协议）服务器是数据来源 — 把它理解成"给 Claude 接上数据管道"。不装的话，Claude 拿不到数据，分析就跑不起来。

### MCP 服务安装：Antseer

Antseer 提供链上资金流、衍生品数据、Smart Money 追踪、情绪分析等核心数据源。

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user antseer https://mcp.antseer.io/mcp
```

**OpenClaw / Claw**

在设置页面添加 MCP 服务器，填写：
- 名称：`antseer`
- URL：`https://mcp.antseer.io/mcp`
- 传输类型：`http`

**OpenCode**

在配置文件 `opencode.json` 中添加：
```json
{
  "mcpServers": {
    "antseer": {
      "type": "http",
      "url": "https://mcp.antseer.io/mcp"
    }
  }
}
```

**通用 MCP 客户端**

任何支持 MCP 协议的客户端均可接入，核心参数：
- MCP 端点：`https://mcp.antseer.io/mcp`
- 传输类型（Transport）：`http`
- 作用域（Scope）：`user`（推荐，跨项目共享）

安装完成后，**重启你的 Agent 客户端**以激活 MCP 服务。

### 工具调用清单

本 Skill 使用以下 Antseer MCP 工具：

| 工具 | 用途 |
|------|------|
| ant_spot_market_structure | 代币与 BTC 价格对比 |
| ant_fund_flow | 交易所资金净流量、鲸鱼大额转账 |
| ant_token_analytics | Top Holders 持仓变化、链上资金流向 |
| ant_smart_money | Smart Money 净流向、持仓、DEX 交易 |
| ant_futures_market_structure | OI 变化、资金费率 |
| ant_market_indicators | RSI、MACD 技术指标 |
| ant_market_sentiment | 社交情绪评分、话题热度 |
| ant_etf_fund_flow | BTC/ETH ETF 资金净流入（仅适用于 BTC/ETH） |

---

## 免责声明

- 本 Skill 的归因框架基于 @Guolier8 的公开推文方法论，方法论版权归原作者所有
- 所有分析基于历史链上和市场数据，不能预测未来价格走势
- 部分归因因素（安全事件、合作公告、上所信息）无法自动验证，需人工核查
- 不构成任何形式的投资建议，最终操作决策需结合个人风险偏好自行判断
