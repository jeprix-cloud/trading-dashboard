# TradingCore Dashboard — Standalone Mode

## Objective

Build TradingCore Dashboard as a **fully standalone web application** that operates independently from OpenClaw. All features should work via direct access to `http://43.134.62.242:5000` without requiring OpenClaw or any OpenClaw skills.

---

## What This Means

| Feature | With OpenClaw | Standalone Mode |
|---------|---------------|-----------------|
| Web Dashboard | ✅ Flask | ✅ Flask (no change) |
| Market Data | ✅ Flask | ✅ Flask (no change) |
| Strategy Builder | ✅ Flask | ✅ Flask (no change) |
| Telegram Alerts | OpenClaw bot | **Dedicated Flask Telegram bot** |
| Cron Screening | OpenClaw cron | **Built-in APScheduler in Flask** |
| Trading Analysis | OpenClaw skills | **Built-in analysis engine in Flask** |
| Bot Start/Stop | OpenClaw commands | **Flask API + Dashboard UI** |

---

## Current Architecture (OpenClaw-Dependent)

```
┌─────────────────────────────────────────┐
│           OpenClaw (Master)             │
│  - Telegram bot (@PakCEO_bot)           │
│  - Cron jobs (15 min screening)         │
│  - Skills: analyst-*, trader-*          │
│  - Trading signals via chat             │
└─────────────────────────────────────────┘
           ↕ (interacts with)
┌─────────────────────────────────────────┐
│       TradingCore Dashboard (Flask)     │
│  - Web UI (port 5000)                  │
│  - API endpoints                        │
│  - Bot scheduler (APScheduler)         │
└─────────────────────────────────────────┘
```

---

## Target Architecture (Standalone)

```
┌─────────────────────────────────────────┐
│       TradingCore Dashboard (Flask)     │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │     Standalone Telegram Bot      │    │
│  │  (@TradingCore_Bot or similar)  │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   Built-in Scheduler (APScheduler)│   │
│  │   - Coin screening every 15 min  │   │
│  │   - Strategy scan every X min    │   │
│  │   - Performance tracking        │   │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   Built-in Analysis Engine       │   │
│  │   - RSI, EMA, MACD, BB, etc.    │   │
│  │   - Strategy evaluation          │   │
│  │   - Confidence scoring           │   │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   Web Dashboard + API            │   │
│  │   - Market data                  │   │
│  │   - Strategy builder             │   │
│  │   - Backtesting                  │   │
│  │   - Live monitoring              │   │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

---

## Components to Build

### 1. Standalone Telegram Bot Service

**Location:** `services/telegram_bot.py` (new)

**Responsibilities:**
- Connect to Telegram Bot API directly (no OpenClaw)
- Handle commands: `/start`, `/help`, `/status`, `/signals`, `/strategies`
- Send alerts for signals and strategy triggers
- Allow user to configure bot token and chat ID from dashboard

**API Endpoints:**
```
POST /api/telegram/configure    → Set bot token + chat ID
POST /api/telegram/test         → Send test message
POST /api/telegram/send-alert   → Send alert (internal)
GET  /api/telegram/status       → Check connection status
```

**Routes:**
```python
# /routes/telegram_bot.py
@bot_bp.route('/configure', methods=['POST'])
def configure_bot():
    # Save bot token + chat ID to config
    # Test connection
    # Return success/failure

@bot_bp.route('/send-alert', methods=['POST'])
def send_alert():
    # Called internally by scheduler
    # Send formatted message to Telegram
```

**Telegram Bot Features:**
```
/start           → Welcome message + instructions
/help            → Show all available commands
/status          → Show current bot status + active strategies
/signals         → Show recent signals
/strategies      → List saved strategies
/scan            → Trigger manual scan
/backtest <id>   → Run backtest for strategy
```

### 2. Built-in Scheduler (APScheduler)

**Location:** `services/scheduler.py` (new or extend existing)

**Jobs to run:**
| Job | Interval | Function |
|-----|----------|----------|
| Coin Screener | Every 15 min | Scan top coins, send alerts |
| Strategy Scanner | Every 5/15/60 min | Evaluate strategies, send signals |
| Market Data Refresh | Every 30 sec | Update market pulse data |
| Performance Tracker | Every 1 hour | Update trade history, win rate |
| Cleanup | Daily at 00:00 | Remove old signal logs |

**Implementation:**
```python
from apscheduler.schedulers.background import BackgroundScheduler

def init_scheduler(app):
    scheduler = BackgroundScheduler()
    
    # Coin screening
    scheduler.add_job(
        run_coin_screen,
        'interval',
        minutes=15,
        args=[app]
    )
    
    # Strategy scanning
    scheduler.add_job(
        run_strategy_scan,
        'interval',
        minutes=5,
        args=[app, 'live']
    )
    
    scheduler.start()
```

### 3. Built-in Analysis Engine

**Location:** `strategies/analysis_engine.py` (new)

**Features:**
- All indicators from `signal_engine.py` (Wilder RSI, EMA, ATR, VWAP, etc.)
- Strategy condition evaluation
- Confidence scoring (V2 system)
- Signal generation

**API Endpoints:**
```
POST /api/analyze           → Analyze a symbol
        Body: { symbol, mode, indicators[] }
        Response: { rsi, ema, signals, confidence }
        
POST /api/scan              → Run full coin scan
        Body: { mode, min_confidence, min_rr }
        Response: { signals[] }

GET  /api/indicators         → List available indicators
GET  /api/indicator/<name>   → Get indicator value for symbol
```

### 4. Strategy Execution Engine

**Location:** `strategies/executor.py` (new)

**Responsibilities:**
- Load saved strategies from `config/strategies.json`
- Evaluate conditions against current market data
- Generate signals when conditions are met
- Send Telegram alerts
- Track open positions (in memory or SQLite)

**Logic:**
```
For each live strategy:
    1. Load strategy config
    2. For each coin in strategy:
        a. Fetch current data (price, indicators)
        b. Evaluate entry conditions
        c. If met → generate BUY signal
        d. Evaluate exit conditions (for open positions)
        e. If met → generate SELL signal
    3. Send Telegram alert if signal generated
```

### 5. Data Storage (SQLite)

**Location:** `data/trading.db` (new)

**Tables:**
```sql
-- Strategies
CREATE TABLE strategies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    config JSON NOT NULL,
    mode TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

-- Signals (for history)
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id TEXT,
    symbol TEXT,
    side TEXT,
    price REAL,
    rsi REAL,
    confidence REAL,
    stop_loss REAL,
    take_profit REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    outcome TEXT,
    outcome_price REAL,
    outcome_timestamp DATETIME
);

-- Backtest Results
CREATE TABLE backtests (
    id TEXT PRIMARY KEY,
    strategy_id TEXT,
    symbol TEXT,
    results JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Performance Metrics
CREATE TABLE performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE,
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    win_rate REAL,
    profit_loss_pct REAL,
    best_trade REAL,
    worst_trade REAL
);
```

---

## File Structure (Final)

```
trading-dashboard/
├── app.py                      # Main Flask app
├── routes/
│   ├── market.py              # ✅ Already exists
│   ├── signals.py            # ✅ Already exists
│   ├── strategies.py          # 🔴 NEW (Strategy CRUD)
│   ├── backtest.py            # 🔴 NEW (Backtest API)
│   ├── live.py                # 🔴 NEW (Live mode API)
│   ├── telegram_bot.py        # 🔴 NEW (Telegram bot endpoints)
│   └── bot_control.py         # ✅ Already exists
├── services/
│   ├── auth.py                # ✅ Already exists
│   ├── telegram_notifier.py   # ✅ Already exists
│   ├── binance_client.py      # ✅ Already exists
│   ├── scheduler.py           # 🔴 NEW (APScheduler manager)
│   ├── telegram_bot.py        # 🔴 NEW (Standalone Telegram bot)
│   └── database.py           # 🔴 NEW (SQLite helper)
├── strategies/
│   ├── signal_engine.py      # ✅ Already exists (indicators)
│   ├── analysis_engine.py     # 🔴 NEW (Analysis wrapper)
│   ├── condition_parser.py    # 🔴 NEW (Parse conditions)
│   ├── strategy_engine.py     # 🔴 NEW (Evaluate strategies)
│   ├── backtester.py          # 🔴 NEW (Backtesting)
│   ├── executor.py            # 🔴 NEW (Live execution)
│   ├── screener.py            # ✅ Already exists
│   └── templates.py          # 🔴 NEW (Strategy templates)
├── config/
│   ├── watchlist.json         # ✅ Already exists
│   ├── strategies.json        # 🔴 NEW (Saved strategies)
│   └── telegram_bot.json      # 🔴 NEW (Bot token + chat ID)
├── data/
│   ├── trading.db             # 🔴 NEW (SQLite database)
│   └── signals/               # ✅ Already exists
├── templates/
│   └── dashboard.html         # MODIFY (Add bot status, live mode)
├── static/
│   ├── app.js                 # MODIFY (Add bot controls, live UI)
│   └── style.css              # MODIFY (Add new styles)
└── requirements.txt           # UPDATE (add new deps)
```

---

## API Routes Summary

### Existing (keep as-is)
```
GET  /api/market/*             → Market data endpoints
GET  /api/signals              → Trading signals
GET  /api/performance          → Performance stats
GET  /api/config               → Bot configuration
POST /api/bot/start            → Start bot
POST /api/bot/stop             → Stop bot
```

### New Endpoints

**Telegram Bot:**
```
POST /api/telegram/configure    → Configure bot token + chat ID
POST /api/telegram/test         → Send test message
POST /api/telegram/send-alert    → Send alert (internal)
GET  /api/telegram/status       → Get bot status
```

**Strategies:**
```
GET    /api/strategies          → List all strategies
POST   /api/strategies           → Create strategy
GET    /api/strategies/<id>      → Get strategy
PUT    /api/strategies/<id>      → Update strategy
DELETE /api/strategies/<id>      → Delete strategy
POST   /api/strategies/<id>/clone → Clone strategy
```

**Backtest:**
```
POST /api/backtest/run           → Run backtest
GET  /api/backtest/history/<id>  → Get backtest result
GET  /api/backtest/history       → List all backtests
```

**Live Mode:**
```
POST /api/live/start             → Start strategy
POST /api/live/stop              → Stop strategy
GET  /api/live/status            → Get active strategies
```

**Analysis:**
```
POST /api/analyze                → Analyze symbol
POST /api/scan                   → Run full scan
GET  /api/indicators             → List indicators
GET  /api/indicator/<name>       → Get indicator value
```

**Scheduler:**
```
POST /api/scheduler/start        → Start scheduler
POST /api/scheduler/stop         → Stop scheduler
GET  /api/scheduler/status       → Get scheduler status
```

---

## Scheduler Jobs Detail

### Coin Screening Job (every 15 min)
```python
def run_coin_screen():
    from strategies.screener import screen_coins
    
    results = screen_coins(
        coins=['BTCUSDT', 'ETHUSDT', ...],
        min_rsi=30,
        max_rsi=70,
        min_volume=10000000
    )
    
    for signal in results:
        if signal.confidence >= 50 and signal.rr >= 2:
            send_telegram_alert(signal)
            save_signal(signal)
```

### Strategy Scan Job (every 5 min per strategy)
```python
def run_strategy_scan(strategy_id):
    from strategies.executor import evaluate_strategy
    
    strategy = load_strategy(strategy_id)
    for coin in strategy.coins:
        result = evaluate_strategy(strategy, coin)
        if result.signal:
            send_telegram_alert(result)
            save_signal(result)
```

### Market Data Refresh (every 30 sec)
```python
def refresh_market_data():
    # Update cache in routes/market.py
    # Already exists via refreshAll() JS
    pass
```

---

## Configuration Files

### `config/telegram_bot.json`
```json
{
    "enabled": true,
    "bot_token": "123456:ABC-DEF...",
    "chat_id": "317970390",
    "alerts_enabled": true,
    "signal_channel": "@Osdigtrading_bot"
}
```

### `config/scheduler.json`
```json
{
    "enabled": true,
    "screening_interval_minutes": 15,
    "strategy_scan_interval_minutes": 5,
    "screening_mode": "BOTH",
    "min_confidence": 60,
    "min_rr": 2.0
}
```

### `config/strategies.json`
```json
{
    "strategies": [
        {
            "id": "uuid-1",
            "name": "RSI Oversold",
            "mode": "SWING",
            "timeframe": "1h",
            "entry_conditions": [...],
            "exit_conditions": [...],
            "coins": ["BTCUSDT", "ETHUSDT"],
            "enabled": true
        }
    ]
}
```

---

## Implementation Phases

### Phase S1: Standalone Telegram Bot
1. Create `services/telegram_bot.py` - pure Telegram Bot API wrapper
2. Create `routes/telegram_bot.py` - Flask endpoints for bot config
3. Add UI in dashboard for bot configuration (Bot Token, Chat ID input)
4. Add test connection button
5. Move Telegram alerts from OpenClaw to this service

### Phase S2: Built-in Scheduler
1. Create `services/scheduler.py` - APScheduler wrapper
2. Move coin screening cron from OpenClaw to here
3. Add strategy scanning job
4. Add scheduler status to dashboard
5. Add start/stop/pause controls

### Phase S3: Analysis Engine
1. Create `strategies/analysis_engine.py` - wrap all indicators
2. Add `/api/analyze` endpoint
3. Add `/api/indicators` list endpoint
4. Create strategy condition evaluator

### Phase S4: Strategy Executor (Live Mode)
1. Create `strategies/executor.py`
2. Create `routes/live.py`
3. Connect strategy scanning to Telegram bot
4. Add live mode panel to dashboard

### Phase S5: Database Integration
1. Set up SQLite database
2. Create signal history table
3. Track performance metrics
4. Add backtest history

### Phase S6: UI Updates
1. Update dashboard with bot status indicator
2. Add Telegram configuration panel
3. Add scheduler controls
4. Add live mode panel
5. Update settings modal

---

## Dependencies to Add

```
# requirements.txt additions
python-telegram-bot>=20.0
apscheduler>=3.10.0
schedule>=1.2.0
```

---

## Testing Checklist

- [ ] Telegram bot can send/receive messages
- [ ] Scheduler runs coin screening every 15 min
- [ ] Strategy scan generates signals
- [ ] Dashboard shows bot status (connected/disconnected)
- [ ] Can start/stop scheduler from dashboard
- [ ] Can configure bot token + chat ID from dashboard
- [ ] Telegram alerts arrive with correct format
- [ ] Signal history is saved to database
- [ ] Backtest results are saved
- [ ] Live mode can be started/stopped
- [ ] All OpenClaw dependencies removed

---

## Migration Notes

### From OpenClaw Cron to Built-in Scheduler
**Before (OpenClaw):**
```
*/15 8-11 * * * MODE=MONITOR /home/ubuntu/.openclaw/skills/coin-screener/screening.sh
```

**After (Standalone):**
```python
scheduler.add_job(
    run_coin_screen,
    'interval',
    minutes=15,
    id='coin_screening'
)
```

### From OpenClaw Telegram to Standalone
**Before:** OpenClaw manages `@Osdigtrading_bot`

**After:** 
1. Create new bot via @BotFather OR
2. Reuse existing bot token in `services/telegram_bot.py`

---

## Key Files to Modify

| File | Change |
|------|--------|
| `app.py` | Register new blueprints, init scheduler |
| `requirements.txt` | Add dependencies |
| `templates/dashboard.html` | Add bot config UI, scheduler controls, live panel |
| `static/app.js` | Add bot status polling, scheduler controls |
| `routes/telegram_bot.py` | New Flask endpoints |
| `services/telegram_bot.py` | New standalone Telegram wrapper |
| `services/scheduler.py` | New APScheduler manager |
| `strategies/executor.py` | New strategy executor |
| `strategies/analysis_engine.py` | New analysis wrapper |

---

## Notes for Antigravity

1. **Start with Phase S1** — Telegram bot is the most critical to get rid of OpenClaw dependency
2. Use `python-telegram-bot` library (not telepot or other wrappers)
3. Follow existing patterns in `routes/market.py` for route structure
4. Store bot config in `config/telegram_bot.json` (not hardcoded)
5. Scheduler should be background process (not blocking Flask)
6. Test Telegram bot manually first before integrating into scheduler
7. Database schema is guidance — adjust if needed
8. Keep backward compatibility — don't break existing OpenClaw integration yet (user may want both)

---

**Commit format:** `feat: Standalone Mode - [description]`
**Branch strategy:** `feature/standalone` → `master`