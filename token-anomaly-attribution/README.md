# token-anomaly-attribution

代币异动归因分析 — 用链上数据和衍生品结构排查代币暴涨暴跌的真实原因，输出信号质量评级（A/B/C）帮你判断"该追、该跑还是等等看"

---

## 这个工具做什么？

你遇到过这种情况吗：某个代币突然暴涨 30%，刷屏都是"要上天了"，你追进去结果被套在山顶。或者暴跌 20%，你恐慌割了，结果是假摔。

问题不在于你胆子大还是小，而在于你不知道**为什么涨/跌**。原因不同，操作策略完全相反：

1. **大盘带飞**？那 BTC 一回调你也跟着跌，跑得越快越好
2. **鲸鱼增持 + Smart Money 流入**？那是真有资金在推，持续性强
3. **KOL 喊单 + 情绪爆炸**？那是末段效应，追进去大概率站岗

这个工具帮你做的是：用 Ant-on-Chain MCP 的链上数据，自动跑完 8 个分析维度，给你一份结构化归因报告，含信号质量 A/B/C 评级和行动建议。

**8 个分析维度：**
1. 价格异动确认（是否达到分析阈值）
2. 大盘 Beta 剔除（排除 BTC/ETH 联动干扰）
3. 链上鲸鱼行为（大户积累 vs 出走）
4. Smart Money 动向（聪明钱净流向）
5. 社交情绪与叙事（KOL 效应 vs 真实利好）
6. ETF 与机构资金流（仅 BTC/ETH）
7. 衍生品杠杆结构（OI、资金费率、多空比）
8. 综合归因评估（信号质量评级 + 行动建议）

---

## 怎么用？

最简版本：
```
/token-anomaly-attribution HYPE
```

带参数版本：
```
/token-anomaly-attribution HYPE --time_range=24h --price_change_threshold=15 --analysis_mode=auto --chain=hyperliquid --token_address=0x...
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| symbol | 是 | — | 代币符号，如 HYPE、BTC、ETH |
| time_range | 否 | 24h | 分析时间窗口：24h / 7d / 30d |
| price_change_threshold | 否 | 15 | 异动阈值（%），绝对值超过此值才触发深度分析 |
| analysis_mode | 否 | auto | surge（只看涨因素）/ dump（只看跌因素）/ auto（自动判断） |
| chain | 否 | auto | 链名称：hyperliquid / ethereum / solana 等 |
| token_address | 否 | — | 合约地址，填写后可拿到更精确的 Holders 和资金流数据 |

---

## 会输出什么？

```markdown
## HYPE 代币异动归因分析报告

**分析时间**: 2026-04-03  **时间窗口**: 7d  **分析模式**: auto

### 价格背景
- HYPE 7日涨幅: +35%
- BTC 同期涨幅: +8%
- 大盘 Beta 贡献率: ~23%  ✦ 存在明显个币 Alpha

### 已量化确认的驱动因素

| 因素类别 | 信号来源 | 具体表现 | 评级 |
|----------|----------|----------|------|
| 鲸鱼行为 | ant_token_analytics | 前10 Holders 持仓稳定，无明显抛售 | 中性偏多 |
| 交易所流向 | ant_fund_flow | 净流出增加，积累信号 | ✅ 正向 |
| Smart Money | ant_smart_money | 净流入增加 | ✅ 正向 |
| 社交热度 | ant_market_sentiment | 7日话题量 +180%，略高于均值 | ⚠️ 情绪助推（中） |
| 衍生品结构 | ant_futures_market_structure | OI 上升，资金费率 +0.04%（适中） | ✅ 无过热风险 |

**量化数据摘要**
| 指标 | 数值 | 信号含义 |
|------|------|---------|
| 鲸鱼行为 | accumulate | 持续增持 |
| 交易所净流量 | -12,400 HYPE | 净流出，持有意愿强 |
| OI 变化 | +18% | 随价格上升，结构健康 |
| 当前资金费率 | +0.04% | 正常区间，未过热 |
| 多空比 | 1.3 | 多头略占优，未极端 |
| Smart Money 方向 | Bullish | 净流入 |
| 情绪评分 | 74/100 | 较热，注意是否已到顶 |
| ETF 资金流 | 不适用 | 非 BTC/ETH |

### 需人工核实的驱动因素
- ⚠️ HIP-4 提案（链上原生结果交易基础设施）是否通过？建议核查官方 GitHub/Discord
- ⚠️ Ripple Prime 接入公告是否官方确认？建议核查官方 PR/新闻稿
- ⚠️ 韩国交易所现货上架时间是否确定？建议确认官方消息来源

### 综合信号质量: A — 多因子叠加
量化数据显示 3 项正向信号，叠加多项待核实正向因素，涨势持续性较高。

### 行动建议: 持仓等待（等公告核实后再决策）

### 后续跟踪指标
1. HIP-4 提案最终通过时间
2. 交易量能否维持近 7 日高位（>均值 80%）
3. 资金费率是否进入极端区间（>0.1%）
4. 鲸鱼是否出现大额转入交易所行为

---
数据截止: 2026-04-03 12:00 UTC
免责声明：分析方法论归属 @Guolier8，基于历史数据不构成投资建议。
```

---

## 什么时候用？什么时候不适合？

### 适合的场景

- 代币单日涨跌超过 15%，想快速了解涨跌原因
- 社群突然爆出某个代币暴拉，想判断是真信号还是拉盘割韭菜
- 持仓代币出现异动，判断是否需要减仓或加仓
- 定期做投研报告，需要量化的链上数据支撑

### 不适合的场景

- 稳定币（USDT、USDC）— 没有价格异动可分析
- 刚上线的新代币（< 30 天）— 链上历史数据不足，分析结果不可靠
- 想要精确预测明天会涨多少 — 这个工具告诉你"为什么"，不预测"多少"
- 极端市场崩盘时刻 — 链上数据延迟可能导致分析滞后，建议数据稳定后再跑
- 非主流链上的小市值代币 — 链上数据覆盖不足，Smart Money 和 Holders 分析不可用

---

## 前置依赖

### 为什么需要装 MCP？

这个工具需要实时的链上和市场数据才能工作。MCP（Model Context Protocol，模型上下文协议）服务器是数据来源 — 把它理解成"给 Claude 接上数据管道"。不装的话，Claude 拿不到数据，分析就跑不起来。

### MCP 服务安装：Ant-on-Chain MCP

Ant-on-Chain 提供链上资金流、衍生品数据、Smart Money 追踪、情绪分析等核心数据源。

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

### 工具调用清单

本 Skill 使用以下 Ant-on-Chain MCP 工具：

| 工具 | query_type | 用途 |
|------|-----------|------|
| ant_spot_market_structure | coins_markets | 代币与 BTC/ETH 价格对比 |
| ant_token_analytics | holders | Top Holders 持仓变化（需 token_address） |
| ant_token_analytics | flow_intelligence | 链上资金流向情报（需 token_address） |
| ant_fund_flow | exchange_netflow | 交易所资金净流量 |
| ant_fund_flow | centralized_exchange_whale_transfer | 鲸鱼大额转账记录 |
| ant_smart_money | netflows | Smart Money 净流向 |
| ant_smart_money | holdings | Smart Money 持仓变化 |
| ant_market_sentiment | coin_detail | 代币社交情绪评分 |
| ant_market_sentiment | topic_detail | 社交话题热度趋势 |
| ant_etf_fund_flow | btc_etf_flow / eth_etf_flow | ETF 资金流（仅 BTC/ETH） |
| ant_futures_market_structure | futures_oi_aggregated | 合约未平仓量变化 |
| ant_futures_market_structure | futures_funding_rate_current | 当前资金费率 |
| ant_futures_market_structure | futures_long_short_ratio | 多空持仓比 |

---

## 免责声明

- 本 Skill 的归因框架基于 @Guolier8 的公开推文方法论（https://x.com/Guolier8/status/2039996241762001198），方法论版权归原作者所有
- 所有分析基于历史链上和市场数据，不能预测未来价格走势
- 部分归因因素（安全事件、合作公告、上所信息、产品升级）无法自动验证，需人工核查
- 不构成任何形式的投资建议，最终操作决策需结合个人风险偏好自行判断
