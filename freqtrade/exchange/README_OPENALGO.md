# OpenAlgo Exchange Implementation

## Overview

This directory contains the OpenAlgo exchange implementation for Freqtrade. OpenAlgo is a self-hosted algorithmic trading platform designed for Indian markets (NSE, BSE, MCX, etc.).

## Key Differences from CCXT Exchanges

Unlike most other exchanges in Freqtrade which use the CCXT library, OpenAlgo:

1. **Custom REST API**: Uses OpenAlgo's proprietary REST API instead of CCXT
2. **Indian Markets Focus**: Specifically designed for NSE, BSE, NFO, MCX, and other Indian exchanges
3. **Broker Agnostic**: Works with multiple Indian brokers (Zerodha, Angel One, Upstox, etc.)
4. **Self-Hosted**: Runs on your own infrastructure

## Architecture

### Class: `OpenAlgo`

Extends the base `Exchange` class with custom implementations for:

- **API Communication**: Direct HTTP requests to OpenAlgo REST API
- **Symbol Conversion**: Converts between Freqtrade pairs and OpenAlgo symbols
- **Market Hours**: Built-in NSE market hours validation
- **Order Management**: Custom order placement, modification, and cancellation

### Key Methods

#### Market Data Methods

- `fetch_ticker(pair)`: Get current ticker/quote data
- `fetch_order_book(pair, limit)`: Get market depth (bid/ask)
- `fetch_ohlcv(pair, timeframe, since, limit)`: Get historical candlestick data

#### Order Management Methods

- `create_order(pair, ordertype, side, amount, rate, params)`: Place new order
- `fetch_order(order_id, pair)`: Get order status
- `cancel_order(order_id, pair)`: Cancel pending order
- `fetch_balance()`: Get account balance

#### Utility Methods

- `is_market_open()`: Check if NSE market is currently open
- `_convert_symbol_to_openalgo(pair)`: Convert Freqtrade pair to OpenAlgo format
- `_convert_symbol_from_openalgo(symbol, exchange)`: Convert OpenAlgo symbol to Freqtrade pair

## Symbol Format

### Freqtrade Format
```
SYMBOL/INR
```

Examples:
- `RELIANCE/INR`
- `TCS/INR`
- `SBIN/INR`

### OpenAlgo Format
```
{
    "symbol": "RELIANCE",
    "exchange": "NSE"
}
```

## Configuration

### Required Settings

```json
{
    "exchange": {
        "name": "openalgo",
        "key": "your_openalgo_api_key",
        "secret": "",
        "urls": {
            "api": "http://127.0.0.1:5000"
        }
    }
}
```

### Optional Settings

- `nse_exchange`: Default exchange (default: "NSE")
- `strategy`: Strategy name for OpenAlgo (default: "Freqtrade")

## Order Types

OpenAlgo supports:

- **Market Orders**: `ordertype='market'`
- **Limit Orders**: `ordertype='limit'`

## Product Types

Specify in order params:

- **MIS**: Intraday (margin) - `{'product': 'MIS'}`
- **CNC**: Delivery - `{'product': 'CNC'}`
- **NRML**: Normal (F&O) - `{'product': 'NRML'}`

## Market Hours

NSE Regular Market Hours (IST):
- **Open**: 09:15
- **Close**: 15:30
- **Days**: Monday to Friday

## Error Handling

The implementation handles various error scenarios:

- **Connection Errors**: Raised as `TemporaryError`
- **API Errors**: Raised as `ExchangeError`
- **Rate Limiting**: Raised as `DDosProtection`
- **Insufficient Funds**: Raised as `InsufficientFundsError`

## API Endpoints Used

| Freqtrade Method | OpenAlgo Endpoint | HTTP Method |
|-----------------|-------------------|-------------|
| `fetch_ticker` | `/api/v1/quotes` | POST |
| `fetch_order_book` | `/api/v1/depth` | POST |
| `fetch_ohlcv` | `/api/v1/history` | POST |
| `create_order` | `/api/v1/placeorder` | POST |
| `fetch_order` | `/api/v1/orderstatus` | POST |
| `cancel_order` | `/api/v1/cancelorder` | POST |
| `fetch_balance` | `/api/v1/funds` | POST |

## Limitations

1. **No WebSocket Support**: Currently uses REST API only (polling mode)
2. **Limited Futures Support**: Primarily designed for equity spot trading
3. **No Stoploss on Exchange**: Uses Freqtrade's internal stoploss
4. **Indian Markets Only**: Not suitable for international markets

## Future Enhancements

Potential improvements:

1. WebSocket support for real-time data
2. Advanced order types (bracket, cover orders)
3. NFO (derivatives) symbol format support
4. Multi-leg order support
5. Paper trading mode integration

## Testing

To test the OpenAlgo integration:

1. **Setup OpenAlgo**:
   ```bash
   # Install and run OpenAlgo
   git clone https://github.com/marketcalls/openalgo
   cd openalgo
   python app.py
   ```

2. **Get API Key**:
   - Login to OpenAlgo at http://127.0.0.1:5000
   - Generate API key from settings

3. **Test Connection**:
   ```python
   from freqtrade.exchange import Exchange
   from freqtrade.configuration import Configuration
   
   config = {
       'exchange': {
           'name': 'openalgo',
           'key': 'your_api_key',
           'urls': {'api': 'http://127.0.0.1:5000'}
       },
       'dry_run': True
   }
   
   exchange = Exchange(config)
   ticker = exchange.fetch_ticker('RELIANCE/INR')
   print(ticker)
   ```

4. **Dry Run Trading**:
   ```bash
   freqtrade trade --config config_openalgo.json --strategy YourStrategy
   ```

## Troubleshooting

### Common Issues

**Issue**: `Connection Error`
- **Solution**: Ensure OpenAlgo server is running on http://127.0.0.1:5000

**Issue**: `Authentication Failed`
- **Solution**: Verify API key is correct and active

**Issue**: `Symbol Not Found`
- **Solution**: Check symbol name matches NSE exactly (e.g., 'RELIANCE' not 'reliance')

**Issue**: `Order Rejected`
- **Solution**: Check market hours, balance, and circuit limits

### Debug Mode

Enable detailed logging:

```json
{
    "verbosity": 3,
    "exchange": {
        "log_responses": true
    }
}
```

## Contributing

When contributing to OpenAlgo exchange implementation:

1. Follow Freqtrade coding standards
2. Add unit tests for new features
3. Update documentation
4. Test with actual OpenAlgo instance
5. Consider backward compatibility

## References

- [OpenAlgo Documentation](https://docs.openalgo.in)
- [OpenAlgo GitHub](https://github.com/marketcalls/openalgo)
- [Freqtrade Exchange Documentation](https://www.freqtrade.io/en/stable/exchanges/)
- [NSE Market Information](https://www.nseindia.com)

## License

This implementation follows Freqtrade's GPL-3.0 license.

## Support

For issues specific to:
- **OpenAlgo API**: Contact OpenAlgo support
- **Freqtrade Integration**: Create an issue on Freqtrade GitHub
- **Trading Strategy**: Consult Freqtrade strategy documentation

---

**Note**: Always test thoroughly with paper trading before using real money. Trading involves substantial risk of loss.
