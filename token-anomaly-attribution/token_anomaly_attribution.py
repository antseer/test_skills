"""
token_anomaly_attribution.py
代币异动归因框架分析 — 主实现模块

方法论归属：@Guolier8
本模块封装 9 步归因分析框架，通过 Antseer MCP 工具采集量化数据，
输出结构化归因报告，辅助判断行情性质与操作策略。

用法（通过 Claude Code Skill 调用）：
    /token-anomaly-attribution HYPE --direction=pump --time_range=7d
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Literal, Optional


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

Direction = Literal["pump", "dump", "unknown"]
WhaleAction = Literal["accumulate", "distribute", "neutral", "unavailable"]
SmartMoneyDirection = Literal["inflow", "outflow", "neutral", "unavailable"]
LeverageSignal = Literal["overleveraged_long", "overleveraged_short", "neutral"]
EtfSignal = Literal["institutional_inflow", "institutional_outflow", "na"]
SentimentTrend = Literal["rising", "falling", "stable"]
SustainabilityRating = Literal["high", "medium-high", "medium", "low"]
ActionSuggestion = Literal["chase", "hold", "wait", "exit", "verify_first"]
ExchangeFlowSignal = Literal["bullish", "bearish", "neutral"]
MacdSignal = Literal["bullish_cross", "bearish_cross", "neutral"]


@dataclass
class Step1Result:
    """价格异动确认与市场背景对比"""
    price_change_pct: float = 0.0
    btc_change_pct: float = 0.0
    market_beta: float = 0.0
    is_idiosyncratic: bool = False
    direction: Direction = "unknown"
    raw_data: dict = field(default_factory=dict)


@dataclass
class Step2Result:
    """链上鲸鱼与大户持仓变化"""
    whale_action: WhaleAction = "neutral"
    whale_exchange_inflow: float = 0.0  # 单位：代币数量，正=流入，负=流出
    top_holders_change_pct: float = 0.0
    has_token_address: bool = False
    raw_data: dict = field(default_factory=dict)


@dataclass
class Step3Result:
    """交易所资金净流量分析"""
    exchange_netflow_7d: float = 0.0  # 正=流入（偏空），负=流出（偏多）
    reserve_change_pct: float = 0.0
    exchange_flow_signal: ExchangeFlowSignal = "neutral"
    raw_data: dict = field(default_factory=dict)


@dataclass
class Step4Result:
    """衍生品结构分析"""
    oi_change_pct: float = 0.0
    funding_rate_avg: float = 0.0
    leverage_signal: LeverageSignal = "neutral"
    raw_data: dict = field(default_factory=dict)


@dataclass
class Step5Result:
    """Smart Money 行为追踪"""
    smart_money_direction: SmartMoneyDirection = "neutral"
    smart_money_conviction: Literal["high", "medium", "low"] = "medium"
    net_flow_usd: float = 0.0
    raw_data: dict = field(default_factory=dict)


@dataclass
class Step6Result:
    """市场情绪与社交热度"""
    sentiment_score: float = 0.0  # 0-100
    sentiment_trend: SentimentTrend = "stable"
    social_spike: bool = False
    raw_data: dict = field(default_factory=dict)


@dataclass
class Step7Result:
    """ETF 资金流分析（仅 BTC/ETH）"""
    etf_netflow_7d: float = 0.0  # 单位：百万美元
    etf_signal: EtfSignal = "na"
    applicable: bool = False
    raw_data: dict = field(default_factory=dict)


@dataclass
class Step8Result:
    """技术指标确认"""
    rsi_14: float = 50.0
    macd_signal: MacdSignal = "neutral"
    macd_histogram: float = 0.0
    raw_data: dict = field(default_factory=dict)


@dataclass
class AttributionFactor:
    """单个归因因素"""
    rank: int
    factor_name: str
    signal_strength: Literal["confirmed", "pending_verification", "counter_signal", "neutral"]
    data_source: str
    sustainability: Literal["high", "medium-high", "medium", "low", "na"]
    note: str = ""


@dataclass
class AttributionReport:
    """最终归因报告"""
    symbol: str
    analysis_time: str
    time_range: str
    price_change_pct: float
    direction: Direction
    market_beta: float
    is_idiosyncratic: bool

    # 量化核心指标
    whale_action: WhaleAction
    exchange_netflow_7d: float
    oi_change_pct: float
    funding_rate_avg: float
    leverage_signal: LeverageSignal
    smart_money_direction: SmartMoneyDirection
    rsi_14: float
    macd_signal: MacdSignal
    sentiment_score: float
    sentiment_trend: SentimentTrend
    social_spike: bool
    etf_netflow_7d: float
    etf_signal: EtfSignal

    # 归因结论
    attribution_factors: list[AttributionFactor]
    unverifiable_factors: list[str]
    sustainability_rating: SustainabilityRating
    action_suggestion: ActionSuggestion
    followup_watchpoints: list[str]
    report_markdown: str = ""


# ---------------------------------------------------------------------------
# 归因逻辑
# ---------------------------------------------------------------------------

class TokenAnomalyAttributor:
    """
    代币异动归因器

    负责汇总 Step 1-8 的中间结果，执行综合评估逻辑，输出最终报告。
    实际的 MCP 工具调用由 Claude Code Skill 执行，本类负责分析逻辑和报告生成。
    """

    ETF_ELIGIBLE_SYMBOLS = {"BTC", "ETH", "WBTC", "WETH"}
    FUNDING_RATE_OVERHEAT_THRESHOLD = 0.05   # % per 8h
    FUNDING_RATE_EXTREME_NEGATIVE = -0.05    # % per 8h
    RSI_OVERBOUGHT = 75.0
    RSI_OVERSOLD = 30.0

    def __init__(
        self,
        symbol: str,
        direction: str = "auto",
        time_range: str = "7d",
        chain: str = "auto",
        token_address: Optional[str] = None,
        threshold_pct: float = 10.0,
    ):
        self.symbol = symbol.upper()
        self.direction_input = direction
        self.time_range = time_range
        self.chain = chain
        self.token_address = token_address
        self.threshold_pct = threshold_pct

    # ------------------------------------------------------------------
    # 步骤结果聚合 — 由 Skill 调用 MCP 工具后传入原始结果
    # ------------------------------------------------------------------

    def parse_step1(self, raw: dict) -> Step1Result:
        """解析 ant_spot_market_structure 返回的价格数据"""
        result = Step1Result(raw_data=raw)
        coins = raw.get("data", [])
        target_data = next((c for c in coins if c.get("symbol", "").upper() == self.symbol), None)
        btc_data = next((c for c in coins if c.get("symbol", "").upper() == "BTC"), None)

        if target_data:
            result.price_change_pct = float(target_data.get("price_change_percentage_24h", 0))
        if btc_data:
            result.btc_change_pct = float(btc_data.get("price_change_percentage_24h", 0))

        # 计算联动系数（简化：用变化量差值绝对值衡量）
        diff = abs(result.price_change_pct - result.btc_change_pct)
        result.is_idiosyncratic = diff >= 10.0
        result.market_beta = round(
            min(1.0, max(0.0, 1.0 - diff / max(abs(result.price_change_pct), 1))), 2
        )

        # 自动判断方向
        if self.direction_input == "auto":
            result.direction = "pump" if result.price_change_pct > 0 else "dump"
        else:
            result.direction = self.direction_input  # type: ignore

        return result

    def parse_step2(self, whale_transfer_raw: dict, holders_raw: Optional[dict] = None) -> Step2Result:
        """解析鲸鱼大额转账和持仓变化数据"""
        result = Step2Result(has_token_address=self.token_address is not None, raw_data=whale_transfer_raw)

        transfers = whale_transfer_raw.get("data", [])
        net_inflow = sum(
            float(t.get("amount", 0)) * (1 if t.get("direction") == "in" else -1)
            for t in transfers
        )
        result.whale_exchange_inflow = net_inflow

        if net_inflow > 1000:
            result.whale_action = "distribute"
        elif net_inflow < -1000:
            result.whale_action = "accumulate"
        else:
            result.whale_action = "neutral"

        if holders_raw:
            result.top_holders_change_pct = float(holders_raw.get("top50_change_pct", 0))

        return result

    def parse_step3(self, netflow_raw: dict, reserve_raw: dict) -> Step3Result:
        """解析交易所净流量和储备数据"""
        result = Step3Result(raw_data={**netflow_raw, **reserve_raw})
        result.exchange_netflow_7d = float(netflow_raw.get("data", {}).get("netflow_7d", 0))
        result.reserve_change_pct = float(reserve_raw.get("data", {}).get("change_pct", 0))

        if result.exchange_netflow_7d < -500:
            result.exchange_flow_signal = "bullish"
        elif result.exchange_netflow_7d > 500:
            result.exchange_flow_signal = "bearish"
        else:
            result.exchange_flow_signal = "neutral"

        return result

    def parse_step4(self, oi_raw: dict, funding_raw: dict) -> Step4Result:
        """解析 OI 和资金费率数据"""
        result = Step4Result(raw_data={**oi_raw, **funding_raw})
        result.oi_change_pct = float(oi_raw.get("data", {}).get("change_pct", 0))

        rates = funding_raw.get("data", [])
        if rates:
            result.funding_rate_avg = sum(float(r.get("rate", 0)) for r in rates) / len(rates)

        if result.funding_rate_avg > self.FUNDING_RATE_OVERHEAT_THRESHOLD:
            result.leverage_signal = "overleveraged_long"
        elif result.funding_rate_avg < self.FUNDING_RATE_EXTREME_NEGATIVE:
            result.leverage_signal = "overleveraged_short"
        else:
            result.leverage_signal = "neutral"

        return result

    def parse_step5(self, netflow_raw: dict, holdings_raw: dict) -> Step5Result:
        """解析 Smart Money 数据"""
        result = Step5Result(raw_data={**netflow_raw, **holdings_raw})
        net_usd = float(netflow_raw.get("data", {}).get("net_usd", 0))
        result.net_flow_usd = net_usd

        if net_usd > 500_000:
            result.smart_money_direction = "inflow"
            result.smart_money_conviction = "high" if net_usd > 2_000_000 else "medium"
        elif net_usd < -500_000:
            result.smart_money_direction = "outflow"
            result.smart_money_conviction = "high" if net_usd < -2_000_000 else "medium"
        else:
            result.smart_money_direction = "neutral"
            result.smart_money_conviction = "low"

        return result

    def parse_step6(self, coin_detail_raw: dict, topics_raw: dict) -> Step6Result:
        """解析市场情绪数据"""
        result = Step6Result(raw_data={**coin_detail_raw, **topics_raw})
        result.sentiment_score = float(coin_detail_raw.get("data", {}).get("sentiment_score", 50))

        trend_val = float(coin_detail_raw.get("data", {}).get("sentiment_change_24h", 0))
        if trend_val > 5:
            result.sentiment_trend = "rising"
        elif trend_val < -5:
            result.sentiment_trend = "falling"
        else:
            result.sentiment_trend = "stable"

        # 情绪急剧飙升：24h 内评分涨幅 > 15 且当前分数 > 70
        result.social_spike = (trend_val > 15 and result.sentiment_score > 70)

        return result

    def parse_step7(self, etf_raw: dict) -> Step7Result:
        """解析 ETF 资金流数据（仅 BTC/ETH）"""
        result = Step7Result()
        result.applicable = self.symbol in self.ETF_ELIGIBLE_SYMBOLS

        if not result.applicable:
            return result

        result.raw_data = etf_raw
        result.etf_netflow_7d = float(etf_raw.get("data", {}).get("net_flow_7d_million_usd", 0))

        if result.etf_netflow_7d > 100:
            result.etf_signal = "institutional_inflow"
        elif result.etf_netflow_7d < -100:
            result.etf_signal = "institutional_outflow"
        else:
            result.etf_signal = "na"

        return result

    def parse_step8(self, rsi_raw: dict, macd_raw: dict) -> Step8Result:
        """解析技术指标数据"""
        result = Step8Result(raw_data={**rsi_raw, **macd_raw})
        result.rsi_14 = float(rsi_raw.get("data", {}).get("rsi_14", 50))
        result.macd_histogram = float(macd_raw.get("data", {}).get("histogram", 0))

        histogram_trend = macd_raw.get("data", {}).get("histogram_trend", "flat")
        if histogram_trend == "rising" and result.macd_histogram > 0:
            result.macd_signal = "bullish_cross"
        elif histogram_trend == "falling" and result.macd_histogram < 0:
            result.macd_signal = "bearish_cross"
        else:
            result.macd_signal = "neutral"

        return result

    # ------------------------------------------------------------------
    # Step 9: 综合归因评估
    # ------------------------------------------------------------------

    def synthesize(
        self,
        s1: Step1Result,
        s2: Step2Result,
        s3: Step3Result,
        s4: Step4Result,
        s5: Step5Result,
        s6: Step6Result,
        s7: Step7Result,
        s8: Step8Result,
    ) -> AttributionReport:
        """汇总所有步骤结果，执行综合归因评估，生成最终报告"""

        direction = s1.direction

        # --- 归因因素构建 ---
        attribution_factors: list[AttributionFactor] = []
        rank = 1

        # 市场 Beta（大盘带飞/拖累）
        if not s1.is_idiosyncratic:
            attribution_factors.append(AttributionFactor(
                rank=rank,
                factor_name="大盘带飞/拖累（市场 Beta 高）",
                signal_strength="confirmed",
                data_source="ant_spot_market_structure",
                sustainability="low",
                note=f"联动系数 β={s1.market_beta}，与 BTC 高度同步",
            ))
            rank += 1

        # 鲸鱼行为
        if s2.whale_action != "neutral" and s2.whale_action != "unavailable":
            factor_name = "鲸鱼集中增持" if s2.whale_action == "accumulate" else "鲸鱼出货/转入交易所"
            attribution_factors.append(AttributionFactor(
                rank=rank,
                factor_name=factor_name,
                signal_strength="confirmed",
                data_source="ant_fund_flow / ant_token_analytics",
                sustainability="high" if s2.whale_action == "accumulate" else "high",
                note=f"交易所净流量: {s2.whale_exchange_inflow:+.0f}",
            ))
            rank += 1

        # 交易所资金净流
        if s3.exchange_flow_signal != "neutral":
            factor_name = "交易所净流出（持仓意愿强）" if s3.exchange_flow_signal == "bullish" else "交易所净流入（抛售压力）"
            attribution_factors.append(AttributionFactor(
                rank=rank,
                factor_name=factor_name,
                signal_strength="confirmed",
                data_source="ant_fund_flow",
                sustainability="medium-high",
                note=f"7日净流量: {s3.exchange_netflow_7d:+.0f}",
            ))
            rank += 1

        # 衍生品结构
        if s4.leverage_signal != "neutral":
            if s4.leverage_signal == "overleveraged_long":
                attribution_factors.append(AttributionFactor(
                    rank=rank,
                    factor_name="多头杠杆过热（资金费率偏高）",
                    signal_strength="counter_signal" if direction == "pump" else "confirmed",
                    data_source="ant_futures_market_structure",
                    sustainability="low",
                    note=f"资金费率: {s4.funding_rate_avg:+.4f}%，OI 变化: {s4.oi_change_pct:+.1f}%",
                ))
            else:
                attribution_factors.append(AttributionFactor(
                    rank=rank,
                    factor_name="空头超载（资金费率极负，短期反弹可能）",
                    signal_strength="confirmed",
                    data_source="ant_futures_market_structure",
                    sustainability="medium",
                    note=f"资金费率: {s4.funding_rate_avg:+.4f}%",
                ))
            rank += 1
        else:
            # 资金费率健康是 pump 的正向信号
            if direction == "pump":
                attribution_factors.append(AttributionFactor(
                    rank=rank,
                    factor_name="资金费率健康（杠杆结构未过热）",
                    signal_strength="confirmed",
                    data_source="ant_futures_market_structure",
                    sustainability="medium",
                    note=f"资金费率: {s4.funding_rate_avg:+.4f}%，OI 变化: {s4.oi_change_pct:+.1f}%",
                ))
                rank += 1

        # Smart Money
        if s5.smart_money_direction != "neutral" and s5.smart_money_direction != "unavailable":
            factor_name = "Smart Money 净流入" if s5.smart_money_direction == "inflow" else "Smart Money 撤离"
            attribution_factors.append(AttributionFactor(
                rank=rank,
                factor_name=factor_name,
                signal_strength="confirmed",
                data_source="ant_smart_money",
                sustainability="high" if s5.smart_money_direction == "inflow" else "high",
                note=f"净流量: ${s5.net_flow_usd:+,.0f}，置信度: {s5.smart_money_conviction}",
            ))
            rank += 1

        # 情绪效应
        if s6.social_spike:
            attribution_factors.append(AttributionFactor(
                rank=rank,
                factor_name="社交情绪急升（KOL 效应/话题爆发）",
                signal_strength="confirmed" if direction == "pump" else "neutral",
                data_source="ant_market_sentiment",
                sustainability="low",
                note=f"情绪评分: {s6.sentiment_score}/100，趋势: {s6.sentiment_trend}",
            ))
            rank += 1

        # ETF 信号（BTC/ETH）
        if s7.applicable and s7.etf_signal != "na":
            factor_name = "ETF 机构资金持续流入" if s7.etf_signal == "institutional_inflow" else "ETF 机构资金撤离"
            attribution_factors.append(AttributionFactor(
                rank=rank,
                factor_name=factor_name,
                signal_strength="confirmed",
                data_source="ant_etf_fund_flow",
                sustainability="high",
                note=f"7日 ETF 净流量: {s7.etf_netflow_7d:+.0f}M USD",
            ))
            rank += 1

        # 技术指标（超买/超卖）
        if s8.rsi_14 > self.RSI_OVERBOUGHT:
            attribution_factors.append(AttributionFactor(
                rank=rank,
                factor_name=f"技术面超买（RSI={s8.rsi_14:.1f}）",
                signal_strength="counter_signal" if direction == "pump" else "neutral",
                data_source="ant_market_indicators",
                sustainability="low",
                note="RSI > 75，追涨风险较高",
            ))
            rank += 1
        elif s8.rsi_14 < self.RSI_OVERSOLD:
            attribution_factors.append(AttributionFactor(
                rank=rank,
                factor_name=f"技术面超卖（RSI={s8.rsi_14:.1f}）",
                signal_strength="confirmed" if direction == "dump" else "neutral",
                data_source="ant_market_indicators",
                sustainability="medium",
                note="RSI < 30，短期技术性反弹空间",
            ))
            rank += 1

        # 非量化因素（需人工核查）
        unverifiable_factors = [
            "主网升级 / 协议提案（需查项目官方公告、Snapshot.org、GitHub）",
            "合作 / 集成公告（需查 CryptoPanic、Twitter 官方账号）",
            "交易所上架 / 下架预期（需查各交易所公告页面）",
            "安全事件 / 黑客攻击（需查 Rekt.news、DeFiLlama Hacks）",
            "上市公司持仓变动（需查 SEC EDGAR 13F 披露文件）",
        ]

        # --- 持续性评级 ---
        sustainability_rating = self._calculate_sustainability(
            direction, s1, s2, s3, s4, s5, s6, s7, s8, attribution_factors
        )

        # --- 操作建议 ---
        action_suggestion = self._determine_action(
            direction, sustainability_rating, s4, s6, s8, attribution_factors
        )

        # --- 后续跟踪观察点 ---
        followup_watchpoints = self._build_followup_watchpoints(
            direction, s3, s4, s6, s7, s8
        )

        report = AttributionReport(
            symbol=self.symbol,
            analysis_time=datetime.utcnow().isoformat() + "Z",
            time_range=self.time_range,
            price_change_pct=s1.price_change_pct,
            direction=direction,
            market_beta=s1.market_beta,
            is_idiosyncratic=s1.is_idiosyncratic,
            whale_action=s2.whale_action,
            exchange_netflow_7d=s3.exchange_netflow_7d,
            oi_change_pct=s4.oi_change_pct,
            funding_rate_avg=s4.funding_rate_avg,
            leverage_signal=s4.leverage_signal,
            smart_money_direction=s5.smart_money_direction,
            rsi_14=s8.rsi_14,
            macd_signal=s8.macd_signal,
            sentiment_score=s6.sentiment_score,
            sentiment_trend=s6.sentiment_trend,
            social_spike=s6.social_spike,
            etf_netflow_7d=s7.etf_netflow_7d,
            etf_signal=s7.etf_signal,
            attribution_factors=attribution_factors,
            unverifiable_factors=unverifiable_factors,
            sustainability_rating=sustainability_rating,
            action_suggestion=action_suggestion,
            followup_watchpoints=followup_watchpoints,
        )
        report.report_markdown = self._render_markdown(report)
        return report

    # ------------------------------------------------------------------
    # 内部评估逻辑
    # ------------------------------------------------------------------

    def _calculate_sustainability(
        self,
        direction: Direction,
        s1: Step1Result,
        s2: Step2Result,
        s3: Step3Result,
        s4: Step4Result,
        s5: Step5Result,
        s6: Step6Result,
        s7: Step7Result,
        s8: Step8Result,
        factors: list[AttributionFactor],
    ) -> SustainabilityRating:
        """计算行情持续性评级"""
        score = 0

        if direction == "pump":
            # 正向加分
            if not s1.is_idiosyncratic:
                score += 0   # 随大盘，不加分
            else:
                score += 10  # 个币独立行情，基础加分

            if s2.whale_action == "accumulate":
                score += 25
            if s3.exchange_flow_signal == "bullish":
                score += 15
            if s4.leverage_signal == "neutral":
                score += 10  # 资金费率健康
            if s5.smart_money_direction == "inflow":
                score += 25 if s5.smart_money_conviction == "high" else 15
            if s7.etf_signal == "institutional_inflow":
                score += 20

            # 负向扣分
            if s4.leverage_signal == "overleveraged_long":
                score -= 20
            if s6.social_spike:
                score -= 10  # 情绪顶部风险
            if s8.rsi_14 > self.RSI_OVERBOUGHT:
                score -= 15

        else:  # dump
            # 评估反弹可能性（score 高 = 跌势不持续 = 或有反弹）
            if s4.leverage_signal == "overleveraged_short":
                score += 20
            if s8.rsi_14 < self.RSI_OVERSOLD:
                score += 15
            if s3.exchange_flow_signal == "bullish":
                score += 10

            # 跌势持续性风险（score 低）
            if s2.whale_action == "distribute":
                score -= 25
            if s5.smart_money_direction == "outflow":
                score -= 20
            if s3.exchange_flow_signal == "bearish":
                score -= 15
            if not s1.is_idiosyncratic:
                score -= 5  # 随大盘跌，持续性中等

            # dump 的 score 解释为"反弹可能性"
            # 对 dump，score 高意味着跌势不持续（短期反弹）
            if score >= 25:
                return "low"   # 跌势持续性低（反弹可能）
            elif score >= 10:
                return "medium"
            elif score >= -10:
                return "medium-high"
            else:
                return "high"  # 跌势持续性高

        # pump 方向
        if score >= 50:
            return "high"
        elif score >= 30:
            return "medium-high"
        elif score >= 10:
            return "medium"
        else:
            return "low"

    def _determine_action(
        self,
        direction: Direction,
        sustainability: SustainabilityRating,
        s4: Step4Result,
        s6: Step6Result,
        s8: Step8Result,
        factors: list[AttributionFactor],
    ) -> ActionSuggestion:
        """根据综合评估结果给出操作建议"""
        pending_count = sum(
            1 for f in factors if f.signal_strength == "pending_verification"
        )
        counter_count = sum(
            1 for f in factors if f.signal_strength == "counter_signal"
        )

        if direction == "pump":
            if sustainability in ("high", "medium-high") and pending_count == 0 and counter_count == 0:
                return "chase"
            elif sustainability in ("high", "medium-high") and pending_count > 0:
                return "verify_first"
            elif counter_count > 0 or s4.leverage_signal == "overleveraged_long":
                return "wait"
            elif sustainability == "low":
                return "wait"
            else:
                return "verify_first"
        else:  # dump
            if sustainability in ("high", "medium-high"):
                # 跌势持续性高，建议减仓
                return "exit"
            elif sustainability in ("low",) and s8.rsi_14 < self.RSI_OVERSOLD:
                # 技术性超卖，持有等反弹
                return "hold"
            else:
                return "wait"

    def _build_followup_watchpoints(
        self,
        direction: Direction,
        s3: Step3Result,
        s4: Step4Result,
        s6: Step6Result,
        s7: Step7Result,
        s8: Step8Result,
    ) -> list[str]:
        """构建后续跟踪观察点"""
        points = []

        if direction == "pump":
            points.append("交易量能否维持当前水平（建议每 24h 检查一次，量价齐跌是风险信号）")
            if s4.funding_rate_avg < 0.03:
                points.append(f"资金费率是否持续走高（当前 {s4.funding_rate_avg:+.4f}%，超过 0.05% 开始过热预警）")
            if s6.social_spike:
                points.append("情绪热度是否持续或回落（情绪顶部后一般有 1-3 天震荡期）")
            if s7.etf_signal == "institutional_inflow":
                points.append("ETF 日净流量是否保持正值（连续 3 天净流出则机构信号翻转）")
        else:
            points.append("关键支撑位是否守住（建议关注链上大额买单情况）")
            if s4.leverage_signal == "overleveraged_short":
                points.append("资金费率是否恢复正常（极负值持续说明空头仍在加码）")
            if s8.rsi_14 < self.RSI_OVERSOLD:
                points.append(f"RSI 是否从超卖区（当前 {s8.rsi_14:.1f}）回升至 40 以上（技术性反弹信号）")

        points.append("鲸鱼地址是否出现大额转入/转出交易所（可作为主力动向早期预警）")
        points.append("Smart Money 净流向是否持续（连续 3 日同向流动置信度更高）")

        return points[:5]  # 最多返回 5 条

    # ------------------------------------------------------------------
    # Markdown 报告渲染
    # ------------------------------------------------------------------

    def _render_markdown(self, report: AttributionReport) -> str:
        direction_label = "pump（上涨异动）" if report.direction == "pump" else "dump（下跌异动）"
        idio_label = "个币独立行情，非市场普涨/跌带动" if report.is_idiosyncratic else "与大盘高度联动，市场因素为主"
        signal_icon = {"confirmed": "✅", "pending_verification": "⚠️", "counter_signal": "❌", "neutral": "—"}
        sustainability_label = {
            "high": "HIGH（高可持续性）",
            "medium-high": "MEDIUM-HIGH（中高可持续性）",
            "medium": "MEDIUM（中等可持续性）",
            "low": "LOW（低可持续性）",
        }
        action_label = {
            "chase": "CHASE（可追入）",
            "hold": "HOLD（持有观察）",
            "wait": "WAIT（等待确认）",
            "exit": "EXIT（建议减仓）",
            "verify_first": "VERIFY FIRST（先核实再操作）",
        }

        factor_rows = "\n".join(
            f"| {f.rank} | {f.factor_name} | {signal_icon.get(f.signal_strength, '—')} {f.signal_strength} | {f.data_source} | {f.sustainability} |"
            f"\n|   | *{f.note}* |   |   |   |" if f.note else
            f"| {f.rank} | {f.factor_name} | {signal_icon.get(f.signal_strength, '—')} {f.signal_strength} | {f.data_source} | {f.sustainability} |"
            for f in report.attribution_factors
        )

        etf_row = (
            f"| ETF 资金流(7d) | {report.etf_netflow_7d:+.0f}M USD | {report.etf_signal} |"
            if report.etf_signal != "na"
            else "| ETF 资金流(7d) | N/A | 仅适用于 BTC/ETH |"
        )

        unverifiable_list = "\n".join(f"- {f}" for f in report.unverifiable_factors)
        watchpoints_list = "\n".join(f"{i+1}. {p}" for i, p in enumerate(report.followup_watchpoints))

        return f"""## {report.symbol} 异动归因分析报告

分析时间窗口: {report.time_range}  |  价格变化: {report.price_change_pct:+.1f}%  |  异动方向: {direction_label}
分析时间: {report.analysis_time}

---

### 市场背景

- BTC 同期表现: 见 Step 1 原始数据
- 联动系数 (β): {report.market_beta} → {idio_label}

---

### 归因因素评估

| # | 归因因素 | 信号强度 | 数据来源 | 持续性 |
|---|---------|---------|---------|-------|
{factor_rows if factor_rows else "| — | 无显著归因因素 | — | — | — |"}

---

### 量化数据摘要

| 指标 | 数值 | 含义 |
|------|------|------|
| 鲸鱼行为 | {report.whale_action} | accumulate=增持 / distribute=出货 / neutral=无明显动作 |
| 交易所净流量(7d) | {report.exchange_netflow_7d:+.0f} | 负=净流出(偏多) / 正=净流入(偏空) |
| OI 变化 | {report.oi_change_pct:+.1f}% | 正值=持仓增加 |
| 资金费率 | {report.funding_rate_avg:+.4f}% | >0.05%=多头过热 / <-0.05%=空头超载 |
| Smart Money 方向 | {report.smart_money_direction} | inflow=流入(看涨) / outflow=流出(看跌) |
| RSI(14) | {report.rsi_14:.1f} | >75=超买 / <30=超卖 |
| MACD 信号 | {report.macd_signal} | bullish_cross=金叉 / bearish_cross=死叉 |
| 情绪评分 | {report.sentiment_score:.0f}/100 | 趋势: {report.sentiment_trend} |
{etf_row}

---

### 需人工核查的非量化因素

以下事项当前数据源不支持自动验证，建议人工确认后再做最终判断：

{unverifiable_list}

---

### 行情持续性评级: {sustainability_label.get(report.sustainability_rating, report.sustainability_rating)}

### 建议操作方向: {action_label.get(report.action_suggestion, report.action_suggestion)}

---

### 后续跟踪观察点

{watchpoints_list}

---

*免责声明：分析方法论归属 @Guolier8，基于历史链上和市场数据，不构成投资建议。最终操作决策需结合个人风险偏好自行判断。*
"""

    # ------------------------------------------------------------------
    # 输出序列化
    # ------------------------------------------------------------------

    def to_json(self, report: AttributionReport) -> str:
        """将报告序列化为 JSON 字符串（不含 Markdown 正文）"""
        d = asdict(report)
        d.pop("report_markdown", None)
        return json.dumps(d, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# CLI 入口（调试用）
# ---------------------------------------------------------------------------

def main() -> None:
    """
    本地调试入口。

    实际运行时，Claude Code Skill 会调用 MCP 工具并将结果传入
    AttributionReport.parse_stepN() 方法，此处使用模拟数据演示。
    """
    import sys

    symbol = sys.argv[1] if len(sys.argv) > 1 else "HYPE"
    attributor = TokenAnomalyAttributor(
        symbol=symbol,
        direction="pump",
        time_range="7d",
        threshold_pct=10.0,
    )

    # 模拟 MCP 返回数据
    s1 = attributor.parse_step1({
        "data": [
            {"symbol": symbol, "price_change_percentage_24h": 35.0},
            {"symbol": "BTC", "price_change_percentage_24h": 5.0},
        ]
    })
    s2 = attributor.parse_step2({
        "data": [
            {"direction": "out", "amount": 500},
            {"direction": "out", "amount": 300},
        ]
    })
    s3 = attributor.parse_step3(
        {"data": {"netflow_7d": -12400}},
        {"data": {"change_pct": -3.2}},
    )
    s4 = attributor.parse_step4(
        {"data": {"change_pct": 18.0}},
        {"data": [{"rate": 0.012}, {"rate": 0.015}, {"rate": 0.010}]},
    )
    s5 = attributor.parse_step5(
        {"data": {"net_usd": 2_500_000}},
        {"data": {}},
    )
    s6 = attributor.parse_step6(
        {"data": {"sentiment_score": 74, "sentiment_change_24h": 8}},
        {"data": {}},
    )
    s7 = attributor.parse_step7({"data": {}})  # HYPE 非 BTC/ETH，跳过
    s8 = attributor.parse_step8(
        {"data": {"rsi_14": 68}},
        {"data": {"histogram": 1.2, "histogram_trend": "rising"}},
    )

    report = attributor.synthesize(s1, s2, s3, s4, s5, s6, s7, s8)
    print(report.report_markdown)


if __name__ == "__main__":
    main()
