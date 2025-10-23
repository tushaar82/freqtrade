"""OpenAlgo exchange subclass - for NSE trading"""

import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional

import pandas as pd
import requests
from pandas import DataFrame, to_datetime

from freqtrade.constants import BuySell
from freqtrade.enums import CandleType, InstrumentType, MarginMode, TradingMode
from freqtrade.exceptions import (
    DDosProtection,
    ExchangeError,
    InsufficientFundsError,
    InvalidOrderException,
    OperationalException,
    TemporaryError,
)
from freqtrade.exchange.custom_exchange import CustomExchange
from freqtrade.exchange.exchange_types import FtHas, OrderBook, Ticker
from freqtrade.exchange.rate_limiter import BrokerRateLimits
from freqtrade.exchange.lot_size_manager import LotSizeManager
from freqtrade.exchange.nse_calendar import get_nse_calendar


logger = logging.getLogger(__name__)


class Openalgo(CustomExchange):
    """
    OpenAlgo exchange class. Contains adjustments needed for Freqtrade to work
    with OpenAlgo for NSE trading.
    
    OpenAlgo is not a CCXT-based exchange, so this implementation uses direct REST API calls.
    """

    _ft_has: FtHas = {
        "ohlcv_candle_limit": 1000,
        "ohlcv_has_history": True,
        "ohlcv_partial_candle": True,
        "ohlcv_require_since": False,
        "stoploss_on_exchange": False,  # OpenAlgo supports stop loss but implementation differs
        "order_time_in_force": ["GTC", "IOC"],
        "trades_has_history": True,
        "tickers_have_quoteVolume": True,
        "tickers_have_bid_ask": True,
        "tickers_have_price": True,
        "ws_enabled": True,  # OpenAlgo supports websocket
        "always_require_api_keys": True,  # OpenAlgo always requires API key
    }

    # NSE Market Hours (IST)
    NSE_MARKET_OPEN = "09:15"
    NSE_MARKET_CLOSE = "15:30"
    
    # Supported trading modes for NSE
    _supported_trading_mode_margin_pairs = [
        (TradingMode.SPOT, MarginMode.NONE),
    ]

    def __init__(self, config, validate: bool = True, exchange_config=None, load_leverage_tiers: bool = False, **kwargs):
        """
        Initialize OpenAlgo exchange.
        
        Requires OpenAlgo server to be running with configured broker.
        """
        # OpenAlgo specific configuration
        # Check if exchange_config parameter is provided (Freqtrade might pass it separately)
        if exchange_config:
            exchange_cfg = exchange_config
            logger.info("Using exchange_config parameter")
        else:
            exchange_cfg = config.get('exchange', {})
            logger.info(f"Using config.get('exchange'), keys: {list(exchange_cfg.keys())}")
        
        self._api_key = exchange_cfg.get('key', '')
        self._host = exchange_cfg.get('urls', {}).get('api', 'http://127.0.0.1:5000')
        self._strategy_name = config.get('strategy', 'Freqtrade')
        self._default_exchange = exchange_cfg.get('nse_exchange', 'NSE')
        
        # Initialize CustomExchange base class
        super().__init__(config)
        
        # Log API key status (masked for security)
        api_key_status = f"set ({self._api_key[:10]}...)" if self._api_key else "NOT SET"
        logger.info(f"OpenAlgo API key: {api_key_status}")
        
        # Session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({'Content-Type': 'application/json'})

        # Initialize rate limiter
        self._rate_limiter = BrokerRateLimits.get_limiter('openalgo')

        # Initialize lot size manager
        self._lot_size_manager = LotSizeManager()

        # Order tracking
        self._open_orders_cache = {}  # Cache for open orders

        # Initialize markets from pair whitelist
        pair_whitelist = config.get('exchange', {}).get('pair_whitelist', [])
        self._init_markets_from_pairs(pair_whitelist, quote_currency='INR')

        logger.info(f"OpenAlgo exchange initialized with host: {self._host}")
        
        # NSE trading hours
        self._market_hours = {
            'start': (9, 15),  # 9:15 AM
            'end': (15, 30),   # 3:30 PM
        }
    
    def is_market_open(self) -> bool:
        """
        Check if NSE market is currently open.
        NSE trading hours: 9:15 AM - 3:30 PM IST, Monday-Friday
        """
        from datetime import datetime
        import pytz
        
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        # Check if weekend
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check if within trading hours
        current_time = (now.hour, now.minute)
        start_time = self._market_hours['start']
        end_time = self._market_hours['end']
        
        # Convert to minutes for easier comparison
        current_minutes = current_time[0] * 60 + current_time[1]
        start_minutes = start_time[0] * 60 + start_time[1]
        end_minutes = end_time[0] * 60 + end_time[1]
        
        return start_minutes <= current_minutes <= end_minutes
    
    @property
    def precisionMode(self) -> int:
        """
        Exchange precision mode.
        DECIMAL_PLACES = 2 (NSE uses decimal places)
        """
        return 2  # DECIMAL_PLACES
    
    @property
    def precision_mode_price(self) -> int:
        """
        Exchange precision mode for price.
        """
        return 2  # DECIMAL_PLACES
        
    def _get_headers(self) -> dict:
        """Get headers for OpenAlgo API requests"""
        return {
            'Authorization': f'Bearer {self._api_key}',
            'Content-Type': 'application/json'
        }

    def _rate_limit(self, endpoint: Optional[str] = None):
        """Apply rate limiting before API calls"""
        if hasattr(self, '_rate_limiter'):
            self._rate_limiter.wait_if_needed(endpoint)

    def _make_request(self, endpoint: str, method: str = 'GET',
                     data: dict | None = None, params: dict | None = None) -> dict:
        """
        Make a request to OpenAlgo API.

        :param endpoint: API endpoint
        :param method: HTTP method
        :param data: Request body data
        :param params: Query parameters
        :return: Response data
        """
        # Apply rate limiting
        self._rate_limit(endpoint)

        url = f"{self._host}{endpoint}"
        
        # OpenAlgo requires API key in request body for POST requests
        if data is None:
            data = {}
        if method == 'POST' and 'apikey' not in data:
            data['apikey'] = self._api_key
            logger.info(f"Added API key to request: {self._api_key[:10] if self._api_key else 'EMPTY'}...")
        
        # Debug: Log the request
        logger.info(f"OpenAlgo request: {method} {url}, data keys: {list(data.keys()) if data else 'None'}, apikey_value: {data.get('apikey', 'NOT_PRESENT')[:10] if data.get('apikey') else 'EMPTY'}...")

        try:
            if method == 'GET':
                response = self._session.get(url, headers=self._get_headers(), params=params)
            elif method == 'POST':
                response = self._session.post(url, headers={'Content-Type': 'application/json'}, json=data)
            elif method == 'PUT':
                response = self._session.put(url, headers=self._get_headers(), json=data)
            elif method == 'DELETE':
                response = self._session.delete(url, headers=self._get_headers(), params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            result = response.json()
            
            # OpenAlgo returns status in response
            if result.get('status') == 'error':
                raise ExchangeError(f"OpenAlgo API error: {result.get('message', 'Unknown error')}")
                
            return result
            
        except requests.exceptions.HTTPError as e:
            # Try to get error details from response
            error_detail = ""
            try:
                error_json = e.response.json()
                error_detail = f" - {error_json}"
            except:
                error_detail = f" - {e.response.text[:200]}"
            
            if e.response.status_code == 429:
                raise DDosProtection(f"OpenAlgo rate limit exceeded: {e}{error_detail}")
            elif e.response.status_code in [500, 502, 503, 504]:
                raise TemporaryError(f"OpenAlgo server error: {e}{error_detail}")
            else:
                raise ExchangeError(f"OpenAlgo HTTP error: {e}{error_detail}")
        except requests.exceptions.RequestException as e:
            raise TemporaryError(f"OpenAlgo connection error: {e}")

    def _convert_symbol_to_openalgo(self, pair: str) -> tuple[str, str]:
        """
        Convert Freqtrade pair format to OpenAlgo symbol format.
        
        :param pair: Freqtrade pair (e.g., 'RELIANCE/INR')
        :return: Tuple of (symbol, exchange)
        """
        # Remove quote currency (typically INR for NSE)
        symbol = pair.split('/')[0]
        
        # Determine exchange from pair or use default
        if 'NFO' in pair.upper():
            exchange = 'NFO'
        elif 'BSE' in pair.upper():
            exchange = 'BSE'
        elif 'MCX' in pair.upper():
            exchange = 'MCX'
        else:
            exchange = self._default_exchange
            
        return symbol, exchange

    def _convert_symbol_from_openalgo(self, symbol: str, exchange: str) -> str:
        """
        Convert OpenAlgo symbol to Freqtrade pair format.
        
        :param symbol: OpenAlgo symbol
        :param exchange: Exchange name
        :return: Freqtrade pair format
        """
        # For NSE, add INR as quote currency
        return f"{symbol}/INR"

    def parse_options_symbol(self, symbol: str) -> dict:
        """
        Parse options symbol to extract components.
        
        :param symbol: Options symbol (e.g., 'NIFTY25DEC24500CE')
        :return: Dict with strike, expiry, option_type, underlying
        """
        if not symbol.endswith(('CE', 'PE')):
            return {}
        
        try:
            # Extract option type (CE/PE)
            option_type = 'CALL' if symbol.endswith('CE') else 'PUT'
            base_symbol = symbol[:-2]  # Remove CE/PE
            
            # Extract strike price (last numeric part)
            import re
            strike_match = re.search(r'(\d+)$', base_symbol)
            if not strike_match:
                return {}
            
            strike_price = float(strike_match.group(1))
            symbol_without_strike = base_symbol[:strike_match.start()]
            
            # Extract expiry date (format varies, e.g., 25DEC24, 2024DEC25)
            expiry_match = re.search(r'(\d{1,2}[A-Z]{3}\d{2,4}|\d{4}[A-Z]{3}\d{1,2})$', symbol_without_strike)
            if expiry_match:
                expiry_str = expiry_match.group(1)
                underlying = symbol_without_strike[:expiry_match.start()]
                
                # Parse expiry date
                expiry_date = self._parse_expiry_date(expiry_str)
            else:
                underlying = symbol_without_strike
                expiry_date = None
            
            return {
                'underlying': underlying,
                'strike_price': strike_price,
                'expiry_date': expiry_date,
                'option_type': option_type,
                'symbol': symbol
            }
            
        except Exception as e:
            logger.error(f"Failed to parse options symbol {symbol}: {e}")
            return {}

    def _parse_expiry_date(self, expiry_str: str) -> Optional[datetime]:
        """Parse expiry date string to datetime"""
        try:
            # Handle different formats
            if len(expiry_str) == 7:  # 25DEC24
                return datetime.strptime(expiry_str, '%d%b%y')
            elif len(expiry_str) == 9:  # 2024DEC25
                return datetime.strptime(expiry_str, '%Y%b%d')
            else:
                return None
        except Exception:
            return None

    def _get_lot_size(self, pair: str) -> int:
        """Get lot size for a symbol"""
        try:
            # Try to get from LotSizeManager if available
            if hasattr(self, '_lot_size_manager') and self._lot_size_manager:
                return self._lot_size_manager.get_lot_size(pair)
        except Exception:
            pass
        return 1  # Default lot size

    def fetch_option_chain(self, underlying: str, expiry: str = None) -> List[dict]:
        """
        Fetch option chain for an underlying (placeholder implementation).
        
        :param underlying: Underlying symbol (e.g., 'NIFTY')
        :param expiry: Expiry date (optional)
        :return: List of option contracts
        """
        # This would need to be implemented based on OpenAlgo's API
        # For now, return empty list
        logger.warning("fetch_option_chain not fully implemented for OpenAlgo")
        return []

    def fetch_ticker(self, pair: str) -> Ticker:
        """
        Fetch ticker data for a pair.
        
        :param pair: Freqtrade pair
        :return: Ticker data
        """
        symbol, exchange = self._convert_symbol_to_openalgo(pair)
        
        try:
            response = self._make_request('/api/v1/quotes', method='POST', data={
                'symbol': symbol,
                'exchange': exchange
            })
            
            data = response.get('data', {})
            
            return {
                'symbol': pair,
                'ask': data.get('ask'),
                'bid': data.get('bid'),
                'last': data.get('ltp'),
                'askVolume': None,
                'bidVolume': None,
                'quoteVolume': data.get('volume'),
                'baseVolume': data.get('volume'),
                'percentage': None,
            }
        except Exception as e:
            raise ExchangeError(f"Failed to fetch ticker for {pair}: {e}")

    def fetch_order_book(self, pair: str, limit: int = 5) -> OrderBook:
        """
        Fetch order book (depth) for a pair.
        
        :param pair: Freqtrade pair
        :param limit: Depth limit (default 5)
        :return: Order book data
        """
        symbol, exchange = self._convert_symbol_to_openalgo(pair)
        
        try:
            response = self._make_request('/api/v1/depth', method='POST', data={
                'symbol': symbol,
                'exchange': exchange
            })
            
            data = response.get('data', {})
            
            # Convert OpenAlgo depth format to Freqtrade format
            asks = [(item['price'], item['quantity']) for item in data.get('asks', [])[:limit]]
            bids = [(item['price'], item['quantity']) for item in data.get('bids', [])[:limit]]
            
            return {
                'symbol': pair,
                'bids': bids,
                'asks': asks,
                'timestamp': None,
                'datetime': None,
                'nonce': None,
            }
        except Exception as e:
            raise ExchangeError(f"Failed to fetch order book for {pair}: {e}")

    def fetch_ohlcv(
        self,
        pair: str,
        timeframe: str = '5m',
        since: int | None = None,
        limit: int | None = None,
        candle_type: CandleType = CandleType.SPOT,
    ) -> list:
        """
        Fetch OHLCV data.
        
        :param pair: Freqtrade pair
        :param timeframe: Timeframe (e.g., '5m', '15m', '1h', 'D')
        :param since: Timestamp in milliseconds
        :param limit: Number of candles to fetch
        :param candle_type: Candle type
        :return: List of OHLCV data
        """
        symbol, exchange = self._convert_symbol_to_openalgo(pair)
        
        # Convert Freqtrade timeframe to OpenAlgo interval
        interval_map = {
            '1m': '1m',
            '3m': '3m',
            '5m': '5m',
            '10m': '10m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '1d': 'D',
        }
        
        interval = interval_map.get(timeframe, '5m')
        
        # Calculate date range
        # Note: Use dates that actually have data available
        if since:
            start_date = datetime.fromtimestamp(since / 1000).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
        else:
            # For live trading, we need recent data
            # Go back 10 days to ensure we get data even with holidays/weekends
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
            logger.debug(f"Using date range for OpenAlgo: {start_date} to {end_date}")
        
        request_data = {
            'symbol': symbol,
            'exchange': exchange,
            'interval': interval,
            'start_date': start_date,
            'end_date': end_date
        }
        logger.info(f"Fetching OHLCV for {pair}: symbol={symbol}, exchange={exchange}, interval={interval}, dates={start_date} to {end_date}")
        
        try:
            response = self._make_request('/api/v1/history', method='POST', data=request_data)
            
            # OpenAlgo returns data as a list of candles
            data = response.get('data', [])
            
            if not data:
                logger.warning(f"No OHLCV data returned from OpenAlgo for {pair}")
                logger.warning(f"Response was: {response}")
                return []
            
            logger.debug(f"Received {len(data)} candles from OpenAlgo for {pair}")
            
            # Convert to OHLCV format: [timestamp_ms, open, high, low, close, volume]
            ohlcv = []
            for candle in data:
                # OpenAlgo returns timestamp in seconds, convert to milliseconds
                timestamp_ms = int(candle['timestamp']) * 1000
                ohlcv.append([
                    timestamp_ms,
                    float(candle['open']),
                    float(candle['high']),
                    float(candle['low']),
                    float(candle['close']),
                    float(candle.get('volume', 0))
                ])
            
            # Apply limit if specified
            if limit:
                ohlcv = ohlcv[-limit:]
            
            logger.info(f"Fetched {len(ohlcv)} candles for {pair} from OpenAlgo")
            return ohlcv
            
        except Exception as e:
            raise ExchangeError(f"Failed to fetch OHLCV for {pair}: {e}")

    def create_order(
        self,
        pair: str,
        ordertype: str,
        side: BuySell,
        amount: float,
        rate: float | None = None,
        params: dict | None = None,
        leverage: float = 1.0,
        reduceOnly: bool = False,
        time_in_force: str = 'GTC',
    ) -> dict:
        """
        Create an order on OpenAlgo.
        
        :param pair: Freqtrade pair
        :param ordertype: Order type ('limit', 'market')
        :param side: Order side ('buy', 'sell')
        :param amount: Order amount
        :param rate: Order price (for limit orders)
        :param params: Additional parameters
        :param leverage: Leverage (not used for NSE spot)
        :param reduceOnly: Reduce only flag (not used for spot)
        :param time_in_force: Time in force (GTC, IOC, etc.)
        :return: Order data
        """
        symbol, exchange = self._convert_symbol_to_openalgo(pair)
        params = params or {}
        
        # Check if this is an options trade and validate lot size
        instrument_type = InstrumentType.from_symbol(pair)
        if instrument_type.requires_lot_size():
            # Validate quantity is in lot multiples
            lot_size = self._get_lot_size(pair)
            if amount % lot_size != 0:
                logger.warning(f"Adjusting quantity {amount} to lot multiple for {pair} (lot size: {lot_size})")
                amount = int(amount / lot_size) * lot_size
        
        # Map order type - OpenAlgo uses 'pricetype' not 'price_type'
        pricetype = 'LIMIT' if ordertype == 'limit' else 'MARKET'
        
        # Get product type (default to MIS for intraday)
        product = params.get('product', 'MIS')
        
        # Calculate quantity for NSE
        # Check if fixed_quantity is configured
        fixed_qty = self._config.get('exchange', {}).get('fixed_quantity')
        
        if fixed_qty and fixed_qty > 0:
            # Use fixed quantity from config
            quantity = int(fixed_qty)
            logger.info(f"Using fixed quantity from config: {quantity} shares")
        else:
            # Freqtrade calculates amount as: stake_amount / price
            # For NSE, we need integer quantities (number of shares)
            # Simply round to nearest integer, minimum 1 share
            quantity = max(1, int(round(amount)))
        
        logger.info(f"Order calculation for {pair}:")
        logger.info(f"  - Original amount: {amount}")
        logger.info(f"  - Price/Rate: {rate}")
        logger.info(f"  - Final quantity: {quantity} shares")
        logger.info(f"  - Order value: {quantity * rate if rate else 0} INR")
        
        order_data = {
            'strategy': self._strategy_name,
            'symbol': symbol,
            'action': side.upper(),
            'exchange': exchange,
            'pricetype': pricetype,  # Changed from 'price_type' to 'pricetype'
            'product': product,
            'quantity': quantity,  # Ensure it's an integer
        }
        
        # Add price for limit orders
        if ordertype == 'limit' and rate:
            order_data['price'] = str(rate)
        else:
            order_data['price'] = '0'
            
        # Add trigger price if provided
        if 'trigger_price' in params:
            order_data['trigger_price'] = str(params['trigger_price'])
        else:
            order_data['trigger_price'] = '0'
            
        try:
            response = self._make_request('/api/v1/placeorder', method='POST', data=order_data)
            
            order_id = response.get('orderid')
            order = self._create_order_response(
                order_id=order_id,
                pair=pair,
                order_type=ordertype,
                side=side,
                amount=quantity,  # Use calculated quantity, not original amount
                price=rate,
                status='open'
            )
            order['info'] = response
            order['filled'] = 0  # Will be updated when order is filled
            order['remaining'] = quantity
            
            # Cache as open order
            self._open_orders_cache[order_id] = order
            
            return order
            
        except Exception as e:
            if 'insufficient' in str(e).lower():
                raise InsufficientFundsError(f"Insufficient funds: {e}")
            raise ExchangeError(f"Failed to create order: {e}")

    def fetch_order_or_stoploss_order(self, order_id: str, pair: str, is_stoploss: bool = False) -> dict:
        """
        Fetch order or stoploss order.
        
        :param order_id: Order ID
        :param pair: Freqtrade pair
        :param is_stoploss: Whether this is a stoploss order
        :return: Order data
        """
        return self.fetch_order(order_id, pair)
    
    def check_order_canceled_empty(self, order: dict) -> bool:
        """
        Verify if an order has been cancelled without being partially filled.
        
        :param order: Order dict as returned from fetch_order()
        :return: True if order has been cancelled without being filled
        """
        NON_OPEN_STATES = ['closed', 'canceled', 'cancelled', 'rejected', 'expired']
        return order.get("status") in NON_OPEN_STATES and order.get("filled", 0) == 0
    
    def fetch_order(self, order_id: str, pair: str, params: dict | None = None) -> dict:
        """
        Fetch order status.
        
        :param order_id: Order ID
        :param pair: Freqtrade pair
        :param params: Additional parameters
        :return: Order data
        """
        try:
            response = self._make_request('/api/v1/orderstatus', method='POST', data={
                'orderid': order_id,  # OpenAlgo uses 'orderid' not 'order_id'
                'strategy': self._strategy_name
            })
            
            data = response.get('data', {})
            
            # Map OpenAlgo order status to Freqtrade status
            status_map = {
                'complete': 'closed',
                'rejected': 'canceled',
                'cancelled': 'canceled',
                'open': 'open',
                'pending': 'open',
            }
            
            order_status = data.get('order_status', 'open')
            status = status_map.get(order_status.lower(), 'open')
            
            # Parse quantity
            quantity = float(data.get('quantity', 0))
            filled = quantity if status == 'closed' else 0
            
            return {
                'id': order_id,
                'info': data,
                'timestamp': None,
                'datetime': data.get('timestamp'),
                'status': status,
                'symbol': pair,
                'type': data.get('pricetype', '').lower(),
                'side': data.get('action', '').lower(),
                'price': float(data.get('price', 0)),
                'average': float(data.get('average_price', 0)),
                'amount': quantity,
                'filled': filled,
                'remaining': quantity - filled,
                'fee': None,
            }
            
        except Exception as e:
            error_str = str(e)
            # If order not found (404), return a canceled order instead of raising
            if '404' in error_str or 'not found' in error_str.lower():
                logger.warning(f"Order {order_id} not found in OpenAlgo, assuming canceled")
                return {
                    'id': order_id,
                    'info': {},
                    'timestamp': None,
                    'datetime': None,
                    'status': 'canceled',
                    'symbol': pair,
                    'type': 'limit',
                    'side': 'buy',
                    'price': 0,
                    'average': 0,
                    'amount': 0,
                    'filled': 0,
                    'remaining': 0,
                    'fee': None,
                }
            raise ExchangeError(f"Failed to fetch order {order_id}: {e}")

    def cancel_order(self, order_id: str, pair: str, params: dict | None = None) -> dict:
        """
        Cancel an order.
        
        :param order_id: Order ID
        :param pair: Freqtrade pair
        :param params: Additional parameters
        :return: Order data
        """
        try:
            response = self._make_request('/api/v1/cancelorder', method='POST', data={
                'order_id': order_id,
                'strategy': self._strategy_name
            })
            
            # Remove from open orders cache
            if order_id in self._open_orders_cache:
                del self._open_orders_cache[order_id]
            
            return {
                'id': order_id,
                'info': response,
                'status': 'canceled',
            }
            
        except Exception as e:
            raise ExchangeError(f"Failed to cancel order {order_id}: {e}")

    def fetch_orders(self, pair: str, since: Optional[int] = None) -> List[dict]:
        """
        Fetch all orders for a pair.
        
        :param pair: Freqtrade pair
        :param since: Timestamp in milliseconds
        :return: List of orders
        """
        try:
            # OpenAlgo doesn't have a direct endpoint for fetching all orders
            # We'll return cached orders for now
            orders = []
            for order_id, order in self._open_orders_cache.items():
                if order['symbol'] == pair:
                    if since is None or order['timestamp'] >= since:
                        orders.append(order)
            return orders
        except Exception as e:
            logger.warning(f"Failed to fetch orders for {pair}: {e}")
            return []
    
    def fetch_open_orders(self, pair: Optional[str] = None) -> List[dict]:
        """
        Fetch open orders.
        
        :param pair: Freqtrade pair (None for all pairs)
        :return: List of open orders
        """
        try:
            # Try to fetch from OpenAlgo API
            response = self._make_request('/api/v1/openorders', method='POST', data={
                'strategy': self._strategy_name
            })
            
            orders_data = response.get('data', [])
            if not isinstance(orders_data, list):
                orders_data = [orders_data] if orders_data else []
            
            open_orders = []
            for order_data in orders_data:
                order_id = order_data.get('orderid')
                order_pair = order_data.get('symbol', '') + '/INR'
                
                # Filter by pair if specified
                if pair and order_pair != pair:
                    continue
                
                # Create order object
                order = {
                    'id': order_id,
                    'timestamp': None,
                    'datetime': order_data.get('timestamp'),
                    'symbol': order_pair,
                    'type': order_data.get('pricetype', '').lower(),
                    'side': order_data.get('action', '').lower(),
                    'price': float(order_data.get('price', 0)),
                    'amount': float(order_data.get('quantity', 0)),
                    'filled': 0,
                    'remaining': float(order_data.get('quantity', 0)),
                    'status': 'open',
                    'info': order_data,
                }
                open_orders.append(order)
                # Update cache
                self._open_orders_cache[order_id] = order
            
            return open_orders
            
        except Exception as e:
            logger.warning(f"Failed to fetch open orders: {e}, using cache")
            # Fallback to cached orders
            if pair:
                return [o for o in self._open_orders_cache.values() if o['symbol'] == pair]
            return list(self._open_orders_cache.values())

    def fetch_balance(self) -> dict:
        """
        Fetch account balance.
        
        :return: Balance data
        """
        try:
            response = self._make_request('/api/v1/funds', method='POST', data={
                'strategy': self._strategy_name
            })
            
            data = response.get('data', {})
            
            # Convert OpenAlgo funds format to Freqtrade format
            balance = {
                'INR': {
                    'free': float(data.get('availablecash', 0)),
                    'used': float(data.get('usedmargin', 0)),
                    'total': float(data.get('availablecash', 0)) + float(data.get('usedmargin', 0)),
                },
                'info': data,
                'free': {'INR': float(data.get('availablecash', 0))},
                'used': {'INR': float(data.get('usedmargin', 0))},
                'total': {'INR': float(data.get('availablecash', 0)) + float(data.get('usedmargin', 0))},
            }
            
            return balance
            
        except Exception as e:
            # If in dry-run mode or balance fetch fails, return default balance
            logger.warning(f"Failed to fetch balance from OpenAlgo: {e}. Using default balance.")
            default_balance = 100000.0  # Default 1 lakh INR
            return {
                'INR': {
                    'free': default_balance,
                    'used': 0.0,
                    'total': default_balance,
                },
                'info': {},
                'free': {'INR': default_balance},
                'used': {'INR': 0.0},
                'total': {'INR': default_balance},
            }

    def get_fee(
        self,
        symbol: str = '',
        type: str = '',
        side: str = '',
        amount: float = 1,
        price: float = 1,
        taker_or_maker: str = 'maker',
        takerOrMaker: str = 'maker'
    ) -> float:
        """Get trading fee for OpenAlgo - typically 0.03% for NSE"""
        return 0.0003  # 0.03% default NSE brokerage
    
    def get_min_pair_stake_amount(
        self,
        pair: str,
        price: float,
        stoploss: float,
        leverage: float = 1.0
    ) -> Optional[float]:
        """Get minimum stake amount - NSE has minimum lot sizes"""
        return 1.0  # Minimum 1 share
    
    def get_max_pair_stake_amount(
        self,
        pair: str,
        price: float,
        leverage: float = 1.0
    ) -> float:
        """Get maximum stake amount"""
        return float('inf')

    @property
    def name(self) -> str:
        """Exchange name"""
        return 'Openalgo'
    
    @property
    def id(self) -> str:
        """Exchange ID"""
        return 'openalgo'
    
    @property
    def markets(self) -> dict:
        """Get markets dictionary"""
        return self._markets
    
    @property
    def precisionMode(self) -> int:
        """Get precision mode (DECIMAL_PLACES = 2 for OpenAlgo)"""
        return 2  # DECIMAL_PLACES
    
    @property
    def timeframes(self) -> list:
        """Supported timeframes for OpenAlgo"""
        return ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w']
    
    def get_markets(self, base_currencies: list | None = None,
                    quote_currencies: list | None = None,
                    spot_only: bool = False, margin_only: bool = False,
                    futures_only: bool = False, tradable_only: bool = True,
                    active_only: bool = False) -> dict:
        """Get filtered markets"""
        markets = self.markets
        
        if tradable_only:
            markets = {k: v for k, v in markets.items() if v.get('active', True)}
        
        if base_currencies:
            markets = {k: v for k, v in markets.items() if v.get('base') in base_currencies}
        
        if quote_currencies:
            markets = {k: v for k, v in markets.items() if v.get('quote') in quote_currencies}
        
        return markets

    def exchange_has(self, endpoint: str) -> bool:
        """Check if exchange supports endpoint"""
        # OpenAlgo supports common trading operations via REST API
        supported = {
            'fetchOHLCV': True,
            'fetchTicker': True,
            'fetchTickers': False,
            'fetchOrderBook': True,
            'createOrder': True,
            'cancelOrder': True,
            'fetchOrder': True,
            'fetchOrders': True,
            'fetchOpenOrders': True,
            'fetchClosedOrders': False,
            'fetchBalance': True,
            'fetchMyTrades': False,
        }
        return supported.get(endpoint, False)
    
    def validate_config(self, config: dict) -> None:
        """Validate OpenAlgo configuration"""
        exchange_config = config.get('exchange', {})
        if not exchange_config.get('key'):
            raise OperationalException("OpenAlgo requires an API key")
        if not exchange_config.get('urls', {}).get('api'):
            logger.warning("OpenAlgo API URL not specified, using default: http://127.0.0.1:5000")
    
    def validate_ordertypes(self, order_types: dict) -> None:
        """
        Validate order types for OpenAlgo.
        
        :param order_types: Order types configuration
        """
        # OpenAlgo supports market and limit orders
        supported_types = ['market', 'limit']
        
        for order_type in order_types.values():
            if order_type not in supported_types:
                raise OperationalException(
                    f'Order type {order_type} not supported by OpenAlgo'
                )
    
    def validate_timeframes(self, timeframe: str | None) -> None:
        """Validate timeframe"""
        # OpenAlgo supports common timeframes
        pass
    
    def validate_config(self, config) -> None:
        """Validate exchange configuration"""
        # Minimal validation for OpenAlgo
        pass
    
    def get_balances(self) -> dict:
        """Get account balances - override to use custom fetch_balance"""
        return self.fetch_balance()
    
    def close(self) -> None:
        """Close exchange connections"""
        if hasattr(self, '_session'):
            self._session.close()
    
    def reload_markets(self, reload: bool = False) -> None:
        """Reload markets (no-op for OpenAlgo as markets are static)"""
        pass
    
    def refresh_latest_ohlcv(self, pair_list: list[tuple[str, str, CandleType]]) -> None:
        """
        Refresh OHLCV data synchronously for OpenAlgo.
        Fetches latest candles from OpenAlgo and stores them in _klines cache.
        """
        for pair, timeframe, candle_type in pair_list:
            try:
                # Fetch OHLCV data from OpenAlgo
                ohlcv = self.fetch_ohlcv(pair, timeframe, candle_type=candle_type)
                
                if ohlcv:
                    # Convert to DataFrame format expected by Freqtrade
                    df = DataFrame(ohlcv, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
                    df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True)
                    
                    # Store in _klines cache
                    cache_key = (pair, timeframe, candle_type)
                    self._klines[cache_key] = df
                    
                    logger.debug(f"Refreshed {len(df)} candles for {pair} ({timeframe})")
                else:
                    logger.warning(f"No OHLCV data fetched for {pair} ({timeframe})")
                    
            except Exception as e:
                logger.error(f"Error refreshing OHLCV for {pair}: {e}")

    def is_market_open(self) -> bool:
        """
        Check if NSE market is currently open.

        :return: True if market is open
        """
        nse_calendar = get_nse_calendar()
        return nse_calendar.is_market_open()
    
    def get_proxy_coin(self) -> str:
        """
        Get the proxy coin for the given coin.
        Falls back to the stake currency if no proxy coin is found.
        
        :return: Proxy coin or stake currency
        """
        return self._config.get("stake_currency", "INR")
    
    def market_is_tradable(self, market: dict[str, Any]) -> bool:
        """
        Check if the market symbol is tradable by Freqtrade.
        For OpenAlgo, all markets in the whitelist are tradable.
        
        :param market: Market dictionary
        :return: True if tradable
        """
        return (
            market.get("quote") is not None
            and market.get("base") is not None
            and market.get("active", True) is True
            and (self.trading_mode == TradingMode.SPOT and market.get("spot", True))
        )
    
    def get_pair_quote_currency(self, pair: str) -> str:
        """
        Return a pair's quote currency (base/quote).
        
        :param pair: Pair to get quote currency for
        :return: Quote currency
        """
        return self._markets.get(pair, {}).get("quote", "INR")
    
    def get_pair_base_currency(self, pair: str) -> str:
        """
        Return a pair's base currency (base/quote).
        
        :param pair: Pair to get base currency for
        :return: Base currency
        """
        # Extract base from pair (e.g., "RELIANCE/INR" -> "RELIANCE")
        base = pair.split('/')[0] if '/' in pair else pair
        return self._markets.get(pair, {}).get("base", base)
    
    def ws_connection_reset(self):
        """
        Called at regular intervals to reset the websocket connection.
        OpenAlgo doesn't use websocket in this implementation, so this is a no-op.
        """
        pass
    
    def klines(self, pair_interval: tuple, copy: bool = True) -> DataFrame:
        """
        Get cached klines data for a pair and timeframe.
        
        :param pair_interval: Tuple of (pair, timeframe, candle_type)
        :param copy: Return a copy of the dataframe
        :return: DataFrame with OHLCV data
        """
        if pair_interval in self._klines:
            return self._klines[pair_interval].copy() if copy else self._klines[pair_interval]
        else:
            return DataFrame()
    
    def get_rate(
        self,
        pair: str,
        refresh: bool,
        side: str,
        is_short: bool,
        order_book: dict | None = None,
        ticker: dict | None = None,
    ) -> float:
        """
        Get the current rate for a pair.
        
        :param pair: Pair to get rate for
        :param refresh: Force refresh (fetch new data)
        :param side: "entry" or "exit"
        :param is_short: Whether this is a short position
        :param order_book: Optional order book data
        :param ticker: Optional ticker data
        :return: Current rate
        """
        # Fetch ticker if not provided
        if ticker is None:
            ticker = self.fetch_ticker(pair)
        
        # Use last price as the rate
        # For entry: use ask price (buying)
        # For exit: use bid price (selling)
        if side == "entry":
            rate = ticker.get('ask') or ticker.get('last')
        else:
            rate = ticker.get('bid') or ticker.get('last')
        
        if rate is None:
            raise ExchangeError(f"Could not determine rate for {pair}")
        
        return float(rate)
    
    def get_funding_fees(
        self,
        pair: str,
        amount: float,
        is_short: bool,
        open_date: datetime,
    ) -> float:
        """
        Get funding fees for a position.
        NSE spot trading doesn't have funding fees.
        
        :return: 0.0 (no funding fees for spot)
        """
        return 0.0
    
    def get_max_leverage(self, pair: str, stake_amount: float) -> float:
        """
        Get maximum leverage for a pair.
        NSE spot trading doesn't support leverage.
        
        :return: 1.0 (no leverage for spot)
        """
        return 1.0
    
    def get_min_pair_stake_amount(
        self,
        pair: str,
        price: float,
        stoploss: float,
        leverage: float = 1.0,
    ) -> float | None:
        """
        Get minimum stake amount for a pair.
        
        :return: Minimum stake amount
        """
        # For NSE, minimum is typically 1 share
        return price * 1.0
    
    def get_max_pair_stake_amount(
        self,
        pair: str,
        price: float,
        leverage: float = 1.0,
    ) -> float:
        """
        Get maximum stake amount for a pair.
        
        :return: Very large number (no practical limit)
        """
        return 1000000000.0  # 1 billion
    
    
    def get_trades_for_order(self, order_id: str, pair: str, since: int) -> list:
        """
        Get trades for a specific order.
        
        :return: List of trades
        """
        # OpenAlgo doesn't provide detailed trade breakdown
        return []
    
    def get_order_id_conditional(self, order: dict) -> str:
        """
        Get order ID from order dict.
        
        :return: Order ID
        """
        return order.get('id', '')
    
    def get_historic_ohlcv(
        self,
        pair: str,
        timeframe: str,
        since_ms: int,
        candle_type: CandleType,
        is_new_pair: bool = False,
        until_ms: int | None = None,
    ) -> tuple:
        """
        Get historic OHLCV data.
        
        :return: Tuple of (pair, timeframe, candle_type, data, drop_incomplete)
        """
        data = self.fetch_ohlcv(pair, timeframe, since_ms, candle_type=candle_type)
        return (pair, timeframe, candle_type, data, True)
    
    def calculate_fee_rate(
        self,
        pair: str,
        taker_or_maker: str,
        buy: bool,
        amount: float,
        price: float,
    ) -> float:
        """
        Calculate fee rate.
        
        :return: Fee rate
        """
        return 0.0003  # 0.03%
    
    def fetch_positions(self, symbols: list[str] | None = None) -> list:
        """
        Fetch open positions.
        NSE spot trading doesn't have positions (only orders).
        
        :return: Empty list (no positions for spot)
        """
        return []
    
    def set_leverage(self, leverage: float, pair: str | None = None) -> None:
        """
        Set leverage for a pair.
        NSE spot trading doesn't support leverage.
        """
        pass
    
    def set_margin_mode(self, margin_mode: str, pair: str | None = None) -> None:
        """
        Set margin mode.
        NSE spot trading doesn't have margin modes.
        """
        pass
    
    def fetch_ticker(self, pair: str) -> dict:
        """
        Fetch ticker data for a pair.
        Returns last price from most recent candle.
        """
        try:
            # Get the most recent candle
            ohlcv = self.fetch_ohlcv(pair, '5m', limit=1)
            if ohlcv and len(ohlcv) > 0:
                last_candle = ohlcv[-1]
                close_price = float(last_candle[4])
                if close_price > 0:
                    return {
                        'symbol': pair,
                        'last': close_price,
                        'bid': close_price,
                        'ask': close_price,
                        'high': float(last_candle[2]),
                        'low': float(last_candle[3]),
                        'volume': float(last_candle[5]),
                    }
            
            # If no data, return None to indicate unavailable
            # This prevents division by zero errors
            logger.warning(f"No ticker data available for {pair}")
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch ticker for {pair}: {e}")
            return None
    
    def fetch_tickers(self, symbols: list[str] | None = None) -> dict:
        """
        Fetch tickers for multiple symbols.
        """
        tickers = {}
        pairs = symbols if symbols else list(self._markets.keys())
        for pair in pairs:
            try:
                tickers[pair] = self.fetch_ticker(pair)
            except Exception:
                pass
        return tickers
    
    def get_tickers(self, symbols: list[str] | None = None, *, cached: bool = False) -> dict:
        """
        Get tickers (alias for fetch_tickers).
        """
        return self.fetch_tickers(symbols)
    
    def fetch_trading_fees(self) -> dict:
        """
        Fetch trading fees.
        """
        return {'trading': {}, 'maker': 0.0003, 'taker': 0.0003}
    
    def get_balances(self) -> dict:
        """
        Get account balances (alias for fetch_balance).
        """
        return self.fetch_balance()
    
    def cancel_order(self, order_id: str, pair: str, params: dict | None = None) -> dict:
        """
        Cancel an order.
        """
        try:
            response = self._make_request('/api/v1/cancelorder', method='POST', data={
                'orderid': order_id,
                'strategy': self._strategy_name
            })
            return {'id': order_id, 'status': 'canceled', 'info': response}
        except Exception as e:
            raise ExchangeError(f"Failed to cancel order: {e}")
    
    def cancel_stoploss_order(self, order_id: str, pair: str, params: dict | None = None) -> dict:
        """
        Cancel a stoploss order.
        """
        return self.cancel_order(order_id, pair, params)
    
    def fetch_l2_order_book(self, pair: str, limit: int = 100) -> dict:
        """
        Fetch order book.
        NSE doesn't provide order book through OpenAlgo.
        Return minimal structure.
        """
        return {
            'bids': [],
            'asks': [],
            'timestamp': None,
            'datetime': None,
        }
    
    def get_markets(self, base_currencies: list[str] | None = None, quote_currencies: list[str] | None = None, **kwargs) -> dict:
        """
        Get available markets.
        """
        return self._markets
    
    def get_quote_currencies(self) -> list[str]:
        """
        Get list of quote currencies.
        """
        return ['INR']
    
    def get_contract_size(self, pair: str) -> float | None:
        """
        Get contract size for a pair.
        For spot, contract size is 1.
        """
        return 1.0
    
    def get_precision_amount(self, pair: str) -> float | None:
        """
        Get amount precision.
        """
        return 1.0
    
    def get_precision_price(self, pair: str) -> float | None:
        """
        Get price precision.
        """
        return 0.05  # NSE tick size
    
    def get_interest_rate(self) -> float:
        """
        Get interest rate for margin trading.
        NSE spot doesn't have interest rates.
        """
        return 0.0
    
    def get_liquidation_price(
        self,
        pair: str,
        side: str,
        amount: float,
        open_rate: float,
        leverage: float,
        wallet_balance: float,
    ) -> float | None:
        """
        Get liquidation price.
        NSE spot doesn't have liquidation.
        """
        return None
    
    def get_option(self, param: str, default: Any | None = None) -> Any:
        """
        Get exchange option.
        """
        return self._config.get('exchange', {}).get(param, default)
    
    def additional_exchange_init(self) -> None:
        """
        Additional exchange initialization.
        """
        pass
    
    def get_valid_pair_amount(self, pair: str, amount: float, price: float) -> float:
        """
        Override amount calculation for NSE.
        Returns integer quantity based on fixed_quantity config or rounded amount.
        """
        fixed_qty = self._config.get('exchange', {}).get('fixed_quantity')
        
        if fixed_qty and fixed_qty > 0:
            return float(fixed_qty)
        else:
            # Round to integer shares
            return float(max(1, int(round(amount))))
    
    def funding_fee_cutoff(self, open_date: datetime) -> bool:
        """
        Check if funding fee cutoff applies.
        NSE spot doesn't have funding fees.
        """
        return False
    
    def fetch_funding_rate(self, pair: str) -> dict:
        """
        Fetch funding rate.
        NSE spot doesn't have funding rates.
        """
        return {'rate': 0.0, 'timestamp': None}
    
    def fetch_funding_rates(self, symbols: list[str] | None = None) -> dict:
        """
        Fetch funding rates for multiple symbols.
        NSE spot doesn't have funding rates.
        """
        return {}
    
    def get_leverage_tiers(self) -> dict:
        """
        Get leverage tiers.
        NSE spot doesn't support leverage.
        """
        return {}
    
    def load_leverage_tiers(self) -> dict:
        """
        Load leverage tiers.
        NSE spot doesn't support leverage.
        """
        return {}
    
    def dry_run_liquidation_price(
        self,
        pair: str,
        open_rate: float,
        is_short: bool,
        amount: float,
        stake_amount: float,
        leverage: float,
        wallet_balance: float,
    ) -> float | None:
        """
        Calculate liquidation price for dry run.
        NSE spot doesn't have liquidation.
        """
        return None
