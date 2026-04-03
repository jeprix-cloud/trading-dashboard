# Market Data Dashboard — Implementation Plan

## Overview

This project extends TradingCore Dashboard with comprehensive market data capabilities. Built in phases.

---

## ✅ COMPLETED: Phase 1-2

### Phase 1: Foundation — Basic Watchlist

**Status: COMPLETED**

| Task | Status | Location |
|------|--------|----------|
| `/api/market/prices` endpoint | ✅ Done | `routes/market.py` |
| `config/watchlist.json` | ✅ Done | Config file |
| Watchlist UI component | ✅ Done | `templates/dashboard.html` |
| Price formatting + arrows | ✅ Done | `static/app.js` |
| Auto-refresh 30s | ✅ Done | `static/app.js` |
| Watchlist caching (30s TTL) | ✅ Done | `routes/market.py` |

**Watchlist enabled coins:** BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, ADAUSDT

### Phase 2: Market Overview Panel

**Status: COMPLETED**

| Task | Status | Location | Notes |
|------|--------|----------|-------|
| `/api/market/pulse` endpoint | ✅ Done | `routes/market.py` | Includes F&G, BTC Dom, Trend, Trending |
| `/api/market/global` endpoint | ✅ Done | `routes/market.py` | Includes total_market_cap, volume, change_24h |
| `/api/market/fear-greed` | ✅ Done | `routes/market.py` | Individual endpoint |
| `/api/market/btc-dominance` | ✅ Done | `routes/market.py` | Individual endpoint |
| `/api/market/trending` | ✅ Done | `routes/market.py` | Individual endpoint |
| `/api/market/btc-trend` | ✅ Done | `routes/market.py` | Individual endpoint |
| Market Pulse UI | ✅ Done | `templates/dashboard.html` | F&G gauge, BTC Dom, Trend, Trending |
| Global Market UI | ✅ Done | `templates/dashboard.html` | Market Cap, 24h Change |
| refreshMarket() JS | ✅ Done | `static/app.js` | Fixed to fetch both pulse + global |
| `formatMarketCap()` helper | ✅ Done | `static/app.js` | Formats T/B/M values |

**Bug Fixes Applied (2026-04-03):**
1. Fixed cache logic: `timedelta.seconds` → `timedelta.total_seconds()`
2. Separated cache per data type (not shared `last_fetch`)
3. Moved `fetch_klines` import to module level
4. Increased BTC trend cache TTL: 5min → 15min (heavy operation)
5. Added watchlist file caching (30s TTL)
6. Reduced HTTP timeouts: 10s → 8s
7. Added `formatMarketCap()` for proper T/B/M formatting
8. Added proper `resp.raise_for_status()` for error handling

---

## 🔴 TODO: Phase 3-5 (for Antigravity)

---

## PHASE 3: Bitcoin Metrics

### Goal
Add Bitcoin network indicators: Hash Rate, Funding Rate, Open Interest, ETF Flows.

### API Endpoints to Create

#### `routes/btc_metrics.py` (NEW FILE)

```python
# GET /api/market/btc-metrics
# Returns:
{
    "hash_rate": "650 EH/s",
    "hash_rate_change_7d": "+2.3%",
    "funding_rate": "0.0123%",
    "open_interest": "$25.4B",
    "etf_net_flow": "+$125M",
    "miner_revenue": "$45M",
    "timestamp": "..."
}
```

#### `routes/etf_data.py` (NEW FILE)

```python
# GET /api/market/etf-flows
# Returns:
{
    "btc_etf_total_aum": "$35.2B",
    "btc_etf_net_flow_24h": "+$125M",
    "btc_etf_net_flow_7d": "+$450M",
    "historical": [...]
}
```

### External APIs Needed

| Data | API Source | Endpoint |
|------|------------|----------|
| Hash Rate | blockchain.com | `https://blockchain.info/q/hashrate` |
| Funding Rate | Binance Futures | `/fapi/v1/premiumIndex` |
| Open Interest | Binance Futures | `/fapi/v1/openInterest` |
| ETF Flows | public APIs | Various sources |

### UI Components to Add

Add new panel in `templates/dashboard.html`:

```html
<!-- BTC Metrics Panel -->
<div class="panel btc-metrics">
    <div class="panel-title">Bitcoin Metrics</div>
    
    <div class="metric-row">
        <span class="metric-label">Hash Rate</span>
        <span class="metric-value" id="hash-rate">--</span>
    </div>
    <div class="metric-row">
        <span class="metric-label">Funding Rate</span>
        <span class="metric-value" id="funding-rate">--</span></div>
    <div class="metric-row">
        <span class="metric-label">Open Interest</span>
        <span class="metric-value" id="open-interest">--</span>
    </div>
    <div class="metric-row">
        <span class="metric-label">BTC ETF Flow (24h)</span>
        <span class="metric-value" id="etf-flow">--</span>
    </div>
</div>
```

### CSS for `static/style.css`

```css
/* BTC Metrics Panel */
.btc-metrics .metric-row {
    display: flex;
    justify-content: space-between;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border);
}

.btc-metrics .metric-label {
    color: var(--text-secondary);
}

.btc-metrics .metric-value {
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}

.btc-metrics .metric-value.positive { color: var(--accent-green); }
.btc-metrics .metric-value.negative { color: var(--accent-red); }
```

### JavaScript for `static/app.js`

```javascript
async function refreshBTCMetrics() {
    const data = await apiFetch('/api/market/btc-metrics');
    if (!data) return;
    
    document.getElementById('hash-rate').textContent = data.hash_rate;
    document.getElementById('funding-rate').textContent = data.funding_rate;
    document.getElementById('open-interest').textContent = data.open_interest;
    document.getElementById('etf-flow').textContent = data.etf_net_flow;
}
```

---

## PHASE 4: Global Indicators

### Goal
Add external market data: DXY (Dollar Index), S&P 500, Gold, US10Y Yield.

### API Endpoints to Create

#### `routes/external_markets.py` (NEW FILE)

```python
# GET /api/market/external
# Returns:
{
    "dxy": {"price": 104.5, "change_24h": "+0.2%"},
    "sp500": {"price": 5200, "change_24h": "-0.5%"},
    "gold": {"price": 2340, "change_24h": "+0.8%"},
    "us10y_yield": {"price": "4.25%", "change_24h": "+0.03%"},
    "btc_correlation": "Negative (DXY up = BTC down)",
    "timestamp": "..."
}
```

### External APIs Needed

| Data | API Source | Endpoint |
|------|------------|----------|
| DXY | Yahoo Finance | `GC=F` (Gold), `DX-Y.NXB` (DXY) |
| S&P 500 | Yahoo Finance | `^GSPC` |
| Gold | Yahoo Finance | `GC=F` |
| US10Y Yield | Yahoo Finance | `^TNX` |

### UI Components to Add

```html
<!-- External Indicators Panel -->
<div class="panel external-markets">
    <div class="panel-title">Global Indicators</div>
    
    <div class="indicator-row">
        <span class="indicator-name">DXY (USD Index)</span>
        <span class="indicator-value" id="dxy-price">--</span>
        <span class="indicator-change" id="dxy-change">--</span>
    </div>
    <div class="indicator-row">
        <span class="indicator-name">S&P 500</span>
        <span class="indicator-value" id="sp500-price">--</span>
        <span class="indicator-change" id="sp500-change">--</span>
    </div>
    <div class="indicator-row">
        <span class="indicator-name">Gold</span>
        <span class="indicator-value" id="gold-price">--</span>
        <span class="indicator-change" id="gold-change">--</span>
    </div>
    <div class="indicator-row">
        <span class="indicator-name">US 10Y Yield</span>
        <span class="indicator-value" id="us10y-price">--</span>
        <span class="indicator-change" id="us10y-change">--</span>
    </div>
    
    <div class="correlation-box">
        <div class="panel-title" style="font-size:0.65rem;margin-top:0.5rem;">BTC Correlation</div>
        <div id="btc-correlation-text">Loading...</div>
    </div>
</div>
```

### Implementation Notes

Use Yahoo Finance via `yfinance` Python package:
```python
import yfinance as yf

def get_dxy():
    dxy = yf.Ticker("DX-Y.NXB")
    hist = dxy.history(period="1d")
    return hist['Close'].iloc[-1]
```

---

## PHASE 5: Advanced — Charts & History

### Goal
Add visualization with lightweight charts.

### Tasks

1. **Add Chart.js library** to `templates/dashboard.html`:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

2. **Create price history endpoint**:
```python
# GET /api/market/price-history?symbol=BTCUSDT&days=7
# Returns:
{
    "symbol": "BTCUSDT",
    "data": [
        {"time": "2026-03-27", "price": 65000},
        {"time": "2026-03-28", "price": 65500},
        ...
    ]
}
```

3. **Add sparkline charts** to watchlist items:
```javascript
// Mini 7d chart per coin
new Chart(ctx, {
    type: 'line',
    data: {...},
    options: {
        responsive: false,
        width: 100,
        height: 30,
        plugins: {legend: {display: false}}
    }
})
```

4. **Add historical chart modal** for detailed view:
```html
<!-- Price History Modal -->
<div class="modal-overlay" id="history-chart-modal">
    <div class="modal" style="max-width:700px;">
        <div class="modal-header">
            <h2 id="chart-coin-name">BTC/USDT</h2>
            <button class="modal-close" onclick="closeHistoryChartModal()">✕</button>
        </div>
        <div class="modal-body">
            <canvas id="price-history-chart"></canvas>
            <div class="timeframe-buttons">
                <button onclick="loadChart('1w')">7D</button>
                <button onclick="loadChart('1m')">30D</button>
                <button onclick="loadChart('3m')">90D</button>
            </div>
        </div>
    </div>
</div>
```

5. **Add BTC Dominance history chart**

6. **Add price alert configuration**:
```html
<!-- Alert Config Modal -->
<div class="control-group">
    <div class="control-label">Alert Price (Above)</div>
    <input type="number" id="alert-above" placeholder="70000">
</div>
<div class="control-group">
    <div class="control-label">Alert Price (Below)</div>
    <input type="number" id="alert-below" placeholder="60000">
</div>
```

---

## File Structure (Final)

```
trading-dashboard/
├── app.py
├── routes/
│   ├── market.py              ✅ Already done (Phase 1-2)
│   ├── btc_metrics.py         🔴 NEW (Phase 3)
│   ├── etf_data.py           🔴 NEW (Phase 3)
│   └── external_markets.py    🔴 NEW (Phase 4)
├── templates/
│   └── dashboard.html        ✅ Phase 1-2 done, need Phase 3-5 panels
├── static/
│   ├── style.css              ✅ Phase 1-2 done, need Phase 3-5 styles
│   └── app.js                 ✅ Phase 1-2 done, need Phase 3-5 refresh fn
├── services/
│   └── external_data.py       🔴 NEW (helper for external APIs)
└── config/
    └── watchlist.json         ✅ Already exists
```

---

## Dependencies to Install

Add to `requirements.txt`:
```
yfinance>=0.2.28
pandas>=2.0.0
```

---

## Current System State

### Routes (`routes/`)
| File | Phase | Status |
|------|-------|--------|
| `auth.py` | System | ✅ Done |
| `binance.py` | System | ✅ Done |
| `bot_control.py` | System | ✅ Done |
| `config.py` | System | ✅ Done |
| `learning.py` | System | ✅ Done |
| `market.py` | 1-2 | ✅ Done (fixed 2026-04-03) |
| `performance.py` | System | ✅ Done |
| `signals.py` | System | ✅ Done |
| `telegram.py` | System | ✅ Done |
| `btc_metrics.py` | 3 | 🔴 TODO |
| `etf_data.py` | 3 | 🔴 TODO |
| `external_markets.py` | 4 | 🔴 TODO |

### Strategies (`strategies/`)
| File | Status |
|------|--------|
| `signal_engine.py` | ✅ Done (Wilder RSI, EMA, ATR, VWAP, Confidence V2) |
| `screener.py` | ✅ Done (pre-filter coins) |
| `lessons.py` | ✅ Done (pattern recognition) |
| `evolution.py` | ✅ Done (auto threshold tuning) |

### Services (`services/`)
| File | Status |
|------|--------|
| `auth.py` | ✅ Done |
| `binance_client.py` | ✅ Done (semi-auto trading) |
| `telegram_notifier.py` | ✅ Done |

---

## Testing Checklist

Before finishing each phase, verify:

- [ ] API returns valid JSON
- [ ] UI displays data correctly
- [ ] No console errors
- [ ] Auto-refresh works
- [ ] Mobile responsive
- [ ] Cache TTL working (no excessive API calls)
- [ ] Error handling (graceful fallback on API failure)

---

## Commit History (Recent)

```
e7267f9 fix: Phase 2 - populate market cap and 24h change from /api/market/global
82301ad fix: Phase 1-2 cache logic, separate TTL per data type, import at module level
61b11a4 docs: Add MARKET_DATA_PLAN.md for Antigravity handoff
a43b86b fix: All market data now real-time
c493190 feat: Add Binance settings UI with tabbed modal
8bde5a3 feat: Add Binance API client and routes for semi-auto trading
968640f feat: Add coin screener, update README & AGENT.md status
b577452 feat: Learning system with lessons & evolution (Priority 4)
9ddadf1 feat: Bot scheduler with APScheduler
5513966 feat: Signal engine with Wilder RSI
721de35 feat: Complete dashboard UI
b8fbe7c feat: Add password protection to dashboard
376bb9e feat: Add Telegram notification system
f72dec3 Initial commit: TradingCore Dashboard Phase 1
```

---

## Questions?

Check existing code in `routes/market.py` for patterns to follow.

---

**Commit format:** `feat: Phase X - [description]`