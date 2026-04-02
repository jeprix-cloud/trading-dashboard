# TradingCore — Full Specification

## Identity

**TradingCore** — cryptocurrency trading dashboard agent built on OpenClaw.

- Bahasa: Indonesian (Bahasa Indonesia)
- Vibe: Professional, data-driven, honest about risk
- Never hype trades. Never promise profit.

## Core Mission

1. **Flexible** — user can configure every parameter without touching code
2. **Scalable** — easily add new strategies, coins, or data sources
3. **Controllable** — bot can be started and stopped on demand
4. **Intelligent** — learns from past trades to improve future signals

---

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  TradingCore Dashboard        [● BOT ACTIVE]  [■ STOP BOT]     │
├──────────────┬──────────────────────────────┬───────────────────┤
│ MARKET PULSE │       LIVE SIGNALS            │   BOT CONTROLS    │
│              │                              │                   │
│ F&G: 42      │  BTC/USDT  BUY              │  Mode: [SWING ▼]  │
│ BTC Dom: 52% │  RSI: 28 | Conf: 72%         │                   │
│ BTC Trend: ↑ │  Entry: $98,240              │  Interval: [15m▼] │
│              │  SL: -2.5% | TP: +7.5%       │                   │
│ Trending:    │  R:R: 1:3.0                  │  Coins: [20 ▼]   │
│ SOL BNB ETH  │                              │                   │
│              │  ETH/USDT  SELL              │  Min R:R: [2.0▼]  │
│              │  RSI: 71 | Conf: 68%         │  Min Conf: [50▼]  │
│              │  Entry: $3,420               │                   │
│              │  SL: +2.5% | TP: -7.5%       │  [▶ START BOT]   │
├──────────────┴──────────────────────────────┴───────────────────┤
│  PERFORMANCE TRACKER                                              │
│  Total: 2 | Win: 1 | Loss: 1 | Win Rate: 50%                    │
│  Best: +6.41% (SOL) | Worst: -3.26% (BNB)                        │
│  [LOG OUTCOME] [VIEW HISTORY] [RUN BACKTEST] [EVOLVE]             │
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

## Bot Controls Panel Parameters

| Control | Options |
|---------|---------|
| Mode | Swing / Scalp / Both |
| Scan Interval | 5m / 15m / 30m / 1h |
| Coin Pool | Top 10 / 20 / 50 |
| Min R:R | 1.5 / 2.0 / 2.5 / 3.0 |
| Min Confidence | 30 / 50 / 70 |
| RSI Buy Max | 30 / 35 / 40 |
| RSI Sell Min | 60 / 65 / 70 |
| EMA200 Filter | ON / OFF |
| F&G Filter | ON / OFF |
| Multi-TF Confirmation | ON / OFF |

---

## Signal Engine Pipeline

```
Step 1: MACRO CHECK
- Fear & Greed Index (alternative.me)
- BTC Dominance % (CoinGecko)
- BTC Trend (EMA50 check)
- Trending Coins (CoinGecko)

Step 2: MACRO FILTER (if enabled)
- Skip BUY if F&G > max_buy_threshold
- Reduce confidence if BTC below EMA50

Step 3: COIN SCREENING
- Get top N coins by volume

Step 4: PER-COIN ANALYSIS
For each coin:
- RSI (Wilder's method)
- EMA9, EMA21 (scalp)
- EMA200 (swing trend filter)
- ATR (dynamic stop loss)
- VWAP
- Volume ratio vs 20-period average

Step 5: CONFIDENCE SCORE V2
| Factor | Max Points |
|--------|-----------|
| RSI quality | 25 |
| R:R bonus | 20 |
| Volume | 15 |
| Macro alignment | 20 |
| Multi-TF confirmation | 10 |
| Trending bonus | 10 |

Step 6: SIGNAL OUTPUT
- BUY/SELL/HOLD
- Entry price
- Stop loss (fixed % or ATR-based)
- Take profit (TP1, TP2)
- R:R ratio
- Confidence score
```

---

## Configuration Parameters

### [1] Mode Trading
- SWING: 2-7 hari, target 5-10%
- SCALP: 5-30 menit, target 1%
- HYBRID: keduanya aktif
- CUSTOM: custom timeframe + targets

### [2] Signal Parameters
- RSI Buy Max: 40 (default)
- RSI Sell Min: 60 (default)
- RSI Extreme Buy: 30
- RSI Extreme Sell: 70
- EMA Fast: 9, EMA Slow: 21, EMA Trend: 200
- Min Volume Ratio: 1.0x
- Vol Spike Bonus: 1.5x

### [3] Risk Management
- Max Risk/Trade: 2% of account
- Min R:R: 2.0 (swing), 1.5 (scalp)
- Max Position: 20% of account
- SL Mode: FIXED or DYNAMIC_ATR
- Fixed SL: 2.5%
- ATR Multiplier: 1.5x
- Scalp SL: 0.3%, TP: 1.0%
- Max Signals/Day: 10

### [4] Filters
- EMA200 Filter: ON/OFF
- Multi-TF Confirm: ON/OFF
- Fear & Greed Filter: ON/OFF
- BTC Dominance Filter: ON/OFF
- BTC Trend Filter: ON/OFF
- Skip RSI 35-40: ON/OFF
- Require Volume: ON/OFF
- Apply Lessons: ON/OFF
- Auto-Blacklist: ON/OFF

### [5] Data Sources
- Primary Exchange: Binance
- Backup Exchange: Bybit
- Fear & Greed: alternative.me
- Trending: CoinGecko
- BTC Dominance: CoinGecko
- Open Interest: Binance Futures

### [6] Notifications
- Alert Bot Token: [hidden]
- Chat ID: [hidden]
- Signal Format: DETAILED / COMPACT
- Include Chart: OFF (future)

---

## Commands Reference

### Bot Control
- `/bot start` — Start bot dengan config saat ini
- `/bot stop` — Stop bot
- `/bot status` — Show status, uptime, next scan
- `/bot restart` — Restart bot
- `/bot log` — View recent logs

### Trading
- `/analyze BTC` — Full swing analysis
- `/scalp ETH` — Scalp analysis 1M
- `/screen` — Manual scan
- `/screen 50` — Scan top 50 coins
- `/signal BTC` — Quick signal check
- `/mode swing/scalp/hybrid` — Change mode

### Configuration
- `/config` — Interactive config menu
- `/config rsi 35` — Set RSI buy max
- `/config rr 2.5` — Set min R:R
- `/config reset` — Reset to defaults
- `/config show` — Show current config

### Dashboard
- `/dashboard` — Open Canvas web dashboard
- `/panel` — Alias untuk dashboard

---

## RSI Wilder's Method

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

```
trading-dashboard/
├── app.py                    # Flask application
├── config/
│   ├── bot_config.json       # All parameters
│   └── bot_status.json       # Running state
├── routes/
│   ├── signals.py            # /api/signals
│   ├── bot_control.py        # /api/bot/start, /api/bot/stop
│   ├── market.py             # /api/market/*
│   └── performance.py        # /api/performance/*
├── strategies/
│   └── signal_engine.py      # Core pipeline
├── templates/
│   └── dashboard.html        # Main dashboard
├── static/
│   └── dashboard.js          # Frontend logic
├── data/
│   └── trades.json            # Trade history
├── docs/
│   └── SPEC.md               # This file
└── requirements.txt
```

---

## API Endpoints

### GET /api/market/pulse
```json
{
  "fear_greed": 42,
  "btc_dominance": 52.3,
  "btc_trend": "bullish",
  "trending": ["SOL", "BNB", "ETH"]
}
```

### GET /api/signals
```json
{
  "signals": [
    {
      "symbol": "BTC/USDT",
      "side": "BUY",
      "rsi": 28,
      "confidence": 72,
      "entry": 98240,
      "sl": 2.5,
      "tp": 7.5,
      "rr": 3.0,
      "mode": "SWING"
    }
  ]
}
```

### POST /api/bot/start
```json
{"config": {...}}
```

### POST /api/bot/stop
```json
{}
```

### GET /api/performance
```json
{
  "total_trades": 2,
  "wins": 1,
  "losses": 1,
  "win_rate": 50,
  "best_trade": {"symbol": "SOL", "pnl": 6.41},
  "worst_trade": {"symbol": "BNB", "pnl": -3.26}
}
```

### GET /api/config
```json
{"mode": "SWING", "interval": "15m", ...}
```

### POST /api/config
```json
{"mode": "SCALP", "min_rr": 2.5, ...}
```

---

## Implementation Notes

- RSI harus Wilder's method — sama dengan TradingView/Binance
- EMA calculation pakai exponential smoothing standard
- ATR pakai True Range standard
- Volume ratio = current volume / 20-period average
- All percentages dalam desimal (2.5% = 0.025)
