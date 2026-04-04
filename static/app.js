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
// WATCHLIST PRICES
// ============================================
async function refreshWatchlist() {
    const container = document.getElementById('watchlist-container');
    if (!container) return;

    const data = await apiFetch('/api/market/prices');
    if (!data || !data.prices || data.prices.length === 0) {
        if (container) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-text">No prices available</div></div>';
        }
        return;
    }

    const html = data.prices.map(coin => {
        const changeClass = coin.change_24h > 0 ? 'up' : coin.change_24h < 0 ? 'down' : 'neutral';
        const sign = coin.change_24h >= 0 ? '+' : '';
        const price = formatPrice(coin.price);
        return `
        <div class="watchlist-item">
            <div class="watchlist-coin">
                <div>
                    <div class="watchlist-name">${coin.name || coin.short}</div>
                    <div class="watchlist-symbol">${coin.short}</div>
                </div>
            </div>
            <div class="watchlist-price">${price}</div>
            <div class="watchlist-change ${changeClass}">${sign}${coin.change_24h?.toFixed(2) || '0.00'}%</div>
        </div>`;
    }).join('');

    if (container) container.innerHTML = html;
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
            ${s.strategy_id ? `<div class="signal-strategy-tag">🎯 ${s.strategy_id}</div>` : ''}
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
            ${!s.is_example ? `
            <div class="signal-actions">
                <button class="execute-btn" onclick='openExecuteModal(${JSON.stringify(s)})' title="Execute trade">▶ EXECUTE</button>
                <button class="skip-btn" onclick="skipSignal('${s.id}')" title="Skip signal">× SKIP</button>
            </div>` : ''}
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
// BACKTEST (Phase 1.7 — uses real API + Chart.js)
// ============================================
let equityChartInstance = null;

function openBacktestModal() {
    const overlay = document.getElementById('backtest-modal');
    if (overlay) overlay.classList.add('show');
    const chartContainer = document.getElementById('equity-chart-container');
    if (chartContainer) chartContainer.style.display = 'none';
}

function closeBacktestModal() {
    const overlay = document.getElementById('backtest-modal');
    if (overlay) overlay.classList.remove('show');
    if (equityChartInstance) { equityChartInstance.destroy(); equityChartInstance = null; }
}

async function runBacktest(strategyId) {
    openBacktestModal();
    const container = document.getElementById('backtest-content');
    const chartContainer = document.getElementById('equity-chart-container');
    if (container) container.innerHTML = '<div class="loading"><span class="spinner"></span> Running backtest...</div>';
    if (chartContainer) chartContainer.style.display = 'none';

    // If no strategyId provided, try to get from selector
    if (!strategyId) {
        const sel = document.getElementById('strategy-select');
        strategyId = sel ? sel.value : null;
    }

    if (!strategyId) {
        showToast('Select a strategy first', 'error');
        if (container) container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-text">No strategy selected</div></div>';
        return;
    }

    showToast('Running backtest...', 'info');
    const data = await apiPost('/api/backtest/run', { strategy_id: strategyId, days: 30 });

    if (!data || !data.success) {
        if (container) container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-text">${data?.error || 'Backtest failed'}</div></div>`;
        showToast('Backtest failed', 'error');
        return;
    }

    const s = data.summary || {};
    const trades = data.trades || [];
    const equity = data.equity_curve || [];

    let html = `
        <div class="perf-stats" style="margin-bottom:1rem;">
            <div class="perf-stat"><div class="perf-value">${s.total_trades || 0}</div><div class="perf-label">Trades</div></div>
            <div class="perf-stat"><div class="perf-value positive">${s.winning_trades || 0}</div><div class="perf-label">Wins</div></div>
            <div class="perf-stat"><div class="perf-value negative">${s.losing_trades || 0}</div><div class="perf-label">Losses</div></div>
            <div class="perf-stat"><div class="perf-value">${s.win_rate || 0}%</div><div class="perf-label">Win Rate</div></div>
            <div class="perf-stat"><div class="perf-value ${(s.total_pnl_pct || 0) >= 0 ? 'positive' : 'negative'}">${(s.total_pnl_pct || 0) >= 0 ? '+' : ''}${s.total_pnl_pct || 0}%</div><div class="perf-label">Total PnL</div></div>
            <div class="perf-stat"><div class="perf-value negative">-${s.max_drawdown_pct || 0}%</div><div class="perf-label">Max DD</div></div>
        </div>`;

    if (trades.length > 0) {
        html += `<table class="history-table"><thead><tr><th>Symbol</th><th>Side</th><th>PnL</th><th>Result</th><th>Date</th></tr></thead><tbody>`;
        trades.slice(0, 20).forEach(t => {
            html += `<tr>
                <td>${t.symbol || '-'}</td>
                <td><span class="signal-side ${(t.side||'buy').toLowerCase()}" style="font-size:0.65rem">${t.side || '-'}</span></td>
                <td style="color:${(t.pnl_pct||0) >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}">${(t.pnl_pct||0) >= 0 ? '+' : ''}${t.pnl_pct || 0}%</td>
                <td style="color:${t.outcome === 'WIN' ? 'var(--accent-green)' : 'var(--accent-red)'}">${t.outcome || '-'}</td>
                <td style="color:var(--text-secondary)">${t.exit_time ? new Date(t.exit_time).toLocaleDateString() : '-'}</td>
            </tr>`;
        });
        html += '</tbody></table>';
    } else {
        html += '<div class="empty-state"><div class="empty-state-text">No trades found in this period</div></div>';
    }

    if (container) container.innerHTML = html;

    // Render equity curve chart if data available
    if (equity.length > 1 && chartContainer) {
        chartContainer.style.display = 'block';
        if (equityChartInstance) equityChartInstance.destroy();
        const ctx = document.getElementById('equity-chart').getContext('2d');
        equityChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: equity.map((_, i) => i),
                datasets: [{
                    label: 'Equity',
                    data: equity,
                    borderColor: '#00ff9d',
                    backgroundColor: 'rgba(0,255,157,0.05)',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { display: false },
                    y: { ticks: { color: '#64748b', font: { size: 10 } }, grid: { color: '#1e293b' } }
                }
            }
        });
    }

    showToast(`Backtest: ${s.win_rate || 0}% win rate, ${s.total_pnl_pct || 0}% PnL`, 'success');
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
    refreshWatchlist();
    refreshSignals();
    refreshPerformance();
    refreshBotStatus();
    if (typeof refreshPositions === 'function') refreshPositions();
    if (typeof refreshRiskStatus === 'function') refreshRiskStatus();
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
    if (typeof refreshStrategies === 'function') refreshStrategies();
    loadStrategySelector();

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
    // Positions refresh every 10 seconds
    setInterval(() => { if (typeof refreshPositions === 'function') refreshPositions(); }, 10000);
    // Risk status refresh every 30 seconds
    setInterval(() => { if (typeof refreshRiskStatus === 'function') refreshRiskStatus(); }, 30000);

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

// ============================================
// POSITIONS PANEL (Phase 1.7)
// ============================================
async function refreshPositions() {
    const resp = await apiFetch('/api/positions');
    if (!resp) return;
    const container = document.getElementById('positions-container');
    const panel = document.getElementById('positions-panel');
    const badge = document.getElementById('position-count-badge');
    
    if (!container) return;
    const positions = resp.positions || [];
    
    if (positions.length === 0) {
        panel.classList.remove('visible');
        badge.textContent = '0';
        container.innerHTML = '<div class="empty-state">No open positions</div>';
        return;
    }
    
    panel.classList.add('visible');
    badge.textContent = positions.length;
    
    let html = '';
    positions.forEach(p => {
        const pnlClass = p.unrealized_pnl_pct >= 0 ? 'profit' : 'loss';
        html += `<div class="position-item">
            <div class="position-symbol">${p.symbol} ${p.side}</div>
            <div class="position-entry">Entry: ${p.entry_price} | Current: ${p.current_price}</div>
            <div class="position-sl-tp">SL: ${p.sl_price?.toFixed(4)} | TP: ${p.tp_price?.toFixed(4)}</div>
            <div class="position-pnl ${pnlClass}">${p.unrealized_pnl_pct >= 0 ? '+' : ''}${p.unrealized_pnl_pct?.toFixed(2)}% ($${p.unrealized_pnl_usd?.toFixed(2)})</div>
            <button class="btn-xs" onclick="closePosition(${p.id})">CLOSE</button>
        </div>`;
    });
    container.innerHTML = html;
}

async function checkPositions() {
    const resp = await apiPost('/api/positions/check');
    if (resp && resp.success) {
        showToast(`Checked: ${resp.checked} updates`, 'info');
        refreshPositions();
    }
}

async function closePosition(positionId) {
    if (!confirm('Close this position?')) return;
    const resp = await apiPost(`/api/positions/${positionId}/close`, {
        exit_price: 0, // Will use current market price
        reason: 'MANUAL_CLOSE'
    });
    if (resp && resp.success) {
        showToast('Position closed', 'success');
        refreshPositions();
        refreshPerformance();
    } else {
        showToast(resp?.error || 'Failed to close', 'error');
    }
}

// ============================================
// RISK STATUS (Phase 1.7)
// ============================================
async function refreshRiskStatus() {
    const resp = await apiFetch('/api/risk/status');
    if (!resp) return;
    const r = resp.risk || {};
    const limits = r.limits || {};
    
    // Circuit breaker
    const cbEl = document.getElementById('cb-status');
    const cbBtn = document.getElementById('cb-reset-btn');
    if (cbEl) {
        if (r.circuit_breaker_active) {
            cbEl.textContent = '🚨 ON';
            cbEl.className = 'risk-value danger';
            if (cbBtn) cbBtn.style.display = 'inline-block';
        } else {
            cbEl.textContent = '✅ OFF';
            cbEl.className = 'risk-value safe';
            if (cbBtn) cbBtn.style.display = 'none';
        }
    }
    
    // Daily loss
    const dlEl = document.getElementById('daily-loss');
    if (dlEl) dlEl.textContent = `${r.daily_loss_pct || 0}% / ${limits.max_daily_loss_pct || 5}%`;
    
    // Weekly loss
    const wlEl = document.getElementById('weekly-loss');
    if (wlEl) wlEl.textContent = `${r.weekly_loss_pct || 0}% / ${limits.max_weekly_loss_pct || 10}%`;
    
    // Open positions count
    const opEl = document.getElementById('open-positions-risk');
    if (opEl) opEl.textContent = `${r.portfolio?.open_count || 0} / ${limits.max_positions || 3}`;
    
    // Total invested
    const tiEl = document.getElementById('total-invested');
    if (tiEl) tiEl.textContent = `$${r.portfolio?.total_invested_usd || 0}`;
}

async function resetCircuitBreaker() {
    if (!confirm('Reset circuit breaker? This will allow new trades.')) return;
    const resp = await apiPost('/api/risk/circuit-breaker/deactivate');
    if (resp && resp.success) {
        showToast('Circuit breaker reset', 'success');
        refreshRiskStatus();
    }
}

// ============================================
// STRATEGIES PANEL (Phase 1.7)
// ============================================
async function refreshStrategies() {
    const container = document.getElementById('strategies-container');
    if (!container) return;
    
    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 8000);
        const resp = await apiFetch('/api/strategies/', { signal: controller.signal });
        clearTimeout(timeout);
        
        if (!resp || !resp.strategies) {
            container.innerHTML = '<div class="empty-state">Failed to load. Tap + NEW.</div>';
            return;
        }
        
        const strategies = resp.strategies;
        if (strategies.length === 0) {
            container.innerHTML = '<div class="empty-state">No strategies yet. Create one!</div>';
            return;
        }
        
        let html = '';
        strategies.forEach(s => {
            const activeBadge = s.is_active ? '<span class="badge active">ACTIVE</span>' : '';
            const mode = s.mode || 'SWING';
            html += '<div class="strategy-item">';
            html += '<div class="strategy-header">';
            html += `<span class="strategy-name">${s.name || ''}</span>`;
            html += activeBadge;
            html += '</div>';
            html += `<div class="strategy-meta">${mode} | ${s.timeframe || '15m'} | ${s.min_rr || 2}x R:R</div>`;
            html += `<div class="strategy-coins">${(s.coins || '').substring(0, 40)}</div>`;
            html += '<div class="strategy-actions">';
            if (s.is_active) {
                html += `<button class="btn-xs" onclick="toggleStrategy('${s.id}', 0)">DEACTIVATE</button>`;
            } else {
                html += `<button class="btn-xs btn-start" onclick="toggleStrategy('${s.id}', 1)">ACTIVATE</button>`;
            }
            html += `<button class="btn-xs" onclick="deleteStrategy('${s.id}')">DELETE</button>`;
            html += '</div></div>';
        });
        container.innerHTML = html;
        
    } catch (e) {
        console.error('refreshStrategies error:', e);
        container.innerHTML = '<div class="empty-state">Error loading. Tap refresh.</div>';
    }
}

async function toggleStrategy(strategyId, activate) {
    const url = activate ? `/api/strategies/${strategyId}/activate` : `/api/strategies/${strategyId}/deactivate`;
    const resp = await apiPost(url);
    if (resp && resp.success) {
        showToast(activate ? 'Strategy activated' : 'Strategy deactivated', 'success');
        refreshStrategies();
    }
}

async function deleteStrategy(strategyId) {
    if (!confirm('Delete this strategy?')) return;
    const resp = await apiFetch(`/api/strategies/${strategyId}`, { method: 'DELETE' });
    if (resp && resp.success) {
        showToast('Strategy deleted', 'success');
        refreshStrategies();
    }
}

// ============================================
// STRATEGY MODAL (Phase 1.7)
// ============================================
// ============================================
// STRATEGY MODAL — ROW BUILDER (Phase 1.7)
// ============================================
const CONDITION_INDICATORS = ['RSI','EMA','MACD','BOLLINGER','ATR','VWAP','VOLUME','PRICE'];
const CONDITION_OPERATORS  = ['<','>','<=','>=','==','CROSS_ABOVE','CROSS_BELOW'];

function buildConditionRowHTML(type, idx) {
    const indOpts = CONDITION_INDICATORS.map(i => `<option value="${i}">${i}</option>`).join('');
    const opOpts  = CONDITION_OPERATORS.map(o => `<option value="${o}">${o}</option>`).join('');
    return `
    <div class="condition-row" id="${type}-cond-${idx}">
        <select class="cond-indicator" style="flex:1.5">${indOpts}</select>
        <input  class="cond-period" type="number" value="14" min="1" placeholder="period" style="width:52px">
        <select class="cond-operator" style="flex:1">${opOpts}</select>
        <input  class="cond-value" type="number" value="30" step="any" placeholder="value" style="width:60px">
        <button class="btn-xs btn-danger-xs" onclick="removeConditionRow('${type}', ${idx})" title="Remove">✕</button>
    </div>`;
}

function addConditionRow(type) {
    const builder = document.getElementById(`${type}-conditions-builder`);
    if (!builder) return;
    const idx = builder.querySelectorAll('.condition-row').length;
    const div = document.createElement('div');
    div.innerHTML = buildConditionRowHTML(type, idx);
    builder.appendChild(div.firstElementChild);
}

function removeConditionRow(type, idx) {
    const row = document.getElementById(`${type}-cond-${idx}`);
    if (row) row.remove();
}

function collectConditions(type) {
    const builder = document.getElementById(`${type}-conditions-builder`);
    if (!builder) return [];
    const rows = builder.querySelectorAll('.condition-row');
    const result = [];
    rows.forEach(row => {
        result.push({
            indicator: row.querySelector('.cond-indicator').value,
            period:    parseInt(row.querySelector('.cond-period').value) || 14,
            operator:  row.querySelector('.cond-operator').value,
            value:     parseFloat(row.querySelector('.cond-value').value) || 0
        });
    });
    return result;
}

function openStrategyModal(prefill) {
    const modal = document.getElementById('strategy-modal');
    if (!modal) return;
    modal.classList.add('show');

    const editingId = document.getElementById('str-editing-id');
    const saveBtn   = document.getElementById('str-save-btn');

    // Clear condition builders
    ['entry','exit'].forEach(t => {
        const b = document.getElementById(`${t}-conditions-builder`);
        if (b) b.innerHTML = '';
    });

    if (prefill) {
        // Editing existing strategy
        if (editingId) editingId.value = prefill.id || '';
        if (saveBtn) saveBtn.textContent = 'UPDATE STRATEGY';
        document.getElementById('str-name').value    = prefill.name || '';
        document.getElementById('str-coins').value   = (typeof prefill.coins === 'string'
            ? JSON.parse(prefill.coins || '[]') : prefill.coins || []).join(', ');
        document.getElementById('str-mode').value      = prefill.mode || 'SWING';
        document.getElementById('str-timeframe').value = prefill.timeframe || '1h';
        document.getElementById('str-sl').value     = prefill.sl_pct || 2.5;
        document.getElementById('str-tp').value     = prefill.tp_pct || 7.5;
        document.getElementById('str-minrr').value  = prefill.min_rr || 2.0;
        document.getElementById('str-minconf').value= prefill.min_confidence || 50;
        document.getElementById('str-entry-logic').value = prefill.entry_logic || 'AND';
        document.getElementById('str-exit-logic').value  = prefill.exit_logic  || 'OR';

        // Populate condition rows from JSON
        const entryConds = typeof prefill.entry_conditions === 'string'
            ? JSON.parse(prefill.entry_conditions || '[]') : prefill.entry_conditions || [];
        const exitConds = typeof prefill.exit_conditions === 'string'
            ? JSON.parse(prefill.exit_conditions || '[]') : prefill.exit_conditions || [];

        entryConds.forEach(() => addConditionRow('entry'));
        exitConds.forEach((c, i) => {
            addConditionRow('exit');
            const row = document.querySelectorAll('#exit-conditions-builder .condition-row')[i];
            if (row) {
                row.querySelector('.cond-indicator').value = c.indicator || 'RSI';
                row.querySelector('.cond-period').value    = c.period    || 14;
                row.querySelector('.cond-operator').value  = c.operator  || '<';
                row.querySelector('.cond-value').value     = c.value     || 0;
            }
        });
        entryConds.forEach((c, i) => {
            const row = document.querySelectorAll('#entry-conditions-builder .condition-row')[i];
            if (row) {
                row.querySelector('.cond-indicator').value = c.indicator || 'RSI';
                row.querySelector('.cond-period').value    = c.period    || 14;
                row.querySelector('.cond-operator').value  = c.operator  || '<';
                row.querySelector('.cond-value').value     = c.value     || 0;
            }
        });
    } else {
        // New strategy — defaults
        if (editingId) editingId.value = '';
        if (saveBtn) saveBtn.textContent = 'CREATE STRATEGY';
        document.getElementById('str-name').value     = '';
        document.getElementById('str-coins').value    = 'BTCUSDT, ETHUSDT, SOLUSDT';
        document.getElementById('str-mode').value     = 'SWING';
        document.getElementById('str-timeframe').value= '1h';
        document.getElementById('str-sl').value       = '2.5';
        document.getElementById('str-tp').value       = '7.5';
        document.getElementById('str-minrr').value    = '2.0';
        document.getElementById('str-minconf').value  = '50';
        // Add one default entry condition
        addConditionRow('entry');
        addConditionRow('exit');
        // Set exit condition default to RSI > 70
        const exitRow = document.querySelector('#exit-conditions-builder .condition-row');
        if (exitRow) {
            exitRow.querySelector('.cond-operator').value = '>';
            exitRow.querySelector('.cond-value').value    = '70';
        }
    }
}

function closeStrategyModal() {
    document.getElementById('strategy-modal').classList.remove('show');
}

async function saveStrategy() {
    const editingId  = document.getElementById('str-editing-id')?.value?.trim();
    const name       = document.getElementById('str-name').value.trim();
    const coinsRaw   = document.getElementById('str-coins').value.trim();
    const mode       = document.getElementById('str-mode').value;
    const timeframe  = document.getElementById('str-timeframe').value;
    const sl_pct     = parseFloat(document.getElementById('str-sl').value)    || 2.5;
    const tp_pct     = parseFloat(document.getElementById('str-tp').value)    || 7.5;
    const min_rr     = parseFloat(document.getElementById('str-minrr').value) || 2.0;
    const min_confidence = parseInt(document.getElementById('str-minconf').value) || 50;
    const entry_logic  = document.getElementById('str-entry-logic')?.value || 'AND';
    const exit_logic   = document.getElementById('str-exit-logic')?.value  || 'OR';

    if (!name || !coinsRaw) { showToast('Name and coins are required', 'error'); return; }

    const entry_conditions = collectConditions('entry');
    const exit_conditions  = collectConditions('exit');

    if (entry_conditions.length === 0) { showToast('Add at least one entry condition', 'error'); return; }
    if (exit_conditions.length  === 0) { showToast('Add at least one exit condition', 'error'); return; }

    const coins = coinsRaw.split(',').map(c => c.trim().toUpperCase()).filter(Boolean);

    const payload = { name, coins, mode, timeframe, entry_conditions, exit_conditions,
        entry_logic, exit_logic, sl_pct, tp_pct, min_rr, min_confidence };

    let resp;
    if (editingId) {
        resp = await apiFetch(`/api/strategies/${editingId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    } else {
        resp = await apiPost('/api/strategies/', payload);
    }

    if (resp && resp.success) {
        showToast(editingId ? 'Strategy updated' : 'Strategy created', 'success');
        closeStrategyModal();
        refreshStrategies();
        loadStrategySelector();
    } else {
        showToast(resp?.error || 'Failed to save strategy', 'error');
    }
}

// ============================================
// TEMPLATES MODAL (Phase 1.7)
// ============================================
function openTemplatesModal() {
    document.getElementById('templates-modal').classList.add('show');
    loadTemplates();
}

function closeTemplatesModal() {
    document.getElementById('templates-modal').classList.remove('show');
}

async function loadTemplates() {
    const resp = await apiFetch('/api/strategies/templates');
    const container = document.getElementById('templates-content');
    if (!resp || !container) return;
    
    const templates = resp.templates || [];
    if (templates.length === 0) {
        container.innerHTML = '<div class="empty-state">No templates available</div>';
        return;
    }
    
    let html = '';
    templates.forEach(t => {
        html += `<div class="template-item">
            <div class="template-name">${t.name}</div>
            <div class="template-desc">${t.description || ''}</div>
            <div class="template-meta">${t.mode} | ${t.timeframe} | SL: ${t.sl_pct}% TP: ${t.tp_pct}%</div>
            <button class="btn btn-start btn-xs" onclick="createFromTemplate('${t.id}', '${t.name} (Copy)')">USE TEMPLATE</button>
        </div>`;
    });
    container.innerHTML = html;
}

async function createFromTemplate(templateId, name) {
    const resp = await apiPost('/api/strategies/from-template', {
        template_id: templateId,
        name: name || 'My Strategy'
    });
    if (resp && resp.success) {
        showToast('Strategy created from template', 'success');
        closeTemplatesModal();
        refreshStrategies();
    } else {
        showToast(resp?.error || 'Failed to create', 'error');
    }
}

// ============================================
// ENHANCED REFRESH ALL (Phase 1.7)
// ============================================
function refreshAll() {
    refreshMarket();
    refreshWatchlist();
    refreshSignals();
    refreshPerformance();
    refreshBotStatus();
    refreshPositions();
    refreshRiskStatus();
    refreshStrategies();
}

async function skipSignal(signalId) {
    const resp = await apiPost(`/api/signals/${signalId}/skip`);
    if (resp?.success) {
        showToast('Signal skipped', 'success');
        refreshSignals();
    } else {
        showToast('Failed to skip signal', 'error');
    }
}

async function loadStrategySelector() {
    const resp = await apiFetch('/api/strategies');
    const selector = document.getElementById('strategy-selector');
    if (!selector || !resp?.strategies) return;
    selector.innerHTML = resp.strategies.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
}

async function refreshStrategies() {
    const resp = await apiFetch('/api/strategies');
    const container = document.getElementById('strategies-list');
    if (!container || !resp?.strategies) return;
    container.innerHTML = resp.strategies.map(s => `
        <div class="strategy-item">
            <span>${s.name}</span>
            <div class="actions">
                <button onclick='openStrategyModal(${JSON.stringify(s)})'>Edit</button>
                <button onclick='runBacktest("${s.id}")'>Backtest</button>
            </div>
        </div>
    `).join('');
}
