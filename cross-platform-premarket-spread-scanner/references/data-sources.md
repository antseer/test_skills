# 数据源参考文档

## 平台 API 接入说明

### 1. Binance Pre-market API

Binance 盘前市场使用标准 REST API，symbol 格式为 `{TOKEN}-PRE-USDT`。

**获取盘前价格：**
```
GET https://api.binance.com/api/v3/ticker/price?symbol=EDGEX-PRE-USDT
```

**获取 Order Book 深度：**
```
GET https://api.binance.com/api/v3/depth?symbol=EDGEX-PRE-USDT&limit=20
```

响应示例：
```json
{"symbol": "EDGEX-PRE-USDT", "price": "0.45000000"}
```

注意：
- 盘前市场 symbol 格式因代币而异，若 `-PRE-USDT` 返回 404，尝试 `PRE-USDT`（无连字符）
- Binance 盘前市场通常在 TGE 前约 1-2 周开放，TGE 后自动迁移到现货

---

### 2. Polymarket Gamma API

Polymarket 是 Polygon 链上的预测市场，使用 USDC 作为结算货币。

**搜索相关市场：**
```
GET https://gamma-api.polymarket.com/markets?keyword=EDGEX&active=true
```

**解析价格逻辑：**
- 在返回列表中找到最相关的市场（通常标题包含 "Will EDGEX be listed" 或 "EDGEX price at TGE"）
- 取 `outcomePrices[0]`（通常对应"Yes"或"更高价格"结果）
- 该价格单位为 USDC，可直接用作隐含价格

响应字段：
```json
{
  "question": "Will EDGEX price exceed $0.5 at TGE?",
  "outcomePrices": ["0.65", "0.35"],
  "outcomes": ["Yes", "No"],
  "volume": "150000"
}
```

注意：Polymarket 价格为概率值（0-1），需根据问题语义转换为隐含价格。

---

### 3. Aspecta AI (ASP) 盘前市场

Aspecta AI 是独立的链上预测/盘前市场平台，无官方公开 REST API 文档。

**替代获取方法（按优先级）：**

1. **WebFetch 直接访问：** `https://aspecta.ai/market/{symbol_lowercase}`
   - 解析页面中的当前报价 DOM 元素

2. **WebSearch 搜索：** `"{SYMBOL} ASP premarket price site:aspecta.ai"`
   - 从搜索摘要中提取价格数字

3. **Twitter/X 搜索：** `"{SYMBOL} ASP price @BTC_Alert_"` 或相关社区
   - 从 KOL 推文中获取当前报价（注意时效性）

---

### 4. Antseer MCP 工具参数

本 Skill 使用以下 Antseer MCP 工具：

#### ant_token_analytics — TGE/解锁时间

```json
{
  "query_type": "emissions",
  "asset": "EDGEX"
}
```

返回字段（关键）：
- `tge_date`: TGE 日期时间戳
- `unlock_schedule`: 各批次解锁时间和数量

#### ant_token_analytics — 解锁批次详情

```json
{
  "query_type": "emission_detail",
  "asset": "EDGEX"
}
```

#### ant_market_sentiment — 情绪分析

```json
{
  "query_type": "coin_detail",
  "coin": "EDGEX"
}
```

返回字段（关键）：
- `sentiment_score`: 0-100 情绪分
- `social_mentions_24h_change_pct`: 24h 社交提及量变化百分比

#### ant_spot_market_structure — 参考代币历史价格

```json
{
  "query_type": "coins_markets",
  "ids": ["OPN"]
}
```

注意：仅支持已上线现货的代币，盘前历史数据不可用。

---

## 费率参考

| 平台 | 挂单费率 | 吃单费率 | 备注 |
|------|---------|---------|------|
| Binance | 0.02% | 0.05% | VIP 等级越高越低 |
| ASP (Aspecta) | ~0.1%-0.3% | ~0.1%-0.3% | 因流动性薄，实际滑点往往更高 |
| Polymarket | 0% | ~1-2% | 通过做市商价差体现，非显式手续费 |

建议双腿合计手续费+滑点按 1-2% 估算（保守值），实际根据仓位大小和当前深度调整。

---

## 风险因子速查

| 风险类型 | 描述 | 对冲建议 |
|---------|------|---------|
| cc 风险 | 代币 listing 被取消或推迟，盘前头寸无法交割 | 降低仓位，确认项目基本面 |
| 流动性风险 | ASP/Polymarket 深度薄，大单滑点超预期 | 分批入场，单笔 ≤ 5,000 USDT |
| FOMO 轧空 | 市场情绪极端时做空腿被轧 | 严格止损，止损位 = 入场价 × 1.3 |
| 超对冲风险 | 做空量超过空投隐式多头，方向性暴露反转 | hedge ratio 上限 1.0 |
| 时间风险 | TGE 推迟导致资金长时间锁定 | 关注官方公告，预留应急流动性 |
