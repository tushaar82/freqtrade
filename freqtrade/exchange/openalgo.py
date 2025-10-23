"""OpenAlgo exchange subclass - for NSE trading"""

import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional

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
        # Initialize CustomExchange base class
        super().__init__(config)
        
        # OpenAlgo specific configuration
        self._api_key = config.get('exchange', {}).get('key', '')
        self._host = config.get('exchange', {}).get('urls', {}).get('api', 'http://127.0.0.1:5000')
        self._strategy_name = config.get('strategy', 'Freqtrade')
        
        # Default exchange for NSE
        self._default_exchange = config.get('exchange', {}).get('nse_exchange', 'NSE')
        
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

        try:
            if method == 'GET':
                response = self._session.get(url, headers=self._get_headers(), params=params)
            elif method == 'POST':
                response = self._session.post(url, headers=self._get_headers(), json=data)
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
            if e.response.status_code == 429:
                raise DDosProtection(f"OpenAlgo rate limit exceeded: {e}")
            elif e.response.status_code in [500, 502, 503, 504]:
                raise TemporaryError(f"OpenAlgo server error: {e}")
            else:
                raise ExchangeError(f"OpenAlgo HTTP error: {e}")
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
        if since:
            start_date = datetime.fromtimestamp(since / 1000).strftime('%Y-%m-%d')
        else:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            response = self._make_request('/api/v1/history', method='POST', data={
                'symbol': symbol,
                'exchange': exchange,
                'interval': interval,
                'start_date': start_date,
                'end_date': end_date
            })
            
            # OpenAlgo returns a DataFrame in dict format
            # We need to convert it to OHLCV list format
            df = DataFrame(response.get('data', {}))
            
            if df.empty:
                return []
            
            # Convert to OHLCV format: [timestamp, open, high, low, close, volume]
            ohlcv = []
            for idx, row in df.iterrows():
                timestamp = int(to_datetime(idx).timestamp() * 1000)
                ohlcv.append([
                    timestamp,
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    float(row.get('volume', 0))
                ])
            
            # Apply limit if specified
            if limit:
                ohlcv = ohlcv[-limit:]
                
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
        
        # Map order type
        price_type = 'LIMIT' if ordertype == 'limit' else 'MARKET'
        
        # Get product type (default to MIS for intraday)
        product = params.get('product', 'MIS')
        
        order_data = {
            'strategy': self._strategy_name,
            'symbol': symbol,
            'action': side.upper(),
            'exchange': exchange,
            'price_type': price_type,
            'product': product,
            'quantity': int(amount),
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
                amount=amount,
                price=rate,
                status='open'
            )
            order['info'] = response
            
            # Cache as open order
            self._open_orders_cache[order_id] = order
            
            return order
            
        except Exception as e:
            if 'insufficient' in str(e).lower():
                raise InsufficientFundsError(f"Insufficient funds: {e}")
            raise ExchangeError(f"Failed to create order: {e}")

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
                'order_id': order_id,
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
            raise ExchangeError(f"Failed to fetch balance: {e}")

    def get_fee(
        self,
        symbol: str = '',
        type: str = '',
        side: str = '',
        amount: float = 1,
        price: float = 1,
        taker_or_maker: str = 'maker'
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
        """Refresh OHLCV data synchronously for OpenAlgo"""
        # OpenAlgo would fetch real data from the API
        # For now, just pass - implement when needed
        pass

    def is_market_open(self) -> bool:
        """
        Check if NSE market is currently open.

        :return: True if market is open
        """
        nse_calendar = get_nse_calendar()
        return nse_calendar.is_market_open()
