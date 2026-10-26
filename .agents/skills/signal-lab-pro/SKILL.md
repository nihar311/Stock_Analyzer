---
name: signal-lab-pro
description: >-
  Full project memory for Signal Lab Pro — an Indian stock analysis dashboard
  built with Flask + TradingView widgets + Gemini AI. Use this skill whenever
  the user asks to continue work on this project in a new chat.
---

# Signal Lab Pro — Project Skill File

## Project Purpose
A stock analysis dashboard for Indian NSE stocks that shows:
- Interactive TradingView charts + Technical Analysis gauge
- Multi-Timeframe agreement panel (15m, 1H, 1D, 1W)
- Gemini AI "buy/hold/sell" decision summary
- Nifty 50 scanner

## Project Location
`e:\Stock Purchase & sell Analysis\`

## GitHub Repository
- URL: (update after first push)
- Branch: main

## Tech Stack
- **Backend**: Python 3, Flask
- **Frontend**: Plain HTML/CSS/JS (no React/Vue)
- **Charts**: TradingView Free Embed Widgets
- **AI**: Google Gemini API (`google-genai` SDK)
- **Data**: yfinance for price snapshots (AI summary only)

## Critical Architecture Decision — Candlestick Charting vs TradingView Embeds

> **KEY DISCOVERY**: TradingView's free embed chart (`embed-widget-advanced-chart.js`) **blocks all Indian stocks (NSE/BSE)** with the error:
> *"Notification: This symbol is only available on TradingView."* and forces an automatic fallback to Apple Inc (AAPL).
>
> **THE FIX**:
> 1. **Main Interactive Chart**: Built with TradingView's official, open-source **Lightweight Charts™** (`lightweight-charts.standalone.production.js`). The candle history is served directly by the Flask endpoint `/api/chart-data/<symbol>` via `yfinance` (`.NS` / `.BO`). It supports periods (1M, 3M, 6M, 1Y), hover OHLC legend, and responsive auto-resize.
> 2. **External Link**: An "Open in TradingView" button is provided to open `https://in.tradingview.com/chart/?symbol=NSE:<SYMBOL>` in a new tab if users want drawing tools.
> 3. **Other Widgets**: TradingView's **Technical Analysis Gauge**, **Timeline News**, **Company Profile**, and **Market Screener** DO work for Indian stocks and are rendered via Jinja2 server-side embedding.

## File Structure
```
e:\Stock Purchase & sell Analysis\
├── .agents\
│   └── skills\
│       └── signal-lab-pro\
│           └── SKILL.md          ← this file
├── .env                          ← GEMINI_API_KEY=...
├── app.py                        ← Flask server (minimal)
├── requirements.txt
├── watchlists\
│   ├── nifty50.json
│   ├── niftybank.json
│   └── high_momentum.json
├── templates\
│   └── index.html                ← Jinja2, symbols baked in
└── static\
    ├── css\
    │   └── style.css
    └── js\
        └── app.js                ← only handles AI fetch + scanner
```

## Key API Endpoints
| Route | Description |
|---|---|
| `GET /?symbol=RELIANCE` | Main dashboard (server-rendered) |
| `GET /api/ai-summary/<symbol>?timeframe=1D` | Gemini AI verdict JSON |
| `GET /api/scanner-stocks` | Returns nifty50.json stock list |

## .env Keys
```
GEMINI_API_KEY=<your-key>
```

## How to Run
```powershell
cd "e:\Stock Purchase & sell Analysis"
pip install flask yfinance google-genai python-dotenv
python app.py
# Open http://localhost:5000
```

## Known Issues / History
- TradingView embed widgets show Apple (AAPL) when symbol is injected via JS — **fixed** by server-side rendering
- `^NSEI` (Nifty index) returns 404 from yfinance — use `^NSEI` or skip index data
- Gemini API key in .env may be a Fyers key (not Gemini) — verify separately

## Nifty50 Watchlist Format (`watchlists/nifty50.json`)
```json
{
  "stocks": [
    { "symbol": "RELIANCE.NS", "name": "Reliance Industries" },
    ...
  ]
}
```
