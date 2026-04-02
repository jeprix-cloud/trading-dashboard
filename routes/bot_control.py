"""
Bot Control Routes - Start/Stop/Status
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
import json
import os

bot_bp = Blueprint('bot', __name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'bot_config.json')
STATUS_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'bot_status.json')


def read_json(path):
    with open(path, 'r') as f:
        return json.load(f)


def write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


@bot_bp.route('/status', methods=['GET'])
def get_status():
    """Get current bot status"""
    status = read_json(STATUS_PATH)
    config = read_json(CONFIG_PATH)
    return jsonify({
        'status': status['status'],
        'started_at': status['started_at'],
        'stopped_at': status['stopped_at'],
        'signals_sent_today': status['signals_sent_today'],
        'scans_performed': status['scans_performed'],
        'last_scan_at': status['last_scan_at'],
        'next_scan_at': status['next_scan_at'],
        'mode': config['mode'],
        'interval': config['interval']
    })


@bot_bp.route('/start', methods=['POST'])
def start_bot():
    """Start the trading bot"""
    status = read_json(STATUS_PATH)
    config = read_json(CONFIG_PATH)
    
    if status['status'] == 'running':
        return jsonify({'error': 'Bot is already running'}), 400
    
    # Update status
    status['status'] = 'running'
    status['started_at'] = datetime.now().isoformat()
    status['signals_sent_today'] = 0
    status['scans_performed'] = 0
    
    write_json(STATUS_PATH, status)
    
    return jsonify({
        'success': True,
        'message': 'Bot started',
        'config': {
            'mode': config['mode'],
            'interval': config['interval'],
            'coin_pool': config['coin_pool'],
            'min_rr': config['min_rr'],
            'min_confidence': config['min_confidence'],
            'filters': {
                'ema200': config['ema200_filter'],
                'fg': config['fg_filter'],
                'multitf': config['multitf_filter']
            }
        }
    })


@bot_bp.route('/stop', methods=['POST'])
def stop_bot():
    """Stop the trading bot"""
    status = read_json(STATUS_PATH)
    
    if status['status'] == 'stopped':
        return jsonify({'error': 'Bot is not running'}), 400
    
    # Calculate session duration
    started = datetime.fromisoformat(status['started_at'])
    stopped = datetime.now()
    duration = stopped - started
    
    # Update status
    status['status'] = 'stopped'
    status['stopped_at'] = stopped.isoformat()
    
    write_json(STATUS_PATH, status)
    
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    
    return jsonify({
        'success': True,
        'message': 'Bot stopped',
        'session_stats': {
            'duration': f'{hours}h {minutes}m',
            'signals_sent': status['signals_sent_today'],
            'scans_performed': status['scans_performed']
        }
    })
