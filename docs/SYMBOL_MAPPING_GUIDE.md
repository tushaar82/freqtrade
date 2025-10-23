# Symbol Mapping Guide

## Overview

Freqtrade now includes a universal symbol mapping system that allows seamless conversion between Freqtrade's internal format and various broker-specific formats (OpenAlgo, SmartAPI, Paper Broker, etc.).

## Why Symbol Mapping?

Different brokers use different symbol formats:

- **Freqtrade**: `RELIANCE/INR`, `NIFTY50/INR`
- **OpenAlgo**: `RELIANCE` on exchange `NSE`, `NIFTY 50` on `NSE`
- **SmartAPI (Angel One)**: `RELIANCE-EQ` with token `2885` on `NSE`, `NIFTY 50` with token `99926000`
- **Paper Broker**: Same as Freqtrade format

The symbol mapper handles all these conversions automatically!

## Features

✅ **Bidirectional Conversion**: Freqtrade ↔ Broker formats  
✅ **Multiple Broker Support**: OpenAlgo, SmartAPI, Paper Broker  
✅ **Configurable Mappings**: Custom symbol mappings via JSON file  
✅ **Options Support**: Parse and convert options symbols  
✅ **Token Lookup**: Automatic token resolution for SmartAPI  

## Configuration

### 1. Enable Symbol Mapping in Config

Add to your `config.json`:

```json
{
  "exchange": {
    "name": "paperbroker",  // or "openalgo", "smartapi"
    "symbol_mapping_file": "user_data/symbol_mappings.json"
  }
}
```

### 2. Create Symbol Mappings File

Copy the example file:

```bash
cp config_examples/symbol_mappings.example.json user_data/symbol_mappings.json
```

### 3. Customize Mappings

Edit `user_data/symbol_mappings.json`:

```json
{
  "RELIANCE": {
    "openalgo": {
      "symbol": "RELIANCE",
      "exchange": "NSE"
    },
    "smartapi": {
      "symbol": "RELIANCE-EQ",
      "token": "2885",
      "exchange": "NSE"
    },
    "paperbroker": {
      "symbol": "RELIANCE"
    }
  },
  "NIFTY50": {
    "openalgo": {
      "symbol": "NIFTY 50",
      "exchange": "NSE"
    },
    "smartapi": {
      "symbol": "NIFTY 50",
      "token": "99926000",
      "exchange": "NSE"
    },
    "paperbroker": {
      "symbol": "NIFTY50"
    }
  }
}
```

## Pre-configured Symbols

The following symbols are pre-configured:

### Indices
- `NIFTY50` → NIFTY 50
- `BANKNIFTY` → NIFTY BANK
- `FINNIFTY` → NIFTY FIN SERVICE
- `MIDCPNIFTY` → NIFTY MID SELECT

### Stocks
- `RELIANCE`, `TCS`, `INFY`, `HDFC`, `SBIN`
- `ICICIBANK`, `AXISBANK`, `KOTAKBANK`
- `LT`, `WIPRO`, `TATAMOTORS`

## Usage Examples

### In Your Strategy

The symbol mapper works automatically! Just use Freqtrade format in your strategy:

```python
class MyStrategy(IStrategy):
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Use standard Freqtrade format
        pair = metadata['pair']  # e.g., "RELIANCE/INR"
        
        # The exchange will automatically convert to broker format
        # when fetching data or placing orders
        return dataframe
```

### Manual Conversion (Advanced)

If you need to manually convert symbols:

```python
from freqtrade.exchange.symbol_mapper import get_symbol_mapper

# Get mapper instance
mapper = get_symbol_mapper()

# Convert Freqtrade → OpenAlgo
symbol, exchange = mapper.to_broker_format("RELIANCE/INR", "openalgo")
# Returns: ("RELIANCE", "NSE")

# Convert Freqtrade → SmartAPI
symbol, token, exchange = mapper.to_broker_format("RELIANCE/INR", "smartapi")
# Returns: ("RELIANCE-EQ", "2885", "NSE")

# Convert Broker → Freqtrade
pair = mapper.from_broker_format("openalgo", "RELIANCE", "NSE")
# Returns: "RELIANCE/INR"
```

### Options Trading

The mapper can parse options symbols:

```python
from freqtrade.exchange.symbol_mapper import get_symbol_mapper

mapper = get_symbol_mapper()

# Parse options symbol
info = mapper.parse_options_symbol("NIFTY25DEC24500CE")
# Returns:
# {
#     'underlying': 'NIFTY',
#     'strike': 24500.0,
#     'option_type': 'CALL',
#     'expiry': '25DEC',
#     'original': 'NIFTY25DEC24500CE'
# }
```

## Adding New Symbols

### Method 1: Edit JSON File

Add to `user_data/symbol_mappings.json`:

```json
{
  "NEWSYMBOL": {
    "openalgo": {
      "symbol": "NEWSYMBOL",
      "exchange": "NSE"
    },
    "smartapi": {
      "symbol": "NEWSYMBOL-EQ",
      "token": "12345",
      "exchange": "NSE"
    },
    "paperbroker": {
      "symbol": "NEWSYMBOL"
    }
  }
}
```

### Method 2: Programmatically

```python
from freqtrade.exchange.symbol_mapper import get_symbol_mapper

mapper = get_symbol_mapper()

# Add mapping
mapper.add_mapping("NEWSYMBOL", "openalgo", {
    "symbol": "NEWSYMBOL",
    "exchange": "NSE"
})

mapper.add_mapping("NEWSYMBOL", "smartapi", {
    "symbol": "NEWSYMBOL-EQ",
    "token": "12345",
    "exchange": "NSE"
})

# Save to file
mapper.save_mappings("user_data/symbol_mappings.json")
```

## Finding SmartAPI Tokens

SmartAPI requires symbol tokens. To find them:

1. **Download Master Symbol File**:
   ```python
   from SmartApi import SmartConnect
   
   smart_api = SmartConnect(api_key="your_key")
   # Login first...
   
   # Get all symbols
   symbols = smart_api.searchScrip("NSE", "RELIANCE")
   print(symbols)
   ```

2. **Use Online Resources**:
   - Angel One Symbol Master: https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json

3. **Common Tokens** (already in config):
   - NIFTY 50: `99926000`
   - NIFTY BANK: `99926009`
   - RELIANCE-EQ: `2885`
   - TCS-EQ: `11536`
   - INFY-EQ: `1594`

## Broker-Specific Notes

### OpenAlgo
- Uses simple symbol + exchange format
- No tokens required
- Supports NSE, BSE, NFO, MCX

### SmartAPI (Angel One)
- Requires symbol tokens
- Uses `-EQ` suffix for equities
- No suffix for F&O
- Tokens must be from Angel One's master file

### Paper Broker
- Uses same format as Freqtrade
- No conversion needed
- Simulates all exchanges

## Troubleshooting

### Symbol Not Found

If you get "Symbol not found" errors:

1. Check if symbol is in your mapping file
2. Verify the broker-specific format
3. For SmartAPI, ensure token is correct
4. Check exchange name (NSE, BSE, NFO, etc.)

### Token Lookup Failed (SmartAPI)

If token lookup fails:

1. Download latest symbol master from Angel One
2. Update tokens in your mapping file
3. Ensure you're using the correct exchange

### Conversion Errors

If conversion fails:

1. Check logs for detailed error messages
2. Verify JSON syntax in mapping file
3. Ensure all required fields are present
4. Test with a known working symbol first

## Best Practices

1. **Keep Mappings Updated**: Broker symbols can change
2. **Use Consistent Format**: Always use Freqtrade format in strategies
3. **Test First**: Test new symbols with paper broker before live trading
4. **Backup Mappings**: Keep a backup of your custom mappings
5. **Document Custom Symbols**: Add comments in your mapping file

## Integration with Exchanges

The symbol mapper is automatically integrated into:

- ✅ Paper Broker
- ✅ OpenAlgo
- ✅ SmartAPI
- ✅ Zerodha (future)

No code changes needed in your strategies!

## API Reference

### SymbolMapper Class

```python
class SymbolMapper:
    def __init__(self, config_path: Optional[str] = None)
    def load_mappings(self, config_path: str)
    def to_broker_format(self, pair: str, broker: str, default_exchange: str = "NSE") -> Tuple
    def from_broker_format(self, broker: str, *args, quote_currency: str = "INR") -> str
    def parse_options_symbol(self, symbol: str) -> Optional[Dict]
    def add_mapping(self, freqtrade_symbol: str, broker: str, mapping: Dict)
    def save_mappings(self, config_path: str)
```

### Global Instance

```python
from freqtrade.exchange.symbol_mapper import get_symbol_mapper

# Get singleton instance
mapper = get_symbol_mapper(config_path="user_data/symbol_mappings.json")
```

## Examples

See `config_examples/symbol_mappings.example.json` for complete examples.

## Support

For issues or questions:
1. Check this guide first
2. Review logs for error messages
3. Test with paper broker
4. Open an issue on GitHub

---

**Happy Trading! 🚀**
