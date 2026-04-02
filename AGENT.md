# TradingCore Dashboard — Agent Instructions for Antigravity

## Objective

Build a complete **TradingCore Dashboard** — a Flask-based cryptocurrency trading platform with web UI, real-time signals, bot control, and Telegram notifications.

**This is a MODULAR project** — build step by step, commit often.

---

## Repository

```
https://github.com/jeprix-cloud/trading-dashboard
git@github.com:jeprix-cloud/trading-dashboard.git
```

---

## Current State

✅ **Already Built (Foundation):**
- Flask app with all API routes
- Login/password protection
- Telegram notification API (service ready, UI needed)
- Basic config management
- Dark-themed HTML template (basic)

✅ **Completed by Antigravity Agent:**
- Full interactive dashboard UI (`templates/dashboard.html`, `static/style.css`, `static/app.js`)
- Signal engine — Wilder RSI, EMA, ATR, VWAP, Confidence V2 (`strategies/signal_engine.py`)
- Coin screener — pre-filter & rank coins before scan (`strategies/screener.py`)
- Bot scheduler — APScheduler with start/stop/Telegram alerts (`routes/bot_control.py`)
- Learning system — pattern recognition & auto-blacklist (`strategies/lessons.py`)
- Evolution system — adaptive threshold tuning (`strategies/evolution.py`)
- Learning API — 8 endpoints under `/api/learning` (`routes/learning.py`)
- Settings modal — Telegram config & test from dashboard
- Performance tracker — LOG OUTCOME, VIEW HISTORY, RUN BACKTEST, EVOLVE
- Evolution modal — UI to view & apply evolved thresholds

**All 4 Priorities: COMPLETE ✅**


---

## Task Priority

### 🔴 PRIORITY 1: Dashboard UI (MOST IMPORTANT)

**Goal:** Full interactive web dashboard matching the spec exactly.

#### File: `templates/dashboard.html`

**Design Spec:**
```
Background:      #0a0e1a (deep navy)
Card background: #111827
Accent Green:    #00ff9d
Accent Red:      #ff4757
Accent Yellow:   #ffd700
Text Primary:    #e2e8f0
Text Secondary:  #64748b
Border:          #1e293b
```

#### Layout Structure:

```
┌─────────────────────────────────────────────────────────────────┐
│  [●] TradingCore Dashboard        [■ STOP BOT] [▶ START BOT] │
├──────────────┬──────────────────────────────┬─────────────────┤
│ MARKET PULSE │      LIVE SIGNALS              │  BOT CONTROLS  │
│              │                              │                 │
│ F&G: 42      │  ┌─────────────────────────┐ │  Mode: [▼]     │
│ (gauge)      │  │ BTC/USDT    [BUY]       │ │  Interval: [▼] │
│              │  │ RSI: 28  Conf: 72%      │ │  Coins: [▼]   │
│ BTC Dom: 52% │  │ Entry: $98,240          │ │  Min R:R: [▼] │
│ BTC Trend: ↑  │  │ SL: -2.5% TP: +7.5%    │ │  Min Conf: [▼]│
│              │  │ R:R: 1:3.0               │ │                 │
│ Trending:    │  └─────────────────────────┘ │  [▶ START BOT] │
│ SOL BNB ETH  │                              │                 │
├──────────────┴──────────────────────────────┴─────────────────┤
│  PERFORMANCE TRACKER                                           │
│  Total: 2  |  Win: 1  |  Loss: 1  |  Win Rate: 50%         │
│  Best: +6.41% (SOL)  |  Worst: -3.26% (BNB)                  │
│  [LOG OUTCOME] [VIEW HISTORY] [RUN BACKTEST] [EVOLVE]         │
└───────────────────────────────────────────────────────────────┘
```

#### UI Components Required:

**1. Header Bar**
- Pulsing green dot (active) / grey dot (stopped) with CSS animation
- "TradingCore Dashboard" title
- START/STOP buttons (toggle based on state)

**2. Market Pulse Panel (left column)**
- Fear & Greed value with color (red < 30, yellow 30-60, green > 60)
- F&G label: "Extreme Fear" / "Fear" / "Greed" / "Extreme Greed"
- BTC Dominance percentage
- BTC Trend arrow (↑ bullish / ↓ bearish)
- Trending coins list (top 3)

**3. Live Signals Panel (center column)**
- Scrollable list of signal cards
- BUY cards: green left border (`border-left: 3px solid #00ff9d`)
- SELL cards: red left border (`border-left: 3px solid #ff4757`)
- Card contents:
  - Symbol (BTC/USDT, ETH/USDT, etc.)
  - Side badge: BUY (green) or SELL (red)
  - RSI value
  - Confidence percentage
  - Entry price
  - Stop Loss %
  - Take Profit %
  - R:R ratio

**4. Bot Controls Panel (right column)**
- Mode dropdown: SWING / SCALP / BOTH
- Interval dropdown: 5m / 15m / 30m / 1h
- Coins dropdown: Top 10 / 20 / 50
- Min R:R dropdown: 1.5 / 2.0 / 2.5 / 3.0
- Min Confidence dropdown: 30% / 50% / 70%
- START BOT button (full width, green)
- SETTINGS button (for Telegram config)

**5. Performance Tracker (bottom bar)**
- Stats: Total | Win | Loss | Win Rate | Best | Worst
- Action buttons: LOG OUTCOME | VIEW HISTORY | RUN BACKTEST | EVOLVE

**6. Settings Modal (for Telegram)**
- Bot Token input (password field)
- Chat ID input
- Test Connection button
- Send Test Signal button
- Connection status indicator

#### API Integration:

```javascript
// Fetch data
GET /api/market/pulse      → Market data (F&G, BTC Dom, trending)
GET /api/signals            → Trading signals array
GET /api/bot/status         → Bot running state
GET /api/performance        → Win rate, trade stats
GET /api/config             → Current config

// Actions
POST /api/bot/start         → { success: true }
POST /api/bot/stop          → { success: true, session_stats: {...} }
POST /api/config            → Update config

// Telegram
GET /api/telegram/status    → { configured: true/false }
POST /api/telegram/test     → Test + save credentials
POST /api/telegram/send-test-signal → Send test notification
```

#### JavaScript Requirements:

```javascript
// Auto-refresh every 30 seconds
setInterval(refreshAll, 30000);

// Bot status polling
async function checkBotStatus() {
    const res = await fetch('/api/bot/status');
    const data = await res.json();
    updateBotStatus(data); // Update dot color, buttons
}

// Signal polling
async function refreshSignals() {
    const res = await fetch('/api/signals');
    const data = await res.json();
    renderSignalCards(data.signals);
}

// Market polling
async function refreshMarket() {
    const res = await fetch('/api/market/pulse');
    const data = await res.json();
    updateMarketPulse(data);
}

// Performance polling
async function refreshPerformance() {
    const res = await fetch('/api/performance');
    const data = await res.json();
    updateStats(data);
}

// Start/Stop handlers
document.getElementById('start-btn').addEventListener('click', () => {
    fetch('/api/bot/start', { method: 'POST' });
    // Update UI immediately
    setBotStatus('running');
});
```

---

### 🔴 PRIORITY 2: Signal Engine

**File:** `strategies/signal_engine.py`

#### Wilder's RSI (REQUIRED — same as TradingView/Binance):

```python
def calculate_rsi_wilder(closes, period=14):
    """
    Wilder's Smoothed RSI
    NOT simple moving average — this is critical
    """
    deltas = []
    for i in range(1, len(closes)):
        deltas.append(closes[i] - closes[i-1])
    
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    # Initial average
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    # Wilder smoothing
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    
    rs = avg_gain / avg_loss if avg_loss > 0 else 0
    return 100 - (100 / (1 + rs))
```

#### EMA Calculation:

```python
def calculate_ema(prices, period):
    """Exponential Moving Average"""
    ema = sum(prices[:period]) / period
    multiplier = 2 / (period + 1)
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return ema
```

#### ATR (Average True Range):

```python
def calculate_atr(highs, lows, closes, period=14):
    """True Range = max(H-L, |H-PC|, |L-PC|)"""
    trs = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i-1]),
            abs(lows[i] - closes[i-1])
        )
        trs.append(tr)
    
    # Wilder smoothing for ATR
    atr = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr = (atr * (period - 1) + trs[i]) / period
    return atr
```

#### VWAP:

```python
def calculate_vwap(closes, volumes):
    """Volume Weighted Average Price"""
    cum_vol = sum(volumes)
    if cum_vol == 0:
        return sum(closes) / len(closes)
    cum_pv = sum(c * v for c, v in zip(closes, volumes))
    return cum_pv / cum_vol
```

#### Confidence Score V2 (100-point system):

```python
def calculate_confidence(rsi, rr_ratio, volume_ratio, macro_score, multitf_aligned, trending):
    """
    Confidence Score V2
    Max 100 points
    """
    score = 0
    
    # RSI quality (25 pts max)
    if rsi < 25 or rsi > 75:
        score += 25
    elif rsi < 30 or rsi > 70:
        score += 20
    elif rsi < 35 or rsi > 65:
        score += 12
    elif 35 <= rsi <= 40 or 60 <= rsi <= 65:
        score += 5  # WARNING ZONE
    else:
        score += 0
    
    # R:R bonus (20 pts max)
    if rr_ratio >= 3.0:
        score += 20
    elif rr_ratio >= 2.5:
        score += 15
    elif rr_ratio >= 2.0:
        score += 10
    
    # Volume (15 pts max)
    if volume_ratio >= 2.0:
        score += 15
    elif volume_ratio >= 1.5:
        score += 10
    elif volume_ratio >= 1.0:
        score += 5
    
    # Macro alignment (20 pts max)
    if macro_score >= 80:
        score += 20
    elif macro_score >= 60:
        score += 15
    elif macro_score >= 40:
        score += 10
    else:
        score += 5
    
    # Multi-TF confirmation (10 pts)
    if multitf_aligned:
        score += 10
    
    # Trending bonus (10 pts)
    if trending:
        score += 10
    
    return min(score, 100)
```

#### Main Signal Generation:

```python
def analyze_coin(symbol, config, market_data):
    """
    Main analysis for one coin
    Returns signal dict or None
    """
    # Fetch OHLCV data from Binance
    # Calculate RSI, EMA, ATR, VWAP
    # Check filters (EMA200, F&G, etc.)
    # Calculate confidence score
    # Return signal if meets criteria
    pass

def run_scan(config, market_data):
    """
    Scan all configured coins
    Filter by min_rr, min_confidence
    Return signals sorted by confidence
    """
    coins = get_top_coins(config['coin_pool'])
    signals = []
    
    for coin in coins:
        signal = analyze_coin(coin, config, market_data)
        if signal:
            signals.append(signal)
    
    # Filter
    signals = [s for s in signals if s['rr'] >= config['min_rr']]
    signals = [s for s in signals if s['confidence'] >= config['min_confidence']]
    
    # Sort by confidence
    signals.sort(key=lambda x: x['confidence'], reverse=True)
    
    return signals
```

---

### 🔴 PRIORITY 3: Bot Scheduler

**File:** `routes/bot_control.py` (enhance existing)

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = BackgroundScheduler()
scheduler.start()

def start_bot_handler():
    """Start scheduled scans"""
    config = read_config()
    interval_map = {
        '5m': 5,
        '15m': 15,
        '30m': 30,
        '1h': 60
    }
    minutes = interval_map.get(config['interval'], 15)
    
    # Schedule recurring scan
    def scan_job():
        signals = run_scan(config, get_market_data())
        save_signals(signals)
        # Send Telegram alerts for new signals
    
    scheduler.add_job(
        scan_job,
        trigger=IntervalTrigger(minutes=minutes),
        id='trading_scan',
        name='Trading Scan',
        replace_existing=True
    )
    
    # Run immediately
    scan_job()

def stop_bot_handler():
    """Stop scheduled scans"""
    scheduler.remove_job('trading_scan')
```

---

### 🟡 PRIORITY 4: Learning System (Can do later)

**Files:** `strategies/lessons.py`, `strategies/evolution.py`

```python
# lessons.json structure
{
    "patterns": [
        {
            "pattern": "F&G<30_AND_RSI<30",
            "occurrences": 5,
            "wins": 4,
            "avg_pnl": 5.2,
            "win_rate": 80
        }
    ],
    "blacklist": ["RSI_35_40_ZONE"]
}

def load_lessons():
    """Load from data/lessons.json"""

def apply_lessons(signals, lessons):
    """Adjust confidence based on learned patterns"""

def evolve_thresholds(history):
    """Adjust RSI/FG thresholds based on historical performance"""
```

---

## File Structure to Create/Modify

```
trading-dashboard/
├── templates/
│   └── dashboard.html          ← ENHANCE (Priority 1)
├── static/
│   ├── style.css               ← CREATE (Priority 1)
│   └── app.js                  ← CREATE (Priority 1)
├── strategies/
│   ├── signal_engine.py        ← CREATE (Priority 2)
│   ├── screener.py            ← CREATE (Priority 2)
│   ├── lessons.py              ← CREATE (Priority 4)
│   └── evolution.py            ← CREATE (Priority 4)
├── data/
│   ├── lessons.json           ← CREATE (auto)
│   └── thresholds.json         ← CREATE (auto)
└── routes/
    └── bot_control.py          ← ENHANCE (Priority 3)
```

---

## Execution Steps

### Step 1: Read
```
1. Read this AGENT.md completely
2. Read docs/SPEC.md for full specifications
3. Read existing templates/dashboard.html
4. Read existing routes/*.py to understand structure
```

### Step 2: Priority 1 — Dashboard UI
```
1. Enhance templates/dashboard.html to match layout exactly
2. Create static/style.css with all styles
3. Create static/app.js with API calls and polling
4. Add Settings modal for Telegram
5. Test: python app.py → open http://localhost:5000
6. Verify all panels display correctly
7. Commit: "feat: Complete dashboard UI"
```

### Step 3: Priority 2 — Signal Engine
```
1. Create strategies/signal_engine.py
2. Implement RSI Wilder, EMA, ATR, VWAP
3. Implement confidence scoring
4. Implement analyze_coin() and run_scan()
5. Test with mock data
6. Commit: "feat: Signal engine with Wilder RSI"
```

### Step 4: Priority 3 — Bot Scheduler
```
1. Install apscheduler: pip install apscheduler
2. Enhance routes/bot_control.py
3. Add APScheduler for recurring scans
4. Connect to Telegram for alerts
5. Test start/stop
6. Commit: "feat: Bot scheduler with APScheduler"
```

### Step 5: Priority 4 — Learning (optional)
```
1. Create strategies/lessons.py
2. Create strategies/evolution.py
3. Implement pattern recognition
4. Implement threshold evolution
5. Commit: "feat: Learning system"
```

---

## Testing Checklist

- [ ] Dashboard loads at http://localhost:5000
- [ ] Login page appears, password works
- [ ] Market Pulse shows F&G, BTC Dom, Trending
- [ ] Signals display as cards with correct colors
- [ ] Bot START/STOP buttons work
- [ ] Bot status indicator updates (green/grey dot)
- [ ] Config changes persist
- [ ] Telegram test connection works
- [ ] No console errors
- [ ] Responsive on mobile width

---

## Important Notes

1. **RSI must be Wilder's method** — simple moving average is WRONG
2. **Commit often** — every completed task, push to GitHub
3. **Test locally first** — before pushing, run `python app.py` and verify
4. **Error handling** — all API calls should handle errors gracefully
5. **Dark theme only** — no light theme, spec explicitly says dark

---

## Questions?

If anything is unclear in the spec, check `docs/SPEC.md` first. That is the source of truth.

For implementation details, check existing code in `routes/` to match patterns.

---

**Commit format:** `feat: [description]` or `fix: [description]`
