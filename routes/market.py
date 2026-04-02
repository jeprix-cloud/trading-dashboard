"""
Market Routes - Fear & Greed, BTC Dominance, Trending Coins
"""
from flask import Blueprint, jsonify
import requests
from datetime import datetime
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.auth import require_auth

market_bp = Blueprint('market', __name__)

# Cache for rate limiting
_cache = {
    'fear_greed': None,
    'btc_dominance': None,
    'trending': None,
    'last_fetch': None
}


def get_fear_greed():
    """Fetch Fear & Greed Index from alternative.me"""
    if _cache['fear_greed'] and _cache['last_fetch']:
        # Cache for 5 minutes
        elapsed = (datetime.now() - _cache['last_fetch']).seconds
        if elapsed < 300:
            return _cache['fear_greed']
    
    try:
        resp = requests.get('https://api.alternative.me/fng/', timeout=10)
        data = resp.json()
        value = int(data['data'][0]['value'])
        _cache['fear_greed'] = value
        _cache['last_fetch'] = datetime.now()
        return value
    except:
        return _cache['fear_greed'] or 50


def get_btc_dominance():
    """Get BTC Dominance from CoinGecko"""
    if _cache['btc_dominance'] and _cache['last_fetch']:
        elapsed = (datetime.now() - _cache['last_fetch']).seconds
        if elapsed < 300:
            return _cache['btc_dominance']
    
    try:
        resp = requests.get('https://api.coingecko.com/api/v3/global', timeout=10)
        data = resp.json()
        btc_dom = data['data']['market_cap_percentage']['btc']
        _cache['btc_dominance'] = round(btc_dom, 1)
        _cache['last_fetch'] = datetime.now()
        return _cache['btc_dominance']
    except:
        return _cache['btc_dominance'] or 52.0


def get_trending_coins():
    """Get trending coins from CoinGecko"""
    if _cache['trending'] and _cache['last_fetch']:
        elapsed = (datetime.now() - _cache['last_fetch']).seconds
        if elapsed < 300:
            return _cache['trending']
    
    try:
        resp = requests.get('https://api.coingecko.com/api/v3/search/trending', timeout=10)
        data = resp.json()
        coins = [item['item']['symbol'].upper() for item in data['coins'][:5]]
        _cache['trending'] = coins
        _cache['last_fetch'] = datetime.now()
        return coins
    except:
        return _cache['trending'] or ['BTC', 'ETH', 'SOL']


@market_bp.route('/pulse', methods=['GET'])
@require_auth
def get_pulse():
    """Get market pulse data"""
    fg = get_fear_greed()
    btc_dom = get_btc_dominance()
    trending = get_trending_coins()
    
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
        'btc_trend': 'bullish',  # TODO: implement BTC trend check
        'trending': trending,
        'timestamp': datetime.now().isoformat()
    })


@market_bp.route('/fear-greed', methods=['GET'])
def get_fear_greed_only():
    """Get only Fear & Greed"""
    fg = get_fear_greed()
    return jsonify({'fear_greed': fg, 'timestamp': datetime.now().isoformat()})


@market_bp.route('/btc-dominance', methods=['GET'])
def get_btc_dominance_only():
    """Get only BTC Dominance"""
    btc_dom = get_btc_dominance()
    return jsonify({'btc_dominance': btc_dom, 'timestamp': datetime.now().isoformat()})


@market_bp.route('/trending', methods=['GET'])
def get_trending_only():
    """Get only trending coins"""
    trending = get_trending_coins()
    return jsonify({'trending': trending, 'timestamp': datetime.now().isoformat()})
