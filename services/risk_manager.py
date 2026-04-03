"""
Risk Manager — Circuit breakers, position size limits, max exposure.
"""
from datetime import date, datetime
from services.database import get_db

# ============================================================
# CONFIG CONSTANTS (can be overridden via config file)
# ============================================================
DEFAULT_MAX_DAILY_LOSS_PCT = 5.0      # Max daily loss % before circuit breaker
DEFAULT_MAX_WEEKLY_LOSS_PCT = 10.0    # Max weekly loss %
DEFAULT_MAX_POSITION_PCT = 20.0       # Max % of balance in single position
DEFAULT_MAX_POSITIONS = 3             # Max open positions simultaneously
DEFAULT_MIN_EQUITY_PCT = 50.0          # Min equity % (vs starting balance) before warning


def load_risk_config():
    """Load risk limits from config/bot_config.json"""
    import json, os
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'bot_config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return {
            'max_daily_loss_pct': config.get('max_daily_loss_pct', DEFAULT_MAX_DAILY_LOSS_PCT),
            'max_weekly_loss_pct': config.get('max_weekly_loss_pct', DEFAULT_MAX_WEEKLY_LOSS_PCT),
            'max_position_pct': config.get('max_position_pct', DEFAULT_MAX_POSITION_PCT),
            'max_positions': config.get('max_positions', DEFAULT_MAX_POSITIONS),
            'min_equity_pct': config.get('min_equity_pct', DEFAULT_MIN_EQUITY_PCT),
        }
    except:
        return {
            'max_daily_loss_pct': DEFAULT_MAX_DAILY_LOSS_PCT,
            'max_weekly_loss_pct': DEFAULT_MAX_WEEKLY_LOSS_PCT,
            'max_position_pct': DEFAULT_MAX_POSITION_PCT,
            'max_positions': DEFAULT_MAX_POSITIONS,
            'min_equity_pct': DEFAULT_MIN_EQUITY_PCT,
        }


def get_risk_state():
    """Get current risk state from DB. Initializes row if missing."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM risk_state WHERE id = 1')
    row = cursor.fetchone()
    
    if not row:
        # Initialize with defaults
        cursor.execute('INSERT INTO risk_state (id) VALUES (1)')
        conn.commit()
        cursor.execute('SELECT * FROM risk_state WHERE id = 1')
        row = cursor.fetchone()
    
    conn.close()
    return dict(row) if row else None


def update_risk_state(daily_loss_usd=0, daily_loss_pct=0, weekly_loss_usd=0, weekly_loss_pct=0):
    """
    Update risk_state row in DB.
    Call this after each trade close.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    today = date.today().isoformat()
    week_start = (date.today() - __import__('datetime').timedelta(days=date.today().weekday())).isoformat()
    
    state = get_risk_state()
    
    # Reset if new day
    if state['last_reset_date'] != today:
        daily_loss_usd = 0
        daily_loss_pct = 0
        cursor.execute('UPDATE risk_state SET daily_loss_usd=0, daily_loss_pct=0, daily_trades=0, last_reset_date=? WHERE id=1', (today,))
    
    # Reset if new week
    if state['last_reset_week'] != week_start:
        weekly_loss_usd = 0
        weekly_loss_pct = 0
        cursor.execute('UPDATE risk_state SET weekly_loss_usd=0, weekly_loss_pct=0, last_reset_week=? WHERE id=1', (week_start,))
    
    cursor.execute('''
        UPDATE risk_state
        SET daily_loss_usd = ?, daily_loss_pct = ?,
            weekly_loss_usd = ?, weekly_loss_pct = ?
        WHERE id = 1
    ''', (daily_loss_usd, daily_loss_pct, weekly_loss_usd, weekly_loss_pct))
    
    conn.commit()
    conn.close()


def check_circuit_breaker():
    """
    Check if circuit breaker should be activated.
    Returns: (blocked: bool, reason: str)
    """
    state = get_risk_state()
    config = load_risk_config()
    
    if state.get('is_circuit_breaker_active'):
        return True, "Circuit breaker already active"
    
    # Check daily loss limit
    if state.get('daily_loss_pct', 0) >= config['max_daily_loss_pct']:
        activate_circuit_breaker()
        return True, f"Daily loss {state['daily_loss_pct']:.2f}% >= limit {config['max_daily_loss_pct']}%"
    
    # Check weekly loss limit
    if state.get('weekly_loss_pct', 0) >= config['max_weekly_loss_pct']:
        activate_circuit_breaker()
        return True, f"Weekly loss {state['weekly_loss_pct']:.2f}% >= limit {config['max_weekly_loss_pct']}%"
    
    return False, ""


def activate_circuit_breaker():
    """Set circuit breaker flag to 1 in DB"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE risk_state SET is_circuit_breaker_active = 1 WHERE id = 1')
    conn.commit()
    conn.close()
    print(f"[Risk Manager] 🚨 Circuit breaker ACTIVATED at {datetime.now().isoformat()}")


def deactivate_circuit_breaker():
    """Reset circuit breaker and daily/weekly counters"""
    conn = get_db()
    cursor = conn.cursor()
    today = date.today().isoformat()
    week_start = (date.today() - __import__('datetime').timedelta(days=date.today().weekday())).isoformat()
    cursor.execute('''
        UPDATE risk_state
        SET is_circuit_breaker_active = 0,
            daily_loss_usd = 0, daily_loss_pct = 0, daily_trades = 0,
            weekly_loss_usd = 0, weekly_loss_pct = 0,
            last_reset_date = ?, last_reset_week = ?
        WHERE id = 1
    ''', (today, week_start))
    conn.commit()
    conn.close()
    print(f"[Risk Manager] ✅ Circuit breaker DEACTIVATED at {datetime.now().isoformat()}")


def can_open_position(symbol, entry_price, quantity):
    """
    Pre-trade risk check before opening a position.
    Returns: (allowed: bool, reason: str)
    """
    config = load_risk_config()
    
    # Check circuit breaker
    blocked, reason = check_circuit_breaker()
    if blocked:
        return False, reason
    
    # Check max open positions
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'OPEN'")
    open_count = cursor.fetchone()[0]
    conn.close()
    
    if open_count >= config['max_positions']:
        return False, f"Max open positions reached ({open_count}/{config['max_positions']})"
    
    # Check max position size vs account balance
    from services.position_manager import get_portfolio_summary
    summary = get_portfolio_summary()
    
    position_value = entry_price * quantity
    total_balance = summary.get('total_invested_usd', 0) or 100.0  # fallback to 100 if no history
    
    position_pct = (position_value / total_balance) * 100
    if position_pct > config['max_position_pct']:
        return False, f"Position size {position_pct:.1f}% > max {config['max_position_pct']}%"
    
    # Check total exposure (all open positions)
    if summary.get('total_invested_usd', 0) > 0:
        total_exposure_pct = (summary.get('total_invested_usd', 0) / total_balance) * 100
        if total_exposure_pct + position_pct > config['max_position_pct'] * config['max_positions']:
            return False, f"Total exposure would exceed {config['max_position_pct'] * config['max_positions']}%"
    
    return True, "OK"


def after_position_closed(position_dict):
    """
    Called after a position is closed (SL/TP/Manual).
    Updates risk_state with new PnL and checks circuit breaker.
    """
    pnl_pct = position_dict.get('pnl_pct', 0)
    pnl_usd = position_dict.get('pnl_usd', 0)
    
    if pnl_usd >= 0:
        # Only track losses for circuit breaker
        return
    
    conn = get_db()
    cursor = conn.cursor()
    
    state = get_risk_state()
    
    # Get starting balance (use config or default 1000)
    import json, os
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'bot_config.json')
    try:
        with open(config_path, 'r') as f:
            cfg = json.load(f)
        starting_balance = cfg.get('starting_balance', 1000.0)
    except:
        starting_balance = 1000.0
    
    new_daily_loss_usd = (state.get('daily_loss_usd') or 0) + abs(pnl_usd)
    new_daily_loss_pct = (new_daily_loss_usd / starting_balance) * 100 if starting_balance > 0 else 0
    
    new_weekly_loss_usd = (state.get('weekly_loss_usd') or 0) + abs(pnl_usd)
    new_weekly_loss_pct = (new_weekly_loss_usd / starting_balance) * 100 if starting_balance > 0 else 0
    
    cursor.execute('''
        UPDATE risk_state
        SET daily_loss_usd = ?, daily_loss_pct = ?,
            weekly_loss_usd = ?, weekly_loss_pct = ?,
            daily_trades = daily_trades + 1
        WHERE id = 1
    ''', (new_daily_loss_usd, new_daily_loss_pct, new_weekly_loss_usd, new_weekly_loss_pct))
    conn.commit()
    conn.close()
    
    # Check if we need to activate circuit breaker
    blocked, reason = check_circuit_breaker()
    if blocked:
        print(f"[Risk Manager] 🚨 {reason}")
        # Send Telegram alert
        try:
            from services.telegram_notifier import send_message, load_config
            config = load_config()
            if config.get('enabled'):
                msg = f"🚨 CIRCUIT BREAKER TRIGGERED\n\n{reason}\n\nBot will not open new positions until manually reset."
                send_message(msg, config.get('alert_bot_token'), config.get('alert_chat_id'))
        except:
            pass


def get_risk_status():
    """
    Return current risk status summary for dashboard.
    """
    state = get_risk_state()
    config = load_risk_config()
    from services.position_manager import get_portfolio_summary
    
    summary = get_portfolio_summary()
    
    return {
        'circuit_breaker_active': bool(state.get('is_circuit_breaker_active')),
        'daily_loss_pct': round(state.get('daily_loss_pct', 0), 2),
        'daily_loss_usd': round(state.get('daily_loss_usd', 0), 2),
        'daily_trades': state.get('daily_trades', 0),
        'weekly_loss_pct': round(state.get('weekly_loss_pct', 0), 2),
        'weekly_loss_usd': round(state.get('weekly_loss_usd', 0), 2),
        'limits': {
            'max_daily_loss_pct': config['max_daily_loss_pct'],
            'max_weekly_loss_pct': config['max_weekly_loss_pct'],
            'max_position_pct': config['max_position_pct'],
            'max_positions': config['max_positions'],
            'min_equity_pct': config['min_equity_pct'],
        },
        'portfolio': {
            'open_count': summary.get('open_count', 0),
            'total_invested_usd': summary.get('total_invested_usd', 0),
            'unrealized_pnl_usd': summary.get('unrealized_pnl_usd', 0),
            'all_time_pnl_usd': summary.get('all_time_pnl_usd', 0),
        }
    }