"""
TradingCore Screener
====================
Pre-filters and ranks coins before running full signal analysis.
Reduces Binance API calls by eliminating poor candidates early.

Used by signal_engine.run_scan() to prioritize which coins to analyze.
"""

import requests
from datetime import datetime

BINANCE_BASE = "https://api.binance.com"

# ============================================================
# COIN LISTS
# ============================================================

# Full curated list (Top 50 by market cap, USDT pairs)
TOP_50_USDT = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
    "MATICUSDT", "SHIBUSDT", "LTCUSDT", "ATOMUSDT", "UNIUSDT",
    "ETCUSDT", "APTUSDT", "NEARUSDT", "FILUSDT", "ARBUSDT",
    "OPUSDT", "INJUSDT", "SUIUSDT", "TIAUSDT", "SEIUSDT",
    "RUNEUSDT", "FETUSDT", "WLDUSDT", "STXUSDT", "IMXUSDT",
    "MKRUSDT", "GRTUSDT", "AAVEUSDT", "SNXUSDT", "PENDLEUSDT",
    "ORDIUSDT", "THETAUSDT", "ALGOUSDT", "FTMUSDT", "EGLDUSDT",
    "FLOWUSDT", "AXSUSDT", "SANDUSDT", "MANAUSDT", "GALAUSDT",
    "APEUSDT", "CHZUSDT", "ENJUSDT", "LRCUSDT", "1INCHUSDT",
]


def get_coin_pool(pool_size=20):
    """
    Return the coin list based on pool size config.
    pool_size: 10, 20, or 50
    """
    return TOP_50_USDT[:min(pool_size, len(TOP_50_USDT))]


# ============================================================
# BINANCE TICKER SCREENER
# ============================================================

def fetch_24h_tickers(symbols=None):
    """
    Fetch 24h price change stats from Binance for all USDT pairs.
    Returns dict keyed by symbol.
    """
    url = f"{BINANCE_BASE}/api/v3/ticker/24hr"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        all_tickers = resp.json()
    except Exception as e:
        print(f"[Screener] Failed to fetch tickers: {e}")
        return {}

    # Filter to our symbols or just USDT pairs
    result = {}
    for t in all_tickers:
        sym = t.get("symbol", "")
        if not sym.endswith("USDT"):
            continue
        if symbols and sym not in symbols:
            continue
        result[sym] = {
            "symbol": sym,
            "price": float(t.get("lastPrice", 0)),
            "volume_usdt": float(t.get("quoteVolume", 0)),
            "change_pct": float(t.get("priceChangePercent", 0)),
            "high": float(t.get("highPrice", 0)),
            "low": float(t.get("lowPrice", 0)),
            "count": int(t.get("count", 0)),  # num of trades
        }
    return result


# ============================================================
# SCREENING FILTERS
# ============================================================

def screen_coins(pool_size=20, min_volume_usdt=1_000_000,
                 trending=None, exclude=None):
    """
    Screen coins from pool before full signal analysis.

    Args:
        pool_size: Number of coins to pull from TOP_50 list
        min_volume_usdt: Minimum 24h volume in USDT (default: $1M)
        trending: List of trending coin base symbols (e.g. ['BTC','ETH'])
        exclude: List of symbols to always skip (blacklist)

    Returns:
        List of symbols sorted by priority score (highest first)
    """
    coins = get_coin_pool(pool_size)
    exclude = set(exclude or [])

    # Fetch 24h ticker data
    tickers = fetch_24h_tickers(symbols=set(coins))

    screened = []

    for symbol in coins:
        # Skip excluded symbols
        if symbol in exclude:
            continue

        ticker = tickers.get(symbol)
        if not ticker:
            # If ticker not available, include anyway (fallback)
            screened.append({"symbol": symbol, "score": 0, "skipped": True})
            continue

        # Volume filter
        if ticker["volume_usdt"] < min_volume_usdt:
            continue

        # Score calculation
        score = 0

        # Volume score (higher volume = more reliable signals)
        vol = ticker["volume_usdt"]
        if vol >= 500_000_000:
            score += 40
        elif vol >= 100_000_000:
            score += 30
        elif vol >= 50_000_000:
            score += 20
        elif vol >= 10_000_000:
            score += 10

        # Trending bonus
        base = symbol.replace("USDT", "")
        if trending and base in trending:
            score += 25

        # Trade count (liquidity indicator)
        if ticker["count"] >= 100_000:
            score += 15
        elif ticker["count"] >= 50_000:
            score += 10
        elif ticker["count"] >= 10_000:
            score += 5

        # Volatility score (some volatility = better signal opportunities)
        price_range_pct = ((ticker["high"] - ticker["low"]) / ticker["low"] * 100) if ticker["low"] > 0 else 0
        if 3 <= price_range_pct <= 10:
            score += 10  # good volatility range
        elif price_range_pct > 10:
            score += 5   # high volatility (risky but active)

        screened.append({
            "symbol": symbol,
            "score": score,
            "volume_usdt": ticker["volume_usdt"],
            "change_pct": ticker["change_pct"],
            "price": ticker["price"],
            "is_trending": base in (trending or []),
        })

    # Sort by score descending
    screened.sort(key=lambda x: x["score"], reverse=True)

    return [s["symbol"] for s in screened]


# ============================================================
# QUICK MOVERS (for opportunity detection)
# ============================================================

def get_top_movers(pool_size=20, top_n=5):
    """
    Get top gaining and losing coins in the pool.
    Useful for identifying momentum opportunities.

    Returns:
        dict with 'gainers' and 'losers' lists
    """
    coins = get_coin_pool(pool_size)
    tickers = fetch_24h_tickers(symbols=set(coins))

    valid = [t for t in tickers.values() if t["volume_usdt"] > 1_000_000]
    valid.sort(key=lambda x: x["change_pct"], reverse=True)

    return {
        "gainers": [
            {"symbol": t["symbol"], "change_pct": t["change_pct"], "price": t["price"]}
            for t in valid[:top_n]
        ],
        "losers": [
            {"symbol": t["symbol"], "change_pct": t["change_pct"], "price": t["price"]}
            for t in valid[-top_n:][::-1]
        ],
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================
# SUMMARY
# ============================================================

def get_screener_summary(pool_size=20, trending=None):
    """
    Get a quick summary of screened coins with scores.
    Used for dashboard/debug info.
    """
    coins = get_coin_pool(pool_size)
    tickers = fetch_24h_tickers(symbols=set(coins))
    trending = trending or []

    summary = []
    for symbol in coins:
        ticker = tickers.get(symbol, {})
        base = symbol.replace("USDT", "")
        summary.append({
            "symbol": symbol,
            "price": ticker.get("price", 0),
            "volume_usdt": ticker.get("volume_usdt", 0),
            "change_pct": ticker.get("change_pct", 0),
            "is_trending": base in trending,
        })

    return {
        "pool_size": pool_size,
        "coins": summary,
        "timestamp": datetime.now().isoformat(),
    }
