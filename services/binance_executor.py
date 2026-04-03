"""
Binance Executor — Semi-auto execution service.
Places orders on Binance (testnet or live) based on signals/positions.
"""
import requests
import json
import os
from datetime import datetime

BINANCE_SPOT_API = "https://api.binance.com"
BINANCE_TESTNET_API = "https://testnet.binance.vision"
BINANCE_FUTURES_API = "https://testnet.binancefuture.com"  # testnet


def get_client():
    """Create BinanceClient from bot_config.json"""
    from services.binance_client import BinanceClient
    return BinanceClient.from_config()


def get_execution_mode():
    """Return execution mode from config: 'signal_only' | 'semi_auto' | 'full_auto'"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'bot_config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config.get('execution_mode', 'signal_only')
    except:
        return 'signal_only'


def can_execute():
    """Check if execution is allowed (semi_auto or full_auto mode)"""
    mode = get_execution_mode()
    return mode in ('semi_auto', 'full_auto')


def execute_signal(signal, config=None):
    """
    Execute a trading signal on Binance.
    
    Flow:
    1. Check execution mode
    2. Check risk (circuit breaker, max positions)
    3. Calculate position size from config
    4. Place MARKET order (or LIMIT if specified)
    5. Record order_id in position
    
    Args:
        signal: dict with symbol, side, sl_pct, tp_pct, entry_price (optional)
        config: optional config dict (uses bot_config.json if not provided)
    
    Returns: dict with success, order_id, or error
    """
    if config is None:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'bot_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    mode = get_execution_mode()
    if mode == 'signal_only':
        return {'success': False, 'error': 'Execution mode is signal_only — orders not enabled'}
    
    if mode not in ('semi_auto', 'full_auto'):
        return {'success': False, 'error': f'Unknown execution mode: {mode}'}
    
    # Check risk
    from services.risk_manager import can_open_position
    
    symbol = signal.get('symbol', '').replace('/', '')  # BTC/USDT -> BTCUSDT
    side = signal.get('side', '').upper()
    entry_price = signal.get('entry_price')
    sl_pct = signal.get('sl_pct', 2.5)
    tp_pct = signal.get('tp_pct', 7.5)
    
    if not entry_price:
        # Fetch current price
        try:
            resp = requests.get(
                f"{BINANCE_SPOT_API}/api/v3/ticker/price",
                params={'symbol': symbol.upper()},
                timeout=8
            )
            entry_price = float(resp.json()['price'])
        except Exception as e:
            return {'success': False, 'error': f'Failed to get price: {e}'}
    
    # Get account balance
    client = get_client()
    try:
        balance = client.get_balance('USDT')
        account_balance = balance.get('total', 0)
    except Exception as e:
        return {'success': False, 'error': f'Failed to get account balance: {e}'}
    
    if account_balance <= 0:
        return {'success': False, 'error': 'No USDT balance available'}
    
    # Calculate position size
    risk_pct = config.get('max_risk_per_trade', 2.0)
    stop_loss_pct = sl_pct
    
    position_info = client.calculate_position_size(
        symbol=symbol,
        account_balance=account_balance,
        risk_pct=risk_pct,
        stop_loss_pct=stop_loss_pct
    )
    
    quantity = position_info['quantity']
    
    if quantity <= 0:
        return {'success': False, 'error': f'Quantity too small: {quantity}'}
    
    # Risk pre-check
    allowed, reason = can_open_position(symbol, entry_price, quantity)
    if not allowed:
        return {'success': False, 'error': f'Risk check failed: {reason}'}
    
    # Place order
    try:
        if side == 'BUY':
            order_result = client.place_market_buy(symbol, quantity)
        else:
            order_result = client.place_market_sell(symbol, quantity)
        
        order_id = order_result.get('orderId')
        executed_price = None
        for fill in order_result.get('fills', []):
            executed_price = float(fill['price'])
            break
        
        return {
            'success': True,
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'entry_price': executed_price or entry_price,
            'mode': mode,
            'executed_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Order placement failed: {e}'}


def execute_from_position(position_id):
    """
    Execute a trade based on an existing position in the DB.
    Gets position details, calculates quantity from balance,
    then places the order on Binance.
    """
    from services.database import get_db
    from services.position_manager import open_position
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM positions WHERE id = ?", (position_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {'success': False, 'error': 'Position not found'}
    
    if row['status'] != 'OPEN':
        return {'success': False, 'error': f'Position is not open (status={row["status"]})'}
    
    # Build signal dict
    signal = {
        'symbol': row['symbol'].replace('/', ''),  # Ensure no slash
        'side': row['side'],
        'entry_price': row['entry_price'],
        'sl_pct': row['sl_pct'],
        'tp_pct': row['tp_pct'],
        'signal_id': row['signal_id'],
        'strategy_id': row['strategy_id']
    }
    
    return execute_signal(signal)


def cancel_order(symbol, order_id):
    """Cancel an open order on Binance"""
    client = get_client()
    try:
        result = client.cancel_order(symbol.upper(), order_id)
        return {'success': True, 'result': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_order_status(symbol, order_id):
    """Get order status from Binance"""
    client = get_client()
    try:
        result = client.get_order(symbol.upper(), order_id)
        return {
            'success': True,
            'order_id': result.get('orderId'),
            'symbol': result.get('symbol'),
            'side': result.get('side'),
            'type': result.get('type'),
            'price': result.get('price'),
            'orig_qty': result.get('origQty'),
            'executed_qty': result.get('executedQty'),
            'status': result.get('status'),
            'create_time': result.get('time'),
            'update_time': result.get('updateTime')
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_futures_balance():
    """Get USDT futures balance from testnet or live"""
    client = get_client()
    try:
        # For futures, use fapi endpoint
        base_url = BINANCE_FUTURES_API if 'testnet' in str(client.base_url) else 'https://fapi.binance.com'
        headers = {'X-MBX-APIKEY': client.api_key}
        
        resp = requests.get(
            f"{base_url}/fapi/v2/balance",
            headers=headers,
            params={'timestamp': int(datetime.now().timestamp() * 1000),
                    'signature': client._sign({'timestamp': int(datetime.now().timestamp() * 1000)})},
            timeout=10
        )
        resp.raise_for_status()
        balances = resp.json()
        for b in balances:
            if b['asset'] == 'USDT':
                return {
                    'asset': 'USDT',
                    'total': float(b['balance']),
                    'available': float(b['availableBalance'])
                }
        return {'asset': 'USDT', 'total': 0, 'available': 0}
    except Exception as e:
        return {'success': False, 'error': str(e)}