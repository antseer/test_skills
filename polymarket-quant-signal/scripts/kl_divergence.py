#!/usr/bin/env python3
"""
KL散度跨周期背离检测工具

用法:
    python3 kl_divergence.py --prices <json文件或逗号分隔价格> --short_window 5 --long_window 15 --threshold 0.10

输出:
    JSON格式: {"kl_divergence": 0.142, "kl_triggered": true, "kl_direction": "BEARISH_REVERT"}
"""

import argparse
import json
import math
import sys
from typing import List, Tuple


def compute_return_series(prices: List[float]) -> List[float]:
    """计算收益率序列"""
    if len(prices) < 2:
        return []
    return [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]


def to_histogram(returns: List[float], bins: int = 20) -> List[float]:
    """将收益率序列转换为概率分布（直方图归一化）"""
    if not returns:
        return []

    min_r = min(returns)
    max_r = max(returns)
    if max_r == min_r:
        # 所有值相同，构造单峰分布
        return [1.0] + [0.0] * (bins - 1)

    bin_width = (max_r - min_r) / bins
    counts = [0] * bins
    for r in returns:
        idx = min(int((r - min_r) / bin_width), bins - 1)
        counts[idx] += 1

    total = sum(counts)
    return [c / total for c in counts]


def kl_divergence(P: List[float], Q: List[float], epsilon: float = 1e-10) -> float:
    """
    计算KL散度 KL(P‖Q) = Σ P(x) · log(P(x)/Q(x))
    加入平滑项 epsilon 防止零除
    """
    if len(P) != len(Q):
        raise ValueError("P 和 Q 的长度必须相同")

    result = 0.0
    for p, q in zip(P, Q):
        p_smooth = p + epsilon
        q_smooth = q + epsilon
        result += p_smooth * math.log(p_smooth / q_smooth)
    return result


def analyze_kl(
    prices: List[float],
    short_window: int = 5,
    long_window: int = 15,
    threshold: float = 0.10,
) -> dict:
    """
    执行KL散度分析

    Returns:
        dict: {kl_divergence, kl_triggered, kl_direction}
    """
    if len(prices) < long_window + 1:
        return {
            "kl_divergence": None,
            "kl_triggered": False,
            "kl_direction": "INSUFFICIENT_DATA",
            "error": f"数据点不足（需要至少{long_window + 1}个，当前{len(prices)}个）",
        }

    # 短周期：使用最近 short_window + 1 个价格点
    short_prices = prices[-(short_window + 1):]
    # 长周期：使用最近 long_window + 1 个价格点
    long_prices = prices[-(long_window + 1):]

    short_returns = compute_return_series(short_prices)
    long_returns = compute_return_series(long_prices)

    # 转换为概率分布
    bins = 20
    P = to_histogram(short_returns, bins=bins)
    Q = to_histogram(long_returns, bins=bins)

    kl_val = kl_divergence(P, Q)
    triggered = kl_val > threshold

    # 方向判断：短周期均值 vs 长周期均值
    short_mean = sum(short_returns) / len(short_returns) if short_returns else 0.0
    long_mean = sum(long_returns) / len(long_returns) if long_returns else 0.0

    if triggered:
        # 短期超涨（短均值 > 长均值）→ 预计向下回归（BEARISH_REVERT）
        direction = "BULLISH_REVERT" if short_mean < long_mean else "BEARISH_REVERT"
    else:
        direction = "NO_DIVERGENCE"

    return {
        "kl_divergence": round(kl_val, 4),
        "kl_triggered": triggered,
        "kl_direction": direction,
        "short_window_mean_return": round(short_mean * 100, 4),
        "long_window_mean_return": round(long_mean * 100, 4),
        "threshold": threshold,
    }


def main():
    parser = argparse.ArgumentParser(description="KL散度跨周期背离检测")
    parser.add_argument("--prices", type=str, required=True, help="价格序列（JSON数组文件路径或逗号分隔数值）")
    parser.add_argument("--short_window", type=int, default=5, help="短周期窗口（分钟，默认5）")
    parser.add_argument("--long_window", type=int, default=15, help="长周期窗口（分钟，默认15）")
    parser.add_argument("--threshold", type=float, default=0.10, help="KL散度触发阈值（默认0.10）")
    args = parser.parse_args()

    # 解析价格输入
    try:
        try:
            with open(args.prices, "r") as f:
                prices = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            prices = [float(x.strip()) for x in args.prices.split(",")]
    except Exception as e:
        print(json.dumps({"error": f"价格解析失败: {e}"}))
        sys.exit(1)

    result = analyze_kl(prices, args.short_window, args.long_window, args.threshold)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
