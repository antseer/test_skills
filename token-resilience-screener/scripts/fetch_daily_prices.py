#!/usr/bin/env python3
"""
fetch_daily_prices.py — 从 CoinGecko Public API 拉取代币历史日线收盘价

用法:
    python3 fetch_daily_prices.py --ids tao,kaito,hype,ethereum --start 2026-03-21 --end 2026-03-27

输出:
    JSON 格式的每日收盘价矩阵，写入 stdout 或 --output 指定文件

依赖:
    requests（pip install requests 或 uv pip install requests）

注意:
    CoinGecko 免费版速率限制约 30 req/min。超过10个代币时建议设置 --delay 2（秒）。
"""

import argparse
import json
import time
import datetime
from typing import Optional

try:
    import requests
except ImportError:
    raise SystemExit("请先安装 requests: uv pip install requests")


COINGECKO_BASE = "https://api.coingecko.com/api/v3"


def date_to_unix(date_str: str, end_of_day: bool = False) -> int:
    """将 YYYY-MM-DD 字符串转换为 Unix 时间戳（UTC）"""
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59)
    return int(dt.timestamp())


def fetch_market_chart(
    coin_id: str,
    start_date: str,
    end_date: str,
    vs_currency: str = "usd",
    api_key: Optional[str] = None,
) -> list[dict]:
    """
    调用 /coins/{id}/market_chart/range，提取每日收盘价序列。

    返回格式:
        [{"date": "2026-03-21", "close": 123.45}, ...]
    """
    url = f"{COINGECKO_BASE}/coins/{coin_id}/market_chart/range"
    params = {
        "vs_currency": vs_currency,
        "from": date_to_unix(start_date),
        "to": date_to_unix(end_date, end_of_day=True),
        "interval": "daily",
    }
    headers = {}
    if api_key:
        headers["x-cg-demo-api-key"] = api_key

    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    prices_raw = data.get("prices", [])
    daily_prices = []
    for ts_ms, price in prices_raw:
        date_str = datetime.datetime.utcfromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d")
        daily_prices.append({"date": date_str, "close": round(price, 6)})

    # 去重（同一天可能有多个数据点），保留最后一个（收盘价）
    by_date: dict[str, float] = {}
    for entry in daily_prices:
        by_date[entry["date"]] = entry["close"]

    return [{"date": d, "close": p} for d, p in sorted(by_date.items())]


def calc_daily_returns(prices: list[dict]) -> list[dict]:
    """
    根据收盘价序列计算日涨跌幅（%）。

    返回格式:
        [{"date": "2026-03-22", "return_pct": -1.23}, ...]
    """
    returns = []
    for i in range(1, len(prices)):
        prev = prices[i - 1]["close"]
        curr = prices[i]["close"]
        if prev == 0:
            pct = 0.0
        else:
            pct = round((curr - prev) / prev * 100, 4)
        returns.append({"date": prices[i]["date"], "return_pct": pct})
    return returns


def main():
    parser = argparse.ArgumentParser(description="Fetch CoinGecko daily price history")
    parser.add_argument("--ids", required=True, help="逗号分隔的 CoinGecko ID 列表，如 tao,kaito,ethereum")
    parser.add_argument("--start", required=True, help="起始日期 YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="结束日期 YYYY-MM-DD")
    parser.add_argument("--currency", default="usd", help="计价货币（默认 usd）")
    parser.add_argument("--api-key", default=None, help="CoinGecko API Key（可选，提升速率限制）")
    parser.add_argument("--delay", type=float, default=1.0, help="每次请求间隔秒数（默认 1.0）")
    parser.add_argument("--output", default=None, help="输出文件路径（默认输出到 stdout）")
    args = parser.parse_args()

    coin_ids = [c.strip() for c in args.ids.split(",") if c.strip()]
    result = {}

    for i, coin_id in enumerate(coin_ids):
        print(f"[{i+1}/{len(coin_ids)}] 拉取 {coin_id} 数据...", flush=True)
        try:
            prices = fetch_market_chart(coin_id, args.start, args.end, args.currency, args.api_key)
            daily_returns = calc_daily_returns(prices)
            avg_return = round(sum(r["return_pct"] for r in daily_returns) / len(daily_returns), 4) if daily_returns else None
            result[coin_id] = {
                "prices": prices,
                "daily_returns": daily_returns,
                "avg_daily_return_pct": avg_return,
            }
        except requests.HTTPError as e:
            print(f"  警告: {coin_id} 请求失败 — {e}", flush=True)
            result[coin_id] = {"error": str(e)}

        if i < len(coin_ids) - 1:
            time.sleep(args.delay)

    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"\n结果已写入: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
