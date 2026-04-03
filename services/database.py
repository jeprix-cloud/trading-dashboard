"""
SQLite Database Service for TradingCore
Thread-safe database connection with row factory
"""
import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'trading.db')


def get_db_path():
    """Return absolute path to data/trading.db"""
    return os.path.abspath(DB_PATH)


def get_db():
    """Get thread-safe database connection. Returns sqlite3.Connection with row_factory=sqlite3.Row"""
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if not exists. Call this on app startup."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Strategies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS strategies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            coins TEXT NOT NULL,
            mode TEXT DEFAULT 'SWING',
            timeframe TEXT DEFAULT '15m',
            entry_conditions TEXT NOT NULL,
            exit_conditions TEXT NOT NULL,
            entry_logic TEXT DEFAULT 'AND',
            exit_logic TEXT DEFAULT 'OR',
            sl_pct REAL DEFAULT 2.5,
            tp_pct REAL DEFAULT 7.5,
            sl_mode TEXT DEFAULT 'FIXED',
            atr_multiplier REAL DEFAULT 1.5,
            min_confidence INTEGER DEFAULT 50,
            min_rr REAL DEFAULT 2.0,
            is_active INTEGER DEFAULT 0,
            is_template INTEGER DEFAULT 0,
            exchange TEXT DEFAULT 'spot',
            leverage INTEGER DEFAULT 1,
            backtest_win_rate REAL,
            backtest_pnl REAL,
            total_trades INTEGER DEFAULT 0,
            total_wins INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Signals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id TEXT PRIMARY KEY,
            strategy_id TEXT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            exchange TEXT DEFAULT 'spot',
            rsi REAL,
            confidence INTEGER,
            entry_price REAL,
            sl_pct REAL,
            tp_pct REAL,
            rr_ratio REAL,
            atr REAL,
            vwap REAL,
            volume_ratio REAL,
            mode TEXT,
            pattern TEXT,
            indicators_json TEXT,
            status TEXT DEFAULT 'ACTIVE',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Positions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id TEXT,
            strategy_id TEXT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            exchange TEXT DEFAULT 'spot',
            entry_price REAL NOT NULL,
            quantity REAL NOT NULL,
            position_value_usd REAL,
            sl_price REAL,
            tp_price REAL,
            sl_pct REAL,
            tp_pct REAL,
            exit_price REAL,
            pnl_pct REAL,
            pnl_usd REAL,
            status TEXT DEFAULT 'OPEN',
            order_id TEXT,
            sl_order_id TEXT,
            tp_order_id TEXT,
            opened_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            closed_at DATETIME,
            notes TEXT
        )
    ''')
    
    # Backtests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS backtests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT,
            name TEXT,
            symbol TEXT,
            timeframe TEXT,
            start_date TEXT,
            end_date TEXT,
            total_trades INTEGER,
            winning_trades INTEGER,
            losing_trades INTEGER,
            win_rate REAL,
            total_pnl_pct REAL,
            max_drawdown_pct REAL,
            sharpe_ratio REAL,
            avg_trade_pnl REAL,
            best_trade_pnl REAL,
            worst_trade_pnl REAL,
            config_json TEXT,
            trades_json TEXT,
            equity_curve_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Daily performance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_performance (
            date DATE PRIMARY KEY,
            total_trades INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            win_rate REAL DEFAULT 0,
            pnl_pct REAL DEFAULT 0,
            pnl_usd REAL DEFAULT 0,
            max_drawdown_pct REAL DEFAULT 0,
            balance_usd REAL,
            notes TEXT
        )
    ''')
    
    # Risk state table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS risk_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            daily_loss_usd REAL DEFAULT 0,
            daily_loss_pct REAL DEFAULT 0,
            daily_trades INTEGER DEFAULT 0,
            weekly_loss_usd REAL DEFAULT 0,
            weekly_loss_pct REAL DEFAULT 0,
            is_circuit_breaker_active INTEGER DEFAULT 0,
            last_reset_date DATE,
            last_reset_week DATE
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Initialize risk_state with default values if not exists
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO risk_state (id) VALUES (1)')
    conn.commit()
    conn.close()


def migrate_json_to_sqlite():
    """
    One-time migration: read data/trades.json, data/signals.json, data/lessons.json
    and import into SQLite tables. Skip if already migrated.
    """
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    # Check if already migrated
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM signals")
    signal_count = cursor.fetchone()[0]
    conn.close()
    
    if signal_count > 0:
        print("[DB] Migration skipped — data already exists")
        return
    
    # Migrate trades.json
    trades_path = os.path.join(data_dir, 'trades.json')
    if os.path.exists(trades_path):
        import json
        with open(trades_path, 'r') as f:
            trades = json.load(f)
        
        conn = get_db()
        cursor = conn.cursor()
        
        for trade in trades:
            cursor.execute('''
                INSERT INTO positions (
                    symbol, side, entry_price, quantity, sl_pct, tp_pct,
                    exit_price, pnl_pct, pnl_usd, status, opened_at, closed_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade.get('symbol'),
                trade.get('side'),
                trade.get('entry_price'),
                trade.get('quantity'),
                trade.get('sl_pct'),
                trade.get('tp_pct'),
                trade.get('exit_price'),
                trade.get('pnl_pct'),
                trade.get('pnl_usd'),
                trade.get('status', 'CLOSED'),
                trade.get('opened_at'),
                trade.get('closed_at'),
                trade.get('notes')
            ))
        
        conn.commit()
        conn.close()
        print(f"[DB] Migrated {len(trades)} trades from JSON")
    
    # Migrate signals.json
    signals_path = os.path.join(data_dir, 'signals.json')
    if os.path.exists(signals_path):
        import json
        with open(signals_path, 'r') as f:
            signals = json.load(f)
        
        conn = get_db()
        cursor = conn.cursor()
        
        for sig in signals:
            cursor.execute('''
                INSERT INTO signals (
                    id, symbol, side, rsi, confidence, entry_price,
                    sl_pct, tp_pct, rr_ratio, atr, vwap, volume_ratio,
                    mode, pattern, indicators_json, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sig.get('id'),
                sig.get('symbol'),
                sig.get('side'),
                sig.get('rsi'),
                sig.get('confidence'),
                sig.get('entry_price'),
                sig.get('sl_pct'),
                sig.get('tp_pct'),
                sig.get('rr_ratio'),
                sig.get('atr'),
                sig.get('vwap'),
                sig.get('volume_ratio'),
                sig.get('mode'),
                sig.get('pattern'),
                json.dumps(sig.get('indicators')),
                sig.get('status', 'ACTIVE'),
                sig.get('created_at')
            ))
        
        conn.commit()
        conn.close()
        print(f"[DB] Migrated {len(signals)} signals from JSON")


if __name__ == '__main__':
    init_db()
    print(f"Database initialized at: {get_db_path()}")