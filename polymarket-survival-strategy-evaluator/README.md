# polymarket-survival-strategy-evaluator

Polymarket 存活策略评估与仓位管理计算器 —— 用蒙特卡洛回测结论检验你的策略，计算 EV 和 Kelly 仓位，给出 ALL CLEAR / 谨慎 / 别交易 的明确判断。

---

## 这个工具做什么？

研究人员对 Polymarket 跑了 10000 次蒙特卡洛模拟，结论是：**97% 的交易者会死**（本金亏损超 80%）。死亡不是因为运气差，是因为策略类型本身就没有胜算。

这个工具帮你做三件事：

1. **检查你的策略是不是"死亡模式"**：动量交易（94.2% 死）、凭直觉/新闻（91.7% 死）、跟单大户（88.3% 死）、价差套利（79.1% 死）—— 四类高死亡率模式逐一对照
2. **算清楚你能不能赚钱**：用公式算出期望值（EV），EV > 0 才值得继续看；顺带算出你的概率优势（Edge）
3. **算出应该押多少钱**：用 Kelly 公式算出最优仓位，默认用 1/4 Kelly 保守系数，设置单笔上限防止过度集中

Polymarket 的核心规律：猜对了不够，下注大小也要对 —— EV × Kelly 双重正确才能存活。

---

## 怎么用？

### 基本调用格式

```
/polymarket-survival-strategy-evaluator \
  --strategy_type=insurance \
  --market_question="Will BTC exceed $100K by end of Q2 2026?" \
  --market_yes_price=0.12 \
  --your_true_prob=0.05 \
  --bankroll=10000
```

### 参数说明

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `strategy_type` | 是 | 策略类型：`insurance`（保险模型）/ `sports_quant`（体育量化）/ `bayesian_arb`（贝叶斯套利）/ `custom`（自定义） | `insurance` |
| `market_question` | 是 | Polymarket 上的市场问题，原文粘贴 | `"Will BTC exceed $100K?"` |
| `market_yes_price` | 是 | YES 的当前市场价格，从 Polymarket 页面读取，0到1之间的小数 | `0.12`（即 12 美分） |
| `your_true_prob` | 是 | 你自己估算的真实概率，你认为 YES 发生的概率 | `0.05` |
| `bankroll` | 是 | 你的总本金，单位美元 | `10000` |
| `market_type` | 否 | `crypto` / `politics` / `sports` / `macro` / `other`，默认 `other` | `crypto` |
| `edge_description` | 否 | 你的优势描述：你凭什么认为你的概率比市场准 | `"基于链上数据模型"` |
| `kelly_fraction` | 否 | Kelly 系数，1 是全 Kelly，0.25 是 1/4 Kelly（默认，保守） | `0.25` |
| `max_position_pct` | 否 | 单笔最大仓位占本金的比例上限，默认 5% | `0.05` |

---

## 会输出什么？

下面是一个完整的保险模型分析示例输出：

```
📊 Polymarket 策略评估报告
═══════════════════════════════════════

市场: "Will XYZ token get listed on Binance in Q2 2026?"
策略类型: 保险模型 (Insurance Model)

【策略健康检查】
✅ SAFE — 买 NO 在 95 美分，符合保险模型特征（NO 价格在 88-98 区间）
  参考案例：LucasMeow 148胜0负，盈利 $275K

【期望值计算】
• 市场 YES 价格: 0.05（买的是 NO = 0.95）
• 你估算的真实 NO 概率: 0.97
• EV: +0.0211（正期望 ✅）
• Edge: +0.02（概率优势 +2.0%）

【Kelly 仓位建议】
• 全 Kelly: 4.2% of bankroll
• 1/4 Kelly（保守）: 1.05% of bankroll
• 建议下注: $105 / $10,000 本金
• 最大单笔上限（5%）: $500（不触发）

【四条件核查】
✅ 每笔正期望值 (EV = +0.0211)
✅ Kelly 仓位管理（1/4 Kelly = 1.05%）
✅ 模型驱动（基于项目基本面评估，非直觉）
⚠️ 结构性优势（描述较模糊，建议补充具体不可复制的能力）

综合评级: ⚠️ CAUTION（3/4 条件满足）

【建议】
PROCEED WITH CAUTION — 可以执行，但需补强结构性优势：
1. 明确你的信息优势来源（为何你的 NO 概率估算优于市场）
2. 保持 1/4 Kelly，不要全仓
3. 建立 100+ 笔记录后评估整体胜率

⚠️ 风险提示:
• 保险模型需要大样本（100+ 笔）才能体现统计优势，单笔结果意义不大
• ant_market_sentiment 情绪数据仅作辅助参考，不直接影响 EV 计算
```

---

## 什么时候用？什么时候不适合？

### 适合

- 你在 Polymarket 上发现了一个"可能低估风险"的市场，想知道买 NO 值不值
- 你有一套自己的概率估算模型，想验证它相对于市场定价是否有优势
- 你想搞清楚自己的策略究竟属于哪类，有没有历史存活先例
- 你要做 Kelly 仓位计算，不想拍脑袋决定押多少
- 你是贝叶斯套利类型的玩家，需要确认信息优势是否足够支撑仓位

### 不适合

- 你没有自己的概率估算（`your_true_prob` 是随便填的），工具输出没有意义
- 你想要实时 Polymarket 价格抓取 —— 需要手动从 Polymarket 页面读取价格
- 你在做体育量化策略，需要球员疲劳度/气象数据 —— 本工具不提供体育数据
- 你想要贝叶斯套利的自动触发系统 —— 仅提供分析，不执行自动化交易
- 你想预测 Polymarket 市场的最终结果 —— 工具分析策略合理性，不预测结果

---

## 前置依赖

### 为什么需要装 MCP？

部分分析（crypto 类市场情绪辅助、贝叶斯套利话题热度监控）需要实时数据。MCP（Model Context Protocol）服务器是数据来源 —— 把它理解成"给 Claude 接上数据管道"。EV 和 Kelly 计算不依赖 MCP（纯数学公式），但如果你分析的是 crypto 类 Polymarket 市场，安装 MCP 后可以获得辅助情绪参考。

### MCP 服务安装

#### ant-on-chain-mcp

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

---

## 理解三类存活策略

### 保险模型（Insurance Model）—— 存活率 71.4%

原理：在 88-98 美分买入 NO，充当"保险提供方"，对方支付风险溢价给你。

核心要求：YES 价格必须在 0.02-0.12 区间（即 NO = 88-98 美分）。不在区间内则风险溢价不足。需要大量重复（100+ 笔）才能体现统计优势，单笔结果波动很大。

### 体育/事件量化（Sports Quant）—— 存活率 68.9%

原理：融合气象、球员疲劳指数、历史赛果分布，建立统计模型，找到市场定价与真实概率的偏差。

核心要求：必须有外部数据支撑（ESPN API、SportsRadar API、气象 API 等）。纯凭"感觉谁会赢"不算量化。

### 贝叶斯事件套利（Bayesian Arb）—— 存活率 64.2%（天花板最高）

原理：突发消息出现后，在市场反应过来的 3-5 分钟内抢先更新概率并下注。

核心要求：信息处理速度必须快过市场，通常需要自动化系统。手动操作几乎无法捕捉 3-5 分钟窗口。收益天花板最高但单次波动也最大。

---

## 免责声明

本工具基于 @NFTCPS（2026-03-23）的蒙特卡洛模拟研究方法论生成，分析方法论归属原作者。

- 分析结论基于历史回测数据（97% 死亡率来自模拟），不能预测未来实际交易结果
- EV 和 Kelly 计算的准确性完全取决于用户提供的 `your_true_prob`，工具无法验证概率估算的质量
- 正 EV 策略在短期内仍可能亏损，需要足够样本量才能体现统计优势
- Polymarket 交易存在本金损失风险，在部分司法管辖区可能存在合规限制
- 本工具不构成投资建议，请根据自身风险承受能力做出决策
