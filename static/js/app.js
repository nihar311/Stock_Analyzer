/* Signal Lab Pro — app.js (Minimal helper for AI analysis & Nifty pills) */
'use strict';

document.addEventListener('DOMContentLoaded', () => {
    loadAI();
    loadNiftyPills();
});

async function loadAI() {
    const box = document.getElementById('ai-box');
    if (!box) return;
    const sym = typeof CURRENT_SYMBOL !== 'undefined' ? CURRENT_SYMBOL : 'RELIANCE';

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
