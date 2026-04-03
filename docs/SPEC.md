# TradingCore — Full Specification

## Identity

**TradingCore** — standalone cryptocurrency trading dashboard with semi-auto execution.

- Platform: Flask web application (standalone, no external dependencies)
- Bahasa: Indonesian (Bahasa Indonesia)
- Vibe: Professional, data-driven, honest about risk
- Never hype trades. Never promise profit.

## Core Mission

1. **Flexible** — user-defined strategies per coin, per market condition
2. **Scalable** — easily add new strategies, indicators, or exchanges
3. **Controllable** — bot can be started/stopped, trades require confirmation
4. **Intelligent** — learns from past trades, evolves thresholds
5. **Safe** — testnet-first, risk management, circuit breakers

---

## Dashboard Layout (Current)

```text
┌─────────────────────────────────────────────────────────────────┐
│  [●] TradingCore Dashboard  [🧪 TESTNET]    [■ STOP] [▶ START] │
├──────────────┬──────────────────────────────┬───────────────────┤
│ MARKET PULSE │       LIVE SIGNALS           │   BOT CONTROLS   │
│              │                              │                  │
│ F&G: 42      │  BTC/USDT  [BUY]  [▶ EXEC] │  Strategy: [▼]   │
│ BTC Dom: 52% │  RSI: 28 | Conf: 72%        │  [+ New Strategy]│
│ BTC Trend: ↑ │  Entry: $98,240             │                  │
│              │  SL: -2.5% | TP: +7.5%      │  Interval: [▼]   │
│ Trending:    │  R:R: 1:3.0                 │  Coins: [▼]      │
│ SOL BNB ETH  │  Strategy: RSI Conservative │                  │
│              │                              │  [▶ START BOT]   │
├──────────────┴──────────────────────────────┴───────────────────┤
│  OPEN POSITIONS                              [Risk: 🟢 OK]     │
│  BTC/USDT  BUY @ $98,240  PnL: +1.2%  [CLOSE]                │
├─────────────────────────────────────────────────────────────────┤
│  STRATEGIES & BACKTEST                                         │
│  [RSI Conservative ✅] [EMA Cross ⬜] [+ New] [Templates]      │
│  Win Rate: 62%  |  PnL: +8.3%  |  [Backtest] [Edit]          │
├─────────────────────────────────────────────────────────────────┤
│  PERFORMANCE TRACKER                                           │
│  Total: 12 | Win: 7 | Loss: 5 | Win Rate: 58%                │
│  Best: +6.41% (SOL) | Worst: -3.26% (BNB)                    │
│  [LOG OUTCOME] [VIEW HISTORY] [RUN BACKTEST] [EVOLVE]         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Color Scheme

| Element | Color |
|---------|-------|
| Background | `#0a0e1a` (deep navy) |
| Card bg | `#111827` |
| Accent Green | `#00ff9d` |
| Accent Red | `#ff4757` |
| Accent Yellow | `#ffd700` |
| Text Primary | `#e2e8f0` |
| Text Secondary | `#64748b` |
| Border | `#1e293b` |

---

## Signal Engine Pipeline

```text
Step 1: STRATEGY SELECTION
- Load all active strategies from database
- Each strategy has its own coins, indicators, conditions

Step 2: MACRO CHECK
- Fear & Greed Index (alternative.me)
- BTC Dominance % (CoinGecko)
- BTC Trend (EMA50 check)
- Trending Coins (CoinGecko)

Step 3: MACRO FILTER (if enabled in strategy)
- Skip BUY if F&G > max_buy_threshold
- Reduce confidence if BTC below EMA50

Step 4: COIN SCREENING
- For each strategy, scan its assigned coins

Step 5: PER-COIN ANALYSIS
For each coin, calculate indicators as defined by strategy:
- RSI (Wilder's method, configurable period)
- EMA (configurable periods: 9, 21, 50, 200)
- MACD (12/26/9 default)
- Bollinger Bands (20/2 default)
- ATR (dynamic stop loss)
- VWAP
- Volume ratio vs 20-period average

Step 6: CONDITION EVALUATION
- Evaluate entry conditions per strategy (AND/OR logic)
- Each condition: {indicator, period, operator, value}
- Operators: <, >, <=, >=, ==, CROSS_ABOVE, CROSS_BELOW

Step 7: CONFIDENCE SCORE V2
| Factor              | Max Points |
|---------------------|-----------|
| RSI quality         | 25        |
| R:R bonus           | 20        |
| Volume              | 15        |
| Macro alignment     | 20        |
| Multi-TF confirm    | 10        |
| Trending bonus      | 10        |

Step 8: RISK CHECK
- Verify: balance >= minimum, daily loss < max, positions < max
- Calculate position size based on risk percentage
- Check circuit breaker status

Step 9: SIGNAL OUTPUT
- BUY/SELL with strategy name
- Entry price, SL price, TP price
- R:R ratio, Confidence score
- Suggested position size
- [EXECUTE] button (semi-auto) or auto-queue (full-auto)
```

---

## Configuration Parameters

### Trading Mode

| Mode | Duration | Target |
|------|----------|--------|
| SWING | 2-7 days | 5-10% |
| SCALP | 5-30 min | 0.5-1.5% |
| HYBRID | Both active | Mixed |

### Signal Parameters (defaults, overridden by strategy)

- RSI Buy Max: 40
- RSI Sell Min: 60
- RSI Extreme Buy: 30
- RSI Extreme Sell: 70
- EMA Fast: 9, EMA Slow: 21, EMA Trend: 200
- Min Volume Ratio: 1.0x

### Risk Management

- Risk per Trade: 2% of account balance
- Max Daily Loss: 5% of account balance
- Max Weekly Loss: 10% of account balance
- Max Open Positions: 3
- Max Position Size: 20% of account
- Min Balance: $5 (stop trading below this)
- Circuit Breaker: 3 consecutive losses → pause 60 min
- SL Mode: FIXED (2.5%) or DYNAMIC_ATR (1.5x ATR)
- Leverage: 1x default, 3x max (futures only)

### Execution Mode

| Mode | Behavior |
|------|----------|
| `semi_auto` | Signal appears → user clicks EXECUTE → order placed |
| `full_auto` | Signal appears → auto-execute after risk check (future) |
| `alert_only` | Signal appears → Telegram alert only, no execution |

### Exchange

- Primary: Binance (Spot + USDT-M Futures)
- Testnet: `testnet.binance.vision` (Spot), `testnet.binancefuture.com` (Futures)
- `use_testnet: true` → all orders go to testnet (default)

### Filters (toggleable)

- EMA200 Filter: ON/OFF
- Multi-TF Confirm: ON/OFF
- Fear & Greed Filter: ON/OFF
- BTC Dominance Filter: ON/OFF
- BTC Trend Filter: ON/OFF
- Skip RSI 35-40 Zone: ON/OFF
- Require Volume: ON/OFF
- Apply Lessons: ON/OFF
- Auto-Blacklist: ON/OFF

### Data Sources

- Exchange Data: Binance API (klines, ticker, orderbook)
- Fear & Greed: alternative.me
- Trending Coins: CoinGecko
- BTC Dominance: CoinGecko

### Notifications

- Telegram Bot Token + Chat ID (configured in dashboard Settings)
- Signal Format: DETAILED / COMPACT
- Notify on: new signal, bot start/stop, TP hit, SL hit, daily summary

---

## RSI — Wilder's Method (MANDATORY)

All RSI calculations MUST use Wilder's smoothing, not SMA. This matches TradingView and Binance.

```python
def calculate_rsi_wilder(closes, period=14):
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    rs = avg_gain / avg_loss if avg_loss > 0 else 0
    return 100 - (100 / (1 + rs))
```

---

## File Structure

```text
trading-dashboard/
├── app.py                          # Flask entry point
├── AGENT.md                        # Agent instructions (read first)
├── requirements.txt                # Python dependencies
├── config/
│   ├── bot_config.json             # All parameters + testnet keys
│   ├── bot_status.json             # Bot running state
│   └── watchlist.json              # Watched coins
├── routes/
│   ├── signals.py                  # GET /api/signals
│   ├── bot_control.py              # /api/bot/start, stop, status
│   ├── market.py                   # /api/market/pulse, prices
│   ├── performance.py              # /api/performance
│   ├── binance.py                  # /api/binance/* (execution)
│   ├── learning.py                 # /api/learning/*
│   ├── strategies.py               # /api/strategies/* (Phase 1.2)
│   ├── backtest.py                 # /api/backtest/* (Phase 1.3)
│   └── positions.py                # /api/positions/* (Phase 1.4)
├── strategies/
│   ├── signal_engine.py            # Core indicators (RSI, EMA, ATR, VWAP)
│   ├── screener.py                 # Coin screening & ranking
│   ├── strategy_engine.py          # Flexible strategy evaluator (Phase 1.2)
│   ├── strategy_templates.py       # 7 built-in templates (Phase 1.2)
│   ├── backtester.py               # Historical backtest engine (Phase 1.3)
│   ├── lessons.py                  # Pattern learning
│   └── evolution.py                # Adaptive thresholds
├── services/
│   ├── auth.py                     # Login + @require_auth decorator
│   ├── binance_client.py           # Binance Spot API client
│   ├── binance_futures.py          # Binance Futures API client (Phase 1.6)
│   ├── telegram_notifier.py        # Telegram notifications
│   ├── database.py                 # SQLite database (Phase 1.1)
│   ├── position_manager.py         # Position tracking (Phase 1.4)
│   └── risk_manager.py             # Risk management (Phase 1.5)
├── templates/
│   └── dashboard.html              # Main dashboard (single page)
├── static/
│   ├── style.css                   # All styles
│   └── app.js                      # Frontend logic
├── data/
│   ├── trading.db                  # SQLite database (Phase 1.1)
│   ├── trades.json                 # Legacy trade history
│   ├── signals.json                # Legacy signals
│   ├── lessons.json                # Learned patterns
│   └── thresholds.json             # Evolved thresholds
└── docs/
    ├── SPEC.md                     # This file
    └── PHASE1_EXECUTION_GUIDE.md   # Step-by-step build guide
```

---

## API Endpoints

### Market Data

```text
GET /api/market/pulse
→ { fear_greed, btc_dominance, btc_trend, trending[] }

GET /api/market/prices
→ { prices: [{ symbol, price, change_24h }] }
```

### Signals

```text
GET /api/signals
→ { signals: [{ symbol, side, rsi, confidence, entry, sl, tp, rr, mode, strategy_name }] }
```

### Bot Control

```text
GET  /api/bot/status     → { running, uptime, next_scan, active_strategies }
POST /api/bot/start      → { success: true }
POST /api/bot/stop       → { success: true, session_stats }
```

### Configuration

```text
GET  /api/config         → { mode, interval, ... all bot_config fields }
POST /api/config         → { success: true }
```

### Strategies (Phase 1.2)

```text
GET    /api/strategies              → List user strategies
POST   /api/strategies              → Create new strategy
GET    /api/strategies/<id>         → Get one strategy
PUT    /api/strategies/<id>         → Update strategy
DELETE /api/strategies/<id>         → Delete strategy
POST   /api/strategies/<id>/clone   → Clone strategy
POST   /api/strategies/<id>/activate    → Activate
POST   /api/strategies/<id>/deactivate  → Deactivate
GET    /api/strategies/templates    → List 7 built-in templates
POST   /api/strategies/from-template → Create from template
```

### Backtest (Phase 1.3)

```text
POST /api/backtest/run              → Run backtest on strategy
POST /api/backtest/preview          → Quick backtest without saving
GET  /api/backtest/history          → Past backtest results
GET  /api/backtest/<id>             → One backtest detail
```

### Positions (Phase 1.4)

```text
GET  /api/positions                 → Open positions
GET  /api/positions/history         → Closed positions
GET  /api/positions/summary         → Portfolio summary
POST /api/positions/<id>/close      → Close position manually
```

### Execution (Phase 1.6)

```text
POST /api/binance/execute           → Execute signal (semi-auto)
GET  /api/binance/account           → Account balance
GET  /api/binance/orders            → Open orders
```

### Performance

```text
GET  /api/performance               → Win rate, PnL stats
POST /api/performance/log           → Log trade outcome
```

### Telegram

```text
GET  /api/telegram/status           → { configured: true/false }
POST /api/telegram/test             → Test + save credentials
POST /api/telegram/send-test-signal → Send test notification
```

### Learning

```text
GET  /api/learning/stats            → Learning system statistics
GET  /api/learning/patterns         → Learned patterns
POST /api/learning/evolve           → Run threshold evolution
```

---

## Implementation Notes

- RSI MUST use Wilder's smoothing — same as TradingView/Binance
- EMA uses exponential smoothing standard
- ATR uses True Range standard
- Volume ratio = current volume / 20-period average
- Percentages stored as numbers: 2.5 means 2.5% (NOT 0.025)
- All API responses: `{ success: true/false, error: "message" }` on failure
- All endpoints use `@require_auth` decorator
- Database: SQLite at `data/trading.db`
- Default to testnet — live trading requires manual toggle in dashboard
