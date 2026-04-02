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
}

// ============================================
// LIVE SIGNALS
// ============================================
function formatPrice(price) {
    if (price >= 1000) return '$' + price.toLocaleString('en-US', { maximumFractionDigits: 0 });
    if (price >= 1) return '$' + price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return '$' + price.toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
}

function renderSignalCards(signals) {
    const container = document.getElementById('signals-container');
    if (!container) return;

    if (!signals || signals.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📡</div>
                <div class="empty-state-text">No signals yet</div>
                <div class="empty-state-sub">Start the bot to begin scanning</div>
            </div>`;
        return;
    }

    container.innerHTML = '<div class="signals-list">' + signals.map(s => `
        <div class="signal-card ${s.side.toLowerCase()}" data-id="${s.id || ''}">
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
    renderSignalCards(data.signals || []);
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

    // Check telegram status for indicator
    (async () => {
        const data = await apiFetch('/api/telegram/status');
        if (data) updateTelegramIndicator(data.configured);
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
