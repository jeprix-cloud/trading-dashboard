"""
Config Routes - Get and update configuration
"""
from flask import Blueprint, jsonify, request
import json
import os

config_bp = Blueprint('config', __name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'bot_config.json')


def read_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def write_config(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)


@config_bp.route('', methods=['GET'])
def get_config():
    """Get current configuration"""
    config = read_config()
    # Hide sensitive fields
    config['alert_bot_token'] = '***' if config.get('alert_bot_token') else ''
    config['alert_chat_id'] = '***' if config.get('alert_chat_id') else ''
    config['main_bot_token'] = '***' if config.get('main_bot_token') else ''
    return jsonify(config)


@config_bp.route('', methods=['POST'])
def update_config():
    """Update configuration"""
    data = request.get_json()
    config = read_config()
    
    # Allowed fields to update
    allowed = [
        'mode', 'interval', 'coin_pool', 'min_rr', 'min_confidence',
        'rsi_buy_max', 'rsi_sell_min', 'rsi_extreme_buy', 'rsi_extreme_sell',
        'ema_fast', 'ema_slow', 'ema_trend', 'ema200_filter', 'fg_filter',
        'multitf_filter', 'btc_dom_filter', 'btc_trend_filter',
        'skip_rsi_35_40', 'require_volume', 'apply_lessons', 'auto_blacklist',
        'sl_mode', 'sl_fixed_buy', 'sl_fixed_sell', 'atr_multiplier',
        'scalp_sl', 'scalp_tp', 'max_signals_per_day', 'max_scalps_per_day',
        'max_risk_per_trade', 'max_position_pct', 'signal_format',
        'notification_new_signal', 'notification_bot_startstop',
        'notification_tp_hit', 'notification_sl_hit',
        'notification_daily_summary', 'daily_summary_time'
    ]
    
    for key in allowed:
        if key in data:
            config[key] = data[key]
    
    write_config(config)
    
    return jsonify({
        'success': True,
        'config': config
    })


@config_bp.route('/reset', methods=['POST'])
def reset_config():
    """Reset config to defaults"""
    default_config = {
        "mode": "SWING",
        "interval": "15m",
        "coin_pool": 20,
        "min_rr": 2.0,
        "min_confidence": 50,
        "rsi_buy_max": 40,
        "rsi_sell_min": 60,
        "rsi_extreme_buy": 30,
        "rsi_extreme_sell": 70,
        "ema_fast": 9,
        "ema_slow": 21,
        "ema_trend": 200,
        "ema200_filter": False,
        "fg_filter": False,
        "multitf_filter": False,
        "btc_dom_filter": False,
        "btc_trend_filter": False,
        "skip_rsi_35_40": False,
        "require_volume": True,
        "apply_lessons": True,
        "auto_blacklist": True,
        "sl_mode": "FIXED",
        "sl_fixed_buy": 2.5,
        "sl_fixed_sell": 2.5,
        "atr_multiplier": 1.5,
        "scalp_sl": 0.3,
        "scalp_tp": 1.0,
        "max_signals_per_day": 10,
        "max_scalps_per_day": 10,
        "max_risk_per_trade": 2.0,
        "max_position_pct": 20,
        "signal_format": "DETAILED",
        "include_chart": False,
        "alert_bot_token": "",
        "alert_chat_id": "",
        "main_bot_token": "",
        "notification_new_signal": True,
        "notification_bot_startstop": True,
        "notification_tp_hit": True,
        "notification_sl_hit": True,
        "notification_daily_summary": True,
        "daily_summary_time": "20:00"
    }
    
    write_config(default_config)
    
    return jsonify({
        'success': True,
        'message': 'Config reset to defaults',
        'config': default_config
    })
