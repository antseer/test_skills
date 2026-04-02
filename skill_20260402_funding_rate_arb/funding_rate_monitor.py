"""
Funding Rate Arbitrage Monitor

监控 Binance、OKX、Bybit 永续合约 funding rate，
检测异常（Z-score）并识别跨交易所套利机会。
"""

import json
import logging
import statistics
import time
from datetime import datetime, timezone
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SYMBOLS = {
    "BTC": {
        "binance": "BTCUSDT",
        "okx": "BTC-USDT-SWAP",
        "bybit": "BTCUSDT",
    },
    "ETH": {
        "binance": "ETHUSDT",
        "okx": "ETH-USDT-SWAP",
        "bybit": "ETHUSDT",
    },
}

Z_SCORE_THRESHOLD = 2.0
SPREAD_THRESHOLD = 0.0005  # 0.05%
HISTORY_DAYS = 30
# Funding rate settlement happens every 8 hours, so 30 days = 90 data points
HISTORY_LIMIT = HISTORY_DAYS * 3
REQUEST_TIMEOUT = 15  # seconds


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def _http_get(url: str) -> Any:
    """Issue a GET request and return parsed JSON."""
    req = Request(url, headers={"User-Agent": "FundingRateMonitor/1.0"})
    try:
        with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except (URLError, json.JSONDecodeError) as exc:
        logger.warning("Request failed for %s: %s", url, exc)
        return None


# ---------------------------------------------------------------------------
# Exchange adapters — current funding rate
# ---------------------------------------------------------------------------

def fetch_binance_funding_rate(symbol: str) -> float | None:
    """Fetch latest funding rate from Binance Futures."""
    url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=1"
    data = _http_get(url)
    if data and len(data) > 0:
        return float(data[0]["fundingRate"])
    return None


def fetch_okx_funding_rate(inst_id: str) -> float | None:
    """Fetch latest funding rate from OKX."""
    url = f"https://www.okx.com/api/v5/public/funding-rate?instId={inst_id}"
    data = _http_get(url)
    if data and data.get("data"):
        return float(data["data"][0]["fundingRate"])
    return None


def fetch_bybit_funding_rate(symbol: str) -> float | None:
    """Fetch latest funding rate from Bybit V5."""
    url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}"
    data = _http_get(url)
    if data and data.get("result", {}).get("list"):
        return float(data["result"]["list"][0]["fundingRate"])
    return None


# ---------------------------------------------------------------------------
# Exchange adapters — historical funding rate
# ---------------------------------------------------------------------------

def fetch_binance_funding_history(symbol: str, limit: int = HISTORY_LIMIT) -> list[float]:
    """Fetch historical funding rates from Binance."""
    url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit={limit}"
    data = _http_get(url)
    if data:
        return [float(item["fundingRate"]) for item in data]
    return []


def fetch_okx_funding_history(inst_id: str, limit: int = HISTORY_LIMIT) -> list[float]:
    """Fetch historical funding rates from OKX (returns up to 100 per page)."""
    rates: list[float] = []
    after = ""
    while len(rates) < limit:
        url = f"https://www.okx.com/api/v5/public/funding-rate-history?instId={inst_id}&limit=100"
        if after:
            url += f"&after={after}"
        data = _http_get(url)
        if not data or not data.get("data"):
            break
        page = data["data"]
        rates.extend(float(item["fundingRate"]) for item in page)
        if len(page) < 100:
            break
        after = page[-1].get("fundingTime", "")
        time.sleep(0.2)  # respect rate limits
    return rates[:limit]


def fetch_bybit_funding_history(symbol: str, limit: int = HISTORY_LIMIT) -> list[float]:
    """Fetch historical funding rates from Bybit V5."""
    url = f"https://api.bybit.com/v5/market/funding/history?category=linear&symbol={symbol}&limit={min(limit, 200)}"
    data = _http_get(url)
    if data and data.get("result", {}).get("list"):
        return [float(item["fundingRate"]) for item in data["result"]["list"]]
    return []


# ---------------------------------------------------------------------------
# Fetch dispatcher
# ---------------------------------------------------------------------------

CURRENT_FETCHERS = {
    "binance": fetch_binance_funding_rate,
    "okx": fetch_okx_funding_rate,
    "bybit": fetch_bybit_funding_rate,
}

HISTORY_FETCHERS = {
    "binance": fetch_binance_funding_history,
    "okx": fetch_okx_funding_history,
    "bybit": fetch_bybit_funding_history,
}


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def compute_z_score(current: float, history: list[float]) -> float | None:
    """Compute Z-score of current value against historical distribution.

    Returns None if insufficient history (< 21 data points, ~7 days).
    """
    if len(history) < 21:
        logger.info("Insufficient history (%d points), skipping Z-score", len(history))
        return None
    mean = statistics.mean(history)
    stdev = statistics.stdev(history)
    if stdev == 0:
        return 0.0
    return (current - mean) / stdev


def find_arbitrage_opportunities(
    rates: dict[str, float | None], asset: str
) -> list[dict[str, Any]]:
    """Compare all exchange pairs and flag spreads exceeding the threshold."""
    opportunities: list[dict[str, Any]] = []
    exchanges = [ex for ex, r in rates.items() if r is not None]
    for i, ex_a in enumerate(exchanges):
        for ex_b in exchanges[i + 1 :]:
            spread = abs(rates[ex_a] - rates[ex_b])  # type: ignore[operator]
            if spread > SPREAD_THRESHOLD:
                opportunities.append(
                    {
                        "type": "arb_opportunity",
                        "asset": asset,
                        "pair": f"{ex_a}-{ex_b}",
                        "spread": round(spread, 8),
                        "rate_a": rates[ex_a],
                        "rate_b": rates[ex_b],
                    }
                )
    return opportunities


# ---------------------------------------------------------------------------
# Main monitor
# ---------------------------------------------------------------------------

def run_monitor() -> dict[str, Any]:
    """Execute a full monitoring cycle and return the JSON result."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    all_rates: dict[str, float | None] = {}
    alerts: list[dict[str, Any]] = []

    for asset, symbol_map in SYMBOLS.items():
        asset_rates: dict[str, float | None] = {}

        for exchange, symbol in symbol_map.items():
            logger.info("Fetching %s %s funding rate from %s...", asset, symbol, exchange)

            # Current rate
            rate = CURRENT_FETCHERS[exchange](symbol)
            key = f"{exchange}_{asset.lower()}"
            all_rates[key] = rate
            asset_rates[exchange] = rate

            if rate is None:
                logger.warning("Could not fetch %s from %s", asset, exchange)
                continue

            # Historical rates for Z-score
            history = HISTORY_FETCHERS[exchange](symbol)
            z_score = compute_z_score(rate, history)

            if z_score is not None and abs(z_score) > Z_SCORE_THRESHOLD:
                alerts.append(
                    {
                        "type": "high_rate",
                        "exchange": exchange,
                        "asset": asset,
                        "funding_rate": round(rate, 8),
                        "z_score": round(z_score, 4),
                    }
                )
                logger.info(
                    "ALERT: %s %s Z-score = %.4f (rate = %.8f)",
                    exchange, asset, z_score, rate,
                )

            # Polite delay between exchange calls
            time.sleep(0.3)

        # Cross-exchange arbitrage
        arb_alerts = find_arbitrage_opportunities(asset_rates, asset)
        alerts.extend(arb_alerts)
        for arb in arb_alerts:
            logger.info(
                "ARB: %s %s spread = %.8f",
                arb["pair"], arb["asset"], arb["spread"],
            )

    result = {
        "timestamp": timestamp,
        "rates": {k: round(v, 8) if v is not None else None for k, v in all_rates.items()},
        "alerts": alerts,
    }
    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the monitor and print the JSON output."""
    result = run_monitor()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
