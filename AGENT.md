# TradingCore Dashboard — Agent Instructions

## Objective

Build a complete **TradingCore Dashboard** — a Flask-based cryptocurrency trading platform with web UI, real-time signals, bot control, and semi-auto execution on Binance.

---

## Repository

```text
https://github.com/jeprix-cloud/trading-dashboard
git@github.com:jeprix-cloud/trading-dashboard.git
```

---

## What Has Already Been Built (DO NOT REDO)

The following features are **COMPLETE and WORKING**. Do not rebuild them:

- ✅ Flask app with authentication (`app.py`, `services/auth.py`)
- ✅ Full dashboard UI (`templates/dashboard.html`, `static/style.css`, `static/app.js`)
- ✅ Signal engine — Wilder RSI, EMA, ATR, VWAP, Confidence V2 (`strategies/signal_engine.py`)
- ✅ Coin screener (`strategies/screener.py`)
- ✅ Bot scheduler — APScheduler (`routes/bot_control.py`)
- ✅ Learning system — pattern recognition & blacklist (`strategies/lessons.py`)
- ✅ Evolution system — adaptive thresholds (`strategies/evolution.py`)
- ✅ Telegram notifications (`services/telegram_notifier.py`)
- ✅ Binance API client — Spot only (`services/binance_client.py`)
- ✅ Performance tracker with mock data (`routes/performance.py`)
- ✅ Settings modal — Telegram config from dashboard
- ✅ Market Pulse, Live Signals, Bot Controls panels

---

## 🚨 CURRENT PRIORITY: Phase 1 Foundation

> **YOU MUST READ:** `docs/PHASE1_EXECUTION_GUIDE.md` — it has detailed step-by-step instructions with code patterns, test commands, and commit messages.

**Goal:** Transform TradingCore from an alert-only system into a real semi-auto trading platform with flexible strategies, real backtesting, position tracking, risk management, and Binance execution.

### Progress Tracker

**Find the FIRST ⬜ item — that is YOUR task:**

1. ⬜ **SQLite Database + Testnet Config** → `services/database.py`
2. ⬜ **Flexible Strategy System** → `strategies/strategy_engine.py`, `strategies/strategy_templates.py`, `routes/strategies.py`
3. ⬜ **Real Backtest Engine** → `strategies/backtester.py`, `routes/backtest.py`
4. ⬜ **Position Manager** → `services/position_manager.py`, `routes/positions.py`
5. ⬜ **Risk Management** → `services/risk_manager.py`
6. ⬜ **Semi-Auto Execution** → `services/binance_futures.py`, update `routes/binance.py`
7. ⬜ **Dashboard UI Updates** → update `dashboard.html`, `app.js`, `style.css`

### Key Configuration

- Binance Testnet API keys: already saved in `config/bot_config.json`
- `use_testnet: true` → system defaults to testnet (no real money)
- `execution_mode: semi_auto` → requires user click to confirm orders
- Testnet Spot URL: `https://testnet.binance.vision`
- Testnet Futures URL: `https://testnet.binancefuture.com`

---

## 🔁 AGENT RELAY PROTOCOL

### When You Start a Session

1. Read this file (`AGENT.md`)
2. Find the FIRST ⬜ sub-phase above — that is YOUR task
3. Open `docs/PHASE1_EXECUTION_GUIDE.md` and go to that sub-phase section
4. Follow ALL tasks in that sub-phase step by step
5. Run the test commands after each task
6. Commit after completing ALL tasks in the sub-phase

### When You Finish a Sub-Phase

1. Run `python app.py` — verify server starts without errors
2. Run the specific test commands from the execution guide
3. `git add -A && git commit -m "feat: Phase 1.X - [description]"`
4. **UPDATE THIS FILE:** Change the ⬜ to ✅ for your completed sub-phase
5. Add an entry to the **Agent Work Log** section below
6. Tell the user: "Sub-Phase 1.X complete. Next agent should work on Sub-Phase 1.Y"

### If Something From a Previous Sub-Phase Is Broken

Fix it before proceeding with your sub-phase.

---

## Design Rules (MUST FOLLOW)

```text
Background:      #0a0e1a (deep navy)
Card background: #111827
Accent Green:    #00ff9d
Accent Red:      #ff4757
Accent Yellow:   #ffd700
Text Primary:    #e2e8f0
Text Secondary:  #64748b
Border:          #1e293b
```

- Dark theme ONLY — no light theme
- RSI must be Wilder's method — simple moving average is WRONG
- Use `@require_auth` decorator on ALL API endpoints
- Error responses: `{"success": false, "error": "message"}`
- Follow existing Flask Blueprint patterns (see `routes/market.py` as example)
- Mobile responsive
- No heavy dependencies — prefer Python stdlib (`sqlite3`, `json`, `uuid`)

---

## Key Files to Read Before Coding

| File | Purpose |
|------|---------|
| `app.py` | Flask app, blueprint registration pattern |
| `routes/market.py` | Example route pattern (Blueprint, `@require_auth`, JSON) |
| `strategies/signal_engine.py` | Indicator calculations (RSI, EMA, ATR, VWAP) |
| `services/binance_client.py` | Binance API client pattern |
| `services/auth.py` | Authentication decorator |
| `config/bot_config.json` | All configuration (testnet keys, risk settings) |
| `docs/PHASE1_EXECUTION_GUIDE.md` | **Step-by-step instructions for Phase 1** |
| `docs/SPEC.md` | Original UI/design specifications |

---

## Agent Work Log

*Each agent adds an entry here after completing their sub-phase:*

| Date | Agent | Sub-Phase | Status | Notes |
|------|-------|-----------|--------|-------|
| 2026-04-03 | Antigravity | Planning | ✅ | Created Phase 1 plan, execution guide, testnet config saved |
| | | | | |

---

## Reference Documents

**Active:**
- `docs/PHASE1_EXECUTION_GUIDE.md` — **Step-by-step instructions for Phase 1 (READ THIS)**
- `docs/SPEC.md` — Original UI/design specifications

**Archived (completed/superseded — do NOT follow these):**
- `docs/archive/STANDALONE_MODE_PLAN.md` — Already implemented
- `docs/archive/STRATEGY_BUILDER_PLAN.md` — Superseded by Phase 1.2
- `docs/archive/MARKET_DATA_PLAN.md` — Phase 1-2 done, rest is future

---

**Commit format:** `feat: [description]` or `fix: [description]`
