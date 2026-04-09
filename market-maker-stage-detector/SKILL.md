---
name: market-maker-stage-detector
description: |
  庄家阶段识别器 — 输入任意代币合约地址，通过 6 维链上信号框架判断庄家所处阶段（吸筹/拉升/出货/已跑），生成可视化分析报告。
  需要 Antseer MCP 服务器。
  Use when asked to: 庄家分析, 控盘检测, 筹码分析, 有没有庄, 庄在哪个阶段, 这个币安全吗,
  market maker detection, whale control analysis, chip concentration, is this token safe,
  analyze token holders, 看看这个币的筹码结构, 帮我查一下这个币有没有被控盘.
  Also trigger when the user pastes a token contract address and asks about risk, holders, or manipulation.
user-invocable: true
argument-hint: "<token_address> --chain <chain>"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Agent
  - mcp__*__ant_meme
  - mcp__*__ant_token_analytics
  - mcp__*__ant_address_profile
  - mcp__*__ant_smart_money
  - mcp__*__ant_spot_market_structure
  - mcp__*__ant_protocol_tvl_yields_revenue
metadata:
  requires:
    mcpServers:
      - name: antseer
        description: "Antseer on-chain data MCP — 需要 ant_meme, ant_token_analytics, ant_address_profile 等工具"
---

# 庄家阶段识别器

通过 6 维链上信号分析代币背后庄家所处阶段，生成可视化 HTML 报告。

方法论来源: @agintender — "普通人如何用10分钟识别一个Token背后有庄？"

## 首次安装提示

```
目标用户：链上投研人员、交易员、MEME 币猎手
使用场景：买入前分析代币控盘情况、定期巡检持仓标的、异常放量时快速诊断
如何使用：/market-maker-stage-detector 0x1234...abcd --chain bsc
```

## 输入

`$ARGUMENTS` = 代币合约地址（必需），可选参数通过 `--chain` 指定链。

支持的链: `ethereum`, `bsc`, `solana`, `base`, `arbitrum`, `polygon`

如果用户只给了代币名称（如 "WALK"），先用 `ant_meme` 的 `search_pairs` 查找合约地址。

默认参数:
- chain: `ethereum`（如果地址以 0x 开头且未指定链）
- time_range: `7d`

## 分析流程

按以下 7 步顺序执行。每步完成后记录中间结果，供后续步骤使用。

### Step 1: 代币基础信息

获取代币价格、市值、交易量、Holder 数。

```
MCP: ant_meme → query_type: token_info
参数: chain_id=<chain>, token_addresses=<address>
```

如果 `ant_meme` 返回数据不完整，降级使用:
```
MCP: ant_spot_market_structure → query_type: search
参数: query=<symbol or address>
```

记录: `price`, `mcap`, `volume_24h`, `holders_count`, `price_change_24h`

### Step 2: 筹码集中度

目标: 获取 Top Holders，识别关联钱包，合并计算真实集中度。

**2a. 获取 Holders:**
```
MCP: ant_token_analytics → query_type: holders
参数: token_address=<address>, chain=<chain>
```

**2b. 对 Top 10 地址查关联钱包（并行调用）:**

对每个 Top 10 holder 地址，启动 Agent 并行查询:
```
MCP: ant_address_profile → query_type: related_wallets
参数: address=<holder_address>, chain=<chain>
```

**2c. 交叉验证转账关系:**
```
MCP: ant_address_profile → query_type: counterparties
参数: address=<holder_address>, chain=<chain>
```

**2d. 合并计算:**
1. 有直接转账关系的地址合并为"同一实体"
2. 重新计算合并后各实体的持仓占比
3. 如果任一实体 > 10%，标记"筹码集中"

输出: `entities[]` (entity名, percentage, wallets_count, is_suspicious), `concentration_score` (0-100)

### Step 3: 成交量真实度

用 Step 1 的数据计算:

```
vol_per_holder = volume_24h / holders_count
```

判断标准:
- vol_per_holder < $500 且 < 2x 同类中位数 → 正常
- vol_per_holder > $500 或 > 2x 同类中位数 → 疑似刷量
- vol_per_holder > $2000 → 明显异常

输出: `vol_per_holder`, `peer_median`(可估算), `is_anomaly`, `ratio_vs_peer`

### Step 4: 换手率与时段分析

**4a. 获取 DEX 交易记录:**
```
MCP: ant_token_analytics → query_type: dex_trades
参数: token_address=<address>, chain=<chain>, date_range='{"from":"<7d_ago>","to":"<today>"}'
```

**4b. 计算:**
1. `turnover_rate = volume_24h / mcap`
2. 按小时分桶，统计每小时成交量
3. 计算均值和标准差
4. 成交量 > 均值 3 倍的时段标记为异常
5. 计算净买入量 (buy_volume - sell_volume)

输出: `turnover_rate`, `hourly_volumes[]`, `anomaly_hours[]`, `mean_hourly`, `net_buy_volume`

### Step 5: 大单占比

用 Step 4 的 DEX 交易数据:

1. 按金额排序所有交易
2. 计算 Top 10% 交易的成交量占总量比例
3. 计算基尼系数: `Gini = 1 - 2 * sum(cumulative_share) / n`
4. 按金额分桶: <$100, $100-1K, $1K-10K, >$10K

判断: Top 10% 占比 > 60% → "少数地址驱动"

输出: `top10_pct`, `gini`, `distribution_buckets[]`

### Step 6: 资金流向

**6a. 资金流向情报:**
```
MCP: ant_token_analytics → query_type: flow_intelligence
参数: token_address=<address>, chain=<chain>
```

**6b. 买卖方分析（并行）:**
```
MCP: ant_token_analytics → query_type: who_bought_sold
参数: token_address=<address>, chain=<chain>, buy_or_sell="BUY"

MCP: ant_token_analytics → query_type: who_bought_sold
参数: token_address=<address>, chain=<chain>, buy_or_sell="SELL"
```

统计 Smart Money / 大户 / 散户各自的买入和卖出金额。

输出: `smart_money_buy`, `smart_money_sell`, `whale_buy`, `whale_sell`, `retail_buy`, `retail_sell`

### Step 7: 庄家阶段判断

综合 Step 2-6 所有结果，匹配以下四阶段信号模式:

**吸筹 (ACCUMULATING):**
- 价格低位横盘或微跌 (price_change_24h 在 -5% ~ +5%)
- 筹码集中度在提升 (concentration_score > 50)
- Holder 数变化不大
- Smart Money 有买入信号 (smart_money_buy > smart_money_sell)
- 成交量不高，换手率偏低 (turnover_rate < 15%)

**拉升 (PUMPING):**
- 价格显著上涨 (price_change_24h > 20%)
- 大单占比高 (top10_pct > 60%)
- 成交量集中在特定时段 (anomaly_hours.length > 0)
- 换手率高 (turnover_rate > 30%)

**出货 (DISTRIBUTING):**
- 价格横盘或微跌
- 大户持仓占比在下降
- Smart Money 出现卖出信号 (smart_money_sell > smart_money_buy)
- 换手率升高但价格不涨
- 大单占比 > 60%

**已跑 (DUMPED):**
- 价格持续下跌 (price_change_24h < -15%)
- 大户持仓占比显著降低
- 成交量萎缩 (turnover_rate < 10%)

**计算方式:**
为每个阶段的每个信号判断是否命中（true/false），匹配信号最多的阶段作为判断结果。置信度 = 命中信号数 / 总信号数 * 100。如果两个阶段信号数相同，优先选择风险更高的阶段（出货 > 拉升 > 吸筹 > 已跑）。

输出: `stage`, `confidence`, `signals_matched`, `total_signals`, `signal_dimensions` (6 维 0-1 评分), `all_signals[]`

## 风险信号汇总

从所有步骤中提取风险信号，按严重度分级:
- **HIGH**: 筹码集中度 > 70, Smart Money 大量卖出, Holder 增长但价格跌
- **MEDIUM**: 成交量异常时段, Vol/Holder > 2x 同类, 大单占比 > 60%
- **LOW**: LP 锁定状态未知, 数据覆盖不完整

## 输出

生成两个输出:

### 1. 聊天摘要

在聊天中输出简洁的分析结论:

```
代币: {symbol} | 链: {chain} | 市值: {mcap}
当前阶段: {stage} ({en}) | 置信度: {confidence}%
信号命中: {matched}/{total}

关键发现:
- {risk_signal_1}
- {risk_signal_2}
- {risk_signal_3}

建议: {action_suggestion}

完整报告已生成: output/mm-report-{symbol}.html
```

### 2. HTML 可视化报告

读取本 skill 目录下的 `references/report-template.html` 模板，将计算结果填入 `window.__DATA__` JSON 对象，写入 `output/mm-report-{symbol}.html`。

`window.__DATA__` 结构:

```json
{
  "meta": { "token_name", "symbol", "chain", "contract_address", "generated_at", "time_range" },
  "kpi": { "price", "price_change_24h", "mcap", "volume_24h", "holders" },
  "chip_concentration": { "score", "entities[]", "threshold", "verdict" },
  "volume_authenticity": { "vol_per_holder", "threshold", "peer_median", "is_anomaly", "ratio_vs_peer", "verdict" },
  "turnover": { "turnover_rate", "hourly_volumes[]", "anomaly_hours[]", "mean_hourly" },
  "large_order_ratio": { "top10_pct", "gini", "distribution_buckets[]", "verdict" },
  "fund_flow": { "smart_money_buy/sell", "whale_buy/sell", "retail_buy/sell" },
  "stage_verdict": { "stage", "confidence", "signals_matched", "total_signals", "signal_dimensions", "all_signals[]" },
  "risk_signals": [{ "severity", "text" }],
  "stage_explanation": { "description", "retail_implication", "action_suggestion" }
}
```

## 阶段解读文本

根据判定的阶段，使用以下模板生成解读:

- **吸筹**: "庄家正在低位悄悄收集筹码。价格横盘但大户持仓在增加。此阶段风险相对较低，但不代表一定会拉升。"
- **拉升**: "庄家正在拉升价格。少数地址驱动交易量，筹码并未大量散出。如果你已经持仓，注意设好止盈；如果没有持仓，追高风险较大。"
- **出货**: "庄家正在将筹码派发给散户。价格横盘但 Holder 增长，说明大户在出货。此阶段对散户极为危险，不建议买入。"
- **已跑**: "庄家已基本出完货。价格下跌但散户被套不割肉。此阶段介入需要极大勇气和充分的理由。"

## 降级处理

- MCP 工具返回错误 → 跳过该指标，在报告中标注"数据不可用"
- Holder 数据不可用 → 跳过 Step 2，concentration_score 标注 N/A
- DEX 交易记录为空 → 跳过 Step 4-5，标注"无 DEX 交易数据"
- 所有 MCP 调用失败 → 告知用户"数据源暂时不可用，请稍后重试"

## 注意事项

- 方法论归属: 分析框架来自 @agintender，报告中保留归属
- 不构成投资建议: 报告末尾必须包含免责声明
- 数据局限: 关联钱包识别可能有漏报，建议人工复核高持仓实体
- 适用范围: 主要针对链上 DEX 交易的中小市值代币，不适用于 BTC/ETH 等大盘币
