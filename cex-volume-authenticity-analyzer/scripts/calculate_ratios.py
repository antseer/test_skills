#!/usr/bin/env python3
"""
CEX Volume Authenticity Analyzer — Ratio Calculation Helper

用法：
    python3 calculate_ratios.py --data data.csv --benchmark_ratio 1.44 --tolerance_pct 15

CSV 格式（UTF-8，含标题行）：
    exchange,spot_30d_usd,deriv_30d_usd,reserve_usd,btc_reserve_ratio

输出：
    每家交易所的资金效率比率、可疑交易量和调整后市场份额
"""

import argparse
import csv
import json
import sys
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExchangeData:
    exchange: str
    spot_30d: float         # 现货30天交易量（USD）
    deriv_30d: float        # 衍生品30天交易量（USD）
    reserve_usd: float      # 核心储备总量（USD）
    btc_reserve_ratio: Optional[float] = None  # BTC 超额储备率（%），如 237 表示 237%


@dataclass
class ExchangeResult:
    exchange: str
    total_volume_30d: float
    total_reserve_usd: float
    daily_avg_volume: float
    total_ratio: float
    spot_ratio: float
    deriv_ratio: float
    authenticity_label: str
    suspicious_volume_30d: float
    authenticity_pct: float
    reported_share: float = 0.0
    adjusted_share: float = 0.0
    share_delta: float = 0.0
    note: str = ""


def classify(total_ratio: float, benchmark_ratio: float, threshold: float) -> str:
    if total_ratio <= benchmark_ratio:
        return "高度可信"
    elif total_ratio <= threshold:
        return "正常范围"
    elif total_ratio <= threshold * 1.5:
        return "灰色地带"
    else:
        return "高度可疑"


def analyze(
    exchanges: list[ExchangeData],
    benchmark_ratio: float = 1.44,
    tolerance_pct: float = 15.0,
    time_range_days: int = 30,
) -> list[ExchangeResult]:
    threshold = benchmark_ratio * (1 + tolerance_pct / 100)

    results: list[ExchangeResult] = []
    for ex in exchanges:
        total_volume = ex.spot_30d + ex.deriv_30d
        daily_avg = total_volume / time_range_days
        daily_spot = ex.spot_30d / time_range_days
        daily_deriv = ex.deriv_30d / time_range_days

        total_ratio = daily_avg / ex.reserve_usd if ex.reserve_usd > 0 else 0.0
        spot_ratio = daily_spot / ex.reserve_usd if ex.reserve_usd > 0 else 0.0
        deriv_ratio = daily_deriv / ex.reserve_usd if ex.reserve_usd > 0 else 0.0

        label = classify(total_ratio, benchmark_ratio, threshold)

        if total_ratio > threshold:
            suspicious_ratio = total_ratio - threshold
            suspicious_volume = suspicious_ratio * ex.reserve_usd * time_range_days
            authenticity_pct = (total_volume - suspicious_volume) / total_volume if total_volume > 0 else 1.0
        else:
            suspicious_volume = 0.0
            authenticity_pct = 1.0

        note = ""
        if ex.btc_reserve_ratio is not None and ex.btc_reserve_ratio > 150:
            note = f"BTC 储备率 {ex.btc_reserve_ratio:.0f}%，明显超额；部分储备可能来自自营资金，可疑水分判定偏保守"

        results.append(ExchangeResult(
            exchange=ex.exchange,
            total_volume_30d=total_volume,
            total_reserve_usd=ex.reserve_usd,
            daily_avg_volume=daily_avg,
            total_ratio=total_ratio,
            spot_ratio=spot_ratio,
            deriv_ratio=deriv_ratio,
            authenticity_label=label,
            suspicious_volume_30d=suspicious_volume,
            authenticity_pct=authenticity_pct,
            note=note,
        ))

    # 计算市场份额
    total_reported = sum(r.total_volume_30d for r in results)
    total_adjusted = sum(r.total_volume_30d - r.suspicious_volume_30d for r in results)

    for r in results:
        r.reported_share = r.total_volume_30d / total_reported if total_reported > 0 else 0.0
        adj = r.total_volume_30d - r.suspicious_volume_30d
        r.adjusted_share = adj / total_adjusted if total_adjusted > 0 else 0.0
        r.share_delta = r.adjusted_share - r.reported_share

    return results


def format_usd(value: float) -> str:
    if value >= 1e12:
        return f"${value/1e12:.2f}T"
    elif value >= 1e9:
        return f"${value/1e9:.1f}B"
    elif value >= 1e6:
        return f"${value/1e6:.1f}M"
    return f"${value:.0f}"


def print_report(
    results: list[ExchangeResult],
    benchmark_ratio: float,
    threshold: float,
    time_range_days: int,
) -> None:
    print("=== CEX 交易量真实性评估报告 ===")
    print(f"分析时间窗口: {time_range_days} 天")
    print(f"基准 DEX: Hyperliquid | 基准比率: {benchmark_ratio:.2f}x | 可信阈值: {threshold:.2f}x\n")

    header = f"{'交易所':<12} {'核心储备':>10} {'报告30天总量':>12} {'总比率':>8} {'评级':<8} {'可疑交易量':>12} {'真实性'}"
    print(header)
    print("-" * len(header))

    for r in results:
        suspicious_str = format_usd(r.suspicious_volume_30d) if r.suspicious_volume_30d > 0 else "$0"
        auth_str = f"{r.authenticity_pct*100:.0f}%"
        print(
            f"{r.exchange:<12} "
            f"{format_usd(r.total_reserve_usd):>10} "
            f"{format_usd(r.total_volume_30d):>12} "
            f"{r.total_ratio:>7.2f}x "
            f"{r.authenticity_label:<8} "
            f"{suspicious_str:>12} "
            f"{auth_str}"
        )
        if r.note:
            print(f"  注: {r.note}")

    print("\n=== 市场份额对比（样本内） ===")
    print(f"{'交易所':<12} {'报告份额':>8} {'调整后份额':>10} {'变化':>8}")
    print("-" * 42)
    for r in results:
        delta_str = f"{r.share_delta*100:+.1f}pp" if abs(r.share_delta) > 0.0005 else "—"
        print(f"{r.exchange:<12} {r.reported_share*100:>7.1f}% {r.adjusted_share*100:>9.1f}% {delta_str:>8}")


def load_csv(path: str) -> list[ExchangeData]:
    exchanges = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            exchanges.append(ExchangeData(
                exchange=row["exchange"],
                spot_30d=float(row["spot_30d_usd"]),
                deriv_30d=float(row["deriv_30d_usd"]),
                reserve_usd=float(row["reserve_usd"]),
                btc_reserve_ratio=float(row["btc_reserve_ratio"]) if row.get("btc_reserve_ratio") else None,
            ))
    return exchanges


def main() -> None:
    parser = argparse.ArgumentParser(description="CEX Volume Authenticity Ratio Calculator")
    parser.add_argument("--data", required=True, help="CSV 文件路径（exchange,spot_30d_usd,deriv_30d_usd,reserve_usd,btc_reserve_ratio）")
    parser.add_argument("--benchmark_ratio", type=float, default=1.44, help="Hyperliquid 基准比率（默认 1.44）")
    parser.add_argument("--tolerance_pct", type=float, default=15.0, help="CEX 宽容系数 %（默认 15）")
    parser.add_argument("--time_range_days", type=int, default=30, help="分析时间窗口天数（默认 30）")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    args = parser.parse_args()

    exchanges = load_csv(args.data)
    threshold = args.benchmark_ratio * (1 + args.tolerance_pct / 100)
    results = analyze(exchanges, args.benchmark_ratio, args.tolerance_pct, args.time_range_days)

    if args.json:
        output = [
            {
                "exchange": r.exchange,
                "total_volume_30d": r.total_volume_30d,
                "total_reserve_usd": r.total_reserve_usd,
                "total_ratio": round(r.total_ratio, 4),
                "spot_ratio": round(r.spot_ratio, 4),
                "deriv_ratio": round(r.deriv_ratio, 4),
                "authenticity_label": r.authenticity_label,
                "suspicious_volume_30d": round(r.suspicious_volume_30d, 2),
                "authenticity_pct": round(r.authenticity_pct, 4),
                "reported_share": round(r.reported_share, 4),
                "adjusted_share": round(r.adjusted_share, 4),
                "share_delta": round(r.share_delta, 4),
                "note": r.note,
            }
            for r in results
        ]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_report(results, args.benchmark_ratio, threshold, args.time_range_days)


if __name__ == "__main__":
    main()
