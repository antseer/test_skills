#!/usr/bin/env python3
"""
fetch_premarket_prices.py

可复用脚本：抓取多平台盘前价格并计算价差矩阵。
来源方法论：@BTC_Alert_ 跨平台盘前套利分析框架

用法：
    python3 fetch_premarket_prices.py EDGEX
    python3 fetch_premarket_prices.py EDGEX --platforms ASP Binance Polymarket
    python3 fetch_premarket_prices.py EDGEX --min-spread-pct 20
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Optional


def fetch_binance_premarket_price(symbol: str) -> Optional[float]:
    """
    从 Binance Pre-market 获取价格。
    Binance 盘前使用 {SYMBOL}-PRE-USDT 或 {SYMBOL}PRE-USDT 格式。

    注意：此函数仅作为逻辑示例，实际执行需要 requests 库。
    在 Claude 环境中，优先使用 WebFetch 工具调用以下 URL：
      https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}-PRE-USDT

    返回：浮点数价格，或 None（如未找到）
    """
    # 示例 URL 格式（Claude 中用 WebFetch 调用）：
    # https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}-PRE-USDT
    # https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}PRE-USDT
    print(f"[Binance] 请使用 WebFetch 调用: "
          f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}-PRE-USDT", file=sys.stderr)
    return None


def fetch_polymarket_implied_price(symbol: str) -> Optional[float]:
    """
    从 Polymarket Gamma API 获取代币相关市场的隐含价格。

    注意：此函数仅作为逻辑示例。
    在 Claude 环境中，优先使用 WebFetch 工具调用以下 URL：
      https://gamma-api.polymarket.com/markets?keyword={symbol}

    解析逻辑：
    - 在结果中找到与 symbol 最相关的市场（通常是"Will {symbol} be listed?"类型）
    - 取 outcomePrices[0]（"Yes"结果的价格，单位 USDC）作为隐含价格
    """
    print(f"[Polymarket] 请使用 WebFetch 调用: "
          f"https://gamma-api.polymarket.com/markets?keyword={symbol}", file=sys.stderr)
    return None


def fetch_asp_premarket_price(symbol: str) -> Optional[float]:
    """
    从 Aspecta AI (ASP) 盘前市场获取价格。

    注意：Aspecta AI 暂无官方公开 REST API 文档。
    在 Claude 环境中，使用 WebFetch 访问：
      https://aspecta.ai/market/{symbol.lower()}
    或使用 WebSearch 搜索：
      "{symbol} ASP premarket price site:aspecta.ai"
    """
    print(f"[ASP] 请使用 WebFetch 访问: https://aspecta.ai 或 WebSearch 搜索 {symbol} ASP price", file=sys.stderr)
    return None


def calculate_spread_matrix(prices: dict) -> list:
    """
    计算所有平台两两之间的价差矩阵。

    参数：
        prices: {"ASP": 0.78, "Binance": 0.45, "Polymarket": 0.52}

    返回：按价差百分比降序排列的列表
    """
    platforms = [(k, v) for k, v in prices.items() if v is not None]
    if len(platforms) < 2:
        return []

    results = []
    for i in range(len(platforms)):
        for j in range(i + 1, len(platforms)):
            p1_name, p1_price = platforms[i]
            p2_name, p2_price = platforms[j]

            short_platform = p1_name if p1_price > p2_price else p2_name
            long_platform = p2_name if p1_price > p2_price else p1_name
            short_price = max(p1_price, p2_price)
            long_price = min(p1_price, p2_price)

            spread_usd = short_price - long_price
            spread_pct = (spread_usd / long_price) * 100

            results.append({
                "short_platform": short_platform,
                "long_platform": long_platform,
                "short_price": short_price,
                "long_price": long_price,
                "spread_usd": round(spread_usd, 4),
                "spread_pct": round(spread_pct, 2),
            })

    return sorted(results, key=lambda x: x["spread_pct"], reverse=True)


def calculate_executable_spread(
    spread_usd: float,
    estimated_slippage_pct: float = 1.0,
    fee_pct_per_leg: float = 0.1,
    reference_price: float = 1.0,
) -> dict:
    """
    计算扣除手续费和滑点后的实际可套利价差。

    参数：
        spread_usd: 名义价差（美元/枚）
        estimated_slippage_pct: 双腿合计预估滑点百分比（基于 long_price）
        fee_pct_per_leg: 每腿手续费百分比
        reference_price: 参考价格（通常为 long_price）

    返回：包含 executable_spread_usd 和 is_executable 的字典
    """
    total_cost_pct = estimated_slippage_pct + (fee_pct_per_leg * 2)
    total_cost_usd = reference_price * (total_cost_pct / 100)
    executable_spread = spread_usd - total_cost_usd

    return {
        "estimated_cost_usd": round(total_cost_usd, 4),
        "executable_spread_usd": round(executable_spread, 4),
        "is_executable": executable_spread > 0,
    }


def calculate_hedge_position(
    airdrop_amount: float,
    short_price: float,
    target_hedge_ratio: float = 0.6,
) -> dict:
    """
    根据空投数量和目标对冲比例计算建议仓位。

    参数：
        airdrop_amount: 预估空投代币数量
        short_price: 做空平台当前价格
        target_hedge_ratio: 目标对冲比例（0-1.0，默认 0.6）

    返回：包含仓位建议的字典
    """
    implicit_long_value = airdrop_amount * short_price
    hedge_ratio = min(1.0, target_hedge_ratio)
    max_safe_position = implicit_long_value * hedge_ratio

    return {
        "airdrop_implicit_long_value_usd": round(implicit_long_value, 2),
        "hedge_ratio_recommended": hedge_ratio,
        "max_safe_position_usd": round(max_safe_position, 2),
        "warning": "hedge_ratio 上限为 1.0，超过会导致方向性风险反转" if target_hedge_ratio > 1.0 else None,
    }


def format_report(
    symbol: str,
    prices: dict,
    spread_matrix: list,
    executable_info: Optional[dict],
    fomo_level: str,
    sentiment_score: Optional[float],
    tge_date: Optional[str],
    hedge_info: Optional[dict],
    reference_comparison: Optional[dict],
    grade: str,
    execution_plan: dict,
    risk_notes: list,
) -> str:
    """生成结构化报告文本"""
    scan_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    lines = [
        f"=== 跨平台盘前价差套利扫描报告 ===",
        f"代币: ${symbol} | 扫描时间: {scan_time} UTC",
        "",
        "【价格矩阵】",
    ]

    for platform, price in prices.items():
        if price is not None:
            lines.append(f"  {platform}: ${price:.4f}")
        else:
            lines.append(f"  {platform}: 数据获取失败")

    if spread_matrix:
        best = spread_matrix[0]
        exec_indicator = "✅" if (executable_info and executable_info.get("is_executable")) else "⚠️"
        lines += [
            "",
            "【最优价差对】",
            f"  做空: {best['short_platform']} @ ${best['short_price']:.4f}",
            f"  做多: {best['long_platform']} @ ${best['long_price']:.4f}",
            f"  名义价差: ${best['spread_usd']:.4f}（{best['spread_pct']:.1f}%）",
        ]
        if executable_info:
            lines += [
                f"  预估双腿手续费+滑点: ${executable_info['estimated_cost_usd']:.4f}",
                f"  实际可套利价差: ${executable_info['executable_spread_usd']:.4f} {exec_indicator}",
            ]

    fomo_emoji = {"low": "✅", "medium": "⚠️", "high": "🔴", "extreme": "🚨"}.get(fomo_level.lower(), "❓")
    lines += [
        "",
        "【FOMO 校验】",
        f"  情绪分: {sentiment_score if sentiment_score is not None else 'N/A'}/100",
        f"  FOMO 风险等级: {fomo_level} {fomo_emoji}",
    ]
    if execution_plan.get("stop_loss"):
        lines.append(f"  建议止损（做空腿）: ${execution_plan['stop_loss']:.4f}")

    if tge_date:
        lines += ["", "【TGE 信息】", f"  TGE 交割日期: {tge_date}"]

    if hedge_info:
        lines += [
            "",
            "【解锁与仓位】",
            f"  空投隐式多头价值: ~${hedge_info['airdrop_implicit_long_value_usd']:,.0f}",
            f"  推荐对冲比例: {hedge_info['hedge_ratio_recommended']}",
            f"  最大安全仓位: ${hedge_info['max_safe_position_usd']:,.0f} USDT 双腿各",
        ]

    if reference_comparison:
        lines += [
            "",
            "【历史类比】",
            f"  参考代币 ${reference_comparison.get('token')}: 走势相似度 {reference_comparison.get('similarity')}",
            f"  当前 {symbol} 定价对应 {reference_comparison.get('current_position_vs_ref')}",
        ]

    grade_labels = {"A": "立即执行", "B": "条件执行", "C": "观望", "D": "放弃"}
    lines += [
        "",
        f"【综合评级】: {grade}（{grade_labels.get(grade, '未知')}）",
        "",
        "【执行建议】",
        f"  做空腿: {execution_plan.get('short_platform')} 开空 {symbol}，{execution_plan.get('position_size_usd', 0):,.0f} USDT 等值",
        f"  做多腿: {execution_plan.get('long_platform')} 做多 {symbol}，{execution_plan.get('position_size_usd', 0):,.0f} USDT 等值",
    ]
    if execution_plan.get("stop_loss"):
        lines.append(f"  止损 ({execution_plan.get('short_platform')} 空仓): ${execution_plan['stop_loss']:.4f}")

    if risk_notes:
        lines += ["", "【风险提示】"]
        for i, note in enumerate(risk_notes, 1):
            lines.append(f"  {i}. {note}")

    lines += [
        "",
        "【免责声明】",
        "  分析方法论归属原作者 @BTC_Alert_，本 Skill 基于其公开推文内容自动生成。",
        "  不构成投资建议。套利交易存在市场风险，请结合自身风险承受能力操作。",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="跨平台盘前价差套利扫描")
    parser.add_argument("symbol", help="目标代币符号，如 EDGEX")
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=["ASP", "Binance", "Polymarket"],
        help="要扫描的平台列表（默认：ASP Binance Polymarket）",
    )
    parser.add_argument(
        "--min-spread-pct",
        type=float,
        default=15.0,
        help="触发报警的最小价差百分比（默认：15）",
    )
    parser.add_argument(
        "--airdrop-amount",
        type=float,
        default=0,
        help="预估空投数量（0 表示跳过仓位计算）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出原始数据",
    )

    args = parser.parse_args()
    symbol = args.symbol.upper()

    print(f"[INFO] 开始扫描 ${symbol} 盘前价差...", file=sys.stderr)
    print(f"[INFO] 目标平台: {', '.join(args.platforms)}", file=sys.stderr)
    print(f"[INFO] 最小价差阈值: {args.min_spread_pct}%", file=sys.stderr)
    print(f"[INFO] 注意：此脚本为骨架代码，实际价格数据需通过 Claude 的 WebFetch 工具获取", file=sys.stderr)
    print(f"[INFO] 在 Claude 环境中，直接使用 /cross-platform-premarket-spread-scanner {symbol} 命令", file=sys.stderr)

    # 示例：展示 spread_matrix 计算逻辑（使用模拟价格）
    example_prices = {
        "ASP": 0.78,
        "Binance": 0.45,
        "Polymarket": 0.52,
    }
    spread_matrix = calculate_spread_matrix(example_prices)
    if spread_matrix:
        best = spread_matrix[0]
        executable = calculate_executable_spread(
            spread_usd=best["spread_usd"],
            reference_price=best["long_price"],
        )
        print(f"\n[示例计算] 使用模拟价格 {example_prices}", file=sys.stderr)
        print(f"[示例计算] 最优价差对: {best['short_platform']} -> {best['long_platform']}, "
              f"价差 {best['spread_pct']:.1f}%", file=sys.stderr)
        print(f"[示例计算] 实际可套利价差: ${executable['executable_spread_usd']:.4f} "
              f"({'可执行' if executable['is_executable'] else '不可执行'})", file=sys.stderr)

    if args.json:
        output = {
            "symbol": symbol,
            "platforms": args.platforms,
            "min_spread_pct": args.min_spread_pct,
            "note": "实际价格数据需通过 Claude WebFetch 工具获取",
            "example_calculation": {
                "prices": example_prices,
                "spread_matrix": spread_matrix,
            },
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
