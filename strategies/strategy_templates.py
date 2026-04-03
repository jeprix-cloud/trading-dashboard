"""
Strategy Templates — Built-in strategy patterns for quick strategy creation.
"""
import uuid
from services.database import get_db


def get_templates():
    """Return list of strategy template dicts"""
    return [
        {
            "id": "tpl_rsi_conservative",
            "name": "RSI Oversold (Conservative)",
            "description": "Classic RSI oversold bounce with EMA200 trend filter. Best for BTC, ETH.",
            "coins": '["BTCUSDT", "ETHUSDT"]',
            "mode": "SWING",
            "timeframe": "1h",
            "entry_conditions": '[{"indicator":"RSI","period":14,"operator":"<","value":30},{"indicator":"PRICE_VS_EMA","period":200,"operator":">","value":0}]',
            "exit_conditions": '[{"indicator":"RSI","period":14,"operator":">","value":70}]',
            "entry_logic": "AND",
            "exit_logic": "OR",
            "sl_pct": 2.5,
            "tp_pct": 7.5,
            "sl_mode": "FIXED",
            "atr_multiplier": 1.5,
            "min_confidence": 60,
            "min_rr": 2.0,
            "is_template": 1,
            "is_active": 0,
            "exchange": "spot",
            "leverage": 1
        },
        {
            "id": "tpl_rsi_aggressive",
            "name": "RSI Oversold (Aggressive)",
            "description": "RSI oversold without trend filter. For altcoins with higher volatility.",
            "coins": '["SOLUSDT", "AVAXUSDT", "MATICUSDT", "LINKUSDT"]',
            "mode": "SWING",
            "timeframe": "15m",
            "entry_conditions": '[{"indicator":"RSI","period":14,"operator":"<","value":35}]',
            "exit_conditions": '[{"indicator":"RSI","period":14,"operator":">","value":65}]',
            "entry_logic": "AND",
            "exit_logic": "OR",
            "sl_pct": 3.0,
            "tp_pct": 9.0,
            "sl_mode": "FIXED",
            "atr_multiplier": 1.5,
            "min_confidence": 55,
            "min_rr": 2.0,
            "is_template": 1,
            "is_active": 0,
            "exchange": "spot",
            "leverage": 1
        },
        {
            "id": "tpl_ema_cross",
            "name": "EMA Cross Bullish",
            "description": "EMA9 crossing above EMA21 with price above EMA200. Trend following.",
            "coins": '["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]',
            "mode": "SWING",
            "timeframe": "1h",
            "entry_conditions": '[{"indicator":"EMA","period":9,"operator":">","value":0},{"indicator":"EMA","period":21,"operator":">","value":0}]',
            "exit_conditions": '[{"indicator":"EMA","period":9,"operator":"<","value":0}]',
            "entry_logic": "AND",
            "exit_logic": "OR",
            "sl_pct": 2.0,
            "tp_pct": 6.0,
            "sl_mode": "FIXED",
            "atr_multiplier": 1.5,
            "min_confidence": 50,
            "min_rr": 2.0,
            "is_template": 1,
            "is_active": 0,
            "exchange": "spot",
            "leverage": 1
        },
        {
            "id": "tpl_macd_momentum",
            "name": "MACD Momentum",
            "description": "MACD line above signal line with positive histogram. Momentum play.",
            "coins": '["BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "NEARUSDT"]',
            "mode": "SWING",
            "timeframe": "1h",
            "entry_conditions": '[{"indicator":"MACD","operator":">","value":0}]',
            "exit_conditions": '[{"indicator":"MACD","operator":"<","value":0}]',
            "entry_logic": "AND",
            "exit_logic": "OR",
            "sl_pct": 2.5,
            "tp_pct": 7.5,
            "sl_mode": "FIXED",
            "atr_multiplier": 1.5,
            "min_confidence": 50,
            "min_rr": 2.0,
            "is_template": 1,
            "is_active": 0,
            "exchange": "spot",
            "leverage": 1
        },
        {
            "id": "tpl_bollinger_bounce",
            "name": "Bollinger Bounce",
            "description": "Price bouncing off lower Bollinger Band with RSI oversold. Range-bound play.",
            "coins": '["BTCUSDT", "ETHUSDT", "BNBUSDT"]',
            "mode": "SWING",
            "timeframe": "15m",
            "entry_conditions": '[{"indicator":"BOLLINGER","period":20,"operator":"<","value":20},{"indicator":"RSI","period":14,"operator":"<","value":35}]',
            "exit_conditions": '[{"indicator":"RSI","period":14,"operator":">","value":50}]',
            "entry_logic": "AND",
            "exit_logic": "OR",
            "sl_pct": 2.0,
            "tp_pct": 5.0,
            "sl_mode": "FIXED",
            "atr_multiplier": 1.5,
            "min_confidence": 55,
            "min_rr": 2.0,
            "is_template": 1,
            "is_active": 0,
            "exchange": "spot",
            "leverage": 1
        },
        {
            "id": "tpl_volume_breakout",
            "name": "Volume Breakout",
            "description": "Volume surge with RSI below 40. Breakout momentum play.",
            "coins": '["BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "APTUSDT"]',
            "mode": "SCALP",
            "timeframe": "5m",
            "entry_conditions": '[{"indicator":"VOLUME","operator":">","value":2.0},{"indicator":"RSI","period":14,"operator":"<","value":40}]',
            "exit_conditions": '[{"indicator":"RSI","period":14,"operator":">","value":65}]',
            "entry_logic": "AND",
            "exit_logic": "OR",
            "sl_pct": 0.3,
            "tp_pct": 0.9,
            "sl_mode": "FIXED",
            "atr_multiplier": 1.5,
            "min_confidence": 50,
            "min_rr": 2.0,
            "is_template": 1,
            "is_active": 0,
            "exchange": "spot",
            "leverage": 1
        },
        {
            "id": "tpl_scalp_quick",
            "name": "Scalp Quick",
            "description": "Fast RSI oversold with volume confirmation. Quick scalp on 1m.",
            "coins": '["BTCUSDT", "ETHUSDT", "BNBUSDT"]',
            "mode": "SCALP",
            "timeframe": "1m",
            "entry_conditions": '[{"indicator":"RSI","period":14,"operator":"<","value":25},{"indicator":"VOLUME","operator":">","value":2.0}]',
            "exit_conditions": '[{"indicator":"RSI","period":14,"operator":">","value":40}]',
            "entry_logic": "AND",
            "exit_logic": "OR",
            "sl_pct": 0.2,
            "tp_pct": 0.6,
            "sl_mode": "FIXED",
            "atr_multiplier": 1.5,
            "min_confidence": 50,
            "min_rr": 2.0,
            "is_template": 1,
            "is_active": 0,
            "exchange": "spot",
            "leverage": 1
        }
    ]


def seed_templates():
    """Insert templates into database if not already present"""
    from services.database import get_db
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if templates already exist
    cursor.execute("SELECT COUNT(*) FROM strategies WHERE is_template = 1")
    count = cursor.fetchone()[0]
    
    if count > 0:
        conn.close()
        return  # Already seeded
    
    templates = get_templates()
    
    for tpl in templates:
        cursor.execute('''
            INSERT INTO strategies (
                id, name, description, coins, mode, timeframe,
                entry_conditions, exit_conditions, entry_logic, exit_logic,
                sl_pct, tp_pct, sl_mode, atr_multiplier, min_confidence, min_rr,
                is_active, is_template, exchange, leverage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tpl['id'],
            tpl['name'],
            tpl['description'],
            tpl['coins'],
            tpl['mode'],
            tpl['timeframe'],
            tpl['entry_conditions'],
            tpl['exit_conditions'],
            tpl['entry_logic'],
            tpl['exit_logic'],
            tpl['sl_pct'],
            tpl['tp_pct'],
            tpl['sl_mode'],
            tpl['atr_multiplier'],
            tpl['min_confidence'],
            tpl['min_rr'],
            tpl['is_active'],
            tpl['is_template'],
            tpl['exchange'],
            tpl['leverage']
        ))
    
    conn.commit()
    conn.close()
    print(f"[Strategy Templates] Seeded {len(templates)} templates")


def get_template_by_id(template_id):
    """Get a single template by ID"""
    templates = get_templates()
    for tpl in templates:
        if tpl['id'] == template_id:
            return tpl
    return None