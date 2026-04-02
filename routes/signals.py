"""
Signals Routes - Get trading signals
Reads from data/signals.json (written by bot scheduler) or falls back to mock data.
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.auth import require_auth

signals_bp = Blueprint('signals', __name__)

SIGNALS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'signals.json')

# Mock signals shown when bot hasn't run yet
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


def get_current_signals():
    """Get signals from file (real) or mock data."""
    if os.path.exists(SIGNALS_PATH):
        try:
            with open(SIGNALS_PATH, 'r') as f:
                data = json.load(f)
            signals = data.get('signals', [])
            if signals:
                return signals
        except (json.JSONDecodeError, IOError):
            pass
    return MOCK_SIGNALS


@signals_bp.route('', methods=['GET'])
@require_auth
def get_signals():
    """Get current trading signals"""
    signals = get_current_signals()
    return jsonify({
        'signals': signals,
        'count': len(signals),
        'timestamp': datetime.now().isoformat()
    })


@signals_bp.route('/<signal_id>', methods=['GET'])
@require_auth
def get_signal(signal_id):
    """Get specific signal by ID"""
    signals = get_current_signals()
    signal = next((s for s in signals if s.get('id') == signal_id), None)
    if signal is None:
        return jsonify({'error': 'Signal not found'}), 404
    return jsonify(signal)


@signals_bp.route('/<signal_id>/outcome', methods=['POST'])
@require_auth
def log_outcome(signal_id):
    """Log trade outcome (TP, SL, or manual)"""
    data = request.get_json()
    outcome = data.get('outcome')
    price = data.get('price')

    signals = get_current_signals()
    signal = next((s for s in signals if s.get('id') == signal_id), None)
    if signal is None:
        return jsonify({'error': 'Signal not found'}), 404

    signal['status'] = outcome.upper()
    signal['closed_at'] = datetime.now().isoformat()
    if price:
        signal['exit_price'] = price

    # Persist updated signals
    if os.path.exists(SIGNALS_PATH):
        try:
            with open(SIGNALS_PATH, 'r') as f:
                file_data = json.load(f)
            for i, s in enumerate(file_data.get('signals', [])):
                if s.get('id') == signal_id:
                    file_data['signals'][i] = signal
                    break
            with open(SIGNALS_PATH, 'w') as f:
                json.dump(file_data, f, indent=2)
        except Exception:
            pass

    return jsonify({
        'success': True,
        'signal': signal
    })
