"""
Example Custom Exchange

This is a template showing how to create a custom exchange.
Copy this file and modify it for your exchange.
"""

import logging
from typing import List, Optional

from freqtrade.constants import BuySell
from freqtrade.enums import CandleType
from freqtrade.exceptions import ExchangeError, TemporaryError
from freqtrade.exchange.custom_exchange import CustomExchange
from freqtrade.exchange.exchange_types import OrderBook, Ticker


logger = logging.getLogger(__name__)


class ExampleExchange(CustomExchange):
    """
    Example custom exchange implementation.
    
    This template shows the minimal implementation needed for a custom exchange.
    Replace the placeholder implementations with actual API calls.
    """
    
    # Define exchange capabilities
    _ft_has = {
        **CustomExchange._ft_has,  # Inherit defaults
        "ohlcv_candle_limit": 1000,  # Max candles per request
        "stoploss_on_exchange": False,  # Does your exchange support stop loss orders?
        "tickers_have_bid_ask": True,  # Do your tickers include bid/ask?
    }
    
    @property
    def name(self) -> str:
        """Exchange name - matches config"""
        return 'ExampleExchange'
    
    @property
    def id(self) -> str:
        """Exchange ID - lowercase"""
        return 'exampleexchange'
    
    def __init__(self, config: dict):
        """
        Initialize the exchange.
        
        :param config: Freqtrade configuration
        """
        super().__init__(config)
        
        # Get exchange-specific configuration
        exchange_config = config.get('exchange', {})
        
        self._api_key = exchange_config.get('key', '')
        self._api_secret = exchange_config.get('secret', '')
        self._api_url = exchange_config.get('urls', {}).get('api', 'https://api.example.com')
        
        # Initialize markets from pair whitelist
        pairs = exchange_config.get('pair_whitelist', [])
        self._init_markets_from_pairs(pairs, quote_currency='USD')
        
        # Initialize your API client here
        # self._client = YourAPIClient(self._api_key, self._api_secret)
        
        logger.info(f"{self.name} initialized with {len(self._markets)} pairs")
    
    def exchange_has(self, endpoint: str) -> bool:
        """
        Specify which endpoints your exchange supports.
        
        :param endpoint: Endpoint name
        :return: True if supported
        """
        supported = {
            'fetchOHLCV': True,
            'fetchTicker': True,
            'fetchTickers': False,  # Multiple tickers at once?
            'fetchOrderBook': True,
            'createOrder': True,
            'cancelOrder': True,
            'fetchOrder': True,
            'fetchOrders': True,
            'fetchOpenOrders': True,
            'fetchClosedOrders': True,
            'fetchBalance': True,
            'fetchMyTrades': False,
        }
        return supported.get(endpoint, False)
    
    # ===== Market Data Methods =====
    
    def fetch_ticker(self, pair: str) -> Ticker:
        """
        Fetch ticker data for a trading pair.
        
        :param pair: Trading pair (e.g., 'BTC/USD')
        :return: Ticker data
        """
        try:
            # TODO: Replace with actual API call
            # response = self._client.get_ticker(pair)
            # last_price = response['last']
            
            # Placeholder implementation
            last_price = 50000.0
            
            return self._create_ticker_response(
                pair=pair,
                bid=last_price * 0.999,
                ask=last_price * 1.001,
                last=last_price,
                volume=1000.0
            )
            
        except Exception as e:
            raise ExchangeError(f"Failed to fetch ticker for {pair}: {e}")
    
    def fetch_order_book(self, pair: str, limit: int = 100) -> OrderBook:
        """
        Fetch order book data.
        
        :param pair: Trading pair
        :param limit: Number of orders to fetch
        :return: Order book
        """
        try:
            # TODO: Replace with actual API call
            # response = self._client.get_orderbook(pair, limit)
            # bids = response['bids']
            # asks = response['asks']
            
            # Placeholder implementation
            last_price = 50000.0
            bids = [
                [last_price - 10, 1.0],
                [last_price - 20, 2.0],
                [last_price - 30, 3.0],
            ]
            asks = [
                [last_price + 10, 1.0],
                [last_price + 20, 2.0],
                [last_price + 30, 3.0],
            ]
            
            return self._create_orderbook_response(pair, bids, asks)
            
        except Exception as e:
            raise ExchangeError(f"Failed to fetch order book for {pair}: {e}")
    
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
        :param since: Timestamp in milliseconds
        :param limit: Number of candles
        :param candle_type: Candle type
        :return: List of OHLCV data [[timestamp, open, high, low, close, volume], ...]
        """
        try:
            # TODO: Replace with actual API call
            # response = self._client.get_ohlcv(pair, timeframe, since, limit)
            # return response
            
            # Placeholder implementation
            import time
            current_time = int(time.time() * 1000)
            ohlcv = []
            
            for i in range(limit or 100):
                timestamp = current_time - (i * 60000)  # 1 minute intervals
                open_price = 50000.0 + i
                high_price = open_price + 100
                low_price = open_price - 100
                close_price = open_price + 50
                volume = 10.0
                
                ohlcv.insert(0, [timestamp, open_price, high_price, low_price, close_price, volume])
            
            return ohlcv
            
        except Exception as e:
            raise ExchangeError(f"Failed to fetch OHLCV for {pair}: {e}")
    
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
        """
        Create an order.
        
        :param pair: Trading pair
        :param order_type: Order type ('limit', 'market')
        :param side: Order side ('buy' or 'sell')
        :param amount: Order amount
        :param price: Order price (for limit orders)
        :param params: Additional parameters
        :return: Order data
        """
        try:
            # TODO: Replace with actual API call
            # response = self._client.create_order(
            #     pair, order_type, side, amount, price, params
            # )
            # return response
            
            # Placeholder implementation
            order_id = self._generate_order_id()
            
            logger.info(
                f"Creating {order_type} {side} order for {pair}: "
                f"{amount} @ {price or 'market'}"
            )
            
            return self._create_order_response(
                order_id=order_id,
                pair=pair,
                order_type=order_type,
                side=side,
                amount=amount,
                price=price,
                status='open'
            )
            
        except Exception as e:
            raise ExchangeError(f"Failed to create order: {e}")
    
    def cancel_order(self, order_id: str, pair: str) -> dict:
        """
        Cancel an order.
        
        :param order_id: Order ID
        :param pair: Trading pair
        :return: Order data
        """
        try:
            # TODO: Replace with actual API call
            # response = self._client.cancel_order(order_id, pair)
            # return response
            
            # Placeholder implementation
            logger.info(f"Canceling order {order_id} for {pair}")
            
            return {
                'id': order_id,
                'status': 'canceled',
                'info': {}
            }
            
        except Exception as e:
            raise ExchangeError(f"Failed to cancel order {order_id}: {e}")
    
    def fetch_order(self, order_id: str, pair: str) -> dict:
        """
        Fetch order status.
        
        :param order_id: Order ID
        :param pair: Trading pair
        :return: Order data
        """
        try:
            # TODO: Replace with actual API call
            # response = self._client.get_order(order_id, pair)
            # return response
            
            # Placeholder implementation
            return {
                'id': order_id,
                'symbol': pair,
                'status': 'closed',
                'filled': 1.0,
                'remaining': 0.0,
                'info': {}
            }
            
        except Exception as e:
            raise ExchangeError(f"Failed to fetch order {order_id}: {e}")
    
    def fetch_orders(self, pair: str, since: Optional[int] = None) -> List[dict]:
        """
        Fetch all orders for a pair.
        
        :param pair: Trading pair
        :param since: Timestamp in milliseconds
        :return: List of orders
        """
        try:
            # TODO: Replace with actual API call
            # response = self._client.get_orders(pair, since)
            # return response
            
            # Placeholder implementation
            return []
            
        except Exception as e:
            raise ExchangeError(f"Failed to fetch orders for {pair}: {e}")
    
    def fetch_open_orders(self, pair: Optional[str] = None) -> List[dict]:
        """
        Fetch open orders.
        
        :param pair: Trading pair (None for all pairs)
        :return: List of open orders
        """
        try:
            # TODO: Replace with actual API call
            # response = self._client.get_open_orders(pair)
            # return response
            
            # Placeholder implementation
            return []
            
        except Exception as e:
            raise ExchangeError(f"Failed to fetch open orders: {e}")
    
    # ===== Balance Methods =====
    
    def fetch_balance(self) -> dict:
        """
        Fetch account balance.
        
        :return: Balance data
        """
        try:
            # TODO: Replace with actual API call
            # response = self._client.get_balance()
            # return response
            
            # Placeholder implementation
            return {
                'USD': {
                    'free': 10000.0,
                    'used': 0.0,
                    'total': 10000.0
                },
                'BTC': {
                    'free': 1.0,
                    'used': 0.0,
                    'total': 1.0
                },
                'info': {}
            }
            
        except Exception as e:
            raise ExchangeError(f"Failed to fetch balance: {e}")
    
    # ===== Optional: Market Hours =====
    
    def is_market_open(self) -> bool:
        """
        Check if market is currently open.
        Override this if your exchange has specific trading hours.
        
        :return: True if market is open
        """
        # For 24/7 crypto exchanges, always return True
        return True
        
        # For stock exchanges with trading hours:
        # from datetime import datetime
        # now = datetime.now()
        # if now.weekday() >= 5:  # Weekend
        #     return False
        # market_open = datetime.strptime("09:15", "%H:%M").time()
        # market_close = datetime.strptime("15:30", "%H:%M").time()
        # return market_open <= now.time() <= market_close
