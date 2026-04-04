# cex-volume-authenticity-analyzer

CEX 交易量真实性评估器 — 用 Hyperliquid 链上基准检测主流交易所刷量水分，重算真实市场份额

---

## 这个工具做什么？

你想知道 "Binance、OKX、MEXC 公布的月度交易量，哪家是真实的，哪家掺了水分？"

这个工具帮你：

1. 从 Hyperliquid（最大的链上永续合约 DEX）拿到一个"诚实交易基准"——每笔交易都需要真实 USDC 保证金，几乎不可能造假，把它的资金效率比率（日均交易量 ÷ 储备）当作天花板
2. 对每家 CEX 计算相同的资金效率比率，超出阈值（基准 × 1.15）的部分就是估算的可疑水分
3. 剔除可疑水分后，重新计算各交易所在样本内的真实市场份额
4. 标注 BTC 超额储备情况（储备率 >150% 的交易所，可疑水分判定偏保守）
5. 输出结构化报告，给出可信阈值评级（高度可信 / 正常范围 / 灰色地带 / 高度可疑）

方法论来源：@agintender（2026-03-30 推文），原始案例分析了 Binance、OKX、Bybit、Bitget、Gate.io、MEXC、KuCoin、HTX 八大 CEX。

---

## 怎么用？

```
/cex-volume-authenticity-analyzer exchanges=["Binance","OKX","Bybit","Bitget","Gate.io","MEXC","KuCoin","HTX"]
```

精简版（分析两家对比）：

```
/cex-volume-authenticity-analyzer exchanges=["MEXC","Binance"]
```

完整参数示例：

```
/cex-volume-authenticity-analyzer exchanges=["Binance","OKX","Bybit"] benchmark_dex=Hyperliquid time_range_days=30 tolerance_pct=15
```

**参数说明：**

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| exchanges | 是 | — | 需要分析的 CEX 列表 |
| benchmark_dex | 否 | Hyperliquid | 链上基准 DEX |
| time_range_days | 否 | 30 | 分析时间窗口（天）|
| tolerance_pct | 否 | 15 | CEX 宽容系数（%）；设为 0 则与 Hyperliquid 同等标准 |
| reserve_assets | 否 | ["BTC","ETH","USDT","USDC"] | 计算储备分母的核心资产 |

**注意**：30 天现货交易量目前 MCP 未覆盖，工具会提示你从 Newhedge 或 CoinGecko 手动提供数据。可以直接粘贴格式为 `exchange,spot_30d,deriv_30d` 的 CSV 数据。

---

## 会输出什么？

下面是一个完整的模拟输出示例（基于 @agintender 原始案例，2026年2-3月数据）：

```
=== CEX 交易量真实性评估报告 ===
分析周期: 2026-02-01 ~ 2026-03-02 (30天)
基准 DEX: Hyperliquid | 基准比率: 1.44x | 可信阈值: 1.66x
数据来源: 储备=Antseer MCP, 现货量=Newhedge, 衍生品量=CoinGlass快照

| 交易所   | 核心储备  | 报告30天总量 | 总比率  | 评级    | 可疑交易量估算          |
|---------|---------|------------|--------|---------|----------------------|
| Binance | ~$4,000亿 | $1,459亿  | 0.44x  | 高度可信  | $0                  |
| OKX     | ~$800亿  | $644亿    | 0.97x  | 高度可信  | $0                  |
| Bybit   | ~$500亿  | $469亿    | 1.13x  | 高度可信  | $0                  |
| Bitget  | ~$300亿  | $378亿    | 1.33x  | 正常范围  | $0                  |
| Gate.io | ~$150亿  | $293亿    | 2.03x  | 灰色地带  | ~$540亿 (约18%)      |
| MEXC    | ~$250亿  | $361亿    | 2.95x  | 高度可疑  | ~$2,010亿 (约56%)    |
| KuCoin  | ~$200亿  | $200亿    | 1.80x  | 灰色地带  | ~$400亿 (约20%)      |
| HTX     | ~$200亿  | $200亿    | 1.20x  | 高度可信  | $0                  |

=== 市场份额对比（八大 CEX 样本内） ===
| 交易所   | 报告份额 | 调整后份额 | 变化    |
|---------|---------|----------|--------|
| Binance | 39.1%   | 45.7%    | +6.6pp |
| OKX     | 17.3%   | 17.3%    | —      |
| Bybit   | 12.6%   | 12.6%    | —      |
| MEXC    | 9.7%    | 5.0%     | -4.7pp |
| Gate.io | 7.9%    | 7.5%     | -0.4pp |

=== 关键发现 ===
- Binance、OKX、Bybit 数据可信，调整后份额明显提升
- MEXC 比率 2.95x，超阈值 78%，高度可疑
- 剔除水分后 Binance 实际份额比报告高约 6.6pp

=== 局限性说明 ===
- 现货量来自 Newhedge，衍生品量为 CoinGlass 快照估算，非精确历史数据
- 储备数据为交易所自我披露，若有低报则可疑量被高估
- 高比率可能来自 0 手续费活动而非系统性造假，需人工判断

⚠️ 注：本分析仅覆盖样本内 CEX，不代表全市场份额。
```

---

## 什么时候用？什么时候不适合？

**适合使用的场景：**
- 项目方在选所上币时，想量化对比各交易所的交易量可信度
- 投研人员做月度竞品情报，追踪主流 CEX 真实市场地位变化
- 监管或合规研究者需要 CEX 刷量程度的统计学参考数据
- 量化交易员在分析市场深度和滑点时，想排除虚假量干扰

**不适合使用的场景：**
- 需要对单笔刷量行为提供法律级别的证据（本工具仅为统计信号）
- 需要实时监控（本工具设计为月度快照分析，不适合高频使用）
- 分析中小/无名 CEX（无公开 PoR 数据，储备无法获取）
- 需要预测某交易所会不会因刷量被监管处罚（超出本工具范围）

---

## 前置依赖

### 为什么需要装 MCP？

这个工具需要实时的链上储备数据、DEX TVL 数据和资产价格才能工作。MCP（Model Context Protocol）服务器是数据来源——把它理解成"给 Claude 接上数据管道"。不装的话，Claude 拿不到储备数据，分析就跑不起来。

本工具使用的 MCP 工具：
- `ant_fund_flow`（exchange_reserve、exchange_netflow）— 各交易所核心资产储备和净流量
- `ant_protocol_tvl_yields_revenue`（protocol_tvl、dex_overview）— Hyperliquid TVL 和交易量基准
- `ant_spot_market_structure`（simple_price）— BTC/ETH/USDT/USDC 实时价格

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

本 Skill 基于历史数据进行统计分析，资金效率比率历史规律不能预测未来交易量走势。分析方法论归属原作者 @agintender，本工具为其方法论的通用化实现，不代表原作者的投资建议。

对任何交易所的可信度评级均为统计模型输出，不代表对其经营合规性的法律判断，更不构成任何形式的投资建议。高资金效率比率可能来自正常商业活动（0手续费、做市商激励等）而非系统性造假，最终判断须结合人工背景信息。
