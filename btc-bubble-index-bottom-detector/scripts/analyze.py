#!/usr/bin/env python3
"""
BTC Bubble Index Bottom Detector
Approximates the "Bitcoin Bubble Index" using MVRV + NVT on-chain metrics.

Usage:
    python analyze.py [--bottom_threshold=12] [--lookback_days=1460] [--price_target=200000]

Data sources: Antseer MCP (ant_spot_market_structure, ant_token_analytics)
Methodology credit: @monkeyjiang
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MVRV_WEIGHT = 0.6
NVT_WEIGHT = 0.4

DEFAULT_BOTTOM_THRESHOLD = 12.0
DEFAULT_LOOKBACK_DAYS = 1460  # ~4 years


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def minmax_normalize(value: float, series: list[float]) -> float:
    """Normalize value to [0, 100] based on historical min/max."""
    if not series:
        return 50.0
    lo = min(series)
    hi = max(series)
    if hi == lo:
        return 50.0
    return max(0.0, min(100.0, (value - lo) / (hi - lo) * 100))


def compute_bubble_proxy(mvrv_current: float, mvrv_series: list[float],
                          nvt_current: float, nvt_series: list[float]) -> dict:
    """Compute the composite bubble proxy index (0-100)."""
    mvrv_norm = minmax_normalize(mvrv_current, mvrv_series)
    nvt_norm = minmax_normalize(nvt_current, nvt_series)
    bubble_proxy = mvrv_norm * MVRV_WEIGHT + nvt_norm * NVT_WEIGHT
    return {
        "bubble_proxy": round(bubble_proxy, 2),
        "mvrv_norm": round(mvrv_norm, 1),
        "nvt_norm": round(nvt_norm, 1),
    }


# ---------------------------------------------------------------------------
# Historical signal scanning
# ---------------------------------------------------------------------------

def find_bottom_signals(bubble_proxy_series: list[dict],
                         price_series: list[dict],
                         threshold: float) -> list[dict]:
    """
    Scan historical bubble proxy values for periods below threshold.
    Each series entry: {"date": "YYYY-MM-DD", "value": float}
    Returns a list of signal events with forward return statistics.
    """
    signals = []
    in_signal = False

    price_map = {p["date"]: p["value"] for p in price_series}

    for i, entry in enumerate(bubble_proxy_series):
        val = entry["value"]
        date = entry["date"]

        if val <= threshold and not in_signal:
            in_signal = True
            entry_price = price_map.get(date)
            if entry_price is None:
                continue

            # Compute forward returns
            def get_price_after(days: int) -> Optional[float]:
                target_date = (
                    datetime.strptime(date, "%Y-%m-%d") + timedelta(days=days)
                ).strftime("%Y-%m-%d")
                return price_map.get(target_date)

            p90 = get_price_after(90)
            p180 = get_price_after(180)
            p365 = get_price_after(365)

            # Max drawdown within 90 days
            drawdowns = []
            for j in range(1, min(91, len(bubble_proxy_series) - i)):
                future_date = bubble_proxy_series[i + j]["date"]
                future_price = price_map.get(future_date)
                if future_price and entry_price:
                    drawdowns.append((future_price - entry_price) / entry_price * 100)

            min_dd = min(drawdowns) if drawdowns else 0.0

            signals.append({
                "date": date,
                "index_value": round(val, 2),
                "entry_price": round(entry_price, 2),
                "return_90d": round((p90 - entry_price) / entry_price * 100, 1) if p90 else None,
                "return_180d": round((p180 - entry_price) / entry_price * 100, 1) if p180 else None,
                "return_365d": round((p365 - entry_price) / entry_price * 100, 1) if p365 else None,
                "max_drawdown_90d": round(min_dd, 1),
            })

        elif val > threshold:
            in_signal = False

    return signals


def summarize_signals(signals: list[dict]) -> dict:
    """Aggregate historical signal statistics."""
    if not signals:
        return {
            "count": 0,
            "avg_return_90d": None,
            "avg_return_180d": None,
            "avg_return_365d": None,
            "avg_max_drawdown": None,
            "low_sample_warning": True,
        }

    def avg(values):
        valid = [v for v in values if v is not None]
        return round(sum(valid) / len(valid), 1) if valid else None

    drawdowns = sorted([s["max_drawdown_90d"] for s in signals if s["max_drawdown_90d"] is not None])
    median_dd = drawdowns[len(drawdowns) // 2] if drawdowns else None

    return {
        "count": len(signals),
        "avg_return_90d": avg([s["return_90d"] for s in signals]),
        "avg_return_180d": avg([s["return_180d"] for s in signals]),
        "avg_return_365d": avg([s["return_365d"] for s in signals]),
        "avg_max_drawdown": median_dd,
        "low_sample_warning": len(signals) < 3,
    }


# ---------------------------------------------------------------------------
# Signal classification
# ---------------------------------------------------------------------------

def classify_signal(bubble_proxy: float, threshold: float,
                     trend_30d_change: float) -> dict:
    """Assign a signal label and compute signal strength."""
    strength = max(0.0, min(100.0, (1 - bubble_proxy / threshold) * 100))

    if bubble_proxy <= threshold:
        if trend_30d_change <= 0:
            label = "Strong Bottom Signal"
            trend_label = "confirmed"
        else:
            label = "Strong Bottom Signal"
            trend_label = "confirmed (recovering)"
    elif bubble_proxy <= threshold * 1.3:
        label = "Approaching Bottom"
        trend_label = "approaching" if trend_30d_change < 0 else "flat"
        strength = strength * 0.7  # partial credit
    else:
        label = "Not in Bottom Zone"
        trend_label = "exiting" if trend_30d_change < 0 else "above threshold"
        strength = max(0.0, strength)

    return {
        "signal_label": label,
        "signal_strength": round(strength, 0),
        "index_trend": trend_label,
    }


# ---------------------------------------------------------------------------
# Report formatter
# ---------------------------------------------------------------------------

def format_report(
    current_price: float,
    bubble_proxy_result: dict,
    signal: dict,
    historical: dict,
    threshold: float,
    lookback_years: float,
    analysis_date: str,
    price_target: Optional[float] = None,
) -> str:
    """Render the bottom detection report. Max ~300 words."""

    bp = bubble_proxy_result["bubble_proxy"]
    mvrv_norm = bubble_proxy_result["mvrv_norm"]
    nvt_norm = bubble_proxy_result["nvt_norm"]

    low_sample = historical.get("low_sample_warning", False)
    sample_note = "  [WARNING: <3 historical events, low statistical significance]" if low_sample else ""

    rr_section = ""
    if price_target:
        upside = (price_target - current_price) / current_price * 100
        avg_dd = historical.get("avg_max_drawdown") or 18.0
        rr = upside / abs(avg_dd) if avg_dd else None
        rr_line = f"{rr:.1f}:1" if rr else "N/A"
        rr_section = (
            f"\n--- Risk-Reward Analysis (target: ${price_target:,.0f}) ---\n"
            f"Potential Upside: +{upside:.1f}%\n"
            f"Risk-Reward Ratio: {rr_line}\n"
            f"Historical Avg Max Drawdown: {avg_dd:.1f}%"
        )

    def fmt_pct(v):
        return f"{v:+.1f}%" if v is not None else "N/A"

    report = f"""=== BTC Bubble Proxy Index — Bottom Detection Report ===

Asset: BTC  |  Analysis Date: {analysis_date}
Current Price: ${current_price:,.0f}
Bubble Proxy Index: {bp:.1f} / 100  (threshold: {threshold})

Signal: {signal['signal_label']}
Signal Strength: {signal['signal_strength']:.0f}/100
Index Trend: {signal['index_trend']}

--- Historical Validation ({lookback_years:.0f}-year lookback) ---
Signals Found: {historical['count']}{sample_note}
Avg Return  90d: {fmt_pct(historical.get('avg_return_90d'))}
Avg Return 365d: {fmt_pct(historical.get('avg_return_365d'))}
Median Max Drawdown After Entry: {historical['avg_max_drawdown']:.1f}% if historical['avg_max_drawdown'] else 'N/A'

--- Component Scores ---
MVRV (60%): {mvrv_norm:.0f}/100
NVT  (40%): {nvt_norm:.0f}/100{rr_section}

Note: This index is a MVRV+NVT proxy, not the original monkeyjiang bubble index.
Methodology credit: @monkeyjiang. Not investment advice."""

    return report


# ---------------------------------------------------------------------------
# Main entry point (standalone testing with mock data)
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="BTC Bubble Index Bottom Detector")
    parser.add_argument("--bottom_threshold", type=float, default=DEFAULT_BOTTOM_THRESHOLD)
    parser.add_argument("--lookback_days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    parser.add_argument("--price_target", type=float, default=None)
    args = parser.parse_args()

    print("[INFO] This script is a reference implementation.")
    print("[INFO] In production, data is fetched via Antseer MCP tools.")
    print("[INFO] Use /btc-bubble-index-bottom-detector in Claude Code to run the full analysis.")
    print()
    print(f"Configuration:")
    print(f"  bottom_threshold: {args.bottom_threshold}")
    print(f"  lookback_days:    {args.lookback_days}")
    print(f"  price_target:     {args.price_target or 'not set'}")


if __name__ == "__main__":
    main()
