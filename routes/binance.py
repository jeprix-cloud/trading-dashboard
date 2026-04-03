"""
Binance API Routes - Configure and manage Binance connection
"""
from flask import Blueprint, jsonify, request
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.binance_client import BinanceClient
from services.auth import require_auth

binance_bp = Blueprint('binance', __name__)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'bot_config.json')


def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)


@binance_bp.route('/status', methods=['GET'])
@require_auth
def get_binance_status():
    """Check if Binance is configured (supports testnet)"""
    config = load_config()
    use_testnet = config.get('use_testnet', False)
    
    # Pick the right keys based on testnet toggle
    if use_testnet:
        api_key = config.get('testnet_api_key', '')
        secret_key = config.get('testnet_secret_key', '')
    else:
        api_key = config.get('binance_api_key', '')
        secret_key = config.get('binance_secret_key', '')
    
    has_key = bool(api_key and secret_key)
    
    result = {
        'configured': has_key,
        'has_api_key': bool(api_key),
        'has_secret_key': bool(secret_key),
        'execution_mode': config.get('execution_mode', 'signal_only'),
        'testnet': use_testnet
    }
    
    # Try to connect if keys exist
    if has_key:
        try:
            client = BinanceClient(api_key, secret_key, testnet=use_testnet)
            account = client.get_account()
            result['connected'] = True
            result['balances'] = account.get('balances', [])[:5]
        except Exception as e:
            result['connected'] = False
            result['error'] = str(e)
    else:
        result['connected'] = False
    
    return jsonify(result)


@binance_bp.route('/test', methods=['POST'])
@require_auth
def test_binance():
    """Test Binance connection with provided credentials"""
    data = request.get_json()
    api_key = data.get('api_key', '').strip()
    secret_key = data.get('secret_key', '').strip()
    
    if not api_key or not secret_key:
        return jsonify({
            'success': False,
            'error': 'API Key and Secret Key are required'
        }), 400
    
    try:
        client = BinanceClient(api_key, secret_key)
        account = client.get_account()
        
        # Save if successful
        config = load_config()
        config['binance_api_key'] = api_key
        config['binance_secret_key'] = secret_key
        save_config(config)
        
        return jsonify({
            'success': True,
            'message': 'Binance connected successfully!',
            'configured': True,
            'account': {
                'maker_commission': account.get('makerCommission'),
                'taker_commission': account.get('takerCommission'),
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Connection failed: {str(e)}'
        }), 400


@binance_bp.route('/save', methods=['POST'])
@require_auth
def save_binance_config():
    """Save Binance configuration without testing"""
    data = request.get_json()
    config = load_config()
    
    config['binance_api_key'] = data.get('api_key', '').strip()
    config['binance_secret_key'] = data.get('secret_key', '').strip()
    config['execution_mode'] = data.get('execution_mode', 'signal_only')
    
    save_config(config)
    
    return jsonify({
        'success': True,
        'message': 'Binance configuration saved',
        'configured': bool(config['binance_api_key'] and config['binance_secret_key'])
    })


@binance_bp.route('/remove', methods=['POST'])
@require_auth
def remove_binance():
    """Remove Binance configuration"""
    config = load_config()
    config['binance_api_key'] = ''
    config['binance_secret_key'] = ''
    config['execution_mode'] = 'signal_only'
    save_config(config)
    
    return jsonify({
        'success': True,
        'message': 'Binance configuration removed'
    })


@binance_bp.route('/set-mode', methods=['POST'])
@require_auth
def set_execution_mode():
    """Set execution mode: signal_only, semi_auto, full_auto"""
    data = request.get_json()
    mode = data.get('mode', 'signal_only')
    
    if mode not in ['signal_only', 'semi_auto', 'full_auto']:
        return jsonify({
            'success': False,
            'error': 'Invalid mode. Must be: signal_only, semi_auto, full_auto'
        }), 400
    
    config = load_config()
    config['execution_mode'] = mode
    save_config(config)
    
    return jsonify({
        'success': True,
        'message': f'Execution mode set to {mode}',
        'mode': mode
    })


@binance_bp.route('/balances', methods=['GET'])
@require_auth
def get_balances():
    """Get account balances"""
    config = load_config()
    api_key = config.get('binance_api_key', '')
    secret_key = config.get('binance_secret_key', '')
    
    if not api_key or not secret_key:
        return jsonify({
            'success': False,
            'error': 'Binance not configured'
        }), 400
    
    try:
        client = BinanceClient(api_key, secret_key)
        account = client.get_account()
        balances = []
        
        for b in account.get('balances', []):
            free = float(b.get('free', 0))
            locked = float(b.get('locked', 0))
            total = free + locked
            if total > 0:
                balances.append({
                    'asset': b['asset'],
                    'free': free,
                    'locked': locked,
                    'total': total
                })
        
        return jsonify({
            'success': True,
            'balances': balances
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@binance_bp.route('/execute', methods=['POST'])
@require_auth
def execute_signal_endpoint():
    """
    Execute a trading signal (from signal engine or manual).
    Uses binance_executor for actual order placement.
    In semi_auto mode, requires confirmed=True in body.
    """
    data = request.get_json()
    signal = data.get('signal', {})
    
    config = load_config()
    execution_mode = config.get('execution_mode', 'signal_only')
    
    if execution_mode == 'signal_only':
        return jsonify({
            'success': False,
            'error': 'Execution is disabled. Set mode to semi_auto or full_auto'
        }), 400
    
    if execution_mode == 'semi_auto' and not data.get('confirmed'):
        # Semi-auto: require confirmation
        return jsonify({
            'success': False,
            'needs_confirmation': True,
            'message': 'This is a LIVE execution. Do you want to proceed?',
            'signal': signal
        }), 202
    
    # Execute using binance_executor
    from services.binance_executor import execute_signal
    result = execute_signal(signal, config)
    
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error')}), 400
    
    return jsonify({
        'success': True,
        'message': f"Order executed: {result['side']} {result['quantity']} {result['symbol']}",
        'order_id': result.get('order_id'),
        'entry_price': result.get('entry_price'),
        'mode': result.get('mode')
    })


@binance_bp.route('/set-testnet', methods=['POST'])
@require_auth
def set_testnet():
    """Toggle testnet mode on/off"""
    data = request.get_json()
    use_testnet = bool(data.get('enabled', True))
    
    config = load_config()
    config['use_testnet'] = use_testnet
    save_config(config)
    
    return jsonify({
        'success': True,
        'message': f"Testnet {'enabled' if use_testnet else 'disabled'}",
        'testnet': use_testnet
    })


@binance_bp.route('/testnet/save', methods=['POST'])
@require_auth
def save_testnet_keys():
    """Save testnet API keys"""
    data = request.get_json()
    api_key = data.get('api_key', '').strip()
    secret_key = data.get('secret_key', '').strip()
    
    if not api_key or not secret_key:
        return jsonify({'success': False, 'error': 'API Key and Secret Key required'}), 400
    
    config = load_config()
    config['testnet_api_key'] = api_key
    config['testnet_secret_key'] = secret_key
    config['use_testnet'] = True
    save_config(config)
    
    return jsonify({
        'success': True,
        'message': 'Testnet keys saved, testnet enabled'
    })
