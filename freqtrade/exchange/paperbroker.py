"""Paper Broker - Virtual trading exchange for testing and simulation"""

import csv
import logging
import os
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from pandas import DataFrame

from freqtrade.constants import BuySell
from freqtrade.enums import CandleType, MarginMode, TradingMode
from freqtrade.exceptions import ExchangeError, InsufficientFundsError, InvalidOrderException
from freqtrade.exchange import Exchange
from freqtrade.exchange.exchange_types import FtHas, OrderBook, Ticker
from freqtrade.exchange.symbol_mapper import get_symbol_mapper


logger = logging.getLogger(__name__)


class Paperbroker(Exchange):
    """
    Paper Broker - Virtual trading exchange for simulation and testing.
    
    This is a simulated exchange that:
    - Doesn't require real API credentials
    - Simulates order execution with realistic slippage
    - Maintains virtual account balance
    - Generates realistic market data
    - Perfect for strategy testing and development
    
    Features:
    - No real money involved
    - Configurable initial balance
    - Simulated order fills with slippage
    - Market data simulation or proxy from real exchange
    - Complete trade history tracking
    """

    _ft_has: FtHas = {
        "ohlcv_candle_limit": 500,
        "ohlcv_has_history": True,
        "ohlcv_partial_candle": True,
        "ohlcv_require_since": False,
        "order_time_in_force": ["GTC", "IOC", "PO"],
        "stoploss_on_exchange": False,
        "trades_pagination": "id",
        "trades_pagination_arg": "since",
        "tickers_have_bid_ask": True,
        "tickers_have_price": True,
        "ws_enabled": False,  # Paper trading doesn't need websocket
        "always_require_api_keys": False,  # No real API keys needed
        "l2_limit_range": [10, 20, 50, 100],  # Supported orderbook depth levels
        "l2_limit_range_required": False,  # Orderbook depth limit not required
        "l2_limit_upper": 100,  # Maximum orderbook depth
        "proxy_coin_mapping": {},  # No proxy coin mapping needed for Paper Broker
    }

    _supported_trading_mode_margin_pairs = [
        (TradingMode.SPOT, MarginMode.NONE),
    ]

    def __init__(self, config, validate: bool = True, exchange_config=None, load_leverage_tiers: bool = False, **kwargs):
        """
        Initialize Paper Broker.
        
        Configuration:
        - initial_balance: Starting balance (default: 100000)
        - slippage_percent: Simulated slippage (default: 0.05%)
        - commission_percent: Trading commission (default: 0.1%)
        - fill_probability: Probability of order fill (default: 0.95)
        - proxy_exchange: Real exchange to get data from (optional)
        """
        # Initialize minimal Exchange attributes without CCXT
        from threading import Lock
        from cachetools import TTLCache
        
        self._api = None  # No CCXT API for Paper Broker
        self._api_async = None
        self._ws_async = None
        self._exchange_ws = None
        self._markets = {}
        self._trading_fees = {}
        self._leverage_tiers = {}
        self._loop_lock = Lock()
        self.loop = None  # No async loop for Paper Broker
        self._config = config
        self._cache_lock = Lock()
        self._fetch_tickers_cache = TTLCache(maxsize=4, ttl=60 * 10)
        self._exit_rate_cache = TTLCache(maxsize=100, ttl=300)
        self._entry_rate_cache = TTLCache(maxsize=100, ttl=300)
        self._klines = {}
        self._expiring_candle_cache = {}
        self._trades = {}
        self._dry_run_open_orders = {}
        self._ohlcv_candle_cache = {}  # Cache for OHLCV data
        
        # Additional Exchange attributes
        self._pairs_last_refresh_time = {}
        self._last_markets_refresh = 0
        self._ft_has = self._ft_has.copy()  # Use the class-level _ft_has
        self.log_responses = False
        self._ohlcv_partial_candle = self._ft_has.get('ohlcv_partial_candle', True)
        self.liquidation_buffer = 0.05
        self.required_candle_call_count = 1  # Number of candle calls needed
        
        # Set trading mode
        self.trading_mode = TradingMode.SPOT
        self.margin_mode = MarginMode.NONE
        self._supported_trading_mode_margin_pairs = [(TradingMode.SPOT, MarginMode.NONE)]
        
        # Paper broker configuration
        exchange_config = config.get('exchange', {})
        self._initial_balance = exchange_config.get('initial_balance', 100000.0)
        self._slippage_percent = exchange_config.get('slippage_percent', 0.05)
        self._commission_percent = exchange_config.get('commission_percent', 0.1)
        self._fill_probability = exchange_config.get('fill_probability', 0.95)
        self._proxy_exchange = exchange_config.get('proxy_exchange', None)
        
        # Virtual account state
        self._balance = {
            'INR': {
                'free': self._initial_balance,
                'used': 0.0,
                'total': self._initial_balance
            }
        }
        
        # Order tracking
        self._orders = {}  # order_id -> order_data
        self._open_orders = {}  # order_id -> order_data
        self._filled_orders = {}  # order_id -> order_data
        self._positions = {}  # pair -> position_data
        
        # Trade history
        self._trade_history = []
        
        # Price cache for simulation
        self._price_cache = {}  # pair -> last_price
        
        # CSV data for realistic simulation
        self._csv_data = {}  # pair -> DataFrame with OHLCV data
        self._csv_data_index = {}  # pair -> current playback index
        self._use_csv_data = False  # Flag to enable CSV data mode
        self._current_csv_time = {}  # pair -> current simulation timestamp (for consistent pricing)
        
        # Initialize proxy exchange if specified
        self._proxy = None
        if self._proxy_exchange:
            self._init_proxy_exchange()
        
        # Initialize markets from pair_whitelist
        self._init_markets()
        
        # Load CSV data if available
        self._load_csv_data()
        
        # Note: Position restore happens later in startup() when database is ready
        self._positions_restored = False
        
        # Initialize symbol mapper
        symbol_mapping_path = config.get('exchange', {}).get('symbol_mapping_file')
        self._symbol_mapper = get_symbol_mapper(symbol_mapping_path)
        
        logger.info(
            f"Paper Broker initialized with balance: {self._initial_balance} "
            f"(slippage: {self._slippage_percent}%, commission: {self._commission_percent}%)"
        )

    def _init_proxy_exchange(self):
        """Initialize proxy exchange for real market data"""
        try:
            # Import the proxy exchange
            # This would be used to get real market data
            logger.info(f"Proxy exchange {self._proxy_exchange} configured for market data")
            # In production, initialize actual proxy exchange here
        except Exception as e:
            logger.warning(f"Failed to initialize proxy exchange: {e}")

    def _init_markets(self):
        """Initialize markets dictionary from config"""
        pair_whitelist = self._config.get('exchange', {}).get('pair_whitelist', [])
        
        for pair in pair_whitelist:
            # Create market entry for each pair
            self._markets[pair] = {
                'id': pair.replace('/', ''),
                'symbol': pair,
                'base': pair.split('/')[0],
                'quote': pair.split('/')[1] if '/' in pair else 'INR',
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

    def _load_csv_data(self):
        """Load OHLCV data from CSV files in user_data/raw_data directory"""
        try:
            # Get user_data directory path
            user_data_dir = self._config.get('user_data_dir', 'user_data')
            raw_data_dir = Path(user_data_dir) / 'raw_data'
            
            if not raw_data_dir.exists():
                logger.info("No raw_data directory found, using simulated data")
                return
            
            # Find all CSV files
            csv_files = list(raw_data_dir.glob('*.csv'))
            
            if not csv_files:
                logger.info("No CSV files found in raw_data, using simulated data")
                return
            
            logger.info(f"Loading {len(csv_files)} CSV file(s) from {raw_data_dir}")
            
            for csv_file in csv_files:
                try:
                    # Extract symbol from filename (e.g., BANK_minute.csv -> BANK/INR)
                    symbol_name = csv_file.stem.replace('_minute', '').replace('_1m', '').upper()
                    pair = f"{symbol_name}/INR"
                    
                    # Load CSV data
                    logger.info(f"Loading {csv_file.name}...")
                    df = pd.read_csv(
                        csv_file,
                        parse_dates=['datetime'],
                        date_parser=lambda x: pd.to_datetime(x)
                    )
                    
                    # Validate required columns
                    required_cols = ['datetime', 'open', 'high', 'low', 'close', 'volume']
                    if not all(col in df.columns for col in required_cols):
                        logger.warning(f"Skipping {csv_file.name}: missing required columns")
                        continue
                    
                    # Convert to millisecond timestamps
                    # Ensure datetime is timezone-aware and convert to milliseconds
                    if df['datetime'].dt.tz is None:
                        df['datetime'] = df['datetime'].dt.tz_localize('UTC')
                    df['timestamp'] = (df['datetime'].astype(int) // 10**6).astype(int)
                    
                    # Store data
                    self._csv_data[pair] = df
                    # Start index at a reasonable position (e.g., 500 candles in) to allow backfill
                    # This ensures we have data to return when fetch_ohlcv is called
                    self._csv_data_index[pair] = min(500, len(df))
                    
                    # Initialize price cache and current time with LATEST price (for live trading simulation)
                    # This ensures ticker price matches the most recent candle in charts
                    if len(df) > 0:
                        last_idx = len(df) - 1
                        self._price_cache[pair] = float(df.iloc[last_idx]['close'])
                        self._current_csv_time[pair] = df.iloc[last_idx]['timestamp']
                    
                    logger.info(
                        f"Loaded {len(df)} candles for {pair} "
                        f"(from {df.iloc[0]['datetime']} to {df.iloc[-1]['datetime']})"
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to load {csv_file.name}: {e}")
                    continue
            
            if self._csv_data:
                self._use_csv_data = True
                logger.info(
                    f"✅ CSV data mode enabled with {len(self._csv_data)} pair(s): "
                    f"{', '.join(self._csv_data.keys())}"
                )
            else:
                logger.info("No CSV data loaded, using simulated data")
                
        except Exception as e:
            logger.error(f"Error loading CSV data: {e}")
            logger.info("Falling back to simulated data")

    def _restore_positions_from_db(self):
        """Restore positions from database on restart to sync wallet state."""
        try:
            # Import Trade model to query database
            from freqtrade.persistence import Trade
            
            # Check if Trade session is available
            if not hasattr(Trade, 'session') or Trade.session is None:
                logger.debug("Trade session not yet initialized, skipping position restore")
                return
            
            # Get all open trades from database
            open_trades = Trade.get_open_trades()
            
            if not open_trades:
                logger.debug("No open trades found in database")
                return
            
            logger.info(f"Restoring {len(open_trades)} positions from database...")
            
            # Restore each position
            for trade in open_trades:
                pair = trade.pair
                amount = trade.amount
                
                # Initialize position if not exists
                if pair not in self._positions:
                    self._positions[pair] = {'amount': 0, 'cost': 0}
                
                # Add to position
                self._positions[pair]['amount'] += amount
                self._positions[pair]['cost'] += (trade.open_rate * amount)
                
                logger.debug(
                    f"Restored position: {pair} = {amount} units @ {trade.open_rate}"
                )
            
            # Update balance to reflect used capital
            total_used = sum(pos['cost'] for pos in self._positions.values())
            if total_used > 0:
                self._balance['INR']['used'] = total_used
                self._balance['INR']['free'] = max(0, self._initial_balance - total_used)
                logger.info(
                    f"Restored balance: Free={self._balance['INR']['free']:.2f}, "
                    f"Used={self._balance['INR']['used']:.2f}"
                )
        
        except ImportError:
            logger.warning("Could not import Trade model for position restore")
        except Exception as e:
            logger.error(f"Error restoring positions from database: {e}")

    def _simulate_price(self, pair: str, base_price: float | None = None) -> float:
        """
        Simulate a realistic price for a pair.
        If CSV data available, use the LATEST (most recent) price to match chart data.
        This ensures ticker price matches the rightmost candle in FreqUI charts.
        
        :param pair: Trading pair
        :param base_price: Base price to simulate from
        :return: Simulated/real price
        """
        # Use CSV data if available - return LATEST price for consistency with charts
        if self._use_csv_data and pair in self._csv_data:
            df = self._csv_data[pair]
            
            # Always use the LATEST candle for current price
            # This ensures ticker matches the most recent data shown in charts
            if len(df) > 0:
                last_idx = len(df) - 1
                latest_price = float(df.iloc[last_idx]['close'])
                self._price_cache[pair] = latest_price
                return latest_price
            else:
                # Shouldn't happen, but fallback
                return self._price_cache.get(pair, 100.0)
        
        # Fallback to random simulation (when no CSV data)
        if pair in self._price_cache:
            last_price = self._price_cache[pair]
            # Random walk with 0.5% max movement
            movement = random.uniform(-0.005, 0.005)
            new_price = last_price * (1 + movement)
        else:
            # First time, use base price or random
            new_price = base_price if base_price else random.uniform(100, 1000)
        
        self._price_cache[pair] = new_price
        return new_price

    def _apply_slippage(self, price: float, side: BuySell) -> float:
        """
        Apply slippage to a price.
        
        :param price: Original price
        :param side: Order side
        :return: Price with slippage
        """
        slippage = price * (self._slippage_percent / 100)
        
        if side == 'buy':
            return price + slippage  # Pay more when buying
        else:
            return price - slippage  # Receive less when selling

    def _calculate_commission(self, amount: float) -> float:
        """
        Calculate trading commission.
        
        :param amount: Trade amount
        :return: Commission amount
        """
        return amount * (self._commission_percent / 100)

    def fetch_ticker(self, pair: str) -> Ticker:
        """
        Fetch simulated ticker data for a pair.
        
        :param pair: Freqtrade pair
        :return: Ticker data
        """
        # Simulate price
        last_price = self._simulate_price(pair)
        
        # Generate realistic bid/ask spread (0.1%)
        spread = last_price * 0.001
        
        return {
            'symbol': pair,
            'ask': last_price + (spread / 2),
            'bid': last_price - (spread / 2),
            'last': last_price,
            'askVolume': random.uniform(100, 10000),
            'bidVolume': random.uniform(100, 10000),
            'quoteVolume': random.uniform(1000000, 10000000),
            'baseVolume': random.uniform(10000, 100000),
            'percentage': random.uniform(-5, 5),
        }
    
    def fetch_tickers(self, symbols: list[str] | None = None, params: dict | None = None) -> dict:
        """
        Fetch multiple tickers at once.
        
        :param symbols: List of symbols to fetch (if None, fetch all pairs)
        :param params: Additional parameters
        :return: Dictionary of tickers
        """
        tickers = {}
        pairs_to_fetch = symbols if symbols else list(self._markets.keys())
        
        for pair in pairs_to_fetch:
            tickers[pair] = self.fetch_ticker(pair)
        
        return tickers
    
    def get_tickers(self, symbols: list[str] | None = None, cached: bool = False) -> dict:
        """
        Override base Exchange.get_tickers() to use our fetch_tickers() instead of self._api
        
        :param symbols: List of symbols to fetch
        :param cached: Use cached tickers (for PaperBroker, always fetch fresh)
        :return: Dictionary of tickers
        """
        return self.fetch_tickers(symbols=symbols)

    def fetch_order_book(self, pair: str, limit: int = 5) -> OrderBook:
        """
        Fetch simulated order book for a pair.
        
        :param pair: Freqtrade pair
        :param limit: Depth limit
        :return: Order book data
        """
        last_price = self._simulate_price(pair)
        
        # Generate realistic order book
        asks = []
        bids = []
        
        for i in range(limit):
            # Asks - progressively higher prices
            ask_price = last_price * (1 + (i * 0.001))
            ask_qty = random.uniform(10, 1000)
            asks.append((ask_price, ask_qty))
            
            # Bids - progressively lower prices
            bid_price = last_price * (1 - (i * 0.001))
            bid_qty = random.uniform(10, 1000)
            bids.append((bid_price, bid_qty))
        
        return {
            'symbol': pair,
            'bids': bids,
            'asks': asks,
            'timestamp': int(datetime.now().timestamp() * 1000),
            'datetime': datetime.now().isoformat(),
            'nonce': None,
        }
    
    def fetch_l2_order_book(self, pair: str, limit: int = 20) -> OrderBook:
        """
        Fetch L2 order book (same as fetch_order_book for Paper Broker).
        
        :param pair: Freqtrade pair
        :param limit: Depth limit
        :return: Order book data
        """
        return self.fetch_order_book(pair, limit)

    def fetch_ohlcv(
        self,
        pair: str,
        timeframe: str = '5m',
        since: int | None = None,
        limit: int | None = None,
        candle_type: CandleType = CandleType.SPOT,
    ) -> list:
        """
        Fetch OHLCV data. Uses CSV data if available, otherwise simulates.
        
        :param pair: Freqtrade pair
        :param timeframe: Timeframe
        :param since: Timestamp in milliseconds
        :param limit: Number of candles
        :param candle_type: Candle type
        :return: List of OHLCV data
        """
        # Use CSV data if available
        if self._use_csv_data and pair in self._csv_data:
            return self._fetch_ohlcv_from_csv(pair, timeframe, since, limit)
        
        # If proxy exchange is configured, try to use real data
        if self._proxy:
            try:
                return self._proxy.fetch_ohlcv(pair, timeframe, since, limit, candle_type)
            except Exception as e:
                logger.warning(f"Failed to fetch from proxy: {e}, using simulation")
        
        # Generate simulated candles
        limit = limit or 100
        
        # Convert timeframe to minutes
        timeframe_minutes = {
            '1m': 1, '3m': 3, '5m': 5, '10m': 10,
            '15m': 15, '30m': 30, '1h': 60, '1d': 1440
        }.get(timeframe, 5)
        
        # Start time
        if since:
            start_time = datetime.fromtimestamp(since / 1000)
        else:
            start_time = datetime.now() - timedelta(minutes=limit * timeframe_minutes)
        
        # Generate candles
        ohlcv = []
        base_price = self._simulate_price(pair)
        
        for i in range(limit):
            timestamp = start_time + timedelta(minutes=i * timeframe_minutes)
            timestamp_ms = int(timestamp.timestamp() * 1000)
            
            # Simulate OHLCV with random walk
            open_price = base_price
            close_price = base_price * (1 + random.uniform(-0.02, 0.02))
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
            volume = random.uniform(1000, 100000)
            
            ohlcv.append([
                timestamp_ms,
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            ])
            
            # Update base price for next candle
            base_price = close_price
        
        # Update price cache
        self._price_cache[pair] = base_price
        
        return ohlcv
    
    def _fetch_ohlcv_from_csv(self, pair: str, timeframe: str, since: int | None, limit: int | None) -> list:
        """
        Fetch OHLCV data from loaded CSV files.
        
        :param pair: Trading pair
        :param timeframe: Requested timeframe
        :param since: Start timestamp in milliseconds
        :param limit: Number of candles to return
        :return: List of OHLCV data [[timestamp, open, high, low, close, volume], ...]
        """
        if pair not in self._csv_data:
            return []
        
        df = self._csv_data[pair].copy()
        limit = limit or 100
        
        # If 'since' is provided, filter data from that timestamp
        if since:
            # Filter dataframe to only include candles >= since
            df = df[df['timestamp'] >= since]
            
            # Return up to 'limit' candles from the filtered data
            candle_slice = df.iloc[:limit]
        else:
            # No 'since' provided - return the most recent 'limit' candles
            # This is what FreqUI and backtesting expect
            candle_slice = df.iloc[-limit:]
        
        # If we need to resample to different timeframe
        if timeframe != '1m':
            candle_slice = self._resample_candles(candle_slice, timeframe)
        
        # Convert to OHLCV list format
        # Format: [timestamp_ms, open, high, low, close, volume]
        ohlcv = []
        for _, row in candle_slice.iterrows():
            candle = [
                int(row['timestamp']),  # Timestamp in milliseconds
                float(row['open']),     # Open price
                float(row['high']),     # High price
                float(row['low']),      # Low price
                float(row['close']),    # Close price
                float(row['volume'])    # Volume
            ]
            ohlcv.append(candle)
        
        # Log sample data for debugging
        if ohlcv:
            logger.debug(
                f"Returning {len(ohlcv)} candles for {pair} ({timeframe}) from CSV data. "
                f"First candle: {ohlcv[0]}, Last candle: {ohlcv[-1]}"
            )
        
        return ohlcv
    
    def _resample_candles(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Resample 1m candles to requested timeframe.
        
        :param df: DataFrame with 1m candles
        :param timeframe: Target timeframe (e.g., '5m', '15m')
        :return: Resampled DataFrame
        """
        # Make a copy to avoid modifying original
        df_copy = df.copy()
        
        # Set datetime as index for resampling
        df_copy = df_copy.set_index('datetime')
        
        # Convert timeframe to pandas frequency
        freq_map = {
            '1m': '1T', '3m': '3T', '5m': '5T', '10m': '10T',
            '15m': '15T', '30m': '30T', '1h': '1H', '1d': '1D'
        }
        freq = freq_map.get(timeframe, '5T')
        
        # Resample with proper OHLC aggregation
        resampled = df_copy.resample(freq).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        # Reset index to get datetime back as column
        resampled = resampled.reset_index()
        
        # Recalculate timestamp from datetime
        if resampled['datetime'].dt.tz is None:
            resampled['datetime'] = resampled['datetime'].dt.tz_localize('UTC')
        resampled['timestamp'] = (resampled['datetime'].astype(int) // 10**6).astype(int)
        
        logger.debug(f"Resampled {len(df_copy)} candles to {len(resampled)} {timeframe} candles")
        
        return resampled

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
        Create a simulated order.
        
        :param pair: Freqtrade pair
        :param ordertype: Order type ('limit', 'market')
        :param side: Order side ('buy', 'sell')
        :param amount: Order amount (for options, this should be lot-size adjusted)
        :param rate: Order price (for limit orders)
        :param params: Additional parameters
        :param leverage: Leverage
        :param reduceOnly: Whether this is a reduce-only order (futures)
        :return: Order data
        """
        # Validate lot size for options trading
        from freqtrade.enums import InstrumentType
        instrument_type = InstrumentType.from_symbol(pair)
        
        if instrument_type.requires_lot_size():
            # Load lot size manager to validate quantity
            try:
                from freqtrade.data.lot_size_manager import LotSizeManager
                lot_mgr = LotSizeManager(self._config)
                lot_size = lot_mgr.get_lot_size(pair)
                
                # Validate that amount is a multiple of lot size
                if amount % lot_size != 0:
                    logger.warning(
                        f"Order amount {amount} for {pair} is not a multiple of lot size {lot_size}. "
                        f"Adjusting to {int(amount / lot_size) * lot_size}"
                    )
                    amount = int(amount / lot_size) * lot_size
                    
                if amount == 0:
                    raise InvalidOrderException(
                        f"Order amount too small for {pair} (lot size: {lot_size})"
                    )
                    
                logger.info(f"Options order: {pair} amount={amount} (lots: {amount/lot_size})")
            except ImportError:
                logger.warning("LotSizeManager not available, skipping lot size validation")
        
        # Generate order ID
        order_id = str(uuid.uuid4())
        
        # Get current price
        current_price = self._simulate_price(pair)
        
        # Determine execution price
        if ordertype == 'market':
            execution_price = self._apply_slippage(current_price, side)
        else:
            execution_price = rate if rate else current_price
        
        # Calculate order value
        order_value = execution_price * amount
        commission = self._calculate_commission(order_value)
        total_cost = order_value + commission
        
        # Check if we have sufficient balance
        if side == 'buy' and total_cost > self._balance['INR']['free']:
            raise InsufficientFundsError(
                f"Insufficient funds: need {total_cost}, have {self._balance['INR']['free']}"
            )
        
        # For Paper Broker, ALWAYS fill orders immediately for realistic testing
        # Both market and limit orders fill instantly to simulate instant execution
        will_fill = True
        
        # Create order
        order = {
            'id': order_id,
            'timestamp': int(datetime.now().timestamp() * 1000),
            'datetime': datetime.now().isoformat(),
            'status': 'closed' if will_fill else 'open',
            'symbol': pair,
            'type': ordertype,
            'side': side,
            'price': execution_price,
            'average': execution_price if will_fill else None,  # Average fill price
            'amount': amount,
            'filled': amount if will_fill else 0,
            'remaining': 0 if will_fill else amount,
            'cost': order_value,
            'fee': {
                'cost': commission,
                'currency': 'INR',
            },
            'info': {
                'slippage': self._slippage_percent,
                'simulated': True
            }
        }
        
        # Store order
        self._orders[order_id] = order
        
        if order['status'] == 'open':
            self._open_orders[order_id] = order
            # Reserve funds for buy orders
            if side == 'buy':
                self._balance['INR']['free'] -= total_cost
                self._balance['INR']['used'] += total_cost
        else:
            self._filled_orders[order_id] = order
            # Update balance
            if side == 'buy':
                self._balance['INR']['free'] -= total_cost
                # Update position
                if pair not in self._positions:
                    self._positions[pair] = {'amount': 0, 'cost': 0}
                self._positions[pair]['amount'] += amount
                self._positions[pair]['cost'] += order_value
            else:
                self._balance['INR']['free'] += (order_value - commission)
                # Update position
                if pair in self._positions:
                    self._positions[pair]['amount'] -= amount
        
        # Log trade
        self._trade_history.append({
            'order_id': order_id,
            'timestamp': order['datetime'],
            'pair': pair,
            'side': side,
            'amount': amount,
            'price': execution_price,
            'commission': commission
        })
        
        logger.info(
            f"Paper trade: {side.upper()} {amount} {pair} @ {execution_price} "
            f"(commission: {commission:.2f})"
        )
        
        return order

    def fetch_order(self, order_id: str, pair: str, params: dict | None = None) -> dict:
        """
        Fetch order status.
        
        :param order_id: Order ID
        :param pair: Freqtrade pair
        :param params: Additional parameters
        :return: Order data
        """
        if order_id not in self._orders:
            raise InvalidOrderException(f"Order {order_id} not found")
        
        return self._orders[order_id]
    
    def fetch_orders(self, pair: str, since: int | None = None, params: dict | None = None) -> list[dict]:
        """
        Fetch all orders for a pair.
        
        :param pair: Freqtrade pair
        :param since: Timestamp in milliseconds
        :param params: Additional parameters
        :return: List of orders
        """
        orders = []
        for order_id, order in self._orders.items():
            if order['symbol'] == pair:
                if since is None or order['timestamp'] >= since:
                    orders.append(order)
        
        return sorted(orders, key=lambda x: x['timestamp'])

    def cancel_order(self, order_id: str, pair: str, params: dict | None = None) -> dict:
        """
        Cancel an order.
        
        :param order_id: Order ID
        :param pair: Freqtrade pair
        :param params: Additional parameters
        :return: Order data
        """
        if order_id not in self._orders:
            raise InvalidOrderException(f"Order {order_id} not found")
        
        order = self._orders[order_id]
        
        if order['status'] == 'closed':
            raise InvalidOrderException(f"Order {order_id} already filled")
        
        # Cancel the order
        order['status'] = 'canceled'
        
        # Release reserved funds
        if order['side'] == 'buy':
            reserved = order['cost'] + self._calculate_commission(order['cost'])
            self._balance['INR']['free'] += reserved
            self._balance['INR']['used'] -= reserved
        
        # Remove from open orders
        if order_id in self._open_orders:
            del self._open_orders[order_id]
        
        return order

    def fetch_balance(self) -> dict:
        """
        Fetch virtual account balance including stock positions.
        
        :return: Balance data
        """
        # Restore positions from database on first call (database is ready now)
        if not self._positions_restored:
            self._restore_positions_from_db()
            self._positions_restored = True
        
        # DEBUG: Log current positions
        logger.debug(f"Paper Broker positions: {self._positions}")
        
        balance = {
            'INR': self._balance['INR'],
            'info': {
                'initial_balance': self._initial_balance,
                'total_trades': len(self._trade_history),
                'open_positions': len(self._positions)
            },
            'free': {'INR': self._balance['INR']['free']},
            'used': {'INR': self._balance['INR']['used']},
            'total': {'INR': self._balance['INR']['total']},
        }
        
        # Add stock positions to balance
        for pair, position in self._positions.items():
            # Extract base currency (e.g., "RELIANCE" from "RELIANCE/INR")
            base_currency = pair.split('/')[0]
            amount = position.get('amount', 0)
            
            logger.debug(f"Position {pair}: amount={amount}, base_currency={base_currency}")
            
            if amount > 0:
                balance[base_currency] = {
                    'free': amount,
                    'used': 0.0,
                    'total': amount
                }
                # Also add to free/used/total dicts
                balance['free'][base_currency] = amount
                balance['used'][base_currency] = 0.0
                balance['total'][base_currency] = amount
        
        logger.debug(f"Paper Broker balance returned: {list(balance.keys())}")
        return balance

    def get_trade_history(self) -> list:
        """Get complete trade history"""
        return self._trade_history

    def get_positions(self) -> dict:
        """Get current positions"""
        return self._positions

    def reset(self):
        """Reset paper broker to initial state"""
        self._balance = {
            'INR': {
                'free': self._initial_balance,
                'used': 0.0,
                'total': self._initial_balance
            }
        }
        
        # Initialize market data
        self._markets = {}
        self._tickers = {}
        self._orderbook = {}
        self._trades = {}
        self._dry_run_open_orders = {}
        self._ohlcv_candle_cache = {}  # Cache for OHLCV data
        
        # Clear price cache and reload CSV data
        self._price_cache = {}
        self._current_csv_time = {}
        self._csv_data = {}
        self._csv_data_index = {}
        self._use_csv_data = False
        
        # Reinitialize markets
        self._init_markets()
        
        # Reload CSV data with fresh data
        self._load_csv_data()
        
        logger.info("Paper Broker reset to initial state with fresh CSV data")
    
    def clear_cache(self):
        """Clear all caches and force reload of CSV data"""
        logger.info("Clearing all caches and reloading CSV data...")
        
        # Clear all caches
        self._ohlcv_candle_cache = {}
        self._price_cache = {}
        self._klines = {}
        self._expiring_candle_cache = {}
        self._fetch_tickers_cache.clear()
        self._exit_rate_cache.clear()
        self._entry_rate_cache.clear()
        
        # Reload CSV data
        self._csv_data = {}
        self._csv_data_index = {}
        self._current_csv_time = {}
        self._use_csv_data = False
        self._load_csv_data()
        
        logger.info("✅ All caches cleared and CSV data reloaded")

    @property
    def name(self) -> str:
        """Exchange name"""
        return 'Paperbroker'
    
    @property
    def id(self) -> str:
        """Exchange ID"""
        return 'paperbroker'
    
    @property
    def markets(self) -> dict:
        """Get markets dictionary"""
        if not self._markets:
            self._init_markets()
        return self._markets
    
    @property
    def precisionMode(self) -> int:
        """Get precision mode (DECIMAL_PLACES = 2 for Paper Broker)"""
        return 2  # DECIMAL_PLACES
    
    @property
    def precision_mode_price(self) -> int:
        """Get precision mode for price (same as precisionMode)"""
        return 2  # DECIMAL_PLACES
    
    @property
    def timeframes(self) -> list:
        """Supported timeframes for Paper Broker"""
        return ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w']
    
    def get_markets(self, base_currencies: list | None = None,
                    quote_currencies: list | None = None,
                    spot_only: bool = False, margin_only: bool = False,
                    futures_only: bool = False, tradable_only: bool = True,
                    active_only: bool = False) -> dict:
        """Get filtered markets"""
        markets = self.markets
        
        # Apply filters if needed
        if tradable_only:
            markets = {k: v for k, v in markets.items() if v.get('active', True)}
        
        if base_currencies:
            markets = {k: v for k, v in markets.items() if v.get('base') in base_currencies}
        
        if quote_currencies:
            markets = {k: v for k, v in markets.items() if v.get('quote') in quote_currencies}
        
        return markets

    def exchange_has(self, endpoint: str) -> bool:
        """Check if exchange supports endpoint"""
        # Paper broker is a virtual exchange that supports common operations
        supported = {
            'fetchOHLCV': True,
            'fetchTicker': True,
            'fetchTickers': True,
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
        # Paper broker supports all order types
        pass
    
    def validate_timeframes(self, timeframe: str | None) -> None:
        """Validate timeframe"""
        # Paper broker supports all common timeframes
        pass
    
    def validate_config(self, config) -> None:
        """Validate exchange configuration"""
        # Minimal validation for paper broker
        pass
    
    def get_balances(self) -> dict:
        """Get account balances - override to use custom fetch_balance"""
        return self.fetch_balance()
    
    def get_fee(self, symbol: str = '', type: str = '', side: str = '', amount: float = 1,
                price: float = 1, taker_or_maker: str = 'maker') -> float:
        """Get trading fee"""
        return self._commission_percent / 100
    
    def get_min_pair_stake_amount(self, pair: str, price: float, stoploss: float,
                                    leverage: float = 1.0) -> float | None:
        """Get minimum stake amount - Paper Broker has no minimums"""
        return 1.0
    
    def get_max_pair_stake_amount(self, pair: str, price: float, leverage: float = 1.0) -> float:
        """Get maximum stake amount - use account balance"""
        return self._balance['INR']['free']
    
    def close(self) -> None:
        """Close exchange connections (no-op for Paper Broker)"""
        pass
    
    def reload_markets(self, reload: bool = False) -> None:
        """Reload markets (no-op for Paper Broker as markets are static)"""
        pass
    
    def refresh_latest_ohlcv(self, pair_list: list[tuple[str, str, CandleType]]) -> None:
        """Refresh OHLCV data synchronously for Paper Broker - REAL-TIME UPDATES"""
        import random
        from datetime import datetime, timedelta
        import pandas as pd
        
        current_time = datetime.now()
        
        # Generate simulated OHLCV data for each pair
        for pair, timeframe, candle_type in pair_list:
            # Create cache key
            cache_key = (pair, timeframe, candle_type)
            
            # Parse timeframe to minutes
            if timeframe.endswith('m'):
                minutes = int(timeframe[:-1])
            elif timeframe.endswith('h'):
                minutes = int(timeframe[:-1]) * 60
            elif timeframe.endswith('d'):
                minutes = int(timeframe[:-1]) * 1440
            else:
                minutes = 5  # default
            
            # Check if we already have data
            if cache_key in self._klines and not self._klines[cache_key].empty:
                # UPDATE EXISTING DATA - Add new candles if time has passed
                df = self._klines[cache_key]
                last_candle_time = df['date'].iloc[-1]
                
                # Calculate how many new candles we need
                time_diff = (current_time - last_candle_time.to_pydatetime().replace(tzinfo=None)).total_seconds() / 60
                new_candles_needed = int(time_diff / minutes)
                
                if new_candles_needed > 0:
                    # Get last close price for continuity
                    last_close = df['close'].iloc[-1]
                    new_candles = []
                    
                    for i in range(1, new_candles_needed + 1):
                        timestamp = last_candle_time + pd.Timedelta(minutes=minutes * i)
                        
                        # Generate new candle with realistic price movement
                        volatility = last_close * 0.02  # 2% volatility
                        open_price = last_close + random.uniform(-volatility/2, volatility/2)
                        close_price = open_price + random.uniform(-volatility, volatility)
                        high_price = max(open_price, close_price) + random.uniform(0, volatility/2)
                        low_price = min(open_price, close_price) - random.uniform(0, volatility/2)
                        volume = random.uniform(100000, 1000000)
                        
                        new_candles.append({
                            'date': timestamp,
                            'open': open_price,
                            'high': high_price,
                            'low': low_price,
                            'close': close_price,
                            'volume': volume
                        })
                        
                        # Update for next candle
                        last_close = close_price
                    
                    # Append new candles
                    new_df = pd.DataFrame(new_candles)
                    df = pd.concat([df, new_df], ignore_index=True)
                    
                    # Keep only last 1000 candles
                    if len(df) > 1000:
                        df = df.iloc[-1000:].reset_index(drop=True)
                    
                    self._klines[cache_key] = df
                    logger.debug(f"Added {new_candles_needed} new candles for {pair} ({timeframe})")
            else:
                # INITIAL GENERATION - Create historical candles
                base_price = random.uniform(100, 5000)  # Random starting price
                candles = []
                
                for i in range(500):
                    timestamp = int((current_time - timedelta(minutes=minutes * (500 - i))).timestamp() * 1000)
                    
                    # Generate realistic OHLCV
                    volatility = base_price * 0.02  # 2% volatility
                    open_price = base_price + random.uniform(-volatility, volatility)
                    close_price = open_price + random.uniform(-volatility, volatility)
                    high_price = max(open_price, close_price) + random.uniform(0, volatility/2)
                    low_price = min(open_price, close_price) - random.uniform(0, volatility/2)
                    volume = random.uniform(100000, 1000000)
                    
                    candles.append([
                        timestamp,
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        volume
                    ])
                    
                    # Update base price for next candle (trend simulation)
                    base_price = close_price
                
                # Convert to DataFrame format expected by Freqtrade
                df = pd.DataFrame(candles, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
                df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True)
                
                # Store in _klines (this is what Freqtrade reads)
                self._klines[cache_key] = df
                
                logger.info(f"Generated {len(df)} simulated candles for {pair} ({timeframe})")
    
    def _get_candle_history_from_trades(
        self, pair: str, timeframe: str, since_ms: int
    ) -> list:
        """Get candle history from cache for Paper Broker"""
        from freqtrade.enums import CandleType
        
        cache_key = (pair, timeframe, CandleType.SPOT)
        
        if cache_key not in self._ohlcv_candle_cache:
            return []
        
        candles = self._ohlcv_candle_cache[cache_key]
        
        # Filter by since_ms if provided
        if since_ms:
            candles = [c for c in candles if c[0] >= since_ms]
        
        return candles
