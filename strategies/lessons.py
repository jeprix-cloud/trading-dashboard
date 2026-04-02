"""
TradingCore Learning System - Lessons Module
=============================================
Learns from past trade outcomes to identify winning/losing patterns.
Adjusts confidence scores and maintains a blacklist of poor setups.
"""

import json
import os
from datetime import datetime

LESSONS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'lessons.json')
TRADES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'trades.json')


# ============================================================
# DATA I/O
# ============================================================

def load_lessons():
    """Load lessons from data/lessons.json"""
    try:
        with open(LESSONS_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            'patterns': [],
            'blacklist': [],
            'last_updated': None,
            'version': 1
        }


def save_lessons(lessons):
    """Save lessons to data/lessons.json"""
    lessons['last_updated'] = datetime.now().isoformat()
    os.makedirs(os.path.dirname(LESSONS_PATH), exist_ok=True)
    with open(LESSONS_PATH, 'w') as f:
        json.dump(lessons, f, indent=2)


def load_trades():
    """Load trade history from data/trades.json"""
    try:
        with open(TRADES_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# ============================================================
# PATTERN IDENTIFICATION
# ============================================================

def identify_pattern(signal, market_data=None):
    """
    Generate a pattern key from signal + market context.
    Examples:
      - "FG<30_AND_RSI<30"
      - "RSI>70_AND_FG>60"
      - "RSI_35_40_ZONE"
      - "HIGH_VOLUME_AND_RSI<30"
    """
    parts = []
    rsi = signal.get('rsi', 50)
    side = signal.get('side', 'BUY')
    confidence = signal.get('confidence', 0)
    volume_ratio = signal.get('volume_ratio', 1.0)

    # RSI condition
    if rsi < 25:
        parts.append('RSI<25')
    elif rsi < 30:
        parts.append('RSI<30')
    elif rsi < 35:
        parts.append('RSI<35')
    elif 35 <= rsi <= 40:
        parts.append('RSI_35_40_ZONE')
    elif 60 <= rsi <= 65:
        parts.append('RSI_60_65_ZONE')
    elif rsi > 75:
        parts.append('RSI>75')
    elif rsi > 70:
        parts.append('RSI>70')
    elif rsi > 65:
        parts.append('RSI>65')

    # Fear & Greed condition
    if market_data:
        fg = market_data.get('fear_greed', 50)
        if fg < 25:
            parts.append('FG<25')
        elif fg < 30:
            parts.append('FG<30')
        elif fg < 40:
            parts.append('FG<40')
        elif fg > 75:
            parts.append('FG>75')
        elif fg > 60:
            parts.append('FG>60')

    # Volume condition
    if volume_ratio >= 2.0:
        parts.append('HIGH_VOLUME')
    elif volume_ratio >= 1.5:
        parts.append('MED_VOLUME')

    # Confidence bracket
    if confidence >= 70:
        parts.append('CONF_HIGH')
    elif confidence >= 50:
        parts.append('CONF_MED')
    else:
        parts.append('CONF_LOW')

    parts.append(side)

    if not parts:
        return 'UNKNOWN'

    return '_AND_'.join(sorted(parts))


# ============================================================
# LEARNING FROM TRADES
# ============================================================

def learn_from_trades():
    """
    Analyze all completed trades and extract winning/losing patterns.
    Updates lessons.json with pattern statistics.
    """
    trades = load_trades()
    lessons = load_lessons()

    if not trades:
        return {
            'success': False,
            'message': 'No trades to learn from',
            'patterns_found': 0
        }

    pattern_map = {}

    for trade in trades:
        signal_proxy = {
            'rsi': trade.get('rsi', 50),
            'side': trade.get('side', 'BUY'),
            'confidence': trade.get('confidence', 50),
            'volume_ratio': trade.get('volume_ratio', 1.0),
        }
        market_proxy = {
            'fear_greed': trade.get('fear_greed', 50),
        }

        pattern_key = identify_pattern(signal_proxy, market_proxy)

        if pattern_key not in pattern_map:
            pattern_map[pattern_key] = {
                'pattern': pattern_key,
                'occurrences': 0,
                'wins': 0,
                'losses': 0,
                'total_pnl': 0,
            }

        entry = pattern_map[pattern_key]
        entry['occurrences'] += 1
        pnl = trade.get('pnl_pct', 0)
        entry['total_pnl'] += pnl

        if trade.get('outcome') in ['TP'] or pnl > 0:
            entry['wins'] += 1
        else:
            entry['losses'] += 1

    # Finalize pattern stats
    patterns = []
    new_blacklist = list(lessons.get('blacklist', []))

    for key, entry in pattern_map.items():
        occ = entry['occurrences']
        win_rate = round((entry['wins'] / occ) * 100, 1) if occ > 0 else 0
        avg_pnl = round(entry['total_pnl'] / occ, 2) if occ > 0 else 0

        pattern_record = {
            'pattern': key,
            'occurrences': occ,
            'wins': entry['wins'],
            'losses': entry['losses'],
            'avg_pnl': avg_pnl,
            'win_rate': win_rate,
        }
        patterns.append(pattern_record)

        # Auto-blacklist: 3+ occurrences with win rate < 30%
        if occ >= 3 and win_rate < 30 and key not in new_blacklist:
            new_blacklist.append(key)

    patterns.sort(key=lambda p: p['win_rate'], reverse=True)

    lessons['patterns'] = patterns
    lessons['blacklist'] = new_blacklist
    save_lessons(lessons)

    return {
        'success': True,
        'message': f'Learned from {len(trades)} trades',
        'patterns_found': len(patterns),
        'blacklisted': len(new_blacklist),
        'patterns': patterns,
    }


# ============================================================
# APPLYING LESSONS TO SIGNALS
# ============================================================

def apply_lessons(signals, market_data=None):
    """
    Adjust signal confidence based on learned patterns.
    Also filters out blacklisted patterns.
    """
    lessons = load_lessons()
    patterns = {p['pattern']: p for p in lessons.get('patterns', [])}
    blacklist = set(lessons.get('blacklist', []))

    adjusted = []

    for signal in signals:
        pattern_key = identify_pattern(signal, market_data)

        # Skip blacklisted patterns
        if pattern_key in blacklist:
            print(f"[Lessons] Blacklisted pattern skipped: {pattern_key} for {signal.get('symbol')}")
            continue

        # Adjust confidence based on historical performance
        if pattern_key in patterns:
            pat = patterns[pattern_key]
            win_rate = pat.get('win_rate', 50)
            occurrences = pat.get('occurrences', 0)

            if occurrences >= 3:
                if win_rate >= 80:
                    boost = min(15, int((win_rate - 50) * 0.3))
                    signal['confidence'] = min(100, signal['confidence'] + boost)
                    signal['lesson_boost'] = boost
                elif win_rate >= 60:
                    boost = min(8, int((win_rate - 50) * 0.3))
                    signal['confidence'] = min(100, signal['confidence'] + boost)
                    signal['lesson_boost'] = boost
                elif win_rate < 40:
                    penalty = min(15, int((50 - win_rate) * 0.3))
                    signal['confidence'] = max(0, signal['confidence'] - penalty)
                    signal['lesson_penalty'] = penalty

            signal['pattern'] = pattern_key
            signal['pattern_win_rate'] = win_rate

        adjusted.append(signal)

    return adjusted


# ============================================================
# BLACKLIST MANAGEMENT
# ============================================================

def get_blacklist():
    lessons = load_lessons()
    return lessons.get('blacklist', [])


def add_to_blacklist(pattern):
    lessons = load_lessons()
    if pattern not in lessons['blacklist']:
        lessons['blacklist'].append(pattern)
        save_lessons(lessons)
    return lessons['blacklist']


def remove_from_blacklist(pattern):
    lessons = load_lessons()
    if pattern in lessons['blacklist']:
        lessons['blacklist'].remove(pattern)
        save_lessons(lessons)
    return lessons['blacklist']


def clear_blacklist():
    lessons = load_lessons()
    lessons['blacklist'] = []
    save_lessons(lessons)
    return []


# ============================================================
# SUMMARY
# ============================================================

def get_learning_summary():
    """Get summary of current learning state"""
    lessons = load_lessons()
    patterns = lessons.get('patterns', [])
    blacklist = lessons.get('blacklist', [])

    top_patterns = sorted(patterns, key=lambda p: p.get('win_rate', 0), reverse=True)[:5]
    worst_patterns = sorted(patterns, key=lambda p: p.get('win_rate', 100))[:5]

    return {
        'total_patterns': len(patterns),
        'blacklisted_count': len(blacklist),
        'blacklisted': blacklist,
        'top_patterns': top_patterns,
        'worst_patterns': worst_patterns,
        'last_updated': lessons.get('last_updated'),
        'version': lessons.get('version', 1),
    }
