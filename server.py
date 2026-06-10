import http.server
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

try: import yfinance as yf
except ImportError: yf = None

DIR = '/home/ubuntu/hermes-site'
TICKERS = [
    "CEG","INTC","PYPL","INSM","LAC","MP","ADBE","CCJ","ACM","NOK",
    "WMT","SNY","JEPI","COIN","GLW","ASTS","CRWV","ASML","RDW","MRVL",
    "LITE","PANW","UNH","OKLO","BA","DDOG","HIMS","RKLB","UUUU","BILI",
    "RKT","CFG","AAPL","AMZN","GOOGL","IBKR","META","MSFT","NVDA","QQQ",
    "SPY","TSLA","TSM","NVO","MU","AMD","REGN","MCD","BIDU","BABA",
    "ARM","COST","AVGO","PLTR","KO",
]

stock_cache = {"data": None, "time": 0, "fetching": False}
CACHE_TTL = 60

def _fetch_one(t):
    try:
        info = yf.Ticker(t).info
        p = info.get("regularMarketPrice") or info.get("currentPrice")
        prev = info.get("regularMarketPreviousClose") or info.get("previousClose")
        chg = info.get("regularMarketChangePercent")
        if chg is None and p and prev and prev != 0: chg = ((p-prev)/prev)*100
        return {"ticker":t,"name":info.get("shortName") or info.get("longName") or t,"price":round(p,2) if p else None,"prev_close":round(prev,2) if prev else None,"change_pct":round(chg,2) if chg is not None else None,"volume":info.get("regularMarketVolume")}
    except: return {"ticker":t,"name":t,"price":None,"change_pct":None,"volume":None}

def fetch_all():
    r=[]
    with ThreadPoolExecutor(max_workers=20) as ex:
        f={ex.submit(_fetch_one,t):t for t in TICKERS}
        for fut in as_completed(f):
            try: r.append(fut.result())
            except: r.append({"ticker":f[fut],"error":"fail"})
    r.sort(key=lambda x:abs(x.get("change_pct") or 0),reverse=True)
    return r

def refresh_stocks():
    global stock_cache
    if stock_cache["fetching"]: return
    stock_cache["fetching"]=True
    try: stock_cache["data"]=fetch_all(); stock_cache["time"]=time.time()
    finally: stock_cache["fetching"]=False

def read_status():
    """Read status.json from disk every time — always fresh."""
    try:
        with open(os.path.join(DIR, 'status.json')) as f:
            return json.load(f)
    except:
        return {"hermes":{"status":"idle","task":""},"michael":{"status":"idle","task":""},"tasks":[]}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=DIR,**kw)
    def do_GET(self):
        if self.path=='/stocks/data':
            if not stock_cache["fetching"] and (stock_cache["data"] is None or time.time()-stock_cache["time"]>CACHE_TTL):
                threading.Thread(target=refresh_stocks,daemon=True).start()
            self._json({"updated":time.strftime("%H:%M:%S UTC",time.gmtime(stock_cache["time"])) if stock_cache["time"] else "loading...","tickers":stock_cache["data"] or [],"stale":stock_cache["data"] is None})
        elif self.path=='/status':
            self._json(read_status())
        else:
            super().do_GET()
    def do_POST(self):
        if self.path == '/api/chat':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            try:
                data = json.loads(body)
                text = data.get('text', '').strip()
            except:
                text = ''
            if not text:
                self._json({'error': 'No text provided'})
                return
            import subprocess
            try:
                proc = subprocess.run(
                    ['hermes', '-z', text, '--yolo', '-t', 'terminal,file,web,search,skills'],
                    capture_output=True, text=True, timeout=120, cwd=os.path.expanduser('~')
                )
                reply = proc.stdout.strip() or proc.stderr.strip() or 'No response.'
            except subprocess.TimeoutExpired:
                reply = 'Sorry, that took too long.'
            except Exception as e:
                reply = f'Error: {e}'
            self._json({'text': reply})
        else:
            self.send_response(404)
            self.end_headers()
    def _json(self,data):
        body=json.dumps(data).encode()
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__=='__main__':
    if yf: threading.Thread(target=refresh_stocks,daemon=True).start()
    http.server.HTTPServer(('0.0.0.0',8080),Handler).serve_forever()
