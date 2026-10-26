"""
Signal Lab Pro — Flask backend
================================
Run:  python app.py
Open: http://localhost:5000/?symbol=RELIANCE
"""

import os, re, json, traceback
from flask import Flask, render_template, jsonify, request

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


# ── AI Summary ───────────────────────────────────────────
def get_snapshot(symbol: str) -> dict:
    try:
        import yfinance as yf
        hist = yf.Ticker(f"{symbol}.NS").history(period="5d", interval="1d")
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


def gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return "Add GEMINI_API_KEY to your .env file to enable AI analysis."
    try:
        from google import genai
        r = genai.Client(api_key=GEMINI_API_KEY).models.generate_content(
            model="gemini-2.0-flash", contents=prompt)
        return r.text.strip()
    except Exception as e:
        return f"AI temporarily unavailable: {e}"


@app.route("/api/ai-summary/<symbol>")
def ai_summary(symbol: str):
    try:
        sym  = clean(symbol)
        tf   = request.args.get("timeframe", "1D")
        snap = get_snapshot(sym)
        pl   = (f"Price ₹{snap['price']} ({snap['change_pct']:+.2f}% today, "
                f"volume {snap['vol_ratio']}x avg)") if snap else "Price unavailable."

        text = gemini(f"""You are a professional Indian stock market analyst.
Stock: {sym} | Timeframe: {tf}
{pl}

In exactly 4 sentences:
1. Current technical picture
2. Key support / resistance level to watch
3. Main risk right now
4. Final verdict — BUY, HOLD, WAIT, or SELL

Be direct. No disclaimers. End with the verdict word in capitals.""")

        return jsonify({"summary": text, "snapshot": snap})
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
