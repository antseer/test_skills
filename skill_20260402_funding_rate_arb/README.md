# Funding Rate Arbitrage Monitor

监控 Binance、OKX、Bybit 永续合约 funding rate，检测异常并识别跨交易所套利机会。

## 依赖

仅使用 Python 标准库（`urllib`、`json`、`statistics`），无需安装第三方包。

要求 Python 3.10+。

## 使用方法

```bash
python funding_rate_monitor.py
```

脚本将：
1. 从 Binance、OKX、Bybit 公开 API 获取 BTC/USDT 和 ETH/USDT 永续合约的当前 funding rate
2. 获取 30 天历史 funding rate 并计算 Z-score
3. 当 |Z-score| > 2 时输出异常告警
4. 比较跨交易所 funding rate，当差值 > 0.05% 时输出套利机会
5. 以 JSON 格式打印结果

## 输出示例

```json
{
  "timestamp": "2026-04-02T00:00:00Z",
  "rates": {
    "binance_btc": 0.0001,
    "okx_btc": 0.00015,
    "bybit_btc": 0.00012,
    "binance_eth": 0.00008,
    "okx_eth": 0.0001,
    "bybit_eth": 0.00009
  },
  "alerts": [
    {
      "type": "high_rate",
      "exchange": "okx",
      "asset": "BTC",
      "funding_rate": 0.00015,
      "z_score": 2.3
    },
    {
      "type": "arb_opportunity",
      "asset": "BTC",
      "pair": "binance-okx",
      "spread": 0.00005,
      "rate_a": 0.0001,
      "rate_b": 0.00015
    }
  ]
}
```

## 配置

脚本顶部可调整以下参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `Z_SCORE_THRESHOLD` | 2.0 | Z-score 告警阈值 |
| `SPREAD_THRESHOLD` | 0.0005 | 跨交易所套利阈值（0.05%） |
| `HISTORY_DAYS` | 30 | Z-score 计算使用的历史天数 |
| `REQUEST_TIMEOUT` | 15 | HTTP 请求超时（秒） |

## 定时运行

Funding rate 每 8 小时结算一次，建议配合 cron 定时执行：

```bash
# 每 8 小时运行一次（UTC 00:00, 08:00, 16:00）
0 0,8,16 * * * cd /path/to/skill && python funding_rate_monitor.py >> output.jsonl
```

## 策略文档

详见 [SKILL.md](./SKILL.md)。
