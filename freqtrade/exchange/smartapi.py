"""Smart API (Angel One) exchange subclass - for NSE trading"""

import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional

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
from freqtrade.exchange import Exchange
from freqtrade.exchange.exchange_types import FtHas, OrderBook, Ticker


logger = logging.getLogger(__name__)


class Smartapi(Exchange):
    """
    Smart API (Angel One) exchange class for NSE trading.
    
    Smart API is Angel One's trading API supporting NSE, BSE, MCX, and other Indian exchanges.
    This implementation uses the SmartAPI Python SDK.
    
    Note: Requires 'SmartApi' package: pip install smartapi-python
    """

    _ft_has: FtHas = {
        "ohlcv_candle_limit": 1000,
        "ohlcv_has_history": True,
        "ohlcv_partial_candle": True,
        "ohlcv_require_since": False,
        "stoploss_on_exchange": True,  # Smart API supports GTT (Good Till Triggered)
        "order_time_in_force": ["DAY", "IOC"],
        "trades_has_history": True,
        "tickers_have_quoteVolume": True,
        "tickers_have_bid_ask": True,
        "tickers_have_price": True,
        "ws_enabled": True,  # Smart API supports WebSocket
        "always_require_api_keys": True,
    }

    # NSE Market Hours (IST)
    NSE_MARKET_OPEN = "09:15"
    NSE_MARKET_CLOSE = "15:30"
    
    # Supported trading modes
    _supported_trading_mode_margin_pairs = [
        (TradingMode.SPOT, MarginMode.NONE),
    ]

    def __init__(self, config, validate: bool = True, exchange_config=None, load_leverage_tiers: bool = False, **kwargs):
        """
        Initialize Smart API exchange.
        
        Requires Smart API credentials (api_key, username, password, totp_token).
        """
        # Initialize minimal Exchange attributes without CCXT
        from threading import Lock
        from cachetools import TTLCache
        
        self._api = None  # No CCXT API for Smart API
        self._api_async = None
        self._ws_async = None
        self._exchange_ws = None
        self._markets = {}
        self._trading_fees = {}
        self._leverage_tiers = {}
        self._loop_lock = Lock()
        self.loop = None  # No async loop for Smart API
        self._config = config
        self._cache_lock = Lock()
        self._fetch_tickers_cache = TTLCache(maxsize=4, ttl=60 * 10)
        self._exit_rate_cache = TTLCache(maxsize=100, ttl=300)
        self._entry_rate_cache = TTLCache(maxsize=100, ttl=300)
        self._klines = {}
        self._expiring_candle_cache = {}
        self._trades = {}
        self._dry_run_open_orders = {}
        
        # Additional Exchange attributes
        self._pairs_last_refresh_time = {}
        self._last_markets_refresh = 0
        self._ft_has = self._ft_has.copy()
        self.log_responses = False
        self._ohlcv_partial_candle = self._ft_has.get('ohlcv_partial_candle', True)
        self.liquidation_buffer = 0.05
        self.required_candle_call_count = 1  # Number of candle calls needed
        
        # Set trading mode
        self.trading_mode = TradingMode.SPOT
        self.margin_mode = MarginMode.NONE
        self._supported_trading_mode_margin_pairs = [(TradingMode.SPOT, MarginMode.NONE)]
        
        try:
            from SmartApi import SmartConnect
            import pyotp
        except ImportError:
            raise OperationalException(
                "SmartAPI requires 'smartapi-python' and 'pyotp' packages. "
                "Install with: pip install smartapi-python pyotp"
            )
        
        # Smart API credentials
        exchange_config = config.get('exchange', {})
        self._api_key = exchange_config.get('key', '')
        self._username = exchange_config.get('username', '')
        self._password = exchange_config.get('password', exchange_config.get('secret', ''))
        self._totp_token = exchange_config.get('totp_token', '')
        
        # Initialize Smart API
        self._smart_api = SmartConnect(api_key=self._api_key)
        self._auth_token = None
        self._refresh_token = None
        self._feed_token = None
        
        # Default exchange
        self._default_exchange = exchange_config.get('nse_exchange', 'NSE')
        
        # Login to Smart API
        self._login()
        
        logger.info(f"Smart API exchange initialized for user: {self._username}")
        
    def _login(self):
        """Login to Smart API and get authentication tokens"""
        try:
            import pyotp
            
            # Generate TOTP
            totp = pyotp.TOTP(self._totp_token).now()
            
            # Generate session
            data = self._smart_api.generateSession(
                clientCode=self._username,
                password=self._password,
                totp=totp
            )
            
            if not data.get('status', False):
                raise ExchangeError(f"Smart API login failed: {data}")
            
            # Extract tokens
            self._auth_token = data['data']['jwtToken']
            self._refresh_token = data['data']['refreshToken']
            self._feed_token = self._smart_api.getfeedToken()
            
            logger.info("Smart API login successful")
            
        except Exception as e:
            raise OperationalException(f"Smart API login failed: {e}")

    def _convert_symbol_to_smartapi(self, pair: str) -> tuple[str, str, str]:
        """
        Convert Freqtrade pair to Smart API format.
        
        :param pair: Freqtrade pair (e.g., 'SBIN/INR')
        :return: Tuple of (trading_symbol, symbol_token, exchange)
        """
        # Remove quote currency
        symbol = pair.split('/')[0]
        
        # Determine exchange
        if 'NFO' in pair.upper():
            exchange = 'NFO'
            trading_symbol = f"{symbol}"
        elif 'BSE' in pair.upper():
            exchange = 'BSE'
            trading_symbol = f"{symbol}-EQ"
        elif 'MCX' in pair.upper():
            exchange = 'MCX'
            trading_symbol = symbol
        else:
            exchange = self._default_exchange
            trading_symbol = f"{symbol}-EQ"
        
        # Note: Symbol token would need to be fetched from Smart API master data
        # For now, we'll use a placeholder. In production, implement token lookup.
        symbol_token = self._get_symbol_token(trading_symbol, exchange)
            
        return trading_symbol, symbol_token, exchange

    def _get_symbol_token(self, trading_symbol: str, exchange: str) -> str:
        """
        Get symbol token for a trading symbol.
        
        In production, this should fetch from Smart API's master symbol data.
        For now, returns a placeholder.
        """
        # TODO: Implement symbol token lookup from Smart API master data
        # This would typically involve:
        # 1. Download master symbols file
        # 2. Search for symbol
        # 3. Return token
        
        logger.warning(f"Symbol token lookup not fully implemented for {trading_symbol}")
        return "0"  # Placeholder

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

    def get_options_instruments(self) -> List[dict]:
        """
        Fetch options instruments from Angel One (placeholder implementation).
        
        :return: List of options instruments
        """
        # This would fetch from Smart API's master data
        # For now, return empty list
        logger.warning("get_options_instruments not fully implemented for SmartAPI")
        return []

    def fetch_option_chain(self, underlying: str, expiry: str = None) -> List[dict]:
        """
        Fetch option chain for an underlying (placeholder implementation).
        
        :param underlying: Underlying symbol (e.g., 'NIFTY')
        :param expiry: Expiry date (optional)
        :return: List of option contracts
        """
        # This would need to be implemented based on Smart API's option chain endpoint
        # For now, return empty list
        logger.warning("fetch_option_chain not fully implemented for SmartAPI")
        return []

    def _get_lot_size(self, pair: str) -> int:
        """Get lot size for a symbol"""
        try:
            # Try to get from LotSizeManager if available
            if hasattr(self, '_lot_size_manager') and self._lot_size_manager:
                return self._lot_size_manager.get_lot_size(pair)
        except Exception:
            pass
        return 1  # Default lot size

    def fetch_ticker(self, pair: str) -> Ticker:
        """
        Fetch ticker data for a pair.
        
        :param pair: Freqtrade pair
        :return: Ticker data
        """
        trading_symbol, symbol_token, exchange = self._convert_symbol_to_smartapi(pair)
        
        try:
            # Smart API uses LTP endpoint
            response = self._smart_api.ltpData(exchange, trading_symbol, symbol_token)
            
            if not response.get('status', False):
                raise ExchangeError(f"Failed to fetch ticker: {response}")
            
            data = response.get('data', {})
            
            return {
                'symbol': pair,
                'ask': None,  # Smart API LTP doesn't provide ask/bid
                'bid': None,
                'last': data.get('ltp'),
                'askVolume': None,
                'bidVolume': None,
                'quoteVolume': None,
                'baseVolume': None,
                'percentage': None,
            }
        except Exception as e:
            raise ExchangeError(f"Failed to fetch ticker for {pair}: {e}")

    def fetch_order_book(self, pair: str, limit: int = 5) -> OrderBook:
        """
        Fetch order book (market depth) for a pair.
        
        :param pair: Freqtrade pair
        :param limit: Depth limit
        :return: Order book data
        """
        trading_symbol, symbol_token, exchange = self._convert_symbol_to_smartapi(pair)
        
        try:
            response = self._smart_api.getMarketData(
                mode="FULL",
                exchangeTokens={exchange: [symbol_token]}
            )
            
            if not response.get('status', False):
                raise ExchangeError(f"Failed to fetch order book: {response}")
            
            data = response.get('data', {}).get('fetched', [{}])[0]
            
            # Extract depth data
            asks = [(d['price'], d['quantity']) for d in data.get('depth', {}).get('sell', [])[:limit]]
            bids = [(d['price'], d['quantity']) for d in data.get('depth', {}).get('buy', [])[:limit]]
            
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
        :param timeframe: Timeframe
        :param since: Timestamp in milliseconds
        :param limit: Number of candles
        :param candle_type: Candle type
        :return: List of OHLCV data
        """
        trading_symbol, symbol_token, exchange = self._convert_symbol_to_smartapi(pair)
        
        # Convert Freqtrade timeframe to Smart API interval
        interval_map = {
            '1m': 'ONE_MINUTE',
            '3m': 'THREE_MINUTE',
            '5m': 'FIVE_MINUTE',
            '10m': 'TEN_MINUTE',
            '15m': 'FIFTEEN_MINUTE',
            '30m': 'THIRTY_MINUTE',
            '1h': 'ONE_HOUR',
            '1d': 'ONE_DAY',
        }
        
        interval = interval_map.get(timeframe, 'FIVE_MINUTE')
        
        # Calculate date range
        if since:
            from_date = datetime.fromtimestamp(since / 1000)
        else:
            from_date = datetime.now() - timedelta(days=7)
            
        to_date = datetime.now()
        
        try:
            params = {
                "exchange": exchange,
                "symboltoken": symbol_token,
                "interval": interval,
                "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
                "todate": to_date.strftime("%Y-%m-%d %H:%M")
            }
            
            response = self._smart_api.getCandleData(params)
            
            if not response.get('status', False):
                raise ExchangeError(f"Failed to fetch OHLCV: {response}")
            
            data = response.get('data', [])
            
            # Convert to OHLCV format: [timestamp, open, high, low, close, volume]
            ohlcv = []
            for candle in data:
                timestamp = int(to_datetime(candle[0]).timestamp() * 1000)
                ohlcv.append([
                    timestamp,
                    float(candle[1]),  # open
                    float(candle[2]),  # high
                    float(candle[3]),  # low
                    float(candle[4]),  # close
                    float(candle[5]) if len(candle) > 5 else 0  # volume
                ])
            
            # Apply limit
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
        leverage: float = 1.0,
    ) -> dict:
        """
        Create an order on Smart API.
        
        :param pair: Freqtrade pair
        :param ordertype: Order type ('limit', 'market')
        :param side: Order side ('buy', 'sell')
        :param amount: Order amount
        :param rate: Order price (for limit orders)
        :param params: Additional parameters
        :param leverage: Leverage
        :return: Order data
        """
        trading_symbol, symbol_token, exchange = self._convert_symbol_to_smartapi(pair)
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
        if ordertype == 'limit':
            order_type = 'LIMIT'
        elif ordertype == 'market':
            order_type = 'MARKET'
        else:
            order_type = 'LIMIT'
        
        # Get product type (default to INTRADAY)
        product_type = params.get('product', 'INTRADAY')
        if product_type == 'MIS':
            product_type = 'INTRADAY'
        elif product_type == 'CNC':
            product_type = 'DELIVERY'
        
        order_params = {
            "variety": "NORMAL",
            "tradingsymbol": trading_symbol,
            "symboltoken": symbol_token,
            "transactiontype": side.upper(),
            "exchange": exchange,
            "ordertype": order_type,
            "producttype": product_type,
            "duration": "DAY",
            "price": str(rate) if rate else "0",
            "squareoff": "0",
            "stoploss": "0",
            "quantity": str(int(amount))
        }
        
        try:
            order_id = self._smart_api.placeOrder(order_params)
            
            return {
                'id': order_id,
                'info': {'orderid': order_id},
                'timestamp': int(datetime.now().timestamp() * 1000),
                'datetime': datetime.now().isoformat(),
                'status': 'open',
                'symbol': pair,
                'type': ordertype,
                'side': side,
                'price': rate,
                'amount': amount,
                'filled': 0,
                'remaining': amount,
                'fee': None,
            }
            
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
            response = self._smart_api.orderBook()
            
            if not response.get('status', False):
                raise ExchangeError(f"Failed to fetch order book: {response}")
            
            orders = response.get('data', [])
            
            # Find the specific order
            order = None
            for o in orders:
                if o.get('orderid') == order_id:
                    order = o
                    break
            
            if not order:
                raise InvalidOrderException(f"Order {order_id} not found")
            
            # Map status
            status_map = {
                'complete': 'closed',
                'rejected': 'canceled',
                'cancelled': 'canceled',
                'open': 'open',
                'pending': 'open',
            }
            
            status = status_map.get(order.get('status', '').lower(), 'open')
            
            return {
                'id': order_id,
                'info': order,
                'timestamp': None,
                'datetime': order.get('updatetime'),
                'status': status,
                'symbol': pair,
                'type': order.get('ordertype', '').lower(),
                'side': order.get('transactiontype', '').lower(),
                'price': float(order.get('price', 0)),
                'average': float(order.get('averageprice', 0)),
                'amount': float(order.get('quantity', 0)),
                'filled': float(order.get('filledshares', 0)),
                'remaining': float(order.get('unfilledshares', 0)),
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
            response = self._smart_api.cancelOrder(
                order_id=order_id,
                variety="NORMAL"
            )
            
            return {
                'id': order_id,
                'info': response,
                'status': 'canceled',
            }
            
        except Exception as e:
            raise ExchangeError(f"Failed to cancel order {order_id}: {e}")

    def fetch_balance(self) -> dict:
        """
        Fetch account balance.
        
        :return: Balance data
        """
        try:
            response = self._smart_api.rmsLimit()
            
            if not response.get('status', False):
                raise ExchangeError(f"Failed to fetch balance: {response}")
            
            data = response.get('data', {})
            
            # Extract available cash
            available_cash = float(data.get('availablecash', 0))
            used_margin = float(data.get('m2munrealized', 0))
            
            balance = {
                'INR': {
                    'free': available_cash,
                    'used': used_margin,
                    'total': available_cash + used_margin,
                },
                'info': data,
                'free': {'INR': available_cash},
                'used': {'INR': used_margin},
                'total': {'INR': available_cash + used_margin},
            }
            
            return balance
            
        except Exception as e:
            raise ExchangeError(f"Failed to fetch balance: {e}")

    @property
    def name(self) -> str:
        """Exchange name"""
        return 'Smartapi'
    
    @property
    def id(self) -> str:
        """Exchange ID"""
        return 'smartapi'
    
    @property
    def markets(self) -> dict:
        """Get markets dictionary"""
        return self._markets
    
    @property
    def precisionMode(self) -> int:
        """Get precision mode (DECIMAL_PLACES = 2 for Smart API)"""
        return 2  # DECIMAL_PLACES
    
    @property
    def timeframes(self) -> list:
        """Supported timeframes for Smart API"""
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
        # Smart API supports common trading operations via SmartAPI SDK
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
            'fetchClosedOrders': True,
            'fetchBalance': True,
            'fetchMyTrades': True,
        }
        return supported.get(endpoint, False)
    
    def validate_ordertypes(self, order_types: dict) -> None:
        """Validate order types"""
        # Smart API supports various order types
        pass
    
    def validate_timeframes(self, timeframe: str | None) -> None:
        """Validate timeframe"""
        # Smart API supports common timeframes
        pass
    
    def validate_config(self, config) -> None:
        """Validate exchange configuration"""
        # Minimal validation for Smart API
        pass
    
    def get_balances(self) -> dict:
        """Get account balances - override to use custom fetch_balance"""
        return self.fetch_balance()
    
    def close(self) -> None:
        """Close exchange connections"""
        # Smart API handles cleanup internally
        pass
    
    def reload_markets(self, reload: bool = False) -> None:
        """Reload markets (no-op for Smart API as markets are static)"""
        pass
    
    def refresh_latest_ohlcv(self, pair_list: list[tuple[str, str, CandleType]]) -> None:
        """Refresh OHLCV data synchronously for Smart API"""
        # Smart API would fetch real data from Angel One
        # For now, just pass - implement when needed
        pass

    def is_market_open(self) -> bool:
        """
        Check if NSE market is currently open.
        
        :return: True if market is open
        """
        now = datetime.now()
        
        # Check if it's a weekday
        if now.weekday() > 4:  # Saturday or Sunday
            return False
            
        # Check market hours
        market_open = datetime.strptime(self.NSE_MARKET_OPEN, '%H:%M').time()
        market_close = datetime.strptime(self.NSE_MARKET_CLOSE, '%H:%M').time()
        
        current_time = now.time()
        
        return market_open <= current_time <= market_close
