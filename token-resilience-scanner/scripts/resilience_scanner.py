#!/usr/bin/env python3
"""
token-resilience-scanner — 代币韧性周报生成器

基于 @Guolier8 的双向 beta 韧性筛选框架，通过 Antseer MCP 数据接口
计算候选代币的上涨日超额（up_alpha）和下跌日超额（down_alpha），
生成 T1/T2/弱势 分层周报。

方法论归属：@Guolier8 (https://x.com/Guolier8/status/2039953528643535218)
不构成投资建议。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta
from statistics import mean
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class TokenMetrics:
    symbol: str
    coingecko_id: str
    daily_returns: list[float]          # 日收益率序列（小数，不是百分比）
    avg_daily_return: float             # 周均日收益率（%）
    up_alpha: float                     # 大盘上涨日超额（%）
    down_alpha: float                   # 大盘下跌日超额（%）
    resilience_score: float             # 综合韧性分
    notable_days: list[str]             # 异动日标注，如 ["3/24 +8.49%"]
    narrative: str                      # 叙事板块标签
    avg_volume_usd: float               # 日均 USD 交易量
    skipped: bool = False               # 流动性不足跳过标志
    skip_reason: str = ""


@dataclass
class ScanResult:
    report_period: str
    market_context: str
    market_avg_daily_return: float      # 大盘周均日收益率（%）
    tier1: list[TokenMetrics] = field(default_factory=list)
    tier2: list[TokenMetrics] = field(default_factory=list)
    weak_alert: list[TokenMetrics] = field(default_factory=list)
    neutral: list[TokenMetrics] = field(default_factory=list)
    skipped: list[TokenMetrics] = field(default_factory=list)
    next_week_watchlist: list[str] = field(default_factory=list)
    conclusion: str = ""


# ---------------------------------------------------------------------------
# CoinGecko ID 映射表（常见 ticker → CoinGecko ID）
# ---------------------------------------------------------------------------

TICKER_TO_COINGECKO: dict[str, str] = {
    "TAO": "bittensor",
    "ETH": "ethereum",
    "SOL": "solana",
    "BTC": "bitcoin",
    "SPEC": "spectral",
    "KAITO": "kaito",
    "HYPE": "hyperliquid",
    "IO": "io-net",
    "STORY": "story-protocol",
    "DRIFT": "drift-protocol",
}


def resolve_coingecko_id(symbol: str) -> str:
    """将 ticker 或 CoinGecko ID 统一解析为 CoinGecko ID。"""
    upper = symbol.upper()
    if upper in TICKER_TO_COINGECKO:
        return TICKER_TO_COINGECKO[upper]
    # 已经是 CoinGecko ID 格式（含连字符或全小写）
    return symbol.lower()


# ---------------------------------------------------------------------------
# 价格序列工具
# ---------------------------------------------------------------------------

def extract_daily_returns(sparkline_prices: list[float], days: int = 7) -> list[float]:
    """
    从 sparkline 价格序列（可能是小时粒度）中提取每日收益率。

    Antseer 的 sparkline 返回 168 个数据点（7天 × 24小时），
    取每 24 个点的最后一个作为"日收盘价"近似值。

    返回：日收益率列表（小数，如 0.0243 表示 +2.43%）
    """
    if not sparkline_prices or len(sparkline_prices) < 2:
        return []

    # 按小时粒度推算：168点 → 7天，每24点取最后一个作日收盘
    points_per_day = max(1, len(sparkline_prices) // days)
    daily_closes: list[float] = []
    for i in range(days):
        idx = min((i + 1) * points_per_day - 1, len(sparkline_prices) - 1)
        daily_closes.append(sparkline_prices[idx])

    daily_returns: list[float] = []
    for i in range(1, len(daily_closes)):
        prev = daily_closes[i - 1]
        curr = daily_closes[i]
        if prev and prev != 0:
            daily_returns.append((curr - prev) / prev * 100.0)
        else:
            daily_returns.append(0.0)

    return daily_returns


def notable_days_from_returns(
    daily_returns: list[float],
    end_date: date,
    threshold_pct: float = 8.0,
) -> list[str]:
    """标注单日涨跌幅绝对值超过 threshold_pct 的日期。"""
    notes: list[str] = []
    n = len(daily_returns)
    for i, ret in enumerate(daily_returns):
        if abs(ret) >= threshold_pct:
            day = end_date - timedelta(days=n - 1 - i)
            sign = "+" if ret >= 0 else ""
            notes.append(f"{day.month}/{day.day} {sign}{ret:.2f}%")
    return notes


# ---------------------------------------------------------------------------
# 韧性计算核心
# ---------------------------------------------------------------------------

def compute_alphas(
    token_returns: list[float],
    market_returns: list[float],
) -> tuple[float, float, float]:
    """
    计算 up_alpha、down_alpha、resilience_score。

    返回：(up_alpha_pct, down_alpha_pct, resilience_score_pct)
    """
    if len(token_returns) != len(market_returns) or not token_returns:
        return 0.0, 0.0, 0.0

    up_excess: list[float] = []
    down_excess: list[float] = []

    for t_ret, m_ret in zip(token_returns, market_returns):
        excess = t_ret - m_ret
        if m_ret > 0:
            up_excess.append(excess)
        elif m_ret < 0:
            down_excess.append(excess)

    up_alpha = mean(up_excess) if up_excess else 0.0
    down_alpha = mean(down_excess) if down_excess else 0.0
    resilience_score = up_alpha * 0.5 + down_alpha * 0.5

    return round(up_alpha, 4), round(down_alpha, 4), round(resilience_score, 4)


# ---------------------------------------------------------------------------
# 分层逻辑
# ---------------------------------------------------------------------------

def classify_tokens(
    tokens: list[TokenMetrics],
    market_avg: float,
    top_n: int = 5,
    weak_n: int = 3,
    t2_threshold_ratio: float = 0.5,
    weak_threshold_ratio: float = 2.0,
) -> tuple[
    list[TokenMetrics],  # tier1
    list[TokenMetrics],  # tier2
    list[TokenMetrics],  # weak_alert
    list[TokenMetrics],  # neutral
]:
    """按 T1/T2/弱势/中性 规则分层。"""
    tier1: list[TokenMetrics] = []
    tier2: list[TokenMetrics] = []
    weak_alert: list[TokenMetrics] = []
    neutral: list[TokenMetrics] = []

    for tok in tokens:
        if tok.skipped:
            continue

        avg = tok.avg_daily_return  # %

        # T1：周均正收益 + 综合韧性分为正
        if avg > 0 and tok.resilience_score > 0:
            tier1.append(tok)
        # 弱势警示：跌幅超过大盘 weak_threshold_ratio 倍
        elif market_avg < 0 and avg < market_avg * weak_threshold_ratio:
            weak_alert.append(tok)
        # T2：微跌但跌幅 < |market_avg| * t2_threshold_ratio，且下跌日超额为正
        elif avg < 0 and abs(avg) < abs(market_avg) * t2_threshold_ratio and tok.down_alpha > 0:
            tier2.append(tok)
        else:
            neutral.append(tok)

    # 排序
    tier1.sort(key=lambda t: t.resilience_score, reverse=True)
    tier1 = tier1[:top_n]

    tier2.sort(key=lambda t: t.resilience_score, reverse=True)

    weak_alert.sort(key=lambda t: t.avg_daily_return)
    weak_alert = weak_alert[:weak_n]

    neutral.sort(key=lambda t: t.resilience_score, reverse=True)

    return tier1, tier2, weak_alert, neutral


# ---------------------------------------------------------------------------
# 报告渲染
# ---------------------------------------------------------------------------

def render_report(result: ScanResult) -> str:
    """将 ScanResult 渲染为 Markdown 周报字符串。"""
    lines: list[str] = []

    lines.append(f"## 代币韧性周报 | {result.report_period}")
    lines.append("")
    lines.append(f"**大盘环境**: {result.market_context}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # T1
    lines.append("### 韧性 T1（强势，周均正收益）")
    lines.append("")
    if result.tier1:
        lines.append("| 代币 | 周均日收益 | 上涨日超额 | 下跌日超额 | 韧性分 | 异动日 | 叙事 |")
        lines.append("|------|-----------|-----------|-----------|-------|--------|------|")
        for tok in result.tier1:
            nd = "、".join(tok.notable_days) if tok.notable_days else "—"
            na = tok.narrative or "—"
            lines.append(
                f"| ${tok.symbol} "
                f"| {tok.avg_daily_return:+.2f}% "
                f"| {tok.up_alpha:+.2f}% "
                f"| {tok.down_alpha:+.2f}% "
                f"| {tok.resilience_score:.2f} "
                f"| {nd} "
                f"| {na} |"
            )
    else:
        lines.append("本周无符合条件的 T1 代币。")
    lines.append("")

    # T2
    lines.append("### 韧性 T2（跑赢大盘，跌幅极小）")
    lines.append("")
    if result.tier2:
        lines.append("| 代币 | 周均日收益 | 下跌日超额 | 异动日 | 叙事 |")
        lines.append("|------|-----------|-----------|--------|------|")
        for tok in result.tier2:
            nd = "、".join(tok.notable_days) if tok.notable_days else "—"
            na = tok.narrative or "—"
            lines.append(
                f"| ${tok.symbol} "
                f"| {tok.avg_daily_return:+.2f}% "
                f"| {tok.down_alpha:+.2f}% "
                f"| {nd} "
                f"| {na} |"
            )
    else:
        lines.append("本周无符合条件的 T2 代币。")
    lines.append("")

    # 弱势警示
    lines.append("### 弱势警示")
    lines.append("")
    if result.weak_alert:
        lines.append("| 代币 | 周均日收益 | vs 大盘倍数 | 信号 |")
        lines.append("|------|-----------|------------|------|")
        for tok in result.weak_alert:
            ratio_str = "N/A"
            if result.market_avg_daily_return and result.market_avg_daily_return != 0:
                ratio = abs(tok.avg_daily_return / result.market_avg_daily_return)
                ratio_str = f"~{ratio:.1f}×"
            nd_note = "、".join(tok.notable_days) if tok.notable_days else "反弹乏力"
            lines.append(
                f"| ${tok.symbol} "
                f"| {tok.avg_daily_return:+.2f}% "
                f"| {ratio_str} "
                f"| {nd_note} |"
            )
    else:
        lines.append("本周无弱势警示代币。")
    lines.append("")

    # 流动性过滤跳过
    if result.skipped:
        lines.append("### 流动性不足（已跳过）")
        lines.append("")
        for tok in result.skipped:
            lines.append(f"- **{tok.symbol}**: {tok.skip_reason}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 下周重点观察
    if result.next_week_watchlist:
        wl = "、".join(f"${s}" for s in result.next_week_watchlist)
        lines.append(f"**下周重点观察**: {wl}")
        lines.append("")

    # 一句话结论
    if result.conclusion:
        lines.append(f"**一句话结论**: {result.conclusion}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*方法论归属：@Guolier8。本报告基于历史数据，不构成投资建议。*")
    lines.append("*数据基于 Antseer MCP 接口，历史价格使用 sparkline 近似值，与精确每日收盘价可能存在细微差异。*")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 结论生成辅助
# ---------------------------------------------------------------------------

def generate_conclusion(result: ScanResult) -> str:
    """根据分层结果生成一句话结论。"""
    t1_names = [f"${t.symbol}" for t in result.tier1]
    t2_names = [f"${t.symbol}" for t in result.tier2]
    weak_names = [f"${t.symbol}" for t in result.weak_alert]

    parts: list[str] = []
    if t1_names:
        parts.append(f"{', '.join(t1_names)} 本周符合「大盘反弹领涨、大盘下跌抗跌」的韧性定义")
    if t2_names:
        parts.append(f"{', '.join(t2_names)} 微跌但显著跑赢基准")
    if weak_names:
        parts.append(f"{', '.join(weak_names)} 跌幅超过基准 2× 以上，需关注风险")

    if not parts:
        return "本周候选代币整体表现与大盘趋同，无明显韧性分化。"

    conclusion = "；".join(parts) + "。"
    if t1_names:
        conclusion += f" 下周重点观察 {', '.join(t1_names)} 企稳后能否率先突破。"
    return conclusion


# ---------------------------------------------------------------------------
# 主扫描函数（由 Claude MCP 调用流程驱动）
# ---------------------------------------------------------------------------

def build_scan_result(
    symbol_returns: dict[str, list[float]],         # symbol -> daily_returns (%)
    benchmark_returns_map: dict[str, list[float]],  # benchmark_id -> daily_returns (%)
    volumes: dict[str, float],                       # symbol -> avg daily volume USD
    narratives: dict[str, str],                      # symbol -> 叙事标签
    end_date: date,
    time_range_days: int = 7,
    top_n: int = 5,
    weak_n: int = 3,
    min_daily_volume_usd: float = 1_000_000,
) -> ScanResult:
    """
    构建 ScanResult 的核心逻辑。

    在 Claude 的 Skill 执行流程中，Step 1–2 由 MCP 工具调用获取数据，
    数据整理后传入此函数完成 Step 3–6 的计算和分类。
    """
    # 合并基准收益序列（取均值）
    all_benchmark_returns = list(benchmark_returns_map.values())
    if not all_benchmark_returns:
        raise ValueError("benchmark_returns_map 不能为空")

    n_days = min(len(r) for r in all_benchmark_returns)
    market_returns = [
        mean(all_benchmark_returns[j][i] for j in range(len(all_benchmark_returns)))
        for i in range(n_days)
    ]
    market_avg = mean(market_returns) if market_returns else 0.0

    # 大盘日分类
    up_days = [i for i, r in enumerate(market_returns) if r > 0]
    down_days = [i for i, r in enumerate(market_returns) if r < 0]

    # 各基准均值描述（用于 market_context 字段）
    benchmark_descs: list[str] = []
    for bid, bret in benchmark_returns_map.items():
        bavg = mean(bret) if bret else 0.0
        ticker = bid.upper().split("-")[0]  # ethereum -> ETH
        benchmark_descs.append(f"{ticker} 周均日收益 {bavg:+.2f}%")

    market_context = "，".join(benchmark_descs)
    if market_avg < -0.5:
        market_context += "，大盘整体承压"
    elif market_avg > 0.5:
        market_context += "，大盘整体强势"
    else:
        market_context += "，大盘震荡"

    report_period_start = end_date - timedelta(days=time_range_days - 1)
    report_period = f"{report_period_start.year}.{report_period_start.month:02d}.{report_period_start.day:02d}–{end_date.month:02d}.{end_date.day:02d}"

    # 逐代币计算韧性指标
    token_metrics_list: list[TokenMetrics] = []
    skipped: list[TokenMetrics] = []

    for symbol, t_returns in symbol_returns.items():
        cg_id = resolve_coingecko_id(symbol)
        vol = volumes.get(symbol, 0.0)

        # 流动性过滤
        if vol < min_daily_volume_usd:
            m = TokenMetrics(
                symbol=symbol, coingecko_id=cg_id,
                daily_returns=t_returns, avg_daily_return=0.0,
                up_alpha=0.0, down_alpha=0.0, resilience_score=0.0,
                notable_days=[], narrative="",
                avg_volume_usd=vol, skipped=True,
                skip_reason=f"日均交易量 ${vol:,.0f} < 过滤阈值 ${min_daily_volume_usd:,.0f}"
            )
            skipped.append(m)
            logger.info("跳过 %s：流动性不足", symbol)
            continue

        # 对齐长度
        min_len = min(len(t_returns), len(market_returns))
        t_aligned = t_returns[-min_len:]
        m_aligned = market_returns[-min_len:]

        avg = mean(t_aligned) if t_aligned else 0.0
        up_alpha, down_alpha, resilience_score = compute_alphas(t_aligned, m_aligned)
        notable = notable_days_from_returns(t_aligned, end_date, threshold_pct=8.0)
        narrative = narratives.get(symbol, "")

        m = TokenMetrics(
            symbol=symbol, coingecko_id=cg_id,
            daily_returns=t_aligned,
            avg_daily_return=round(avg, 4),
            up_alpha=up_alpha, down_alpha=down_alpha,
            resilience_score=resilience_score,
            notable_days=notable, narrative=narrative,
            avg_volume_usd=vol,
        )
        token_metrics_list.append(m)

    tier1, tier2, weak_alert, neutral = classify_tokens(
        token_metrics_list, market_avg,
        top_n=top_n, weak_n=weak_n,
    )

    result = ScanResult(
        report_period=report_period,
        market_context=market_context,
        market_avg_daily_return=round(market_avg, 4),
        tier1=tier1, tier2=tier2,
        weak_alert=weak_alert, neutral=neutral,
        skipped=skipped,
        next_week_watchlist=[t.symbol for t in tier1[:3]],
    )
    result.conclusion = generate_conclusion(result)

    return result


# ---------------------------------------------------------------------------
# CLI 快速测试入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """
    快速本地测试：模拟 2026.03.21–03.27 原始推文数据。
    实际运行时，日收益数据由 Claude 通过 Antseer MCP 工具获取后传入 build_scan_result()。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # 模拟数据（基于推文原始案例）
    mock_benchmark = {
        "ethereum": [-1.5, -0.8, -2.1, 0.3, -0.9, -1.2, -0.4],
        "solana":   [-1.8, -0.6, -2.3, 0.2, -1.0, -1.3, -0.2],
    }
    mock_tokens = {
        "TAO":   [1.2, 0.8, -0.3, 12.0, 11.0, 0.5, -0.4],
        "SPEC":  [21.0, -1.0, -1.5, 0.2, -0.8, -0.5, -0.3],
        "KAITO": [0.5, 1.2, -0.8, 6.78, -0.3, 0.1, 0.2],
        "HYPE":  [-0.2, -0.5, -1.0, 8.49, -0.3, -0.1, 0.1],
        "IO":    [-0.1, -0.3, -0.8, 0.5, -0.2, -0.1, 0.0],
        "STORY": [-3.5, -4.2, -5.0, 0.8, -4.5, -5.1, -4.1],
        "DRIFT": [-2.8, -3.5, -4.2, 0.4, -3.8, -4.1, -3.3],
    }
    mock_volumes = {s: 5_000_000 for s in mock_tokens}
    mock_narratives = {
        "TAO": "AI叙事", "SPEC": "基础设施", "KAITO": "InfoFi",
        "HYPE": "DeFi/Perp", "IO": "DePIN", "STORY": "生态基础设施", "DRIFT": "DeFi/Perp",
    }

    result = build_scan_result(
        symbol_returns=mock_tokens,
        benchmark_returns_map=mock_benchmark,
        volumes=mock_volumes,
        narratives=mock_narratives,
        end_date=date(2026, 3, 27),
        time_range_days=7,
        top_n=5,
        weak_n=3,
        min_daily_volume_usd=1_000_000,
    )

    report_md = render_report(result)
    print(report_md)
    print("\n--- JSON 摘要 ---")
    summary = {
        "report_period": result.report_period,
        "market_avg_daily_return_pct": result.market_avg_daily_return,
        "tier1": [{"symbol": t.symbol, "avg_daily_return": t.avg_daily_return, "resilience_score": t.resilience_score} for t in result.tier1],
        "tier2": [{"symbol": t.symbol, "avg_daily_return": t.avg_daily_return} for t in result.tier2],
        "weak_alert": [{"symbol": t.symbol, "avg_daily_return": t.avg_daily_return} for t in result.weak_alert],
        "conclusion": result.conclusion,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
