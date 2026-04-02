"""
Signals Routes - Get trading signals
Logic:
- Bot NEVER run → show MOCK_SIGNALS (with is_example=true)
- Bot RUNNING but RSI neutral → return empty signals []
- Bot HAS REAL SIGNALS → return real signals
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
STATUS_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'bot_status.json')

# Mock signals — ONLY shown when bot has NEVER been run
MOCK_SIGNALS = [
    {
        'id': 'mock_001',
        'symbol': 'BTC/USDT',
        'side': 'BUY',
        'rsi': 28,
        'confidence': 72,
        'entry': 66457,
        'sl': 2.5,
        'tp': 7.5,
        'rr': 3.0,
        'mode': 'SWING',
        'created_at': datetime.now().isoformat(),
        'status': 'EXAMPLE',
        'is_example': True
    },
    {
        'id': 'mock_002',
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
        'status': 'EXAMPLE',
        'is_example': True
    },
    {
        'id': 'mock_003',
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
        'status': 'EXAMPLE',
        'is_example': True
    }
]


def get_bot_status():
    """Read bot status from file."""
    try:
        with open(STATUS_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_current_signals():
    """
    Get signals with proper logic:
    1. If bot NEVER run → return MOCK_SIGNALS (is_example=true)
    2. If bot HAS REAL signals in signals.json → return them
    3. If bot running but NO signals (RSI neutral) → return empty []
    """
    status = get_bot_status()
    bot_ever_run = status.get('started_at') is not None
    signals = []

    if os.path.exists(SIGNALS_PATH):
        try:
            with open(SIGNALS_PATH, 'r') as f:
                data = json.load(f)
            signals = data.get('signals', [])
        except (json.JSONDecodeError, IOError):
            signals = []

    # If bot has never run → show mock with disclaimer
    if not bot_ever_run:
        return {
            'signals': MOCK_SIGNALS,
            'is_example': True,
            'message': 'Example signals. Start the bot to see real signals.'
        }

    # If bot has run but no signals (RSI neutral) → return empty
    if not signals:
        return {
            'signals': [],
            'is_example': False,
            'message': 'No signals found. RSI is neutral. Check back later.'
        }

    # Return real signals
    return {
        'signals': signals,
        'is_example': False,
        'scanned_at': signals[0].get('created_at') if signals else None
    }


@signals_bp.route('', methods=['GET'])
@require_auth
def get_signals():
    """Get current trading signals"""
    result = get_current_signals()
    return jsonify({
        'signals': result['signals'],
        'count': len(result['signals']),
        'is_example': result['is_example'],
        'message': result.get('message'),
        'scanned_at': result.get('scanned_at'),
        'timestamp': datetime.now().isoformat()
    })


@signals_bp.route('/<signal_id>', methods=['GET'])
@require_auth
def get_signal(signal_id):
    """Get specific signal by ID"""
    result = get_current_signals()
    # Check in real signals first
    for s in result['signals']:
        if s.get('id') == signal_id:
            return jsonify(s)
    # Check in mock signals
    for s in MOCK_SIGNALS:
        if s.get('id') == signal_id:
            return jsonify(s)
    return jsonify({'error': 'Signal not found'}), 404


@signals_bp.route('/<signal_id>/outcome', methods=['POST'])
@require_auth
def log_outcome(signal_id):
    """Log trade outcome (TP, SL, or manual)"""
    # Don't allow logging outcome for mock signals
    if signal_id.startswith('mock_'):
        return jsonify({'error': 'Cannot log outcome for example signals'}), 400

    data = request.get_json()
    outcome = data.get('outcome')
    price = data.get('price')

    result = get_current_signals()
    signal = next((s for s in result['signals'] if s.get('id') == signal_id), None)

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
