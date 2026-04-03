"""
Telegram Notification Service
Handles sending alerts to Telegram bot
"""
import requests
import json
import os
from datetime import datetime

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'bot_config.json')


def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def get_telegram_config():
    """Get Telegram configuration from bot_config.json"""
    config = load_config()
    return {
        'bot_token': config.get('alert_bot_token', ''),
        'chat_id': config.get('alert_chat_id', ''),
        'enabled': bool(config.get('alert_bot_token') and config.get('alert_chat_id'))
    }


def send_message(text, bot_token=None, chat_id=None):
    """Send message via Telegram bot"""
    if bot_token is None or chat_id is None:
        tg_config = get_telegram_config()
        bot_token = tg_config['bot_token']
        chat_id = tg_config['chat_id']
    
    if not bot_token or not chat_id:
        return {'success': False, 'error': 'Telegram not configured'}
    
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        result = resp.json()
        return {'success': result.get('ok', False), 'response': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def test_connection(bot_token, chat_id):
    """Test Telegram bot connection"""
    return send_message(
        "✅ <b>TradingCore Bot Connected!</b>\n\n"
        "Your Telegram notifications are now active.\n"
        "Time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        bot_token=bot_token,
        chat_id=chat_id
    )


def format_signal_message(signal):
    """Format trading signal for Telegram"""
    side = signal.get('side', 'BUY')
    symbol = signal.get('symbol', 'N/A')
    entry = signal.get('entry', 0)
    sl = signal.get('sl', 0)
    tp = signal.get('tp', 0)
    rr = signal.get('rr', 0)
    confidence = signal.get('confidence', 0)
    mode = signal.get('mode', 'SWING')
    
    emoji = '🟢' if side == 'BUY' else '🔴'
    
    text = f"""
{emoji} <b>{side} SIGNAL</b>

📊 <b>{symbol}</b>
🎯 Entry: ${entry:,.2f}
🛡️ Stop Loss: {sl}%
� Take Profit: {tp}%
📈 R:R Ratio: 1:{rr}
💪 Confidence: {confidence}%
📱 Mode: {mode}
"""
    return text.strip()


def format_bot_started_message(config):
    """Format bot started notification"""
    return f"""
✅ <b>Bot Started</b>

🔹 Mode: {config.get('mode', 'N/A')}
⏱️ Interval: {config.get('interval', 'N/A')}
🪙 Coins: Top {config.get('coin_pool', 'N/A')}
📊 Min R:R: {config.get('min_rr', 'N/A')}
💪 Min Confidence: {config.get('min_confidence', 'N/A')}

🟢 Scanning every {config.get('interval', 'N/A')}...
"""


def format_bot_stopped_message(session_stats):
    """Format bot stopped notification"""
    return f"""
⚠️ <b>Bot Stopped</b>

⏱️ Duration: {session_stats.get('duration', 'N/A')}
📊 Signals sent: {session_stats.get('signals_sent', 0)}
🔍 Scans performed: {session_stats.get('scans_performed', 0)}
"""


def format_tp_hit_message(signal, exit_price):
    """Format TP hit notification"""
    return f"""
🎉 <b>Take Profit Hit!</b>

📊 {signal.get('symbol', 'N/A')}
🏔️ Exit Price: ${exit_price:,.2f}
📈 Profit: +{signal.get('tp', 0)}%
💰 Mode: {signal.get('mode', 'SWING')}
"""


def format_sl_hit_message(signal, exit_price):
    """Format SL hit notification"""
    return f"""
😔 <b>Stop Loss Hit</b>

📊 {signal.get('symbol', 'N/A')}
💔 Exit Price: ${exit_price:,.2f}
📉 Loss: -{signal.get('sl', 0)}%
"""


def format_daily_summary(performance):
    """Format daily performance summary"""
    total = performance.get('total_trades', 0)
    wins = performance.get('wins', 0)
    losses = performance.get('losses', 0)
    win_rate = performance.get('win_rate', 0)
    best = performance.get('best_trade', {})
    worst = performance.get('worst_trade', {})
    
    text = f"""
📊 <b>Daily Summary</b>

📈 Total Trades: {total}
✅ Wins: {wins}
❌ Losses: {losses}
🎯 Win Rate: {win_rate}%
"""
    
    if best:
        text += f"\n🏆 Best: +{best.get('pnl', 0)}% ({best.get('symbol', 'N/A')})"
    if worst:
        text += f"\n💸 Worst: {worst.get('pnl', 0)}% ({worst.get('symbol', 'N/A')})"
    
    return text.strip()


# Notification sender functions
def notify_signal(signal, config):
    """Send new signal notification"""
    if not config.get('notification_new_signal', True):
        return
    
    if not get_telegram_config()['enabled']:
        return
    
    message = format_signal_message(signal)
    return send_message(message)


def notify_bot_started(config):
    """Send bot started notification"""
    if not config.get('notification_bot_startstop', True):
        return
    
    if not get_telegram_config()['enabled']:
        return
    
    message = format_bot_started_message(config)
    return send_message(message)


def notify_bot_stopped(session_stats, config=None):
    """Send bot stopped notification"""
    if config is None:
        config = load_config()
    if not config.get('notification_bot_startstop', True):
        return
    
    if not get_telegram_config()['enabled']:
        return
    
    message = format_bot_stopped_message(session_stats)
    return send_message(message)


def notify_tp_hit(signal, exit_price, config=None):
    """Send TP hit notification"""
    if config is None:
        config = load_config()
    if not config.get('notification_tp_hit', True):
        return
    
    if not get_telegram_config()['enabled']:
        return
    
    message = format_tp_hit_message(signal, exit_price)
    return send_message(message)


def notify_sl_hit(signal, exit_price, config=None):
    """Send SL hit notification"""
    if config is None:
        config = load_config()
    if not config.get('notification_sl_hit', True):
        return
    
    if not get_telegram_config()['enabled']:
        return
    
    message = format_sl_hit_message(signal, exit_price)
    return send_message(message)


def notify_daily_summary(performance, config=None):
    """Send daily summary notification"""
    if config is None:
        config = load_config()
    if not config.get('notification_daily_summary', True):
        return
    
    if not get_telegram_config()['enabled']:
        return
    
    message = format_daily_summary(performance)
    return send_message(message)



def notify_position_closed(position):
    """Send Telegram when a position is closed (SL/TP/Manual)"""
    try:
        config = load_config()
        if not config.get('enabled'):
            return
        
        status = position.get('status', 'UNKNOWN')
        symbol = position.get('symbol', '')
        side = position.get('side', '')
        pnl_pct = position.get('pnl_pct', 0)
        exit_price = position.get('exit_price', 0)
        entry_price = position.get('entry_price', 0)
        
        if status == 'TP':
            msg = f"🎯 Take Profit Hit!\n\n"
        elif status == 'SL':
            msg = f"🛑 Stop Loss Hit!\n\n"
        else:
            msg = f"📤 Position Closed\n\n"
        
        msg += f"{symbol} {side}\n"
        msg += f"Entry: {entry_price:.4f}\n"
        msg += f"Exit: {exit_price:.4f}\n"
        msg += f"PnL: {pnl_pct:+.4f}%"
        
        if pnl_pct > 0:
            msg += " ✅"
        else:
            msg += " ❌"
        
        send_message(msg, config.get('alert_bot_token'), config.get('alert_chat_id'))
    except Exception as e:
        print(f"[Telegram] notify_position_closed error: {e}")
