#!/usr/bin/env python3
"""
Kelly仓位计算 + Stoikov最优执行价格工具

用法:
    python3 kelly_stoikov.py \
        --p_bayes 0.71 \
        --p_market 0.28 \
        --mid_price 65430 \
        --boll_upper 66270 \
        --boll_lower 64830 \
        --kelly_scale 0.25 \
        --risk_aversion 0.10 \
        --direction SHORT

输出:
    JSON格式: {kelly_fraction_theoretical, kelly_fraction_actual, r_optimal, price_in_range, ...}
"""

import argparse
import json
import sys


def kelly_fraction(p_bayes: float, p_market: float) -> float:
    """
    计算理论Kelly系数

    二元预测市场标准公式：
    赔率 b = (1 - p_market) / p_market
    f* = (b * p_bayes - (1 - p_bayes)) / b

    Args:
        p_bayes: 模型（贝叶斯后验）估计的获胜概率
        p_market: 市场隐含获胜概率（来自Polymarket YES代币价格）

    Returns:
        float: 理论Kelly系数（负数表示无正期望值）
    """
    if p_market <= 0 or p_market >= 1:
        raise ValueError(f"p_market 必须在 (0, 1) 范围内，当前值: {p_market}")
    if p_bayes <= 0 or p_bayes >= 1:
        raise ValueError(f"p_bayes 必须在 (0, 1) 范围内，当前值: {p_bayes}")

    b = (1 - p_market) / p_market
    f_star = (b * p_bayes - (1 - p_bayes)) / b
    return f_star


def stoikov_reservation_price(
    mid_price: float,
    position_size: float,
    sigma: float,
    gamma: float,
) -> float:
    """
    简化Stoikov模型：最优保留价格

    r = mid_price - q * gamma * sigma^2

    Args:
        mid_price: 当前市场中间价（USDT）
        position_size: 目标仓位大小（账户净值百分比，作为 q）
        sigma: 价格波动率标准差（布林带带宽/2，USDT）
        gamma: 风险厌恶系数（默认0.10）

    Returns:
        float: 最优执行保留价（USDT）
    """
    return mid_price - position_size * gamma * (sigma ** 2)


def analyze(
    p_bayes: float,
    p_market: float,
    mid_price: float,
    boll_upper: float,
    boll_lower: float,
    kelly_scale: float = 0.25,
    risk_aversion: float = 0.10,
    direction: str = "SHORT",
) -> dict:
    """
    执行Kelly+Stoikov联合计算

    Args:
        direction: "LONG" 或 "SHORT"，决定执行价格区间判断方向

    Returns:
        dict: 完整计算结果
    """
    # Kelly计算
    f_star = kelly_fraction(p_bayes, p_market)
    f_actual = max(0.0, f_star * kelly_scale)
    kelly_triggered = f_star > 0

    # Stoikov计算
    sigma = (boll_upper - boll_lower) / 2.0
    r_optimal = stoikov_reservation_price(mid_price, f_actual, sigma, risk_aversion)

    # 价格区间判断
    if direction.upper() == "LONG":
        # 做多：当前价格 <= 保留价时可执行（价格低于预期才买入）
        price_in_range = mid_price <= r_optimal
    else:
        # 做空：当前价格 >= 保留价时可执行（价格高于预期才卖出）
        price_in_range = mid_price >= r_optimal

    # EV缺口方向分析
    ev_gap = p_bayes - p_market
    b = (1 - p_market) / p_market

    return {
        "kelly": {
            "p_bayes": round(p_bayes, 4),
            "p_market": round(p_market, 4),
            "odds_b": round(b, 4),
            "kelly_fraction_theoretical": round(f_star, 4),
            "kelly_fraction_actual": round(f_actual, 4),
            "kelly_scale": kelly_scale,
            "kelly_triggered": kelly_triggered,
            "ev_gap": round(ev_gap, 4),
        },
        "stoikov": {
            "mid_price": round(mid_price, 2),
            "boll_upper": round(boll_upper, 2),
            "boll_lower": round(boll_lower, 2),
            "sigma": round(sigma, 2),
            "risk_aversion": risk_aversion,
            "position_size_q": round(f_actual, 4),
            "r_optimal": round(r_optimal, 2),
            "price_in_range": price_in_range,
            "direction": direction.upper(),
        },
        "summary": {
            "recommended_direction": direction.upper() if kelly_triggered else "WAIT",
            "recommended_size_pct": round(f_actual * 100, 2),
            "execution_price": round(r_optimal, 2),
            "current_price": round(mid_price, 2),
            "execution_ready": price_in_range and kelly_triggered,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Kelly仓位 + Stoikov执行价格计算")
    parser.add_argument("--p_bayes", type=float, required=True, help="贝叶斯后验概率（0-1）")
    parser.add_argument("--p_market", type=float, required=True, help="Polymarket市场隐含概率（YES代币价格，0-1）")
    parser.add_argument("--mid_price", type=float, required=True, help="当前市场中间价（USDT）")
    parser.add_argument("--boll_upper", type=float, required=True, help="布林带上轨（USDT）")
    parser.add_argument("--boll_lower", type=float, required=True, help="布林带下轨（USDT）")
    parser.add_argument("--kelly_scale", type=float, default=0.25, help="Kelly缩放系数（默认0.25）")
    parser.add_argument("--risk_aversion", type=float, default=0.10, help="Stoikov风险厌恶系数γ（默认0.10）")
    parser.add_argument("--direction", type=str, default="SHORT", choices=["LONG", "SHORT"], help="交易方向")
    args = parser.parse_args()

    try:
        result = analyze(
            p_bayes=args.p_bayes,
            p_market=args.p_market,
            mid_price=args.mid_price,
            boll_upper=args.boll_upper,
            boll_lower=args.boll_lower,
            kelly_scale=args.kelly_scale,
            risk_aversion=args.risk_aversion,
            direction=args.direction,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
