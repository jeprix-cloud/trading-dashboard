"""
Real Backtest Engine — Historical backtesting with proper trade simulation.
"""
import json
import time
from datetime import datetime, timedelta
from services.database import get_db
from strategies.strategy_engine import (
    calculate_indicator, evaluate_conditions
)


BINANCE_BASE = "https://api.binance.com"


def fetch_historical_klines(symbol, interval, days):
    """
    Fetch klines for <days> from Binance.
    Binance limit is 1000 per request, so paginate if needed.
    
    Returns: dict with opens, highs, lows, closes, volumes, timestamps
    or None on failure.
    """
    import requests
    
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    
    all_klines = []
    current_start = start_time
    
    interval_to_ms = {
        '1m': 60000, '5m': 300000, '15m': 900000,
        '30m': 1800000, '1h': 3600000, '4h': 14400000,
        '1d': 86400000
    }
    step_ms = interval_to_ms.get(interval, 900000)
    
    # Limit requests to avoid rate limiting
    max_requests = 10
    
    for _ in range(max_requests):
        url = f"{BINANCE_BASE}/api/v3/klines"
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'startTime': current_start,
            'endTime': end_time,
            'limit': 1000
        }
        
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            if not data:
                break
            
            all_klines.extend(data)
            
            # If we got less than 1000, we're done
            if len(data) < 1000:
                break
            
            # Move start time to last kline's open time
            current_start = data[-1][0] + step_ms
            
            if current_start >= end_time:
                break
            
            # Small delay to avoid rate limits
            time.sleep(0.2)
            
        except Exception as e:
            print(f"[Backtester] Failed to fetch {symbol} {interval}: {e}")
            break
    
    if not all_klines:
        return None
    
    return {
        'opens': [float(k[1]) for k in all_klines],
        'highs': [float(k[2]) for k in all_klines],
        'lows': [float(k[3]) for k in all_klines],
        'closes': [float(k[4]) for k in all_klines],
        'volumes': [float(k[5]) for k in all_klines],
        'timestamps': [k[0] for k in all_klines]
    }


def calculate_max_drawdown(equity_curve):
    """
    Calculate max drawdown from equity curve.
    equity_curve = list of balance values over time
    Max DD = max peak-to-trough decline as percentage
    """
    if not equity_curve or len(equity_curve) < 2:
        return 0.0
    
    peak = equity_curve[0]
    max_dd = 0.0
    
    for value in equity_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
    
    return round(max_dd, 2)


def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """
    Calculate Sharpe ratio from list of per-trade PnL percentages.
    Sharpe = (mean_return - risk_free) / std_dev(returns)
    """
    if not returns or len(returns) < 2:
        return 0.0
    
    import statistics
    
    mean_return = statistics.mean(returns)
    std_dev = statistics.stdev(returns)
    
    if std_dev == 0:
        return 0.0
    
    sharpe = (mean_return - risk_free_rate) / std_dev
    return round(sharpe, 2)


def run_backtest(strategy_id, days=90, initial_balance=100.0):
    """
    Run backtest for a strategy over historical data.
    
    1. Load strategy from database
    2. For each coin in strategy:
       a. Fetch historical klines
       b. Need at least 200 candles for EMA200
       c. Start evaluating from candle 200 onward
       d. For each candle (i):
          - Build klines slice [0:i+1] for indicator calculation
          - Evaluate entry conditions using strategy_engine.evaluate_conditions()
          - If entry conditions met AND no open position:
            * Open position at close price
            * Calculate SL and TP prices
          - If position is open:
            * Check if low <= SL price → close at SL, record loss
            * Check if high >= TP price → close at TP, record win
            * Evaluate exit conditions → close at close price if met
    3. Calculate summary stats
    4. Save to backtests table
    5. Return results
    """
    from services.database import get_db
    
    # Load strategy
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {'error': f'Strategy {strategy_id} not found'}
    
    strategy = dict(row)
    
    coins = strategy.get('coins', '[]')
    if isinstance(coins, str):
        try:
            coins = json.loads(coins)
        except:
            coins = []
    
    entry_conditions = strategy.get('entry_conditions', '[]')
    if isinstance(entry_conditions, str):
        try:
            entry_conditions = json.loads(entry_conditions)
        except:
            entry_conditions = []
    
    exit_conditions = strategy.get('exit_conditions', '[]')
    if isinstance(exit_conditions, str):
        try:
            exit_conditions = json.loads(exit_conditions)
        except:
            exit_conditions = []
    
    entry_logic = strategy.get('entry_logic', 'AND')
    exit_logic = strategy.get('exit_logic', 'OR')
    
    timeframe = strategy.get('timeframe', '1h')
    sl_pct = strategy.get('sl_pct', 2.5)
    tp_pct = strategy.get('tp_pct', 7.5)
    
    all_trades = []
    equity_curve = [initial_balance]
    
    for coin in coins:
        print(f"[Backtester] Testing {coin}...")
        
        klines = fetch_historical_klines(coin, timeframe, days)
        position = None
        highs = klines['highs']
        lows = klines['lows']
        closes = klines['closes']
        volumes = klines['volumes']
        
        # Start from candle 200 (need enough for EMA200)
        position = None  # {'entry_price': float, 'side': str, 'sl': float, 'tp': float}
        
        for i in range(200, len(closes)):
            # Build current klines slice
            current_klines = {
                'opens': opens[:i+1],
                'highs': highs[:i+1],
                'lows': lows[:i+1],
                'closes': closes[:i+1],
                'volumes': volumes[:i+1]
            }
            
            prev_klines = None
            if i > 200:
                prev_klines = {
                    'opens': opens[:i],
                    'highs': highs[:i],
                    'lows': lows[:i],
                    'closes': closes[:i],
                    'volumes': volumes[:i]
                }
            
            current_price = closes[i]
            
            if position is None:
                # Check entry conditions
                entry_met, _ = evaluate_conditions(
                    entry_conditions, entry_logic, current_klines, prev_klines
                )
                
                if entry_met:
                    # Determine side
                    # Find RSI condition to determine direction
                    side = 'BUY'
                    for cond in entry_conditions:
                        if cond.get('indicator') == 'RSI':
                            op = cond.get('operator', '<')
                            if op in ['<', '<=']:
                                side = 'BUY'
                            elif op in ['>', '>=']:
                                side = 'SELL'
                            break
                    
                    sl_price = current_price * (1 - sl_pct / 100) if side == 'BUY' else current_price * (1 + sl_pct / 100)
                    tp_price = current_price * (1 + tp_pct / 100) if side == 'BUY' else current_price * (1 - tp_pct / 100)
                    
                    position = {
                        'entry_price': current_price,
                        'side': side,
                        'sl': sl_price,
                        'tp': tp_price,
                        'entry_time': datetime.fromtimestamp(klines['timestamps'][i] / 1000).isoformat()
                    }
            
            else:
                # Check exit conditions
                exit_met, _ = evaluate_conditions(
                    exit_conditions, exit_logic, current_klines, prev_klines
                )
                
                # Check SL/TP hit
                sl_hit = False
                tp_hit = False
                
                if position['side'] == 'BUY':
                    if lows[i] <= position['sl']:
                        sl_hit = True
                    elif highs[i] >= position['tp']:
                        tp_hit = True
                else:  # SELL
                    if highs[i] >= position['sl']:
                        sl_hit = True
                    elif lows[i] <= position['tp']:
                        tp_hit = True
                
                if sl_hit or tp_hit or exit_met:
                    exit_price = position['sl'] if sl_hit else (position['tp'] if tp_hit else current_price)
                    
                    if position['side'] == 'BUY':
                        pnl_pct = (exit_price - position['entry_price']) / position['entry_price'] * 100
                    else:
                        pnl_pct = (position['entry_price'] - exit_price) / position['entry_price'] * 100
                    
                    trade = {
                        'symbol': coin,
                        'side': position['side'],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'exit_reason': 'SL' if sl_hit else ('TP' if tp_hit else 'EXIT'),
                        'pnl_pct': round(pnl_pct, 4),
                        'entry_time': position['entry_time'],
                        'exit_time': datetime.fromtimestamp(klines['timestamps'][i] / 1000).isoformat()
                    }
                    
                    all_trades.append(trade)
                    
                    # Update equity
                    position_value = equity_curve[-1]
                    pnl = position_value * (pnl_pct / 100)
                    new_balance = position_value + pnl
                    equity_curve.append(new_balance)
                    
                    position = None
    
    # If position still open at end, close at last price
    if position:
        last_price = closes[-1]
        if position['side'] == 'BUY':
            pnl_pct = (last_price - position['entry_price']) / position['entry_price'] * 100
        else:
            pnl_pct = (position['entry_price'] - last_price) / position['entry_price'] * 100
        
        trade = {
            'symbol': coin,
            'side': position['side'],
            'entry_price': position['entry_price'],
            'exit_price': last_price,
            'exit_reason': 'END',
            'pnl_pct': round(pnl_pct, 4),
            'entry_time': position['entry_time'],
            'exit_time': datetime.now().isoformat()
        }
        all_trades.append(trade)
        
        pnl = equity_curve[-1] * (pnl_pct / 100)
        equity_curve.append(equity_curve[-1] + pnl)
    
    # Calculate stats
    total_trades = len(all_trades)
    if total_trades == 0:
        return {'error': 'No trades generated', 'total_trades': 0}
    
    winning_trades = [t for t in all_trades if t['pnl_pct'] > 0]
    losing_trades = [t for t in all_trades if t['pnl_pct'] <= 0]
    
    win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
    
    pnls = [t['pnl_pct'] for t in all_trades]
    total_pnl_pct = sum(pnls)
    avg_trade_pnl = sum(pnls) / len(pnls)
    best_trade_pnl = max(pnls)
    worst_trade_pnl = min(pnls)
    
    max_drawdown = calculate_max_drawdown(equity_curve)
    sharpe = calculate_sharpe_ratio(pnls)
    
    # Save to database
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO backtests (
            strategy_id, name, symbol, timeframe,
            start_date, end_date,
            total_trades, winning_trades, losing_trades,
            win_rate, total_pnl_pct, max_drawdown_pct,
            sharpe_ratio, avg_trade_pnl, best_trade_pnl, worst_trade_pnl,
            config_json, trades_json, equity_curve_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        strategy_id,
        strategy.get('name', 'Backtest'),
        ','.join(coins) if isinstance(coins, list) else coins,
        timeframe,
        (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
        datetime.now().strftime('%Y-%m-%d'),
        total_trades,
        len(winning_trades),
        len(losing_trades),
        round(win_rate, 2),
        round(total_pnl_pct, 2),
        max_drawdown,
        sharpe,
        round(avg_trade_pnl, 4),
        round(best_trade_pnl, 4),
        round(worst_trade_pnl, 4),
        json.dumps({
            'sl_pct': sl_pct,
            'tp_pct': tp_pct,
            'entry_conditions': entry_conditions,
            'exit_conditions': exit_conditions,
            'initial_balance': initial_balance
        }),
        json.dumps(all_trades),
        json.dumps(equity_curve)
    ))
    
    backtest_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        'id': backtest_id,
        'strategy_id': strategy_id,
        'strategy_name': strategy.get('name'),
        'total_trades': total_trades,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': round(win_rate, 2),
        'total_pnl_pct': round(total_pnl_pct, 2),
        'max_drawdown_pct': max_drawdown,
        'sharpe_ratio': sharpe,
        'avg_trade_pnl': round(avg_trade_pnl, 4),
        'best_trade_pnl': round(best_trade_pnl, 4),
        'worst_trade_pnl': round(worst_trade_pnl, 4),
        'equity_curve': equity_curve,
        'trades': all_trades[-20:],  # Last 20 trades for display
        'initial_balance': initial_balance,
        'final_balance': round(equity_curve[-1], 2)
    }


def preview_backtest(conditions, coins, sl_pct, tp_pct, days=30, initial_balance=100.0):
    """
    Quick backtest WITHOUT saving strategy first.
    Useful for testing before committing to a strategy.
    """
    all_trades = []
    equity_curve = [initial_balance]
    
    timeframe = '1h'  # Default for preview
    
    for coin in coins:
        klines = fetch_historical_klines(coin, timeframe, days)
        if not klines or len(klines['closes']) < 200:
            continue
        
        opens = klines['opens']
        highs = klines['highs']
        lows = klines['lows']
        closes = klines['closes']
        volumes = klines['volumes']
        
        position = None
        
        for i in range(200, len(closes)):
            current_klines = {
                'opens': opens[:i+1],
                'highs': highs[:i+1],
                'lows': lows[:i+1],
                'closes': closes[:i+1],
                'volumes': volumes[:i+1]
            }
            
            prev_klines = None
            if i > 200:
                prev_klines = {
                    'opens': opens[:i],
                    'highs': highs[:i],
                    'lows': lows[:i],
                    'closes': closes[:i],
                    'volumes': volumes[:i]
                }
            
            current_price = closes[i]
            
            if position is None:
                entry_met, _ = evaluate_conditions(conditions, 'AND', current_klines, prev_klines)
                if entry_met:
                    side = 'BUY'
                    for cond in conditions:
                        if cond.get('indicator') == 'RSI':
                            if cond.get('operator') in ['<', '<=']:
                                side = 'BUY'
                            elif cond.get('operator') in ['>', '>=']:
                                side = 'SELL'
                            break
                    
                    sl_price = current_price * (1 - sl_pct / 100) if side == 'BUY' else current_price * (1 + sl_pct / 100)
                    tp_price = current_price * (1 + tp_pct / 100) if side == 'BUY' else current_price * (1 - tp_pct / 100)
                    
                    position = {
                        'entry_price': current_price,
                        'side': side,
                        'sl': sl_price,
                        'tp': tp_price,
                        'entry_time': datetime.fromtimestamp(klines['timestamps'][i] / 1000).isoformat()
                    }
            
            else:
                exit_met, _ = evaluate_conditions(conditions, 'OR', current_klines, prev_klines)
                
                sl_hit = tp_hit = False
                if position['side'] == 'BUY':
                    if lows[i] <= position['sl']:
                        sl_hit = True
                    elif highs[i] >= position['tp']:
                        tp_hit = True
                else:
                    if highs[i] >= position['sl']:
                        sl_hit = True
                    elif lows[i] <= position['tp']:
                        tp_hit = True
                
                if sl_hit or tp_hit or exit_met:
                    exit_price = position['sl'] if sl_hit else (position['tp'] if tp_hit else current_price)
                    
                    if position['side'] == 'BUY':
                        pnl_pct = (exit_price - position['entry_price']) / position['entry_price'] * 100
                    else:
                        pnl_pct = (position['entry_price'] - exit_price) / position['entry_price'] * 100
                    
                    all_trades.append({
                        'symbol': coin,
                        'side': position['side'],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'exit_reason': 'SL' if sl_hit else ('TP' if tp_hit else 'EXIT'),
                        'pnl_pct': round(pnl_pct, 4),
                        'entry_time': position['entry_time'],
                        'exit_time': datetime.fromtimestamp(klines['timestamps'][i] / 1000).isoformat()
                    })
                    
                    pnl = equity_curve[-1] * (pnl_pct / 100)
                    equity_curve.append(equity_curve[-1] + pnl)
                    position = None
    
        if position:
            last_price = closes[-1]
            if position['side'] == 'BUY':
                pnl_pct = (last_price - position['entry_price']) / position['entry_price'] * 100
            else:
                pnl_pct = (position['entry_price'] - last_price) / position['entry_price'] * 100

            all_trades.append({
                'symbol': coin,
                'side': position['side'],
                'entry_price': position['entry_price'],
                'exit_price': last_price,
                'exit_reason': 'END',
                'pnl_pct': round(pnl_pct, 4),
                'entry_time': position['entry_time'],
                'exit_time': datetime.now().isoformat()
            })
            equity_curve.append(equity_curve[-1] + equity_curve[-1] * (pnl_pct / 100))
    
    total_trades = len(all_trades)
    if total_trades == 0:
        return {'total_trades': 0, 'message': 'No trades generated'}
    
    winning_trades = [t for t in all_trades if t['pnl_pct'] > 0]
    pnls = [t['pnl_pct'] for t in all_trades]
    
    return {
        'total_trades': total_trades,
        'winning_trades': len(winning_trades),
        'losing_trades': total_trades - len(winning_trades),
        'win_rate': round(len(winning_trades) / total_trades * 100, 2),
        'total_pnl_pct': round(sum(pnls), 2),
        'avg_trade_pnl': round(sum(pnls) / len(pnls), 4),
        'best_trade_pnl': round(max(pnls), 4),
        'worst_trade_pnl': round(min(pnls), 4),
        'max_drawdown_pct': calculate_max_drawdown(equity_curve),
        'equity_curve': equity_curve,
        'trades': all_trades[-20:],
        'initial_balance': initial_balance,
        'final_balance': round(equity_curve[-1], 2)
    }