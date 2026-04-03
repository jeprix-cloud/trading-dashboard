"""
Risk Management Routes — Circuit breaker status and controls.
"""
from flask import Blueprint, jsonify, request
from services.auth import require_auth
from services.risk_manager import (
    get_risk_status, get_risk_state, check_circuit_breaker,
    activate_circuit_breaker, deactivate_circuit_breaker,
    can_open_position, load_risk_config
)

risk_bp = Blueprint('risk', __name__)


@risk_bp.route('/status', methods=['GET'])
@require_auth
def risk_status():
    """GET /api/risk/status → current risk status for dashboard"""
    status = get_risk_status()
    return jsonify({'success': True, 'risk': status})


@risk_bp.route('/check', methods=['POST'])
@require_auth
def risk_check():
    """
    POST /api/risk/check → can_open_position(symbol, entry_price, quantity)
    Body: {"symbol": "BTCUSDT", "entry_price": 68000, "quantity": 0.01}
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    symbol = data.get('symbol', '').strip()
    entry_price = data.get('entry_price')
    quantity = data.get('quantity')
    
    if not symbol or entry_price is None or quantity is None:
        return jsonify({'success': False, 'error': 'symbol, entry_price, quantity required'}), 400
    
    allowed, reason = can_open_position(symbol, entry_price, quantity)
    
    return jsonify({
        'success': True,
        'allowed': allowed,
        'reason': reason
    })


@risk_bp.route('/circuit-breaker/activate', methods=['POST'])
@require_auth
def activate_cb():
    """POST /api/risk/circuit-breaker/activate → force activate circuit breaker"""
    activate_circuit_breaker()
    return jsonify({'success': True, 'message': 'Circuit breaker activated'})


@risk_bp.route('/circuit-breaker/deactivate', methods=['POST'])
@require_auth
def deactivate_cb():
    """POST /api/risk/circuit-breaker/deactivate → reset circuit breaker"""
    deactivate_circuit_breaker()
    return jsonify({'success': True, 'message': 'Circuit breaker deactivated'})


@risk_bp.route('/circuit-breaker/status', methods=['GET'])
@require_auth
def cb_status():
    """GET /api/risk/circuit-breaker/status → is circuit breaker active?"""
    blocked, reason = check_circuit_breaker()
    return jsonify({
        'success': True,
        'active': blocked,
        'reason': reason if blocked else ''
    })


@risk_bp.route('/config', methods=['GET'])
@require_auth
def risk_config():
    """GET /api/risk/config → current risk limits"""
    config = load_risk_config()
    return jsonify({'success': True, 'config': config})