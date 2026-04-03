# TradingCore Strategy Builder — Specification

## Overview

Add modular strategy builder to TradingCore Dashboard. Users can create custom trading strategies by combining indicators with AND/OR/NOT logic, backtest them against historical data, and run them live for real-time alerts.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     DASHBOARD                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Strategy   │  │   Backtest  │  │    Live     │     │
│  │   Builder   │  │   Results   │  │   Monitor   │     │
│  └──────┬──────┘  └─────────────┘  └──────┬──────┘     │
│         │                                 │            │
│  ┌──────▼──────────────────────────────────▼──────┐    │
│  │              Strategy Engine                  │    │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐          │    │
│  │  │ RSI  │ │ EMA  │ │MACD  │ │ BB   │  ...     │    │
│  │  └──────┘ └──────┘ └──────┘ └──────┘          │    │
│  │                                             │    │
│  │  ┌────────────────────────────────────────┐  │    │
│  │  │  Condition Builder (AND/OR/NOT)       │  │    │
│  │  └────────────────────────────────────────┘  │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## Features

### 1. Indicator Library

All indicators from `strategies/signal_engine.py` exposed as modular functions:

| Indicator | Parameters | Description |
|-----------|------------|-------------|
| RSI (Wilder) | period (default 14) | Wilder's Smoothed RSI |
| EMA | period (default 50, 200) | Exponential Moving Average |
| SMA | period | Simple Moving Average |
| MACD | fast, slow, signal | MACD histogram |
| Bollinger Bands | period, std_dev | Upper/Middle/Lower bands |
| ATR | period (default 14) | Average True Range |
| VWAP | timeframe | Volume Weighted Average Price |
| Stochastic | k_period, d_period | Stochastic Oscillator |
| Volume | threshold | Volume spike detection |
| Price vs MA | period | Price above/below MA |
| Funding Rate | exchange | Binance funding rate |
| Open Interest | symbol | Futures open interest |

### 2. Condition Builder

User can build entry/exit conditions:

```
Entry Conditions (example):
  RSI < 30 AND EMA50 > EMA200 AND Volume > 1.5x

Exit Conditions (example):
  RSI > 70 OR Price < EMA200 OR ATR > 3%
```

**Condition Types:**
- `AND` — all conditions must be true
- `OR` — any condition must be true
- `NOT` — negate a condition
- `CROSS` — crossover detection (e.g., RSI crosses 30)

**Supported Operators:**
- `<`, `>`, `<=`, `>=`, `==`, `!=`
- `CROSS_ABOVE`, `CROSS_BELOW`

### 3. Strategy Templates

Pre-built starter strategies:

| Template | Conditions | Description |
|----------|------------|-------------|
| RSI Oversold | RSI < 30 | Classic oversold bounce |
| EMA Cross Bullish | EMA9 > EMA21 AND Price > EMA21 | Golden cross |
| MACD Momentum | MACD > Signal AND MACD > 0 | MACD bullish |
| Volatility Breakout | ATR > 1.5x AND Price > UpperBB | BB squeeze breakout |
| Mean Reversion | RSI < 30 AND Price < LowerBB | Oversold + oversold |
| Trend Following | EMA50 > EMA200 AND RSI > 50 | Trend confirmation |
| Scalp Quick | RSI < 35 AND Volume > 2x | Fast scalp entry |

### 4. Multi-Timeframe Analysis

Combine signals from multiple timeframes:

```
1h: EMA50 > EMA200 → Uptrend confirmed
15m: RSI < 30 → Pullback entry
5m: Volume spike → Momentum confirmation
→ BUY signal generated
```

### 5. Backtesting Engine

Test strategies against historical data:

- Fetch historical klines (up to 90 days)
- Run strategy logic on each candle
- Calculate: Win Rate, Total Trades, Profit/Loss, Max Drawdown, Sharpe Ratio
- Generate performance report with chart

### 6. Live Mode

Run strategies in real-time:

- Scan coins at configured interval
- Evaluate conditions against live data
- Generate BUY/SELL signals
- Send to Telegram with strategy name + coin + entry price
- Track open positions and outcomes

### 7. Telegram Alerts

Customizable alerts per strategy:

```
📊 [STRATEGY_NAME] SIGNAL
🪙 {symbol}
📈 {side} Entry: {entry_price}
🔧 RSI: {rsi_value} | Conf: {confidence}%
📉 SL: {sl}% | 📈 TP: {tp}%
⏱️ Timeframe: {tf}
```

---

## File Structure (New Files)

```
trading-dashboard/
├── strategies/
│   ├── indicators.py          # NEW: Modular indicator functions
│   ├── condition_parser.py    # NEW: Parse condition strings
│   ├── strategy_engine.py     # NEW: Evaluate conditions + generate signals
│   ├── backtester.py          # NEW: Backtesting engine
│   └── templates.py           # NEW: Pre-built strategy templates
├── routes/
│   ├── strategies.py          # NEW: API routes for strategy CRUD
│   ├── backtest.py            # NEW: API routes for backtesting
│   └── live.py                # NEW: API routes for live mode
├── templates/
│   └── dashboard.html         # MODIFY: Add strategy builder UI
├── static/
│   ├── app.js                  # MODIFY: Add strategy UI logic
│   └── style.css               # MODIFY: Add strategy builder styles
└── config/
    └── strategies.json         # NEW: Saved strategies storage
```

---

## API Endpoints (New)

### Strategy Management

```
GET    /api/strategies              → List all saved strategies
POST   /api/strategies              → Create new strategy
GET    /api/strategies/<id>         → Get strategy details
PUT    /api/strategies/<id>         → Update strategy
DELETE /api/strategies/<id>         → Delete strategy
POST   /api/strategies/<id>/clone   → Clone a strategy
```

### Backtesting

```
POST   /api/backtest/run            → Run backtest
        Body: { strategy_id, symbol, start_date, end_date }
        Response: { trades, win_rate, profit_loss, max_drawdown, sharpe }
GET    /api/backtest/history/<id>   → Get backtest result
```

### Live Mode

```
POST   /api/live/start              → Start live strategy
        Body: { strategy_id, symbols[], interval }
POST   /api/live/stop               → Stop live strategy
GET    /api/live/status             → Get active strategies
```

### Indicators (Reference)

```
GET    /api/indicators              → List available indicators + params
GET    /api/indicators/<name>/value → Get current value for a coin
        Query: ?symbol=BTCUSDT&period=14
```

---

## UI Components

### Strategy Builder Modal

```
┌─────────────────────────────────────────────────────────┐
│  Strategy Builder                                    [X] │
├─────────────────────────────────────────────────────────┤
│  Name: [________________]                               │
│  Mode: [SCALP ▼]  Timeframe: [15m ▼]                    │
├─────────────────────────────────────────────────────────┤
│  ENTRY CONDITIONS                                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Indicator    │ Operator │ Value │ Action       │    │
│  ├─────────────────────────────────────────────────┤    │
│  │ [RSI      ▼] │ [<      ▼] │ [30 ] │ [🗑]       │    │
│  │ [EMA 50   ▼] │ [>      ▼] │ [EMA200▼]│ [🗑]    │    │
│  │ [+ Add condition ▼]                             │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Logic: (•) AND  ( ) OR                                 │
├─────────────────────────────────────────────────────────┤
│  EXIT CONDITIONS                                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │ [Same structure as Entry]                       │    │
│  └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  PARAMETERS                                             │
│  Entry Price: (•) Current  ( ) Last Close              │
│  Stop Loss: [2.5]%  Take Profit: [7.5]%                 │
│  Min Confidence: [60]%                                  │
├─────────────────────────────────────────────────────────┤
│  [Cancel]              [Save Strategy] [Start Backtest] │
└─────────────────────────────────────────────────────────┘
```

### Backtest Results Panel

```
┌─────────────────────────────────────────────────────────┐
│  Backtest Results: RSI Oversold on BTCUSDT              │
├─────────────────────────────────────────────────────────┤
│  Period: 2026-01-01 to 2026-03-31                       │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ Trades   │ │ Win Rate │ │ Profit   │ │Max DD    │     │
│  │   24     │ │  66.7%   │ │ +12.4%   │ │  -5.2%   │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│                                                         │
│  [Equity Curve Chart]                                   │
│                                                         │
│  Recent Trades:                                         │
│  +3.2% BTCUSDT 2026-03-28                               │
│  -1.8% BTCUSDT 2026-03-26                               │
│  +5.1% BTCUSDT 2026-03-24                               │
└─────────────────────────────────────────────────────────┘
```

### Live Monitor Panel

```
┌─────────────────────────────────────────────────────────┐
│  Active Strategies                                       │
├─────────────────────────────────────────────────────────┤
│  ● RSI Oversold (15m)    BTC,ETH,SOL    ▶ Running       │
│  ● EMA Cross (1h)        BTC,ETH        ▶ Running       │
│  ○ Scalp Quick (5m)      ALERT         ⏸ Paused         │
├─────────────────────────────────────────────────────────┤
│  Recent Signals (Live)                                  │
│  ✅ 12:30 BTCUSDT BUY  RSI:28 Conf:75%  SL:2% TP:6%    │
│  ✅ 12:15 ETHUSDT BUY  RSI:29 Conf:68%  SL:2.5% TP:7%  │
└─────────────────────────────────────────────────────────┘
```

---

## Data Models

### Strategy Schema

```json
{
  "id": "uuid",
  "name": "RSI Oversold Bounce",
  "mode": "SWING",
  "timeframe": "15m",
  "entry_conditions": [
    { "indicator": "RSI", "params": { "period": 14 }, "operator": "<", "value": 30 },
    { "indicator": "EMA", "params": { "period": 50 }, "operator": ">", "value_ref": "EMA", "value_params": { "period": 200 } }
  ],
  "entry_logic": "AND",
  "exit_conditions": [
    { "indicator": "RSI", "params": { "period": 14 }, "operator": ">", "value": 70 }
  ],
  "exit_logic": "OR",
  "stop_loss_pct": 2.5,
  "take_profit_pct": 7.5,
  "min_confidence": 60,
  "coins": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
  "created_at": "2026-04-03T12:00:00Z",
  "updated_at": "2026-04-03T12:00:00Z"
}
```

### Backtest Result Schema

```json
{
  "id": "uuid",
  "strategy_id": "uuid",
  "symbol": "BTCUSDT",
  "start_date": "2026-01-01",
  "end_date": "2026-03-31",
  "trades": [
    { "date": "2026-03-28", "side": "BUY", "entry": 65000, "exit": 67000, "pnl_pct": 3.08 }
  ],
  "total_trades": 24,
  "winning_trades": 16,
  "win_rate": 66.7,
  "profit_loss_pct": 12.4,
  "max_drawdown": -5.2,
  "sharpe_ratio": 1.45
}
```

---

## Implementation Phases

### Phase 1: Core Infrastructure
1. Extract indicator functions from `signal_engine.py` → `strategies/indicators.py`
2. Create condition parser → `strategies/condition_parser.py`
3. Build strategy engine → `strategies/strategy_engine.py`
4. Add strategy API routes → `routes/strategies.py`
5. Create strategy storage in `config/strategies.json`

### Phase 2: Strategy Builder UI
1. Add Strategy Builder modal to `dashboard.html`
2. Add JavaScript for condition builder (add/remove rows)
3. Add styles for strategy builder panel
4. Connect UI to strategy API

### Phase 3: Backtesting
1. Create `strategies/backtester.py`
2. Add backtest API routes → `routes/backtest.py`
3. Add backtest results UI panel
4. Add equity curve chart (Chart.js)

### Phase 4: Live Mode
1. Extend strategy engine for live evaluation
2. Add live mode API routes → `routes/live.py`
3. Add live monitor panel to dashboard
4. Connect to existing Telegram notification system

### Phase 5: Templates & Polish
1. Add pre-built strategy templates → `strategies/templates.py`
2. Add strategy cloning feature
3. Add performance analytics
4. Mobile responsive optimization

---

## Dependencies

Add to `requirements.txt`:
```
numpy>=1.24.0
pandas>=2.0.0
yfinance>=0.2.28
```

Add to `templates/dashboard.html`:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

---

## Testing Checklist

- [ ] Create a custom strategy
- [ ] Save and reload strategy
- [ ] Run backtest and verify results
- [ ] Start live mode and receive Telegram alert
- [ ] Stop live mode
- [ ] Clone existing strategy
- [ ] Delete strategy
- [ ] Verify all indicators calculate correctly
- [ ] Verify condition logic (AND/OR/NOT/CROSS)
- [ ] Mobile responsive check

---

## Example: Building RSI Oversold Strategy

1. Click "New Strategy" button
2. Name: "RSI Oversold"
3. Mode: SWING, Timeframe: 1h
4. Add Entry Condition:
   - Indicator: RSI, Period: 14, Operator: <, Value: 30
5. Add Entry Condition:
   - Indicator: Price vs EMA, Period: 50, Operator: >, Compare: EMA 200
6. Entry Logic: AND
7. Add Exit Condition:
   - Indicator: RSI, Period: 14, Operator: >, Value: 70
8. Exit Logic: OR
9. Stop Loss: 3%, Take Profit: 9%
10. Min Confidence: 55%
11. Select coins: BTCUSDT, ETHUSDT, SOLUSDT
12. Click "Save Strategy"
13. Click "Run Backtest" → see results
14. If satisfied, click "Start Live" → receive alerts on Telegram

---

## Notes for Antigravity

1. Start from `strategies/indicators.py` — extract all calculation functions from `signal_engine.py`
2. Use existing patterns in `routes/market.py` for API route structure
3. Auth is already implemented via `require_auth` decorator
4. Telegram integration already exists in `services/telegram_notifier.py`
5. For Chart.js charts, check existing patterns in Phase 5 spec
6. Test incrementally — each phase should be runnable and testable

---

**Commit format:** `feat: Strategy Builder - [description]`
**Branch strategy:** `feature/strategy-builder` → `master`