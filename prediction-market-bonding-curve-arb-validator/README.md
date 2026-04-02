# Prediction Market Bonding Curve Arbitrage Validator

## What It Does

This skill evaluates whether cross-platform arbitrage between two prediction markets is viable when one platform uses Bonding Curve pricing. It addresses a common misconception: in Bonding Curve markets, displayed odds do not equal your actual return rate because pool share dilution erodes early participants' payouts as the pool grows.

## The Problem

A trader sees that Polymarket prices "Token Launch by 2026" at 63% (Yes), while platform 42's "No Token Launch" pool offers 1:10 odds. Naive static analysis suggests a profitable hedge. However, 42 uses a Bonding Curve -- as more capital flows into the "No Token Launch" pool, the trader's share drops from ~11% to ~2.4% (at 5x TVL growth), and the promised 1:10 payout never materializes in full.

## Five-Step Analysis

1. **Static Arbitrage PnL** -- Calculate idealized returns assuming fixed odds on both platforms.
2. **Bonding Curve Dilution Simulation** -- Model how pool TVL growth dilutes your share under conservative linear approximation.
3. **Dynamic PnL Matrix** -- Recalculate real PnL across TVL growth scenarios with dilution factored in.
4. **Early Exit Path Analysis** -- Compare selling along the curve before event settlement vs holding to expiry.
5. **Comprehensive Verdict** -- Output VIABLE / CONDITIONAL / NOT_VIABLE with risk warnings and strategy suggestions.

## Usage

```python
from arb_validator import ArbValidator

validator = ArbValidator(
    event_description="Will Project X launch a token before 2026 end?",
    platform_a_name="Polymarket",
    platform_a_odds=0.63,
    platform_a_bet_amount=5000.0,
    platform_a_pricing_model="AMM",
    platform_b_name="42",
    platform_b_pool="No Token Launch",
    platform_b_odds=10.0,
    platform_b_bet_amount=500.0,
    platform_b_pool_tvl=4000.0,
    platform_b_pricing_model="BondingCurve",
    pool_growth_scenarios=[2, 5, 10],
)

report = validator.run()
print(report["verdict"])          # VIABLE / CONDITIONAL / NOT_VIABLE
print(report["risk_warnings"])    # List of key risks
print(report["strategy_suggestion"])
```

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| event_description | str | Yes | Description of the prediction event |
| platform_a_name | str | Yes | Name of Platform A (e.g., Polymarket) |
| platform_a_odds | float | Yes | Platform A probability (0.01 - 0.99) |
| platform_a_bet_amount | float | Yes | Bet amount on Platform A (USD) |
| platform_a_pricing_model | str | No | AMM / OrderBook / Fixed (default: AMM) |
| platform_b_name | str | Yes | Name of Platform B (e.g., 42) |
| platform_b_pool | str | Yes | Target pool name on Platform B |
| platform_b_odds | float | Yes | Platform B odds multiplier (e.g., 10 for 1:10) |
| platform_b_bet_amount | float | Yes | Bet amount on Platform B (USD) |
| platform_b_pool_tvl | float | Yes | Platform B pool TVL in USD |
| platform_b_pricing_model | str | No | BondingCurve / AMM / Fixed (default: BondingCurve) |
| pool_growth_scenarios | list | No | TVL growth multipliers (default: [2, 5, 10]) |

## Output Structure

| Field | Type | Description |
|-------|------|-------------|
| static_pnl | dict | Static PnL for event-happens and event-not-happens scenarios |
| dilution_table | list | Share dilution at each TVL growth multiplier |
| dynamic_pnl_matrix | list | Dynamic PnL across TVL growth x event outcome combinations |
| early_exit_comparison | dict | Early exit vs hold-to-expiry return comparison |
| verdict | str | VIABLE / CONDITIONAL / NOT_VIABLE |
| risk_warnings | list | Key risk warnings |
| strategy_suggestion | str | Actionable strategy recommendation |

## Data Coverage

- **Fully covered by Antseer MCP**: Token spot price (ant_spot_market_structure)
- **Partially covered**: Market sentiment, social heat (ant_market_sentiment)
- **Not covered**: Prediction market odds, pool TVL, Bonding Curve parameters -- all require user input

## Limitations

- Bonding Curve formula varies by platform; this tool uses linear approximation as a conservative estimate.
- Cannot fetch live prediction market data automatically (v1 is a "calculator mode" requiring manual input).
- Does not support multi-event combination arbitrage strategies.
- TVL growth projections are user-provided assumptions, not predictions.

## Origin

Analysis framework derived from @Wuhuoqiu's tweet analyzing Polymarket vs 42 cross-platform arbitrage dynamics, generalized into a reusable validation tool.
