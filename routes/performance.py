"""
Performance Routes - Win rate, trade history
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.auth import require_auth

performance_bp = Blueprint('performance', __name__)

TRADES_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'trades.json')

# Mock trade data for demo
MOCK_TRADES = [
    {
        'id': 'trade_001',
        'symbol': 'SOL/USDT',
        'side': 'BUY',
        'entry': 168.50,
        'exit': 179.35,
        'pnl_pct': 6.41,
        'outcome': 'TP',
        'mode': 'SWING',
        'opened_at': (datetime.now() - timedelta(days=3)).isoformat(),
        'closed_at': datetime.now().isoformat()
    },
    {
        'id': 'trade_002',
        'symbol': 'BNB/USDT',
        'side': 'BUY',
        'entry': 598.20,
        'exit': 578.80,
        'pnl_pct': -3.26,
        'outcome': 'SL',
        'mode': 'SWING',
        'opened_at': (datetime.now() - timedelta(days=2)).isoformat(),
        'closed_at': datetime.now().isoformat()
    }
]


def get_trades():
    """Get all trades"""
    if os.path.exists(TRADES_PATH):
        with open(TRADES_PATH, 'r') as f:
            return json.load(f)
    return MOCK_TRADES


@performance_bp.route('', methods=['GET'])
@require_auth
def get_performance():
    """Get overall performance stats"""
    trades = get_trades()
    
    if not trades:
        return jsonify({
            'total_trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0,
            'best_trade': None, 'worst_trade': None, 'avg_pnl': 0
        })
    
    wins = [t for t in trades if t['outcome'] in ['TP', 'MANUAL'] and t['pnl_pct'] > 0]
    losses = [t for t in trades if t['outcome'] in ['SL', 'MANUAL'] and t['pnl_pct'] < 0]
    best = max(trades, key=lambda t: t['pnl_pct']) if trades else None
    worst = min(trades, key=lambda t: t['pnl_pct']) if trades else None
    
    return jsonify({
        'total_trades': len(trades), 'wins': len(wins), 'losses': len(losses),
        'win_rate': round(len(wins) / len(trades) * 100, 1) if trades else 0,
        'best_trade': {'symbol': best['symbol'], 'pnl': best['pnl_pct']} if best else None,
        'worst_trade': {'symbol': worst['symbol'], 'pnl': worst['pnl_pct']} if worst else None,
        'avg_pnl': round(sum(t['pnl_pct'] for t in trades) / len(trades), 2) if trades else 0,
        'timestamp': datetime.now().isoformat()
    })


@performance_bp.route('/history', methods=['GET'])
@require_auth
def get_history():
    """Get trade history"""
    trades = get_trades()
    return jsonify({'trades': trades, 'count': len(trades)})


@performance_bp.route('/trade', methods=['POST'])
@require_auth
def add_trade():
    """Add a new trade"""
    data = request.get_json()
    trades = get_trades()
    
    trade = {
        'id': f'trade_{len(trades) + 1:03d}',
        'symbol': data.get('symbol'), 'side': data.get('side'),
        'entry': data.get('entry'), 'exit': data.get('exit'),
        'pnl_pct': data.get('pnl_pct'), 'outcome': data.get('outcome'),
        'mode': data.get('mode', 'SWING'),
        'opened_at': data.get('opened_at', datetime.now().isoformat()),
        'closed_at': datetime.now().isoformat()
    }
    
    trades.append(trade)
    os.makedirs(os.path.dirname(TRADES_PATH), exist_ok=True)
    with open(TRADES_PATH, 'w') as f:
        json.dump(trades, f, indent=2)
    
    return jsonify({'success': True, 'trade': trade})
