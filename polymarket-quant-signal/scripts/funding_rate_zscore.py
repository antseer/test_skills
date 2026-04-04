#!/usr/bin/env python3
"""
资金费率Z-score计算工具（LMSR定价偏差代理指标）

用法:
    python3 funding_rate_zscore.py --rates "0.001,0.0012,-0.0008,..." --threshold 2.0

输出:
    JSON格式: {"z_score": 2.34, "ev_direction": "SHORT", "triggered": true, ...}
"""

import argparse
import json
import math
import sys
from typing import List


def compute_zscore(rates: List[float], threshold: float = 2.0) -> dict:
    """
    计算资金费率Z-score并判断EV方向

    Args:
        rates: 资金费率历史序列（最近30天，8小时结算周期共约90个数据点）
        threshold: Z-score触发阈值（默认2.0，约95%历史分位）

    Returns:
        dict: {z_score, mu, sigma, current_rate, ev_direction, triggered, ...}
    """
    if len(rates) < 10:
        return {
            "z_score": None,
            "ev_direction": "NEUTRAL",
            "triggered": False,
            "error": f"数据点不足（当前{len(rates)}个，建议至少10个）",
        }

    # 历史序列：排除最后一个（当前值）用于统计
    historical = rates[:-1] if len(rates) > 1 else rates
    current = rates[-1]

    mu = sum(historical) / len(historical)
    variance = sum((r - mu) ** 2 for r in historical) / len(historical)
    sigma = math.sqrt(variance)

    if sigma == 0:
        return {
            "z_score": 0.0,
            "ev_direction": "NEUTRAL",
            "triggered": False,
            "mu": mu,
            "sigma": 0.0,
            "current_rate": current,
            "note": "历史资金费率标准差为0，无法计算Z-score",
        }

    z_score = (current - mu) / sigma

    # 方向判断
    if z_score > threshold:
        ev_direction = "SHORT"  # 市场过度偏多，做空有正期望值
        triggered = True
    elif z_score < -threshold:
        ev_direction = "LONG"  # 市场过度偏空，做多有正期望值
        triggered = True
    else:
        ev_direction = "NEUTRAL"
        triggered = False

    return {
        "z_score": round(z_score, 4),
        "ev_direction": ev_direction,
        "triggered": triggered,
        "current_rate": round(current * 100, 6),  # 转换为百分比
        "mu_pct": round(mu * 100, 6),
        "sigma_pct": round(sigma * 100, 6),
        "threshold": threshold,
        "sample_count": len(historical),
        "percentile_note": f"Z={z_score:.2f} 对应约{_z_to_percentile(z_score):.0f}%历史分位",
    }


def _z_to_percentile(z: float) -> float:
    """Z-score近似转换为百分位数（正态分布假设）"""
    # 简化近似：使用误差函数
    import math
    return (1 + math.erf(z / math.sqrt(2))) / 2 * 100


def main():
    parser = argparse.ArgumentParser(description="资金费率Z-score计算（LMSR代理指标）")
    parser.add_argument("--rates", type=str, required=True, help="资金费率序列（逗号分隔，最新值在最后）")
    parser.add_argument("--threshold", type=float, default=2.0, help="Z-score触发阈值（默认2.0）")
    args = parser.parse_args()

    try:
        rates = [float(x.strip()) for x in args.rates.split(",")]
    except ValueError as e:
        print(json.dumps({"error": f"资金费率解析失败: {e}"}))
        sys.exit(1)

    result = compute_zscore(rates, args.threshold)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
