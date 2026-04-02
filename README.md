# TradingCore Dashboard

Scalable & Flexible Trading Control Panel untuk OpenClaw.

## Overview

Web-based trading dashboard yang menghubungkan OpenClaw trading skills menjadi unified control panel. Dibangun dengan Flask + vanilla HTML/JS — ringan, fast, dan mudah dimodifikasi.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    BROWSER (Dashboard)                  │
│  HTML/CSS/JS ──── Fetch API ──── Flask Server           │
└─────────────────────────────────────────────────────────┘
                    ↑                    ↓
              /api/signals     ┌─────────────────┐
              /api/bot/*       │  Trading Engine │
              /api/performance  │  (OpenClaw)     │
              /api/config      └─────────────────┘
                     ↑                ↓
              /api/market      ┌─────────────────┐
                               │  External APIs  │
                               │  Binance/CoinGec│
                               └─────────────────┘
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python app.py

# Open browser
http://localhost:5000
```

## Dashboard Features

- **Market Pulse** — Fear & Greed, BTC Dominance, Trending Coins
- **Live Signals** — Real-time BUY/SELL cards dengan RSI, confidence, R:R
- **Bot Controls** — Start/Stop + semua parameter
- **Performance Tracker** — Win rate, best/worst trade

## Documentation

Lihat `docs/SPEC.md` untuk spesifikasi lengkap.

## untuk Developer

Lihat `CONTRIBUTING.md` untuk panduan development.

## License

MIT