---
name: "Funding Rate Arbitrage Monitor"
description: "监控主流交易所永续合约 funding rate，识别异常和跨交易所套利机会"
strategy_agent: "monitoring"
version: "1.0.0"
created_at: "2026-04-02T00:00:00Z"
skill_lifecycle: "draft"
author: "creator-agent"
---

# Funding Rate Arbitrage Monitor

## Overview

实时监控 Binance、OKX、Bybit 三家交易所的 BTC/USDT 和 ETH/USDT 永续合约 funding rate。基于 30 天历史数据计算 Z-score 检测单交易所异常，同时比较跨交易所 funding rate 差值以识别套利机会。每 8 小时采集一次数据，输出结构化 JSON 告警，供量化交易员和做市商消费。

## Demand Context

加密货币量化交易员、DeFi 做市商和对冲基金研究员需要自动化的 funding rate 监控工具。永续合约 funding rate 是市场情绪的重要指标：当 funding rate 显著偏离均值时，通常暗示市场过度杠杆化或存在跨交易所套利窗口。手动监控多交易所 funding rate 效率低且容易错过短暂套利机会，因此需要自动化方案。

## Features (Data Inputs)

| Feature | Source | Description |
|---------|--------|-------------|
| funding_rate_binance | Binance Public API | Binance BTC/ETH 永续合约当前 funding rate |
| funding_rate_okx | OKX Public API | OKX BTC/ETH 永续合约当前 funding rate |
| funding_rate_bybit | Bybit Public API | Bybit BTC/ETH 永续合约当前 funding rate |
| funding_rate_history_30d | 各交易所 Public API | 30 天 funding rate 历史数据，用于 Z-score 计算 |
| funding_rate_z_score | 自定义计算 | 基于 30 天历史的 funding rate Z-score |
| cross_exchange_spread | 自定义计算 | 跨交易所 funding rate 差值 |

## Entry Conditions

```yaml
entry_conditions:
  single_exchange_alert:
    - condition: funding_rate_z_score
      operator: "abs_gt"
      threshold: 2
      description: "单交易所 funding rate Z-score 绝对值超过 2，标记为异常"
  arbitrage_opportunity:
    - condition: cross_exchange_spread
      operator: ">"
      threshold: 0.0005  # 0.05%
      description: "跨交易所 funding rate 差值超过 0.05%，标记为套利机会"
```

## Exit Conditions

```yaml
exit_conditions:
  single_exchange_alert:
    - condition: funding_rate_z_score
      operator: "abs_lt"
      threshold: 1.5
      description: "Z-score 回落至 1.5 以内，取消异常告警"
  arbitrage_opportunity:
    - condition: cross_exchange_spread
      operator: "<"
      threshold: 0.0003  # 0.03%
      description: "跨交易所差值收窄至 0.03% 以下，套利窗口关闭"
```

## Action Specification

```yaml
action:
  schedule: "every 8 hours"
  steps:
    - step: collect_funding_rates
      description: "从 Binance、OKX、Bybit 公开 API 采集 BTC/ETH 当前 funding rate"
      timeout: 30s
    - step: fetch_historical_rates
      description: "获取 30 天历史 funding rate 数据"
      timeout: 60s
    - step: compute_z_scores
      description: "基于 30 天历史计算每个交易所每个交易对的 Z-score"
    - step: compute_cross_exchange_spreads
      description: "计算所有交易所两两之间的 funding rate 差值"
    - step: evaluate_conditions
      description: "根据 Entry/Exit 条件判定告警和套利信号"
    - step: emit_json_output
      description: "输出结构化 JSON 包含当前 rates、Z-scores、告警列表"
  output_format: "JSON"
```

## Risk Parameters

```yaml
risk:
  api_rate_limits:
    binance: "1200 req/min"
    okx: "20 req/2s"
    bybit: "120 req/min"
    mitigation: "请求间添加适当延迟，使用批量接口减少调用次数"
  data_staleness:
    max_acceptable_delay: 60s
    mitigation: "如数据时间戳超过 60 秒则标记为 stale，不参与 Z-score 计算"
  exchange_downtime:
    mitigation: "单交易所不可用时跳过该交易所，不影响其余交易所监控"
  z_score_accuracy:
    min_history_days: 7
    mitigation: "历史数据不足 7 天时不输出 Z-score 告警，仅输出原始 rate"
```
