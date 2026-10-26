/* Signal Lab Pro — app.js
   Full Integration: TradingView Lightweight Charts + Gemini AI + Watchlists
*/
'use strict';

let chartInstance = null;
let candleSeries = null;
let volumeSeries = null;
let lastCandle = null;
let currentChartPeriod = '1y';

document.addEventListener('DOMContentLoaded', () => {
    const sym = typeof CURRENT_SYMBOL !== 'undefined' ? CURRENT_SYMBOL : 'RELIANCE';

    // 1. Initialize Chart
    initChart(sym, currentChartPeriod);

    // 2. Setup Period Buttons
    setupPeriodButtons(sym);

    // 3. Load Gemini AI Analysis
    loadAI(sym);

    // 4. Load Nifty 50 Watchlist Pills
    loadNiftyPills();
});

/* ─── TradingView Lightweight Charts ────────────────────────────── */
function initChart(symbol, period) {
    const container = document.getElementById('lightweight-chart-container');
    if (!container) return;

    if (typeof LightweightCharts === 'undefined') {
        container.innerHTML = '<p style="color:var(--red);padding:20px;">Lightweight Charts library failed to load from CDN.</p>';
        return;
    }

    if (chartInstance) {
        chartInstance.remove();
        chartInstance = null;
    }

    chartInstance = LightweightCharts.createChart(container, {
        width: container.clientWidth || 700,
        height: 480,
        layout: {
            background: { type: 'solid', color: '#0a0b12' },
            textColor: '#7777aa',
            fontSize: 12,
            fontFamily: "'Inter', sans-serif",
        },
        grid: {
            vertLines: { color: 'rgba(255, 255, 255, 0.04)' },
            horzLines: { color: 'rgba(255, 255, 255, 0.04)' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
            vertLine: { color: 'rgba(0, 200, 255, 0.4)', width: 1, style: 2 },
            horzLine: { color: 'rgba(0, 200, 255, 0.4)', width: 1, style: 2 },
        },
        rightPriceScale: {
            borderColor: 'rgba(255, 255, 255, 0.08)',
            scaleMargins: { top: 0.1, bottom: 0.25 },
        },
        timeScale: {
            borderColor: 'rgba(255, 255, 255, 0.08)',
            timeVisible: true,
            secondsVisible: false,
        },
    });

    // Candlesticks (Zerodha / TradingView colorway)
    candleSeries = chartInstance.addCandlestickSeries({
        upColor: '#00e676',
        downColor: '#ff4560',
        borderUpColor: '#00e676',
        borderDownColor: '#ff4560',
        wickUpColor: '#00e676',
        wickDownColor: '#ff4560',
    });

    // Volume histogram overlay
    volumeSeries = chartInstance.addHistogramSeries({
        priceFormat: { type: 'volume' },
        priceScaleId: '',
        scaleMargins: { top: 0.8, bottom: 0 },
    });

    // Responsive auto-resize
    const resizeObserver = new ResizeObserver(entries => {
        if (!entries || !entries.length) return;
        const { width, height } = entries[0].contentRect;
        if (chartInstance && width > 0 && height > 0) {
            chartInstance.applyOptions({ width, height });
        }
    });
    resizeObserver.observe(container);

    // Crosshair hover legend
    chartInstance.subscribeCrosshairMove(param => {
        if (!param || !param.time || !param.seriesData) {
            updateLegend(lastCandle);
            return;
        }
        const bar = param.seriesData.get(candleSeries);
        const vol = param.seriesData.get(volumeSeries);
        if (bar) {
            updateLegend({
                open: bar.open,
                high: bar.high,
                low: bar.low,
                close: bar.close,
                volume: vol ? vol.value : null,
            });
        }
    });

    // Fetch and load data
    loadChartData(symbol, period);
}

async function loadChartData(symbol, period) {
    const loadingOverlay = document.getElementById('chart-loading');
    if (loadingOverlay) loadingOverlay.style.display = 'flex';

    try {
        const res = await fetch(`/api/chart-data/${encodeURIComponent(symbol)}?period=${period}`);
        const data = await res.json();

        if (data.error) {
            const container = document.getElementById('lightweight-chart-container');
            container.innerHTML = `<p style="color:var(--red);padding:20px;">${data.error}</p>`;
            return;
        }

        if (data.candles && data.candles.length > 0) {
            candleSeries.setData(data.candles);
            if (data.volume && data.volume.length > 0) {
                volumeSeries.setData(data.volume);
            }

            // Fit content
            chartInstance.timeScale().fitContent();

            // Set last candle in legend
            const last = data.candles[data.candles.length - 1];
            const lastVol = data.volume && data.volume.length ? data.volume[data.volume.length - 1].value : null;
            lastCandle = { ...last, volume: lastVol };
            updateLegend(lastCandle);
        }
    } catch (err) {
        console.error('Failed to load chart data:', err);
    } finally {
        if (loadingOverlay) loadingOverlay.style.display = 'none';
    }
}

function updateLegend(bar) {
    if (!bar) return;
    const fmt = n => typeof n === 'number' ? n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—';
    const fmtVol = v => {
        if (!v) return '—';
        if (v >= 1e7) return (v / 1e7).toFixed(2) + ' Cr';
        if (v >= 1e5) return (v / 1e5).toFixed(2) + ' L';
        if (v >= 1e3) return (v / 1e3).toFixed(1) + ' k';
        return v.toString();
    };

    const elO = document.getElementById('leg-open');
    const elH = document.getElementById('leg-high');
    const elL = document.getElementById('leg-low');
    const elC = document.getElementById('leg-close');
    const elV = document.getElementById('leg-vol');

    if (elO) elO.textContent = '₹' + fmt(bar.open);
    if (elH) elH.textContent = '₹' + fmt(bar.high);
    if (elL) elL.textContent = '₹' + fmt(bar.low);
    if (elC) {
        elC.textContent = '₹' + fmt(bar.close);
        elC.style.color = (bar.close >= bar.open) ? 'var(--green)' : 'var(--red)';
    }
    if (elV) elV.textContent = fmtVol(bar.volume);
}

function setupPeriodButtons(symbol) {
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentChartPeriod = btn.dataset.period;
            loadChartData(symbol, currentChartPeriod);
        });
    });
}

/* ─── Gemini AI Decision ────────────────────────────────────────── */
async function loadAI(symbol) {
    const sym = symbol || (typeof CURRENT_SYMBOL !== 'undefined' ? CURRENT_SYMBOL : 'RELIANCE');
    const box = document.getElementById('ai-box');
    if (!box) return;

    box.className = 'ai-loading';
    box.innerHTML = `<div class="spinner"></div> Analysing <strong>${sym}</strong> with Gemini AI…`;

    try {
        const res = await fetch(`/api/ai-summary/${encodeURIComponent(sym)}?timeframe=1D`);
        const data = await res.json();

        if (data.error) {
            box.className = 'ai-result fade';
            box.innerHTML = `<p style="color:var(--red)">${data.error}</p>`;
            return;
        }

        const snap = data.snapshot || {};
        const text = data.summary || 'No summary returned.';
        const provider = data.provider || 'AI';

        // Update provider badge in card header
        const badgeEl = document.getElementById('ai-provider-badge');
        if (badgeEl) {
            badgeEl.textContent = provider;
            if (data.fallback_triggered) {
                badgeEl.style.background = 'linear-gradient(135deg, #ff9100, #ff3d00)';
            } else {
                badgeEl.style.background = 'linear-gradient(135deg, #a000ff, #5500cc)';
            }
        }

        // Detect verdict
        const match = text.match(/\b(STRONG BUY|BUY|HOLD|WAIT|SELL|STRONG SELL|AVOID)\b/i);
        const verdict = match ? match[1].toUpperCase() : 'HOLD';
        const vClass = verdict.includes('BUY') ? 'buy'
                     : (verdict.includes('SELL') || verdict === 'AVOID') ? 'sell'
                     : verdict === 'WAIT' ? 'wait' : 'hold';

        box.className = 'ai-result fade';
        box.innerHTML = `
            <div class="verdict ${vClass}">${verdict}</div>
            <div style="flex:1">
                <p class="ai-text">${text.replace(/\n/g, '<br>')}</p>
                ${snap.price ? `
                <div class="snap">
                    <div class="snap-item"><span class="snap-l">Price</span><span class="snap-v">₹${snap.price.toLocaleString('en-IN')}</span></div>
                    <div class="snap-item"><span class="snap-l">Today</span><span class="snap-v" style="color:${snap.change_pct >= 0 ? 'var(--green)' : 'var(--red)'}">${snap.change_pct >= 0 ? '+' : ''}${snap.change_pct}%</span></div>
                    <div class="snap-item"><span class="snap-l">Volume</span><span class="snap-v">${snap.vol_ratio}x avg</span></div>
                    <div class="snap-item"><span class="snap-l">5D High</span><span class="snap-v">₹${snap.week_high ? snap.week_high.toLocaleString('en-IN') : '—'}</span></div>
                    <div class="snap-item"><span class="snap-l">5D Low</span><span class="snap-v">₹${snap.week_low ? snap.week_low.toLocaleString('en-IN') : '—'}</span></div>
                </div>` : ''}
            </div>
        `;
    } catch (err) {
        box.className = 'ai-result fade';
        box.innerHTML = `<p style="color:var(--red)">Failed to fetch AI summary: ${err.message}</p>`;
    }
}

/* ─── Nifty 50 Watchlist Pills ──────────────────────────────────── */
async function loadNiftyPills() {
    const wrap = document.getElementById('pills');
    if (!wrap) return;

    try {
        const res = await fetch('/api/scanner-stocks');
        const stocks = await res.json();
        if (!stocks || !Array.isArray(stocks)) {
            wrap.innerHTML = `<span style="color:var(--t2)">Unable to load Nifty 50 stocks</span>`;
            return;
        }

        wrap.innerHTML = stocks.map(s => {
            const sym = (s.symbol || '').replace(/\.(NS|BO)$/i, '').toUpperCase();
            return `<a href="/?symbol=${encodeURIComponent(sym)}" class="pill">${sym}</a>`;
        }).join('');
    } catch (err) {
        wrap.innerHTML = `<span style="color:var(--t2)">Error: ${err.message}</span>`;
    }
}
