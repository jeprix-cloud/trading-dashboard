"""
Strategy Engine — Evaluate user-defined strategy conditions against market data.
"""
import json
import uuid
from datetime import datetime
from strategies.signal_engine import (
    calculate_rsi_wilder, calculate_ema, calculate_atr,
    calculate_vwap, calculate_confidence, fetch_klines
)


def calculate_indicator(indicator_name, klines, params=None):
    """
    Calculate a single indicator value from klines data.
    
    Supported indicators:
    - RSI: returns RSI value (uses calculate_rsi_wilder)
    - EMA: returns EMA value (uses calculate_ema)
    - MACD: returns (macd_line, signal_line, histogram)
    - BOLLINGER: returns (upper, middle, lower)
    - ATR: returns ATR value (uses calculate_atr)
    - VWAP: returns VWAP value (uses calculate_vwap)
    - VOLUME: returns volume_ratio (current vs 20-period avg)
    - PRICE: returns current close price
    """
    if params is None:
        params = {}
    
    closes = klines.get('closes', [])
    highs = klines.get('highs', [])
    lows = klines.get('lows', [])
    volumes = klines.get('volumes', [])
    
    if not closes:
        return None
    
    indicator = indicator_name.upper()
    
    if indicator == 'RSI':
        period = params.get('period', 14)
        return calculate_rsi_wilder(closes, period)
    
    elif indicator == 'EMA':
        period = params.get('period', 21)
        return calculate_ema(closes, period)
    
    elif indicator == 'MACD':
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal_period = params.get('signal', 9)
        
        # Calculate EMAs for MACD line
        ema_fast = calculate_ema(closes, fast)
        ema_slow = calculate_ema(closes, slow)
        macd_line = ema_fast - ema_slow
        
        # We need MACD history for signal line calculation
        # For simplicity, return current values using last values
        # A full implementation would track MACD series
        macd_hist = []  # Would need historical MACD values
        signal_line = macd_line  # Simplified
        
        return {
            'macd': round(macd_line, 8),
            'signal': round(signal_line, 8),
            'histogram': round(macd_line - signal_line, 8)
        }
    
    elif indicator == 'BOLLINGER':
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2)
        
        if len(closes) < period:
            return None
        
        sma = sum(closes[-period:]) / period
        variance = sum((c - sma) ** 2 for c in closes[-period:]) / period
        std = variance ** 0.5
        
        upper = sma + std_dev * std
        middle = sma
        lower = sma - std_dev * std
        
        return {
            'upper': round(upper, 8),
            'middle': round(middle, 8),
            'lower': round(lower, 8)
        }
    
    elif indicator == 'ATR':
        period = params.get('period', 14)
        return calculate_atr(highs, lows, closes, period)
    
    elif indicator == 'VWAP':
        if len(volumes) < 2:
            return closes[-1] if closes else 0
        return calculate_vwap(closes, volumes)
    
    elif indicator == 'VOLUME':
        if len(volumes) < 21:
            return 1.0
        avg_vol = sum(volumes[-21:-1]) / 20
        current_vol = volumes[-1]
        return current_vol / avg_vol if avg_vol > 0 else 1.0
    
    elif indicator == 'PRICE':
        return closes[-1]
    
    elif indicator == 'PRICE_VS_EMA':
        period = params.get('period', 200)
        if len(closes) < period:
            return 0
        ema_val = calculate_ema(closes, period)
        return (closes[-1] - ema_val) / ema_val * 100  # % difference
    
    return None


def evaluate_single_condition(condition, klines, prev_klines=None):
    """
    Evaluate one condition dict against klines.
    Returns: (bool result, float current_value)
    
    condition example: {"indicator": "RSI", "period": 14, "operator": "<", "value": 30}
    
    Operators: <, >, <=, >=, ==, CROSS_ABOVE, CROSS_BELOW
    For CROSS_ABOVE/BELOW: need prev_klines to compare previous candle state
    """
    indicator = condition.get('indicator', '')
    params = condition.get('params', {})
    operator = condition.get('operator', '>')
    target_value = condition.get('value', 0)
    
    # Get current indicator value
    result = calculate_indicator(indicator, klines, params)
    
    if result is None:
        return False, 0
    
    # Handle dict result (MACD, Bollinger)
    if isinstance(result, dict):
        # For MACD, use histogram; for Bollinger, use position relative to bands
        if indicator == 'MACD':
            current_value = result.get('histogram', 0)
        elif indicator == 'BOLLINGER':
            price = klines.get('closes', [0])[-1]
            upper = result.get('upper', 0)
            lower = result.get('lower', 0)
            if upper == lower:
                current_value = 50
            else:
                current_value = (price - lower) / (upper - lower) * 100
        else:
            current_value = list(result.values())[0] if result else 0
    else:
        current_value = result
    
    # Handle CROSS_ABOVE / CROSS_BELOW
    if operator == 'CROSS_ABOVE':
        if prev_klines is None:
            return False, current_value
        prev_result = calculate_indicator(indicator, prev_klines, params)
        if prev_result is None:
            return False, current_value
        if isinstance(prev_result, dict):
            prev_value = list(prev_result.values())[0]
        else:
            prev_value = prev_result
        # Current crosses above target, prev was below
        return prev_value < target_value and current_value >= target_value, current_value
    
    elif operator == 'CROSS_BELOW':
        if prev_klines is None:
            return False, current_value
        prev_result = calculate_indicator(indicator, prev_klines, params)
        if prev_result is None:
            return False, current_value
        if isinstance(prev_result, dict):
            prev_value = list(prev_result.values())[0]
        else:
            prev_value = prev_result
        return prev_value > target_value and current_value <= target_value, current_value
    
    # Standard comparison operators
    if operator == '<':
        return current_value < target_value, current_value
    elif operator == '>':
        return current_value > target_value, current_value
    elif operator == '<=':
        return current_value <= target_value, current_value
    elif operator == '>=':
        return current_value >= target_value, current_value
    elif operator == '==':
        return abs(current_value - target_value) < 0.0001, current_value
    
    return False, current_value


def evaluate_conditions(conditions, logic, klines, prev_klines=None):
    """
    Evaluate array of conditions with AND/OR logic.
    Returns: (bool result, list of condition_details)
    
    logic='AND': ALL conditions must be true
    logic='OR': ANY condition must be true
    """
    if not conditions:
        return True, []
    
    details = []
    results = []
    
    for condition in conditions:
        passed, current_val = evaluate_single_condition(condition, klines, prev_klines)
        details.append({
            'condition': condition,
            'passed': passed,
            'value': current_val
        })
        results.append(passed)
    
    if logic == 'AND':
        final_result = all(results)
    else:  # OR
        final_result = any(results)
    
    return final_result, details


def scan_with_strategy(strategy_dict, market_data=None):
    """
    Run scan for ONE strategy across all its coins.
    
    1. For each coin in strategy['coins']:
       a. Fetch klines (use signal_engine.fetch_klines)
       b. Evaluate entry_conditions
       c. If entry met → calculate confidence, generate signal dict
    2. Filter by min_confidence, min_rr
    3. Return list of signals
    """
    coins = strategy_dict.get('coins', [])
    if isinstance(coins, str):
        try:
            coins = json.loads(coins)
        except:
            coins = []
    
    if not coins:
        return []
    
    entry_conditions = strategy_dict.get('entry_conditions', '[]')
    if isinstance(entry_conditions, str):
        try:
            entry_conditions = json.loads(entry_conditions)
        except:
            entry_conditions = []
    
    exit_conditions = strategy_dict.get('exit_conditions', '[]')
    if isinstance(exit_conditions, str):
        try:
            exit_conditions = json.loads(exit_conditions)
        except:
            exit_conditions = []
    
    entry_logic = strategy_dict.get('entry_logic', 'AND')
    exit_logic = strategy_dict.get('exit_logic', 'OR')
    
    mode = strategy_dict.get('mode', 'SWING')
    timeframe = strategy_dict.get('timeframe', '15m')
    sl_pct = strategy_dict.get('sl_pct', 2.5)
    tp_pct = strategy_dict.get('tp_pct', 7.5)
    min_confidence = strategy_dict.get('min_confidence', 50)
    min_rr = strategy_dict.get('min_rr', 2.0)
    
    signals = []
    
    for coin in coins:
        try:
            klines = fetch_klines(coin, interval=timeframe, limit=200)
            if not klines or len(klines['closes']) < 50:
                continue
            
            # Get previous klines for cross detection
            prev_klines = None
            if len(klines['closes']) >= 51:
                prev_klines = {
                    'opens': klines['opens'][:-1],
                    'highs': klines['highs'][:-1],
                    'lows': klines['lows'][:-1],
                    'closes': klines['closes'][:-1],
                    'volumes': klines['volumes'][:-1]
                }
            
            # Evaluate entry conditions
            entry_met, entry_details = evaluate_conditions(
                entry_conditions, entry_logic, klines, prev_klines
            )
            
            if not entry_met:
                continue
            
            # Determine side based on RSI comparison
            # If RSI < 30 → BUY; If RSI > 70 → SELL
            closes = klines['closes']
            rsi = calculate_rsi_wilder(closes, 14)
            
            # Figure out which condition passed to infer side
            # Default to RSI-based inference
            side = 'BUY' if rsi < 50 else 'SELL'
            
            # Check conditions more carefully
            for detail in entry_details:
                cond = detail['condition']
                if cond.get('indicator') == 'RSI':
                    if detail['passed']:
                        # RSI condition passed - check if it's < or >
                        op = cond.get('operator', '>')
                        val = cond.get('value', 50)
                        if op == '<' or op == '<=':
                            side = 'BUY'
                        elif op == '>' or op == '>=':
                            side = 'SELL'
            
            current_price = closes[-1]
            
            # Calculate RR
            rr_ratio = round(tp_pct / sl_pct, 1) if sl_pct > 0 else 0
            
            # Calculate volume ratio
            volumes = klines['volumes']
            if len(volumes) >= 21:
                avg_vol = sum(volumes[-21:-1]) / 20
                volume_ratio = volumes[-1] / avg_vol if avg_vol > 0 else 1.0
            else:
                volume_ratio = 1.0
            
            # Calculate macro score
            macro_score = 50
            if market_data:
                fg = market_data.get('fear_greed', 50)
                btc_trend = market_data.get('btc_trend', 'neutral')
                if side == 'BUY' and fg < 40:
                    macro_score = 80
                elif side == 'BUY' and fg < 50:
                    macro_score = 60
                elif side == 'SELL' and fg > 60:
                    macro_score = 80
                elif side == 'SELL' and fg > 50:
                    macro_score = 60
            
            # Calculate confidence
            confidence = calculate_confidence(
                rsi=rsi,
                rr_ratio=rr_ratio,
                volume_ratio=volume_ratio,
                macro_score=macro_score,
                multitf_aligned=True,
                trending=False
            )
            
            # Filter by min_confidence and min_rr
            if confidence < min_confidence:
                continue
            if rr_ratio < min_rr:
                continue
            
            signal = {
                'id': f"sig_{uuid.uuid4().hex[:8]}",
                'strategy_id': strategy_dict.get('id'),
                'symbol': coin.replace('USDT', '/USDT'),
                'side': side,
                'exchange': strategy_dict.get('exchange', 'spot'),
                'rsi': round(rsi, 2),
                'confidence': confidence,
                'entry_price': round(current_price, 2),
                'sl_pct': round(sl_pct, 2),
                'tp_pct': round(tp_pct, 2),
                'rr_ratio': rr_ratio,
                'atr': 0,
                'vwap': 0,
                'volume_ratio': round(volume_ratio, 2),
                'mode': mode,
                'pattern': 'strategy',
                'indicators_json': json.dumps(entry_details),
                'status': 'ACTIVE',
                'created_at': datetime.now().isoformat()
            }
            
            signals.append(signal)
            
        except Exception as e:
            print(f"[Strategy Engine] Error scanning {coin}: {e}")
            continue
    
    return signals


def scan_all_active_strategies(market_data=None):
    """
    Load all strategies with is_active=1 from database.
    Run scan_with_strategy for each.
    Return combined signals sorted by confidence.
    """
    from services.database import get_db
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM strategies WHERE is_active = 1")
    rows = cursor.fetchall()
    conn.close()
    
    all_signals = []
    
    for row in rows:
        strategy = {
            'id': row['id'],
            'name': row['name'],
            'coins': row['coins'],
            'mode': row['mode'],
            'timeframe': row['timeframe'],
            'entry_conditions': row['entry_conditions'],
            'exit_conditions': row['exit_conditions'],
            'entry_logic': row['entry_logic'],
            'exit_logic': row['exit_logic'],
            'sl_pct': row['sl_pct'],
            'tp_pct': row['tp_pct'],
            'min_confidence': row['min_confidence'],
            'min_rr': row['min_rr'],
            'exchange': row['exchange']
        }
        
        signals = scan_with_strategy(strategy, market_data)
        all_signals.extend(signals)
    
    # Sort by confidence
    all_signals.sort(key=lambda x: x['confidence'], reverse=True)
    
    return all_signals