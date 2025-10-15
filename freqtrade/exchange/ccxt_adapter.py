"""
CCXT Exchange Adapter

Wraps CCXT exchanges to work with the ExchangeAdapter interface.
"""

import logging
from typing import Any, Dict, List, Optional

import ccxt

from freqtrade.constants import BuySell
from freqtrade.enums import CandleType
from freqtrade.exceptions import OperationalException
from freqtrade.exchange.exchange_adapter import ExchangeAdapter
from freqtrade.exchange.exchange_types import OrderBook, Ticker


logger = logging.getLogger(__name__)


class CCXTAdapter(ExchangeAdapter):
    """
    Adapter for CCXT-based exchanges.
    
    This wraps any CCXT exchange to work with the ExchangeAdapter interface.
    """
    
    def __init__(self, config: dict):
        """
        Initialize CCXT adapter.
        
        :param config: Freqtrade configuration
        """
        super().__init__(config)
        
        exchange_name = config['exchange']['name']
        exchange_config = config['exchange']
        
        # Initialize CCXT exchange
        try:
            exchange_class = getattr(ccxt, exchange_name)
            
            ccxt_config = {
                'apiKey': exchange_config.get('key'),
                'secret': exchange_config.get('secret'),
                'password': exchange_config.get('password'),
                'uid': exchange_config.get('uid', ''),
            }
            
            # Add custom CCXT config
            ccxt_config.update(exchange_config.get('ccxt_config', {}))
            ccxt_config.update(exchange_config.get('ccxt_sync_config', {}))
            
            self._api = exchange_class(ccxt_config)
            
            logger.info(f"CCXT adapter initialized for {exchange_name}")
            
        except AttributeError:
            raise OperationalException(
                f"Exchange {exchange_name} is not supported by CCXT"
            )
        except Exception as e:
            raise OperationalException(
                f"Failed to initialize CCXT exchange {exchange_name}: {e}"
            )
        
        # Load markets
        self._load_markets()
    
    def _load_markets(self):
        """Load markets from CCXT"""
        try:
            self._markets = self._api.load_markets()
            logger.info(f"Loaded {len(self._markets)} markets from {self.name}")
        except Exception as e:
            logger.warning(f"Failed to load markets: {e}")
            self._markets = {}
    
    @property
    def name(self) -> str:
        """Exchange name"""
        return self._api.name
    
    @property
    def id(self) -> str:
        """Exchange ID"""
        return self._api.id
    
    def validate_config(self, config: dict) -> None:
        """Validate exchange configuration"""
        # CCXT handles most validation internally
        pass
    
    def validate_ordertypes(self, order_types: dict) -> None:
        """Validate order types"""
        # CCXT validates order types on order creation
        pass
    
    def validate_timeframes(self, timeframe: Optional[str]) -> None:
        """Validate timeframes"""
        if timeframe and hasattr(self._api, 'timeframes'):
            if timeframe not in self._api.timeframes:
                raise OperationalException(
                    f"Timeframe {timeframe} not supported by {self.name}"
                )
    
    def exchange_has(self, endpoint: str) -> bool:
        """Check if exchange supports endpoint"""
        return endpoint in self._api.has and self._api.has[endpoint]
    
    # ===== Market Data Methods =====
    
    def fetch_ticker(self, pair: str) -> Ticker:
        """Fetch ticker data"""
        ticker = self._api.fetch_ticker(pair)
        return ticker
    
    def fetch_order_book(self, pair: str, limit: int = 100) -> OrderBook:
        """Fetch order book"""
        order_book = self._api.fetch_order_book(pair, limit)
        return order_book
    
    def fetch_ohlcv(
        self,
        pair: str,
        timeframe: str,
        since: Optional[int] = None,
        limit: Optional[int] = None,
        candle_type: CandleType = CandleType.SPOT
    ) -> List[List]:
        """Fetch OHLCV data"""
        params = {}
        if candle_type != CandleType.SPOT:
            # Handle futures/margin candles if needed
            pass
        
        ohlcv = self._api.fetch_ohlcv(pair, timeframe, since, limit, params)
        return ohlcv
    
    # ===== Trading Methods =====
    
    def create_order(
        self,
        pair: str,
        order_type: str,
        side: BuySell,
        amount: float,
        price: Optional[float] = None,
        params: Optional[dict] = None
    ) -> dict:
        """Create an order"""
        params = params or {}
        order = self._api.create_order(pair, order_type, side, amount, price, params)
        return order
    
    def cancel_order(self, order_id: str, pair: str) -> dict:
        """Cancel an order"""
        return self._api.cancel_order(order_id, pair)
    
    def fetch_order(self, order_id: str, pair: str) -> dict:
        """Fetch order status"""
        return self._api.fetch_order(order_id, pair)
    
    def fetch_orders(self, pair: str, since: Optional[int] = None) -> List[dict]:
        """Fetch all orders"""
        return self._api.fetch_orders(pair, since)
    
    def fetch_open_orders(self, pair: Optional[str] = None) -> List[dict]:
        """Fetch open orders"""
        return self._api.fetch_open_orders(pair)
    
    # ===== Balance Methods =====
    
    def fetch_balance(self) -> dict:
        """Fetch account balance"""
        return self._api.fetch_balance()
    
    def get_balances(self) -> dict:
        """Get account balances"""
        return self.fetch_balance()
    
    # ===== Fee and Limits Methods =====
    
    def get_fee(
        self,
        symbol: str = '',
        type: str = '',
        side: str = '',
        amount: float = 1,
        price: float = 1,
        taker_or_maker: str = 'maker'
    ) -> float:
        """Get trading fee"""
        if symbol and symbol in self._markets:
            market = self._markets[symbol]
            if taker_or_maker == 'maker':
                return market.get('maker', 0.001)
            else:
                return market.get('taker', 0.001)
        return 0.001  # Default 0.1%
    
    def get_min_pair_stake_amount(
        self,
        pair: str,
        price: float,
        stoploss: float,
        leverage: float = 1.0
    ) -> Optional[float]:
        """Get minimum stake amount"""
        if pair in self._markets:
            market = self._markets[pair]
            limits = market.get('limits', {})
            cost_min = limits.get('cost', {}).get('min')
            amount_min = limits.get('amount', {}).get('min')
            
            if cost_min:
                return cost_min
            elif amount_min:
                return amount_min * price
        
        return 10.0  # Default minimum
    
    def get_max_pair_stake_amount(
        self,
        pair: str,
        price: float,
        leverage: float = 1.0
    ) -> float:
        """Get maximum stake amount"""
        if pair in self._markets:
            market = self._markets[pair]
            limits = market.get('limits', {})
            cost_max = limits.get('cost', {}).get('max')
            
            if cost_max:
                return cost_max
        
        return float('inf')  # No limit by default
