"""
Market Routes - Fear & Greed, BTC Dominance, Trending Coins, BTC Trend
FIXED: Cache logic, separate caches per type, imports at module level
"""
from flask import Blueprint, jsonify
import requests
from datetime import datetime
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.auth import require_auth

market_bp = Blueprint('market', __name__)

# Import signal engine at module level (avoid repeated imports)
from strategies.signal_engine import fetch_klines, calculate_ema

# Separate cache per data type - each has its own TTL
_cache = {
    'fear_greed': {'value': None, 'last_fetch': None},
    'btc_dominance': {'value': None, 'last_fetch': None},
    'trending': {'value': None, 'last_fetch': None},
    'btc_trend': {'value': None, 'last_fetch': None},
}

# Cache TTL in seconds per data type
_CACHE_TTL = {
    'fear_greed': 300,      # 5 min
    'btc_dominance': 300,  # 5 min
    'trending': 300,       # 5 min
    'btc_trend': 900,      # 15 min (heavy - fetches 200 klines)
}

# Watchlist cache
_watchlist_cache = {'data': [], 'last_fetch': None}
WATCHLIST_CACHE_TTL = 30  # 30 seconds


def _is_cache_valid(cache_key):
    """Check if cache is still valid using total_seconds()"""
    c = _cache.get(cache_key)
    if not c or c['value'] is None or c['last_fetch'] is None:
        return False
    elapsed = (datetime.now() - c['last_fetch']).total_seconds()
    return elapsed < _CACHE_TTL.get(cache_key, 300)


def get_fear_greed():
    """Fetch Fear & Greed Index from alternative.me"""
    if _is_cache_valid('fear_greed'):
        return _cache['fear_greed']['value']
    
    try:
        resp = requests.get('https://api.alternative.me/fng/', timeout=8)
        resp.raise_for_status()
        data = resp.json()
        value = int(data['data'][0]['value'])
        _cache['fear_greed'] = {'value': value, 'last_fetch': datetime.now()}
        return value
    except Exception as e:
        print(f"[Market] Fear & Greed fetch failed: {e}")
        return _cache['fear_greed']['value'] or 50


def get_btc_dominance():
    """Get BTC Dominance from CoinGecko"""
    if _is_cache_valid('btc_dominance'):
        return _cache['btc_dominance']['value']
    
    try:
        resp = requests.get('https://api.coingecko.com/api/v3/global', timeout=8)
        resp.raise_for_status()
        data = resp.json()
        btc_dom = data['data']['market_cap_percentage']['btc']
        value = round(btc_dom, 1)
        _cache['btc_dominance'] = {'value': value, 'last_fetch': datetime.now()}
        return value
    except Exception as e:
        print(f"[Market] BTC Dominance fetch failed: {e}")
        return _cache['btc_dominance']['value'] or 52.0


def get_trending_coins():
    """Get trending coins from CoinGecko"""
    if _is_cache_valid('trending'):
        return _cache['trending']['value']
    
    try:
        resp = requests.get('https://api.coingecko.com/api/v3/search/trending', timeout=8)
        resp.raise_for_status()
        data = resp.json()
        coins = [item['item']['symbol'].upper() for item in data['coins'][:5]]
        _cache['trending'] = {'value': coins, 'last_fetch': datetime.now()}
        return coins
    except Exception as e:
        print(f"[Market] Trending coins fetch failed: {e}")
        return _cache['trending']['value'] or ['BTC', 'ETH', 'SOL']


def get_btc_trend():
    """Get BTC trend using EMA analysis (real data)"""
    if _is_cache_valid('btc_trend'):
        return _cache['btc_trend']['value']
    
    try:
        klines = fetch_klines('BTCUSDT', '1h', limit=200)
        if klines and len(klines['closes']) >= 50:
            closes = klines['closes']
            ema50 = calculate_ema(closes, 50)
            ema200 = calculate_ema(closes, 200)
            price = closes[-1]
            
            if price > ema50 and price > ema200:
                trend = 'strong_bullish'
            elif price > ema50:
                trend = 'bullish'
            elif price < ema50 and price < ema200:
                trend = 'strong_bearish'
            else:
                trend = 'bearish'
            
            _cache['btc_trend'] = {'value': trend, 'last_fetch': datetime.now()}
            return trend
    except Exception as e:
        print(f"[Market] BTC trend calculation failed: {e}")
    
    return _cache['btc_trend']['value'] or 'neutral'


def _load_watchlist():
    """Load watchlist from config file"""
    global _watchlist_cache
    
    # Check cache first
    if (_watchlist_cache['data'] and _watchlist_cache['last_fetch']):
        elapsed = (datetime.now() - _watchlist_cache['last_fetch']).total_seconds()
        if elapsed < WATCHLIST_CACHE_TTL:
            return _watchlist_cache['data']
    
    WATCHLIST_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'watchlist.json')
    try:
        with open(WATCHLIST_PATH, 'r') as f:
            data = json.load(f)
        _watchlist_cache = {'data': data.get('watchlist', []), 'last_fetch': datetime.now()}
    except Exception as e:
        print(f"[Market] Watchlist load failed: {e}")
        _watchlist_cache = {'data': [], 'last_fetch': datetime.now()}
    
    return _watchlist_cache['data']


@market_bp.route('/pulse', methods=['GET'])
@require_auth
def get_pulse():
    """Get market pulse data (all real)"""
    fg = get_fear_greed()
    btc_dom = get_btc_dominance()
    trending = get_trending_coins()
    btc_trend = get_btc_trend()
    
    # Determine F&G label
    if fg >= 75:
        fg_label = 'Extreme Greed'
    elif fg >= 50:
        fg_label = 'Greed'
    elif fg >= 25:
        fg_label = 'Fear'
    else:
        fg_label = 'Extreme Fear'
    
    return jsonify({
        'fear_greed': fg,
        'fear_greed_label': fg_label,
        'btc_dominance': btc_dom,
        'btc_trend': btc_trend,
        'trending': trending,
        'timestamp': datetime.now().isoformat()
    })


@market_bp.route('/fear-greed', methods=['GET'])
@require_auth
def get_fear_greed_only():
    """Get only Fear & Greed"""
    fg = get_fear_greed()
    return jsonify({'fear_greed': fg, 'timestamp': datetime.now().isoformat()})


@market_bp.route('/btc-dominance', methods=['GET'])
@require_auth
def get_btc_dominance_only():
    """Get only BTC Dominance"""
    btc_dom = get_btc_dominance()
    return jsonify({'btc_dominance': btc_dom, 'timestamp': datetime.now().isoformat()})


@market_bp.route('/trending', methods=['GET'])
@require_auth
def get_trending_only():
    """Get only trending coins"""
    trending = get_trending_coins()
    return jsonify({'trending': trending, 'timestamp': datetime.now().isoformat()})


@market_bp.route('/btc-trend', methods=['GET'])
@require_auth
def get_btc_trend_only():
    """Get only BTC Trend"""
    trend = get_btc_trend()
    return jsonify({'btc_trend': trend, 'timestamp': datetime.now().isoformat()})


@market_bp.route('/prices', methods=['GET'])
@require_auth
def get_prices():
    """Get prices for watchlist coins"""
    watchlist = _load_watchlist()
    
    # Get prices from Binance
    prices = []
    for coin in watchlist:
        if not coin.get('enabled', True):
            continue
        symbol = coin['symbol']
        try:
            resp = requests.get(
                f'https://api.binance.com/api/v3/ticker/24hr',
                params={'symbol': symbol},
                timeout=8
            )
            resp.raise_for_status()
            data = resp.json()
            prices.append({
                'symbol': symbol,
                'name': coin.get('name', symbol),
                'short': coin.get('short', symbol.replace('USDT', '')),
                'price': float(data.get('lastPrice', 0)),
                'change_24h': float(data.get('priceChangePercent', 0)),
                'high_24h': float(data.get('highPrice', 0)),
                'low_24h': float(data.get('lowPrice', 0)),
                'volume': float(data.get('quoteVolume', 0))
            })
        except Exception as e:
            print(f"[Market] Price fetch failed for {symbol}: {e}")
            continue
    
    return jsonify({
        'prices': prices,
        'count': len(prices),
        'timestamp': datetime.now().isoformat()
    })


@market_bp.route('/global', methods=['GET'])
@require_auth
def get_global_data():
    """Get global market data from CoinGecko"""
    try:
        resp = requests.get('https://api.coingecko.com/api/v3/global', timeout=8)
        resp.raise_for_status()
        data = resp.json().get('data', {})
        
        total_mcap = data.get('total_market_cap', {}).get('usd', 0)
        total_vol = data.get('total_volume', {}).get('usd', 0)
        mcap_change = data.get('market_cap_change_percentage_24h_usd', 0)
        
        return jsonify({
            'total_market_cap': total_mcap,
            'total_volume': total_vol,
            'market_cap_change_24h': mcap_change,
            'active_cryptocurrencies': data.get('active_cryptocurrencies', 0),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"[Market] Global data fetch failed: {e}")
        return jsonify({'error': str(e)}), 500