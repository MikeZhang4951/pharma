#!/usr/bin/env python3
"""Stock tracking website — fetches live data via yfinance and serves it."""
import http.server
import json
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import yfinance as yf

DIR = '/home/ubuntu/hermes-site'
PORT = 8081
TICKERS = [
    "CEG","INTC","PYPL","INSM","LAC","MP","ADBE","CCJ","ACM","NOK",
    "WMT","SNY","JEPI","COIN","GLW","ASTS","CRWV","ASML","RDW","MRVL",
    "LITE","PANW","UNH","OKLO","BA","DDOG","HIMS","RKLB","UUUU","BILI",
    "RKT","CFG","AAPL","AMZN","GOOGL","IBKR","META","MSFT","NVDA","QQQ",
    "SPY","TSLA","TSM","NVO","MU","AMD","REGN","MCD","BIDU","BABA",
    "ARM","COST","AVGO","PLTR","KO",
]

# Cached results
cache = {"data": None, "time": 0, "fetching": False}
CACHE_TTL = 60  # seconds


def fetch_all():
    results = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(_fetch_one, t): t for t in TICKERS}
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as e:
                results.append({"ticker": futures[fut], "error": str(e)})
    results.sort(key=lambda r: abs(r.get("change_pct") or 0), reverse=True)
    return results


def _fetch_one(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        price = info.get("regularMarketPrice") or info.get("currentPrice")
        prev = info.get("regularMarketPreviousClose") or info.get("previousClose")
        chg = info.get("regularMarketChangePercent")
        vol = info.get("regularMarketVolume")
        name = info.get("shortName") or info.get("longName") or ticker
        if chg is None and price and prev and prev != 0:
            chg = ((price - prev) / prev) * 100
        return {
            "ticker": ticker, "name": name,
            "price": round(price, 2) if price else None,
            "prev_close": round(prev, 2) if prev else None,
            "change_pct": round(chg, 2) if chg is not None else None,
            "volume": vol,
        }
    except:
        return {"ticker": ticker, "name": ticker, "price": None, "change_pct": None, "volume": None}


def refresh_cache():
    global cache
    if cache["fetching"]:
        return
    cache["fetching"] = True
    try:
        cache["data"] = fetch_all()
        cache["time"] = time.time()
    finally:
        cache["fetching"] = False


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_GET(self):
        if self.path == '/data':
            # Refresh if stale and not currently fetching
            if not cache["fetching"] and (cache["data"] is None or time.time() - cache["time"] > CACHE_TTL):
                threading.Thread(target=refresh_cache, daemon=True).start()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            resp = {
                "updated": time.strftime("%H:%M:%S UTC", time.gmtime(cache["time"])) if cache["time"] else "loading...",
                "tickers": cache["data"] or [],
                "stale": cache["data"] is None
            }
            self.wfile.write(json.dumps(resp).encode())
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            with open(os.path.join(DIR, 'stocks.html')) as f:
                self.wfile.write(f.read().encode())
        else:
            super().do_GET()


if __name__ == '__main__':
    # Initial fetch
    threading.Thread(target=refresh_cache, daemon=True).start()
    print(f"Stock tracker on http://0.0.0.0:{PORT}")
    http.server.HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
