# MCP 数据映射参考

本文档说明 token-resilience-weekly-report Skill 所依赖的 MCP 工具调用方式。

## 数据需求与 MCP 映射

| 数据需求 | MCP 工具 | query_type | 推荐参数 | 覆盖度 |
|----------|----------|------------|----------|--------|
| 代币 7 日 sparkline（近似日收盘价） | ant_spot_market_structure | coins_markets | include_sparkline_7d=true | 覆盖（近似） |
| 基准币（BTC/ETH/SOL）7 日 sparkline | ant_spot_market_structure | coins_markets | ids=benchmark_ids, sparkline | 覆盖（近似） |
| 代币 24h / 7d 价格变化率 | ant_spot_market_structure | coins_markets | price_change_percentage=["7d","24h"] | 完整覆盖 |
| 代币当前价格 | ant_spot_market_structure | simple_price | ids | 完整覆盖 |
| 未知 Ticker 搜索 → CoinGecko ID | ant_meme | search_pairs | query={ticker} | 完整覆盖 |
| 市场情绪 / 叙事话题（可选） | ant_market_sentiment | coin_detail | coin={symbol} | 完整覆盖 |
| Smart Money 净流向（可选增强） | ant_smart_money | netflows | chains | 完整覆盖 |
| 精确日级 OHLCV 收盘价 | — | — | 需 CoinGecko 公开 API | 未覆盖 |

## 批量调用示例

一次调用同时获取基准和目标代币数据（减少请求次数）：

```
ant_spot_market_structure(
  query_type="coins_markets",
  ids=["bitcoin", "ethereum", "solana", "bittensor", "kaito", "hyperliquid", "io-net"],
  include_sparkline_7d=True,
  price_change_percentage=["7d", "24h"],
  vs_currency="usd"
)
```

## Sparkline 数据处理说明

`coins_markets` 返回的 sparkline 包含过去 7 天的小时级价格点（约 168 个数据点）。

提取日收盘价的方法：
- 将 168 个数据点按 24 小时分为 7 组
- 取每组最后一个数据点作为当日收盘价近似值
- 与 CoinGecko 标准每日收盘价可能存在 1–3% 误差

若需精确日收盘价，可通过 WebFetch 工具调用 CoinGecko 免费公开 API：
```
GET https://api.coingecko.com/api/v3/coins/{id}/market_chart?vs_currency=usd&days=7&interval=daily
```

## 常见 Ticker → CoinGecko ID 映射

| Ticker | CoinGecko ID |
|--------|--------------|
| BTC | bitcoin |
| ETH | ethereum |
| SOL | solana |
| TAO | bittensor |
| SPEC | spectral |
| KAITO | kaito |
| HYPE | hyperliquid |
| IO | io-net |
| STORY | story-protocol |
| DRIFT | drift-protocol |
| SUI | sui |
| APT | aptos |
| ARB | arbitrum |
| OP | optimism |
| AVAX | avalanche-2 |
| DOT | polkadot |
| LINK | chainlink |
| UNI | uniswap |
| AAVE | aave |
| SNX | synthetix-network-token |
