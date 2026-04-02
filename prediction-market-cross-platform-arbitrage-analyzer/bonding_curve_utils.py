"""
Bonding Curve calculation utilities for prediction market arbitrage analysis.

Supports three curve types: exponential, linear, logarithmic.
Provides share dilution simulation and breakeven pool size calculation.
"""

import math
from dataclasses import dataclass
from typing import List, Literal


CurveType = Literal["exponential", "linear", "logarithmic"]


@dataclass
class DilutionScenario:
    """A single point on the dilution curve."""
    pool_tvl: float          # Pool TVL at this scenario (USD)
    user_share_pct: float    # User's share of the pool (%)
    effective_odds: float    # Actual odds ratio after dilution
    effective_payout: float  # Actual payout in USD


@dataclass
class ScenarioCell:
    """A single cell in the 3x3 scenario matrix."""
    event_outcome: str       # "event_occurs" | "event_not_occurs_hold" | "early_exit"
    market_scenario: str     # "optimistic" | "neutral" | "pessimistic"
    platform_a_pnl: float   # P&L from platform A (USD)
    platform_b_pnl: float   # P&L from platform B (USD)
    net_pnl: float           # Total net P&L (USD)
    label: str               # Human-readable label


@dataclass
class ArbitrageAnalysis:
    """Complete arbitrage analysis result."""
    event_description: str
    static_arbitrage_spread: float
    current_share_pct: float
    diluted_scenarios: List[DilutionScenario]
    scenario_matrix: List[ScenarioCell]
    breakeven_pool_size: float
    feasibility_rating: str
    recommended_strategy: str
    risk_warnings: List[str]


def calculate_user_tokens_exponential(
    entry_tvl: float,
    investment: float,
    k: float = 0.001
) -> float:
    """
    Calculate tokens received for an exponential bonding curve.

    price(supply) = base_price * e^(k * supply)
    tokens = (1/k) * ln((entry_tvl + investment) / entry_tvl)
    """
    if entry_tvl <= 0 or investment <= 0:
        return 0.0
    return (1.0 / k) * math.log((entry_tvl + investment) / entry_tvl)


def calculate_total_supply_exponential(pool_tvl: float, base_tvl: float = 100.0, k: float = 0.001) -> float:
    """Total token supply at a given pool TVL for exponential curve."""
    if pool_tvl <= 0 or base_tvl <= 0:
        return 0.0
    return (1.0 / k) * math.log(pool_tvl / base_tvl)


def calculate_user_tokens_linear(
    entry_tvl: float,
    investment: float,
    k: float = 0.01
) -> float:
    """
    Calculate tokens received for a linear bonding curve.

    price(supply) = base_price + k * supply
    tokens = (sqrt(entry_tvl + investment) - sqrt(entry_tvl)) / sqrt(k/2)
    """
    if entry_tvl <= 0 or investment <= 0:
        return 0.0
    return (math.sqrt(entry_tvl + investment) - math.sqrt(entry_tvl)) / math.sqrt(k / 2.0)


def calculate_total_supply_linear(pool_tvl: float, k: float = 0.01) -> float:
    """Total token supply at a given pool TVL for linear curve."""
    if pool_tvl <= 0:
        return 0.0
    return math.sqrt(2.0 * pool_tvl / k)


def calculate_user_tokens_logarithmic(
    entry_tvl: float,
    investment: float,
    k: float = 0.01
) -> float:
    """
    Calculate tokens received for a logarithmic bonding curve.

    Approximation: tokens proportional to integral of 1/price(supply).
    """
    if entry_tvl <= 0 or investment <= 0:
        return 0.0
    s1 = entry_tvl
    s2 = entry_tvl + investment
    return (s2 * math.log(1 + k * s2) - s2 + 1.0 / k) - (s1 * math.log(1 + k * s1) - s1 + 1.0 / k)


def calculate_share_percentage(
    curve_type: CurveType,
    entry_tvl: float,
    investment: float,
    current_pool_tvl: float,
    k: float = 0.001
) -> float:
    """
    Calculate user's share percentage at a given pool TVL.

    Returns percentage (0-100).
    """
    if curve_type == "exponential":
        user_tokens = calculate_user_tokens_exponential(entry_tvl, investment, k)
        total_supply = calculate_total_supply_exponential(current_pool_tvl, base_tvl=min(100.0, entry_tvl), k=k)
    elif curve_type == "linear":
        user_tokens = calculate_user_tokens_linear(entry_tvl, investment, k)
        total_supply = calculate_total_supply_linear(current_pool_tvl, k)
    elif curve_type == "logarithmic":
        user_tokens = calculate_user_tokens_logarithmic(entry_tvl, investment, k)
        total_supply = calculate_user_tokens_logarithmic(0.01, current_pool_tvl, k)
    else:
        raise ValueError(f"Unsupported curve type: {curve_type}")

    if total_supply <= 0:
        return 0.0
    return (user_tokens / total_supply) * 100.0


def simulate_dilution(
    curve_type: CurveType,
    entry_tvl: float,
    investment: float,
    current_pool_tvl: float,
    multipliers: List[float] = None,
    k: float = 0.001
) -> List[DilutionScenario]:
    """
    Simulate share dilution at various pool TVL levels.

    Args:
        curve_type: Type of bonding curve
        entry_tvl: TVL when user entered
        investment: User's investment amount (USD)
        current_pool_tvl: Current pool TVL
        multipliers: List of TVL multipliers to simulate (default: [1, 2, 5, 10])
        k: Curve parameter

    Returns:
        List of DilutionScenario objects
    """
    if multipliers is None:
        multipliers = [1.0, 2.0, 5.0, 10.0]

    scenarios = []

    # Include entry point
    entry_share = calculate_share_percentage(curve_type, entry_tvl, investment, entry_tvl + investment, k)
    entry_payout = (entry_share / 100.0) * (entry_tvl + investment)
    entry_odds = entry_payout / investment if investment > 0 else 0
    scenarios.append(DilutionScenario(
        pool_tvl=entry_tvl,
        user_share_pct=round(entry_share, 2),
        effective_odds=round(entry_odds, 2),
        effective_payout=round(entry_payout, 2)
    ))

    for mult in multipliers:
        tvl = current_pool_tvl * mult
        if tvl <= entry_tvl:
            continue
        share_pct = calculate_share_percentage(curve_type, entry_tvl, investment, tvl, k)
        payout = (share_pct / 100.0) * tvl
        odds = payout / investment if investment > 0 else 0
        scenarios.append(DilutionScenario(
            pool_tvl=round(tvl, 2),
            user_share_pct=round(share_pct, 2),
            effective_odds=round(odds, 2),
            effective_payout=round(payout, 2)
        ))

    return scenarios


def build_scenario_matrix(
    investment_a: float,
    cost_b: float,
    probability_b: float,
    dilution_scenarios: List[DilutionScenario],
) -> List[ScenarioCell]:
    """
    Build a 3x3 scenario matrix (event outcome x market scenario).

    Args:
        investment_a: User's investment in platform A (USD)
        cost_b: User's position cost in platform B (USD)
        probability_b: Platform B's event probability (%)
        dilution_scenarios: Dilution scenarios from simulate_dilution()

    Returns:
        List of ScenarioCell objects (9 cells total)
    """
    total_cost = investment_a + cost_b
    platform_b_payout = cost_b / (probability_b / 100.0) if probability_b > 0 else 0

    # Map scenarios to optimistic/neutral/pessimistic
    # Use first 3 non-entry scenarios, or pad with available data
    payout_scenarios = dilution_scenarios[1:] if len(dilution_scenarios) > 1 else dilution_scenarios
    while len(payout_scenarios) < 3:
        payout_scenarios.append(payout_scenarios[-1] if payout_scenarios else DilutionScenario(0, 0, 0, 0))

    scenario_labels = ["optimistic", "neutral", "pessimistic"]
    cells = []

    for i, (scenario, label) in enumerate(zip(payout_scenarios[:3], scenario_labels)):
        # Event occurs: platform A loses, platform B wins
        event_occurs_a_pnl = -investment_a
        event_occurs_b_pnl = platform_b_payout - cost_b
        cells.append(ScenarioCell(
            event_outcome="event_occurs",
            market_scenario=label,
            platform_a_pnl=round(event_occurs_a_pnl, 2),
            platform_b_pnl=round(event_occurs_b_pnl, 2),
            net_pnl=round(event_occurs_a_pnl + event_occurs_b_pnl, 2),
            label=f"Event occurs / {label}: net = {round(event_occurs_a_pnl + event_occurs_b_pnl, 2)} USD"
        ))

        # Event not occurs + hold to settlement: platform A wins (diluted), platform B loses
        not_occurs_a_pnl = scenario.effective_payout - investment_a
        not_occurs_b_pnl = -cost_b
        cells.append(ScenarioCell(
            event_outcome="event_not_occurs_hold",
            market_scenario=label,
            platform_a_pnl=round(not_occurs_a_pnl, 2),
            platform_b_pnl=round(not_occurs_b_pnl, 2),
            net_pnl=round(not_occurs_a_pnl + not_occurs_b_pnl, 2),
            label=f"Event not occurs, hold / {label}: net = {round(not_occurs_a_pnl + not_occurs_b_pnl, 2)} USD"
        ))

        # Early exit: sell along curve (estimate ~40-60% recovery of current value)
        exit_recovery_rate = 0.5  # Conservative 50% recovery via curve sell
        early_exit_a_pnl = scenario.effective_payout * exit_recovery_rate - investment_a
        early_exit_b_value = cost_b * 0.8  # Estimate 80% of position value mid-term
        early_exit_b_pnl = early_exit_b_value - cost_b
        cells.append(ScenarioCell(
            event_outcome="early_exit",
            market_scenario=label,
            platform_a_pnl=round(early_exit_a_pnl, 2),
            platform_b_pnl=round(early_exit_b_pnl, 2),
            net_pnl=round(early_exit_a_pnl + early_exit_b_pnl, 2),
            label=f"Early exit / {label}: net = {round(early_exit_a_pnl + early_exit_b_pnl, 2)} USD"
        ))

    return cells


def calculate_breakeven_pool_size(
    curve_type: CurveType,
    entry_tvl: float,
    investment_a: float,
    cost_b: float,
    k: float = 0.001,
    search_max: float = 1_000_000,
    precision: float = 10.0
) -> float:
    """
    Find the pool TVL at which the 'event not occurs + hold' scenario breaks even.

    breakeven: user_share_pct * pool_tvl - investment_a - cost_b = 0

    Uses binary search.
    """
    total_cost = investment_a + cost_b
    low = entry_tvl + investment_a
    high = search_max

    for _ in range(100):  # Max iterations
        mid = (low + high) / 2.0
        share_pct = calculate_share_percentage(curve_type, entry_tvl, investment_a, mid, k)
        payout = (share_pct / 100.0) * mid
        net = payout - total_cost

        if abs(net) < precision:
            return round(mid, 2)
        elif net > 0:
            low = mid
        else:
            high = mid

    return round((low + high) / 2.0, 2)


def determine_feasibility(scenario_cells: List[ScenarioCell]) -> tuple:
    """
    Determine feasibility rating based on scenario matrix.

    Returns:
        (rating, recommendation) tuple
    """
    positive_count = sum(1 for c in scenario_cells if c.net_pnl > 0)
    negative_count = sum(1 for c in scenario_cells if c.net_pnl < 0)
    total = len(scenario_cells)

    # Check if early exit is always the best strategy
    early_exit_cells = [c for c in scenario_cells if c.event_outcome == "early_exit"]
    hold_cells = [c for c in scenario_cells if c.event_outcome == "event_not_occurs_hold"]

    early_exit_better = all(
        e.net_pnl > h.net_pnl
        for e, h in zip(early_exit_cells, hold_cells)
    ) if early_exit_cells and hold_cells else False

    if positive_count == total:
        return ("feasible", "All scenarios show positive returns. Arbitrage is viable with low risk. Execute as planned.")
    elif early_exit_better:
        return ("not_arbitrage", "Early exit consistently outperforms holding to settlement. This is effectively a directional trade with timing, not risk-free arbitrage. Treat as speculative position.")
    elif positive_count > negative_count:
        return ("conditionally_feasible", "Majority of scenarios are profitable but loss scenarios exist. Set stop-loss at the breakeven pool TVL and monitor pool size weekly.")
    else:
        return ("not_feasible", "Static arbitrage assumption has failed. Bonding Curve dilution causes actual payout to fall below breakeven in most scenarios. Do not execute as arbitrage.")


if __name__ == "__main__":
    # Example: reproduce the tweet's original case
    print("=== Prediction Market Arbitrage Analysis ===\n")

    curve_type = "exponential"
    entry_tvl = 1500.0
    investment = 500.0
    current_tvl = 4000.0
    cost_b = 5000.0
    prob_b = 63.0

    print("Dilution Simulation:")
    scenarios = simulate_dilution(curve_type, entry_tvl, investment, current_tvl)
    for s in scenarios:
        print(f"  TVL: {s.pool_tvl:>10,.0f} | Share: {s.user_share_pct:>6.2f}% | Odds: 1:{s.effective_odds:.1f} | Payout: {s.effective_payout:,.0f} USD")

    print("\nScenario Matrix:")
    matrix = build_scenario_matrix(investment, cost_b, prob_b, scenarios)
    for cell in matrix:
        print(f"  {cell.label}")

    breakeven = calculate_breakeven_pool_size(curve_type, entry_tvl, investment, cost_b)
    print(f"\nBreakeven Pool Size: {breakeven:,.0f} USD")

    rating, recommendation = determine_feasibility(matrix)
    print(f"\nFeasibility: {rating}")
    print(f"Recommendation: {recommendation}")
