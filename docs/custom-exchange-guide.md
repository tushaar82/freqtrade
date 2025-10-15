# Custom Exchange Integration Guide

## Overview

Freqtrade now supports a clean adapter pattern that decouples the bot from CCXT, making it easy to add custom exchanges. You can integrate any exchange or broker, whether they have a CCXT implementation or not.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Freqtrade Core                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │   ExchangeAdapter (ABC)    │  ← Abstract Base Class
        └─────────────┬──────────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
        ▼                            ▼
┌──────────────────┐      ┌──────────────────────┐
│   CCXTAdapter    │      │  CustomExchange      │
│  (CCXT wrapper)  │      │   (Base for custom)  │
└──────────────────┘      └──────────┬───────────┘
        │                             │
        │                    ┌────────┴────────┐
        ▼                    │                 │
┌──────────────┐      ┌──────────┐   ┌────────────┐
│ Binance      │      │ Paper    │   │ OpenAlgo   │
│ (via CCXT)   │      │ Broker   │   │  Smart API │
└──────────────┘      └──────────┘   └────────────┘
```

## Key Components

### 1. ExchangeAdapter
Abstract base class defining the interface all exchanges must implement.

**Location**: `freqtrade/exchange/exchange_adapter.py`

### 2. CCXTAdapter
Wrapper that makes any CCXT exchange work with the adapter interface.

**Location**: `freqtrade/exchange/ccxt_adapter.py`

### 3. CustomExchange
Base class for custom exchanges with sensible defaults.

**Location**: `freqtrade/exchange/custom_exchange.py`

### 4. ExchangeFactory
Factory that creates the appropriate adapter based on configuration.

**Location**: `freqtrade/exchange/exchange_factory.py`

## Creating a Custom Exchange

### Quick Start

Here's a minimal example of creating a custom exchange:

```python
# freqtrade/exchange/myexchange.py

from freqtrade.exchange.custom_exchange import CustomExchange
from freqtrade.constants import BuySell
from typing import List, Optional

class Myexchange(CustomExchange):
    """My custom exchange implementation"""
    
    @property
    def name(self) -> str:
        return 'Myexchange'
    
    @property
    def id(self) -> str:
        return 'myexchange'
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Initialize your exchange-specific stuff
        self._api_key = config['exchange'].get('key', '')
        self._api_secret = config['exchange'].get('secret', '')
        
        # Initialize markets from pair whitelist
        pairs = config['exchange'].get('pair_whitelist', [])
        self._init_markets_from_pairs(pairs)
    
    def exchange_has(self, endpoint: str) -> bool:
        """Specify which endpoints you support"""
        supported = {
            'fetchOHLCV': True,
            'fetchTicker': True,
            'fetchOrderBook': True,
            'createOrder': True,
            'cancelOrder': True,
            'fetchOrder': True,
            'fetchBalance': True,
        }
        return supported.get(endpoint, False)
    
    # Implement required methods
    
    def fetch_ticker(self, pair: str):
        # Your implementation
        last_price = 100.0  # Get from your API
        return self._create_ticker_response(
            pair=pair,
            bid=last_price * 0.999,
            ask=last_price * 1.001,
            last=last_price,
            volume=10000.0
        )
    
    def fetch_order_book(self, pair: str, limit: int = 100):
        # Your implementation
        bids = [[99.0, 100], [98.0, 200]]
        asks = [[101.0, 100], [102.0, 200]]
        return self._create_orderbook_response(pair, bids, asks)
    
    def fetch_ohlcv(self, pair: str, timeframe: str, 
                    since: Optional[int] = None,
                    limit: Optional[int] = None, **kwargs):
        # Your implementation
        # Return [[timestamp, open, high, low, close, volume], ...]
        return []
    
    def create_order(self, pair: str, order_type: str, side: BuySell,
                    amount: float, price: Optional[float] = None, 
                    params: Optional[dict] = None):
        # Your implementation
        order_id = self._generate_order_id()
        return self._create_order_response(
            order_id, pair, order_type, side, amount, price
        )
    
    def cancel_order(self, order_id: str, pair: str):
        # Your implementation
        return {'id': order_id, 'status': 'canceled'}
    
    def fetch_order(self, order_id: str, pair: str):
        # Your implementation
        return {}
    
    def fetch_orders(self, pair: str, since: Optional[int] = None):
        # Your implementation
        return []
    
    def fetch_open_orders(self, pair: Optional[str] = None):
        # Your implementation
        return []
    
    def fetch_balance(self):
        # Your implementation
        return {
            'USD': {'free': 10000, 'used': 0, 'total': 10000},
            'info': {}
        }
```

### Register Your Exchange

```python
# freqtrade/exchange/__init__.py

from freqtrade.exchange.myexchange import Myexchange
from freqtrade.exchange.exchange_factory import register_custom_exchange

# Register the exchange
register_custom_exchange('myexchange', Myexchange)
```

### Configuration

```json
{
  "exchange": {
    "name": "myexchange",
    "key": "your_api_key",
    "secret": "your_api_secret",
    "pair_whitelist": [
      "BTC/USD",
      "ETH/USD"
    ]
  }
}
```

## Advanced Examples

### NSE Stock Exchange (Paper Broker)

```python
class Paperbroker(CustomExchange):
    """Virtual trading exchange for testing"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Virtual account
        exchange_config = config['exchange']
        self._balance = {
            'INR': {
                'free': exchange_config.get('initial_balance', 100000),
                'used': 0,
                'total': exchange_config.get('initial_balance', 100000)
            }
        }
        
        # Load pairs
        pairs = exchange_config.get('pair_whitelist', [])
        self._init_markets_from_pairs(pairs, quote_currency='INR')
        
        # Virtual orders
        self._orders = {}
    
    def create_order(self, pair, order_type, side, amount, price=None, params=None):
        order_id = self._generate_order_id()
        
        # Simulate order execution
        if order_type == 'market':
            price = self._get_market_price(pair)
        
        cost = amount * price
        
        # Update balance
        if side == 'buy':
            if self._balance['INR']['free'] < cost:
                raise InsufficientFundsError("Insufficient funds")
            self._balance['INR']['free'] -= cost
            self._balance['INR']['used'] += cost
        
        # Store order
        order = self._create_order_response(
            order_id, pair, order_type, side, amount, price, 'closed'
        )
        order['filled'] = amount
        order['remaining'] = 0
        self._orders[order_id] = order
        
        return order
```

### REST API Exchange (OpenAlgo)

```python
import requests

class Openalgo(CustomExchange):
    """OpenAlgo REST API integration"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        self._api_key = config['exchange'].get('key', '')
        self._host = config['exchange'].get('urls', {}).get('api', 'http://localhost:5000')
        self._session = requests.Session()
        self._session.headers.update({'Authorization': f'Bearer {self._api_key}'})
    
    def fetch_ticker(self, pair: str):
        # Convert RELIANCE/INR -> {symbol: RELIANCE, exchange: NSE}
        symbol, _ = pair.split('/')
        
        response = self._session.post(
            f'{self._host}/api/v1/quotes',
            json={'symbol': symbol, 'exchange': 'NSE'}
        )
        data = response.json()
        
        return self._create_ticker_response(
            pair=pair,
            bid=float(data['ltp']) * 0.999,
            ask=float(data['ltp']) * 1.001,
            last=float(data['ltp']),
            volume=float(data.get('volume', 0))
        )
    
    def create_order(self, pair, order_type, side, amount, price=None, params=None):
        symbol, _ = pair.split('/')
        
        response = self._session.post(
            f'{self._host}/api/v1/placeorder',
            json={
                'symbol': symbol,
                'exchange': 'NSE',
                'action': side.upper(),
                'quantity': int(amount),
                'price': price,
                'order_type': order_type.upper(),
                'product': 'MIS'
            }
        )
        
        data = response.json()
        order_id = data['orderid']
        
        return self._create_order_response(
            order_id, pair, order_type, side, amount, price
        )
```

## Helper Methods

The `CustomExchange` base class provides useful helpers:

### Market Initialization
```python
# Initialize from pair list
self._init_markets_from_pairs(['BTC/USD', 'ETH/USD'])
```

### Order ID Generation
```python
order_id = self._generate_order_id()  # Returns: "exchange_1234567890123_5678"
```

### Standard Responses
```python
# Ticker
ticker = self._create_ticker_response(pair, bid, ask, last, volume)

# Order
order = self._create_order_response(order_id, pair, type, side, amount, price)

# Order book
orderbook = self._create_orderbook_response(pair, bids, asks)
```

## Testing Your Exchange

### 1. Unit Tests

```python
# tests/exchange/test_myexchange.py

def test_fetch_ticker():
    config = {'exchange': {'name': 'myexchange', 'pair_whitelist': ['BTC/USD']}}
    exchange = Myexchange(config)
    
    ticker = exchange.fetch_ticker('BTC/USD')
    assert 'last' in ticker
    assert ticker['symbol'] == 'BTC/USD'
```

### 2. Integration Test

```python
# Run with paper trading
python3 -m freqtrade trade --config config_myexchange.json --dry-run
```

## Best Practices

### 1. Error Handling

```python
from freqtrade.exceptions import ExchangeError, TemporaryError

def fetch_ticker(self, pair: str):
    try:
        response = self._api.get_ticker(pair)
        return self._create_ticker_response(...)
    except ConnectionError as e:
        raise TemporaryError(f"Connection error: {e}")
    except Exception as e:
        raise ExchangeError(f"Failed to fetch ticker: {e}")
```

### 2. Rate Limiting

```python
import time

class Myexchange(CustomExchange):
    def __init__(self, config: dict):
        super().__init__(config)
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
    
    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
```

### 3. Logging

```python
import logging

logger = logging.getLogger(__name__)

def create_order(self, ...):
    logger.info(f"Creating {side} order for {pair}: {amount} @ {price}")
    # ... implementation
    logger.debug(f"Order created: {order_id}")
```

### 4. Configuration Validation

```python
def validate_config(self, config: dict):
    exchange_config = config.get('exchange', {})
    
    if not exchange_config.get('key'):
        raise ConfigurationError("API key is required")
    
    if not exchange_config.get('pair_whitelist'):
        raise ConfigurationError("pair_whitelist is required")
```

## Migration Guide

### For Existing Custom Exchanges

If you have existing custom exchanges that inherit from `Exchange`:

**Before:**
```python
class Myexchange(Exchange):
    def __init__(self, config, **kwargs):
        # Mess with CCXT initialization
        super().__init__(config, **kwargs)
```

**After:**
```python
class Myexchange(CustomExchange):
    def __init__(self, config):
        super().__init__(config)
        # No CCXT mess!
```

## Examples in Freqtrade

### Paper Broker
- **File**: `freqtrade/exchange/paperbroker.py`
- **Type**: Virtual trading
- **Use Case**: Strategy testing

### OpenAlgo  
- **File**: `freqtrade/exchange/openalgo.py`
- **Type**: REST API
- **Use Case**: NSE trading via OpenAlgo

### Smart API
- **File**: `freqtrade/exchange/smartapi.py`
- **Type**: SDK-based
- **Use Case**: Angel One NSE trading

## Support

For questions or issues:
1. Check existing examples in `freqtrade/exchange/`
2. Review the adapter interface in `exchange_adapter.py`
3. Use the helper methods in `custom_exchange.py`
4. Open an issue on GitHub

## Summary

✅ **Clean separation** - CCXT and custom exchanges are independent  
✅ **Easy to add** - Inherit from `CustomExchange` and implement methods  
✅ **Helper methods** - Utilities for common tasks  
✅ **Type safety** - Full type hints throughout  
✅ **Flexible** - Support any exchange or broker  
✅ **Future-proof** - Easy to maintain and extend
