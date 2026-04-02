"""
Signals Routes - Get trading signals
"""
from flask import Blueprint, jsonify
from datetime import datetime

signals_bp = Blueprint('signals', __name__)

# Mock signals for demo - replace with real signal engine
MOCK_SIGNALS = [
    {
        'id': 'sig_001',
        'symbol': 'BTC/USDT',
        'side': 'BUY',
        'rsi': 28,
        'confidence': 72,
        'entry': 98240,
        'sl': 2.5,
        'tp': 7.5,
        'rr': 3.0,
        'mode': 'SWING',
        'created_at': datetime.now().isoformat(),
        'status': 'ACTIVE'
    },
    {
        'id': 'sig_002',
        'symbol': 'ETH/USDT',
        'side': 'SELL',
        'rsi': 71,
        'confidence': 68,
        'entry': 3420,
        'sl': 2.5,
        'tp': 7.5,
        'rr': 3.0,
        'mode': 'SWING',
        'created_at': datetime.now().isoformat(),
        'status': 'ACTIVE'
    },
    {
        'id': 'sig_003',
        'symbol': 'SOL/USDT',
        'side': 'BUY',
        'rsi': 32,
        'confidence': 65,
        'entry': 178,
        'sl': 2.0,
        'tp': 6.0,
        'rr': 3.0,
        'mode': 'SWING',
        'created_at': datetime.now().isoformat(),
        'status': 'ACTIVE'
    }
]


@signals_bp.route('', methods=['GET'])
def get_signals():
    """Get current trading signals"""
    return jsonify({
        'signals': MOCK_SIGNALS,
        'count': len(MOCK_SIGNALS),
        'timestamp': datetime.now().isoformat()
    })


@signals_bp.route('/<signal_id>', methods=['GET'])
def get_signal(signal_id):
    """Get specific signal by ID"""
    signal = next((s for s in MOCK_SIGNALS if s['id'] == signal_id), None)
    if signal is None:
        return jsonify({'error': 'Signal not found'}), 404
    return jsonify(signal)


@signals_bp.route('/<signal_id>/outcome', methods=['POST'])
def log_outcome(signal_id):
    """Log trade outcome (TP, SL, or manual)"""
    data = request.get_json()
    outcome = data.get('outcome')  # 'tp', 'sl', 'manual'
    price = data.get('price')
    
    signal = next((s for s in MOCK_SIGNALS if s['id'] == signal_id), None)
    if signal is None:
        return jsonify({'error': 'Signal not found'}), 404
    
    # Update signal status
    signal['status'] = outcome.upper()
    signal['closed_at'] = datetime.now().isoformat()
    if price:
        signal['exit_price'] = price
    
    return jsonify({
        'success': True,
        'signal': signal
    })
