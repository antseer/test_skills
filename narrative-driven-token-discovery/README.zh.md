<div align="center">

# 叙事驱动代币发现

叙事驱动代币发现 — 用社交热点关键词扫描链上匹配代币，评估叙事生命周期阶段和交易信号

[![X](https://img.shields.io/badge/关注-%40Antseer__ai-black?logo=x&logoColor=white)](https://x.com/Antseer_ai) [![Telegram](https://img.shields.io/badge/Telegram-AntseerGroup-2CA5E0?logo=telegram&logoColor=white)](https://t.me/AntseerGroup) [![GitHub](https://img.shields.io/badge/GitHub-antseer--dev-181717?logo=github&logoColor=white)](https://github.com/antseer-dev/OpenWeb3Data_MCP) [![Medium](https://img.shields.io/badge/Medium-antseer-000000?logo=medium&logoColor=white)](https://medium.com/@antseer/)

[English](README.md) | 简体中文

</div>

## 这个工具做什么？

你在刷推特时看到一个爆炸性新闻——比如"Trump 解密外星人文件"或者"Elon 又发 DOGE 推文"——第一反应是：链上有没有对应的 MEME 代币？这个代币现在处于什么阶段？聪明钱（Smart Money，指链上操作水平较高的大户钱包）有没有进场？

这个工具帮你在几十秒内回答这些问题：

1. **验证叙事热度** — 检查你输入的关键词在社交媒体上是不是真的在火，讨论量是上升还是下降
2. **扫描匹配代币** — 在链上搜索名称/符号包含关键词的代币，按流动性（Liquidity，即这个代币有多少资金可供交易）过滤掉空气币
3. **体检代币基本面** — 看持仓集中度（前 10 个钱包是不是持有 80% 以上，如果是说明风险很高）、DEX 交易活跃度、代币创建时间
4. **交叉验证 Smart Money** — 检查聪明钱有没有买入。如果聪明钱买了 + 社交热度上升 = 高信心信号
5. **判断叙事生命周期** — 综合社交趋势、价格、交易量，判断叙事处于萌芽期/爆发期/高潮期/衰退期
6. **输出信号报告** — 每个代币给一个综合评分（0-100）和操作建议（关注进场/观察等待/回避）

数据来源：AntSeer MCP 数据服务（`ant_market_sentiment`、`ant_meme`、`ant_token_analytics`、`ant_smart_money`）。

方法论来源：@thecryptoskanda（方法论拆解）和 @Clukz（原始交易方法）。

## 怎么用？

```
/narrative-driven-token-discovery Aliens
```

**参数说明：**

| 参数 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| narrative_keyword | 是 | 热点叙事关键词，中英文均可 | -- |
| chain | 否 | 目标链 | solana |
| time_window | 否 | 叙事热度评估时间窗口 | 24h |
| min_liquidity_usd | 否 | 最小流动性过滤阈值（USD） | 10000 |
| min_social_score | 否 | 最小社交热度分数阈值 | -- |
| top_n | 否 | 返回匹配代币数量上限 | 10 |

**更多示例：**

```
/narrative-driven-token-discovery DOGE
/narrative-driven-token-discovery UFO --chain=solana --top_n=5
/narrative-driven-token-discovery 伊朗 --time_window=4h --min_liquidity_usd=50000
```

## 会输出什么？

完整的结构化分析报告。下面是一个基于原推文案例的模拟输出：

```
=== 叙事驱动代币发现报告 ===
叙事关键词: Aliens / UFO
叙事热度: 78/100 (上升中)
生命周期阶段: 爆发期

| 代币     | 链     | 价格   | 流动性   | 年龄  | SM状态  | 综合评分 | 信号 |
|----------|--------|--------|----------|-------|---------|----------|------|
| ALIENS   | Solana | $0.012 | $85,000  | 2h    | 已进场  | 82       | 强   |
| UFO      | Solana | $0.003 | $32,000  | 45min | 未进场  | 58       | 中   |
| XFILES   | Solana | $0.001 | $8,000   | 15min | 未进场  | 35       | 弱   |

ALIENS — 建议关注进场机会
  叙事爆发期 + Smart Money 已进场 + 流动性充足
  注意：代币年龄仅 2h，波动性极高

UFO — 建议观察等待
  叙事匹配度高，但 Smart Money 未进场、流动性一般

XFILES — 不建议进场
  流动性不足（$8,000 低于 $10,000 阈值），无 Smart Money 验证

免责声明：本分析基于链上数据和社交信号自动生成，
不构成投资建议。MEME 代币风险极高，可能归零。
方法论归属 @thecryptoskanda / @Clukz。
```

## 什么时候用？什么时候不适合？

**适合的场景：**
- 突发新闻刚出来，你想快速查链上有没有匹配的代币
- 刷推看到一个热点话题，想在进场前做多维度评估
- 想知道聪明钱有没有已经进了某个叙事相关的代币
- 需要判断一个叙事是还在早期还是已经开始衰退

**不适合的场景：**
- 想要实时推送新代币提醒（这个工具是主动查询模式，不是实时推送流）
- 想自动下单交易（这个工具只输出信号，不连接交易所）
- 想知道精确的止盈/止损价位
- 叙事关键词是非英语的小众话题（社交数据源 LunarCrush 对非英语覆盖不足）
- 代币刚创建不到 5 分钟（可能还没被数据源收录）

## 安装

### Skill 安装

将此 Skill 添加到你的 Claude Code 环境：

```bash
claude skill add narrative-driven-token-discovery
```

### MCP 依赖安装

本 Skill 需要以下 AntSeer MCP 服务来获取实时数据。MCP（Model Context Protocol，模型上下文协议）就是给 AI 接上数据管道——不装的话 Claude 拿不到链上数据，分析就跑不起来。

#### antseer-sentiment（社交情绪数据）

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user antseer-sentiment https://mcp.antseer.com/sentiment
```

**OpenClaw / Claw**

在设置页面添加 MCP 服务器：
- 名称：`antseer-sentiment`
- URL：`https://mcp.antseer.com/sentiment`
- 传输类型：`http`

**OpenCode**

在配置文件 `opencode.json` 中添加：
```json
{
  "mcpServers": {
    "antseer-sentiment": {
      "type": "http",
      "url": "https://mcp.antseer.com/sentiment"
    }
  }
}
```

#### antseer-meme（MEME 代币数据）

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user antseer-meme https://mcp.antseer.com/meme
```

**OpenClaw / Claw**

在设置页面添加 MCP 服务器：
- 名称：`antseer-meme`
- URL：`https://mcp.antseer.com/meme`
- 传输类型：`http`

**OpenCode**

在配置文件 `opencode.json` 中添加：
```json
{
  "mcpServers": {
    "antseer-meme": {
      "type": "http",
      "url": "https://mcp.antseer.com/meme"
    }
  }
}
```

#### antseer-token-analytics（代币链上分析）

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user antseer-token-analytics https://mcp.antseer.com/token-analytics
```

**OpenClaw / Claw**

在设置页面添加 MCP 服务器：
- 名称：`antseer-token-analytics`
- URL：`https://mcp.antseer.com/token-analytics`
- 传输类型：`http`

**OpenCode**

在配置文件 `opencode.json` 中添加：
```json
{
  "mcpServers": {
    "antseer-token-analytics": {
      "type": "http",
      "url": "https://mcp.antseer.com/token-analytics"
    }
  }
}
```

#### antseer-smart-money（Smart Money 追踪）

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user antseer-smart-money https://mcp.antseer.com/smart-money
```

**OpenClaw / Claw**

在设置页面添加 MCP 服务器：
- 名称：`antseer-smart-money`
- URL：`https://mcp.antseer.com/smart-money`
- 传输类型：`http`

**OpenCode**

在配置文件 `opencode.json` 中添加：
```json
{
  "mcpServers": {
    "antseer-smart-money": {
      "type": "http",
      "url": "https://mcp.antseer.com/smart-money"
    }
  }
}
```

**通用 MCP 客户端**

任何支持 MCP 协议的客户端均可接入，核心参数：
- 情绪端点：`https://mcp.antseer.com/sentiment`
- MEME 端点：`https://mcp.antseer.com/meme`
- 代币分析端点：`https://mcp.antseer.com/token-analytics`
- Smart Money 端点：`https://mcp.antseer.com/smart-money`
- 传输类型（Transport）：`http`
- 作用域（Scope）：`user`（推荐，跨项目共享）

安装完成后，**重启你的 Agent 客户端**以激活 MCP 服务。

## 免责声明

- 本 Skill 基于 @thecryptoskanda 和 @Clukz 公开分享的交易方法论构建，方法论归属原作者
- 分析结果基于历史链上数据和社交信号，不能预测未来市场走势
- 不构成任何投资建议，具体交易决策需结合个人风险偏好和基本面判断
- MEME 代币是极高风险资产，价值可能归零，请勿投入超出承受能力的资金
- 代币搜索基于名称/符号文本匹配，可能遗漏与叙事相关但名称不含关键词的代币

---

<div align="center">

Built by [AntSeer](https://antseer.ai) · Powered by AI Agents

</div>
