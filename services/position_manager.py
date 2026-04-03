"""
Position Manager — Track and manage open trading positions.
"""
from datetime import datetime
from services.database import get_db


def open_position(signal_id, strategy_id, symbol, side, entry_price, quantity, sl_pct, tp_pct, exchange='spot', order_id=None):
    """
    Insert new position into positions table with status='OPEN'
    
    Returns: position_id (int)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Calculate SL and TP prices
    if side == 'BUY':
        sl_price = entry_price * (1 - sl_pct / 100)
        tp_price = entry_price * (1 + tp_pct / 100)
    else:  # SELL
        sl_price = entry_price * (1 + sl_pct / 100)
        tp_price = entry_price * (1 - tp_pct / 100)
    
    position_value = entry_price * quantity
    
    cursor.execute('''
        INSERT INTO positions (
            signal_id, strategy_id, symbol, side, exchange,
            entry_price, quantity, position_value_usd,
            sl_price, tp_price, sl_pct, tp_pct,
            status, order_id, opened_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        signal_id, strategy_id, symbol, side, exchange,
        entry_price, quantity, position_value,
        sl_price, tp_price, sl_pct, tp_pct,
        'OPEN', order_id, datetime.now().isoformat()
    ))
    
    position_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return position_id


def close_position(position_id, exit_price, reason='MANUAL_CLOSE'):
    """
    Update position: set exit_price, calculate pnl_pct and pnl_usd,
    set status=reason, set closed_at=now
    
    Returns: updated position dict or None if not found
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Get current position
    cursor.execute("SELECT * FROM positions WHERE id = ?", (position_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
    
    entry_price = row['entry_price']
    side = row['side']
    quantity = row['quantity']
    
    # Calculate PnL
    if side == 'BUY':
        pnl_pct = (exit_price - entry_price) / entry_price * 100
    else:  # SELL
        pnl_pct = (entry_price - exit_price) / entry_price * 100
    
    pnl_usd = (pnl_pct / 100) * row['position_value_usd'] if row['position_value_usd'] else 0
    
    cursor.execute('''
        UPDATE positions
        SET exit_price = ?, pnl_pct = ?, pnl_usd = ?, status = ?, closed_at = ?
        WHERE id = ?
    ''', (
        exit_price,
        round(pnl_pct, 4),
        round(pnl_usd, 2),
        reason,
        datetime.now().isoformat(),
        position_id
    ))
    
    conn.commit()
    
    cursor.execute("SELECT * FROM positions WHERE id = ?", (position_id,))
    updated = dict(cursor.fetchone())
    conn.close()
    
    return updated


def check_open_positions():
    """
    For each OPEN position:
    1. Fetch current price from Binance
    2. Calculate current PnL
    3. Check if current price hit SL or TP
    4. If SL/TP hit: close_position() + send Telegram notification
    5. Return list of position updates
    """
    import requests
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM positions WHERE status = 'OPEN'")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return []
    
    updates = []
    
    for row in rows:
        symbol = row['symbol']
        side = row['side']
        sl_price = row['sl_price']
        tp_price = row['tp_price']
        
        # Fetch current price from Binance
        try:
            resp = requests.get(
                'https://api.binance.com/api/v3/ticker/price',
                params={'symbol': symbol.upper()},
                timeout=8
            )
            resp.raise_for_status()
            current_price = float(resp.json()['price'])
        except Exception as e:
            print(f"[Position Manager] Failed to get price for {symbol}: {e}")
            continue
        
        # Check SL/TP hit
        sl_hit = tp_hit = False
        
        if side == 'BUY':
            if current_price <= sl_price:
                sl_hit = True
            elif current_price >= tp_price:
                tp_hit = True
        else:  # SELL
            if current_price >= sl_price:
                sl_hit = True
            elif current_price <= tp_price:
                tp_hit = True
        
        if sl_hit or tp_hit:
            reason = 'SL' if sl_hit else 'TP'
            closed = close_position(row['id'], current_price, reason)
            
            if closed:
                updates.append({
                    'position_id': row['id'],
                    'symbol': symbol,
                    'side': side,
                    'exit_price': current_price,
                    'reason': reason,
                    'pnl_pct': closed['pnl_pct'],
                    'pnl_usd': closed['pnl_usd']
                })
                
                # Send Telegram notification
                try:
                    from services.telegram_notifier import notify_position_closed
                    notify_position_closed(closed)
                except Exception as e:
                    print(f"[Position Manager] Telegram notify failed: {e}")
    
    return updates


def get_open_positions():
    """Query positions WHERE status='OPEN', return as list of dicts"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, signal_id, strategy_id, symbol, side, exchange,
               entry_price, quantity, position_value_usd,
               sl_price, tp_price, sl_pct, tp_pct,
               opened_at, notes
        FROM positions WHERE status = 'OPEN'
        ORDER BY opened_at DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    positions = []
    for row in rows:
        # Fetch current price for each
        import requests
        try:
            resp = requests.get(
                'https://api.binance.com/api/v3/ticker/price',
                params={'symbol': row['symbol'].upper()},
                timeout=8
            )
            current_price = float(resp.json()['price'])
            
            # Calculate unrealized PnL
            if row['side'] == 'BUY':
                pnl_pct = (current_price - row['entry_price']) / row['entry_price'] * 100
            else:
                pnl_pct = (row['entry_price'] - current_price) / row['entry_price'] * 100
        except:
            current_price = row['entry_price']
            pnl_pct = 0
        
        positions.append({
            'id': row['id'],
            'signal_id': row['signal_id'],
            'strategy_id': row['strategy_id'],
            'symbol': row['symbol'],
            'side': row['side'],
            'exchange': row['exchange'],
            'entry_price': row['entry_price'],
            'current_price': round(current_price, 8),
            'quantity': row['quantity'],
            'position_value_usd': row['position_value_usd'],
            'sl_price': row['sl_price'],
            'tp_price': row['tp_price'],
            'sl_pct': row['sl_pct'],
            'tp_pct': row['tp_pct'],
            'unrealized_pnl_pct': round(pnl_pct, 4),
            'unrealized_pnl_usd': round((pnl_pct / 100) * row['position_value_usd'], 2) if row['position_value_usd'] else 0,
            'opened_at': row['opened_at'],
            'notes': row['notes']
        })
    
    return positions


def get_position_history(limit=50):
    """Query closed positions ORDER BY closed_at DESC LIMIT <limit>"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, symbol, side, exchange, entry_price, exit_price,
               quantity, pnl_pct, pnl_usd, status, opened_at, closed_at, notes
        FROM positions WHERE status != 'OPEN'
        ORDER BY closed_at DESC LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_portfolio_summary():
    """
    Return: {
        open_count, total_invested_usd, unrealized_pnl_usd, unrealized_pnl_pct,
        today_realized_pnl, all_time_pnl, all_time_trades, all_time_win_rate
    }
    """
    from datetime import date
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Open positions
    cursor.execute("""
        SELECT COUNT(*), SUM(position_value_usd)
        FROM positions WHERE status = 'OPEN'
    """)
    open_row = cursor.fetchone()
    open_count = open_row[0] or 0
    total_invested = open_row[1] or 0
    
    # Unrealized PnL for open positions
    unrealized_pnl = 0
    if open_count > 0:
        cursor.execute("SELECT id FROM positions WHERE status = 'OPEN'")
        open_ids = [row[0] for row in cursor.fetchall()]
        
        import requests
        for pos_id in open_ids:
            cursor.execute("SELECT symbol, side, entry_price, quantity, position_value_usd FROM positions WHERE id = ?", (pos_id,))
            pos = cursor.fetchone()
            try:
                resp = requests.get(
                    'https://api.binance.com/api/v3/ticker/price',
                    params={'symbol': pos[0].upper()},
                    timeout=8
                )
                current_price = float(resp.json()['price'])
                if pos[1] == 'BUY':
                    pnl_pct = (current_price - pos[2]) / pos[2] * 100
                else:
                    pnl_pct = (pos[2] - current_price) / pos[2] * 100
                unrealized_pnl += (pnl_pct / 100) * pos[4]
            except:
                pass
    
    # Today's realized PnL
    today = date.today().isoformat()
    cursor.execute("""
        SELECT SUM(pnl_usd), COUNT(*)
        FROM positions
        WHERE status != 'OPEN' AND closed_at LIKE ?
    """, (f"{today}%",))
    today_row = cursor.fetchone()
    today_pnl = today_row[0] or 0
    today_trades = today_row[1] or 0
    
    # All-time stats
    cursor.execute("""
        SELECT COUNT(*), SUM(pnl_pct), SUM(pnl_usd), SUM(CASE WHEN pnl_pct > 0 THEN 1 ELSE 0 END)
        FROM positions WHERE status != 'OPEN'
    """)
    all_row = cursor.fetchone()
    all_trades = all_row[0] or 0
    all_pnl_pct = all_row[1] or 0
    all_pnl_usd = all_row[2] or 0
    all_wins = all_row[3] or 0
    
    all_time_win_rate = round(all_wins / all_trades * 100, 2) if all_trades > 0 else 0
    
    conn.close()
    
    unrealized_pnl_pct = round((unrealized_pnl / total_invested) * 100, 2) if total_invested > 0 else 0
    
    return {
        'open_count': open_count,
        'total_invested_usd': round(total_invested, 2),
        'unrealized_pnl_usd': round(unrealized_pnl, 2),
        'unrealized_pnl_pct': unrealized_pnl_pct,
        'today_realized_pnl_usd': round(today_pnl, 2),
        'today_trades': today_trades,
        'all_time_pnl_usd': round(all_pnl_usd, 2),
        'all_time_trades': all_trades,
        'all_time_win_rate': all_time_win_rate
    }