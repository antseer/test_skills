# whale-control-analysis

庄家控盘度分析 -- 用链上 Holder 数据识别代币是否被单一实体高度控盘

## 这个工具做什么？

你发现某个代币短期暴涨了 30 倍，怀疑有庄家在背后操盘，但不知道怎么验证。这个工具帮你做三件事：

1. **拉取 Top Holders** -- 查出持币最多的前 50 个地址（数量可调），排除交易所、销毁钱包等公共地址
2. **地址聚类** -- 通过买入时间和资金来源分析，把表面上独立但实际上属于同一个人/机构的地址归到一起
3. **计算控盘度** -- 算出每个实体真实持有比例，关联已知做市商身份，评估合约市场操纵风险

最终输出一份结构化的 JSON 报告，告诉你：谁控盘、控多少、风险多大。

## 怎么用？

```
/whale-control-analysis SIREN ethereum
```

### 参数说明

| 参数 | 含义 | 是否必填 | 默认值 |
|------|------|----------|--------|
| symbol | 代币符号 | 必填 | -- |
| chain | 所在链 | 必填 | ethereum |
| token_address | 合约地址（精确查询） | 可选 | -- |
| top_n | 分析前多少名持有者 | 可选 | 50 |
| time_window_days | 聚类时间窗口（天） | 可选 | 14 |
| known_addresses | 额外排除的公共地址 | 可选 | 内置列表 |
| control_threshold | 告警阈值 | 可选 | 0.5 |

### 更多用法示例

```
# 分析 Solana 上的代币，扩大到前 100 名持有者
/whale-control-analysis BONK solana --top_n=100

# 用合约地址精确查询，缩短聚类窗口到 7 天
/whale-control-analysis SIREN ethereum --token_address=0x... --time_window_days=7
```

## 会输出什么？

以下是基于 $SIREN 案例的模拟输出：

```json
{
  "symbol": "SIREN",
  "chain": "ethereum",
  "total_supply": 7276836158,
  "circulating_supply": 7276836158,
  "analyzed_holders": 54,
  "excluded_addresses": [
    {"address": "0x000...dead", "reason": "burn wallet", "rank": 1},
    {"address": "0xBinance...", "reason": "Binance Web3 wallet", "rank": 3}
  ],
  "entities": [
    {
      "entity_id": "entity_001",
      "addresses_count": 52,
      "total_holding": 6440000000,
      "control_ratio": 0.885,
      "suspected_identity": "DWF Labs",
      "confidence": "medium",
      "evidence": [
        "DWF Labs public wallet holds 3M SIREN",
        "DWF Labs SIREN transfer followed by 66.5% token consolidation next day",
        "All 52 addresses first bought in late June to early July 2025",
        "48 addresses participated in consolidation event"
      ]
    }
  ],
  "hhi_index": 0.784,
  "top_entity_control_ratio": 0.885,
  "risk_level": "Extreme risk",
  "futures_correlation": {
    "has_perp": true,
    "oi_value": "refer to live data",
    "funding_rate": "refer to live data",
    "manipulation_risk": "high -- 88.5% spot control + active perpetual market"
  },
  "data_limitations": [
    "On-chain only; CEX internal holdings not included",
    "Entity identity is inferred, not legally confirmed"
  ],
  "summary": "SIREN on-chain control ratio 88.5%, top 54 addresses with 52 attributed to one entity (suspected DWF Labs), extreme risk."
}
```

## 什么时候用？什么时候不适合？

### 适合的场景

- 某代币短期暴涨/暴跌，想排查是否有庄家控盘
- 发现某代币出现大规模代币归集（很多地址同时往一个地址转币）
- 准备投资某代币前，想了解筹码集中度
- 风控需要评估某代币的操纵风险

### 不适合的场景

- 想分析 CEX 内部持仓（链上工具看不到交易所内部数据）
- 需要法律层面确认某机构身份（本工具只能做推断，不是法律证据）
- 想预测价格走势或获取交易信号（这不是交易工具）
- 分析非 EVM 链代币时，数据覆盖度可能不完整

## 前置依赖

### 为什么需要装 MCP？

这个工具需要实时的链上数据才能工作。MCP（Model Context Protocol）服务器是数据来源 -- 把它理解成"给 Claude 接上数据管道"。不装的话，Claude 拿不到数据，分析就跑不起来。

本 Skill 依赖以下 4 个 MCP 服务：

- **ant_meme** -- 代币基础信息（供应量、价格、市值）
- **ant_token_analytics** -- Top Holders 列表
- **ant_address_profile** -- 地址标签、交易历史、关联钱包
- **ant_futures_market_structure** -- 永续合约 OI、资金费率、多空比

### MCP 服务安装

#### ant_meme

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user ant-meme https://mcp.antseer.com/ant_meme
```

**OpenClaw / Claw**

在设置页面添加 MCP 服务器，填写：
- 名称：`ant-meme`
- URL：`https://mcp.antseer.com/ant_meme`
- 传输类型：`http`

**OpenCode**

在配置文件 `opencode.json` 中添加：
```json
{
  "mcpServers": {
    "ant-meme": {
      "type": "http",
      "url": "https://mcp.antseer.com/ant_meme"
    }
  }
}
```

#### ant_token_analytics

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user ant-token-analytics https://mcp.antseer.com/ant_token_analytics
```

**OpenClaw / Claw**

在设置页面添加 MCP 服务器，填写：
- 名称：`ant-token-analytics`
- URL：`https://mcp.antseer.com/ant_token_analytics`
- 传输类型：`http`

**OpenCode**

在配置文件 `opencode.json` 中添加：
```json
{
  "mcpServers": {
    "ant-token-analytics": {
      "type": "http",
      "url": "https://mcp.antseer.com/ant_token_analytics"
    }
  }
}
```

#### ant_address_profile

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user ant-address-profile https://mcp.antseer.com/ant_address_profile
```

**OpenClaw / Claw**

在设置页面添加 MCP 服务器，填写：
- 名称：`ant-address-profile`
- URL：`https://mcp.antseer.com/ant_address_profile`
- 传输类型：`http`

**OpenCode**

在配置文件 `opencode.json` 中添加：
```json
{
  "mcpServers": {
    "ant-address-profile": {
      "type": "http",
      "url": "https://mcp.antseer.com/ant_address_profile"
    }
  }
}
```

#### ant_futures_market_structure

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user ant-futures-market-structure https://mcp.antseer.com/ant_futures_market_structure
```

**OpenClaw / Claw**

在设置页面添加 MCP 服务器，填写：
- 名称：`ant-futures-market-structure`
- URL：`https://mcp.antseer.com/ant_futures_market_structure`
- 传输类型：`http`

**OpenCode**

在配置文件 `opencode.json` 中添加：
```json
{
  "mcpServers": {
    "ant-futures-market-structure": {
      "type": "http",
      "url": "https://mcp.antseer.com/ant_futures_market_structure"
    }
  }
}
```

**通用 MCP 客户端**

任何支持 MCP 协议的客户端均可接入，核心参数：
- MCP 端点：见上方各服务 URL
- 传输类型（Transport）：`http`
- 作用域（Scope）：`user`（推荐，跨项目共享）

安装完成后，**重启你的 Agent 客户端**以激活 MCP 服务。

## 分析方法论来源

本 Skill 的分析方法论基于链上分析师 @EmberCN 的 $SIREN 控盘分析推文。核心方法（Holder 集中度聚类 + 实体身份关联 + 合约市场关联推断）归属原作者。

## 免责声明

- 本工具基于历史链上数据进行分析，不能预测未来价格走势
- 分析方法论归属原作者 @EmberCN，本工具将其通用化和自动化
- 实体身份关联为技术推断，不构成对任何个人或机构的指控
- 链上控盘度可能低估实际控盘（CEX 内部持仓不可见）
- 不构成投资建议，使用者需自行判断风险
