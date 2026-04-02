"""
Prediction Market Bonding Curve Arbitrage Validator

Analyzes whether cross-platform arbitrage between two prediction markets
is viable when one platform uses Bonding Curve pricing.

Five-step analysis:
  1. Static arbitrage PnL calculation
  2. Bonding Curve pool share dilution simulation
  3. Dynamic PnL recalculation with dilution
  4. Early exit path analysis
  5. Comprehensive verdict determination
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ArbValidator:
    """Cross-platform prediction market arbitrage validator with Bonding Curve dilution analysis."""

    # Event
    event_description: str = ""

    # Platform A (typically fixed-odds / AMM)
    platform_a_name: str = ""
    platform_a_odds: float = 0.0       # probability 0.01-0.99
    platform_a_bet_amount: float = 0.0  # USD
    platform_a_pricing_model: str = "AMM"

    # Platform B (typically Bonding Curve)
    platform_b_name: str = ""
    platform_b_pool: str = ""
    platform_b_odds: float = 0.0       # multiplier, e.g. 10 means 1:10
    platform_b_bet_amount: float = 0.0  # USD
    platform_b_pool_tvl: float = 0.0   # USD
    platform_b_pricing_model: str = "BondingCurve"

    # Optional
    time_horizon: str = "6 months"
    pool_growth_scenarios: list[float] = field(default_factory=lambda: [2.0, 5.0, 10.0])

    # --- Public API ---

    def run(self) -> dict[str, Any]:
        """Execute the full five-step analysis and return the structured report."""
        errors = self._validate_inputs()
        if errors:
            return {
                "status": "error",
                "errors": errors,
            }

        static_pnl = self._step1_static_pnl()
        dilution_table = self._step2_dilution_simulation()
        dynamic_pnl_matrix = self._step3_dynamic_pnl(static_pnl, dilution_table)
        early_exit = self._step4_early_exit(dilution_table)
        verdict, risk_warnings, strategy = self._step5_verdict(
            static_pnl, dynamic_pnl_matrix, early_exit
        )

        report = {
            "status": "completed",
            "event_description": self.event_description,
            "platform_a": {
                "name": self.platform_a_name,
                "odds": self.platform_a_odds,
                "bet_amount": self.platform_a_bet_amount,
                "pricing_model": self.platform_a_pricing_model,
            },
            "platform_b": {
                "name": self.platform_b_name,
                "pool": self.platform_b_pool,
                "odds": self.platform_b_odds,
                "bet_amount": self.platform_b_bet_amount,
                "pool_tvl": self.platform_b_pool_tvl,
                "pricing_model": self.platform_b_pricing_model,
            },
            "static_pnl": static_pnl,
            "dilution_table": dilution_table,
            "dynamic_pnl_matrix": dynamic_pnl_matrix,
            "early_exit_comparison": early_exit,
            "verdict": verdict,
            "risk_warnings": risk_warnings,
            "strategy_suggestion": strategy,
        }

        logger.info("Analysis complete: verdict=%s", verdict)
        return report

    # --- Step 1: Static Arbitrage PnL ---

    def _step1_static_pnl(self) -> dict[str, Any]:
        """Calculate idealized arbitrage PnL assuming fixed odds on both platforms."""
        bet_a = self.platform_a_bet_amount
        prob_a = self.platform_a_odds
        bet_b = self.platform_b_bet_amount
        odds_b = self.platform_b_odds

        # Scenario A: event happens -> Platform A wins, Platform B loses
        pnl_a_event_yes = bet_a * (1.0 / prob_a - 1.0)
        pnl_b_event_yes = -bet_b
        net_event_yes = pnl_a_event_yes + pnl_b_event_yes

        # Scenario B: event does not happen -> Platform A loses, Platform B wins
        pnl_a_event_no = -bet_a
        pnl_b_event_no = bet_b * (odds_b - 1.0)  # net profit from odds
        net_event_no = pnl_a_event_no + pnl_b_event_no

        result = {
            "event_happens": {
                "platform_a_pnl": round(pnl_a_event_yes, 2),
                "platform_b_pnl": round(pnl_b_event_yes, 2),
                "net_pnl": round(net_event_yes, 2),
            },
            "event_not_happens": {
                "platform_a_pnl": round(pnl_a_event_no, 2),
                "platform_b_pnl": round(pnl_b_event_no, 2),
                "net_pnl": round(net_event_no, 2),
            },
            "total_capital_deployed": round(bet_a + bet_b, 2),
        }

        logger.info(
            "Step 1 - Static PnL: event_yes=%.2f, event_no=%.2f",
            net_event_yes,
            net_event_no,
        )
        return result

    # --- Step 2: Bonding Curve Dilution Simulation ---

    def _step2_dilution_simulation(self) -> list[dict[str, Any]]:
        """Simulate pool share dilution under various TVL growth scenarios.

        Uses conservative linear dilution approximation:
          initial_share = bet_amount / (pool_tvl + bet_amount)
          diluted_share = bet_amount / new_tvl
        """
        bet_b = self.platform_b_bet_amount
        tvl = self.platform_b_pool_tvl
        odds_b = self.platform_b_odds

        # Entry share (at time of buy)
        entry_share = bet_b / (tvl + bet_b)

        table = []

        # Include 1x (no growth) as baseline
        all_scenarios = [1.0] + [s for s in self.pool_growth_scenarios if s != 1.0]

        for multiplier in sorted(all_scenarios):
            new_tvl = tvl * multiplier
            # Conservative: diluted share based on new TVL
            # The bet_amount is already part of the pool at entry, so at 1x the share
            # is entry_share. At higher TVL we approximate linearly.
            if multiplier <= 1.0:
                current_share = entry_share
            else:
                current_share = bet_b / new_tvl

            # Estimated payout if event resolves in favor of this pool
            # Total pool payout * share (simplified: pool pays out its TVL to winners)
            estimated_payout = new_tvl * current_share
            # The "promised" payout at entry odds
            promised_payout = bet_b * odds_b

            table.append({
                "tvl_multiplier": multiplier,
                "pool_tvl": round(new_tvl, 2),
                "user_share_pct": round(current_share * 100, 4),
                "estimated_payout": round(estimated_payout, 2),
                "promised_payout": round(promised_payout, 2),
                "payout_gap": round(promised_payout - estimated_payout, 2),
                "dilution_vs_entry": round((1 - current_share / entry_share) * 100, 2)
                if entry_share > 0
                else 0,
            })

        logger.info(
            "Step 2 - Dilution simulation: %d scenarios, entry_share=%.4f%%",
            len(table),
            entry_share * 100,
        )
        return table

    # --- Step 3: Dynamic PnL with Dilution ---

    def _step3_dynamic_pnl(
        self,
        static_pnl: dict[str, Any],
        dilution_table: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Recalculate PnL incorporating Bonding Curve dilution effects."""
        bet_a = self.platform_a_bet_amount
        prob_a = self.platform_a_odds

        # Platform A PnL is unaffected by Platform B's Bonding Curve
        pnl_a_yes = bet_a * (1.0 / prob_a - 1.0)
        pnl_a_no = -bet_a

        matrix = []
        for row in dilution_table:
            # Platform B actual payout with dilution (event not happens = B wins)
            actual_b_payout = row["estimated_payout"]
            pnl_b_no_diluted = actual_b_payout - self.platform_b_bet_amount

            # Event happens: B loses entire bet (same as static)
            pnl_b_yes = -self.platform_b_bet_amount

            net_yes = pnl_a_yes + pnl_b_yes
            net_no = pnl_a_no + pnl_b_no_diluted

            # Compare with static
            static_net_no = static_pnl["event_not_happens"]["net_pnl"]

            matrix.append({
                "tvl_multiplier": row["tvl_multiplier"],
                "event_happens": {
                    "platform_a_pnl": round(pnl_a_yes, 2),
                    "platform_b_pnl": round(pnl_b_yes, 2),
                    "net_pnl": round(net_yes, 2),
                },
                "event_not_happens": {
                    "platform_a_pnl": round(pnl_a_no, 2),
                    "platform_b_pnl": round(pnl_b_no_diluted, 2),
                    "net_pnl": round(net_no, 2),
                    "vs_static_delta": round(net_no - static_net_no, 2),
                },
            })

        logger.info("Step 3 - Dynamic PnL matrix: %d entries", len(matrix))
        return matrix

    # --- Step 4: Early Exit Path Analysis ---

    def _step4_early_exit(
        self,
        dilution_table: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Evaluate selling along the Bonding Curve before event settlement.

        If TVL grows, the curve price rises. Early participants can sell their
        position at a profit by exiting before settlement. This models the
        "sell to latecomers" path vs "hold to expiry".
        """
        bet_b = self.platform_b_bet_amount
        tvl = self.platform_b_pool_tvl
        entry_price_per_unit = bet_b / (tvl + bet_b)  # normalized entry cost

        exit_scenarios = []
        for row in dilution_table:
            multiplier = row["tvl_multiplier"]
            if multiplier <= 1.0:
                # No growth, no early exit premium
                continue

            new_tvl = row["pool_tvl"]
            # Simplified Bonding Curve exit: if TVL grew, the curve price also grew.
            # Approximate exit value as proportional to TVL growth of user's original share.
            # At entry: paid bet_b for share. Current "mark to market" value of that share
            # scales with how much the curve price has risen.
            # Conservative estimate: exit_value ~ bet_b * sqrt(multiplier)
            # (sub-linear because selling pushes price down along the curve)
            import math

            exit_value = bet_b * math.sqrt(multiplier)
            early_exit_profit = exit_value - bet_b

            # Hold to expiry: get estimated_payout if win, lose bet if lose
            hold_payout_win = row["estimated_payout"]
            hold_expected_value = hold_payout_win * 0.5 - bet_b * 0.5  # 50/50 assumption

            exit_scenarios.append({
                "tvl_multiplier": multiplier,
                "early_exit_value": round(exit_value, 2),
                "early_exit_profit": round(early_exit_profit, 2),
                "early_exit_roi_pct": round((early_exit_profit / bet_b) * 100, 2),
                "hold_to_expiry_expected_value": round(hold_expected_value, 2),
                "recommendation": "early_exit"
                if early_exit_profit > hold_expected_value
                else "hold_to_expiry",
            })

        # Summary
        exit_preferred_count = sum(
            1 for s in exit_scenarios if s["recommendation"] == "early_exit"
        )

        result = {
            "scenarios": exit_scenarios,
            "summary": {
                "early_exit_preferred_in": f"{exit_preferred_count}/{len(exit_scenarios)} scenarios",
                "note": "Early exit values use sqrt(multiplier) approximation for Bonding Curve "
                "sell pressure. Actual values depend on the specific curve formula.",
            },
        }

        logger.info(
            "Step 4 - Early exit: preferred in %d/%d scenarios",
            exit_preferred_count,
            len(exit_scenarios),
        )
        return result

    # --- Step 5: Comprehensive Verdict ---

    def _step5_verdict(
        self,
        static_pnl: dict[str, Any],
        dynamic_matrix: list[dict[str, Any]],
        early_exit: dict[str, Any],
    ) -> tuple[str, list[str], str]:
        """Determine overall arbitrage viability and generate risk warnings + strategy."""
        risk_warnings: list[str] = []
        bet_a = self.platform_a_bet_amount
        bet_b = self.platform_b_bet_amount
        total_capital = bet_a + bet_b

        # Analyze dynamic PnL across scenarios
        all_positive = True
        any_positive = False
        low_growth_positive = False

        for entry in dynamic_matrix:
            net_yes = entry["event_happens"]["net_pnl"]
            net_no = entry["event_not_happens"]["net_pnl"]
            min_pnl = min(net_yes, net_no)

            if min_pnl < 0:
                all_positive = False
            if net_yes > 0 or net_no > 0:
                any_positive = True
            if entry["tvl_multiplier"] <= 2.0 and min_pnl > 0:
                low_growth_positive = True

        # Check static vs dynamic divergence
        static_no_pnl = static_pnl["event_not_happens"]["net_pnl"]
        if dynamic_matrix:
            worst_dynamic_no = min(
                e["event_not_happens"]["net_pnl"] for e in dynamic_matrix
            )
            if static_no_pnl > 0 and worst_dynamic_no < 0:
                risk_warnings.append(
                    "Static analysis shows profit but dynamic analysis shows loss "
                    "after Bonding Curve dilution -- static odds are misleading."
                )

        # Bonding Curve specific warnings
        if self.platform_b_pricing_model == "BondingCurve":
            risk_warnings.append(
                "Platform B uses Bonding Curve pricing: displayed odds do not represent "
                "guaranteed payout. Actual returns depend on final pool size at settlement."
            )
            risk_warnings.append(
                "Share dilution is modeled with linear approximation. "
                "Actual Bonding Curve may produce more severe dilution."
            )

        # Capital concentration warning
        if bet_b / total_capital > 0.3:
            risk_warnings.append(
                f"Platform B bet ({bet_b:.0f} USD) represents "
                f"{bet_b / total_capital * 100:.0f}% of total capital -- "
                f"high exposure to Bonding Curve dilution risk."
            )

        # Settlement risk
        risk_warnings.append(
            "Cross-platform settlement rules may differ. "
            "Verify both platforms use the same event resolution criteria."
        )

        # Determine verdict
        if all_positive:
            verdict = "VIABLE"
            strategy = (
                f"Arbitrage appears viable across all TVL growth scenarios. "
                f"Deploy {bet_a:.0f} USD on {self.platform_a_name} "
                f"and {bet_b:.0f} USD on {self.platform_b_name}. "
                f"Monitor pool TVL and set alerts at 5x growth to reassess. "
                f"Consider partial early exit if TVL grows rapidly."
            )
        elif low_growth_positive or any_positive:
            verdict = "CONDITIONAL"
            strategy = (
                f"Arbitrage is conditionally viable under low TVL growth. "
                f"If entering, keep position small (max 5% of portfolio), "
                f"set TVL monitoring alerts on {self.platform_b_name} "
                f"pool '{self.platform_b_pool}', "
                f"and plan early exit along the Bonding Curve if TVL exceeds 3x "
                f"current level ({self.platform_b_pool_tvl:.0f} USD). "
                f"Do not rely on static odds for PnL projection."
            )
        else:
            verdict = "NOT_VIABLE"
            strategy = (
                f"Arbitrage is not viable. Bonding Curve dilution on "
                f"{self.platform_b_name} erodes Platform B returns across "
                f"all modeled TVL scenarios. The static odds of "
                f"1:{self.platform_b_odds:.0f} are misleading. "
                f"If you still believe in the event direction, consider a "
                f"directional bet on a single platform with fixed odds instead."
            )

        logger.info("Step 5 - Verdict: %s", verdict)
        return verdict, risk_warnings, strategy

    # --- Input Validation ---

    def _validate_inputs(self) -> list[str]:
        """Validate all input parameters and return list of errors (empty if valid)."""
        errors = []

        if not self.event_description:
            errors.append("event_description is required")
        if not self.platform_a_name:
            errors.append("platform_a_name is required")
        if not self.platform_b_name:
            errors.append("platform_b_name is required")
        if not self.platform_b_pool:
            errors.append("platform_b_pool is required")

        if not (0.01 <= self.platform_a_odds <= 0.99):
            errors.append(
                f"platform_a_odds must be between 0.01 and 0.99, got {self.platform_a_odds}"
            )
        if self.platform_b_odds <= 1.0:
            errors.append(
                f"platform_b_odds must be greater than 1.0, got {self.platform_b_odds}"
            )

        if self.platform_a_bet_amount <= 0:
            errors.append("platform_a_bet_amount must be positive")
        if self.platform_b_bet_amount <= 0:
            errors.append("platform_b_bet_amount must be positive")
        if self.platform_b_pool_tvl <= 0:
            errors.append("platform_b_pool_tvl must be positive")

        valid_models_a = {"AMM", "OrderBook", "Fixed"}
        if self.platform_a_pricing_model not in valid_models_a:
            errors.append(
                f"platform_a_pricing_model must be one of {valid_models_a}, "
                f"got '{self.platform_a_pricing_model}'"
            )

        valid_models_b = {"BondingCurve", "AMM", "Fixed"}
        if self.platform_b_pricing_model not in valid_models_b:
            errors.append(
                f"platform_b_pricing_model must be one of {valid_models_b}, "
                f"got '{self.platform_b_pricing_model}'"
            )

        if not self.pool_growth_scenarios:
            errors.append("pool_growth_scenarios must contain at least one value")
        else:
            for s in self.pool_growth_scenarios:
                if s < 1.0:
                    errors.append(
                        f"pool_growth_scenarios values must be >= 1.0, got {s}"
                    )

        if errors:
            logger.warning("Input validation failed: %s", errors)

        return errors


def run_example() -> dict[str, Any]:
    """Run the example from the original tweet analysis (Polymarket vs 42)."""
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
        pool_growth_scenarios=[2.0, 5.0, 10.0],
    )
    return validator.run()


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    result = run_example()
    print(json.dumps(result, indent=2, ensure_ascii=False))
