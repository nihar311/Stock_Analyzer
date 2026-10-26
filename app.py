"""
Signal Lab Pro — Flask backend
================================
Run:  python app.py
Open: http://localhost:5000/?symbol=RELIANCE
"""

import os, re, json, traceback
from flask import Flask, render_template, jsonify, request
from modules.ai_engine import get_ai_conclusion

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


def clean(raw: str) -> str:
    """Strip exchange prefix / suffix → plain NSE symbol e.g. RELIANCE"""
    s = raw.strip().upper()
    s = re.sub(r"^(NSE:|BSE:|NSEINDIA:)", "", s)
    s = re.sub(r"\.(NS|BO)$", "", s)
    return s or "RELIANCE"


# ── Pages ────────────────────────────────────────────────
@app.route("/")
def index():
    symbol    = clean(request.args.get("symbol", "RELIANCE"))
    tv_symbol = f"NSE:{symbol}"
    return render_template("index.html", symbol=symbol, tv_symbol=tv_symbol)


# ── Chart Data for Lightweight Charts (NSE / BSE real candles) ───
@app.route("/api/chart-data/<symbol>")
def chart_data(symbol: str):
    try:
        import yfinance as yf
        sym = clean(symbol)
        period = request.args.get("period", "1y")
        interval = request.args.get("interval", "1d")

        # Try NSE first, fallback to BSE
        hist = yf.Ticker(f"{sym}.NS").history(period=period, interval=interval)
        if hist is None or hist.empty:
            hist = yf.Ticker(f"{sym}.BO").history(period=period, interval=interval)

        if hist is None or hist.empty:
            return jsonify({"error": f"No candlestick history found for {sym}"}), 404

        candles = []
        volume = []
        for idx, row in hist.iterrows():
            t_str = idx.strftime("%Y-%m-%d")
            o = round(float(row["Open"]), 2)
            h = round(float(row["High"]), 2)
            l = round(float(row["Low"]), 2)
            c = round(float(row["Close"]), 2)
            v = int(row["Volume"])

            candles.append({
                "time": t_str,
                "open": o,
                "high": h,
                "low": l,
                "close": c
            })

            vol_color = "rgba(0, 230, 118, 0.45)" if c >= o else "rgba(255, 69, 96, 0.45)"
            volume.append({
                "time": t_str,
                "value": v,
                "color": vol_color
            })

        return jsonify({
            "symbol": sym,
            "period": period,
            "candles": candles,
            "volume": volume
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── AI Summary ───────────────────────────────────────────
def get_snapshot(symbol: str) -> dict:
    try:
        import yfinance as yf
        hist = yf.Ticker(f"{symbol}.NS").history(period="5d", interval="1d")
        if hist is None or hist.empty:
            hist = yf.Ticker(f"{symbol}.BO").history(period="5d", interval="1d")
        if hist is None or hist.empty:
            return {}
        c, p = float(hist["Close"].iloc[-1]), float(hist["Close"].iloc[-2]) if len(hist) > 1 else float(hist["Close"].iloc[-1])
        v, av = int(hist["Volume"].iloc[-1]), int(hist["Volume"].mean())
        return {
            "price":      round(c, 2),
            "change_pct": round((c - p) / p * 100, 2) if p else 0,
            "vol_ratio":  round(v / av, 2) if av else 1,
            "week_high":  round(float(hist["High"].max()), 2),
            "week_low":   round(float(hist["Low"].min()), 2),
        }
    except Exception as e:
        print(f"[snapshot] {e}")
        return {}


@app.route("/api/ai-summary/<symbol>")
def ai_summary(symbol: str):
    try:
        sym  = clean(symbol)
        tf   = request.args.get("timeframe", "1D")
        snap = get_snapshot(sym)
        pl   = (f"Price ₹{snap['price']} ({snap['change_pct']:+.2f}% today, "
                f"volume {snap['vol_ratio']}x avg)") if snap else "Price unavailable."

        res = get_ai_conclusion(sym, pl, tf)
        return jsonify({
            "summary": res.get("summary", ""),
            "provider": res.get("provider", "Gemini"),
            "model": res.get("model", ""),
            "fallback_triggered": res.get("fallback_triggered", False),
            "snapshot": snap
        })
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Server error"}), 500


@app.route("/api/scanner-stocks")
def scanner_stocks():
    try:
        p = os.path.join(os.path.dirname(__file__), "watchlists", "nifty50.json")
        with open(p, encoding="utf-8") as f:
            return jsonify(json.load(f).get("stocks", []))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  Signal Lab Pro  ->  http://localhost:5000")
    print("="*55 + "\n")
    app.run(debug=True, port=5000)
