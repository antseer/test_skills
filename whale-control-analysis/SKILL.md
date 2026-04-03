---
name: "whale-control-analysis"
description: "Analyze on-chain holder concentration to identify market maker control patterns. Use when the user mentions holder concentration, whale control, market maker analysis, token manipulation, address clustering, control ratio, or when a token shows abnormal price action and the user wants to investigate whether it is controlled by a single entity."
---

## Overview

Analyze a token's top holders via on-chain data, cluster addresses into entities, calculate real control ratios, and assess market manipulation risk. Produces a structured JSON report with entity identities, control ratios, and risk levels.

## Demand Context

When a token experiences abnormal price action (e.g., 30x in 6 weeks), it often indicates that a single entity controls the majority of circulating supply through multiple wallets. This skill automates the investigation workflow pioneered by on-chain analyst @EmberCN: pull top holders, filter out known public addresses, cluster the rest by buy-timing and funding links, then calculate the true control ratio and attempt to identify the controlling entity.

The methodology originates from @EmberCN's analysis of $SIREN, where 52 out of 54 top holder addresses were attributed to a single entity (suspected DWF Labs) controlling 88.5% of supply.

## Features (Data Inputs)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| symbol | string | Yes | -- | Token symbol (e.g., SIREN) |
| chain | string | Yes | ethereum | Blockchain where the token resides |
| token_address | string | No | -- | Contract address for precise lookup |
| top_n | integer | No | 50 | Number of top holders to analyze |
| time_window_days | integer | No | 14 | Clustering window for first-buy timing |
| known_addresses | list[string] | No | built-in | Public addresses to exclude (exchanges, burn wallets) |
| control_threshold | float | No | 0.5 | Alert threshold for control ratio |

## Entry Conditions

Trigger this skill when any of the following apply:

- User asks about holder concentration, whale control, or market maker control for a specific token
- User wants to investigate abnormal price action (short-term pump/dump) and suspects manipulation
- User mentions keywords: control ratio, address clustering, holder analysis, top holders analysis
- User provides a token symbol or contract address and wants to know "who controls this token"

## Exit Conditions

The skill completes when:

- A full structured JSON report is produced with entities, control ratios, and risk level
- All 9 analysis steps have been executed (or gracefully degraded with documented reasons)
- The report includes a one-line summary and risk assessment

The skill should NOT continue if:

- The token cannot be found on the specified chain (report error and exit)
- No holder data is available from MCP tools (report data unavailability and exit)

## Action Specification

Execute the following 9 steps sequentially. Each step builds on prior results. If an MCP call fails, log the failure and continue with available data -- partial analysis is more useful than no analysis.

### Step 1: Retrieve Token Basics

Call `ant_meme` with query_type `token_info`, passing chain_id and token_addresses.

Record: total_supply, circulating_supply, current price, market_cap. These are the denominators for all subsequent ratio calculations.

### Step 2: Retrieve Top Holders List

Call `ant_token_analytics` with query_type `holders`, passing token_address and chain.

Retrieve the top `top_n` addresses sorted by balance descending. Record address, balance, and percentage for each.

### Step 3: Filter Known Public Addresses

For each top holder address, call `ant_address_profile` with query_type `labels`, passing address and chain.

Exclude addresses labeled as: burn, exchange (hot/cold wallets), contract (DEX pools, staking), project treasury/lockup. Record each exclusion with the reason. The remaining addresses form the "analysis set."

### Step 4: Cluster by Buy-Timing Window

For each address in the analysis set, call `ant_address_profile` with query_type `transactions`, passing address and chain.

Extract the timestamp of the first acquisition of this token. Group addresses whose first-buy timestamps fall within the same `time_window_days` window into clusters. Addresses buying in the same narrow window are suspected to be the same entity.

### Step 5: Validate Clusters via Funding Source Analysis

For each cluster from Step 4, call:
- `ant_address_profile` with query_type `counterparties` for each address
- `ant_address_profile` with query_type `related_wallets` for each address

Check for: direct transfers between cluster members, shared upstream funding addresses, common counterparties. If confirmed, merge into a single entity with a confidence_score and evidence list.

### Step 6: Calculate Control Ratios

This step requires no additional MCP calls -- compute from existing data.

For each confirmed entity:
- entity_control_ratio = sum(entity_addresses_balance) / circulating_supply
- Flag entities exceeding control_threshold

Calculate the HHI (Herfindahl-Hirschman Index) across all entities and remaining individual holders to measure overall concentration.

### Step 7: Entity Identity Correlation

For each entity's addresses, call `ant_address_profile` with query_type `labels`.

Check if any address is tagged with a known institution name (e.g., DWF Labs, Wintermute, Jump Trading, Alameda Research). If found, assign as suspected_identity with confidence level based on evidence strength:
- **high**: Multiple addresses tagged + behavioral match
- **medium**: Single tagged address + timing/funding correlation
- **low**: Behavioral pattern only, no direct label match

### Step 8: Futures Market Correlation

Call `ant_futures_market_structure` with:
- query_type `futures_oi_aggregated` for open interest
- query_type `futures_funding_rate_latest` or `futures_funding_rate_history` for funding rates
- query_type `futures_long_short_ratio` for long/short ratio

If the token has perpetual contracts, assess the "spot control + futures exploitation" pattern:
- High spot control + large OI + abnormal funding rate = elevated manipulation risk
- This is an inferential indicator, not a definitive conclusion -- state this clearly in the output

If no futures market exists for this token, note "No perpetual contract available" and skip.

### Step 9: Comprehensive Assessment

Aggregate all findings into the final report. Apply risk level based on the highest single-entity control ratio:

- Control ratio above 80%: Extreme risk -- price almost entirely controlled by one entity
- Control ratio 50%-80%: High risk -- clear control, price can be manipulated
- Control ratio 30%-50%: Medium risk -- concentrated holdings, monitor closely
- Control ratio below 30%: Relatively dispersed

Generate a one-line summary in the format: "{SYMBOL} on-chain control ratio {X}%, top {N} addresses with {M} attributed to one entity (suspected {identity}), {risk_level}."

## Output Format

Always produce output as a JSON object with this structure:

```json
{
  "symbol": "TOKEN",
  "chain": "ethereum",
  "total_supply": 0,
  "circulating_supply": 0,
  "analyzed_holders": 50,
  "excluded_addresses": [
    {"address": "0x...", "reason": "burn wallet", "rank": 1}
  ],
  "entities": [
    {
      "entity_id": "entity_001",
      "addresses_count": 0,
      "addresses": ["0x..."],
      "total_holding": 0,
      "control_ratio": 0.0,
      "suspected_identity": "Unknown",
      "confidence": "low",
      "evidence": ["description of evidence"]
    }
  ],
  "hhi_index": 0.0,
  "top_entity_control_ratio": 0.0,
  "risk_level": "Extreme / High / Medium / Low",
  "futures_correlation": {
    "has_perp": false,
    "oi_value": null,
    "funding_rate": null,
    "long_short_ratio": null,
    "manipulation_risk": "none / low / medium / high"
  },
  "data_limitations": [
    "On-chain control ratio only; CEX holdings not included"
  ],
  "summary": "One-line summary here."
}
```

## Output Example (Based on $SIREN Case)

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
      "addresses": ["0x...(truncated)"],
      "total_holding": 6440000000,
      "control_ratio": 0.885,
      "suspected_identity": "DWF Labs",
      "confidence": "medium",
      "evidence": [
        "DWF Labs public wallet holds 3M SIREN",
        "DWF Labs SIREN transfer followed by 66.5% token consolidation next day",
        "All 52 addresses first bought in late June to early July 2025 window",
        "48 of 52 addresses participated in consolidation event"
      ]
    }
  ],
  "hhi_index": 0.784,
  "top_entity_control_ratio": 0.885,
  "risk_level": "Extreme risk -- price almost entirely controlled by one entity",
  "futures_correlation": {
    "has_perp": true,
    "oi_value": "refer to live data",
    "funding_rate": "refer to live data",
    "long_short_ratio": "refer to live data",
    "manipulation_risk": "high -- 88.5% spot control + active perpetual market"
  },
  "data_limitations": [
    "On-chain control ratio only; CEX internal holdings not included",
    "Entity identity is inferred, not legally confirmed",
    "Address clustering depends on transaction history completeness"
  ],
  "summary": "SIREN on-chain control ratio 88.5%, top 54 addresses with 52 attributed to one entity (suspected DWF Labs), extreme risk."
}
```

## Risk Parameters

- **Rate limiting**: Steps 3-5 and 7 make per-address MCP calls. For top_n=50, expect up to 200+ individual calls. Pace requests appropriately and batch where possible.
- **Partial data**: If `ant_address_profile` returns incomplete data for some addresses, proceed with available data and note the gap in data_limitations.
- **False clustering**: Time-window clustering can produce false positives (unrelated addresses buying in the same period). Always cross-validate with funding source analysis (Step 5) before confirming clusters.
- **Identity confidence**: Never state entity identity as fact. Use "suspected" and assign confidence levels. The output is analytical inference, not legal determination.
- **CEX blind spot**: On-chain analysis cannot capture CEX internal holdings. Always include the limitation "On-chain control ratio only; CEX holdings not included" in the report.
- **Non-EVM chains**: MCP tool coverage may differ for non-EVM chains (e.g., Solana). If data availability is limited, note it in data_limitations and proceed with available data.

## 首次安装提示

```
目标用户：投研人员、交易员、风控分析师
使用场景：某代币出现异常价格走势（短期暴涨/暴跌），需要排查是否存在庄家控盘
如何使用：/whale-control-analysis SIREN ethereum
```

## Disclaimer

This skill is based on the on-chain analysis methodology originated by @EmberCN. The analysis produces technical inferences, not legal conclusions. Entity identification is probabilistic and should not be treated as accusation against any individual or institution. On-chain control ratios may underestimate actual control due to CEX holdings being invisible to chain analysis. This tool does not constitute investment advice.
