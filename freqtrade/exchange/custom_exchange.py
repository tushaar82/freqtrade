"""
Custom Exchange Base Class

Base class for implementing custom (non-CCXT) exchanges with sensible defaults.
"""

import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Optional
from threading import Lock

from cachetools import TTLCache

from freqtrade.constants import BuySell
from freqtrade.enums import CandleType, MarginMode, TradingMode
from freqtrade.exchange.exchange_adapter import ExchangeAdapter
from freqtrade.exchange.exchange_types import FtHas, OrderBook, Ticker


logger = logging.getLogger(__name__)


class CustomExchange(ExchangeAdapter):
    """
    Base class for custom exchanges.
    
    Provides sensible defaults and utility methods to make implementing
    custom exchanges easier. Inherit from this and override only what you need.
    """
    
    # Exchange capabilities - override in subclass
    _ft_has: FtHas = {
        "ohlcv_candle_limit": 500,
        "ohlcv_has_history": True,
        "ohlcv_partial_candle": True,
        "ohlcv_require_since": False,
        "order_time_in_force": ["GTC", "IOC", "PO"],
        "stoploss_on_exchange": False,
        "stop_price_param": "stopPrice",
        "stop_price_prop": "stopPrice",
        "stoploss_order_types": {"limit": "limit", "market": "market"},
        "tickers_have_bid_ask": True,
        "tickers_have_price": True,
        "trades_pagination": "id",
        "trades_pagination_arg": "since",
        "ws_enabled": False,
        "always_require_api_keys": False,
    }
    
    def __init__(self, config: dict):
        """
        Initialize custom exchange.
        
        :param config: Freqtrade configuration
        """
        super().__init__(config)
        
        # Initialize required attributes for Freqtrade compatibility
        self._api = None  # No CCXT API
        self._api_async = None
        self._ws_async = None
        self._exchange_ws = None
        self._trading_fees = {}
        self._leverage_tiers = {}
        self._loop_lock = Lock()
        self._cache_lock = Lock()
        
        # Caching
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
        self._ccxt_config = {}
        self._ccxt_params = {}
        self.log_responses = False
        self._ohlcv_partial_candle = self._ft_has.get('ohlcv_partial_candle', True)
        self.liquidation_buffer = 0.05
        
        # Trading mode
        self.trading_mode = TradingMode.SPOT
        self.margin_mode = MarginMode.NONE
        self._supported_trading_mode_margin_pairs = [(TradingMode.SPOT, MarginMode.NONE)]
        
        logger.info(f"Custom exchange {self.name} initialized")
    
    # ===== Default Implementations =====
    
    def validate_config(self, config: dict) -> None:
        """Validate configuration - override if needed"""
        pass
    
    def validate_ordertypes(self, order_types: dict) -> None:
        """Validate order types - override if needed"""
        pass
    
    def validate_timeframes(self, timeframe: Optional[str]) -> None:
        """Validate timeframes - override if needed"""
        pass
    
    def exchange_has(self, endpoint: str) -> bool:
        """
        Check if exchange supports endpoint.
        Override to specify which endpoints your exchange supports.
        """
        return False
    
    def get_balances(self) -> dict:
        """Get balances - calls fetch_balance by default"""
        return self.fetch_balance()
    
    def get_fee(
        self,
        symbol: str = '',
        type: str = '',
        side: str = '',
        amount: float = 1,
        price: float = 1,
        taker_or_maker: str = 'maker'
    ) -> float:
        """Get trading fee - override to return actual fees"""
        return 0.001  # Default 0.1%
    
    def get_min_pair_stake_amount(
        self,
        pair: str,
        price: float,
        stoploss: float,
        leverage: float = 1.0
    ) -> Optional[float]:
        """Get minimum stake amount - override for actual limits"""
        return 1.0
    
    def get_max_pair_stake_amount(
        self,
        pair: str,
        price: float,
        leverage: float = 1.0
    ) -> float:
        """Get maximum stake amount - override for actual limits"""
        return float('inf')
    
    # ===== Utility Methods =====
    
    def _init_markets_from_pairs(self, pairs: List[str], quote_currency: str = 'INR'):
        """
        Initialize markets from a list of pairs.
        Useful for exchanges that don't have a markets API.
        
        :param pairs: List of trading pairs (e.g., ['RELIANCE/INR', 'TCS/INR'])
        :param quote_currency: Default quote currency
        """
        for pair in pairs:
            if '/' in pair:
                base, quote = pair.split('/')
            else:
                base = pair
                quote = quote_currency
                pair = f"{base}/{quote}"
            
            self._markets[pair] = {
                'id': pair.replace('/', ''),
                'symbol': pair,
                'base': base,
                'quote': quote,
                'active': True,
                'type': 'spot',
                'spot': True,
                'future': False,
                'swap': False,
                'option': False,
                'contract': False,
                'precision': {
                    'amount': 8,
                    'price': 2,
                },
                'limits': {
                    'amount': {'min': 0.00000001, 'max': 1000000},
                    'price': {'min': 0.01, 'max': 1000000},
                    'cost': {'min': 1.0, 'max': None},
                },
                'info': {},
            }
    
    def _generate_order_id(self) -> str:
        """Generate a unique order ID"""
        timestamp = int(datetime.now().timestamp() * 1000)
        random_part = random.randint(1000, 9999)
        return f"{self.id}_{timestamp}_{random_part}"
    
    def _create_order_response(
        self,
        order_id: str,
        pair: str,
        order_type: str,
        side: BuySell,
        amount: float,
        price: Optional[float],
        status: str = 'open'
    ) -> dict:
        """
        Create a standard order response dictionary.
        
        :param order_id: Order ID
        :param pair: Trading pair
        :param order_type: Order type
        :param side: Order side
        :param amount: Order amount
        :param price: Order price
        :param status: Order status
        :return: Order dictionary
        """
        timestamp = int(datetime.now().timestamp() * 1000)
        
        return {
            'id': order_id,
            'clientOrderId': None,
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp / 1000).isoformat(),
            'lastTradeTimestamp': None,
            'symbol': pair,
            'type': order_type,
            'side': side,
            'price': price,
            'amount': amount,
            'cost': (price * amount) if price else None,
            'average': None,
            'filled': 0.0,
            'remaining': amount,
            'status': status,
            'fee': None,
            'trades': [],
            'info': {},
        }
    
    def _create_ticker_response(
        self,
        pair: str,
        bid: float,
        ask: float,
        last: float,
        volume: float = 0.0
    ) -> Ticker:
        """
        Create a standard ticker response.
        
        :param pair: Trading pair
        :param bid: Bid price
        :param ask: Ask price
        :param last: Last price
        :param volume: 24h volume
        :return: Ticker dictionary
        """
        timestamp = int(datetime.now().timestamp() * 1000)
        
        return {
            'symbol': pair,
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp / 1000).isoformat(),
            'high': last * 1.05,
            'low': last * 0.95,
            'bid': bid,
            'bidVolume': None,
            'ask': ask,
            'askVolume': None,
            'vwap': last,
            'open': last,
            'close': last,
            'last': last,
            'previousClose': None,
            'change': None,
            'percentage': None,
            'average': last,
            'baseVolume': volume,
            'quoteVolume': volume * last,
            'info': {},
        }
    
    def _create_orderbook_response(
        self,
        pair: str,
        bids: List[List[float]],
        asks: List[List[float]]
    ) -> OrderBook:
        """
        Create a standard order book response.
        
        :param pair: Trading pair
        :param bids: List of [price, amount] bids
        :param asks: List of [price, amount] asks
        :return: Order book dictionary
        """
        timestamp = int(datetime.now().timestamp() * 1000)
        
        return {
            'symbol': pair,
            'bids': bids,
            'asks': asks,
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp / 1000).isoformat(),
            'nonce': None,
        }
