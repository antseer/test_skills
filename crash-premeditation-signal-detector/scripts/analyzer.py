"""
崩盘预谋模型信号检测器 — 核心分析逻辑

方法论来源：@wuk_Bitcoin（2026-02-01）
实现：自动生成，v1 草稿

依赖：ant-on-chain-mcp（通过 Claude MCP 工具调用）
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


# ─────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────

@dataclass
class AnalysisParams:
    """分析参数"""
    symbol: str
    lookback_hours: int = 6
    timeframe: str = "1h"
    oi_decline_threshold_pct: float = 5.0
    price_rise_threshold_pct: float = 1.0
    exchanges: list = field(default_factory=lambda: ["Binance", "Bybit", "OKX"])


@dataclass
class StepResult:
    """单步分析结果"""
    success: bool
    data: dict = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class SignalReport:
    """最终信号报告"""
    symbol: str
    analysis_window: str
    signal_level: str          # No Signal / Weak / Moderate / Strong
    score: int
    price_change_pct: float
    oi_change_pct: float
    consecutive_oi_decline_hours: int
    funding_rate_signal: str   # positive_crowded / neutral / short_dominant
    avg_funding_rate: float
    ls_ratio_change: str       # declining / stable / rising
    smart_money_perp_direction: str  # net_short / net_long / neutral
    liquidation_wall_below: bool
    liquidation_concentration_usd: str
    taker_direction: str       # buy_dominant / neutral / sell_dominant
    summary: str
    risk_note: str
    generated_at: str


# ─────────────────────────────────────────────
# 评分逻辑
# ─────────────────────────────────────────────

SCORE_WEIGHTS = {
    "funding_rate_positive_crowded": 2,
    "ls_ratio_declining": 2,
    "smart_money_net_short": 3,
    "liquidation_wall_present": 2,
    "taker_buy_dominant": 1,
    # 负分项（信号方向与模型不符）
    "funding_rate_short_dominant": -1,
    "ls_ratio_rising": -1,
    "smart_money_net_long": -1,
    "taker_sell_dominant": -1,
}

SIGNAL_LEVELS = [
    (8, "Strong（强信号）", "🔴"),
    (4, "Moderate（中等信号）", "🟡"),
    (0, "Weak（弱信号）", "⚠️"),
]


def calculate_score(
    funding_rate_signal: str,
    ls_ratio_change: str,
    smart_money_perp_direction: str,
    liquidation_wall_below: bool,
    taker_direction: str,
) -> int:
    """计算综合得分（0-10）"""
    score = 0

    if funding_rate_signal == "positive_crowded":
        score += SCORE_WEIGHTS["funding_rate_positive_crowded"]
    elif funding_rate_signal == "short_dominant":
        score += SCORE_WEIGHTS["funding_rate_short_dominant"]

    if ls_ratio_change == "declining":
        score += SCORE_WEIGHTS["ls_ratio_declining"]
    elif ls_ratio_change == "rising":
        score += SCORE_WEIGHTS["ls_ratio_rising"]

    if smart_money_perp_direction == "net_short":
        score += SCORE_WEIGHTS["smart_money_net_short"]
    elif smart_money_perp_direction == "net_long":
        score += SCORE_WEIGHTS["smart_money_net_long"]

    if liquidation_wall_below:
        score += SCORE_WEIGHTS["liquidation_wall_present"]

    if taker_direction == "buy_dominant":
        score += SCORE_WEIGHTS["taker_buy_dominant"]
    elif taker_direction == "sell_dominant":
        score += SCORE_WEIGHTS["taker_sell_dominant"]

    return max(0, score)  # 最低 0 分


def get_signal_level(score: int) -> tuple[str, str]:
    """根据得分返回 (信号级别文本, emoji)"""
    for threshold, level, emoji in SIGNAL_LEVELS:
        if score >= threshold:
            return level, emoji
    return "Weak（弱信号）", "⚠️"


# ─────────────────────────────────────────────
# 报告渲染
# ─────────────────────────────────────────────

def render_report(report: SignalReport) -> str:
    """渲染文字报告（<300 字）"""
    _, emoji = get_signal_level(report.score)

    liq_str = (
        f"存在 ({report.liquidation_concentration_usd})"
        if report.liquidation_wall_below
        else "未检测到"
    )

    oi_arrow = "↓" if report.oi_change_pct < 0 else "↑"
    price_arrow = "↑" if report.price_change_pct > 0 else ("↓" if report.price_change_pct < 0 else "→")

    lines = [
        "═══════════════════════════════════════════",
        "崩盘预谋模型信号检测报告",
        "═══════════════════════════════════════════",
        f"标的:       {report.symbol} ({report.symbol}USDT Perpetual)",
        f"分析窗口:   {report.analysis_window}",
        f"生成时间:   {report.generated_at} UTC",
        "",
        "─────────────── 信号评级 ───────────────",
        f"{emoji} {report.signal_level}  得分: {report.score}/10",
        "",
        "─────────────── 关键指标 ───────────────",
        f"价格变化:      {report.price_change_pct:+.1f}%   {price_arrow}",
        f"OI 变化:       {report.oi_change_pct:+.1f}%   {oi_arrow} (持续下降 {report.consecutive_oi_decline_hours} 小时)",
        f"连续下降:      {report.consecutive_oi_decline_hours} 小时",
        f"资金费率:      {report.avg_funding_rate:+.4f}%  ({report.funding_rate_signal})",
        f"大户多空比:    {report.ls_ratio_change}",
        f"Smart Money:  {report.smart_money_perp_direction}",
        f"下方爆仓墙:   {liq_str}",
        f"Taker 流:     {report.taker_direction}",
        "",
        "─────────────── 结论 ───────────────",
        report.summary,
        "",
        f"⚠️ 风险提示: {report.risk_note}",
        "═══════════════════════════════════════════",
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────────
# 主分析入口（供 Claude 调用的伪代码框架）
# ─────────────────────────────────────────────

def build_no_signal_report(params: AnalysisParams, reason: str) -> SignalReport:
    """构建 No Signal 报告"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    return SignalReport(
        symbol=params.symbol,
        analysis_window=f"最近 {params.lookback_hours}h",
        signal_level="No Signal",
        score=0,
        price_change_pct=0.0,
        oi_change_pct=0.0,
        consecutive_oi_decline_hours=0,
        funding_rate_signal="neutral",
        avg_funding_rate=0.0,
        ls_ratio_change="stable",
        smart_money_perp_direction="neutral",
        liquidation_wall_below=False,
        liquidation_concentration_usd="N/A",
        taker_direction="neutral",
        summary=f"核心条件不满足：{reason}",
        risk_note="本分析为模型信号，不构成投资建议。",
        generated_at=now,
    )


def build_signal_report(
    params: AnalysisParams,
    price_change_pct: float,
    oi_change_pct: float,
    consecutive_decline: int,
    funding_signal: str,
    avg_funding: float,
    ls_change: str,
    sm_direction: str,
    liq_wall: bool,
    liq_usd: str,
    taker_dir: str,
    start_time: str,
    end_time: str,
) -> SignalReport:
    """构建完整信号报告"""
    score = calculate_score(funding_signal, ls_change, sm_direction, liq_wall, taker_dir)
    level, _ = get_signal_level(score)

    # 自动生成结论摘要
    summary_parts = [
        f"{params.symbol} 价格上涨 {price_change_pct:+.1f}% 同时 OI 持续 {consecutive_decline} 小时下降（{oi_change_pct:+.1f}%）。"
    ]
    if sm_direction == "net_short":
        summary_parts.append("Smart Money 同步建立净空仓，空单布局信号显著。")
    if liq_wall:
        summary_parts.append(f"下方存在 {liq_usd} 密集爆仓区域，砸盘收益可观。")
    if score >= 8:
        summary_parts.append("建议高度警惕，谨慎持有多单，关注托价订单是否撤出。")
    elif score >= 4:
        summary_parts.append("建议减少多单风险敞口，持续监控。")
    else:
        summary_parts.append("信号较弱，需更多维度确认后再行动。")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    return SignalReport(
        symbol=params.symbol,
        analysis_window=f"{start_time} → {end_time} UTC ({params.lookback_hours}h)",
        signal_level=level,
        score=score,
        price_change_pct=price_change_pct,
        oi_change_pct=oi_change_pct,
        consecutive_oi_decline_hours=consecutive_decline,
        funding_rate_signal=funding_signal,
        avg_funding_rate=avg_funding,
        ls_ratio_change=ls_change,
        smart_money_perp_direction=sm_direction,
        liquidation_wall_below=liq_wall,
        liquidation_concentration_usd=liq_usd,
        taker_direction=taker_dir,
        summary=" ".join(summary_parts),
        risk_note="本分析为模型信号，方法论归属 @wuk_Bitcoin，不构成投资建议。",
        generated_at=now,
    )
