"""
Position Routes — Open/close positions, view history and portfolio summary.
"""
from flask import Blueprint, jsonify, request
from services.auth import require_auth
from services.position_manager import (
    open_position, close_position, check_open_positions,
    get_open_positions, get_position_history, get_portfolio_summary
)

positions_bp = Blueprint('positions', __name__)


@positions_bp.route('', methods=['GET'])
@require_auth
def list_open_positions():
    """GET /api/positions → get_open_positions()"""
    positions = get_open_positions()
    return jsonify({'positions': positions, 'count': len(positions)})


@positions_bp.route('/history', methods=['GET'])
@require_auth
def list_position_history():
    """GET /api/positions/history?limit=50 → get_position_history()"""
    limit = request.args.get('limit', 50, type=int)
    positions = get_position_history(limit=limit)
    return jsonify({'positions': positions, 'count': len(positions)})


@positions_bp.route('/summary', methods=['GET'])
@require_auth
def get_summary():
    """GET /api/positions/summary → get_portfolio_summary()"""
    summary = get_portfolio_summary()
    return jsonify({'success': True, 'summary': summary})


@positions_bp.route('/<int:position_id>/close', methods=['POST'])
@require_auth
def close_position_endpoint(position_id):
    """POST /api/positions/<id>/close → close_position(id, exit_price)"""
    data = request.get_json()
    
    if not data or 'exit_price' not in data:
        return jsonify({'success': False, 'error': 'exit_price is required'}), 400
    
    exit_price = data['exit_price']
    reason = data.get('reason', 'MANUAL_CLOSE')
    
    result = close_position(position_id, exit_price, reason)
    
    if result is None:
        return jsonify({'success': False, 'error': 'Position not found'}), 404
    
    # Send Telegram notification
    try:
        from services.telegram_notifier import notify_position_closed
        notify_position_closed(result)
    except Exception as e:
        print(f"[Positions] Telegram notify failed: {e}")
    
    return jsonify({'success': True, 'position': result})


@positions_bp.route('/check', methods=['POST'])
@require_auth
def check_positions_endpoint():
    """
    POST /api/positions/check → check_open_positions()
    Manually trigger SL/TP check for all open positions.
    """
    updates = check_open_positions()
    return jsonify({
        'success': True,
        'checked': len(updates),
        'updates': updates
    })


@positions_bp.route('/open', methods=['POST'])
@require_auth
def open_position_endpoint():
    """
    POST /api/positions/open → open_position()
    Manually open a position (for semi-auto execution).
    """
    data = request.get_json()
    
    required = ['symbol', 'side', 'entry_price', 'quantity', 'sl_pct', 'tp_pct']
    for field in required:
        if field not in data:
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    position_id = open_position(
        signal_id=data.get('signal_id'),
        strategy_id=data.get('strategy_id'),
        symbol=data['symbol'],
        side=data['side'],
        entry_price=data['entry_price'],
        quantity=data['quantity'],
        sl_pct=data['sl_pct'],
        tp_pct=data['tp_pct'],
        exchange=data.get('exchange', 'spot'),
        order_id=data.get('order_id')
    )
    
    return jsonify({
        'success': True,
        'position_id': position_id,
        'message': 'Position opened'
    }), 201