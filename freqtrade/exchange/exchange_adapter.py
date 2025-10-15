"""
Exchange Adapter Interface

This module defines the adapter pattern for exchanges, allowing both CCXT-based
and custom exchange implementations to coexist seamlessly.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from freqtrade.constants import BuySell
from freqtrade.enums import CandleType
from freqtrade.exchange.exchange_types import OrderBook, Ticker


class ExchangeAdapter(ABC):
    """
    Abstract base class for exchange adapters.
    
    All exchanges (CCXT-based or custom) must implement this interface.
    This ensures a consistent API regardless of the underlying implementation.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the exchange adapter.
        
        :param config: Freqtrade configuration dictionary
        """
        self._config = config
        self._markets: Dict[str, Any] = {}
    
    # ===== Required Properties =====
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Exchange name (e.g., 'Binance', 'Paperbroker')"""
        pass
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Exchange ID (lowercase, e.g., 'binance', 'paperbroker')"""
        pass
    
    @property
    def markets(self) -> Dict[str, Any]:
        """Get available markets"""
        return self._markets
    
    # ===== Required Methods =====
    
    @abstractmethod
    def validate_config(self, config: dict) -> None:
        """
        Validate exchange configuration.
        
        :param config: Configuration to validate
        :raises: ConfigurationError if config is invalid
        """
        pass
    
    @abstractmethod
    def validate_ordertypes(self, order_types: dict) -> None:
        """
        Validate order types.
        
        :param order_types: Order types configuration
        :raises: OperationalException if order types are invalid
        """
        pass
    
    @abstractmethod
    def validate_timeframes(self, timeframe: Optional[str]) -> None:
        """
        Validate timeframes.
        
        :param timeframe: Timeframe to validate
        :raises: OperationalException if timeframe is invalid
        """
        pass
    
    @abstractmethod
    def exchange_has(self, endpoint: str) -> bool:
        """
        Check if exchange supports a specific endpoint.
        
        :param endpoint: Endpoint to check (e.g., 'fetchOHLCV', 'createOrder')
        :return: True if supported
        """
        pass
    
    # ===== Market Data Methods =====
    
    @abstractmethod
    def fetch_ticker(self, pair: str) -> Ticker:
        """
        Fetch ticker data for a trading pair.
        
        :param pair: Trading pair (e.g., 'BTC/USDT', 'RELIANCE/INR')
        :return: Ticker data
        """
        pass
    
    @abstractmethod
    def fetch_order_book(self, pair: str, limit: int = 100) -> OrderBook:
        """
        Fetch order book data.
        
        :param pair: Trading pair
        :param limit: Number of orders to fetch
        :return: Order book data
        """
        pass
    
    @abstractmethod
    def fetch_ohlcv(
        self,
        pair: str,
        timeframe: str,
        since: Optional[int] = None,
        limit: Optional[int] = None,
        candle_type: CandleType = CandleType.SPOT
    ) -> List[List]:
        """
        Fetch OHLCV (candlestick) data.
        
        :param pair: Trading pair
        :param timeframe: Timeframe (e.g., '1m', '5m', '1h', '1d')
        :param since: Timestamp in milliseconds to fetch from
        :param limit: Number of candles to fetch
        :param candle_type: Type of candle (spot, futures, etc.)
        :return: List of OHLCV data [[timestamp, open, high, low, close, volume], ...]
        """
        pass
    
    # ===== Trading Methods =====
    
    @abstractmethod
    def create_order(
        self,
        pair: str,
        order_type: str,
        side: BuySell,
        amount: float,
        price: Optional[float] = None,
        params: Optional[dict] = None
    ) -> dict:
        """
        Create an order.
        
        :param pair: Trading pair
        :param order_type: Order type ('limit', 'market', etc.)
        :param side: Order side ('buy' or 'sell')
        :param amount: Order amount
        :param price: Order price (for limit orders)
        :param params: Additional parameters
        :return: Order data
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str, pair: str) -> dict:
        """
        Cancel an order.
        
        :param order_id: Order ID
        :param pair: Trading pair
        :return: Order data
        """
        pass
    
    @abstractmethod
    def fetch_order(self, order_id: str, pair: str) -> dict:
        """
        Fetch order status.
        
        :param order_id: Order ID
        :param pair: Trading pair
        :return: Order data
        """
        pass
    
    @abstractmethod
    def fetch_orders(self, pair: str, since: Optional[int] = None) -> List[dict]:
        """
        Fetch all orders for a pair.
        
        :param pair: Trading pair
        :param since: Timestamp in milliseconds
        :return: List of orders
        """
        pass
    
    @abstractmethod
    def fetch_open_orders(self, pair: Optional[str] = None) -> List[dict]:
        """
        Fetch open orders.
        
        :param pair: Trading pair (None for all pairs)
        :return: List of open orders
        """
        pass
    
    # ===== Balance Methods =====
    
    @abstractmethod
    def fetch_balance(self) -> dict:
        """
        Fetch account balance.
        
        :return: Balance data
        """
        pass
    
    @abstractmethod
    def get_balances(self) -> dict:
        """
        Get account balances (convenience method).
        
        :return: Balance data
        """
        pass
    
    # ===== Fee and Limits Methods =====
    
    @abstractmethod
    def get_fee(
        self,
        symbol: str = '',
        type: str = '',
        side: str = '',
        amount: float = 1,
        price: float = 1,
        taker_or_maker: str = 'maker'
    ) -> float:
        """
        Get trading fee.
        
        :param symbol: Trading pair
        :param type: Order type
        :param side: Order side
        :param amount: Order amount
        :param price: Order price
        :param taker_or_maker: 'taker' or 'maker'
        :return: Fee as decimal (e.g., 0.001 for 0.1%)
        """
        pass
    
    @abstractmethod
    def get_min_pair_stake_amount(
        self,
        pair: str,
        price: float,
        stoploss: float,
        leverage: float = 1.0
    ) -> Optional[float]:
        """
        Get minimum stake amount for a pair.
        
        :param pair: Trading pair
        :param price: Current price
        :param stoploss: Stop loss percentage
        :param leverage: Leverage
        :return: Minimum stake amount
        """
        pass
    
    @abstractmethod
    def get_max_pair_stake_amount(
        self,
        pair: str,
        price: float,
        leverage: float = 1.0
    ) -> float:
        """
        Get maximum stake amount for a pair.
        
        :param pair: Trading pair
        :param price: Current price
        :param leverage: Leverage
        :return: Maximum stake amount
        """
        pass
    
    # ===== Markets Methods =====
    
    def get_markets(
        self,
        base_currencies: Optional[List[str]] = None,
        quote_currencies: Optional[List[str]] = None,
        spot_only: bool = False,
        margin_only: bool = False,
        futures_only: bool = False,
        tradable_only: bool = True,
        active_only: bool = False
    ) -> Dict[str, Any]:
        """
        Get filtered markets.
        
        :param base_currencies: Filter by base currencies
        :param quote_currencies: Filter by quote currencies
        :param spot_only: Only spot markets
        :param margin_only: Only margin markets
        :param futures_only: Only futures markets
        :param tradable_only: Only tradable markets
        :param active_only: Only active markets
        :return: Filtered markets dictionary
        """
        markets = self.markets.copy()
        
        if tradable_only:
            markets = {k: v for k, v in markets.items() if v.get('active', True)}
        
        if base_currencies:
            markets = {k: v for k, v in markets.items() if v.get('base') in base_currencies}
        
        if quote_currencies:
            markets = {k: v for k, v in markets.items() if v.get('quote') in quote_currencies}
        
        if spot_only:
            markets = {k: v for k, v in markets.items() if v.get('spot', False)}
        
        if futures_only:
            markets = {k: v for k, v in markets.items() if v.get('future', False)}
        
        return markets
    
    # ===== Utility Methods =====
    
    def is_market_open(self) -> bool:
        """
        Check if market is currently open.
        Override this for exchanges with specific market hours (e.g., NSE).
        
        :return: True if market is open (default: always True for 24/7 crypto)
        """
        return True
