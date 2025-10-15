# OpenAlgo NSE Integration

This guide explains how to use Freqtrade with OpenAlgo for trading on the National Stock Exchange (NSE) of India.

## Overview

OpenAlgo is a self-hosted algorithmic trading platform designed for Indian markets. This integration allows Freqtrade to trade NSE equities, derivatives, and other Indian market instruments through OpenAlgo.

## Prerequisites

1. **OpenAlgo Installation**: Install and run OpenAlgo on your system or server
   - Download from: https://github.com/marketcalls/openalgo
   - Follow the installation instructions in the OpenAlgo documentation
   - Ensure OpenAlgo is running (default: http://127.0.0.1:5000)

2. **Broker Account**: Configure your Indian broker account with OpenAlgo
   - Supported brokers: Angel One, Zerodha, Upstox, Fyers, etc.
   - Configure broker credentials in OpenAlgo

3. **API Key**: Generate an API key from OpenAlgo dashboard
   - Login to OpenAlgo web interface
   - Navigate to API settings
   - Generate and copy your API key

## Configuration

### Basic Configuration

Create a configuration file based on `config_examples/config_openalgo_nse.example.json`:

```json
{
    "stake_currency": "INR",
    "stake_amount": 10000,
    "timeframe": "5m",
    "exchange": {
        "name": "openalgo",
        "key": "your_openalgo_api_key_here",
        "secret": "",
        "urls": {
            "api": "http://127.0.0.1:5000"
        },
        "nse_exchange": "NSE",
        "pair_whitelist": [
            "RELIANCE/INR",
            "TCS/INR",
            "INFY/INR"
        ]
    }
}
```

### Exchange Configuration Options

- **name**: Must be set to `"openalgo"`
- **key**: Your OpenAlgo API key (required)
- **secret**: Leave empty (not used by OpenAlgo)
- **urls.api**: OpenAlgo server URL
  - Local: `http://127.0.0.1:5000`
  - Remote: Use your server's URL or ngrok URL
- **nse_exchange**: Default exchange for symbols (NSE, BSE, NFO, BFO, MCX, etc.)

### Pair Format

NSE pairs use the format: `SYMBOL/INR`

Examples:
- Equity: `RELIANCE/INR`, `TCS/INR`, `INFY/INR`
- For derivatives (NFO), include NFO in the symbol or configure exchange appropriately

### Product Types

OpenAlgo supports different product types for trading:

- **MIS**: Margin Intraday Square-off (positions auto-squared off at end of day)
- **CNC**: Cash and Carry (delivery-based trading)
- **NRML**: Normal (for F&O positions held overnight)

Configure product type in your strategy or order parameters.

## Market Hours

NSE operates during the following hours (Indian Standard Time):

- **Regular Market**: 09:15 AM - 03:30 PM (Monday to Friday)
- **Pre-market**: 09:00 AM - 09:15 AM
- **Post-market**: 03:40 PM - 04:00 PM

The OpenAlgo integration includes a `is_market_open()` method to check market status.

## Supported Order Types

OpenAlgo supports the following order types:

1. **Market Orders**: Execute at current market price
   ```json
   "order_types": {
       "entry": "market",
       "exit": "market"
   }
   ```

2. **Limit Orders**: Execute at specified price or better
   ```json
   "order_types": {
       "entry": "limit",
       "exit": "limit"
   }
   ```

3. **Stop Loss**: Market or limit stop loss orders
   ```json
   "stoploss": "market"
   ```

## Trading Strategy Considerations

### 1. Lot Sizes

NSE equities typically trade in lot sizes of 1, but check specific instrument requirements.

### 2. Price Precision

NSE typically uses tick sizes of:
- Equities: ₹0.05 for stocks > ₹1000, ₹0.01 for others
- F&O: Varies by instrument

### 3. Circuit Limits

NSE has circuit breakers (typically ±10% or ±20% for most stocks). Orders outside these limits will be rejected.

### 4. Intraday vs Delivery

- **MIS orders**: Automatically squared off before market close (typically by 3:20 PM)
- **CNC orders**: For delivery-based trading

## Example Strategy Configuration

```python
# In your strategy file
class NSEStrategy(IStrategy):
    
    # Strategy specific settings
    timeframe = '5m'
    
    # Use INR as stake currency
    stake_currency = 'INR'
    
    # Minimal ROI for Indian market
    minimal_roi = {
        "60": 0.01,
        "30": 0.02,
        "0": 0.03
    }
    
    # Stoploss
    stoploss = -0.03  # 3% stop loss
    
    # Order types
    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }
    
    # Your strategy logic here
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Add your indicators
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Add your entry logic
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Add your exit logic
        return dataframe
```

## Running Freqtrade with OpenAlgo

### 1. Start OpenAlgo

```bash
# Start OpenAlgo server
cd /path/to/openalgo
python app.py
```

### 2. Verify OpenAlgo Connection

Test the connection using curl or your browser:
```bash
curl http://127.0.0.1:5000/api/v1/apiversion
```

### 3. Start Freqtrade

```bash
# Dry run (recommended for testing)
freqtrade trade --config config_openalgo_nse.json --strategy YourStrategy

# Live trading (use with caution)
freqtrade trade --config config_openalgo_nse.json --strategy YourStrategy
```

## Monitoring and Logging

### View Positions

```bash
# Check open positions
freqtrade show_trades

# Check current status
freqtrade status
```

### OpenAlgo Dashboard

Access the OpenAlgo web interface at `http://127.0.0.1:5000` to:
- View order history
- Check positions
- Monitor account balance
- View trade analytics

## Troubleshooting

### Common Issues

1. **Connection Error**
   - Ensure OpenAlgo server is running
   - Verify the API URL in configuration
   - Check firewall settings

2. **Authentication Failed**
   - Verify API key is correct
   - Ensure API key is active in OpenAlgo

3. **Order Rejection**
   - Check if you have sufficient balance
   - Verify symbol format is correct
   - Ensure market is open
   - Check if circuit limits are hit

4. **Symbol Not Found**
   - Verify symbol name matches NSE symbol exactly
   - Check if symbol is available on your broker
   - Ensure correct exchange is specified

### Debug Mode

Enable debug logging in your configuration:

```json
{
    "verbosity": 3,
    "logfile": "logs/freqtrade.log"
}
```

## Best Practices

1. **Start with Dry Run**: Always test your strategy in dry-run mode first
2. **Small Position Sizes**: Start with small stake amounts
3. **Monitor Market Hours**: Ensure your bot respects market hours
4. **Set Appropriate Stop Loss**: Always use stop loss for risk management
5. **Regular Monitoring**: Monitor your trades regularly, especially initially
6. **Backup Configuration**: Keep backups of your configuration and strategy files
7. **Update Symbols**: Keep your pair whitelist updated with actively traded stocks

## Advanced Features

### Custom Product Type

Pass product type in order parameters:

```python
def custom_entry_price(self, pair: str, current_time, proposed_rate, 
                       entry_tag, side, **kwargs) -> float:
    
    # Set product type for this order
    kwargs['order_params'] = {'product': 'CNC'}  # For delivery
    
    return proposed_rate
```

### Bracket Orders

Configure bracket orders with target and stop loss:

```python
def custom_stoploss(self, pair: str, trade, current_time, current_rate,
                   current_profit, **kwargs) -> float:
    
    # Dynamic stop loss based on profit
    if current_profit > 0.02:
        return 0.01  # Trail stop loss
    
    return self.stoploss
```

## Security Considerations

1. **API Key Protection**: Never commit API keys to version control
2. **Use Environment Variables**: Store sensitive data in environment variables
3. **Secure Network**: Use HTTPS for remote OpenAlgo servers
4. **Regular Updates**: Keep OpenAlgo and Freqtrade updated
5. **Access Control**: Restrict access to your OpenAlgo instance

## Support and Resources

- **OpenAlgo Documentation**: https://docs.openalgo.in
- **Freqtrade Documentation**: https://www.freqtrade.io
- **OpenAlgo GitHub**: https://github.com/marketcalls/openalgo
- **Freqtrade GitHub**: https://github.com/freqtrade/freqtrade

## Disclaimer

Trading in equity and derivative markets involves significant risk. This integration is provided as-is without any warranty. Always test thoroughly with paper trading before using real money. The developers are not responsible for any financial losses incurred through the use of this software.

## Contributing

If you find bugs or have suggestions for improvements, please:
1. Check existing issues on GitHub
2. Create a new issue with detailed information
3. Submit pull requests for bug fixes or enhancements

---

**Last Updated**: 2025-10-15

For the latest updates and detailed API documentation, refer to the official OpenAlgo and Freqtrade documentation.
