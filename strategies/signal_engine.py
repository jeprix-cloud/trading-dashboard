"""
TradingCore Signal Engine
=========================
Technical indicators (Wilder RSI, EMA, ATR, VWAP) and
confidence-scored signal generation from Binance OHLCV data.
"""

import time
import uuid
import requests
from datetime import datetime


# ============================================================
# TECHNICAL INDICATORS
# ============================================================

def calculate_rsi_wilder(closes, period=14):
    """
    Wilder's Smoothed RSI — matches TradingView / Binance.
    NOT simple moving average — this is critical.
    Requires at least (period + 1) data points.
    """
    if len(closes) < period + 1:
        return 50.0  # neutral fallback

    deltas = []
    for i in range(1, len(closes)):
        deltas.append(closes[i] - closes[i - 1])

    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    # Initial average (SMA seed)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Wilder smoothing
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def calculate_ema(prices, period):
    """Exponential Moving Average"""
    if len(prices) < period:
        return prices[-1] if prices else 0
    ema = sum(prices[:period]) / period
    multiplier = 2 / (period + 1)
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return round(ema, 8)


def calculate_atr(highs, lows, closes, period=14):
    """
    Average True Range with Wilder smoothing.
    True Range = max(H-L, |H-PC|, |L-PC|)
    """
    if len(closes) < period + 1:
        return 0
    trs = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        )
        trs.append(tr)

    # Wilder smoothing for ATR
    atr = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr = (atr * (period - 1) + trs[i]) / period
    return round(atr, 8)


def calculate_vwap(closes, volumes):
    """Volume Weighted Average Price"""
    cum_vol = sum(volumes)
    if cum_vol == 0:
        return sum(closes) / len(closes) if closes else 0
    cum_pv = sum(c * v for c, v in zip(closes, volumes))
    return round(cum_pv / cum_vol, 8)


# ============================================================
# CONFIDENCE SCORE V2 (100-point system)
# ============================================================

def calculate_confidence(rsi, rr_ratio, volume_ratio, macro_score,
                         multitf_aligned=False, trending=False):
    """
    Confidence Score V2 — Max 100 points.
    Breakdown:
      RSI quality:       25 pts
      R:R bonus:         20 pts
      Volume:            15 pts
      Macro alignment:   20 pts
      Multi-TF confirm:  10 pts
      Trending bonus:    10 pts
    """
    score = 0

    # RSI quality (25 pts max)
    if rsi < 25 or rsi > 75:
        score += 25
    elif rsi < 30 or rsi > 70:
        score += 20
    elif rsi < 35 or rsi > 65:
        score += 12
    elif 35 <= rsi <= 40 or 60 <= rsi <= 65:
        score += 5   # WARNING ZONE
    else:
        score += 0

    # R:R bonus (20 pts max)
    if rr_ratio >= 3.0:
        score += 20
    elif rr_ratio >= 2.5:
        score += 15
    elif rr_ratio >= 2.0:
        score += 10

    # Volume (15 pts max)
    if volume_ratio >= 2.0:
        score += 15
    elif volume_ratio >= 1.5:
        score += 10
    elif volume_ratio >= 1.0:
        score += 5

    # Macro alignment (20 pts max)
    if macro_score >= 80:
        score += 20
    elif macro_score >= 60:
        score += 15
    elif macro_score >= 40:
        score += 10
    else:
        score += 5

    # Multi-TF confirmation (10 pts)
    if multitf_aligned:
        score += 10

    # Trending bonus (10 pts)
    if trending:
        score += 10

    return min(score, 100)


# ============================================================
# BINANCE DATA FETCHER
# ============================================================

BINANCE_BASE = "https://api.binance.com"


def fetch_klines(symbol, interval="15m", limit=200):
    """
    Fetch OHLCV klines from Binance public API.
    Returns dict with lists: opens, highs, lows, closes, volumes
    or None on failure.
    """
    url = f"{BINANCE_BASE}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[Signal Engine] Failed to fetch {symbol}: {e}")
        return None

    if not data or len(data) < 30:
        return None

    opens = [float(k[1]) for k in data]
    highs = [float(k[2]) for k in data]
    lows = [float(k[3]) for k in data]
    closes = [float(k[4]) for k in data]
    volumes = [float(k[5]) for k in data]

    return {
        "opens": opens,
        "highs": highs,
        "lows": lows,
        "closes": closes,
        "volumes": volumes,
    }


def get_top_coins(pool_size=20):
    """
    Get top coins by market cap from Binance exchange-info,
    filtered to USDT pairs that are trading.
    """
    # Curated list covering top coins by market cap
    top_list = [
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
    return top_list[:min(pool_size, len(top_list))]


# ============================================================
# SIGNAL ANALYSIS
# ============================================================

def analyze_coin(symbol, config, market_data=None):
    """
    Full technical analysis for one coin.
    Returns signal dict or None if no signal.

    Args:
        symbol: Binance symbol e.g. "BTCUSDT"
        config: Bot config dict
        market_data: Optional dict with fear_greed, btc_trend, trending list
    """
    interval = config.get("interval", "15m")
    klines = fetch_klines(symbol, interval=interval, limit=200)
    if not klines:
        return None

    closes = klines["closes"]
    highs = klines["highs"]
    lows = klines["lows"]
    volumes = klines["volumes"]
    current_price = closes[-1]

    # ---- Calculate indicators ----
    rsi = calculate_rsi_wilder(closes, period=14)

    ema_fast = calculate_ema(closes, config.get("ema_fast", 9))
    ema_slow = calculate_ema(closes, config.get("ema_slow", 21))
    ema_trend = calculate_ema(closes, config.get("ema_trend", 200))

    atr = calculate_atr(highs, lows, closes, period=14)
    vwap = calculate_vwap(closes[-20:], volumes[-20:])

    # Volume ratio (current vs 20-period avg)
    avg_vol = sum(volumes[-21:-1]) / 20 if len(volumes) >= 21 else sum(volumes) / len(volumes)
    volume_ratio = volumes[-1] / avg_vol if avg_vol > 0 else 1.0

    # ---- Determine signal side ----
    rsi_buy_max = config.get("rsi_buy_max", 40)
    rsi_sell_min = config.get("rsi_sell_min", 60)

    side = None
    if rsi <= rsi_buy_max and ema_fast > ema_slow:
        side = "BUY"
    elif rsi >= rsi_sell_min and ema_fast < ema_slow:
        side = "SELL"
    else:
        return None  # No clear signal

    # ---- Skip RSI 35-40 warning zone ----
    if config.get("skip_rsi_35_40", False):
        if 35 <= rsi <= 40 or 60 <= rsi <= 65:
            return None

    # ---- EMA 200 filter ----
    if config.get("ema200_filter", False):
        if side == "BUY" and current_price < ema_trend:
            return None
        if side == "SELL" and current_price > ema_trend:
            return None

    # ---- Fear & Greed filter ----
    if config.get("fg_filter", False) and market_data:
        fg = market_data.get("fear_greed", 50)
        if side == "BUY" and fg > 75:
            return None  # Don't buy in extreme greed
        if side == "SELL" and fg < 25:
            return None  # Don't sell in extreme fear

    # ---- Volume filter ----
    if config.get("require_volume", True):
        if volume_ratio < 0.8:
            return None

    # ---- Calculate SL / TP ----
    sl_mode = config.get("sl_mode", "FIXED")

    if sl_mode == "ATR" and atr > 0:
        atr_mult = config.get("atr_multiplier", 1.5)
        sl_pct = round((atr * atr_mult / current_price) * 100, 2)
    else:
        if side == "BUY":
            sl_pct = config.get("sl_fixed_buy", 2.5)
        else:
            sl_pct = config.get("sl_fixed_sell", 2.5)

    # TP based on min R:R
    min_rr = config.get("min_rr", 2.0)
    tp_pct = round(sl_pct * min_rr, 2)
    rr_ratio = round(tp_pct / sl_pct, 1) if sl_pct > 0 else 0

    # ---- Macro score ----
    macro_score = 50  # default
    if market_data:
        fg = market_data.get("fear_greed", 50)
        btc_trend = market_data.get("btc_trend", "neutral")
        # Favorable macro: buying in fear or selling in greed
        if side == "BUY" and fg < 40:
            macro_score = 80
        elif side == "BUY" and fg < 50:
            macro_score = 60
        elif side == "SELL" and fg > 60:
            macro_score = 80
        elif side == "SELL" and fg > 50:
            macro_score = 60

        if btc_trend == "bullish" and side == "BUY":
            macro_score = min(macro_score + 10, 100)
        elif btc_trend == "bearish" and side == "SELL":
            macro_score = min(macro_score + 10, 100)

    # ---- Multi-TF alignment (simplified) ----
    multitf_aligned = False
    if config.get("multitf_filter", False):
        # Check if price vs EMA200 aligns with signal direction
        multitf_aligned = (side == "BUY" and current_price > ema_trend) or \
                          (side == "SELL" and current_price < ema_trend)
    else:
        # If filter is off, give benefit of the doubt
        multitf_aligned = True

    # ---- Trending bonus ----
    is_trending = False
    if market_data and market_data.get("trending"):
        # Extract base symbol (e.g. "BTCUSDT" -> "BTC")
        base = symbol.replace("USDT", "")
        is_trending = base in market_data["trending"]

    # ---- Confidence score ----
    confidence = calculate_confidence(
        rsi=rsi,
        rr_ratio=rr_ratio,
        volume_ratio=volume_ratio,
        macro_score=macro_score,
        multitf_aligned=multitf_aligned,
        trending=is_trending
    )

    # ---- Format symbol for display ----
    display_symbol = symbol.replace("USDT", "/USDT")

    return {
        "id": f"sig_{uuid.uuid4().hex[:8]}",
        "symbol": display_symbol,
        "side": side,
        "rsi": rsi,
        "confidence": confidence,
        "entry": round(current_price, 2),
        "sl": sl_pct,
        "tp": tp_pct,
        "rr": rr_ratio,
        "mode": config.get("mode", "SWING"),
        "atr": round(atr, 2),
        "vwap": round(vwap, 2),
        "ema_fast": round(ema_fast, 2),
        "ema_slow": round(ema_slow, 2),
        "volume_ratio": round(volume_ratio, 2),
        "created_at": datetime.now().isoformat(),
        "status": "ACTIVE",
    }


# ============================================================
# MAIN SCANNER
# ============================================================

def run_scan(config, market_data=None):
    """
    Scan all configured coins.
    Filter by min_rr, min_confidence.
    Return signals sorted by confidence (highest first).
    """
    pool_size = config.get("coin_pool", 20)
    coins = get_top_coins(pool_size)
    signals = []

    print(f"[Signal Engine] Scanning {len(coins)} coins "
          f"({config.get('mode', 'SWING')} / {config.get('interval', '15m')})...")

    for coin in coins:
        try:
            signal = analyze_coin(coin, config, market_data)
            if signal:
                signals.append(signal)
        except Exception as e:
            print(f"[Signal Engine] Error analyzing {coin}: {e}")
            continue
        # Small delay to avoid Binance rate limits
        time.sleep(0.1)

    # Filter by minimum R:R
    min_rr = config.get("min_rr", 2.0)
    signals = [s for s in signals if s["rr"] >= min_rr]

    # Filter by minimum confidence
    min_conf = config.get("min_confidence", 50)
    signals = [s for s in signals if s["confidence"] >= min_conf]

    # Sort by confidence descending
    signals.sort(key=lambda x: x["confidence"], reverse=True)

    # Limit to max signals per day
    max_signals = config.get("max_signals_per_day", 10)
    signals = signals[:max_signals]

    print(f"[Signal Engine] Scan complete: {len(signals)} signals found")
    return signals
