"""
Binance API Client
Handles authenticated requests to Binance API
"""
import requests
import hashlib
import hmac
import time
from urllib.parse import urlencode

BINANCE_BASE = "https://api.binance.com"
BINANCE_API_VERSION = "v3"


class BinanceClient:
    """Simple Binance API client for authenticated requests"""
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = False):
        self.api_key = api_key
        self.secret_key = secret_key
        if testnet:
            self.base_url = "https://testnet.binance.vision"
        else:
            self.base_url = BINANCE_BASE
    
    def _sign(self, params: dict) -> str:
        """Generate signature for authenticated requests"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(self, method: str, endpoint: str, signed: bool = False, **params):
        """Make request to Binance API"""
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._sign(params)
        
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == 'POST':
            response = requests.post(url, headers=headers, params=params, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, params=params, timeout=10)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        if response.status_code != 200:
            error_msg = response.json().get('msg', response.text)
            raise Exception(f"Binance API error ({response.status_code}): {error_msg}")
        
        return response.json()
    
    # ========== ACCOUNT METHODS ==========
    
    def get_account(self):
        """Get account information"""
        return self._request('GET', '/api/v3/account', signed=True)
    
    def get_balance(self, asset: str):
        """Get balance for specific asset"""
        account = self.get_account()
        for balance in account.get('balances', []):
            if balance['asset'] == asset:
                return {
                    'asset': asset,
                    'free': float(balance['free']),
                    'locked': float(balance['locked']),
                    'total': float(balance['free']) + float(balance['locked'])
                }
        return {'asset': asset, 'free': 0, 'locked': 0, 'total': 0}
    
    # ========== ORDER METHODS ==========
    
    def place_market_buy(self, symbol: str, quantity: float):
        """Place a market buy order"""
        params = {
            'symbol': symbol.upper(),
            'side': 'BUY',
            'type': 'MARKET',
            'quantity': quantity
        }
        return self._request('POST', '/api/v3/order', signed=True, **params)
    
    def place_market_sell(self, symbol: str, quantity: float):
        """Place a market sell order"""
        params = {
            'symbol': symbol.upper(),
            'side': 'SELL',
            'type': 'MARKET',
            'quantity': quantity
        }
        return self._request('POST', '/api/v3/order', signed=True, **params)
    
    def place_limit_buy(self, symbol: str, quantity: float, price: float):
        """Place a limit buy order"""
        params = {
            'symbol': symbol.upper(),
            'side': 'BUY',
            'type': 'LIMIT',
            'quantity': quantity,
            'price': price,
            'timeInForce': 'GTC'
        }
        return self._request('POST', '/api/v3/order', signed=True, **params)
    
    def place_limit_sell(self, symbol: str, quantity: float, price: float):
        """Place a limit sell order"""
        params = {
            'symbol': symbol.upper(),
            'side': 'SELL',
            'type': 'LIMIT',
            'quantity': quantity,
            'price': price,
            'timeInForce': 'GTC'
        }
        return self._request('POST', '/api/v3/order', signed=True, **params)
    
    def place_stop_loss(self, symbol: str, quantity: float, stop_price: float):
        """Place a stop loss order (SELL)"""
        params = {
            'symbol': symbol.upper(),
            'side': 'SELL',
            'type': 'STOP_LOSS',
            'quantity': quantity,
            'stopPrice': stop_price
        }
        return self._request('POST', '/api/v3/order', signed=True, **params)
    
    def place_take_profit(self, symbol: str, quantity: float, take_profit_price: float):
        """Place a take profit order (SELL"""
        params = {
            'symbol': symbol.upper(),
            'side': 'SELL',
            'type': 'TAKE_PROFIT',
            'quantity': quantity,
            'stopPrice': take_profit_price
        }
        return self._request('POST', '/api/v3/order', signed=True, **params)
    
    def get_open_orders(self, symbol: str = None):
        """Get all open orders or for specific symbol"""
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        return self._request('GET', '/api/v3/openOrders', signed=True, **params)
    
    def cancel_order(self, symbol: str, order_id: int):
        """Cancel an order"""
        params = {
            'symbol': symbol.upper(),
            'orderId': order_id
        }
        return self._request('DELETE', '/api/v3/order', signed=True, **params)
    
    def get_order(self, symbol: str, order_id: int):
        """Get specific order status"""
        params = {
            'symbol': symbol.upper(),
            'orderId': order_id
        }
        return self._request('GET', '/api/v3/order', signed=True, **params)
    
    # ========== POSITION SIZE CALCULATOR ==========
    
    def calculate_position_size(self, symbol: str, account_balance: float, risk_pct: float, stop_loss_pct: float):
        """
        Calculate position size based on risk management
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            account_balance: Total account balance in USDT
            risk_pct: Risk percentage per trade (e.g., 2 for 2%)
            stop_loss_pct: Stop loss percentage (e.g., 2.5 for 2.5%)
        
        Returns:
            dict with quantity and risk details
        """
        # Get current price
        ticker = requests.get(
            f"{self.base_url}/api/v3/ticker/price",
            params={'symbol': symbol.upper()},
            timeout=10
        ).json()
        
        current_price = float(ticker['price'])
        
        # Calculate position size
        risk_amount = account_balance * (risk_pct / 100)
        stop_loss_distance = current_price * (stop_loss_pct / 100)
        quantity = risk_amount / stop_loss_distance
        
        # Round to appropriate precision
        symbol_info = requests.get(
            f"{self.base_url}/api/v3/exchangeInfo",
            timeout=10
        ).json()
        
        for s in symbol_info.get('symbols', []):
            if s['symbol'] == symbol.upper():
                for f in s['filters']:
                    if f['filterType'] == 'LOT_SIZE':
                        step_size = float(f['stepSize'])
                        min_qty = float(f['minQty'])
                        
                        # Adjust quantity to step size
                        quantity = round(quantity - (quantity % step_size))
                        quantity = max(quantity, min_qty)
                        break
                break
        
        return {
            'symbol': symbol,
            'entry_price': current_price,
            'quantity': quantity,
            'position_value': quantity * current_price,
            'risk_amount': risk_amount,
            'risk_pct': risk_pct,
            'stop_loss_pct': stop_loss_pct
        }
    
    # ========== TEST CONNECTION ==========
    
    @staticmethod
    def from_config():
        """Create client from bot_config.json, auto-detect testnet"""
        import json, os
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'bot_config.json')
        with open(config_path) as f:
            config = json.load(f)
        
        use_testnet = config.get('use_testnet', True)
        if use_testnet:
            api_key = config.get('testnet_api_key', '')
            secret_key = config.get('testnet_secret_key', '')
        else:
            api_key = config.get('binance_api_key', '')
            secret_key = config.get('binance_secret_key', '')
        
        return BinanceClient(api_key, secret_key, testnet=use_testnet)
    
    @staticmethod
    def test_connection(api_key: str, secret_key: str) -> dict:
        """Test if credentials work"""
        try:
            client = BinanceClient(api_key, secret_key)
            account = client.get_account()
            return {
                'success': True,
                'account_type': 'SPOT' if not account.get('marginUsed') else 'MARGIN',
                'maker_commission': account.get('makerCommission'),
                'taker_commission': account.get('takerCommission')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
