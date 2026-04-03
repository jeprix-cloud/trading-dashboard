"""
Bot Control Routes - Start/Stop/Status with APScheduler
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.auth import require_auth

bot_bp = Blueprint('bot', __name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'bot_config.json')
STATUS_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'bot_status.json')
SIGNALS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'signals.json')

# ============================================================
# APScheduler setup
# ============================================================
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = BackgroundScheduler(daemon=True)
scheduler.start()

SCAN_JOB_ID = 'trading_scan'


# ============================================================
# JSON helpers
# ============================================================
def read_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


# ============================================================
# Market data helper (for signal engine)
# ============================================================
def get_market_data():
    """Fetch current market context for signal scoring."""
    try:
        import requests as req
        from strategies.signal_engine import fetch_klines, calculate_ema

        # Fear & Greed
        fg = 50
        try:
            r = req.get('https://api.alternative.me/fng/', timeout=5)
            fg = int(r.json()['data'][0]['value'])
        except Exception:
            pass

        # Trending coins
        trending = ['BTC', 'ETH', 'SOL']
        try:
            r = req.get('https://api.coingecko.com/api/v3/search/trending', timeout=5)
            trending = [item['item']['symbol'].upper() for item in r.json()['coins'][:5]]
        except Exception:
            pass

        # BTC Trend (real EMA check)
        btc_trend = 'neutral'
        try:
            klines = fetch_klines('BTCUSDT', '1h', limit=200)
            if klines and len(klines['closes']) >= 50:
                closes = klines['closes']
                ema50 = calculate_ema(closes, 50)
                ema200 = calculate_ema(closes, 200)
                price = closes[-1]

                # Trend: bullish if price above EMA50, bearish if below
                if price > ema50:
                    btc_trend = 'bullish'
                else:
                    btc_trend = 'bearish'

                # Strong trend: price above both EMAs
                if price > ema50 and price > ema200:
                    btc_trend = 'strong_bullish'
                elif price < ema50 and price < ema200:
                    btc_trend = 'strong_bearish'
        except Exception:
            btc_trend = 'neutral'

        return {
            'fear_greed': fg,
            'btc_trend': btc_trend,
            'trending': trending,
        }
    except Exception:
        return {'fear_greed': 50, 'btc_trend': 'neutral', 'trending': []}


# ============================================================
# Scan job (runs on schedule)
# ============================================================
def scan_job():
    """Execute a trading scan — called by APScheduler."""
    from strategies.signal_engine import run_scan
    from services.telegram_notifier import notify_signal, get_telegram_config

    print(f"[Bot] ⏰ Running scheduled scan at {datetime.now().isoformat()}")

    config = read_json(CONFIG_PATH)
    status = read_json(STATUS_PATH)
    market_data = get_market_data()

    # Check if any strategies are active
    from services.database import get_db
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM strategies WHERE is_active = 1")
    active_strategies_count = cursor.fetchone()[0]
    conn.close()

    if active_strategies_count > 0:
        # Use strategy engine for active strategies
        try:
            from strategies.strategy_engine import scan_all_active_strategies
            signals = scan_all_active_strategies(market_data)
            print(f"[Bot] Strategy scan: {len(signals)} signals from {active_strategies_count} active strategies")
        except Exception as e:
            print(f"[Bot] ❌ Strategy scan error: {e}")
            signals = []
    else:
        # Fallback to legacy scan using config
        try:
            signals = run_scan(config, market_data)
        except Exception as e:
            print(f"[Bot] ❌ Scan error: {e}")
            signals = []

    # Apply learning system (if enabled)
    if config.get('apply_lessons', True) and signals:
        try:
            from strategies.lessons import apply_lessons as apply_learned_lessons
            original_count = len(signals)
            signals = apply_learned_lessons(signals, market_data)
            filtered = original_count - len(signals)
            if filtered > 0:
                print(f"[Bot] 🧠 Learning filtered {filtered} signals (blacklisted patterns)")
        except Exception as e:
            print(f"[Bot] ⚠️ Learning system error (non-fatal): {e}")

    # Save signals to data/signals.json
    write_json(SIGNALS_PATH, {
        'signals': signals,
        'count': len(signals),
        'scanned_at': datetime.now().isoformat(),
    })

    # Update status
    status['scans_performed'] = status.get('scans_performed', 0) + 1
    status['last_scan_at'] = datetime.now().isoformat()

    # Calculate next scan time
    interval_map = {'5m': 5, '15m': 15, '30m': 30, '1h': 60}
    minutes = interval_map.get(config.get('interval', '15m'), 15)
    from datetime import timedelta
    status['next_scan_at'] = (datetime.now() + timedelta(minutes=minutes)).isoformat()

    # Send Telegram alerts for new signals
    tg_enabled = get_telegram_config()['enabled']
    if tg_enabled and signals:
        for signal in signals:
            try:
                notify_signal(signal, config)
                status['signals_sent_today'] = status.get('signals_sent_today', 0) + 1
            except Exception as e:
                print(f"[Bot] ⚠️ Telegram send failed: {e}")

    write_json(STATUS_PATH, status)
    print(f"[Bot] ✅ Scan done: {len(signals)} signals")


# ============================================================
# Routes
# ============================================================
@bot_bp.route('/status', methods=['GET'])
@require_auth
def get_status():
    """Get current bot status"""
    status = read_json(STATUS_PATH)
    config = read_json(CONFIG_PATH)

    # Check if scheduler job is actually running
    job = scheduler.get_job(SCAN_JOB_ID)
    actual_status = 'running' if job else 'stopped'

    # Sync if out of date
    if status.get('status') != actual_status:
        status['status'] = actual_status
        write_json(STATUS_PATH, status)

    return jsonify({
        'status': actual_status,
        'started_at': status.get('started_at'),
        'stopped_at': status.get('stopped_at'),
        'signals_sent_today': status.get('signals_sent_today', 0),
        'scans_performed': status.get('scans_performed', 0),
        'last_scan_at': status.get('last_scan_at'),
        'next_scan_at': status.get('next_scan_at'),
        'mode': config.get('mode', 'SWING'),
        'interval': config.get('interval', '15m'),
    })


@bot_bp.route('/start', methods=['POST'])
@require_auth
def start_bot():
    """Start the trading bot with scheduled scans"""
    status = read_json(STATUS_PATH)
    config = read_json(CONFIG_PATH)

    # Check if already running
    if scheduler.get_job(SCAN_JOB_ID):
        return jsonify({'error': 'Bot is already running'}), 400

    # Determine scan interval
    interval_map = {'5m': 5, '15m': 15, '30m': 30, '1h': 60}
    minutes = interval_map.get(config.get('interval', '15m'), 15)

    # Schedule recurring scan
    scheduler.add_job(
        scan_job,
        trigger=IntervalTrigger(minutes=minutes),
        id=SCAN_JOB_ID,
        name='Trading Scan',
        replace_existing=True,
    )

    # Update status
    status['status'] = 'running'
    status['started_at'] = datetime.now().isoformat()
    status['stopped_at'] = None
    status['signals_sent_today'] = 0
    status['scans_performed'] = 0
    write_json(STATUS_PATH, status)

    # Send Telegram notification
    try:
        from services.telegram_notifier import notify_bot_started
        notify_bot_started(config)
    except Exception:
        pass

    print(f"[Bot] ▶ Started ({config.get('mode')} / {config.get('interval')})")

    # Run first scan immediately (in background thread)
    try:
        scheduler.add_job(scan_job, id='immediate_scan', replace_existing=True)
    except Exception:
        pass

    return jsonify({
        'success': True,
        'message': 'Bot started',
        'config': {
            'mode': config.get('mode'),
            'interval': config.get('interval'),
            'coin_pool': config.get('coin_pool'),
            'min_rr': config.get('min_rr'),
            'min_confidence': config.get('min_confidence'),
            'filters': {
                'ema200': config.get('ema200_filter'),
                'fg': config.get('fg_filter'),
                'multitf': config.get('multitf_filter'),
            },
        },
    })


@bot_bp.route('/stop', methods=['POST'])
@require_auth
def stop_bot():
    """Stop the trading bot"""
    status = read_json(STATUS_PATH)

    # Remove scheduled job
    job = scheduler.get_job(SCAN_JOB_ID)
    if not job:
        return jsonify({'error': 'Bot is not running'}), 400

    scheduler.remove_job(SCAN_JOB_ID)

    # Also remove immediate scan if pending
    try:
        scheduler.remove_job('immediate_scan')
    except Exception:
        pass

    # Calculate session duration
    started_at = status.get('started_at')
    if started_at:
        started = datetime.fromisoformat(started_at)
        stopped = datetime.now()
        duration = stopped - started
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        duration_str = f'{hours}h {minutes}m'
    else:
        duration_str = '0h 0m'

    # Update status
    status['status'] = 'stopped'
    status['stopped_at'] = datetime.now().isoformat()
    status['next_scan_at'] = None
    write_json(STATUS_PATH, status)

    session_stats = {
        'duration': duration_str,
        'signals_sent': status.get('signals_sent_today', 0),
        'scans_performed': status.get('scans_performed', 0),
    }

    # Send Telegram notification
    try:
        from services.telegram_notifier import notify_bot_stopped
        notify_bot_stopped(session_stats)
    except Exception:
        pass

    print(f"[Bot] ■ Stopped (session: {duration_str})")

    return jsonify({
        'success': True,
        'message': 'Bot stopped',
        'session_stats': session_stats,
    })
