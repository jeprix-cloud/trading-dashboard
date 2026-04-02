"""
TradingCore Evolution System
=============================
Dynamically adjusts RSI, F&G, and confidence thresholds
based on historical trade performance to improve signal quality.
"""

import json
import os
from datetime import datetime

THRESHOLDS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'thresholds.json')
TRADES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'trades.json')
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'bot_config.json')


def load_thresholds():
    try:
        with open(THRESHOLDS_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return _default_thresholds()


def save_thresholds(thresholds):
    os.makedirs(os.path.dirname(THRESHOLDS_PATH), exist_ok=True)
    with open(THRESHOLDS_PATH, 'w') as f:
        json.dump(thresholds, f, indent=2)


def load_trades():
    try:
        with open(TRADES_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def load_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)


def _default_thresholds():
    return {
        'rsi_buy_max': 40,
        'rsi_sell_min': 60,
        'rsi_extreme_buy': 30,
        'rsi_extreme_sell': 70,
        'min_rr': 2.0,
        'min_confidence': 50,
        'evolution_history': [],
        'last_evolved': None,
        'generation': 0
    }


def _analyze_rsi_performance(trades):
    """Analyze which RSI ranges produced winning trades."""
    rsi_brackets = {
        'ultra_low': {'range': (0, 25), 'wins': 0, 'losses': 0, 'pnl': 0},
        'low': {'range': (25, 30), 'wins': 0, 'losses': 0, 'pnl': 0},
        'mid_low': {'range': (30, 35), 'wins': 0, 'losses': 0, 'pnl': 0},
        'warning_low': {'range': (35, 40), 'wins': 0, 'losses': 0, 'pnl': 0},
        'neutral': {'range': (40, 60), 'wins': 0, 'losses': 0, 'pnl': 0},
        'warning_high': {'range': (60, 65), 'wins': 0, 'losses': 0, 'pnl': 0},
        'mid_high': {'range': (65, 70), 'wins': 0, 'losses': 0, 'pnl': 0},
        'high': {'range': (70, 75), 'wins': 0, 'losses': 0, 'pnl': 0},
        'ultra_high': {'range': (75, 100), 'wins': 0, 'losses': 0, 'pnl': 0},
    }

    for trade in trades:
        rsi = trade.get('rsi', 50)
        pnl = trade.get('pnl_pct', 0)
        is_win = pnl > 0

        for bracket in rsi_brackets.values():
            low, high = bracket['range']
            if low <= rsi < high:
                if is_win:
                    bracket['wins'] += 1
                else:
                    bracket['losses'] += 1
                bracket['pnl'] += pnl
                break

    return rsi_brackets


def _compute_optimal_rsi(rsi_brackets):
    """Compute optimal RSI buy/sell thresholds."""
    buy_candidates = ['ultra_low', 'low', 'mid_low', 'warning_low']
    best_buy_max = 40

    for name in buy_candidates:
        bracket = rsi_brackets[name]
        total = bracket['wins'] + bracket['losses']
        if total >= 2:
            win_rate = bracket['wins'] / total
            if win_rate >= 0.6:
                best_buy_max = bracket['range'][1]

    sell_candidates = ['ultra_high', 'high', 'mid_high', 'warning_high']
    best_sell_min = 60

    for name in sell_candidates:
        bracket = rsi_brackets[name]
        total = bracket['wins'] + bracket['losses']
        if total >= 2:
            win_rate = bracket['wins'] / total
            if win_rate >= 0.6:
                best_sell_min = bracket['range'][0]

    return best_buy_max, best_sell_min


def evolve_thresholds(apply_to_config=False):
    """
    Analyze historical trades and evolve thresholds.
    Adjusts RSI, min confidence, and min R:R based on performance.
    """
    trades = load_trades()
    thresholds = load_thresholds()
    config = load_config()

    if len(trades) < 5:
        return {
            'success': False,
            'message': f'Need at least 5 trades to evolve (have {len(trades)})',
            'generation': thresholds.get('generation', 0),
        }

    generation = thresholds.get('generation', 0) + 1

    before = {
        'rsi_buy_max': thresholds.get('rsi_buy_max', 40),
        'rsi_sell_min': thresholds.get('rsi_sell_min', 60),
        'min_confidence': thresholds.get('min_confidence', 50),
        'min_rr': thresholds.get('min_rr', 2.0),
    }

    # RSI Analysis
    rsi_brackets = _analyze_rsi_performance(trades)
    new_buy_max, new_sell_min = _compute_optimal_rsi(rsi_brackets)
    new_buy_max = max(25, min(45, new_buy_max))
    new_sell_min = max(55, min(75, new_sell_min))

    # Confidence Analysis
    low_conf_trades = [t for t in trades if t.get('confidence', 50) < 50]
    high_conf_trades = [t for t in trades if t.get('confidence', 50) >= 50]

    new_min_conf = thresholds.get('min_confidence', 50)
    if low_conf_trades:
        low_wins = sum(1 for t in low_conf_trades if t.get('pnl_pct', 0) > 0)
        low_conf_wr = low_wins / len(low_conf_trades)
        if low_conf_wr < 0.35 and len(low_conf_trades) >= 3:
            new_min_conf = min(70, new_min_conf + 5)
        elif low_conf_wr > 0.65 and len(low_conf_trades) >= 3:
            new_min_conf = max(30, new_min_conf - 5)

    # R:R Analysis
    avg_pnl = sum(t.get('pnl_pct', 0) for t in trades) / len(trades)
    new_min_rr = thresholds.get('min_rr', 2.0)
    if avg_pnl < -1.0:
        new_min_rr = min(3.5, new_min_rr + 0.25)
    elif avg_pnl > 2.0:
        new_min_rr = max(1.5, new_min_rr - 0.25)

    after = {
        'rsi_buy_max': new_buy_max,
        'rsi_sell_min': new_sell_min,
        'min_confidence': new_min_conf,
        'min_rr': round(new_min_rr, 2),
    }

    changes = []
    for key in before:
        if before[key] != after[key]:
            changes.append({
                'param': key,
                'before': before[key],
                'after': after[key],
                'direction': 'up' if after[key] > before[key] else 'down',
            })

    overall_wr = round(sum(1 for t in trades if t.get('pnl_pct', 0) > 0) / len(trades) * 100, 1)

    history_entry = {
        'generation': generation,
        'timestamp': datetime.now().isoformat(),
        'trades_analyzed': len(trades),
        'overall_win_rate': overall_wr,
        'avg_pnl': round(avg_pnl, 2),
        'before': before,
        'after': after,
        'changes': changes,
    }

    history = thresholds.get('evolution_history', [])
    history.append(history_entry)
    history = history[-20:]

    thresholds.update(after)
    thresholds['evolution_history'] = history
    thresholds['last_evolved'] = datetime.now().isoformat()
    thresholds['generation'] = generation
    save_thresholds(thresholds)

    if apply_to_config and changes:
        for key in after:
            config[key] = after[key]
        save_config(config)

    return {
        'success': True,
        'generation': generation,
        'trades_analyzed': len(trades),
        'overall_win_rate': overall_wr,
        'avg_pnl': round(avg_pnl, 2),
        'changes': changes,
        'before': before,
        'after': after,
        'applied_to_config': apply_to_config and bool(changes),
        'rsi_analysis': {
            name: {
                'wins': b['wins'],
                'losses': b['losses'],
                'win_rate': round(b['wins'] / (b['wins'] + b['losses']) * 100, 1) if (b['wins'] + b['losses']) > 0 else 0,
            }
            for name, b in rsi_brackets.items()
            if b['wins'] + b['losses'] > 0
        },
    }


def get_evolution_status():
    """Get current evolution state and history"""
    thresholds = load_thresholds()
    history = thresholds.get('evolution_history', [])
    return {
        'generation': thresholds.get('generation', 0),
        'current_thresholds': {
            'rsi_buy_max': thresholds.get('rsi_buy_max', 40),
            'rsi_sell_min': thresholds.get('rsi_sell_min', 60),
            'min_confidence': thresholds.get('min_confidence', 50),
            'min_rr': thresholds.get('min_rr', 2.0),
        },
        'last_evolved': thresholds.get('last_evolved'),
        'history_count': len(history),
        'recent_evolutions': history[-5:] if history else [],
    }


def reset_thresholds():
    """Reset all thresholds to defaults"""
    thresholds = _default_thresholds()
    save_thresholds(thresholds)
    return thresholds
