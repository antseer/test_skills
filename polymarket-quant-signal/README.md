# polymarket-quant-signal

Polymarket 量化多因子信号系统 — 用六层过滤器在预测市场中发现正期望值入场机会

---

## 这个工具做什么？

你在看Polymarket的BTC/ETH预测市场，想知道现在是否是"数学上值得下注"的时机。这个工具帮你做三件事：

1. **采集数据**：从BTC期货市场拉取价格历史、资金费率、Taker流向、市场情绪、布林带波动率
2. **六层过滤**：依次算KL散度（跨周期背离）→ 资金费率Z-score（定价偏差）→ 贝叶斯信号聚合（多因子融合）→ Polymarket EV缺口（隐含概率对比）→ Kelly系数（最优仓位）→ Stoikov执行价（防追高）
3. **输出信号**：告诉你当前是ALL_GREEN（可执行）、PARTIAL_N（部分满足，观望）还是NO_SIGNAL（不操作）

方法论来源：@NFTCPS 的Polymarket量化机器人策略。

---

## 怎么用？

### 基础调用（仅资金费率+KL散度+贝叶斯，无Polymarket数据）

```
/polymarket-quant-signal --symbol=BTC
```

### 完整六因子分析（需要Polymarket市场标识符）

```
/polymarket-quant-signal --symbol=BTC --market_slug=will-btc-exceed-100k-by-june-2026
```

market_slug 是Polymarket市场URL的最后一段，比如 `https://polymarket.com/event/will-btc-exceed-100k-by-june-2026` 对应的 slug 就是 `will-btc-exceed-100k-by-june-2026`。

### 带跟单钱包分析

```
/polymarket-quant-signal --symbol=BTC --trader_address=0xabc...123 --market_slug=will-btc-exceed-100k-by-june-2026
```

### 参数说明

| 参数 | 说明 | 默认值 | 可选 |
|------|------|--------|------|
| `--symbol` | 基础资产 | BTC | 是 |
| `--market_slug` | Polymarket市场标识符 | 无（跳过EV缺口计算） | 是 |
| `--trader_address` | Polygon链钱包地址（跟单分析） | 无（跳过） | 是 |
| `--kl_threshold` | KL散度触发阈值 | 0.10 | 是 |
| `--funding_zscore_threshold` | 资金费率Z-score阈值 | 2.0 | 是 |
| `--ev_min_edge` | 最小EV缺口 | 0.05 | 是 |
| `--kelly_scale` | Kelly系数缩放（控制实际仓位大小） | 0.25 | 是 |
| `--risk_aversion` | Stoikov风险厌恶系数γ | 0.10 | 是 |

---

## 会输出什么？

```
=== Polymarket 量化多因子信号报告 ===
分析时间: 2026-03-23 09:58:32 UTC
分析标的: BTC | 目标市场: will-btc-exceed-100k-by-march-2026

━━━━━ 六因子过滤结果 ━━━━━

因子          数值      阈值    状态
KL散度        0.142     >0.10   ✅ 触发（BEARISH_REVERT）
资金费率Z     +2.34     >2.0    ✅ 触发（EV方向: SHORT）
贝叶斯概率    0.71      >0.60   ✅ 触发
EV缺口        +0.08     >0.05   ✅ 触发
Kelly系数     f*=0.29   >0      ✅ 触发（实际仓位: 7.25%）
执行价格区间  等待回落  —       ❌ 暂不满足

━━━━━ 综合评估 ━━━━━

信号状态: PARTIAL_5 (5/6 过滤器通过)
建议方向: SHORT（做空 NO代币，等待入场）
建议仓位: 7.25% 账户净值
执行条件: 等待价格回落至 64,890 USDT 附近
当前建议: WAIT — 设置价格提醒 64,890 USDT
```

---

## 什么时候用？什么时候不适合？

### 适合

- 你正在参与Polymarket的BTC/ETH价格预测市场，需要量化信号辅助决策
- 你想知道当前资金费率和跨周期背离是否同时指向同一方向
- 你在研究某个Polymarket量化钱包的历史策略，想复现其逻辑
- 市场有明显的情绪偏斜（资金费率极端偏多或偏空时最有效）

### 不适合

- 你想全自动执行Polymarket交易（本工具仅输出信号，不接交易执行接口）
- 市场是非BTC/ETH类预测市场（如政治事件、天气），本工具的数据源不适用
- Polymarket市场流动性极低（KL散度和EV计算需要足够的历史数据和市场深度）
- 黑天鹅事件期间（所有统计模型在极端行情下可靠性下降）
- 你期望复现"1430美元变171万"的历史表现（原作者已指出该数据存在选择性偏差）

---

## 前置依赖

### 为什么需要装 MCP？

这个工具需要实时的期货市场数据才能工作。MCP（Model Context Protocol）服务器是数据来源 — 把它理解成"给 Claude 接上数据管道"。不装的话，Claude 拿不到BTC期货价格、资金费率等数据，六因子中的五个会无法计算。

Polymarket隐含概率通过 `https://gamma-api.polymarket.com` 公开API获取，需要网络访问权限，不依赖MCP。

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

## 免责声明

- 本 Skill 基于历史数据进行统计分析，不能预测未来市场走势
- 六因子量化方法论归属原作者 @NFTCPS，本工具为量化实现参考
- 推文所述历史绩效（$1430 → $171万）存在数据展示的选择性偏差，原作者本人已在推文末段说明
- 本 Skill 的任何输出不构成投资建议
- Polymarket 在部分司法管辖区可能存在合规限制，使用前请确认当地法规
- 使用者需自行承担基于本工具的任何投资决策风险
