# Smart API (Angel One) Integration

This guide explains how to use Freqtrade with Smart API (Angel One) for trading on Indian markets.

## Overview

Smart API is Angel One's official trading API that provides programmatic access to NSE, BSE, MCX, and other Indian exchanges. This integration enables Freqtrade to execute trades through your Angel One account.

## Prerequisites

### 1. Angel One Account

- Active Angel One trading account
- Enable API trading in your account
- Complete Angel One's API activation process

### 2. Smart API Credentials

You'll need the following:
- **API Key**: Get from Angel One developer console
- **Client Code**: Your Angel One client ID
- **PIN**: Your trading PIN
- **TOTP Token**: QR code value for 2-factor authentication

### 3. Python Dependencies

```bash
pip install smartapi-python pyotp
```

## Getting Smart API Credentials

### Step 1: Get API Key

1. Login to [smartapi.angelbroking.com](https://smartapi.angelbroking.com/)
2. Navigate to "My Apps"
3. Create a new app
4. Note down your **API Key**

### Step 2: Get TOTP Token

1. Open Angel One mobile app
2. Go to Settings → Security → 2FA
3. Setup authenticator app
4. **Save the QR code secret value** - this is your TOTP token
   - The token is the alphanumeric string in the QR code
   - Example: `JBSWY3DPEHPK3PXP`

### Step 3: Prepare Credentials

You'll need:
- **API Key**: From developer console
- **Client Code**: Your Angel One account ID (e.g., `A12345`)
- **PIN**: Your 4-digit trading PIN
- **TOTP Token**: The secret from QR code

## Configuration

### Basic Configuration

Create a configuration file `config_smartapi.json`:

```json
{
    "stake_currency": "INR",
    "stake_amount": 10000,
    "timeframe": "5m",
    "exchange": {
        "name": "smartapi",
        "key": "YOUR_API_KEY",
        "username": "YOUR_CLIENT_CODE",
        "password": "YOUR_PIN",
        "totp_token": "YOUR_TOTP_TOKEN",
        "nse_exchange": "NSE",
        "pair_whitelist": [
            "SBIN/INR",
            "RELIANCE/INR",
            "TCS/INR"
        ]
    }
}
```

Or copy the example:
```bash
cp config_examples/config_smartapi_nse.example.json config_smartapi.json
```

### Configuration Options

| Parameter | Description | Example |
|-----------|-------------|---------|
| `key` | Smart API key | `"your_api_key"` |
| `username` | Client code | `"A12345"` |
| `password` | Trading PIN | `"1234"` |
| `totp_token` | TOTP secret | `"JBSWY3DPEHPK3PXP"` |
| `nse_exchange` | Default exchange | `"NSE"`, `"BSE"`, `"MCX"` |

## Symbol Format

### Freqtrade Format
```
SYMBOL/INR
```

Examples:
- **NSE Equity**: `SBIN/INR`, `RELIANCE/INR`
- **BSE Equity**: `SBIN-BSE/INR`
- **NFO Derivatives**: `NIFTY-NFO/INR`

### Smart API Format

Smart API uses:
```json
{
    "tradingsymbol": "SBIN-EQ",
    "symboltoken": "3045",
    "exchange": "NSE"
}
```

The integration handles conversion automatically.

## Product Types

Smart API supports different product types:

### INTRADAY (MIS)
- Margin Intraday Square-off
- Auto-squared off before market close
- Higher leverage available

### DELIVERY (CNC)
- Cash and Carry
- For delivery-based trading
- No auto-square off

### MARGIN (NRML)
- Normal product for F&O
- Can carry positions overnight

### Configuration

Specify product type in strategy:
```python
def custom_entry_price(self, pair, current_time, proposed_rate, 
                       entry_tag, side, **kwargs):
    kwargs['order_params'] = {'product': 'INTRADAY'}  # or 'DELIVERY', 'MARGIN'
    return proposed_rate
```

## Order Types

Smart API supports:

1. **LIMIT**: Limit orders
2. **MARKET**: Market orders
3. **STOPLOSS_LIMIT**: Stop loss with limit price
4. **STOPLOSS_MARKET**: Stop loss with market execution

## Market Hours

**NSE Regular Market** (IST):
- Pre-market: 09:00 - 09:15
- Regular: 09:15 - 15:30
- Post-market: 15:40 - 16:00

## Running with Smart API

### 1. Test Connection

```python
from freqtrade.exchange import Exchange

config = {
    'exchange': {
        'name': 'smartapi',
        'key': 'your_api_key',
        'username': 'your_client_code',
        'password': 'your_pin',
        'totp_token': 'your_totp_token'
    },
    'dry_run': True
}

exchange = Exchange(config)
print(exchange.fetch_ticker('SBIN/INR'))
```

### 2. Dry Run Trading

```bash
freqtrade trade --config config_smartapi.json --strategy NSESampleStrategy
```

### 3. Live Trading

⚠️ **Only after thorough testing!**

```bash
# Set dry_run to false in config
freqtrade trade --config config_smartapi.json --strategy NSESampleStrategy
```

## Features

### ✅ Implemented

- Market and limit orders
- Order book data
- Historical OHLCV data
- Real-time quotes
- Position tracking
- Balance queries
- Order status
- Order cancellation
- Market hours validation

### WebSocket Support

Smart API provides WebSocket for real-time data:

```python
# WebSocket will be used automatically if configured
# Enable in exchange settings
"ws_enabled": true
```

## Example Strategy

Using the NSESampleStrategy:

```bash
# Download data
freqtrade download-data --config config_smartapi.json --timerange 20240101-

# Backtest
freqtrade backtesting --config config_smartapi.json --strategy NSESampleStrategy

# Live trade
freqtrade trade --config config_smartapi.json --strategy NSESampleStrategy
```

## Troubleshooting

### Authentication Failed

**Issue**: "Invalid Token" or "Login failed"

**Solutions**:
1. Verify API key is correct
2. Check client code format (uppercase)
3. Ensure TOTP token is the QR secret, not the OTP
4. Verify PIN is correct
5. Check if API trading is enabled in your account

### Symbol Token Error

**Issue**: "Symbol token not found"

**Solutions**:
1. Update symbol master data
2. Check symbol name is correct
3. Use exact NSE symbol format
4. Verify exchange is correct (NSE/BSE/MCX)

### Order Rejection

**Issue**: Orders getting rejected

**Solutions**:
1. Check account balance
2. Verify market hours
3. Check circuit limits
4. Ensure correct product type
5. Verify symbol is tradable

### Rate Limiting

**Issue**: "Too many requests"

**Solutions**:
1. Reduce API call frequency
2. Increase `process_throttle_secs` in config
3. Use WebSocket for real-time data instead of polling

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables**:
   ```bash
   export SMARTAPI_KEY="your_api_key"
   export SMARTAPI_USERNAME="your_client_code"
   export SMARTAPI_PASSWORD="your_pin"
   export SMARTAPI_TOTP="your_totp_token"
   ```

3. **Secure TOTP token**: Store securely, it's equivalent to your password
4. **Monitor account**: Regular check for unauthorized access
5. **Use strong PIN**: Don't use easily guessable PINs

## Advanced Features

### GTT (Good Till Triggered) Orders

Smart API supports GTT for stop loss:

```python
# In strategy
stoploss_on_exchange = True
```

### Bracket Orders

Configure bracket orders for risk management:

```python
# Bracket order parameters
order_params = {
    'product': 'INTRADAY',
    'squareoff': '10',  # Target profit
    'stoploss': '5'     # Stop loss
}
```

### Market Data API

Access additional market data:

```python
# Get market depth
depth = exchange.fetch_order_book('SBIN/INR', limit=20)

# Get LTP
ticker = exchange.fetch_ticker('SBIN/INR')

# Historical data
ohlcv = exchange.fetch_ohlcv('SBIN/INR', '5m', limit=100)
```

## Limitations

1. **Symbol Token Lookup**: Currently requires manual mapping (TODO: Auto-fetch from master)
2. **WebSocket**: Basic implementation, full streaming support pending
3. **Options Chain**: Not yet implemented
4. **Basket Orders**: Single order at a time

## API Rate Limits

Smart API rate limits:
- **Order Placement**: 10 orders per second
- **Market Data**: 100 requests per second
- **Historical Data**: 3 requests per second

## Cost

- **API Access**: Free for Angel One clients
- **Brokerage**: As per your Angel One plan
- **Data**: Real-time data included

## Support

- **Smart API Docs**: [smartapi.angelbroking.com/docs](https://smartapi.angelbroking.com/docs/)
- **Angel One Support**: Contact via app or website
- **GitHub Issues**: For integration-specific issues

## Comparison with OpenAlgo

| Feature | Smart API | OpenAlgo |
|---------|-----------|----------|
| **Broker Support** | Angel One only | Multi-broker |
| **Setup** | Cloud-based | Self-hosted |
| **API Keys** | Angel One account | API key only |
| **Authentication** | TOTP required | API key |
| **WebSocket** | Native support | Supported |
| **Maintenance** | Angel One managed | Self-managed |

## Quick Commands

```bash
# Test connection
freqtrade test-pairlist --config config_smartapi.json

# Download data
freqtrade download-data --config config_smartapi.json --days 30

# Backtest
freqtrade backtesting --config config_smartapi.json --strategy YourStrategy

# Paper trade
freqtrade trade --config config_smartapi.json --strategy YourStrategy

# Live trade (caution!)
# Edit config: "dry_run": false
freqtrade trade --config config_smartapi.json --strategy YourStrategy
```

## Disclaimer

⚠️ **Trading involves risk**. Always:
- Test thoroughly before live trading
- Start with small amounts
- Understand the risks
- Never invest more than you can afford to lose
- Comply with local regulations

---

**Ready to trade NSE with Angel One? Start with dry-run mode!** 🚀
