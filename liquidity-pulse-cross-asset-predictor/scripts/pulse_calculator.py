#!/usr/bin/env python3
"""
流动性供应脉冲跨资产价格预测计算器
Liquidity Pulse Cross-Asset Price Predictor

方法论来源: @xiaomustock
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


@dataclass
class ReferenceAsset:
    name: str
    ath_price: float
    ath_year: Optional[str]
    new_ath_price: float
    new_ath_date: date
    pulse_start_price: float
    pulse_start_date: date


@dataclass
class TargetAsset:
    name: str
    ath_price: float
    current_price: float
    current_date: date
    currency: str = "USD"


@dataclass
class PulseParams:
    total_amplification: float       # reference_new_ath / reference_ath
    acceleration_gain: float         # reference_new_ath / reference_pulse_start
    duration_trading_days: int       # trading days from pulse_start to new_ath
    pulse_start_discount: float      # reference_pulse_start / reference_new_ath


@dataclass
class PredictionResult:
    asset_name: str
    current_price: float
    predicted_peak_price: float
    upside_pct: float
    predicted_peak_date: date
    confidence_level: str            # 高 / 中 / 低
    equivalent_position_deviation: float  # % deviation in equivalent mapping
    equivalent_position_valid: bool


def count_trading_days(start: date, days: int) -> date:
    """Count forward N trading days (excluding weekends). Simplified: no holiday calendar."""
    current = start
    remaining = days
    while remaining > 0:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Monday=0 ... Friday=4
            remaining -= 1
    return current


def count_trading_days_between(start: date, end: date) -> int:
    """Count trading days between two dates (weekdays only)."""
    count = 0
    current = start + timedelta(days=1)
    while current <= end:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count


def calculate_pulse_params(ref: ReferenceAsset) -> PulseParams:
    total_amp = ref.new_ath_price / ref.ath_price
    accel_gain = ref.new_ath_price / ref.pulse_start_price
    duration = count_trading_days_between(ref.pulse_start_date, ref.new_ath_date)
    discount = ref.pulse_start_price / ref.new_ath_price
    return PulseParams(
        total_amplification=total_amp,
        acceleration_gain=accel_gain,
        duration_trading_days=duration,
        pulse_start_discount=discount,
    )


def calculate_equivalent_position(ref: ReferenceAsset, target: TargetAsset) -> tuple[float, float]:
    """
    Returns (target_above_ath_pct, equivalent_ref_price).
    Checks if target's position maps to ~reference_pulse_start_price.
    """
    target_above_ath_pct = (target.current_price - target.ath_price) / target.ath_price
    equivalent_ref_price = ref.ath_price * (1 + target_above_ath_pct)
    return target_above_ath_pct, equivalent_ref_price


def predict_target(
    ref: ReferenceAsset,
    params: PulseParams,
    target: TargetAsset,
    trading_days_offset: int = 0,
) -> PredictionResult:
    # Equivalent position check
    target_above_ath_pct, equiv_ref_price = calculate_equivalent_position(ref, target)
    deviation = abs(equiv_ref_price - ref.pulse_start_price) / ref.pulse_start_price
    valid = deviation < 0.15

    # Peak price using ATH-binding formula (matches original tweet methodology)
    predicted_peak = target.ath_price * (ref.new_ath_price / ref.ath_price)
    upside_pct = (predicted_peak - target.current_price) / target.current_price * 100

    # Peak date
    total_days = params.duration_trading_days + trading_days_offset
    peak_date = count_trading_days(target.current_date, total_days)

    # Confidence
    if deviation < 0.05 and valid:
        confidence = "高"
    elif deviation < 0.15:
        confidence = "中"
    else:
        confidence = "低"

    return PredictionResult(
        asset_name=target.name,
        current_price=target.current_price,
        predicted_peak_price=predicted_peak,
        upside_pct=upside_pct,
        predicted_peak_date=peak_date,
        confidence_level=confidence,
        equivalent_position_deviation=deviation * 100,
        equivalent_position_valid=valid,
    )


def predict_derived_asset(
    name: str,
    current_price: float,
    current_date: date,
    main_target_current: float,
    main_target_peak: float,
    peak_date: date,
    currency: str = "USD",
) -> PredictionResult:
    """
    Predict a derived asset using price ratio from the main target asset.
    """
    ratio = main_target_peak / main_target_current
    predicted_peak = current_price * ratio
    upside_pct = (predicted_peak - current_price) / current_price * 100

    return PredictionResult(
        asset_name=name,
        current_price=current_price,
        predicted_peak_price=predicted_peak,
        upside_pct=upside_pct,
        predicted_peak_date=peak_date,
        confidence_level="低",
        equivalent_position_deviation=float("nan"),
        equivalent_position_valid=False,
    )


def format_price(price: float, currency: str = "", decimals: int = 0) -> str:
    if price >= 1_000_000:
        return f"{price / 10000:.1f}万 {currency}".strip()
    elif price >= 1_000:
        return f"{price:,.0f} {currency}".strip()
    else:
        return f"{price:,.{decimals}f} {currency}".strip()


def print_report(
    ref: ReferenceAsset,
    params: PulseParams,
    results: list[PredictionResult],
    analysis_date: date,
) -> None:
    print(f"\n=== 流动性供应脉冲跨资产价格预测 ===")
    print(f"分析日期: {analysis_date}")
    print()
    print(f"参考资产: {ref.name}")
    print(f"├── 历史前高: {ref.ath_price:.1f} ({ref.ath_year or 'N/A'})")
    print(f"├── 本轮新高: {ref.new_ath_price:.1f} ({ref.new_ath_date})")
    print(f"├── 脉冲总倍幅: {params.total_amplification:.2f}x")
    print(f"├── 脉冲加速段起点: {ref.pulse_start_price:.1f} ({ref.pulse_start_date})")
    print(f"└── 脉冲加速段持续: {params.duration_trading_days}个交易日")
    print()
    print("目标资产预测:")
    header = f"{'资产':<20} {'当前价格':>12} {'预测峰值':>12} {'上涨空间':>8} {'预计达峰':>12} {'置信度':>6}"
    print(header)
    print("-" * len(header))
    for r in results:
        curr_str = f"{r.current_price:,.0f}"
        peak_str = f"{r.predicted_peak_price:,.0f}"
        print(
            f"{r.asset_name:<20} {curr_str:>12} {peak_str:>12} "
            f"{r.upside_pct:>+7.1f}% {str(r.predicted_peak_date):>12} {r.confidence_level:>6}"
        )
    print()
    print("等价位置验证:")
    for r in results:
        if not math.isnan(r.equivalent_position_deviation):
            mark = "✓" if r.equivalent_position_valid else "✗"
            print(f"  {r.asset_name}: 等价位置偏差 {r.equivalent_position_deviation:.1f}% {mark}")
    print()
    print("关键假设:")
    print("  ① 参考资产与目标资产处于同一宏观流动性供应脉冲环境")
    print("  ② 各资产历史ATH为有效的长周期估值锚定点")
    print("  ③ 脉冲加速段时间窗口内无重大假期干扰（简化：仅排除周末）")
    print("  ④ 目标资产间相对强弱比率在预测周期内保持稳定（联动资产）")
    print()
    print("风险提示:")
    print("  - 宏观政策突变（加息、地缘政治）可能提前终止脉冲")
    print("  - 半导体/目标行业基本面变化可能破坏技术形态")
    print("  - 基于单一历史案例推演，不代表必然重复")
    print()
    print("⚠️ 本输出不构成投资建议。方法论归属 @xiaomustock。")


# ─────────────────────────────────────────────
# 示例：重现推文原始案例（白银 → 海力士等）
# ─────────────────────────────────────────────
if __name__ == "__main__":
    ref = ReferenceAsset(
        name="白银 (Silver)",
        ath_price=50.0,
        ath_year="1980",
        new_ath_price=120.0,
        new_ath_date=date(2026, 1, 29),
        pulse_start_price=68.5,
        pulse_start_date=date(2025, 12, 20),
    )

    params = calculate_pulse_params(ref)

    targets = [
        TargetAsset("海力士 (SK Hynix)", ath_price=770000, current_price=1070000,
                    current_date=date(2026, 2, 27), currency="KRW"),
        TargetAsset("三星 (Samsung)", ath_price=240000, current_price=240000,
                    current_date=date(2026, 2, 27), currency="KRW"),
    ]

    results = [predict_target(ref, params, t) for t in targets]

    # Derived asset: EWY (ratio from Hynix)
    if results:
        main = results[0]
        ewy = predict_derived_asset(
            name="EWY ETF",
            current_price=140.0,
            current_date=date(2026, 2, 27),
            main_target_current=main.current_price,
            main_target_peak=main.predicted_peak_price,
            peak_date=main.predicted_peak_date,
            currency="USD",
        )
        results.append(ewy)

    print_report(ref, params, results, analysis_date=date(2026, 2, 27))
