# New Features: Symbol Mapping & Backtesting UI

## 🎉 What's New?

We've added two major features to make NSE trading with Freqtrade even better:

1. **Universal Symbol Mapping System** 🔄
2. **Enhanced Backtesting UI** 📊

---

## 1. Universal Symbol Mapping System

### Problem Solved

Different brokers use different symbol formats:
- **OpenAlgo**: `RELIANCE` on `NSE`
- **SmartAPI**: `RELIANCE-EQ` with token `2885`
- **Freqtrade**: `RELIANCE/INR`

This caused confusion and required manual conversion. **Not anymore!**

### Solution

A centralized symbol mapping system that automatically converts between formats.

### Key Features

✅ **Automatic Conversion**: No manual symbol conversion needed  
✅ **Multi-Broker Support**: OpenAlgo, SmartAPI, Paper Broker  
✅ **Configurable**: Customize mappings via JSON file  
✅ **Options Support**: Parse and convert options symbols  
✅ **Token Management**: Automatic token lookup for SmartAPI  

### Quick Start

1. **Copy example mappings**:
   ```bash
   cp config_examples/symbol_mappings.example.json user_data/symbol_mappings.json
   ```

2. **Enable in config**:
   ```json
   {
     "exchange": {
       "name": "paperbroker",
       "symbol_mapping_file": "user_data/symbol_mappings.json"
     }
   }
   ```

3. **Use in strategies**:
   ```python
   # Just use standard Freqtrade format!
   pair = "RELIANCE/INR"  # Automatically converted to broker format
   ```

### Pre-configured Symbols

The system comes with mappings for:

**Indices**: NIFTY50, BANKNIFTY, FINNIFTY, MIDCPNIFTY  
**Stocks**: RELIANCE, TCS, INFY, HDFC, SBIN, ICICIBANK, AXISBANK, KOTAKBANK, LT, WIPRO, TATAMOTORS

### Documentation

See **[SYMBOL_MAPPING_GUIDE.md](SYMBOL_MAPPING_GUIDE.md)** for complete documentation.

---

## 2. Enhanced Backtesting UI

### Problem Solved

Running backtests from command line was:
- ❌ Complex for beginners
- ❌ Hard to visualize results
- ❌ Difficult to compare strategies
- ❌ No real-time progress monitoring

### Solution

A beautiful web-based backtesting interface with real-time monitoring and rich visualizations.

### Key Features

✅ **Web Interface**: Run backtests from your browser  
✅ **Real-time Progress**: Monitor backtest progress live  
✅ **Rich Metrics**: Comprehensive performance analysis  
✅ **History Management**: View and compare past backtests  
✅ **Export Results**: Download reports in JSON/CSV  
✅ **Strategy Comparison**: Compare multiple strategies  

### Quick Start

1. **Start Backtesting UI**:
   ```bash
   ./backtest_ui.sh
   ```

2. **Open Browser**:
   Navigate to http://localhost:8080

3. **Run Backtest**:
   - Click "Backtest" tab
   - Select strategy
   - Configure parameters
   - Click "Start Backtest"
   - View results!

### Features in Detail

#### Real-time Monitoring
- Progress bar shows completion percentage
- Live trade count updates
- Current processing step displayed
- Estimated time remaining

#### Performance Metrics
- Total Profit/Loss
- Win Rate
- Profit Factor
- Sharpe Ratio
- Max Drawdown
- Trade Statistics

#### Visualizations
- Equity Curve
- Daily Profit Chart
- Trade Distribution
- Pair Performance
- Drawdown Chart

#### History Management
- View all past backtests
- Filter by date, strategy, profit
- Delete old results
- Export to file
- Add notes to backtests

### Documentation

See **[BACKTESTING_UI_GUIDE.md](BACKTESTING_UI_GUIDE.md)** for complete documentation.

---

## Integration with Paper Broker

Both features work seamlessly with Paper Broker:

```json
{
  "exchange": {
    "name": "paperbroker",
    "initial_balance": 100000,
    "nse_simulation": true,
    "simulate_holidays": true,
    "symbol_mapping_file": "user_data/symbol_mappings.json",
    "pair_whitelist": [
      "RELIANCE/INR",
      "TCS/INR",
      "NIFTY50/INR",
      "BANKNIFTY/INR"
    ]
  }
}
```

### Paper Broker Features

- ✅ NSE market hours simulation
- ✅ Holiday calendar
- ✅ Realistic slippage and fees
- ✅ Symbol mapping support
- ✅ CSV data support for backtesting

---

## File Structure

### New Files

```
freqtrade/
├── freqtrade/exchange/
│   └── symbol_mapper.py                    # Symbol mapping utility
├── config_examples/
│   └── symbol_mappings.example.json        # Example symbol mappings
├── backtest_ui.sh                          # Quick start script
├── SYMBOL_MAPPING_GUIDE.md                 # Symbol mapping documentation
├── BACKTESTING_UI_GUIDE.md                 # Backtesting UI documentation
└── NEW_FEATURES_README.md                  # This file
```

### Modified Files

```
freqtrade/
└── freqtrade/exchange/
    └── paperbroker.py                      # Added symbol mapper integration
```

---

## Usage Examples

### Example 1: Paper Trading with Symbol Mapping

```bash
# 1. Copy symbol mappings
cp config_examples/symbol_mappings.example.json user_data/symbol_mappings.json

# 2. Start paper trading
./run_paper.sh

# 3. Symbols are automatically converted!
```

### Example 2: Backtesting with UI

```bash
# 1. Start backtesting UI
./backtest_ui.sh

# 2. Open http://localhost:8080

# 3. Navigate to Backtest tab

# 4. Configure and run backtest

# 5. View beautiful results!
```

### Example 3: Adding Custom Symbol

Edit `user_data/symbol_mappings.json`:

```json
{
  "MYNEWSTOCK": {
    "openalgo": {
      "symbol": "MYNEWSTOCK",
      "exchange": "NSE"
    },
    "smartapi": {
      "symbol": "MYNEWSTOCK-EQ",
      "token": "12345",
      "exchange": "NSE"
    },
    "paperbroker": {
      "symbol": "MYNEWSTOCK"
    }
  }
}
```

### Example 4: Programmatic Symbol Mapping

```python
from freqtrade.exchange.symbol_mapper import get_symbol_mapper

# Get mapper
mapper = get_symbol_mapper()

# Convert to OpenAlgo format
symbol, exchange = mapper.to_broker_format("RELIANCE/INR", "openalgo")
print(f"OpenAlgo: {symbol} on {exchange}")  # RELIANCE on NSE

# Convert to SmartAPI format
symbol, token, exchange = mapper.to_broker_format("RELIANCE/INR", "smartapi")
print(f"SmartAPI: {symbol} (token: {token}) on {exchange}")  # RELIANCE-EQ (token: 2885) on NSE

# Parse options symbol
info = mapper.parse_options_symbol("NIFTY25DEC24500CE")
print(info)  # {'underlying': 'NIFTY', 'strike': 24500.0, 'option_type': 'CALL', ...}
```

---

## API Reference

### Symbol Mapper

```python
from freqtrade.exchange.symbol_mapper import get_symbol_mapper

# Get singleton instance
mapper = get_symbol_mapper(config_path="user_data/symbol_mappings.json")

# Convert to broker format
symbol, exchange = mapper.to_broker_format("RELIANCE/INR", "openalgo")

# Convert from broker format
pair = mapper.from_broker_format("openalgo", "RELIANCE", "NSE")

# Parse options symbol
info = mapper.parse_options_symbol("NIFTY25DEC24500CE")

# Add custom mapping
mapper.add_mapping("NEWSYMBOL", "openalgo", {
    "symbol": "NEWSYMBOL",
    "exchange": "NSE"
})

# Save mappings
mapper.save_mappings("user_data/symbol_mappings.json")
```

### Backtesting API

```bash
# Start backtest
POST /api/v1/backtest
{
  "strategy": "SampleStrategy",
  "timeframe": "5m",
  "timerange": "20240101-20241231"
}

# Get status
GET /api/v1/backtest

# Get history
GET /api/v1/backtest/history

# Delete backtest
DELETE /api/v1/backtest
```

---

## Configuration Examples

### Minimal Config with Symbol Mapping

```json
{
  "exchange": {
    "name": "paperbroker",
    "symbol_mapping_file": "user_data/symbol_mappings.json"
  }
}
```

### Full Config with All Features

```json
{
  "max_open_trades": 5,
  "stake_currency": "INR",
  "stake_amount": 10000,
  "dry_run": false,
  
  "exchange": {
    "name": "paperbroker",
    "initial_balance": 100000,
    "slippage_percent": 0.05,
    "commission_percent": 0.03,
    "nse_simulation": true,
    "simulate_holidays": true,
    "symbol_mapping_file": "user_data/symbol_mappings.json",
    "pair_whitelist": [
      "RELIANCE/INR",
      "TCS/INR",
      "NIFTY50/INR",
      "BANKNIFTY/INR"
    ]
  },
  
  "api_server": {
    "enabled": true,
    "listen_ip_address": "127.0.0.1",
    "listen_port": 8080,
    "username": "admin",
    "password": "admin123"
  }
}
```

---

## Troubleshooting

### Symbol Mapping Issues

**Problem**: Symbol not found  
**Solution**: Add symbol to `user_data/symbol_mappings.json`

**Problem**: Token lookup failed (SmartAPI)  
**Solution**: Update token in mapping file from Angel One's master file

**Problem**: Conversion error  
**Solution**: Check logs, verify JSON syntax, ensure all required fields present

### Backtesting UI Issues

**Problem**: UI not loading  
**Solution**: Run `freqtrade install-ui` or use `./backtest_ui.sh`

**Problem**: Backtest not starting  
**Solution**: Check if another backtest is running, verify strategy exists

**Problem**: No trades generated  
**Solution**: Review strategy logic, check data quality, adjust timeframe

---

## Performance Tips

### Symbol Mapping

1. **Cache Mappings**: Mappings are cached in memory for fast access
2. **Minimal Lookups**: Conversion happens only when needed
3. **Batch Operations**: Multiple symbols converted efficiently

### Backtesting

1. **Use Appropriate Timeframe**: Smaller timeframes = more data = slower
2. **Limit Timerange**: Start with shorter periods for testing
3. **Enable Caching**: Reuse data between backtests
4. **Optimize Strategy**: Simpler strategies backtest faster

---

## Migration Guide

### From Old System

If you were manually converting symbols:

**Before**:
```python
# Manual conversion
if broker == "openalgo":
    symbol = pair.split('/')[0]
    exchange = "NSE"
elif broker == "smartapi":
    symbol = f"{pair.split('/')[0]}-EQ"
    token = lookup_token(symbol)
```

**After**:
```python
# Automatic conversion
from freqtrade.exchange.symbol_mapper import get_symbol_mapper

mapper = get_symbol_mapper()
symbol, exchange = mapper.to_broker_format(pair, broker)
```

### From Command Line Backtesting

**Before**:
```bash
freqtrade backtest --config config.json --strategy MyStrategy --timerange 20240101-20241231
```

**After**:
```bash
# Option 1: Still use command line (works as before)
freqtrade backtest --config config.json --strategy MyStrategy --timerange 20240101-20241231

# Option 2: Use new UI
./backtest_ui.sh
# Then use web interface
```

---

## Roadmap

### Planned Features

- [ ] Auto-download SmartAPI token master file
- [ ] Symbol search in UI
- [ ] Bulk symbol import
- [ ] Symbol validation tool
- [ ] Advanced backtest comparison
- [ ] Export backtest reports as PDF
- [ ] Real-time backtest streaming
- [ ] Strategy optimization in UI

---

## Contributing

Want to add more symbols or improve the system?

1. Fork the repository
2. Add your symbols to `config_examples/symbol_mappings.example.json`
3. Test with Paper Broker
4. Submit a pull request

---

## Support

### Documentation

- [Symbol Mapping Guide](SYMBOL_MAPPING_GUIDE.md)
- [Backtesting UI Guide](BACKTESTING_UI_GUIDE.md)
- [NSE Trading Guide](NSE_TRADING_COMPLETE_GUIDE.md)

### Getting Help

1. Check documentation first
2. Review logs for errors
3. Test with Paper Broker
4. Open an issue on GitHub

---

## Credits

Developed for the Freqtrade NSE Trading community.

Special thanks to all contributors and testers!

---

## License

Same as Freqtrade - GPLv3

---

**Happy Trading! 🚀📈**
