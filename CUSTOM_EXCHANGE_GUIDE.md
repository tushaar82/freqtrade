# Custom Exchange Integration - Complete Guide

## Quick Start

### Using PaperBroker (Virtual Trading)
```bash
# 1. Create config
cat > config.json << 'EOF'
{
  "exchange": {
    "name": "paperbroker",
    "initial_balance": 100000,
    "pair_whitelist": ["RELIANCE/INR", "TCS/INR"]
  },
  "stake_amount": 1000,
  "strategy": "NSESampleStrategy"
}
EOF

# 2. Run
freqtrade trade --config config.json
```

### Using OpenAlgo (NSE Trading)
```bash
# 1. Start OpenAlgo server
# 2. Create config with your API key
{
  "exchange": {
    "name": "openalgo",
    "key": "YOUR_API_KEY",
    "urls": {"api": "http://127.0.0.1:5000"},
    "pair_whitelist": ["RELIANCE/INR", "TCS/INR"]
  }
}
# 3. Run freqtrade
```

---

## Architecture

### Adapter Pattern (No CCXT Required)

**Components:**
1. `ExchangeAdapter` - Interface for all exchanges
2. `CustomExchange` - Base class with helpers
3. `ExchangeFactory` - Creates correct exchange instance

**Benefits:**
- ✅ No CCXT for custom exchanges
- ✅ Easy to add brokers (~100 lines)
- ✅ Full control over API
- ✅ Type-safe implementation

---

## Available Exchanges

### 1. PaperBroker (Virtual)
- **Purpose:** Testing strategies without real money
- **Features:** Realistic simulation, slippage, commission
- **Config:**
  ```json
  {
    "exchange": {
      "name": "paperbroker",
      "initial_balance": 100000,
      "slippage_percent": 0.05,
      "commission_percent": 0.1
    }
  }
  ```

### 2. OpenAlgo (NSE/BSE/MCX)
- **Purpose:** Live trading on Indian markets
- **Features:** MIS/CNC/NRML, market hours validation
- **Config:**
  ```json
  {
    "exchange": {
      "name": "openalgo",
      "key": "api_key",
      "urls": {"api": "http://127.0.0.1:5000"}
    }
  }
  ```

### 3. SmartAPI (Angel One)
- **Purpose:** Direct Angel One trading
- **Config:**
  ```json
  {
    "exchange": {
      "name": "smartapi",
      "key": "api_key",
      "username": "client_code",
      "password": "pin",
      "totp_token": "secret"
    }
  }
  ```

---

## Strategy Features

### NSESampleStrategy

**Entry Logic:**
- RSI < 30 (oversold)
- EMA crossover (bullish)
- High volume
- MACD confirmation

**Exit Logic:**
- RSI > 70 (overbought)
- EMA bearish crossover
- MACD bearish
- Bollinger upper band

**Trailing Stoploss:**
```python
stoploss = -0.03                      # 3% hard stop
trailing_stop = True
trailing_stop_positive = 0.01         # Trail 1% below peak
trailing_stop_positive_offset = 0.015 # Activate at 1.5% profit
```

**NSE Market Hours:**
- No entries: 09:15-09:30, after 14:45
- Force exit: 15:15 (before market close)

---

## Adding a New Exchange

```python
# 1. Create exchange class
from freqtrade.exchange.custom_exchange import CustomExchange

class MyExchange(CustomExchange):
    @property
    def name(self) -> str:
        return 'MyExchange'
    
    @property
    def id(self) -> str:
        return 'myexchange'
    
    def __init__(self, config):
        super().__init__(config)
        # Initialize markets
        pairs = config.get('exchange', {}).get('pair_whitelist', [])
        self._init_markets_from_pairs(pairs)
    
    def fetch_ticker(self, pair):
        # Your implementation
        price = self._get_price_from_api(pair)
        return self._create_ticker_response(
            pair, bid=price*0.999, ask=price*1.001, last=price
        )
    
    # Implement other required methods...

# 2. Register in __init__.py
from freqtrade.exchange.exchange_factory import register_custom_exchange
register_custom_exchange('myexchange', MyExchange)

# 3. Use it
config = {"exchange": {"name": "myexchange"}}
```

---

## Testing

### Test Suite
```bash
python3 test_broker_integration.py
```

**Tests:**
- Exchange registration
- Market data fetching
- Order operations
- Balance management
- Error handling

### Backtesting
```bash
freqtrade backtesting \
  --config config.json \
  --strategy NSESampleStrategy \
  --timerange 20231001-20231101
```

---

## Error Handling

**Exception Types:**
- `InsufficientFundsError` - Not enough balance
- `InvalidOrderException` - Invalid order
- `ExchangeError` - General error
- `TemporaryError` - Retryable
- `DDosProtection` - Rate limit

**Retry Logic:**
- Up to 4 retries for temporary errors
- Exponential backoff for rate limits
- Detailed logging

---

## Best Practices

### 1. Always Test First
- Use PaperBroker before live trading
- Backtest strategies thoroughly
- Verify all functionality

### 2. Monitor Closely
- Check logs regularly
- Verify orders are executing
- Watch trailing stoploss

### 3. Risk Management
- Set appropriate stoploss
- Use trailing stoploss
- Limit stake per trade
- Monitor total exposure

### 4. NSE Specific
- Respect market hours
- Square off MIS before 15:15
- Avoid first 15 minutes
- No entries near market close

---

## Troubleshooting

### Exchange not found
**Fix:** Check registration in `freqtrade/exchange/__init__.py`

### Orders not filling
**Fix:** Check balance, market hours, order parameters

### Connection errors
**Fix:** Verify API URL, check network, ensure server is running

### Balance incorrect
**Fix:** Check balance calculation in exchange implementation

---

## Files Structure

```
freqtrade/
├── exchange/
│   ├── exchange_adapter.py      # Interface
│   ├── custom_exchange.py       # Base class
│   ├── exchange_factory.py      # Factory
│   ├── openalgo.py             # OpenAlgo
│   ├── paperbroker.py          # PaperBroker
│   ├── smartapi.py             # SmartAPI
│   └── __init__.py             # Registration
├── user_data/
│   └── strategies/
│       └── NSESampleStrategy.py
└── test_broker_integration.py   # Tests
```

---

## Support

For detailed architecture information, see code documentation in:
- `freqtrade/exchange/exchange_adapter.py`
- `freqtrade/exchange/custom_exchange.py`
- `freqtrade/exchange/exchange_factory.py`

For NSE-specific trading guide, see:
- `NSE_TRADING_COMPLETE_GUIDE.md`

---

**Everything is production-ready. Happy trading! 📈**
