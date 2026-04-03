# Phase 1: Foundation — Execution Guide for AI Agents

## READ THIS FIRST

This is a step-by-step execution guide for building TradingCore Phase 1.
**Follow tasks IN ORDER. Do NOT skip ahead. Test after each task.**

### Project Context
- **Framework:** Flask (Python) — see `app.py` for entry point
- **Frontend:** Vanilla HTML/JS/CSS — single page in `templates/dashboard.html`
- **Current state:** Dashboard UI, Signal Engine, Bot Scheduler, Learning System — all working
- **Goal:** Add SQLite DB, flexible strategies, real backtest, position tracking, semi-auto execution, risk management

### Key Files to Read Before Starting
1. `app.py` — Flask app, blueprint registration
2. `routes/market.py` — Example of route pattern (Blueprint, `@require_auth`, JSON responses)
3. `strategies/signal_engine.py` — Core indicator calculations (RSI, EMA, ATR, VWAP)
4. `services/binance_client.py` — Binance API client pattern
5. `config/bot_config.json` — All configuration (testnet keys already saved here)
6. `routes/bot_control.py` — APScheduler pattern, scan_job()

### Code Patterns to Follow
```python
# Route pattern (see routes/market.py):
from flask import Blueprint, jsonify, request
from services.auth import require_auth

example_bp = Blueprint('example', __name__)

@example_bp.route('/endpoint', methods=['GET'])
@require_auth
def get_example():
    return jsonify({'key': 'value'})
```

```python
# Register blueprint in app.py:
from routes.example import example_bp
app.register_blueprint(example_bp, url_prefix='/api/example')
```

### Binance Testnet Config
- Testnet Spot URL: `https://testnet.binance.vision`
- Testnet Futures URL: `https://testnet.binancefuture.com`
- API keys are in `config/bot_config.json` under `testnet_api_key` and `testnet_secret_key`
- `use_testnet: true` means use testnet URLs

### Commit Convention
After each sub-phase: `git add -A && git commit -m "feat: Phase 1.X - [description]"`

---

## SUB-PHASE 1.1: SQLite Database + Testnet Config

### Task 1.1.1: Create `services/database.py`

**Create file:** `services/database.py`

**Requirements:**
- Use Python's built-in `sqlite3` module (no extra dependencies)
- Database file location: `data/trading.db`
- Thread-safe: use `check_same_thread=False`
- Create all tables on init

**Tables to create:**

```sql
CREATE TABLE IF NOT EXISTS strategies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    coins TEXT NOT NULL,
    mode TEXT DEFAULT 'SWING',
    timeframe TEXT DEFAULT '15m',
    entry_conditions TEXT NOT NULL,
    exit_conditions TEXT NOT NULL,
    entry_logic TEXT DEFAULT 'AND',
    exit_logic TEXT DEFAULT 'OR',
    sl_pct REAL DEFAULT 2.5,
    tp_pct REAL DEFAULT 7.5,
    sl_mode TEXT DEFAULT 'FIXED',
    atr_multiplier REAL DEFAULT 1.5,
    min_confidence INTEGER DEFAULT 50,
    min_rr REAL DEFAULT 2.0,
    is_active INTEGER DEFAULT 0,
    is_template INTEGER DEFAULT 0,
    exchange TEXT DEFAULT 'spot',
    leverage INTEGER DEFAULT 1,
    backtest_win_rate REAL,
    backtest_pnl REAL,
    total_trades INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS signals (
    id TEXT PRIMARY KEY,
    strategy_id TEXT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    exchange TEXT DEFAULT 'spot',
    rsi REAL,
    confidence INTEGER,
    entry_price REAL,
    sl_pct REAL,
    tp_pct REAL,
    rr_ratio REAL,
    atr REAL,
    vwap REAL,
    volume_ratio REAL,
    mode TEXT,
    pattern TEXT,
    indicators_json TEXT,
    status TEXT DEFAULT 'ACTIVE',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id TEXT,
    strategy_id TEXT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    exchange TEXT DEFAULT 'spot',
    entry_price REAL NOT NULL,
    quantity REAL NOT NULL,
    position_value_usd REAL,
    sl_price REAL,
    tp_price REAL,
    sl_pct REAL,
    tp_pct REAL,
    exit_price REAL,
    pnl_pct REAL,
    pnl_usd REAL,
    status TEXT DEFAULT 'OPEN',
    order_id TEXT,
    sl_order_id TEXT,
    tp_order_id TEXT,
    opened_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    closed_at DATETIME,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS backtests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id TEXT,
    name TEXT,
    symbol TEXT,
    timeframe TEXT,
    start_date TEXT,
    end_date TEXT,
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    win_rate REAL,
    total_pnl_pct REAL,
    max_drawdown_pct REAL,
    sharpe_ratio REAL,
    avg_trade_pnl REAL,
    best_trade_pnl REAL,
    worst_trade_pnl REAL,
    config_json TEXT,
    trades_json TEXT,
    equity_curve_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_performance (
    date DATE PRIMARY KEY,
    total_trades INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    win_rate REAL DEFAULT 0,
    pnl_pct REAL DEFAULT 0,
    pnl_usd REAL DEFAULT 0,
    max_drawdown_pct REAL DEFAULT 0,
    balance_usd REAL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS risk_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    daily_loss_usd REAL DEFAULT 0,
    daily_loss_pct REAL DEFAULT 0,
    daily_trades INTEGER DEFAULT 0,
    weekly_loss_usd REAL DEFAULT 0,
    weekly_loss_pct REAL DEFAULT 0,
    is_circuit_breaker_active INTEGER DEFAULT 0,
    last_reset_date DATE,
    last_reset_week DATE
);
```

**Functions to implement:**
```python
def get_db_path():
    """Return absolute path to data/trading.db"""

def get_db():
    """Get thread-safe database connection. Returns sqlite3.Connection with row_factory=sqlite3.Row"""

def init_db():
    """Create all tables if not exists. Call this on app startup."""

def migrate_json_to_sqlite():
    """
    One-time migration: read data/trades.json, data/signals.json, data/lessons.json
    and import into SQLite tables. Skip if already migrated.
    """
```

**Test:** `cd trading-dashboard && python -c "from services.database import init_db; init_db(); print('DB OK')"`

### Task 1.1.2: Update `app.py` to init database

**Modify:** `app.py`

Add after `app = Flask(__name__)`:
```python
from services.database import init_db
init_db()
```

**Test:** `python app.py` — should start without errors and create `data/trading.db`

### Task 1.1.3: Update `services/binance_client.py` for testnet toggle

**Modify:** `services/binance_client.py`

Add testnet support to `BinanceClient.__init__`:
```python
def __init__(self, api_key, secret_key, testnet=False):
    self.api_key = api_key
    self.secret_key = secret_key
    if testnet:
        self.base_url = "https://testnet.binance.vision"
    else:
        self.base_url = "https://api.binance.com"
```

Add helper to load client from config:
```python
@staticmethod
def from_config():
    """Create client from bot_config.json, auto-detect testnet"""
    import json, os
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'bot_config.json')
    with open(config_path) as f:
        config = json.load(f)
    
    use_testnet = config.get('use_testnet', True)
    if use_testnet:
        api_key = config.get('testnet_api_key', '')
        secret_key = config.get('testnet_secret_key', '')
    else:
        api_key = config.get('binance_api_key', '')
        secret_key = config.get('binance_secret_key', '')
    
    return BinanceClient(api_key, secret_key, testnet=use_testnet)
```

**Test:** `python -c "from services.binance_client import BinanceClient; c = BinanceClient.from_config(); print('Testnet:', c.base_url)"`
Expected: `Testnet: https://testnet.binance.vision`

### Task 1.1.4: Commit

```bash
git add -A && git commit -m "feat: Phase 1.1 - SQLite database + testnet config"
```

---

## SUB-PHASE 1.2: Flexible Strategy System

### Task 1.2.1: Create `strategies/strategy_engine.py`

**Create file:** `strategies/strategy_engine.py`

**Purpose:** Evaluate user-defined strategy conditions against market data.

**Key concept:** A strategy's entry/exit conditions are stored as JSON arrays. Each condition is a dict like:
```json
{"indicator": "RSI", "period": 14, "operator": "<", "value": 30}
```

**Functions to implement:**

```python
def calculate_indicator(indicator_name, klines, params):
    """
    Calculate a single indicator value from klines data.
    Use functions from signal_engine.py (calculate_rsi_wilder, calculate_ema, etc.)
    
    Supported indicators:
    - RSI: returns RSI value (uses calculate_rsi_wilder)
    - EMA: returns EMA value (uses calculate_ema)
    - MACD: returns (macd_line, signal_line, histogram)
    - BOLLINGER: returns (upper, middle, lower)
    - ATR: returns ATR value (uses calculate_atr)
    - VWAP: returns VWAP value (uses calculate_vwap)
    - VOLUME: returns volume_ratio (current vs 20-period avg)
    - PRICE: returns current close price
    """

def evaluate_single_condition(condition, klines, prev_klines=None):
    """
    Evaluate one condition dict against klines.
    Returns: (bool result, float current_value)
    
    condition example: {"indicator": "RSI", "period": 14, "operator": "<", "value": 30}
    
    Operators: <, >, <=, >=, ==, CROSS_ABOVE, CROSS_BELOW
    For CROSS_ABOVE/BELOW: need prev_klines to compare previous candle state
    """

def evaluate_conditions(conditions, logic, klines, prev_klines=None):
    """
    Evaluate array of conditions with AND/OR logic.
    Returns: (bool result, list of condition_details)
    
    logic='AND': ALL conditions must be true
    logic='OR': ANY condition must be true
    """

def scan_with_strategy(strategy_dict, market_data=None):
    """
    Run scan for ONE strategy across all its coins.
    
    1. For each coin in strategy['coins']:
       a. Fetch klines (use signal_engine.fetch_klines)
       b. Evaluate entry_conditions
       c. If entry met → calculate confidence, generate signal dict
    2. Filter by min_confidence, min_rr
    3. Return list of signals
    """

def scan_all_active_strategies(market_data=None):
    """
    Load all strategies with is_active=1 from database.
    Run scan_with_strategy for each.
    Return combined signals sorted by confidence.
    """
```

**Important:** Reuse indicator functions from `strategies/signal_engine.py`:
```python
from strategies.signal_engine import (
    calculate_rsi_wilder, calculate_ema, calculate_atr,
    calculate_vwap, calculate_confidence, fetch_klines
)
```

**For MACD (new indicator):**
```python
def calculate_macd(closes, fast=12, slow=26, signal=9):
    ema_fast = calculate_ema(closes, fast)
    ema_slow = calculate_ema(closes, slow)
    # Need full EMA series, not just last value
    # Build MACD line = EMA(fast) - EMA(slow) for each point
    # Signal line = EMA of MACD line
    # Histogram = MACD - Signal
```

**For Bollinger Bands (new indicator):**
```python
def calculate_bollinger(closes, period=20, std_dev=2):
    sma = sum(closes[-period:]) / period
    variance = sum((c - sma) ** 2 for c in closes[-period:]) / period
    std = variance ** 0.5
    return sma + std_dev * std, sma, sma - std_dev * std  # upper, middle, lower
```

### Task 1.2.2: Create `strategies/strategy_templates.py`

**Create file:** `strategies/strategy_templates.py`

Return a list of template dicts. Each template follows the strategy schema.

**Must include these 7 templates:**

1. **RSI Oversold Conservative** — RSI<30 AND Price>EMA200, exit RSI>70. For BTC/ETH.
2. **RSI Oversold Aggressive** — RSI<35, exit RSI>65. For altcoins.
3. **EMA Cross Bullish** — EMA9>EMA21 AND Price>EMA200, exit EMA9<EMA21.
4. **MACD Momentum** — MACD>0 AND MACD>Signal, exit MACD<Signal.
5. **Bollinger Bounce** — Price<LowerBB AND RSI<35, exit Price>MiddleBB.
6. **Volume Breakout** — Volume>2x AND RSI<40, exit RSI>65.
7. **Scalp Quick** — RSI<25 AND Volume>2x, exit RSI>40.

Each template should have `is_template: 1` and realistic SL/TP values.

```python
def get_templates():
    """Return list of strategy template dicts"""
    return [
        {
            "id": "tpl_rsi_conservative",
            "name": "RSI Oversold (Conservative)",
            "description": "Classic RSI oversold bounce with EMA200 trend filter. Best for BTC, ETH.",
            "coins": '["BTCUSDT", "ETHUSDT"]',
            "mode": "SWING",
            "timeframe": "1h",
            "entry_conditions": '[{"indicator":"RSI","period":14,"operator":"<","value":30},{"indicator":"PRICE_VS_EMA","period":200,"operator":">","value":0}]',
            "exit_conditions": '[{"indicator":"RSI","period":14,"operator":">","value":70}]',
            "entry_logic": "AND",
            "exit_logic": "OR",
            "sl_pct": 2.5,
            "tp_pct": 7.5,
            "min_confidence": 60,
            "min_rr": 2.0,
            "is_template": 1,
            "is_active": 0
        },
        # ... 6 more templates
    ]
```

### Task 1.2.3: Create `routes/strategies.py`

**Create file:** `routes/strategies.py`

**Blueprint name:** `strategies_bp`, prefix `/api/strategies`

**Endpoints:**

```
GET    /                  → List all strategies (exclude templates unless ?include_templates=1)
POST   /                  → Create new strategy (generate UUID for id)
GET    /<id>              → Get one strategy
PUT    /<id>              → Update strategy
DELETE /<id>              → Delete strategy (can't delete templates)
POST   /<id>/clone        → Clone strategy with new name
POST   /<id>/activate     → Set is_active=1
POST   /<id>/deactivate   → Set is_active=0
GET    /templates         → List built-in templates
POST   /from-template     → Create strategy from template (clone template + set is_template=0)
```

**All endpoints use `@require_auth` decorator.**

Store/read from SQLite `strategies` table.

For `POST /` and `PUT /<id>`, validate:
- `name` is required and non-empty
- `coins` is a valid JSON array
- `entry_conditions` is a valid JSON array with at least 1 condition
- `exit_conditions` is a valid JSON array with at least 1 condition

### Task 1.2.4: Register blueprint in `app.py`

```python
from routes.strategies import strategies_bp
app.register_blueprint(strategies_bp, url_prefix='/api/strategies')
```

### Task 1.2.5: Seed templates on startup

In `app.py`, after `init_db()`:
```python
from strategies.strategy_templates import seed_templates
seed_templates()  # Insert templates if not already in DB
```

### Task 1.2.6: Update `routes/bot_control.py`

Modify `scan_job()` function:
- Instead of calling `run_scan(config, market_data)`, call `scan_all_active_strategies(market_data)`
- Keep the existing `run_scan()` as fallback if no strategies are active
- Rest of scan_job stays the same (save signals, send Telegram, etc.)

### Task 1.2.7: Test

```bash
# Start server
python app.py &

# List templates
curl -s http://localhost:5000/api/strategies/templates | python -m json.tool

# Create strategy from template
curl -s -X POST http://localhost:5000/api/strategies/from-template \
  -H "Content-Type: application/json" \
  -d '{"template_id": "tpl_rsi_conservative", "name": "My BTC Strategy"}' | python -m json.tool

# List strategies
curl -s http://localhost:5000/api/strategies | python -m json.tool
```

### Task 1.2.8: Commit

```bash
git add -A && git commit -m "feat: Phase 1.2 - Flexible strategy system with templates"
```

---

## SUB-PHASE 1.3: Real Backtest Engine

### Task 1.3.1: Create `strategies/backtester.py`

**Create file:** `strategies/backtester.py`

**Core logic:**

```python
def fetch_historical_klines(symbol, interval, days):
    """
    Fetch klines for <days> days from Binance.
    Binance limit is 1000 per request, so paginate if needed.
    For 90 days at 15m interval = 8640 candles = 9 requests.
    
    Returns: dict with opens, highs, lows, closes, volumes, timestamps
    """

def run_backtest(strategy_id, days=90, initial_balance=100.0):
    """
    1. Load strategy from database
    2. For each coin in strategy:
       a. Fetch historical klines
       b. Need at least 200 candles for EMA200
       c. Start evaluating from candle 200 onward
       d. For each candle (i):
          - Build klines slice [0:i+1] for indicator calculation
          - Evaluate entry conditions using strategy_engine.evaluate_conditions()
          - If entry conditions met AND no open position:
            * Open position at close price
            * Calculate SL and TP prices
          - If position is open:
            * Check if low <= SL price → close at SL, record loss
            * Check if high >= TP price → close at TP, record win
            * Evaluate exit conditions → close at close price if met
    3. Calculate summary stats
    4. Save to backtests table
    5. Return results
    """

def calculate_max_drawdown(equity_curve):
    """
    equity_curve = list of balance values over time
    Max DD = max peak-to-trough decline
    """
    peak = equity_curve[0]
    max_dd = 0
    for value in equity_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak * 100
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)

def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """
    returns = list of per-trade PnL percentages
    Sharpe = (mean_return - risk_free) / std_dev(returns)
    """
```

**Important considerations:**
- Don't open a new position if one is already open for same coin
- Use the strategy's SL/TP percentages
- Track equity curve: start at initial_balance, adjust after each closed trade
- Save each trade: entry_time, exit_time, entry_price, exit_price, side, pnl_pct

### Task 1.3.2: Create `routes/backtest.py`

**Create file:** `routes/backtest.py`

**Blueprint name:** `backtest_bp`, prefix `/api/backtest`

**Endpoints:**

```python
@backtest_bp.route('/run', methods=['POST'])
@require_auth
def run_backtest_endpoint():
    """
    Body: {"strategy_id": "str-001", "days": 90}
    Calls backtester.run_backtest()
    Returns: summary + trades + equity_curve
    """

@backtest_bp.route('/preview', methods=['POST'])
@require_auth
def preview_backtest():
    """
    Body: {"conditions": [...], "coins": ["BTCUSDT"], "sl_pct": 2.5, "tp_pct": 7.5, "days": 30}
    Quick backtest WITHOUT saving strategy first.
    Useful for testing before committing to a strategy.
    """

@backtest_bp.route('/history', methods=['GET'])
@require_auth
def get_backtest_history():
    """Return all past backtest results from database"""

@backtest_bp.route('/<int:backtest_id>', methods=['GET'])
@require_auth
def get_backtest_detail(backtest_id):
    """Return one backtest detail including trades and equity curve"""
```

### Task 1.3.3: Register blueprint

In `app.py`:
```python
from routes.backtest import backtest_bp
app.register_blueprint(backtest_bp, url_prefix='/api/backtest')
```

### Task 1.3.4: Update `routes/performance.py`

Remove `MOCK_TRADES` list and the fake backtest endpoint.
Replace with real data from SQLite positions table.

### Task 1.3.5: Test

```bash
# First create and activate a strategy, then:
curl -s -X POST http://localhost:5000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": "YOUR_STRATEGY_ID", "days": 30}' | python -m json.tool

# Expected: win_rate between 30-70% (realistic), trades list, equity curve
# If win_rate is >80%, something is wrong with the logic
```

### Task 1.3.6: Commit

```bash
git add -A && git commit -m "feat: Phase 1.3 - Real backtesting engine with historical data"
```

---

## SUB-PHASE 1.4: Position Manager

### Task 1.4.1: Create `services/position_manager.py`

**Functions:**

```python
def open_position(signal_id, strategy_id, symbol, side, entry_price, quantity, sl_pct, tp_pct, exchange='spot', order_id=None):
    """Insert new position into positions table with status='OPEN'"""

def close_position(position_id, exit_price, reason='MANUAL_CLOSE'):
    """
    Update position: set exit_price, calculate pnl_pct and pnl_usd,
    set status=reason, set closed_at=now
    PnL for BUY: (exit - entry) / entry * 100
    PnL for SELL: (entry - exit) / entry * 100
    """

def check_open_positions():
    """
    For each OPEN position:
    1. Fetch current price from Binance (use requests to /api/v3/ticker/price)
    2. Calculate current PnL
    3. Check if current price hit SL or TP:
       - BUY position: SL hit if price <= sl_price, TP hit if price >= tp_price
       - SELL position: SL hit if price >= sl_price, TP hit if price <= tp_price
    4. If SL/TP hit: close_position() + send Telegram notification
    5. Return list of position updates
    """

def get_open_positions():
    """Query positions WHERE status='OPEN', return as list of dicts"""

def get_position_history(limit=50):
    """Query positions WHERE status!='OPEN' ORDER BY closed_at DESC LIMIT <limit>"""

def get_portfolio_summary():
    """
    Return: {
        open_count, total_invested_usd, unrealized_pnl_usd, unrealized_pnl_pct,
        today_realized_pnl, all_time_pnl, all_time_trades, all_time_win_rate
    }
    """
```

### Task 1.4.2: Create `routes/positions.py`

**Blueprint name:** `positions_bp`, prefix `/api/positions`

```
GET  /              → get_open_positions()
GET  /history       → get_position_history()
GET  /summary       → get_portfolio_summary()
POST /<id>/close    → close_position(id, request.json['exit_price'])
```

### Task 1.4.3: Add position checking to scheduler

In `routes/bot_control.py`, add a new scheduler job that runs every 30 seconds:
```python
scheduler.add_job(
    check_positions_job,
    'interval',
    seconds=30,
    id='position_checker',
    replace_existing=True
)
```

### Task 1.4.4: Register blueprint, test, commit

```bash
git add -A && git commit -m "feat: Phase 1.4 - Position manager with auto SL/TP tracking"
```

---

## SUB-PHASE 1.5: Risk Manager

### Task 1.5.1: Create `services/risk_manager.py`

**Functions:**

```python
def can_trade(signal, exchange='spot'):
    """
    Check ALL risk rules. Returns: {'allowed': bool, 'reason': str, 'position_size': {...}}
    
    Rules to check:
    1. Balance >= min_balance_usd
    2. daily_trades < max (from config)
    3. daily_loss_pct < max_daily_loss_pct
    4. weekly_loss_pct < max_weekly_loss_pct
    5. open_positions_count < max_open_positions
    6. circuit_breaker is not active
    """

def calculate_position_size(balance, risk_pct, sl_pct, entry_price, exchange='spot', leverage=1):
    """
    Calculate safe position size.
    risk_amount = balance * risk_pct / 100
    position_value = risk_amount / (sl_pct / 100)
    if leverage > 1: position_value *= leverage (futures only)
    quantity = position_value / entry_price
    Returns: {'quantity': float, 'value_usd': float, 'risk_usd': float}
    """

def update_daily_stats(pnl_usd, pnl_pct, is_win):
    """Update risk_state table after a position closes"""

def check_circuit_breaker():
    """Check if 3 consecutive losses happened, return bool"""

def reset_daily_counters():
    """Reset daily counters. Called by midnight scheduler job."""

def get_risk_status():
    """Return current risk state for dashboard display"""
```

### Task 1.5.2: Commit

```bash
git add -A && git commit -m "feat: Phase 1.5 - Risk management with circuit breaker"
```

---

## SUB-PHASE 1.6: Semi-Auto Execution Engine

### Task 1.6.1: Create `services/binance_futures.py`

**Create file:** `services/binance_futures.py`

Separate client for Binance USDT-M Futures.
Pattern similar to `binance_client.py` but with:
- Base URL: `https://testnet.binancefuture.com` (testnet) or `https://fapi.binance.com` (live)
- Different endpoints: `/fapi/v1/order`, `/fapi/v2/account`, `/fapi/v1/leverage`

Key methods: `place_market_long()`, `place_market_short()`, `close_position()`, `set_leverage()`, `get_account()`

### Task 1.6.2: Update `routes/binance.py` execute endpoint

Rewrite the `/execute` endpoint:

```python
@binance_bp.route('/execute', methods=['POST'])
@require_auth
def execute_signal():
    """
    Semi-auto execution flow:
    1. Get signal_id from request
    2. Load signal from database
    3. Check risk_manager.can_trade()
    4. If not allowed → return reason
    5. Calculate position size
    6. Execute order on Binance (testnet or live based on config)
    7. Place SL and TP orders
    8. Save position to database via position_manager.open_position()
    9. Send Telegram notification
    10. Return order details
    """
```

### Task 1.6.3: Test

Test full flow with Binance testnet:
1. Start bot → get signal
2. Click execute → confirm → order sent to testnet
3. Check position appears in /api/positions
4. Wait for SL/TP → auto close

### Task 1.6.4: Commit

```bash
git add -A && git commit -m "feat: Phase 1.6 - Semi-auto execution with Binance testnet"
```

---

## SUB-PHASE 1.7: Dashboard UI Updates

### Task 1.7.1: Update `templates/dashboard.html`

Add these new UI sections (keep existing sections, ADD new ones):

1. **Header:** Add `[🧪 TESTNET]` badge and `[Risk: 🟢 OK]` status badge
2. **Bot Controls panel:** Replace mode/interval dropdowns with strategy selector dropdown + "New Strategy" button
3. **Signal cards:** Add `[▶ EXECUTE]` and `[SKIP]` buttons to each card. Show which strategy generated the signal.
4. **New section: OPEN POSITIONS** — between signals and performance. Show each open position with PnL, SL/TP, and CLOSE button.
5. **New section: STRATEGIES & BACKTEST** — show strategy cards with name, win rate, PnL. Each has [Backtest] and [Edit] buttons. Plus [+ New Strategy] and [Templates] buttons.
6. **Strategy Editor Modal** — form to create/edit strategy: name, coins (multi-select), conditions builder (add/remove rows), SL/TP, timeframe
7. **Backtest Results Modal** — show results: trades, equity curve (use Chart.js), summary stats
8. **Execute Confirmation Modal** — "Execute BUY BTCUSDT @ $65,000? Risk: $2.00 (2%)"

### Task 1.7.2: Update `static/app.js`

Add these functions:
```javascript
// Strategy management
async function loadStrategies() { }
async function createStrategy(data) { }
async function editStrategy(id) { }
async function deleteStrategy(id) { }
async function activateStrategy(id) { }

// Backtest
async function runBacktest(strategyId) { }
async function showBacktestResults(data) { }

// Positions
async function refreshPositions() { }
async function closePosition(id) { }

// Execution
async function executeSignal(signalId) { }
async function showExecuteConfirmation(signal) { }

// Risk
async function refreshRiskStatus() { }

// Add to polling interval:
setInterval(refreshPositions, 10000);  // every 10s
setInterval(refreshRiskStatus, 30000); // every 30s
```

### Task 1.7.3: Update `static/style.css`

Add styles for:
- `.strategy-card` — card for each strategy
- `.position-row` — row in open positions panel
- `.execute-btn` — green pulsing button
- `.risk-badge` — status badge in header
- `.testnet-badge` — yellow badge saying TESTNET
- `.modal-strategy-editor` — strategy editor modal
- `.modal-backtest-results` — backtest results modal
- `.modal-confirm-execute` — execution confirmation dialog

### Task 1.7.4: Add Chart.js

In `dashboard.html`, add before `</body>`:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

### Task 1.7.5: Test

1. Open `http://localhost:5000` in browser
2. Verify all new panels display
3. Create a strategy from template
4. Run backtest → verify results show
5. Start bot → verify signals show with EXECUTE button
6. Click EXECUTE → verify confirmation dialog
7. Check positions panel updates

### Task 1.7.6: Commit

```bash
git add -A && git commit -m "feat: Phase 1.7 - Dashboard UI with strategies, backtest, positions"
```

---

## FINAL: Push to GitHub

```bash
git push origin master
```

---

## VERIFICATION CHECKLIST

After all sub-phases are complete, verify:

- [ ] `python app.py` starts without errors
- [ ] Database `data/trading.db` exists with all tables
- [ ] `GET /api/strategies/templates` returns 7 templates
- [ ] Can create strategy from template
- [ ] Can edit strategy conditions
- [ ] Can run backtest on strategy → realistic win rate (30-70%)
- [ ] Backtest shows equity curve
- [ ] Bot scan uses active strategies (not hardcoded logic)
- [ ] Open positions panel shows positions
- [ ] Position auto-closes on SL/TP hit
- [ ] Risk status badge shows in header
- [ ] TESTNET badge visible
- [ ] Execute button triggers confirmation dialog
- [ ] Order executes on Binance testnet
- [ ] Telegram notification sent on signal + execution
- [ ] No JavaScript console errors
- [ ] Mobile responsive still works

---

## NOTES FOR AI AGENTS

1. **Do NOT skip tasks.** Each task builds on the previous one.
2. **Test after each task.** Run the test command before proceeding.
3. **Keep existing code working.** Don't break what already works.
4. **Follow existing patterns.** Look at `routes/market.py` for route patterns, `signal_engine.py` for indicator patterns.
5. **Use `@require_auth` on ALL API endpoints.**
6. **JSON responses should match existing format** (see `routes/signals.py` for examples).
7. **Error handling:** Wrap API calls in try/except, return `{"success": false, "error": "message"}` on failure.
8. **Do NOT install heavy dependencies.** Use Python stdlib (`sqlite3`, `json`, `uuid`, `datetime`) where possible. Only add `pandas`/`numpy` if truly needed for backtesting math.
9. **Commit after each sub-phase**, not after each task.
10. **If stuck, re-read the existing code** in the files listed at the top of this guide.

---

## 🔁 CRITICAL: AGENT RELAY PROTOCOL

**After completing each sub-phase, you MUST do ALL of these:**

1. **Test:** Run `python app.py` — server must start without errors
2. **Test:** Run the specific test commands listed in your sub-phase
3. **Commit:** `git add -A && git commit -m "feat: Phase 1.X - [description]"`
4. **Update AGENT.md:** Open `AGENT.md`, find the sub-phase list under "CURRENT PRIORITY", change your completed item from `⬜` to `✅`
5. **Report:** Tell the user which sub-phase you completed and which is next

**Example:** If you completed Sub-Phase 1.2, update AGENT.md:
```
BEFORE: 2. ⬜ Flexible Strategy System
AFTER:  2. ✅ Flexible Strategy System
```

This ensures the NEXT agent knows exactly where to pick up.

**If the user tells you to "continue" or "start" without specifying a sub-phase:**
1. Read `AGENT.md`
2. Find the first ⬜ item
3. That is your task — go to that section in THIS file and execute it

**Design rules:**
- UI dark theme: `#0a0e1a` background, `#111827` cards, `#00ff9d` accent green, `#ff4757` accent red
- All text must be readable on dark background
- Mobile responsive (existing dashboard already is)
- Follow existing HTML structure in `templates/dashboard.html`
- Follow existing JS patterns in `static/app.js`
- Follow existing CSS variables in `static/style.css`
