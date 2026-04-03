/**
 * TradingCore Dashboard — App Controller
 * Handles API calls, polling, UI updates, modals
 */

// ============================================
// TOAST NOTIFICATION SYSTEM
// ============================================
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { success: '✓', error: '✗', info: 'ℹ' };
    toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span> ${message}`;
    container.appendChild(toast);
    setTimeout(() => { if (toast.parentNode) toast.remove(); }, 4000);
}

// ============================================
// API HELPERS
// ============================================
async function apiFetch(url, options = {}) {
    try {
        const res = await fetch(url, options);
        if (res.status === 401) {
            window.location.href = '/login';
            return null;
        }
        return await res.json();
    } catch (e) {
        console.error(`API Error [${url}]:`, e);
        return null;
    }
}

async function apiPost(url, body = {}) {
    return apiFetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
}

// ============================================
// FEAR & GREED GAUGE
// ============================================
function updateFearGreedGauge(value) {
    const gaugeEl = document.getElementById('fg-gauge-fill');
    const valueEl = document.getElementById('fg-value');
    const labelEl = document.getElementById('fg-label');
    if (!gaugeEl || !valueEl) return;

    // SVG arc params (half-circle gauge)
    const arcLength = 188.5; // circumference of half-circle r=60
    const offset = arcLength - (value / 100) * arcLength;
    gaugeEl.style.strokeDashoffset = offset;

    // Color based on value
    let color, label, cssClass;
    if (value < 25) {
        color = '#ff4757'; label = 'Extreme Fear'; cssClass = 'fg-extreme-fear';
    } else if (value < 45) {
        color = '#ff8c42'; label = 'Fear'; cssClass = 'fg-fear';
    } else if (value < 55) {
        color = '#ffd700'; label = 'Neutral'; cssClass = 'fg-neutral';
    } else if (value < 75) {
        color = '#7bed9f'; label = 'Greed'; cssClass = 'fg-greed';
    } else {
        color = '#00ff9d'; label = 'Extreme Greed'; cssClass = 'fg-extreme-greed';
    }

    gaugeEl.style.stroke = color;
    valueEl.textContent = value;
    valueEl.className = `fg-value ${cssClass}`;
    if (labelEl) labelEl.textContent = label;
}

// ============================================
// MARKET PULSE
// ============================================
async function refreshMarket() {
    const data = await apiFetch('/api/market/pulse');
    if (!data) return;

    updateFearGreedGauge(data.fear_greed || 50);

    const btcDom = document.getElementById('btc-dom');
    const btcTrend = document.getElementById('btc-trend');
    const trendingEl = document.getElementById('trending');

    if (btcDom) btcDom.textContent = (data.btc_dominance || '--') + '%';

    if (btcTrend) {
        const isBullish = data.btc_trend === 'bullish';
        btcTrend.textContent = isBullish ? '↑ Bullish' : '↓ Bearish';
        btcTrend.className = `stat-value ${isBullish ? 'bullish' : 'bearish'}`;
    }

    if (trendingEl && data.trending) {
        trendingEl.innerHTML = data.trending.slice(0, 5).map(coin =>
            `<span class="trending-coin">${coin}</span>`
        ).join('');
    }

    // Fetch global market data for Market Cap and 24h change
    const globalData = await apiFetch('/api/market/global');
    if (globalData) {
        const mcapEl = document.getElementById('total-mcap');
        const changeEl = document.getElementById('mcap-change');
        if (mcapEl) mcapEl.textContent = formatMarketCap(globalData.total_market_cap);
        if (changeEl) {
            const change = globalData.market_cap_change_24h;
            if (change !== undefined && change !== null) {
                const sign = change >= 0 ? '+' : '';
                changeEl.textContent = sign + change.toFixed(2) + '%';
                changeEl.className = `stat-value ${change >= 0 ? 'bullish' : 'bearish'}`;
            }
        }
    }
}

// ============================================
// LIVE SIGNALS
// ============================================
function formatPrice(price) {
    if (price >= 1000) return '$' + price.toLocaleString('en-US', { maximumFractionDigits: 0 });
    if (price >= 1) return '$' + price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return '$' + price.toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
}

function formatMarketCap(value) {
    if (!value || value === 0) return '--';
    if (value >= 1e12) return '$' + (value / 1e12).toFixed(2) + 'T';
    if (value >= 1e9) return '$' + (value / 1e9).toFixed(2) + 'B';
    if (value >= 1e6) return '$' + (value / 1e6).toFixed(2) + 'M';
    return '$' + value.toLocaleString('en-US', { maximumFractionDigits: 0 });
}

function renderSignalCards(signals, isExample = false, message = '') {
    const container = document.getElementById('signals-container');
    if (!container) return;

    if (!signals || signals.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📡</div>
                <div class="empty-state-text">${isExample ? 'Example Signals' : 'No signals found'}</div>
                <div class="empty-state-sub">${message || (isExample ? 'Start the bot to see real signals' : 'RSI is neutral. Check back later.')}</div>
            </div>`;
        return;
    }

    let header = '';
    if (isExample) {
        header = `<div class="signals-header">
            <span class="example-badge">📋 EXAMPLE</span>
            <span class="signals-info">Start the bot for real signals</span>
        </div>`;
    }

    container.innerHTML = header + '<div class="signals-list">' + signals.map(s => `
        <div class="signal-card ${s.side.toLowerCase()}${s.is_example ? ' example' : ''}" data-id="${s.id || ''}">
            ${s.is_example ? '<div class="signal-example-badge">EXAMPLE</div>' : ''}
            <div class="signal-header">
                <span class="signal-symbol">${s.symbol}</span>
                <span class="signal-side ${s.side.toLowerCase()}">${s.side}</span>
            </div>
            <div class="signal-details">
                <div class="signal-detail">
                    <span class="detail-label">RSI</span>
                    <span class="detail-value">${s.rsi}</span>
                </div>
                <div class="signal-detail">
                    <span class="detail-label">Confidence</span>
                    <span class="detail-value">${s.confidence}%</span>
                </div>
                <div class="signal-detail">
                    <span class="detail-label">Entry</span>
                    <span class="detail-value">${formatPrice(s.entry)}</span>
                </div>
                <div class="signal-detail">
                    <span class="detail-label">SL</span>
                    <span class="detail-value" style="color:var(--accent-red)">-${s.sl}%</span>
                </div>
                <div class="signal-detail">
                    <span class="detail-label">TP</span>
                    <span class="detail-value" style="color:var(--accent-green)">+${s.tp}%</span>
                </div>
                <div class="signal-detail">
                    <span class="detail-label">R:R</span>
                    <span class="detail-value">1:${s.rr}</span>
                </div>
            </div>
        </div>
    `).join('') + '</div>';
}

async function refreshSignals() {
    const data = await apiFetch('/api/signals');
    if (!data) return;
    renderSignalCards(data.signals || [], data.is_example || false, data.message || '');
}

// ============================================
// PERFORMANCE
// ============================================
async function refreshPerformance() {
    const data = await apiFetch('/api/performance');
    if (!data) return;

    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };

    set('total-trades', data.total_trades || 0);
    set('win-count', data.wins || 0);
    set('loss-count', data.losses || 0);
    set('win-rate', (data.win_rate || 0) + '%');

    const bestEl = document.getElementById('best-trade');
    const worstEl = document.getElementById('worst-trade');

    if (bestEl) {
        if (data.best_trade) {
            bestEl.textContent = '+' + data.best_trade.pnl + '%';
            bestEl.className = 'perf-value positive';
            bestEl.title = data.best_trade.symbol;
        } else {
            bestEl.textContent = '--';
            bestEl.className = 'perf-value';
        }
    }
    if (worstEl) {
        if (data.worst_trade) {
            worstEl.textContent = data.worst_trade.pnl + '%';
            worstEl.className = 'perf-value negative';
            worstEl.title = data.worst_trade.symbol;
        } else {
            worstEl.textContent = '--';
            worstEl.className = 'perf-value';
        }
    }
}

// ============================================
// BOT STATUS
// ============================================
let botRunning = false;

function setBotUI(running) {
    botRunning = running;
    const dot = document.getElementById('status-dot');
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');

    if (dot) dot.classList.toggle('active', running);
    if (startBtn) startBtn.style.display = running ? 'none' : 'inline-flex';
    if (stopBtn) stopBtn.style.display = running ? 'inline-flex' : 'none';
}

async function refreshBotStatus() {
    const data = await apiFetch('/api/bot/status');
    if (!data) return;
    setBotUI(data.status === 'running');
}

// Start bot
async function startBot() {
    setBotUI(true);
    showToast('Starting bot...', 'info');
    const data = await apiPost('/api/bot/start');
    if (data && data.success) {
        showToast(`Bot started — ${data.config.mode} / ${data.config.interval}`, 'success');
    } else {
        setBotUI(false);
        showToast(data?.error || 'Failed to start bot', 'error');
    }
}

// Stop bot
async function stopBot() {
    setBotUI(false);
    showToast('Stopping bot...', 'info');
    const data = await apiPost('/api/bot/stop');
    if (data && data.success) {
        showToast(`Bot stopped — Session: ${data.session_stats.duration}`, 'success');
    } else {
        setBotUI(true);
        showToast(data?.error || 'Failed to stop bot', 'error');
    }
}

// ============================================
// CONFIG SYNC
// ============================================
async function loadConfig() {
    const data = await apiFetch('/api/config');
    if (!data) return;

    const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val; };
    setVal('mode-select', data.mode);
    setVal('interval-select', data.interval);
    setVal('coins-select', data.coin_pool);
    setVal('rr-select', data.min_rr);
    setVal('conf-select', data.min_confidence);
}

async function saveConfig() {
    const getVal = (id) => { const el = document.getElementById(id); return el ? el.value : null; };
    const config = {
        mode: getVal('mode-select'),
        interval: getVal('interval-select'),
        coin_pool: parseInt(getVal('coins-select')),
        min_rr: parseFloat(getVal('rr-select')),
        min_confidence: parseInt(getVal('conf-select'))
    };
    const data = await apiPost('/api/config', config);
    if (data && data.success) {
        showToast('Config saved', 'success');
    }
}

// Auto-save on dropdown change
function setupConfigListeners() {
    ['mode-select', 'interval-select', 'coins-select', 'rr-select', 'conf-select'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', saveConfig);
    });
}

// ============================================
// SETTINGS MODAL (Telegram)
// ============================================
function openSettingsModal() {
    const overlay = document.getElementById('settings-modal');
    if (overlay) {
        overlay.classList.add('show');
        checkTelegramStatus();
    }
}

function closeSettingsModal() {
    const overlay = document.getElementById('settings-modal');
    if (overlay) overlay.classList.remove('show');
}

async function checkTelegramStatus() {
    const data = await apiFetch('/api/telegram/status');
    const statusEl = document.getElementById('tg-connection-status');
    if (!statusEl) return;

    if (data && data.configured) {
        statusEl.innerHTML = '<span>✓</span> Telegram connected';
        statusEl.className = 'connection-status success';
    } else {
        statusEl.innerHTML = '<span>○</span> Not configured';
        statusEl.className = 'connection-status pending';
    }
}

async function testTelegram() {
    const token = document.getElementById('tg-token').value.trim();
    const chatId = document.getElementById('tg-chatid').value.trim();
    const statusEl = document.getElementById('tg-connection-status');

    if (!token || !chatId) {
        showToast('Enter Bot Token and Chat ID', 'error');
        return;
    }

    statusEl.innerHTML = '<span class="spinner"></span> Testing...';
    statusEl.className = 'connection-status pending';

    const data = await apiPost('/api/telegram/test', { bot_token: token, chat_id: chatId });

    if (data && data.success) {
        statusEl.innerHTML = '<span>✓</span> Connected!';
        statusEl.className = 'connection-status success';
        showToast('Telegram connected!', 'success');
        updateTelegramIndicator(true);
    } else {
        statusEl.innerHTML = `<span>✗</span> ${data?.error || 'Connection failed'}`;
        statusEl.className = 'connection-status error';
        showToast('Telegram test failed', 'error');
    }
}

async function sendTestSignal() {
    showToast('Sending test signal...', 'info');
    const data = await apiPost('/api/telegram/send-test-signal');
    if (data && data.success) {
        showToast('Test signal sent to Telegram!', 'success');
    } else {
        showToast(data?.error || 'Failed to send test signal', 'error');
    }
}

function updateTelegramIndicator(connected) {
    const dot = document.getElementById('tg-status-dot');
    const text = document.getElementById('tg-status-text');
    if (dot) dot.classList.toggle('connected', connected);
    if (text) text.textContent = connected ? 'Telegram connected' : 'Not configured';
}

// ============================================
// LOG OUTCOME MODAL
// ============================================
let selectedSignalId = null;
let selectedOutcome = null;

function openLogOutcomeModal() {
    const overlay = document.getElementById('outcome-modal');
    if (overlay) overlay.classList.add('show');
    loadSignalsForOutcome();
}

function closeLogOutcomeModal() {
    const overlay = document.getElementById('outcome-modal');
    if (overlay) overlay.classList.remove('show');
    selectedSignalId = null;
    selectedOutcome = null;
}

async function loadSignalsForOutcome() {
    const data = await apiFetch('/api/signals');
    const container = document.getElementById('outcome-signals');
    if (!container || !data) return;

    const signals = (data.signals || []).filter(s => s.status === 'ACTIVE');
    if (signals.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-text">No active signals</div></div>';
        return;
    }

    container.innerHTML = signals.map(s => `
        <div class="outcome-signal-item" onclick="selectSignalForOutcome('${s.id}', this)">
            <span style="font-weight:600;font-family:'JetBrains Mono',monospace;">${s.symbol}</span>
            <span class="signal-side ${s.side.toLowerCase()}" style="font-size:0.7rem">${s.side}</span>
        </div>
    `).join('');
}

function selectSignalForOutcome(id, el) {
    selectedSignalId = id;
    document.querySelectorAll('.outcome-signal-item').forEach(e => e.classList.remove('selected'));
    el.classList.add('selected');
    const form = document.getElementById('outcome-form');
    if (form) form.classList.add('show');
}

function selectOutcome(outcome, btn) {
    selectedOutcome = outcome;
    document.querySelectorAll('.outcome-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}

async function submitOutcome() {
    if (!selectedSignalId || !selectedOutcome) {
        showToast('Select a signal and outcome', 'error');
        return;
    }
    const price = document.getElementById('exit-price').value;
    const data = await apiPost(`/api/signals/${selectedSignalId}/outcome`, {
        outcome: selectedOutcome,
        price: price ? parseFloat(price) : null
    });
    if (data && data.success) {
        showToast('Outcome logged!', 'success');
        closeLogOutcomeModal();
        refreshPerformance();
        refreshSignals();
    } else {
        showToast('Failed to log outcome', 'error');
    }
}

// ============================================
// HISTORY MODAL
// ============================================
function openHistoryModal() {
    const overlay = document.getElementById('history-modal');
    if (overlay) overlay.classList.add('show');
    loadHistory();
}

function closeHistoryModal() {
    const overlay = document.getElementById('history-modal');
    if (overlay) overlay.classList.remove('show');
}

async function loadHistory() {
    const data = await apiFetch('/api/performance/history');
    const container = document.getElementById('history-content');
    if (!container || !data) return;

    const trades = data.trades || [];
    if (trades.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-text">No trade history yet</div></div>';
        return;
    }

    container.innerHTML = `
        <table class="history-table">
            <thead>
                <tr><th>Symbol</th><th>Side</th><th>PnL</th><th>Outcome</th><th>Date</th></tr>
            </thead>
            <tbody>
                ${trades.map(t => `
                    <tr>
                        <td>${t.symbol}</td>
                        <td><span class="signal-side ${t.side.toLowerCase()}" style="font-size:0.65rem">${t.side}</span></td>
                        <td style="color:${t.pnl_pct >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}">${t.pnl_pct >= 0 ? '+' : ''}${t.pnl_pct}%</td>
                        <td>${t.outcome}</td>
                        <td style="color:var(--text-secondary)">${new Date(t.closed_at).toLocaleDateString()}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>`;
}

// ============================================
// BACKTEST
// ============================================
function openBacktestModal() {
    const overlay = document.getElementById('backtest-modal');
    if (overlay) overlay.classList.add('show');
}

function closeBacktestModal() {
    const overlay = document.getElementById('backtest-modal');
    if (overlay) overlay.classList.remove('show');
}

async function runBacktest() {
    openBacktestModal();
    const container = document.getElementById('backtest-content');
    if (container) container.innerHTML = '<div class="loading"><span class="spinner"></span> Scanning coins & running backtest...</div>';

    showToast('Running backtest...', 'info');
    const data = await apiPost('/api/performance/backtest');

    if (!data || !data.success) {
        if (container) container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-text">${data?.error || 'Backtest failed'}</div></div>`;
        showToast('Backtest failed', 'error');
        return;
    }

    const s = data.summary;
    const results = data.results || [];

    let html = `
        <div class="perf-stats" style="margin-bottom:1rem;">
            <div class="perf-stat"><div class="perf-value">${s.total_signals}</div><div class="perf-label">Signals</div></div>
            <div class="perf-stat"><div class="perf-value positive">${s.wins}</div><div class="perf-label">Wins</div></div>
            <div class="perf-stat"><div class="perf-value negative">${s.losses}</div><div class="perf-label">Losses</div></div>
            <div class="perf-stat"><div class="perf-value">${s.win_rate}%</div><div class="perf-label">Win Rate</div></div>
            <div class="perf-stat"><div class="perf-value ${s.total_pnl >= 0 ? 'positive' : 'negative'}">${s.total_pnl >= 0 ? '+' : ''}${s.total_pnl}%</div><div class="perf-label">Total PnL</div></div>
        </div>`;

    if (results.length === 0) {
        html += '<div class="empty-state"><div class="empty-state-text">No signals found in current market</div><div class="empty-state-sub">Try again later when market conditions change</div></div>';
    } else {
        html += `<table class="history-table"><thead><tr><th>Symbol</th><th>Side</th><th>RSI</th><th>Conf</th><th>PnL</th><th>Result</th></tr></thead><tbody>`;
        for (const r of results) {
            html += `<tr>
                <td>${r.symbol}</td>
                <td><span class="signal-side ${r.side.toLowerCase()}" style="font-size:0.65rem">${r.side}</span></td>
                <td>${r.rsi}</td>
                <td>${r.confidence}%</td>
                <td style="color:${r.simulated_pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}">${r.simulated_pnl >= 0 ? '+' : ''}${r.simulated_pnl}%</td>
                <td style="color:${r.outcome === 'WIN' ? 'var(--accent-green)' : 'var(--accent-red)'}">${r.outcome}</td>
            </tr>`;
        }
        html += '</tbody></table>';
    }

    html += `<div style="margin-top:0.75rem;font-size:0.7rem;color:var(--text-muted)">Config: ${data.config_used.mode} / ${data.config_used.interval} / Top ${data.config_used.coin_pool}</div>`;

    if (container) container.innerHTML = html;
    showToast(`Backtest done: ${s.total_signals} signals, ${s.win_rate}% win rate`, 'success');
}

// ============================================
// EVOLUTION SYSTEM
// ============================================
function openEvolutionModal() {
    const overlay = document.getElementById('evolution-modal');
    if (overlay) overlay.classList.add('show');
}

function closeEvolutionModal() {
    const overlay = document.getElementById('evolution-modal');
    if (overlay) overlay.classList.remove('show');
}

let lastEvolutionResult = null;

async function runEvolve() {
    openEvolutionModal();
    const container = document.getElementById('evolution-content');
    const applyBtn = document.getElementById('apply-evolution-btn');
    if (container) container.innerHTML = '<div class="loading"><span class="spinner"></span> Analyzing trades & evolving thresholds...</div>';
    if (applyBtn) applyBtn.style.display = 'none';

    showToast('Running evolution...', 'info');
    const data = await apiPost('/api/learning/evolution/evolve', { apply_to_config: false });

    if (!data) {
        if (container) container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-text">Evolution failed</div></div>';
        showToast('Evolution failed', 'error');
        return;
    }

    if (!data.success) {
        if (container) container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📊</div><div class="empty-state-text">${data.message || 'Cannot evolve yet'}</div><div class="empty-state-sub">Log more trade outcomes to enable evolution</div></div>`;
        showToast(data.message || 'Not enough data', 'info');
        return;
    }

    lastEvolutionResult = data;

    let html = `
        <div class="perf-stats" style="margin-bottom:1rem;">
            <div class="perf-stat"><div class="perf-value">#${data.generation}</div><div class="perf-label">Generation</div></div>
            <div class="perf-stat"><div class="perf-value">${data.trades_analyzed}</div><div class="perf-label">Trades</div></div>
            <div class="perf-stat"><div class="perf-value">${data.overall_win_rate}%</div><div class="perf-label">Win Rate</div></div>
            <div class="perf-stat"><div class="perf-value ${data.avg_pnl >= 0 ? 'positive' : 'negative'}">${data.avg_pnl >= 0 ? '+' : ''}${data.avg_pnl}%</div><div class="perf-label">Avg PnL</div></div>
        </div>`;

    if (data.changes && data.changes.length > 0) {
        html += `<div class="control-label" style="margin-bottom:0.5rem;">Threshold Changes</div>
        <table class="history-table"><thead><tr><th>Parameter</th><th>Before</th><th>After</th><th></th></tr></thead><tbody>`;
        for (const c of data.changes) {
            const arrow = c.direction === 'up' ? '↑' : '↓';
            const color = c.direction === 'up' ? 'var(--accent-green)' : 'var(--accent-red)';
            html += `<tr>
                <td>${c.param}</td>
                <td style="color:var(--text-secondary)">${c.before}</td>
                <td style="font-weight:600">${c.after}</td>
                <td style="color:${color};font-size:1.1rem">${arrow}</td>
            </tr>`;
        }
        html += '</tbody></table>';
        if (applyBtn) applyBtn.style.display = '';
    } else {
        html += '<div class="empty-state" style="padding:1rem"><div class="empty-state-text">No threshold changes needed</div><div class="empty-state-sub">Current thresholds are optimal for your trade history</div></div>';
    }

    if (data.rsi_analysis && Object.keys(data.rsi_analysis).length > 0) {
        html += `<div class="control-label" style="margin-top:1rem;margin-bottom:0.5rem;">RSI Bracket Analysis</div>
        <table class="history-table"><thead><tr><th>Bracket</th><th>Wins</th><th>Losses</th><th>Win Rate</th></tr></thead><tbody>`;
        for (const [name, info] of Object.entries(data.rsi_analysis)) {
            const wr = info.win_rate;
            const color = wr >= 60 ? 'var(--accent-green)' : wr >= 40 ? 'var(--accent-yellow)' : 'var(--accent-red)';
            html += `<tr><td>${name}</td><td>${info.wins}</td><td>${info.losses}</td><td style="color:${color}">${wr}%</td></tr>`;
        }
        html += '</tbody></table>';
    }

    if (container) container.innerHTML = html;
    showToast(`Evolution Gen #${data.generation} complete`, 'success');
}

async function applyEvolution() {
    showToast('Applying evolved thresholds to config...', 'info');
    const data = await apiPost('/api/learning/evolution/evolve', { apply_to_config: true });
    if (data && data.success) {
        showToast('Thresholds applied to config!', 'success');
        loadConfig();
        const applyBtn = document.getElementById('apply-evolution-btn');
        if (applyBtn) applyBtn.style.display = 'none';
    } else {
        showToast('Failed to apply thresholds', 'error');
    }
}

// ============================================
// SETTINGS MODAL - TAB SYSTEM
// ============================================
let currentSettingsTab = 'telegram';

function switchSettingsTab(tab) {
    currentSettingsTab = tab;

    // Update tab buttons
    document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    document.getElementById('tab-' + tab)?.classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById('content-' + tab)?.classList.add('active');
}

function openSettingsModal() {
    const overlay = document.getElementById('settings-modal');
    if (overlay) {
        overlay.classList.add('show');
        // Load status for current tab
        if (currentSettingsTab === 'telegram') {
            checkTelegramStatus();
        } else {
            checkBinanceStatus();
        }
    }
}

function closeSettingsModal() {
    const overlay = document.getElementById('settings-modal');
    if (overlay) overlay.classList.remove('show');
}

// ============================================
// TELEGRAM FUNCTIONS
// ============================================
async function checkTelegramStatus() {
    const data = await apiFetch('/api/telegram/status');
    const statusEl = document.getElementById('tg-connection-status');
    if (!statusEl) return;

    if (data && data.configured) {
        statusEl.innerHTML = '<span>✓</span> Telegram connected';
        statusEl.className = 'connection-status success';
    } else {
        statusEl.innerHTML = '<span>○</span> Not configured';
        statusEl.className = 'connection-status pending';
    }
}

async function testTelegram() {
    const token = document.getElementById('tg-token').value.trim();
    const chatId = document.getElementById('tg-chatid').value.trim();

    if (!token || !chatId) {
        showToast('Enter Bot Token and Chat ID', 'error');
        return;
    }

    showToast('Testing Telegram connection...', 'info');
    const data = await apiPost('/api/telegram/test', { bot_token: token, chat_id: chatId });

    if (data && data.success) {
        showToast('Telegram connected!', 'success');
        updateTelegramIndicator(true);
        checkTelegramStatus();
    } else {
        showToast(data?.error || 'Telegram test failed', 'error');
    }
}

async function sendTestSignal() {
    showToast('Sending test signal...', 'info');
    const data = await apiPost('/api/telegram/send-test-signal');
    if (data && data.success) {
        showToast('Test signal sent to Telegram!', 'success');
    } else {
        showToast(data?.error || 'Failed to send test signal', 'error');
    }
}

function updateTelegramIndicator(connected) {
    const dot = document.getElementById('tg-status-dot');
    if (dot) {
        dot.classList.toggle('connected', connected);
        dot.classList.toggle('disconnected', !connected);
    }
}

// ============================================
// BINANCE FUNCTIONS
// ============================================
async function checkBinanceStatus() {
    const data = await apiFetch('/api/binance/status');
    const statusEl = document.getElementById('binance-connection-status');
    const balancesEl = document.getElementById('binance-balances');
    const balancesList = document.getElementById('balances-list');

    if (!statusEl) return;

    if (data && data.configured) {
        if (data.connected) {
            statusEl.innerHTML = '<span>✓</span> Binance connected';
            statusEl.className = 'connection-status success';
            updateBinanceIndicator(true);

            // Show balances if available
            if (data.balances && data.balances.length > 0 && balancesEl && balancesList) {
                balancesEl.style.display = 'block';
                balancesList.innerHTML = data.balances.map(b => `
                    <div class="balance-item">
                        <span class="balance-asset">${b.asset}</span>
                        <span class="balance-amount">${b.total.toFixed(4)}</span>
                    </div>
                `).join('');
            }
        } else {
            statusEl.innerHTML = `<span>✗</span> ${data.error || 'Connection failed'}`;
            statusEl.className = 'connection-status error';
            updateBinanceIndicator(false);
        }
    } else {
        statusEl.innerHTML = '<span>○</span> Not configured';
        statusEl.className = 'connection-status pending';
        updateBinanceIndicator(false);
    }
}

async function testBinance() {
    const apiKey = document.getElementById('binance-api-key').value.trim();
    const secretKey = document.getElementById('binance-secret-key').value.trim();

    if (!apiKey || !secretKey) {
        showToast('Enter API Key and Secret Key', 'error');
        return;
    }

    showToast('Testing Binance connection...', 'info');
    const data = await apiPost('/api/binance/test', { api_key: apiKey, secret_key: secretKey });

    if (data && data.success) {
        showToast('Binance connected!', 'success');
        updateBinanceIndicator(true);
        checkBinanceStatus();
    } else {
        showToast(data?.error || 'Binance test failed', 'error');
        updateBinanceIndicator(false);
    }
}

async function saveBinanceConfig() {
    const apiKey = document.getElementById('binance-api-key').value.trim();
    const secretKey = document.getElementById('binance-secret-key').value.trim();
    const executionMode = document.getElementById('execution-mode-select').value;

    const data = await apiPost('/api/binance/save', {
        api_key: apiKey,
        secret_key: secretKey,
        execution_mode: executionMode
    });

    if (data && data.success) {
        showToast('Binance settings saved!', 'success');
        updateExecutionModeBadge(executionMode);
    } else {
        showToast('Failed to save Binance settings', 'error');
    }
}

async function loadBinanceConfig() {
    const data = await apiFetch('/api/config');
    if (!data) return;

    // Load execution mode
    const execMode = data.execution_mode || 'signal_only';
    const selectEl = document.getElementById('execution-mode-select');
    if (selectEl) selectEl.value = execMode;

    updateExecutionModeBadge(execMode);
}

function updateExecutionModeBadge(mode) {
    const badge = document.getElementById('execution-badge');
    const valueEl = document.getElementById('execution-mode-value');

    if (valueEl) {
        const modeLabels = {
            'signal_only': 'SIGNALS ONLY',
            'semi_auto': 'SEMI-AUTO',
            'full_auto': 'FULL-AUTO'
        };
        valueEl.textContent = modeLabels[mode] || mode.toUpperCase();
    }

    if (badge) {
        badge.className = 'execution-badge mode-' + mode;
    }
}

function updateBinanceIndicator(connected) {
    const dot = document.getElementById('binance-status-dot');
    if (dot) {
        dot.classList.toggle('connected', connected);
        dot.classList.toggle('disconnected', !connected);
    }
}

// ============================================
// COMBINED SETTINGS HANDLERS
// ============================================
async function testSettings() {
    if (currentSettingsTab === 'telegram') {
        testTelegram();
    } else {
        testBinance();
    }
}

async function saveSettings() {
    if (currentSettingsTab === 'telegram') {
        // Save telegram settings
        const token = document.getElementById('tg-token').value.trim();
        const chatId = document.getElementById('tg-chatid').value.trim();
        await apiPost('/api/telegram/save', { bot_token: token, chat_id: chatId });
    } else {
        // Save binance settings
        await saveBinanceConfig();
    }
    // Close modal after save
    closeSettingsModal();
}

// ============================================
// EXECUTE SIGNAL (Semi-Auto)
// ============================================
let pendingExecuteSignal = null;

function openExecuteModal(signal) {
    pendingExecuteSignal = signal;
    const overlay = document.getElementById('execute-modal');
    const detailsEl = document.getElementById('execute-signal-details');

    if (overlay && detailsEl) {
        detailsEl.innerHTML = `
            <div class="execute-signal-card ${signal.side.toLowerCase()}">
                <div class="signal-header">
                    <span class="signal-symbol">${signal.symbol}</span>
                    <span class="signal-side ${signal.side.toLowerCase()}">${signal.side}</span>
                </div>
                <div class="signal-details">
                    <div class="signal-detail">
                        <span class="detail-label">Entry</span>
                        <span class="detail-value">${formatPrice(signal.entry)}</span>
                    </div>
                    <div class="signal-detail">
                        <span class="detail-label">SL</span>
                        <span class="detail-value" style="color:var(--accent-red)">-${signal.sl}%</span>
                    </div>
                    <div class="signal-detail">
                        <span class="detail-label">TP</span>
                        <span class="detail-value" style="color:var(--accent-green)">+${signal.tp}%</span>
                    </div>
                    <div class="signal-detail">
                        <span class="detail-label">R:R</span>
                        <span class="detail-value">1:${signal.rr}</span>
                    </div>
                </div>
            </div>
        `;
        overlay.classList.add('show');
    }
}

function closeExecuteModal() {
    const overlay = document.getElementById('execute-modal');
    if (overlay) overlay.classList.remove('show');
    pendingExecuteSignal = null;
}

async function confirmExecute() {
    if (!pendingExecuteSignal) return;

    showToast('Executing trade...', 'info');
    const data = await apiPost('/api/binance/execute', {
        signal: pendingExecuteSignal,
        confirmed: true
    });

    if (data && data.success) {
        showToast(`Trade executed: ${data.order?.symbol || pendingExecuteSignal.symbol}`, 'success');
        closeExecuteModal();
    } else {
        showToast(data?.error || 'Trade execution failed', 'error');
    }
}

// ============================================
// REFRESH ALL
// ============================================
function refreshAll() {
    refreshMarket();
    refreshSignals();
    refreshPerformance();
    refreshBotStatus();
}

// ============================================
// INIT
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Button listeners
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    if (startBtn) startBtn.addEventListener('click', startBot);
    if (stopBtn) stopBtn.addEventListener('click', stopBot);

    // Config listeners
    setupConfigListeners();

    // Load everything
    refreshAll();
    loadConfig();
    loadBinanceConfig();

    // Check status for indicators
    (async () => {
        const tgData = await apiFetch('/api/telegram/status');
        if (tgData) updateTelegramIndicator(tgData.configured);

        const binanceData = await apiFetch('/api/binance/status');
        if (binanceData) {
            updateBinanceIndicator(binanceData.connected);
            updateExecutionModeBadge(binanceData.execution_mode || 'signal_only');
        }
    })();

    // Auto-refresh every 30 seconds
    setInterval(refreshAll, 30000);

    // Close modals on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.classList.remove('show');
        });
    });

    // Close modals on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.show').forEach(m => m.classList.remove('show'));
        }
    });
});
