"""
预测市场跨平台套利分析器 (Prediction Market Cross-Platform Arbitrage Analyzer)

6 步分析流程:
  1. 市场状态快照
  2. 静态套利计算
  3. Bonding Curve 稀释建模
  4. 多情景动态 P&L 模拟
  5. 流动性与退出路径分析
  6. 综合评估与风险评级
"""

from __future__ import annotations

import json
import math
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ArbitrageInput:
    """用户输入参数."""
    event_description: str
    platform_a: str
    platform_b: str
    position_a_type: str
    position_b_type: str
    investment_a: float
    investment_b: float
    odds_a_entry: float
    prob_b_entry: float
    pool_tvl_a: float = 0.0
    pool_type: str = "bonding_curve"
    time_horizon: str = ""
    scenarios: Optional[List[dict]] = None

    def validate(self) -> None:
        if self.investment_a <= 0 or self.investment_b <= 0:
            raise ValueError("investment_a and investment_b must be positive")
        if self.odds_a_entry <= 0:
            raise ValueError("odds_a_entry must be positive")
        if not (0 < self.prob_b_entry < 1):
            raise ValueError("prob_b_entry must be between 0 and 1 (exclusive)")


@dataclass
class MarketSnapshot:
    """Step 1 output."""
    platform_a_name: str
    platform_a_tvl: float
    platform_a_odds: float
    platform_a_position: str
    platform_b_name: str
    platform_b_probability: float
    platform_b_implied_odds: float
    platform_b_position: str
    investment_a: float
    investment_b: float


@dataclass
class StaticArbitragePnl:
    """Step 2 output."""
    event_occurs_pnl_a: float
    event_occurs_pnl_b: float
    event_occurs_net: float
    event_not_occurs_pnl_a: float
    event_not_occurs_pnl_b: float
    event_not_occurs_net: float
    is_static_arb_valid: bool


@dataclass
class DilutionRow:
    tvl: float
    share_pct: float
    effective_odds: float
    dilution_pct: float


@dataclass
class ScenarioPnl:
    name: str
    description: str
    pnl_a: float
    pnl_b: float
    net_pnl: float
    assessment: str


@dataclass
class ExitAnalysis:
    exit_slippage_pct: float
    exit_receive_amount: float
    exit_friction: str
    optimal_exit_note: str


@dataclass
class AnalysisResult:
    """Final output from Step 6."""
    event: str
    static_arbitrage_pnl: dict
    is_static_arb_valid: bool
    dilution_table: List[dict]
    effective_odds_current: float
    scenarios: List[dict]
    worst_case_pnl: float
    best_case_pnl: float
    exit_slippage_estimate: float
    risk_rating: str
    risk_factors: List[str]
    recommendation: str


# ---------------------------------------------------------------------------
# Bonding Curve helpers
# ---------------------------------------------------------------------------

DEFAULT_K = 0.001  # exponential curve steepness parameter


def _bonding_curve_tokens(investment: float, entry_tvl: float, k: float = DEFAULT_K) -> float:
    """Calculate tokens received for *investment* entering at *entry_tvl* on an exponential bonding curve.

    Model: price(supply) = base * e^(k * supply)
    Tokens received = (1/k) * ln((entry_tvl + investment) / entry_tvl)
    """
    if entry_tvl <= 0:
        entry_tvl = 1.0  # avoid log(0)
    return (1.0 / k) * math.log((entry_tvl + investment) / entry_tvl)


def _bonding_curve_total_supply(tvl: float, base_tvl: float = 1.0, k: float = DEFAULT_K) -> float:
    """Total token supply when pool reaches *tvl*."""
    if base_tvl <= 0:
        base_tvl = 1.0
    return (1.0 / k) * math.log(tvl / base_tvl)


def _sell_along_curve(tokens_to_sell: float, current_supply: float, current_tvl: float, k: float = DEFAULT_K) -> float:
    """Estimate USD received when selling *tokens_to_sell* along the bonding curve.

    Integral of price curve from (current_supply - tokens_to_sell) to current_supply.
    Receive = current_tvl - base_tvl * e^(k * (current_supply - tokens_to_sell))
    Simplified: receive = current_tvl * (1 - e^(-k * tokens_to_sell))
    """
    if tokens_to_sell <= 0:
        return 0.0
    ratio = 1.0 - math.exp(-k * tokens_to_sell)
    return current_tvl * ratio


# ---------------------------------------------------------------------------
# Analysis steps
# ---------------------------------------------------------------------------

def step1_market_snapshot(inp: ArbitrageInput) -> MarketSnapshot:
    """Step 1: Collect market state from both platforms."""
    implied_odds_b = 1.0 / inp.prob_b_entry if inp.prob_b_entry > 0 else 0.0
    snapshot = MarketSnapshot(
        platform_a_name=inp.platform_a,
        platform_a_tvl=inp.pool_tvl_a,
        platform_a_odds=inp.odds_a_entry,
        platform_a_position=inp.position_a_type,
        platform_b_name=inp.platform_b,
        platform_b_probability=inp.prob_b_entry,
        platform_b_implied_odds=round(implied_odds_b, 4),
        platform_b_position=inp.position_b_type,
        investment_a=inp.investment_a,
        investment_b=inp.investment_b,
    )
    logger.info("Step 1 complete: market snapshot captured")
    return snapshot


def step2_static_arbitrage(inp: ArbitrageInput) -> StaticArbitragePnl:
    """Step 2: Calculate static arbitrage P&L assuming fixed odds/probability."""
    # Event occurs: platform A loses, platform B wins
    pnl_a_occurs = -inp.investment_a
    pnl_b_occurs = inp.investment_b * (1.0 / inp.prob_b_entry - 1.0)

    # Event does NOT occur: platform A wins at entry odds, platform B loses
    pnl_a_not = inp.investment_a * inp.odds_a_entry
    pnl_b_not = -inp.investment_b

    net_occurs = pnl_a_occurs + pnl_b_occurs
    net_not = pnl_a_not + pnl_b_not

    is_valid = net_occurs > 0 and net_not > 0

    result = StaticArbitragePnl(
        event_occurs_pnl_a=round(pnl_a_occurs, 2),
        event_occurs_pnl_b=round(pnl_b_occurs, 2),
        event_occurs_net=round(net_occurs, 2),
        event_not_occurs_pnl_a=round(pnl_a_not, 2),
        event_not_occurs_pnl_b=round(pnl_b_not, 2),
        event_not_occurs_net=round(net_not, 2),
        is_static_arb_valid=is_valid,
    )
    logger.info("Step 2 complete: static arb valid=%s", is_valid)
    return result


def step3_dilution_model(inp: ArbitrageInput) -> List[DilutionRow]:
    """Step 3: Model Bonding Curve dilution at various TVL levels."""
    entry_tvl = inp.pool_tvl_a if inp.pool_tvl_a > 0 else inp.investment_a * 4
    user_tokens = _bonding_curve_tokens(inp.investment_a, entry_tvl)

    multipliers = [1.0, 2.0, 5.0, 10.0, 20.0]
    rows: List[DilutionRow] = []

    for mult in multipliers:
        future_tvl = entry_tvl * mult
        total_supply = _bonding_curve_total_supply(future_tvl, base_tvl=1.0)
        if total_supply <= 0:
            total_supply = 1.0
        share_pct = (user_tokens / total_supply) * 100.0
        # Effective odds: share of total payout pool / investment
        effective_payout = (user_tokens / total_supply) * future_tvl
        effective_odds = effective_payout / inp.investment_a if inp.investment_a > 0 else 0
        dilution_pct = (1.0 - effective_odds / inp.odds_a_entry) * 100.0 if inp.odds_a_entry > 0 else 0

        rows.append(DilutionRow(
            tvl=round(future_tvl, 2),
            share_pct=round(share_pct, 4),
            effective_odds=round(effective_odds, 4),
            dilution_pct=round(dilution_pct, 2),
        ))

    logger.info("Step 3 complete: dilution table with %d rows", len(rows))
    return rows


def step4_scenario_pnl(inp: ArbitrageInput, dilution_rows: List[DilutionRow]) -> List[ScenarioPnl]:
    """Step 4: Multi-scenario dynamic P&L simulation."""
    scenarios: List[ScenarioPnl] = []

    # Find current dilution row (1x multiplier)
    current_eff_odds = dilution_rows[0].effective_odds if dilution_rows else inp.odds_a_entry
    # Find 5x dilution row
    diluted_5x_odds = dilution_rows[2].effective_odds if len(dilution_rows) > 2 else current_eff_odds * 0.3
    # Find 10x dilution row
    diluted_10x_odds = dilution_rows[3].effective_odds if len(dilution_rows) > 3 else current_eff_odds * 0.15

    # Scenario 1: Event occurs (optimistic for platform B position)
    pnl_a_1 = -inp.investment_a
    pnl_b_1 = inp.investment_b * (1.0 / inp.prob_b_entry - 1.0)
    net_1 = pnl_a_1 + pnl_b_1
    scenarios.append(ScenarioPnl(
        name="事件发生",
        description="事件按预期发生，平台 A 头寸归零，平台 B 正常获利结算",
        pnl_a=round(pnl_a_1, 2),
        pnl_b=round(pnl_b_1, 2),
        net_pnl=round(net_1, 2),
        assessment="盈利" if net_1 > 0 else "亏损",
    ))

    # Scenario 2: Event does NOT occur + pool expands 5x (pessimistic)
    pnl_a_2 = inp.investment_a * diluted_5x_odds
    pnl_b_2 = -inp.investment_b
    net_2 = pnl_a_2 + pnl_b_2
    scenarios.append(ScenarioPnl(
        name="不发生 + 池子膨胀 5x",
        description="事件未发生，平台 A 池子膨胀到 5 倍，份额严重稀释",
        pnl_a=round(pnl_a_2, 2),
        pnl_b=round(pnl_b_2, 2),
        net_pnl=round(net_2, 2),
        assessment="盈利" if net_2 > 0 else "亏损",
    ))

    # Scenario 3: Mid-exit -- sell along curve, close both sides
    entry_tvl = inp.pool_tvl_a if inp.pool_tvl_a > 0 else inp.investment_a * 4
    user_tokens = _bonding_curve_tokens(inp.investment_a, entry_tvl)
    exit_tvl = entry_tvl * 3  # assume pool grew 3x when exiting
    total_supply_at_exit = _bonding_curve_total_supply(exit_tvl)
    sell_receive = _sell_along_curve(user_tokens, total_supply_at_exit, exit_tvl)
    pnl_a_3 = sell_receive - inp.investment_a
    # Platform B: assume probability dropped to 0.40 (partial loss)
    prob_b_exit = 0.40
    pnl_b_3 = -inp.investment_b * (1.0 - prob_b_exit / inp.prob_b_entry)
    net_3 = pnl_a_3 + pnl_b_3
    scenarios.append(ScenarioPnl(
        name="中途退出",
        description="池子增长 3 倍时沿 Bonding Curve 卖出平台 A 头寸，同时平仓平台 B",
        pnl_a=round(pnl_a_3, 2),
        pnl_b=round(pnl_b_3, 2),
        net_pnl=round(net_3, 2),
        assessment="盈利" if net_3 > 0 else "亏损",
    ))

    # Scenario 4: Black swan -- platform A liquidity crisis
    pnl_a_4 = -inp.investment_a * 0.8  # recover only 20%
    pnl_b_4 = -inp.investment_b * 0.5  # partial platform B disruption
    net_4 = pnl_a_4 + pnl_b_4
    scenarios.append(ScenarioPnl(
        name="黑天鹅",
        description="平台出现流动性危机或规则变更，双边头寸均受损",
        pnl_a=round(pnl_a_4, 2),
        pnl_b=round(pnl_b_4, 2),
        net_pnl=round(net_4, 2),
        assessment="盈利" if net_4 > 0 else "亏损",
    ))

    logger.info("Step 4 complete: %d scenarios simulated", len(scenarios))
    return scenarios


def step5_exit_analysis(inp: ArbitrageInput) -> ExitAnalysis:
    """Step 5: Liquidity and exit path analysis."""
    entry_tvl = inp.pool_tvl_a if inp.pool_tvl_a > 0 else inp.investment_a * 4
    user_tokens = _bonding_curve_tokens(inp.investment_a, entry_tvl)

    # Simulate selling at current TVL
    total_supply = _bonding_curve_total_supply(entry_tvl)
    sell_receive = _sell_along_curve(user_tokens, total_supply, entry_tvl)

    slippage_pct = (1.0 - sell_receive / inp.investment_a) * 100.0 if inp.investment_a > 0 else 0
    slippage_pct = max(slippage_pct, 0.0)  # can't be negative in normal cases

    friction = "低" if slippage_pct < 3 else ("中" if slippage_pct < 8 else "高")

    optimal_note = (
        "建议在池子 TVL 未超过进入时 3 倍前退出，以控制滑点在 5% 以内。"
        if slippage_pct < 5
        else "当前滑点已偏高，建议分批退出或等待池子流动性改善后再操作。"
    )

    result = ExitAnalysis(
        exit_slippage_pct=round(slippage_pct, 2),
        exit_receive_amount=round(sell_receive, 2),
        exit_friction=friction,
        optimal_exit_note=optimal_note,
    )
    logger.info("Step 5 complete: slippage=%.2f%%", slippage_pct)
    return result


def step6_comprehensive_evaluation(
    inp: ArbitrageInput,
    static_arb: StaticArbitragePnl,
    dilution_rows: List[DilutionRow],
    scenarios: List[ScenarioPnl],
    exit: ExitAnalysis,
) -> AnalysisResult:
    """Step 6: Comprehensive evaluation and risk rating."""

    # Determine effective odds at current TVL (first row in dilution table)
    effective_odds_current = dilution_rows[0].effective_odds if dilution_rows else inp.odds_a_entry
    dilution_ratio = effective_odds_current / inp.odds_a_entry if inp.odds_a_entry > 0 else 0

    # Risk rating logic
    if not static_arb.is_static_arb_valid:
        risk_rating = "不推荐"
        recommendation = "不存在静态套利机会，两个场景中至少有一个净损益为负。建议放弃此套利策略。"
    elif dilution_ratio >= 0.70:
        risk_rating = "推荐"
        recommendation = (
            f"套利机会存在。稀释后有效赔率保持在初始赔率的 {dilution_ratio:.0%}，"
            "但需持续监控池子 TVL 变化。建议设定 TVL 上限警报，超过阈值时触发退出。"
        )
    elif dilution_ratio >= 0.50:
        risk_rating = "谨慎"
        recommendation = (
            f"静态套利空间存在但受 Bonding Curve 稀释侵蚀（有效赔率仅为初始的 {dilution_ratio:.0%}）。"
            "需设止损线并定期重新评估。考虑减小平台 B 头寸以降低风险敞口。"
        )
    else:
        risk_rating = "不推荐"
        recommendation = (
            f"Bonding Curve 稀释严重（有效赔率仅为初始的 {dilution_ratio:.0%}），"
            "静态套利假设已失效。实质为方向性交易而非无风险套利。建议放弃或仅以极小仓位参与。"
        )

    # Collect risk factors
    risk_factors = []
    risk_factors.append(f"Bonding Curve 稀释: 有效赔率从 1:{inp.odds_a_entry:.0f} 降至 1:{effective_odds_current:.1f}")
    if any(s.net_pnl < 0 for s in scenarios):
        worst = min(s.net_pnl for s in scenarios)
        risk_factors.append(f"存在亏损情景: 最差情况净亏损 {worst:.0f} USD")
    if exit.exit_slippage_pct > 5:
        risk_factors.append(f"退出滑点偏高: {exit.exit_slippage_pct:.1f}%")
    risk_factors.append("结算规则差异: 两个平台对同一事件的定义和结算条件可能不同")
    risk_factors.append("平台运营风险: 预测市场平台可能下线或修改规则")
    risk_factors.append("数据时效性: 核心定价数据为用户手动输入快照，可能与实时数据存在偏差")

    net_pnls = [s.net_pnl for s in scenarios]
    worst_case = min(net_pnls) if net_pnls else 0
    best_case = max(net_pnls) if net_pnls else 0

    result = AnalysisResult(
        event=inp.event_description,
        static_arbitrage_pnl={
            "event_occurs": {
                "pnl_a": static_arb.event_occurs_pnl_a,
                "pnl_b": static_arb.event_occurs_pnl_b,
                "net": static_arb.event_occurs_net,
            },
            "event_not_occurs": {
                "pnl_a": static_arb.event_not_occurs_pnl_a,
                "pnl_b": static_arb.event_not_occurs_pnl_b,
                "net": static_arb.event_not_occurs_net,
            },
        },
        is_static_arb_valid=static_arb.is_static_arb_valid,
        dilution_table=[asdict(r) for r in dilution_rows],
        effective_odds_current=round(effective_odds_current, 4),
        scenarios=[asdict(s) for s in scenarios],
        worst_case_pnl=round(worst_case, 2),
        best_case_pnl=round(best_case, 2),
        exit_slippage_estimate=exit.exit_slippage_pct,
        risk_rating=risk_rating,
        risk_factors=risk_factors,
        recommendation=recommendation,
    )
    logger.info("Step 6 complete: rating=%s", risk_rating)
    return result


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_analysis(params: dict) -> dict:
    """Run the full 6-step analysis pipeline.

    Args:
        params: Dictionary matching ArbitrageInput fields.

    Returns:
        Dictionary with the full AnalysisResult.
    """
    inp = ArbitrageInput(**{
        k: v for k, v in params.items()
        if k in ArbitrageInput.__dataclass_fields__
    })
    inp.validate()

    # Step 1
    snapshot = step1_market_snapshot(inp)
    logger.info("Market snapshot: %s vs %s", snapshot.platform_a_name, snapshot.platform_b_name)

    # Step 2
    static_arb = step2_static_arbitrage(inp)

    # Step 3
    dilution_rows = step3_dilution_model(inp)

    # Step 4
    scenarios = step4_scenario_pnl(inp, dilution_rows)

    # Step 5
    exit_analysis = step5_exit_analysis(inp)

    # Step 6
    result = step6_comprehensive_evaluation(inp, static_arb, dilution_rows, scenarios, exit_analysis)

    return asdict(result)


def format_report(result: dict) -> str:
    """Format analysis result into a human-readable report string."""
    lines = []
    lines.append("=== 预测市场跨平台套利分析 ===")
    lines.append("")
    lines.append(f"事件: {result['event']}")
    lines.append("")

    # Static arbitrage
    sa = result["static_arbitrage_pnl"]
    lines.append("--- 静态套利分析 ---")
    eo = sa["event_occurs"]
    lines.append(f"场景 A (事件发生):  A {eo['pnl_a']:+.0f}U + B {eo['pnl_b']:+.0f}U = 净 {eo['net']:+.0f}U")
    en = sa["event_not_occurs"]
    lines.append(f"场景 B (事件不发生): A {en['pnl_a']:+.0f}U + B {en['pnl_b']:+.0f}U = 净 {en['net']:+.0f}U")
    valid_str = "两场景均为正 -- 静态套利成立" if result["is_static_arb_valid"] else "存在亏损场景 -- 静态套利不成立"
    lines.append(f"静态套利: {valid_str}")
    lines.append("")

    # Dilution table
    lines.append("--- Bonding Curve 稀释分析 ---")
    lines.append(f"{'TVL':>12} | {'份额占比':>10} | {'有效赔率':>10} | {'稀释程度':>10}")
    lines.append("-" * 52)
    for row in result["dilution_table"]:
        lines.append(
            f"{row['tvl']:>12,.0f}U | {row['share_pct']:>9.2f}% | 1:{row['effective_odds']:>8.2f} | {row['dilution_pct']:>9.1f}%"
        )
    # Check for severe dilution
    severe = [r for r in result["dilution_table"] if r["dilution_pct"] > 50]
    if severe:
        lines.append("")
        lines.append("WARNING: 严重稀释警告 -- 部分 TVL 场景下有效赔率降幅超过 50%")
    lines.append("")

    # Scenarios
    lines.append("--- 多情景 P&L ---")
    lines.append(f"{'情景':>20} | {'A P&L':>10} | {'B P&L':>10} | {'净 P&L':>10} | {'评估':>6}")
    lines.append("-" * 70)
    for s in result["scenarios"]:
        lines.append(
            f"{s['name']:>20} | {s['pnl_a']:>+10.0f}U | {s['pnl_b']:>+10.0f}U | {s['net_pnl']:>+10.0f}U | {s['assessment']:>6}"
        )
    lines.append("")

    # Exit analysis
    lines.append(f"退出滑点估算: {result['exit_slippage_estimate']:.1f}%")
    lines.append("")

    # Final rating
    lines.append("--- 综合评估 ---")
    lines.append(f"风险评级: {result['risk_rating']}")
    lines.append(f"最佳情景净 P&L: {result['best_case_pnl']:+,.0f}U")
    lines.append(f"最差情景净 P&L: {result['worst_case_pnl']:+,.0f}U")
    lines.append("")
    lines.append("风险因素:")
    for rf in result["risk_factors"]:
        lines.append(f"  - {rf}")
    lines.append("")
    lines.append(f"建议: {result['recommendation']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    # Example from the PRD tweet case
    example_params = {
        "event_description": "某项目是否在2026年底前发币",
        "platform_a": "42 (Polymarket)",
        "platform_b": "Opinion",
        "position_a_type": "NO (No Token Launch)",
        "position_b_type": "YES (63% 概率发币)",
        "investment_a": 500,
        "investment_b": 5000,
        "odds_a_entry": 18,
        "prob_b_entry": 0.63,
        "pool_tvl_a": 4000,
        "pool_type": "bonding_curve",
        "time_horizon": "2026-12-31",
    }

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    result = run_analysis(example_params)
    report = format_report(result)
    print(report)
    print("\n--- JSON Output ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
