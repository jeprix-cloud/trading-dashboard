# TradingCore Dashboard

Platform trading crypto berbasis Flask dengan real-time signals, bot scheduler, dan sistem pembelajaran otomatis.

## Overview

TradingCore Dashboard adalah web-based trading control panel yang menggabungkan:
- **Signal Engine** — scan pasar otomatis dengan indikator teknikal presisi
- **Bot Scheduler** — menjalankan scan terjadwal dengan APScheduler
- **Learning System** — belajar dari riwayat trade untuk meningkatkan akurasi signal
- **Telegram Alerts** — notifikasi real-time ke Telegram

Dibangun dengan Flask + vanilla HTML/JS — ringan, cepat, dan mudah dikustomisasi.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    BROWSER (Dashboard)                  │
│  HTML/CSS/JS ──── Fetch API ──── Flask Server           │
└─────────────────────────────────────────────────────────┘
                    ↑                    ↓
              /api/signals     ┌─────────────────┐
              /api/bot/*       │  Signal Engine  │
              /api/performance  │  (Wilder RSI,   │
              /api/config      │   EMA, ATR,VWAP)│
              /api/learning    └─────────────────┘
                     ↑                ↓
              /api/market      ┌─────────────────┐
                               │  External APIs  │
                               │  Binance/CoinGec│
                               └─────────────────┘
```

## Features

| Feature | Status |
|---------|--------|
| Dashboard UI (dark theme, responsive) | ✅ |
| Market Pulse (F&G, BTC Dom, Trending) | ✅ |
| Live Signals (BUY/SELL cards) | ✅ |
| Bot Controls (Start/Stop + config) | ✅ |
| Performance Tracker | ✅ |
| Signal Engine (Wilder RSI, EMA, ATR, VWAP) | ✅ |
| Confidence Score V2 (100-point system) | ✅ |
| Bot Scheduler (APScheduler) | ✅ |
| Telegram Notifications | ✅ |
| Learning System (pattern recognition) | ✅ |
| Evolution System (auto threshold tuning) | ✅ |
| Coin Screener (pre-filter before scan) | ✅ |

## Quick Start

```bash
# Clone repo
git clone https://github.com/jeprix-cloud/trading-dashboard.git
cd trading-dashboard

# Buat virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Opsional) Set password custom
export DASHBOARD_PASSWORD=passwordkamu

# Run server
python app.py

# Buka browser
http://localhost:5000
```

Default password: `tradingcore2026`

## Dashboard Panels

### Market Pulse (kiri)
- Fear & Greed Index dengan gauge animasi
- BTC Dominance %
- BTC Trend (Bullish/Bearish)
- Trending Coins (top 5)

### Live Signals (tengah)
- Signal cards BUY (hijau) / SELL (merah)
- Setiap card: Symbol, RSI, Confidence, Entry, SL%, TP%, R:R
- Auto-refresh setiap 30 detik

### Bot Controls (kanan)
- Mode: SWING / SCALP / BOTH
- Interval: 5m / 15m / 30m / 1h
- Coins: Top 10 / 20 / 50
- Min R:R & Min Confidence
- START/STOP bot

### Performance Tracker (bawah)
- Total trades, Win, Loss, Win Rate
- Best & Worst trade
- LOG OUTCOME / VIEW HISTORY / RUN BACKTEST / EVOLVE

## Signal Engine

Menggunakan indikator teknikal berstandar TradingView/Binance:

- **RSI** — Wilder's Smoothed RSI (bukan SMA biasa)
- **EMA** — Fast (9), Slow (21), Trend (200)
- **ATR** — Average True Range dengan Wilder smoothing
- **VWAP** — Volume Weighted Average Price
- **Confidence Score** — Sistem 100 poin berdasarkan RSI + R:R + Volume + Macro + MultiTF + Trending

## Learning System

Bot belajar dari setiap trade yang di-log:

1. **Lessons** (`strategies/lessons.py`) — identifikasi pattern menang/kalah, auto-blacklist setup buruk
2. **Evolution** (`strategies/evolution.py`) — evolusi threshold RSI/confidence/R:R berdasarkan performa historis

API:
```
GET  /api/learning/lessons           → Summary patterns
POST /api/learning/lessons/learn     → Trigger learning dari trades
POST /api/learning/evolution/evolve  → Evolve thresholds
GET  /api/learning/evolution         → Status evolusi
```

## API Endpoints

```
# Market
GET  /api/market/pulse          → F&G, BTC Dom, Trending

# Signals
GET  /api/signals               → Daftar signal aktif
POST /api/signals/<id>/outcome  → Log hasil trade

# Bot
GET  /api/bot/status            → Status bot
POST /api/bot/start             → Start bot
POST /api/bot/stop              → Stop bot

# Performance
GET  /api/performance           → Stats keseluruhan
GET  /api/performance/history   → Riwayat trade
POST /api/performance/backtest  → Backtest signal saat ini

# Config
GET  /api/config                → Config aktif
POST /api/config                → Update config

# Telegram
GET  /api/telegram/status       → Status koneksi
POST /api/telegram/test         → Test + simpan credentials
POST /api/telegram/send-test-signal → Kirim test signal

# Learning
GET  /api/learning/lessons           → Summary pattern
POST /api/learning/lessons/learn     → Trigger learn
GET  /api/learning/lessons/blacklist → Lihat blacklist
POST /api/learning/evolution/evolve  → Evolve thresholds
GET  /api/learning/evolution         → Status evolusi
```

## Project Structure

```
trading-dashboard/
├── app.py                    ← Flask entry point
├── templates/
│   └── dashboard.html        ← Dashboard UI
├── static/
│   ├── style.css             ← Dark theme styles
│   └── app.js                ← API calls & UI logic
├── routes/
│   ├── auth.py               ← Login/logout
│   ├── bot_control.py        ← Start/stop bot + APScheduler
│   ├── config.py             ← Config management
│   ├── learning.py           ← Learning system API
│   ├── market.py             ← Market data
│   ├── performance.py        ← Trade stats & backtest
│   ├── signals.py            ← Signal reads
│   └── telegram.py           ← Telegram API
├── strategies/
│   ├── signal_engine.py      ← Wilder RSI, EMA, ATR, VWAP, scan
│   ├── screener.py           ← Coin pre-filter & ranking
│   ├── lessons.py            ← Pattern learning
│   └── evolution.py          ← Threshold evolution
├── services/
│   ├── auth.py               ← Password & session
│   └── telegram_notifier.py  ← Send Telegram messages
├── config/
│   ├── bot_config.json       ← Bot parameters
│   └── bot_status.json       ← Bot running state
├── data/
│   ├── signals.json          ← Current signals (runtime)
│   ├── trades.json           ← Trade history (runtime)
│   ├── lessons.json          ← Learned patterns (runtime)
│   └── thresholds.json       ← Evolved thresholds (runtime)
└── requirements.txt
```

## Requirements

```
Flask==3.0.0
requests==2.31.0
python-dotenv==1.0.0
apscheduler==3.10.4
```

## Documentation

Lihat `docs/SPEC.md` untuk spesifikasi lengkap sistem.

## Contributing

Lihat `CONTRIBUTING.md` untuk panduan development.

## License

MIT