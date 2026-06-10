#!/usr/bin/env python3
"""Portfolio tracker — live P&L from positions.json + yfinance. Port 8093."""

import http.server
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    yf = None

PORT = 8093
THIS_DIR = Path(__file__).parent
POSITIONS_FILE = THIS_DIR / "positions.json"
CACHE_TTL = 30

_cache = {"data": None, "ts": 0}


def load_positions() -> list[dict]:
    """Load positions from JSON file."""
    if not POSITIONS_FILE.exists():
        return []
    with open(POSITIONS_FILE) as f:
        return json.load(f)


def fetch_one(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info
        price = info.get("regularMarketPrice") or info.get("currentPrice")
        prev = info.get("regularMarketPreviousClose") or info.get("previousClose")
        chg = info.get("regularMarketChangePercent")
        if chg is None and price and prev and prev != 0:
            chg = ((price - prev) / prev) * 100
        name = info.get("shortName") or info.get("longName") or ticker
        return {"ticker": ticker, "name": name, "price": price, "change_pct": chg}
    except Exception:
        return {"ticker": ticker, "name": ticker, "price": None, "change_pct": None}


def get_portfolio() -> dict:
    """Fetch live prices and compute P&L for all positions."""
    now = time.time()
    if _cache["data"] is not None and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["data"]

    positions = load_positions()
    if not positions:
        return {"error": "No positions configured", "positions": [], "totals": {}}

    tickers = list(set(p["ticker"] for p in positions))
    prices = {}
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(fetch_one, t): t for t in tickers}
        for fut in as_completed(futures):
            result = fut.result()
            prices[result["ticker"]] = result

    holdings = []
    total_cost = 0.0
    total_value = 0.0
    total_day_change = 0.0

    for pos in positions:
        t = pos["ticker"]
        ticker_data = prices.get(t, {})
        price = ticker_data.get("price")
        change_pct = ticker_data.get("change_pct")
        shares = pos["shares"]
        cost_basis = pos["cost_basis"]

        cost_total = shares * cost_basis
        value = shares * price if price else 0
        pnl = value - cost_total if price else 0
        pnl_pct = ((price - cost_basis) / cost_basis * 100) if price and cost_basis else 0
        day_pnl = (value * change_pct / 100) if value and change_pct else 0

        total_cost += cost_total
        total_value += value
        total_day_change += day_pnl

        holdings.append({
            "ticker": t,
            "name": ticker_data.get("name", t),
            "shares": shares,
            "cost_basis": cost_basis,
            "price": round(price, 2) if price else None,
            "change_pct": round(change_pct, 2) if change_pct is not None else None,
            "value": round(value, 2),
            "cost_total": round(cost_total, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "day_pnl": round(day_pnl, 2),
        })

    holdings.sort(key=lambda h: abs(h.get("pnl") or 0), reverse=True)
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost else 0

    result = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "holdings": holdings,
        "totals": {
            "cost_basis": round(total_cost, 2),
            "value": round(total_value, 2),
            "pnl": round(total_pnl, 2),
            "pnl_pct": round(total_pnl_pct, 2),
            "day_change": round(total_day_change, 2),
        },
    }
    _cache["data"] = result
    _cache["ts"] = now
    return result


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == "/":
            self._serve_file("portfolio.html", "text/html")
        elif self.path == "/api/portfolio":
            self._json(get_portfolio())
        elif self.path == "/health":
            self._json({"status": "ok"})
        else:
            self.send_error(404)

    def _json(self, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, filename, ctype):
        path = THIS_DIR / filename
        try:
            content = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", f"{ctype}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(500, f"{filename} missing")


if __name__ == "__main__":
    print(f"Portfolio tracker on 0.0.0.0:{PORT}")
    httpd = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
