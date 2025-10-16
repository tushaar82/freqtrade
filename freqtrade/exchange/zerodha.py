"""Zerodha exchange subclass - for NSE trading using Kite Connect API"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import time
import json

from pandas import DataFrame, to_datetime

from freqtrade.constants import BuySell
from freqtrade.enums import CandleType, MarginMode, TradingMode
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


logger = logging.getLogger(__name__)


class Zerodha(CustomExchange):
    """
    Zerodha exchange class using Kite Connect API for NSE trading.
    
    Zerodha Kite Connect is the official API for Zerodha customers.
    Requires daily OAuth authentication and Connect plan subscription (₹500/month).
    
    Note: Requires 'kiteconnect' package: pip install kiteconnect
    """

    _ft_has: FtHas = {
        "ohlcv_candle_limit": 1000,
        "ohlcv_has_history": True,
        "ohlcv_partial_candle": True,
        "ohlcv_require_since": False,
        "stoploss_on_exchange": True,  # Kite supports GTT (Good Till Triggered)
        "order_time_in_force": ["DAY", "IOC"],
        "trades_has_history": True,
        "tickers_have_quoteVolume": True,
        "tickers_have_bid_ask": True,
        "tickers_have_price": True,
        "ws_enabled": True,  # Kite supports WebSocket via KiteTicker
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
        Initialize Zerodha exchange.
        
        Requires Kite Connect credentials (api_key, api_secret, redirect_url).
        Daily OAuth authentication required.
        """
        # Initialize CustomExchange base class
        super().__init__(config)
        
        try:
            from kiteconnect import KiteConnect, KiteTicker
        except ImportError:
            raise OperationalException(
                "Zerodha requires 'kiteconnect' package. "
                "Install with: pip install kiteconnect"
            )
        
        # Kite Connect credentials
        exchange_config = config.get('exchange', {})
        self._api_key = exchange_config.get('key', '')
        self._api_secret = exchange_config.get('secret', '')
        self._redirect_url = exchange_config.get('redirect_url', 'https://127.0.0.1:8080')
        self._totp_token = exchange_config.get('totp_token', '')
        
        # Initialize Kite Connect
        self._kite = KiteConnect(api_key=self._api_key)
        self._access_token = None
        self._request_token = None
        
        # WebSocket ticker
        self._kws = None
        
        # Default exchange
        self._default_exchange = exchange_config.get('nse_exchange', 'NSE')
        
        # Instrument tokens cache
        self._instruments = {}
        self._symbol_to_token = {}
        
        # Session management
        self._session_expiry = None
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
        
        # Login to Kite Connect
        self._login()
        
        # Load instruments
        self._load_instruments()
        
        # Initialize markets from pair whitelist
        pair_whitelist = config.get('exchange', {}).get('pair_whitelist', [])
        self._init_markets_from_pairs(pair_whitelist, quote_currency='INR')
        
        logger.info(f"Zerodha exchange initialized for API key: {self._api_key[:8]}...")
        
    def _login(self):
        """Login to Kite Connect and get access token"""
        try:
            # Check if we have stored access token
            stored_token = self._get_stored_access_token()
            if stored_token and self._is_token_valid(stored_token):
                self._access_token = stored_token
                self._kite.set_access_token(self._access_token)
                logger.info("Using stored access token")
                return
            
            # Generate login URL for manual authentication
            login_url = self._kite.login_url()
            logger.warning(f"Please visit this URL to authenticate: {login_url}")
            
            # In production, implement automated OAuth flow with request_token
            # For now, require manual token input
            request_token = self._get_request_token_from_config()
            
            if not request_token:
                raise OperationalException(
                    "Request token required for Zerodha authentication. "
                    "Please visit the login URL and provide request_token in config."
                )
            
            # Generate session
            data = self._kite.generate_session(
                request_token=request_token,
                api_secret=self._api_secret
            )
            
            self._access_token = data["access_token"]
            self._kite.set_access_token(self._access_token)
            
            # Store access token for reuse
            self._store_access_token(self._access_token)
            
            # Set session expiry (Kite tokens expire at 6 AM next day)
            self._session_expiry = self._calculate_session_expiry()
            
            logger.info("Zerodha login successful")
            
        except Exception as e:
            raise OperationalException(f"Zerodha login failed: {e}")

    def _get_request_token_from_config(self) -> Optional[str]:
        """Get request token from config or environment"""
        # Check config first
        request_token = self._config.get('exchange', {}).get('request_token')
        if request_token:
            return request_token
        
        # Check environment variable
        import os
        return os.getenv('ZERODHA_REQUEST_TOKEN')

    def _get_stored_access_token(self) -> Optional[str]:
        """Get stored access token from file"""
        try:
            import os
            token_file = os.path.expanduser('~/.freqtrade_zerodha_token')
            if os.path.exists(token_file):
                with open(token_file, 'r') as f:
                    data = json.load(f)
                    return data.get('access_token')
        except Exception:
            pass
        return None

    def _store_access_token(self, token: str):
        """Store access token to file"""
        try:
            import os
            token_file = os.path.expanduser('~/.freqtrade_zerodha_token')
            data = {
                'access_token': token,
                'timestamp': datetime.now().isoformat(),
                'expiry': self._session_expiry.isoformat() if self._session_expiry else None
            }
            with open(token_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to store access token: {e}")

    def _is_token_valid(self, token: str) -> bool:
        """Check if access token is still valid"""
        try:
            # Set token temporarily to test
            old_token = self._kite.access_token
            self._kite.set_access_token(token)
            
            # Try to fetch profile
            self._kite.profile()
            
            # Restore old token
            self._kite.set_access_token(old_token)
            return True
        except Exception:
            return False

    def _calculate_session_expiry(self) -> datetime:
        """Calculate when the session expires (6 AM next day IST)"""
        now = datetime.now()
        next_day = now.replace(hour=6, minute=0, second=0, microsecond=0)
        if now.hour >= 6:
            next_day += timedelta(days=1)
        return next_day

    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last)
        self._last_request_time = time.time()

    def _load_instruments(self):
        """Load instrument master data from Kite"""
        try:
            self._rate_limit()
            
            # Fetch instruments for NSE and NFO
            nse_instruments = self._kite.instruments("NSE")
            nfo_instruments = self._kite.instruments("NFO")
            
            # Combine all instruments
            all_instruments = nse_instruments + nfo_instruments
            
            # Build symbol to token mapping
            for instrument in all_instruments:
                symbol = instrument['tradingsymbol']
                token = instrument['instrument_token']
                exchange = instrument['exchange']
                
                # Store in both directions
                self._symbol_to_token[f"{symbol}:{exchange}"] = token
                self._instruments[token] = instrument
            
            logger.info(f"Loaded {len(all_instruments)} instruments from Kite")
            
        except Exception as e:
            logger.error(f"Failed to load instruments: {e}")
            # Continue without instruments - will use fallback methods

    def _get_instrument_token(self, symbol: str, exchange: str = None) -> Optional[str]:
        """
        Get instrument token for a symbol.
        
        :param symbol: Trading symbol
        :param exchange: Exchange (NSE, NFO, etc.)
        :return: Instrument token
        """
        if not exchange:
            exchange = self._default_exchange
        
        key = f"{symbol}:{exchange}"
        return self._symbol_to_token.get(key)

    def _convert_symbol_to_kite(self, pair: str) -> tuple[str, str, str]:
        """
        Convert Freqtrade pair to Kite format.
        
        :param pair: Freqtrade pair (e.g., 'SBIN/INR', 'NIFTY25DEC24500CE/INR')
        :return: Tuple of (trading_symbol, instrument_token, exchange)
        """
        # Remove quote currency
        symbol = pair.split('/')[0]
        
        # Determine if it's options
        if self._is_options_symbol(symbol):
            exchange = 'NFO'
            trading_symbol = symbol
        elif 'NFO' in pair.upper():
            exchange = 'NFO'
            trading_symbol = symbol
        elif 'BSE' in pair.upper():
            exchange = 'BSE'
            trading_symbol = symbol
        else:
            exchange = self._default_exchange
            trading_symbol = symbol
        
        # Get instrument token
        instrument_token = self._get_instrument_token(trading_symbol, exchange)
        
        if not instrument_token:
            logger.warning(f"Instrument token not found for {trading_symbol}:{exchange}")
            instrument_token = "0"  # Fallback
            
        return trading_symbol, instrument_token, exchange

    def _is_options_symbol(self, symbol: str) -> bool:
        """Check if symbol is an options contract"""
        # Options symbols typically end with CE (Call European) or PE (Put European)
        return symbol.endswith(('CE', 'PE'))

    def parse_options_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Parse options symbol to extract components.
        
        :param symbol: Options symbol (e.g., 'NIFTY25DEC24500CE')
        :return: Dict with strike, expiry, option_type, underlying
        """
        if not self._is_options_symbol(symbol):
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

    def fetch_ticker(self, pair: str) -> Ticker:
        """
        Fetch ticker data for a pair.
        
        :param pair: Freqtrade pair
        :return: Ticker data
        """
        trading_symbol, instrument_token, exchange = self._convert_symbol_to_kite(pair)
        
        try:
            self._rate_limit()
            
            # Fetch LTP (Last Traded Price)
            ltp_data = self._kite.ltp([f"{exchange}:{instrument_token}"])
            
            # Fetch quote for more detailed data
            quote_data = self._kite.quote([f"{exchange}:{instrument_token}"])
            
            token_key = f"{exchange}:{instrument_token}"
            ltp = ltp_data.get(token_key, {}).get('last_price', 0)
            quote = quote_data.get(token_key, {})
            
            return {
                'symbol': pair,
                'ask': quote.get('depth', {}).get('sell', [{}])[0].get('price'),
                'bid': quote.get('depth', {}).get('buy', [{}])[0].get('price'),
                'last': ltp,
                'askVolume': quote.get('depth', {}).get('sell', [{}])[0].get('quantity'),
                'bidVolume': quote.get('depth', {}).get('buy', [{}])[0].get('quantity'),
                'quoteVolume': quote.get('volume', 0),
                'baseVolume': quote.get('volume', 0),
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
        trading_symbol, instrument_token, exchange = self._convert_symbol_to_kite(pair)
        
        try:
            self._rate_limit()
            
            quote_data = self._kite.quote([f"{exchange}:{instrument_token}"])
            token_key = f"{exchange}:{instrument_token}"
            quote = quote_data.get(token_key, {})
            
            depth = quote.get('depth', {})
            
            # Extract asks and bids
            asks = [(d['price'], d['quantity']) for d in depth.get('sell', [])[:limit]]
            bids = [(d['price'], d['quantity']) for d in depth.get('buy', [])[:limit]]
            
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
        trading_symbol, instrument_token, exchange = self._convert_symbol_to_kite(pair)
        
        # Convert Freqtrade timeframe to Kite interval
        interval_map = {
            '1m': 'minute',
            '3m': '3minute',
            '5m': '5minute',
            '10m': '10minute',
            '15m': '15minute',
            '30m': '30minute',
            '1h': '60minute',
            '1d': 'day',
        }
        
        interval = interval_map.get(timeframe, '5minute')
        
        # Calculate date range
        if since:
            from_date = datetime.fromtimestamp(since / 1000).date()
        else:
            from_date = (datetime.now() - timedelta(days=30)).date()
            
        to_date = datetime.now().date()
        
        try:
            self._rate_limit()
            
            # Fetch historical data
            data = self._kite.historical_data(
                instrument_token=int(instrument_token),
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
            
            # Convert to OHLCV format: [timestamp, open, high, low, close, volume]
            ohlcv = []
            for candle in data:
                timestamp = int(candle['date'].timestamp() * 1000)
                ohlcv.append([
                    timestamp,
                    float(candle['open']),
                    float(candle['high']),
                    float(candle['low']),
                    float(candle['close']),
                    float(candle['volume'])
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
        Create an order on Kite.
        
        :param pair: Freqtrade pair
        :param ordertype: Order type ('limit', 'market')
        :param side: Order side ('buy', 'sell')
        :param amount: Order amount
        :param rate: Order price (for limit orders)
        :param params: Additional parameters
        :param leverage: Leverage
        :return: Order data
        """
        trading_symbol, instrument_token, exchange = self._convert_symbol_to_kite(pair)
        params = params or {}
        
        # Map order type
        if ordertype == 'limit':
            order_type = self._kite.ORDER_TYPE_LIMIT
        elif ordertype == 'market':
            order_type = self._kite.ORDER_TYPE_MARKET
        else:
            order_type = self._kite.ORDER_TYPE_LIMIT
        
        # Get product type (default to MIS - Margin Intraday Squareoff)
        product_type = params.get('product', 'MIS')
        if product_type == 'MIS':
            product = self._kite.PRODUCT_MIS
        elif product_type == 'CNC':
            product = self._kite.PRODUCT_CNC
        elif product_type == 'NRML':
            product = self._kite.PRODUCT_NRML
        else:
            product = self._kite.PRODUCT_MIS
        
        # Determine transaction type
        transaction_type = self._kite.TRANSACTION_TYPE_BUY if side == 'buy' else self._kite.TRANSACTION_TYPE_SELL
        
        try:
            self._rate_limit()
            
            order_id = self._kite.place_order(
                variety=self._kite.VARIETY_REGULAR,
                exchange=exchange,
                tradingsymbol=trading_symbol,
                transaction_type=transaction_type,
                quantity=int(amount),
                product=product,
                order_type=order_type,
                price=rate if rate else None,
                validity=self._kite.VALIDITY_DAY,
                tag="freqtrade"
            )
            
            return {
                'id': order_id,
                'info': {'order_id': order_id},
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
            if 'insufficient' in str(e).lower() or 'margin' in str(e).lower():
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
            self._rate_limit()
            
            orders = self._kite.orders()
            
            # Find the specific order
            order = None
            for o in orders:
                if o.get('order_id') == order_id:
                    order = o
                    break
            
            if not order:
                raise InvalidOrderException(f"Order {order_id} not found")
            
            # Map status
            status_map = {
                'COMPLETE': 'closed',
                'REJECTED': 'canceled',
                'CANCELLED': 'canceled',
                'OPEN': 'open',
                'PENDING': 'open',
            }
            
            status = status_map.get(order.get('status', '').upper(), 'open')
            
            return {
                'id': order_id,
                'info': order,
                'timestamp': None,
                'datetime': order.get('order_timestamp'),
                'status': status,
                'symbol': pair,
                'type': order.get('order_type', '').lower(),
                'side': order.get('transaction_type', '').lower(),
                'price': float(order.get('price', 0)),
                'average': float(order.get('average_price', 0)),
                'amount': float(order.get('quantity', 0)),
                'filled': float(order.get('filled_quantity', 0)),
                'remaining': float(order.get('pending_quantity', 0)),
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
            self._rate_limit()
            
            response = self._kite.cancel_order(
                variety=self._kite.VARIETY_REGULAR,
                order_id=order_id
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
            self._rate_limit()
            
            margins = self._kite.margins()
            equity = margins.get('equity', {})
            
            # Extract available cash
            available_cash = float(equity.get('available', {}).get('cash', 0))
            used_margin = float(equity.get('utilised', {}).get('debits', 0))
            
            balance = {
                'INR': {
                    'free': available_cash,
                    'used': used_margin,
                    'total': available_cash + used_margin,
                },
                'info': margins,
                'free': {'INR': available_cash},
                'used': {'INR': used_margin},
                'total': {'INR': available_cash + used_margin},
            }
            
            return balance
            
        except Exception as e:
            raise ExchangeError(f"Failed to fetch balance: {e}")

    def fetch_positions(self) -> List[dict]:
        """
        Fetch current positions.
        
        :return: List of positions
        """
        try:
            self._rate_limit()
            
            positions = self._kite.positions()
            return positions.get('day', []) + positions.get('net', [])
            
        except Exception as e:
            raise ExchangeError(f"Failed to fetch positions: {e}")

    def fetch_option_chain(self, underlying: str, expiry: str = None) -> List[dict]:
        """
        Fetch option chain for an underlying.
        
        :param underlying: Underlying symbol (e.g., 'NIFTY')
        :param expiry: Expiry date (optional)
        :return: List of option contracts
        """
        try:
            # Filter instruments for options of the underlying
            option_contracts = []
            
            for token, instrument in self._instruments.items():
                if (instrument.get('name', '').upper() == underlying.upper() and 
                    instrument.get('instrument_type') in ['CE', 'PE']):
                    
                    if expiry and instrument.get('expiry'):
                        # Filter by expiry if specified
                        if instrument['expiry'].strftime('%Y-%m-%d') != expiry:
                            continue
                    
                    option_contracts.append({
                        'symbol': instrument['tradingsymbol'],
                        'strike': instrument.get('strike', 0),
                        'expiry': instrument.get('expiry'),
                        'option_type': 'CALL' if instrument.get('instrument_type') == 'CE' else 'PUT',
                        'lot_size': instrument.get('lot_size', 1),
                        'instrument_token': token,
                    })
            
            return sorted(option_contracts, key=lambda x: (x['expiry'], x['strike']))
            
        except Exception as e:
            raise ExchangeError(f"Failed to fetch option chain for {underlying}: {e}")

    def set_session_expiry_hook(self, callback):
        """Set callback for session expiry handling"""
        self._session_expiry_callback = callback

    def _check_session_expiry(self):
        """Check if session is about to expire"""
        if self._session_expiry and datetime.now() >= self._session_expiry:
            logger.warning("Kite session expired, re-authentication required")
            if hasattr(self, '_session_expiry_callback'):
                self._session_expiry_callback()

    @property
    def name(self) -> str:
        """Exchange name"""
        return 'Zerodha'
    
    @property
    def id(self) -> str:
        """Exchange ID"""
        return 'zerodha'

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

    def close(self) -> None:
        """Close exchange connections"""
        if self._kws:
            self._kws.close()
