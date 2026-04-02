"""
Telegram Routes - Configure and test Telegram notifications
"""
from flask import Blueprint, jsonify, request
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.telegram_notifier import get_telegram_config, test_connection, send_message

telegram_bp = Blueprint('telegram', __name__)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'bot_config.json')


def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)


@telegram_bp.route('/status', methods=['GET'])
def get_telegram_status():
    """Check if Telegram is configured"""
    tg_config = get_telegram_config()
    return jsonify({
        'configured': tg_config['enabled'],
        'has_token': bool(tg_config['bot_token']),
        'has_chat_id': bool(tg_config['chat_id'])
    })


@telegram_bp.route('/test', methods=['POST'])
def test_telegram():
    """Test Telegram connection with provided credentials"""
    data = request.get_json()
    bot_token = data.get('bot_token', '').strip()
    chat_id = data.get('chat_id', '').strip()
    
    if not bot_token or not chat_id:
        return jsonify({
            'success': False,
            'error': 'Bot token and chat ID are required'
        }), 400
    
    result = test_connection(bot_token, chat_id)
    
    if result['success']:
        # Save if test successful
        config = load_config()
        config['alert_bot_token'] = bot_token
        config['alert_chat_id'] = chat_id
        save_config(config)
        
        return jsonify({
            'success': True,
            'message': 'Telegram connected successfully!',
            'configured': True
        })
    else:
        error_msg = result.get('error', 'Unknown error')
        return jsonify({
            'success': False,
            'error': f'Connection failed: {error_msg}'
        }), 400


@telegram_bp.route('/save', methods=['POST'])
def save_telegram_config():
    """Save Telegram configuration without testing"""
    data = request.get_json()
    bot_token = data.get('bot_token', '').strip()
    chat_id = data.get('chat_id', '').strip()
    
    config = load_config()
    config['alert_bot_token'] = bot_token
    config['alert_chat_id'] = chat_id
    save_config(config)
    
    return jsonify({
        'success': True,
        'message': 'Telegram configuration saved',
        'configured': bool(bot_token and chat_id)
    })


@telegram_bp.route('/remove', methods=['POST'])
def remove_telegram():
    """Remove Telegram configuration"""
    config = load_config()
    config['alert_bot_token'] = ''
    config['alert_chat_id'] = ''
    save_config(config)
    
    return jsonify({
        'success': True,
        'message': 'Telegram configuration removed'
    })


@telegram_bp.route('/send-test-signal', methods=['POST'])
def send_test_signal():
    """Send a test signal notification"""
    tg_config = get_telegram_config()
    
    if not tg_config['enabled']:
        return jsonify({
            'success': False,
            'error': 'Telegram not configured'
        }), 400
    
    test_signal = {
        'symbol': 'BTC/USDT',
        'side': 'BUY',
        'entry': 98500,
        'sl': 2.5,
        'tp': 7.5,
        'rr': 3.0,
        'confidence': 75,
        'mode': 'SWING'
    }
    
    message = f"""
🧪 <b>Test Signal</b>

📊 <b>{test_signal['symbol']}</b>
🎯 Entry: ${test_signal['entry']:,.2f}
🛡️ Stop Loss: {test_signal['sl']}%
📈 Take Profit: {test_signal['tp']}%
📈 R:R Ratio: 1:{test_signal['rr']}
💪 Confidence: {test_signal['confidence']}%
"""
    
    result = send_message(message.strip())
    
    return jsonify({
        'success': result['success'],
        'error': result.get('error')
    })
