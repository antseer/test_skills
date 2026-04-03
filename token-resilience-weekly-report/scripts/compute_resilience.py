#!/usr/bin/env python3
"""
代币韧性得分计算脚本
用法: python compute_resilience.py <data.json>

输入 JSON 结构:
{
  "benchmarks": {
    "ETH": [daily_returns...],   # 7 个日收益率（%）
    "BTC": [daily_returns...]
  },
  "tokens": {
    "TAO": [daily_returns...],
    "KAITO": [daily_returns...]
  },
  "t1_min_return": 0.0,
  "t2_min_return": -0.5,
  "weak_multiplier": 2.0
}

输出: 各代币韧性分级和得分（JSON 格式）
"""

import json
import sys
from typing import Dict, List, Tuple


def extract_daily_returns_from_sparkline(sparkline_prices: List[float]) -> List[float]:
    """
    从 sparkline 小时级价格数据提取近似日收益率。
    每 24 小时取最后一个价格点作为当日收盘价近似值。
    """
    if len(sparkline_prices) < 2:
        return []

    # sparkline 约 168 个点（7天 × 24小时），每 24 点取最后一个
    daily_closes = []
    chunk_size = len(sparkline_prices) // 7
    if chunk_size == 0:
        return []

    for i in range(7):
        end_idx = (i + 1) * chunk_size
        daily_closes.append(sparkline_prices[end_idx - 1])

    # 计算日收益率（需要第 0 天的基准，使用第一个点近似）
    base_price = sparkline_prices[0]
    returns = []
    for i, price in enumerate(daily_closes):
        if i == 0:
            prev = base_price
        else:
            prev = daily_closes[i - 1]
        if prev != 0:
            returns.append((price - prev) / prev * 100)
        else:
            returns.append(0.0)

    return returns


def compute_benchmark_stats(
    benchmark_returns: Dict[str, List[float]]
) -> Tuple[List[int], List[int], float, float, float]:
    """
    计算基准市场统计数据。
    返回: (up_days, down_days, bench_up_avg, bench_down_avg, bench_weekly_avg)
    """
    # 以 BTC 日收益判断市场方向（若无 BTC 则用第一个基准）
    reference_ticker = "BTC" if "BTC" in benchmark_returns else next(iter(benchmark_returns))
    reference_returns = benchmark_returns[reference_ticker]

    n_days = len(reference_returns)
    up_days = [d for d in range(n_days) if reference_returns[d] > 0]
    down_days = [d for d in range(n_days) if reference_returns[d] < 0]

    # 计算所有基准代币在上涨日和下跌日的均值
    all_bench_returns = list(benchmark_returns.values())

    def avg_on_days(days: List[int]) -> float:
        if not days or not all_bench_returns:
            return 0.0
        vals = []
        for returns in all_bench_returns:
            for d in days:
                if d < len(returns):
                    vals.append(returns[d])
        return sum(vals) / len(vals) if vals else 0.0

    bench_up_avg = avg_on_days(up_days)
    bench_down_avg = avg_on_days(down_days)

    # 基准周均日收益（所有基准的均值）
    all_bench_avgs = [
        sum(r) / len(r) for r in all_bench_returns if r
    ]
    bench_weekly_avg = sum(all_bench_avgs) / len(all_bench_avgs) if all_bench_avgs else 0.0

    return up_days, down_days, bench_up_avg, bench_down_avg, bench_weekly_avg


def compute_token_resilience(
    token_returns: List[float],
    up_days: List[int],
    down_days: List[int],
    bench_up_avg: float,
    bench_down_avg: float,
) -> Dict:
    """
    计算单个代币的韧性指标。
    """
    weekly_avg_return = sum(token_returns) / len(token_returns) if token_returns else 0.0

    def avg_on_days(days: List[int]) -> float:
        if not days:
            return 0.0
        vals = [token_returns[d] for d in days if d < len(token_returns)]
        return sum(vals) / len(vals) if vals else 0.0

    token_up_avg = avg_on_days(up_days)
    token_down_avg = avg_on_days(down_days)

    upside_alpha = token_up_avg - bench_up_avg
    downside_alpha = token_down_avg - bench_down_avg
    resilience_score = upside_alpha + downside_alpha

    return {
        "weekly_avg_return": round(weekly_avg_return, 4),
        "resilience_score": round(resilience_score, 4),
        "upside_alpha": round(upside_alpha, 4),
        "downside_alpha": round(downside_alpha, 4),
        "token_up_avg": round(token_up_avg, 4),
        "token_down_avg": round(token_down_avg, 4),
    }


def classify_token(
    metrics: Dict,
    bench_weekly_avg: float,
    t1_min_return: float = 0.0,
    t2_min_return: float = -0.5,
    weak_multiplier: float = 2.0,
) -> str:
    """
    根据韧性指标和阈值进行代币分级。
    """
    w = metrics["weekly_avg_return"]
    rs = metrics["resilience_score"]
    ua = metrics["upside_alpha"]
    da = metrics["downside_alpha"]

    # T1: 周均正收益且双向均跑赢
    if w >= t1_min_return and rs > 0:
        return "T1"

    # T2: 至少一侧跑赢
    if w >= t2_min_return and (ua > 0 or da > 0):
        return "T2"

    # 弱势警示: 跌幅相对基准超过倍数阈值
    # bench_weekly_avg 为负数时，乘以 weak_multiplier 结果更负
    if bench_weekly_avg < 0:
        weak_threshold = bench_weekly_avg * weak_multiplier
        if w <= weak_threshold:
            return "weak"

    return "neutral"


def run_analysis(data: Dict) -> Dict:
    """
    主分析函数：计算所有代币的韧性得分并分级。
    """
    benchmark_returns = data.get("benchmarks", {})
    token_returns_map = data.get("tokens", {})
    t1_min_return = data.get("t1_min_return", 0.0)
    t2_min_return = data.get("t2_min_return", -0.5)
    weak_multiplier = data.get("weak_multiplier", 2.0)

    if not benchmark_returns:
        return {"error": "No benchmark data provided"}

    up_days, down_days, bench_up_avg, bench_down_avg, bench_weekly_avg = (
        compute_benchmark_stats(benchmark_returns)
    )

    results = []
    for symbol, returns in token_returns_map.items():
        metrics = compute_token_resilience(
            returns, up_days, down_days, bench_up_avg, bench_down_avg
        )
        tier = classify_token(
            metrics, bench_weekly_avg, t1_min_return, t2_min_return, weak_multiplier
        )
        results.append(
            {
                "symbol": symbol,
                "tier": tier,
                **metrics,
            }
        )

    # 按等级和韧性得分排序
    tier_order = {"T1": 0, "T2": 1, "neutral": 2, "weak": 3}
    results.sort(
        key=lambda x: (tier_order.get(x["tier"], 99), -x["resilience_score"])
    )

    # 基准统计摘要
    benchmark_summary = {}
    for ticker, returns in benchmark_returns.items():
        benchmark_summary[ticker] = {
            "weekly_avg_return": round(sum(returns) / len(returns), 4) if returns else 0.0,
            "daily_returns": [round(r, 4) for r in returns],
        }

    return {
        "benchmark_summary": benchmark_summary,
        "bench_weekly_avg": round(bench_weekly_avg, 4),
        "bench_up_avg": round(bench_up_avg, 4),
        "bench_down_avg": round(bench_down_avg, 4),
        "up_days": up_days,
        "down_days": down_days,
        "tokens": results,
        "parameters": {
            "t1_min_return": t1_min_return,
            "t2_min_return": t2_min_return,
            "weak_multiplier": weak_multiplier,
        },
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compute_resilience.py <data.json>")
        print("       或通过 stdin 传入 JSON: cat data.json | python compute_resilience.py -")
        sys.exit(1)

    path = sys.argv[1]
    if path == "-":
        data = json.load(sys.stdin)
    else:
        with open(path) as f:
            data = json.load(f)

    result = run_analysis(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
