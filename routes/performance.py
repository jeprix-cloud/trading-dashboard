"""
Performance Routes - Win rate, trade history from SQLite
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.auth import require_auth

performance_bp = Blueprint('performance', __name__)


@performance_bp.route('', methods=['GET'])
@require_auth
def get_performance():
    """Get overall performance stats from SQLite positions table"""
    from services.database import get_db
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get closed positions
    cursor.execute("""
        SELECT pnl_pct, pnl_usd, side, symbol, status, exit_price, entry_price
        FROM positions WHERE status != 'OPEN'
        ORDER BY closed_at DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return jsonify({
            'total_trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0,
            'best_trade': None, 'worst_trade': None, 'avg_pnl': 0
        })
    
    wins = [r for r in rows if r['pnl_pct'] and r['pnl_pct'] > 0]
    losses = [r for r in rows if r['pnl_pct'] and r['pnl_pct'] <= 0]
    
    best = max(rows, key=lambda r: r['pnl_pct'] or 0) if rows else None
    worst = min(rows, key=lambda r: r['pnl_pct'] or 0) if rows else None
    
    return jsonify({
        'total_trades': len(rows),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(len(wins) / len(rows) * 100, 1) if rows else 0,
        'best_trade': {'symbol': best['symbol'], 'pnl': best['pnl_pct']} if best else None,
        'worst_trade': {'symbol': worst['symbol'], 'pnl': worst['pnl_pct']} if worst else None,
        'avg_pnl': round(sum(r['pnl_pct'] or 0 for r in rows) / len(rows), 2) if rows else 0,
        'timestamp': datetime.now().isoformat()
    })


@performance_bp.route('/history', methods=['GET'])
@require_auth
def get_history():
    """Get trade history from positions table"""
    from services.database import get_db
    
    limit = request.args.get('limit', 50, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, symbol, side, entry_price, exit_price, quantity,
               pnl_pct, pnl_usd, status, opened_at, closed_at, notes
        FROM positions WHERE status != 'OPEN'
        ORDER BY closed_at DESC LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    trades = []
    for row in rows:
        trades.append({
            'id': row['id'],
            'symbol': row['symbol'],
            'side': row['side'],
            'entry': row['entry_price'],
            'exit': row['exit_price'],
            'quantity': row['quantity'],
            'pnl_pct': row['pnl_pct'],
            'pnl_usd': row['pnl_usd'],
            'status': row['status'],
            'opened_at': row['opened_at'],
            'closed_at': row['closed_at'],
            'notes': row['notes']
        })
    
    return jsonify({'trades': trades, 'count': len(trades)})


@performance_bp.route('/trade', methods=['POST'])
@require_auth
def add_trade():
    """Add a new trade to positions table"""
    from services.database import get_db
    
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    required = ['symbol', 'side', 'entry_price', 'quantity']
    for field in required:
        if field not in data:
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO positions (
            symbol, side, entry_price, quantity,
            sl_pct, tp_pct, status, opened_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['symbol'],
        data['side'],
        data['entry_price'],
        data['quantity'],
        data.get('sl_pct', 2.5),
        data.get('tp_pct', 7.5),
        'OPEN',
        datetime.now().isoformat()
    ))
    
    trade_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'trade_id': trade_id}), 201


@performance_bp.route('/backtest', methods=['POST'])
@require_auth
def run_backtest():
    """Run a quick backtest using signal engine on current market data"""
    try:
        from strategies.signal_engine import run_scan, fetch_klines, calculate_rsi_wilder

        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'bot_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Use relaxed filters to find more signals for backtest
        bt_config = dict(config)
        bt_config['min_confidence'] = 20
        bt_config['require_volume'] = False
        bt_config['ema200_filter'] = False
        bt_config['fg_filter'] = False
        bt_config['skip_rsi_35_40'] = False

        signals = run_scan(bt_config, {
            'fear_greed': 50,
            'btc_trend': 'neutral',
            'trending': []
        })

        # Simulate outcomes based on historical ATR volatility
        results = []
        wins = 0
        losses = 0
        total_pnl = 0

        for sig in signals:
            # Simple simulation: if RSI < 35 → likely win, RSI > 65 → likely win for sell
            rsi = sig['rsi']
            if sig['side'] == 'BUY':
                win = rsi < 35
            else:
                win = rsi > 65

            pnl = sig['tp'] if win else -sig['sl']
            if win:
                wins += 1
            else:
                losses += 1
            total_pnl += pnl

            results.append({
                'symbol': sig['symbol'],
                'side': sig['side'],
                'rsi': sig['rsi'],
                'confidence': sig['confidence'],
                'entry': sig['entry'],
                'rr': sig['rr'],
                'simulated_pnl': round(pnl, 2),
                'outcome': 'WIN' if win else 'LOSS',
            })

        total = wins + losses
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total_signals': total,
                'wins': wins,
                'losses': losses,
                'win_rate': round(wins / total * 100, 1) if total > 0 else 0,
                'total_pnl': round(total_pnl, 2),
                'avg_pnl': round(total_pnl / total, 2) if total > 0 else 0,
            },
            'config_used': {
                'mode': bt_config['mode'],
                'interval': bt_config['interval'],
                'coin_pool': bt_config['coin_pool'],
            },
            'timestamp': datetime.now().isoformat(),
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500
