"""
Backtest Routes — Run and view historical backtests.
"""
from flask import Blueprint, jsonify, request
from services.auth import require_auth
from services.database import get_db
from strategies.backtester import run_backtest, preview_backtest

backtest_bp = Blueprint('backtest', __name__)


@backtest_bp.route('/run', methods=['POST'])
@require_auth
def run_backtest_endpoint():
    """
    Run backtest for a strategy.
    Body: {"strategy_id": "str-001", "days": 90}
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    strategy_id = data.get('strategy_id')
    if not strategy_id:
        return jsonify({'success': False, 'error': 'strategy_id is required'}), 400
    
    days = data.get('days', 90)
    initial_balance = data.get('initial_balance', 100.0)
    
    try:
        result = run_backtest(strategy_id, days=days, initial_balance=initial_balance)
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400
        
        return jsonify({
            'success': True,
            'backtest': result
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/preview', methods=['POST'])
@require_auth
def preview_backtest_endpoint():
    """
    Quick backtest WITHOUT saving strategy first.
    Body: {
        "conditions": [...],
        "coins": ["BTCUSDT"],
        "sl_pct": 2.5,
        "tp_pct": 7.5,
        "days": 30
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    conditions = data.get('conditions', [])
    coins = data.get('coins', [])
    sl_pct = data.get('sl_pct', 2.5)
    tp_pct = data.get('tp_pct', 7.5)
    days = data.get('days', 30)
    initial_balance = data.get('initial_balance', 100.0)
    
    if not conditions or not coins:
        return jsonify({'success': False, 'error': 'conditions and coins are required'}), 400
    
    try:
        result = preview_backtest(conditions, coins, sl_pct, tp_pct, days=days, initial_balance=initial_balance)
        return jsonify({
            'success': True,
            'preview': result
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@backtest_bp.route('/history', methods=['GET'])
@require_auth
def get_backtest_history():
    """Return all past backtest results from database"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, strategy_id, name, symbol, timeframe,
               start_date, end_date, total_trades, winning_trades,
               losing_trades, win_rate, total_pnl_pct, max_drawdown_pct,
               sharpe_ratio, created_at
        FROM backtests
        ORDER BY created_at DESC
        LIMIT 50
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'id': row['id'],
            'strategy_id': row['strategy_id'],
            'name': row['name'],
            'symbol': row['symbol'],
            'timeframe': row['timeframe'],
            'start_date': row['start_date'],
            'end_date': row['end_date'],
            'total_trades': row['total_trades'],
            'winning_trades': row['winning_trades'],
            'losing_trades': row['losing_trades'],
            'win_rate': row['win_rate'],
            'total_pnl_pct': row['total_pnl_pct'],
            'max_drawdown_pct': row['max_drawdown_pct'],
            'sharpe_ratio': row['sharpe_ratio'],
            'created_at': row['created_at']
        })
    
    return jsonify({'success': True, 'history': history, 'count': len(history)})


@backtest_bp.route('/<int:backtest_id>', methods=['GET'])
@require_auth
def get_backtest_detail(backtest_id):
    """Return one backtest detail including trades and equity curve"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM backtests WHERE id = ?", (backtest_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'success': False, 'error': 'Backtest not found'}), 404
    
    import json
    
    return jsonify({
        'success': True,
        'backtest': {
            'id': row['id'],
            'strategy_id': row['strategy_id'],
            'name': row['name'],
            'symbol': row['symbol'],
            'timeframe': row['timeframe'],
            'start_date': row['start_date'],
            'end_date': row['end_date'],
            'total_trades': row['total_trades'],
            'winning_trades': row['winning_trades'],
            'losing_trades': row['losing_trades'],
            'win_rate': row['win_rate'],
            'total_pnl_pct': row['total_pnl_pct'],
            'max_drawdown_pct': row['max_drawdown_pct'],
            'sharpe_ratio': row['sharpe_ratio'],
            'avg_trade_pnl': row['avg_trade_pnl'],
            'best_trade_pnl': row['best_trade_pnl'],
            'worst_trade_pnl': row['worst_trade_pnl'],
            'config_json': json.loads(row['config_json']) if row['config_json'] else {},
            'trades_json': json.loads(row['trades_json']) if row['trades_json'] else [],
            'equity_curve_json': json.loads(row['equity_curve_json']) if row['equity_curve_json'] else [],
            'created_at': row['created_at']
        }
    })