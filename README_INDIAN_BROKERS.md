# Freqtrade with Indian Brokers Support

Freqtrade has been successfully decoupled from CCXT and now includes native support for Indian brokers with comprehensive F&O trading capabilities.

## Supported Brokers

### 1. OpenAlgo
- **Type**: Multi-broker aggregator
- **Supports**: NSE, BSE, NFO, MCX
- **Features**: Unified API for multiple Indian brokers
- **Rate Limit**: 10 req/s, 300 req/min

### 2. SmartAPI (Angel One)
- **Type**: Angel One official API
- **Supports**: NSE, BSE, NFO, MCX
- **Features**: Real-time data, GTT orders
- **Rate Limit**: 10 req/s, 500 req/min
- **Requirements**: `smartapi-python`, `pyotp`

### 3. Zerodha Kite Connect
- **Type**: Zerodha official API
- **Supports**: NSE, BSE, NFO, MCX
- **Features**: Real-time data, GTT orders, comprehensive market data
- **Rate Limit**: 3 req/s, 180 req/min
- **Requirements**: `kiteconnect`

## Key Features

### 1. Broker Adapter Layer
- **Architecture**: Clean separation between Freqtrade core and broker implementations
- **Base Classes**: 
  - `ExchangeAdapter`: Abstract interface for all brokers
  - `CustomExchange`: Base class for non-CCXT brokers
  - `CCXTAdapter`: Wrapper for legacy CCXT brokers

### 2. Rate Limiting
- **Token Bucket Algorithm**: Prevents API rate limit violations
- **Multi-tier Limits**: Per-second, per-minute, per-hour, per-day
- **Broker-specific**: Pre-configured limits for each broker
- **Endpoint-specific**: Different limits for different API endpoints

### 3. Lot Size Management
- **Automatic Validation**: Ensures orders are in valid lot multiples
- **F&O Support**: Handles NIFTY, BANKNIFTY, FINNIFTY, etc.
- **Caching**: Stores lot sizes locally for fast access
- **Master File Support**: Can load from NSE master data

### 4. NSE Trading Calendar
- **Market Hours**: Automatic validation of NSE trading hours (9:15 AM - 3:30 PM IST)
- **Holidays**: Pre-loaded with 2024-2025 NSE trading holidays
- **Weekend Detection**: Prevents trading on Saturdays and Sundays
- **Custom Holidays**: Support for adding/removing holidays

### 5. Indian F&O Support
- **Instrument Types**: Equity, Futures, Call Options, Put Options, Indices
- **Symbol Parsing**: Automatic parsing of options symbols (e.g., NIFTY25DEC24500CE)
- **Strike/Expiry Detection**: Extracts strike price and expiry from symbol names
- **Lot Size Validation**: Ensures quantities are valid multiples

## Installation

```bash
# Quick install
./install.sh

# The script will:
# 1. Create virtual environment
# 2. Install Freqtrade dependencies
# 3. Install broker-specific dependencies (SmartAPI, Kite)
# 4. Setup directories
# 5. Offer to copy example configuration
```

## Configuration

### OpenAlgo Example

```json
{
  "exchange": {
    "name": "openalgo",
    "key": "your-api-key-here",
    "urls": {
      "api": "http://127.0.0.1:5000"
    },
    "nse_exchange": "NSE",
    "pair_whitelist": [
      "RELIANCE/INR",
      "TCS/INR",
      "NIFTY25DEC24500CE/INR"
    ]
  },
  "stake_currency": "INR",
  "dry_run": true
}
```

### SmartAPI Example

```json
{
  "exchange": {
    "name": "smartapi",
    "key": "your-api-key",
    "username": "your-client-id",
    "password": "your-password",
    "totp_token": "your-totp-secret",
    "nse_exchange": "NSE",
    "pair_whitelist": [
      "SBIN/INR",
      "INFY/INR"
    ]
  }
}
```

### Zerodha Example

```json
{
  "exchange": {
    "name": "zerodha",
    "key": "your-api-key",
    "secret": "your-api-secret",
    "request_token": "request-token-from-login",
    "pair_whitelist": [
      "TATASTEEL/INR",
      "NIFTY25DEC24500PE/INR"
    ]
  }
}
```

## Usage

### Start Trading

```bash
# Start with config
./start.sh

# Or manually
source .venv/bin/activate
freqtrade trade --config config.json --strategy YourStrategy
```

### Stop Trading

```bash
./stop.sh
```

### Clean Cache and Logs

```bash
./clean.sh
```

## Trading Indian F&O

### Options Trading Example

```python
# In your strategy
def populate_entry_trend(self, dataframe, metadata):
    # For NIFTY options
    symbol = metadata['pair']  # e.g., "NIFTY25DEC24500CE/INR"
    
    # The broker adapter automatically:
    # 1. Validates it's a valid options symbol
    # 2. Checks lot size requirements
    # 3. Adjusts quantity to lot multiples
    # 4. Verifies market is open before placing orders
    
    dataframe.loc[
        (dataframe['rsi'] < 30) &
        (dataframe['volume'] > 0),
        'enter_long'] = 1
    return dataframe
```

### Lot Size Handling

```python
# Automatic lot size adjustment
from freqtrade.exchange import LotSizeManager

lot_manager = LotSizeManager()

# Get lot size for a symbol
lot_size = lot_manager.get_lot_size("NIFTY")  # Returns 25

# Validate quantity
is_valid = lot_manager.validate_quantity("NIFTY25DEC24500CE/INR", 50)  # True (2 lots)

# Auto-adjust quantity
adjusted = lot_manager.adjust_quantity_to_lot("NIFTY", 30)  # Returns 25 (1 lot)
```

### Market Hours Check

```python
from freqtrade.exchange import get_nse_calendar

calendar = get_nse_calendar()

# Check if market is open
if calendar.is_market_open():
    # Place orders
    pass

# Get time until market opens
seconds = calendar.time_until_market_open()

# Check if today is a trading day
if calendar.is_trading_day():
    # Run daily tasks
    pass

# Get upcoming holidays
holidays = calendar.get_upcoming_holidays(days=30)
```

## Architecture

```
Freqtrade Core
     ↓
ExchangeResolver
     ↓
ExchangeAdapter (Abstract Interface)
     ├── CCXTAdapter → CCXT Exchanges (Binance, Kraken, etc.)
     └── CustomExchange → Indian Brokers
              ├── OpenAlgo
              ├── SmartAPI
              └── Zerodha

Utilities:
- RateLimiter: Token bucket rate limiting
- LotSizeManager: F&O lot size handling
- NSECalendar: Market hours and holidays
```

## Rate Limiting Details

### Configured Limits

| Broker | Req/Second | Req/Minute | Min Interval |
|--------|------------|------------|--------------|
| OpenAlgo | 10 | 300 | 50ms |
| SmartAPI | 10 | 500 | 100ms |
| Zerodha | 3 | 180 | 333ms |

### Custom Rate Limiting

```python
from freqtrade.exchange.rate_limiter import RateLimiter

# Create custom rate limiter
limiter = RateLimiter(
    requests_per_second=5,
    requests_per_minute=100,
    min_request_interval=0.2
)

# Use in your code
limiter.wait_if_needed()
# Make API call
```

## Testing

```bash
# Run all tests
pytest

# Test specific broker
pytest tests/exchange/test_openalgo.py
pytest tests/exchange/test_smartapi.py
pytest tests/exchange/test_zerodha.py

# Test broker integration
python test_broker_integration.py
```

## Important Notes

### CCXT Decoupling
- SmartAPI now extends `CustomExchange` instead of CCXT's `Exchange`
- All Indian brokers are 100% independent of CCXT
- CCXT brokers still supported via `CCXTAdapter`

### Indian F&O Specifics
- All quantities automatically validated against lot sizes
- Options symbols parsed automatically (e.g., NIFTY25DEC24500CE)
- Market hours enforced (9:15 AM - 3:30 PM IST)
- NSE holidays automatically handled

### Rate Limiting
- All broker API calls automatically rate-limited
- Prevents DDos protection triggers
- Statistics available via `limiter.get_stats()`

### Session Management
- Zerodha requires daily OAuth authentication
- SmartAPI requires TOTP for login
- OpenAlgo uses Bearer token authentication

## Troubleshooting

### Rate Limit Errors
- Check `get_stats()` on rate limiter
- Adjust limits in `BrokerRateLimits` class
- Add per-endpoint limits if needed

### Lot Size Errors
- Verify lot sizes are up-to-date
- Use `lot_manager.update_lot_sizes()` to refresh
- Check NSE master file for current lot sizes

### Market Hours Issues
- Ensure system timezone is correct (IST)
- Check NSE calendar for holidays
- Use `calendar.add_holiday()` for custom holidays

## Support

For issues, feature requests, or contributions:
- GitHub Issues: [freqtrade/issues](https://github.com/freqtrade/freqtrade/issues)
- Documentation: [freqtrade.io](https://www.freqtrade.io)

## License

This project is licensed under the GPLv3 License.
