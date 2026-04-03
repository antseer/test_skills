"""
BTC 周度综合市场分析 — 主实现脚本

方法论归属原作者 @Guolier8
推文：https://x.com/Guolier8/status/2039989943213404528

本脚本封装了七层递进分析框架的数据采集与报告生成逻辑，
供 btc-weekly-market-analysis Skill 在 Claude Code 环境中调用。

依赖：Antseer MCP 工具集（通过 Claude MCP 协议访问）
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 参数与数据结构
# ---------------------------------------------------------------------------

@dataclass
class AnalysisParams:
    """Skill 入参，对应 SKILL.md Features 章节定义的所有参数。"""
    symbol: str = "BTC"
    start_date: Optional[str] = None   # YYYY-MM-DD；None 时自动推算上周一
    end_date: Optional[str] = None     # YYYY-MM-DD；None 时自动推算上周日
    include_eth_etf: bool = True
    whale_threshold: int = 1000        # 鲸鱼地址持仓阈值（BTC 数量）
    whale_lookback_days: int = 14      # 鲸鱼净增减持统计窗口（天）
    fear_greed_threshold: int = 20     # 极端恐慌阈值

    def resolve_dates(self) -> tuple[str, str]:
        """若 start_date/end_date 未指定，自动推算上周一到上周日（UTC 时区基准）。"""
        if self.start_date and self.end_date:
            return self.start_date, self.end_date
        today = date.today()
        # 本周一 = today - weekday()（0=周一）
        this_monday = today - timedelta(days=today.weekday())
        last_monday = this_monday - timedelta(weeks=1)
        last_sunday = this_monday - timedelta(days=1)
        return last_monday.strftime("%Y-%m-%d"), last_sunday.strftime("%Y-%m-%d")


@dataclass
class MacroSignal:
    """Step 1: 宏观流动性信号"""
    fed_rate: Optional[float] = None        # Fed 利率（%）
    cpi_yoy: Optional[float] = None         # CPI 同比（%）
    dxy_estimate: Optional[str] = None      # DXY 估算（MCP 不直接覆盖时给定性描述）
    gold_price_usd: Optional[float] = None  # 黄金 token（PAXG）价格
    gold_weekly_pct: Optional[float] = None # 黄金本周涨跌幅（%）
    signal: str = "中性"                    # 鹰派 / 中性 / 鸽派
    notes: list[str] = field(default_factory=list)


@dataclass
class GeopoliticalSignal:
    """Step 2: 地缘政治与外生风险信号"""
    gold_btc_divergence: bool = False       # 黄金涨而 BTC 未跟涨
    signal: str = "中"                      # 高 / 中 / 低
    notes: list[str] = field(default_factory=list)


@dataclass
class EtfFlowSignal:
    """Step 3: ETF 资金流向信号"""
    btc_weekly_netflow_usd: Optional[float] = None   # BTC ETF 周净流量（USD）
    btc_max_single_day_outflow_usd: Optional[float] = None  # 最大单日流出（USD）
    eth_weekly_netflow_usd: Optional[float] = None   # ETH ETF 周净流量（USD，可选）
    direction: str = "混合"                           # 净流入 / 净流出 / 混合
    divergence_flag: bool = False                     # ETF 背离信号
    divergence_note: str = ""
    daily_flows: list[dict] = field(default_factory=list)   # [{date, amount_usd, note}]
    notes: list[str] = field(default_factory=list)


@dataclass
class DerivativesSignal:
    """Step 4: 衍生品市场结构信号"""
    funding_rate: Optional[float] = None      # 资金费率（%）
    oi_value: Optional[float] = None          # OI（美元）
    oi_change_pct: Optional[float] = None     # OI 周变化（%）
    long_short_ratio: Optional[float] = None  # 多空比
    liquidation_long_usd: Optional[float] = None   # 多头爆仓（USD）
    liquidation_short_usd: Optional[float] = None  # 空头爆仓（USD）
    sentiment: str = "中性"                   # 偏多 / 中性 / 偏空
    notes: list[str] = field(default_factory=list)


@dataclass
class OnChainSignal:
    """Step 5: 链上资金结构信号"""
    exchange_reserve_btc: Optional[float] = None      # 交易所 BTC 存量
    exchange_reserve_change_btc: Optional[float] = None  # 存量周变化（BTC）
    exchange_netflow_btc: Optional[float] = None      # 交易所净流量（BTC，负=流出=减少抛压）
    whale_net_accumulation_btc: Optional[float] = None  # 鲸鱼净增减持（BTC）
    stablecoin_mcap_usd_b: Optional[float] = None     # 稳定币总市值（十亿 USD）
    supply_in_profit_pct: Optional[float] = None      # 盈利供应率（%，MVRV 近似）
    mvrv: Optional[float] = None
    fear_greed_index: Optional[int] = None
    fear_greed_label: str = ""
    sell_pressure: str = "中"    # 高 / 中 / 低
    buy_power: str = "中"        # 强 / 中 / 弱
    notes: list[str] = field(default_factory=list)


@dataclass
class PriceStructureSignal:
    """Step 6: 价格结构信号"""
    current_price: Optional[float] = None
    weekly_high: Optional[float] = None
    weekly_low: Optional[float] = None
    weekly_pct_change: Optional[float] = None
    key_supports: list[float] = field(default_factory=list)    # 降序排列
    key_resistances: list[float] = field(default_factory=list) # 升序排列
    structure: str = "震荡筑底"   # 强势突破 / 震荡筑底 / 弱势下行
    driver: str = "混合"          # 真实需求 / 被动对冲 / 混合
    notes: list[str] = field(default_factory=list)


@dataclass
class ComprehensiveJudgment:
    """Step 7: 综合研判结果"""
    bearish_signal_count: int = 0
    short_term_bias: str = "震荡"          # 偏多 / 震荡 / 偏空
    short_term_range: str = ""
    breakout_confirmation_condition: str = ""
    scenario_bull_trigger: str = ""
    scenario_bull_target: str = ""
    prob_bull: int = 35
    scenario_bear_trigger: str = ""
    scenario_bear_target: str = ""
    prob_bear: int = 50
    scenario_extreme_trigger: str = ""
    scenario_extreme_target: str = ""
    prob_extreme: int = 15
    key_watch_variables: list[str] = field(default_factory=list)
    fear_greed_stat_note: str = ""


@dataclass
class WeeklyReport:
    """完整周报输出结构，对应 SKILL.md 报告结构模板。"""
    symbol: str = "BTC"
    start_date: str = ""
    end_date: str = ""
    macro: MacroSignal = field(default_factory=MacroSignal)
    geopolitical: GeopoliticalSignal = field(default_factory=GeopoliticalSignal)
    etf: EtfFlowSignal = field(default_factory=EtfFlowSignal)
    derivatives: DerivativesSignal = field(default_factory=DerivativesSignal)
    on_chain: OnChainSignal = field(default_factory=OnChainSignal)
    price_structure: PriceStructureSignal = field(default_factory=PriceStructureSignal)
    judgment: ComprehensiveJudgment = field(default_factory=ComprehensiveJudgment)
    data_gaps: list[str] = field(default_factory=list)  # 数据缺失记录

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 信号判断逻辑（纯函数，便于单元测试）
# ---------------------------------------------------------------------------

def classify_macro_signal(fed_rate: Optional[float], cpi_yoy: Optional[float]) -> str:
    """
    根据 Fed 利率和通胀读数判断宏观信号方向。

    判断逻辑：
    - 利率 >= 4% 且通胀 >= 2.5% → 鹰派
    - 利率 <= 2% 或通胀 <= 2.0% → 鸽派
    - 其余 → 中性
    """
    if fed_rate is None and cpi_yoy is None:
        return "中性"
    if (fed_rate or 0) >= 4.0 and (cpi_yoy or 0) >= 2.5:
        return "鹰派"
    if (fed_rate or 5) <= 2.0 or (cpi_yoy or 5) <= 2.0:
        return "鸽派"
    return "中性"


def classify_derivatives_sentiment(
    funding_rate: Optional[float],
    oi_change_pct: Optional[float],
    long_short_ratio: Optional[float],
) -> str:
    """
    根据资金费率、OI变化、多空比判断衍生品情绪。

    判断逻辑：
    - 资金费率 < 0.01% 且 OI 下降 > 3% → 偏空
    - 资金费率 >= 0.03% 且 OI 稳定或上升 → 偏多
    - 其余 → 中性
    """
    bearish_signals = 0
    bullish_signals = 0

    if funding_rate is not None:
        if funding_rate < 0.01:
            bearish_signals += 1
        elif funding_rate >= 0.03:
            bullish_signals += 1

    if oi_change_pct is not None:
        if oi_change_pct < -3.0:
            bearish_signals += 1
        elif oi_change_pct > 3.0:
            bullish_signals += 1

    if long_short_ratio is not None:
        if long_short_ratio < 0.9:
            bearish_signals += 1
        elif long_short_ratio > 1.1:
            bullish_signals += 1

    if bearish_signals >= 2:
        return "偏空"
    if bullish_signals >= 2:
        return "偏多"
    return "中性"


def classify_etf_direction(weekly_netflow_usd: Optional[float]) -> str:
    """
    根据 ETF 周净流量方向分类。

    阈值：+/- $50M 以内视为混合。
    """
    if weekly_netflow_usd is None:
        return "混合"
    if weekly_netflow_usd > 50_000_000:
        return "净流入"
    if weekly_netflow_usd < -50_000_000:
        return "净流出"
    return "混合"


def count_bearish_signals(
    macro_signal: str,
    etf_direction: str,
    funding_rate: Optional[float],
    stablecoin_mcap_trend: str = "持平",  # 上升/持平/下降
) -> int:
    """
    统计偏空信号数量（对应 SKILL.md Step 7 判断框架）。

    计分规则：
    - 宏观鹰派 → +1
    - ETF 净流出 → +1
    - 资金费率低（< 0.01%）→ +1
    - 链上买力弱（稳定币持平或下降）→ +1
    """
    count = 0
    if macro_signal == "鹰派":
        count += 1
    if etf_direction == "净流出":
        count += 1
    if funding_rate is not None and funding_rate < 0.01:
        count += 1
    if stablecoin_mcap_trend in ("持平", "下降"):
        count += 1
    return count


def determine_short_term_bias(bearish_count: int, breakout_confirmed: bool = False) -> str:
    """
    根据偏空信号数量和突破确认状态判断短期方向。

    规则：
    - 已确认突破 → 偏多
    - 偏空信号 >= 3 → 偏弱震荡（偏空）
    - 偏空信号 1-2 → 震荡
    - 偏空信号 0 → 偏多
    """
    if breakout_confirmed:
        return "偏多"
    if bearish_count >= 3:
        return "偏空"
    if bearish_count >= 1:
        return "震荡"
    return "偏多"


def classify_fear_greed_label(index: Optional[int]) -> str:
    """将 Fear & Greed 数值转换为语义标签。"""
    if index is None:
        return "数据缺失"
    if index <= 20:
        return "极度恐慌"
    if index <= 40:
        return "恐慌"
    if index <= 60:
        return "中性"
    if index <= 80:
        return "贪婪"
    return "极度贪婪"


# ---------------------------------------------------------------------------
# Markdown 报告生成器
# ---------------------------------------------------------------------------

SIGNAL_ICON = {
    "鹰派": "🔴",
    "鸽派": "🟢",
    "中性": "🟡",
    "偏多": "🟢",
    "偏空": "🔴",
    "震荡": "🟡",
    "净流入": "🟢",
    "净流出": "🔴",
    "混合": "🟡",
    "高": "🔴",
    "中": "🟡",
    "低": "🟢",
    "强": "🟢",
    "弱": "🔴",
}


def _fmt_usd_m(amount: Optional[float]) -> str:
    """格式化美元金额为 $XXM 形式。"""
    if amount is None:
        return "数据缺失"
    m = amount / 1_000_000
    sign = "+" if m >= 0 else ""
    return f"{sign}{m:.0f}M"


def _fmt_pct(value: Optional[float]) -> str:
    if value is None:
        return "数据缺失"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def _fmt_price(value: Optional[float]) -> str:
    if value is None:
        return "数据缺失"
    return f"${value:,.0f}"


def generate_markdown_report(
    report: WeeklyReport,
    fear_greed_threshold: int = 20,
) -> str:
    """
    根据 WeeklyReport 数据对象生成符合 SKILL.md 报告结构模板的 Markdown 周报。

    参数：
        report: WeeklyReport 数据对象，由 Skill 执行框架填充各 Step 数据
        fear_greed_threshold: 极端恐慌判断阈值

    返回：
        完整的 Markdown 格式周报字符串
    """
    r = report
    m = r.macro
    e = r.etf
    d = r.derivatives
    o = r.on_chain
    p = r.price_structure
    j = r.judgment

    macro_icon = SIGNAL_ICON.get(m.signal, "🟡")
    etf_icon = SIGNAL_ICON.get(e.direction, "🟡")
    deriv_icon = SIGNAL_ICON.get(d.sentiment, "🟡")

    # -----------------------------------------------------------------------
    # 综合结论先行
    # -----------------------------------------------------------------------
    weekly_pct_str = _fmt_pct(p.weekly_pct_change)
    conclusion_lines = []
    if p.current_price and p.weekly_pct_change is not None:
        price_movement = "回落" if p.weekly_pct_change < 0 else "上涨"
        conclusion_lines.append(
            f"BTC 本周{price_movement}至 {_fmt_price(p.current_price)}（约 {weekly_pct_str}）。"
        )
    macro_note = f"宏观{m.signal}" if m.signal else "宏观数据待确认"
    etf_note = f"ETF 资金{e.direction}（周净 {_fmt_usd_m(e.btc_weekly_netflow_usd)}）" if e.btc_weekly_netflow_usd is not None else "ETF 数据待确认"
    deriv_note = f"衍生品{d.sentiment}（资金费率 {_fmt_pct(d.funding_rate)}）" if d.funding_rate is not None else "衍生品数据待确认"
    conclusion_lines.append(f"{macro_note}，{etf_note}，{deriv_note}。")

    onchain_notes = []
    if o.whale_net_accumulation_btc is not None:
        direction = "增持" if o.whale_net_accumulation_btc > 0 else "减持"
        onchain_notes.append(f"链上鲸鱼{direction}（+{o.whale_net_accumulation_btc:,.0f} BTC）")
    if o.stablecoin_mcap_usd_b is not None:
        onchain_notes.append(f"稳定币场外资金 ${o.stablecoin_mcap_usd_b:.0f}B")
    if onchain_notes:
        conclusion_lines.append("，".join(onchain_notes) + "。")

    conclusion_lines.append(
        f"**短期：{j.short_term_bias}。中期：取决于{j.scenario_bear_trigger or '关键宏观变量'}。**"
    )

    # -----------------------------------------------------------------------
    # 构建各章节
    # -----------------------------------------------------------------------
    sections = []

    # 标题
    sections.append(f"## {r.symbol} 周度市场分析报告 — {r.start_date} ~ {r.end_date}")
    sections.append("")
    sections.append("### 综合结论（先行）")
    sections.extend(conclusion_lines)
    sections.append("")

    # 一、宏观
    sections.append(f"### 一、宏观信号 {macro_icon} {m.signal}")
    sections.append("| 指标 | 数值 | 信号 |")
    sections.append("|------|------|------|")
    sections.append(f"| Fed 利率 | {f'{m.fed_rate}%' if m.fed_rate else '数据缺失'} | {'维持高位' if (m.fed_rate or 0) >= 3.5 else '宽松路径'} |")
    sections.append(f"| 通胀（CPI） | {f'{m.cpi_yoy}%' if m.cpi_yoy else '数据缺失'} | {'偏紧' if (m.cpi_yoy or 0) >= 2.5 else '受控'} |")
    sections.append(f"| DXY | {m.dxy_estimate or '数据缺失'} | — |")
    sections.append(f"| 黄金（PAXG）本周涨跌 | {_fmt_pct(m.gold_weekly_pct)} | {'BTC 未跟涨，避险属性弱化' if r.geopolitical.gold_btc_divergence else 'BTC 同步联动'} |")
    if m.notes:
        sections.append("")
        for note in m.notes:
            sections.append(f"> {note}")
    sections.append("")

    # 二、ETF
    sections.append(f"### 二、ETF 资金 {etf_icon} {e.direction}")
    if e.daily_flows:
        sections.append("| 日期 | BTC ETF 净流量 | 备注 |")
        sections.append("|------|---------------|------|")
        for flow in e.daily_flows:
            sections.append(f"| {flow.get('date', '—')} | {_fmt_usd_m(flow.get('amount_usd'))} | {flow.get('note', '—')} |")
    sections.append(f"| 周合计 | **{_fmt_usd_m(e.btc_weekly_netflow_usd)}** | {'净流出确认' if e.direction == '净流出' else '净流入'} |")
    if e.eth_weekly_netflow_usd is not None:
        sections.append(f"ETH ETF 周累计: {_fmt_usd_m(e.eth_weekly_netflow_usd)}")
    sections.append(f"**背离信号**: {e.divergence_note if e.divergence_flag else '无明显背离信号'}")
    sections.append("")

    # 三、衍生品
    sections.append(f"### 三、衍生品结构 {deriv_icon} {d.sentiment}")
    sections.append("| 指标 | 数值 | 基准/信号 |")
    sections.append("|------|------|---------|")
    sections.append(f"| 资金费率 | {_fmt_pct(d.funding_rate)} | 正常牛市 0.03%+ |")
    sections.append(f"| OI | {_fmt_usd_m(d.oi_value)}（{_fmt_pct(d.oi_change_pct)}）| {'去杠杆进行中' if (d.oi_change_pct or 0) < -3 else '杠杆稳定'} |")
    sections.append(f"| 多空比 | {d.long_short_ratio if d.long_short_ratio else '数据缺失'} | {'偏空' if (d.long_short_ratio or 1) < 0.95 else '偏多' if (d.long_short_ratio or 1) > 1.05 else '中性'} |")
    liq_long = _fmt_usd_m(d.liquidation_long_usd)
    liq_short = _fmt_usd_m(d.liquidation_short_usd)
    sections.append(f"| 爆仓（多头/空头）| {liq_long} / {liq_short} | {'多头爆仓为主，拉盘受阻' if (d.liquidation_long_usd or 0) > (d.liquidation_short_usd or 0) else '空头爆仓为主，短期反弹动能'} |")
    sections.append("> 注：期权 put/call 偏斜（Deribit）无 MCP 覆盖，建议参考 Laevitas.ch")
    sections.append("")

    # 四、链上
    fear_greed_icon = "⚠️" if (o.fear_greed_index or 100) < fear_greed_threshold else "🟡"
    sections.append(f"### 四、链上结构 {fear_greed_icon} 供需评估")
    sections.append("| 指标 | 数值 | 信号 |")
    sections.append("|------|------|------|")
    whale_val = f"+{o.whale_net_accumulation_btc:,.0f} BTC" if (o.whale_net_accumulation_btc or 0) >= 0 else f"{o.whale_net_accumulation_btc:,.0f} BTC"
    sections.append(f"| 鲸鱼净增减持（估算）| {whale_val if o.whale_net_accumulation_btc is not None else '数据缺失'} | {'增持信号 🟢' if (o.whale_net_accumulation_btc or 0) > 0 else '减持信号 🔴'} |")
    reserve_chg = f"{o.exchange_reserve_change_btc:+,.0f} BTC" if o.exchange_reserve_change_btc is not None else "数据缺失"
    sections.append(f"| 交易所 BTC 存量变化 | {reserve_chg} | {'抛压减少 🟢' if (o.exchange_reserve_change_btc or 0) < 0 else '抛压增加 🔴'} |")
    sections.append(f"| 稳定币总量 | ${o.stablecoin_mcap_usd_b:.0f}B" + ("（持平）" if o.stablecoin_mcap_usd_b else "") + f" | {'无新增买力 🔴' if o.buy_power == '弱' else '资金流入 🟢'} |")
    sections.append(f"| MVRV 近似盈利供应率 | ~{o.supply_in_profit_pct:.0f}%" if o.supply_in_profit_pct else "| MVRV 盈利供应率 | 数据缺失 | — |")
    sections.append(f"| Fear & Greed 指数 | {o.fear_greed_index if o.fear_greed_index is not None else '数据缺失'} | {o.fear_greed_label} |")
    sections.append("")
    sections.append(f"**核心矛盾**: 卖压 {o.sell_pressure} × 买力 {o.buy_power} — 需关注稳定币场外资金是否启动")
    sections.append("")

    # 五、价格结构
    sections.append("### 五、价格结构")
    supports_str = " → ".join(_fmt_price(s) for s in p.key_supports) if p.key_supports else "待确认"
    resistances_str = " → ".join(_fmt_price(r_) for r_ in p.key_resistances) if p.key_resistances else "待确认"
    sections.append(f"- 支撑: {supports_str}")
    sections.append(f"- 压力: {resistances_str}")
    low_str = _fmt_price(p.weekly_low)
    high_str = _fmt_price(p.weekly_high)
    sections.append(f"- 本周价格区间: {low_str} ~ {high_str}（周涨跌 {weekly_pct_str}）")
    sections.append(f"- 近期驱动判断: {p.driver}")
    sections.append(f"- 结构评估: {p.structure}")
    sections.append("")

    # 六、综合判断
    sections.append("### 六、综合判断")
    sections.append(f"**短期（1-2周）: {j.short_term_bias}，参考区间 {j.short_term_range}**")
    sections.append(f"- 突破确认条件: {j.breakout_confirmation_condition}")
    sections.append("")
    sections.append("**中期（1-3月）情景路径:**")
    sections.append("| 情景 | 触发条件 | 目标区间 | 概率估计 |")
    sections.append("|------|---------|---------|---------|")
    sections.append(f"| 乐观 | {j.scenario_bull_trigger} | {j.scenario_bull_target} | ~{j.prob_bull}% |")
    sections.append(f"| 悲观 | {j.scenario_bear_trigger} | {j.scenario_bear_target} | ~{j.prob_bear}% |")
    sections.append(f"| 极端 | {j.scenario_extreme_trigger} | {j.scenario_extreme_target} | ~{j.prob_extreme}% |")
    sections.append("")
    sections.append("**关键观察变量:**")
    for i, var in enumerate(j.key_watch_variables, 1):
        sections.append(f"{i}. {var}")
    sections.append("")

    # Fear & Greed 统计补充
    if o.fear_greed_index is not None and o.fear_greed_index < fear_greed_threshold:
        sections.append(f"**统计参考（F&G 极端恐慌区间 < {fear_greed_threshold}）：**")
        sections.append(f"- F&G < {fear_greed_threshold} 历史 30 日正收益概率：参考历史数据约 65-70%（样本量有限，统计仅供参考）")
        if o.whale_net_accumulation_btc is not None and o.whale_net_accumulation_btc > 0:
            sections.append("- 当前鲸鱼增持信号与 2023 Q4 底部区间特征相似，可作辅助参考")
        sections.append("")

    # 数据缺失说明
    if r.data_gaps:
        sections.append("**数据缺失说明：**")
        for gap in r.data_gaps:
            sections.append(f"- {gap}")
        sections.append("")

    sections.append("*免责声明：本报告由 AI 自动生成，基于历史数据不能预测未来走势。方法论归属原作者 @Guolier8。不构成投资建议。*")

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# 主入口（命令行调用）
# ---------------------------------------------------------------------------

def main() -> None:
    """
    命令行入口，接收参数并调用分析流程。

    实际数据采集通过 Claude MCP 工具调用完成（Skill 执行框架负责）。
    本脚本主要提供：
    1. 参数解析与日期推算（AnalysisParams.resolve_dates）
    2. 信号判断逻辑（classify_* 函数）
    3. Markdown 报告生成（generate_markdown_report）

    在 Skill 执行环境中，Claude 会在 SKILL.md Action Specification 的指导下，
    依次调用 Antseer MCP 工具，将数据填充到 WeeklyReport 数据结构，
    最后调用 generate_markdown_report 输出周报。
    """
    import argparse

    parser = argparse.ArgumentParser(description="BTC 周度综合市场分析")
    parser.add_argument("symbol", nargs="?", default="BTC", help="分析标的（默认 BTC）")
    parser.add_argument("--start_date", help="分析开始日期 YYYY-MM-DD")
    parser.add_argument("--end_date", help="分析结束日期 YYYY-MM-DD")
    parser.add_argument("--include_eth_etf", type=lambda x: x.lower() == "true", default=True)
    parser.add_argument("--whale_threshold", type=int, default=1000)
    parser.add_argument("--whale_lookback_days", type=int, default=14)
    parser.add_argument("--fear_greed_threshold", type=int, default=20)
    parser.add_argument("--output_json", help="输出 JSON 路径（可选）")
    args = parser.parse_args()

    params = AnalysisParams(
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        include_eth_etf=args.include_eth_etf,
        whale_threshold=args.whale_threshold,
        whale_lookback_days=args.whale_lookback_days,
        fear_greed_threshold=args.fear_greed_threshold,
    )

    start_date, end_date = params.resolve_dates()

    # 创建空报告模板，供 Skill 执行框架填充
    report = WeeklyReport(
        symbol=params.symbol,
        start_date=start_date,
        end_date=end_date,
    )

    # 在非 MCP 环境下输出空模板 JSON 供调试
    print(f"分析周期: {start_date} ~ {end_date}")
    print(f"参数: whale_threshold={params.whale_threshold}, lookback={params.whale_lookback_days}d, "
          f"fear_greed_threshold={params.fear_greed_threshold}, include_eth_etf={params.include_eth_etf}")
    print()
    print("提示: 实际数据采集通过 Antseer MCP 工具完成。")
    print("请在 Claude Code 中运行 /btc-weekly-market-analysis 以获取完整报告。")

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"空模板 JSON 已输出至: {args.output_json}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
