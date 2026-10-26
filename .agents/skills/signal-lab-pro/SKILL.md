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

## Critical Architecture Decision — TradingView Widgets

> **The ONLY reliable way to load TradingView widgets with a dynamic symbol is
> server-side rendering via Flask/Jinja2.**

### Why dynamic JS injection fails
TradingView embed widgets (`embed-widget-*.js`) read their config JSON via
`document.currentScript.textContent`. When a `<script src="...">` tag is
created dynamically via `document.createElement('script')`, the browser sets
`document.currentScript = null` during execution in most environments.
This causes TradingView to fall back to its default symbol (Apple / AAPL).

### The working pattern (ALWAYS use this)
```
User types stock → form GET /?symbol=RELIANCE → Flask renders index.html
with {{ tv_symbol }} = "NSE:RELIANCE" baked into every widget's static
<script> tag → TradingView reads it perfectly.
```

Never try to:
- `document.createElement('script')` for TradingView widgets
- `iframe.srcdoc` with TradingView scripts
- `new TradingView.widget()` from tv.js for Indian stocks
- Set `script.innerHTML` or `script.text` after DOM creation

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
