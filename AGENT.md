# TradingCore Dashboard — Agent Instructions

## Objective

Build a complete TradingCore Dashboard web application based on the specification in `docs/SPEC.md`.

## Project Overview

A Flask-based cryptocurrency trading dashboard with:
- Dark-themed interactive UI
- Real-time market data (Fear & Greed, BTC Dominance)
- Trading signals display
- Bot start/stop controls
- Performance tracking

## Repository Structure

```
trading-dashboard/
├── README.md              ← Project overview
├── CONTRIBUTING.md        ← Development guide
├── AGENT.md              ← THIS FILE — Agent instructions
├── docs/SPEC.md          ← Detailed specification
├── requirements.txt       ← Python dependencies
├── app.py                ← Flask application entry point
├── config/
│   ├── bot_config.json   ← Trading parameters (40+ settings)
│   └── bot_status.json   ← Bot running state
├── routes/
│   ├── bot_control.py    ← /api/bot/start, /api/bot/stop, /api/bot/status
│   ├── signals.py        ← /api/signals, /api/signals/<id>
│   ├── market.py         ← /api/market/pulse, /api/market/fear-greed
│   ├── performance.py    ← /api/performance, /api/performance/history
│   └── config.py         ← /api/config (GET/PUT)
├── templates/
│   └── dashboard.html    ← Main dashboard UI (PRIMARY TARGET)
├── static/               ← Static assets (empty, to be created)
├── strategies/
│   └── signal_engine.py  ← Trading signal calculation (to be created)
├── data/
│   └── trades.json       ← Trade history (auto-created)
└── tests/                ← Unit tests (to be created)
```

## Your Tasks (in order)

### Task 1: Complete the Dashboard HTML

**File:** `templates/dashboard.html`

The file exists but needs enhancement. Improve it to match SPEC.md exactly:

**Required Sections:**
1. **Header Bar** — Bot status (pulsing green dot when active), title, START/STOP buttons
2. **Market Pulse Panel** — Fear & Greed gauge, BTC Dominance %, BTC Trend arrow, Trending coins
3. **Live Signals Panel** — Scrollable list of BUY/SELL signal cards
4. **Bot Controls Panel** — All dropdowns for: Mode, Interval, Coin Pool, Min R:R, Min Confidence
5. **Performance Tracker Footer** — Stats bar with Total/Win/Loss/Win Rate/Best/Worst + action buttons

**Color Scheme (MUST USE):**
- Background: `#0a0e1a`
- Card bg: `#111827`
- Accent Green: `#00ff9d`
- Accent Red: `#ff4757`
- Accent Yellow: `#ffd700`
- Text Primary: `#e2e8f0`
- Text Secondary: `#64748b`
- Border: `#1e293b`

**API Endpoints to Connect:**
- `GET /api/market/pulse` — Market data
- `GET /api/signals` — Trading signals
- `GET /api/bot/status` — Bot running state
- `POST /api/bot/start` — Start bot
- `POST /api/bot/stop` — Stop bot
- `GET /api/performance` — Performance stats
- `GET /api/config` — Current config
- `POST /api/config` — Update config

**Signal Card Layout:**
```
┌─────────────────────────────────────┐
│ BTC/USDT            [BUY] green   │
│ RSI: 28  Conf: 72%  Entry: $98240│
│ SL: -2.5%  TP: +7.5%  R:R: 1:3.0  │
└─────────────────────────────────────┘
```

### Task 2: Add Static Assets

**Create `static/style.css`:**
- Extract and organize CSS from dashboard.html
- Add responsive design
- Add hover states for buttons and cards

**Create `static/app.js`:**
- API call functions (fetch wrappers)
- Polling mechanism (refresh every 30 seconds)
- Error handling
- Loading states

### Task 3: Create Signal Engine

**File:** `strategies/signal_engine.py`

Implement the trading signal pipeline from SPEC.md:

```python
def calculate_rsi_wilder(closes, period=14):
    """Wilder's Smoothed RSI — same as TradingView"""
    # Implementation required
    pass

def calculate_ema(prices, period):
    """Exponential Moving Average"""
    pass

def calculate_atr(highs, lows, closes, period=14):
    """Average True Range"""
    pass

def analyze_coin(symbol, config):
    """
    Main analysis function.
    Returns: signal dict with side, rsi, confidence, entry, sl, tp, rr
    """
    pass

def run_scan(config):
    """
    Scan all coins and return signals.
    Filter by min_rr, min_confidence.
    """
    pass
```

### Task 4: Create the Screening Module

**File:** `strategies/screener.py`

```python
def get_top_coins(limit=20, min_volume=5_000_000):
    """Get top coins by volume from CoinGecko"""
    pass

def filter_by_volume(coins, min_volume):
    """Filter coins by minimum 24h volume"""
    pass
```

### Task 5: Add Unit Tests

**File:** `tests/test_signal_engine.py`

Test:
- RSI calculation (known values)
- EMA calculation
- Signal generation with mock data
- Config validation

## Execution Steps

1. **Read** `docs/SPEC.md` thoroughly
2. **Read** `CONTRIBUTING.md` for frontend guidelines
3. **Read** existing `templates/dashboard.html` to understand current state
4. **Enhance** dashboard.html to match spec exactly
5. **Create** `static/style.css` and `static/app.js`
6. **Implement** `strategies/signal_engine.py`
7. **Implement** `strategies/screener.py`
8. **Add** basic tests in `tests/`
9. **Test** locally: `python app.py` → open `http://localhost:5000`
10. **Verify** all API endpoints work
11. **Commit** with meaningful message
12. **Push** to main branch

## Quality Standards

- All API endpoints must return valid JSON
- Dashboard must be responsive (mobile-friendly)
- Dark theme must match color scheme exactly
- Signal cards must clearly distinguish BUY (green) vs SELL (red)
- Bot status must update in real-time
- All dropdowns must be functional

## Verification Checklist

Before finishing, verify:

- [ ] Dashboard loads at `http://localhost:5000`
- [ ] Market Pulse shows Fear & Greed value
- [ ] Signals display in cards with correct colors
- [ ] Bot START/STOP buttons work
- [ ] Config dropdowns change values
- [ ] Performance stats display
- [ ] No console errors
- [ ] Responsive on mobile width

## Questions?

If anything is unclear, check SPEC.md first. The specification is the source of truth.

---

**Commit format:** `feat: [description]` or `fix: [description]`
