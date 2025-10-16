# Options Trading Data Flow & Fixes

## Overview
This document describes the complete data flow from market data to order placement for options trading in Freqtrade, and the fixes implemented to ensure consistency between chart data and current prices.

## Problem Statement

### 1. OHLCV vs Ticker Price Mismatch
**Issue**: The candlestick charts in FreqUI were showing historical OHLCV data that didn't match the current ticker price used for order placement.

**Root Cause**: 
- `fetch_ohlcv()` returned the last N candles from CSV data
- `fetch_ticker()` used `_simulate_price()` which advanced through CSV data sequentially using an index
- This caused the "current price" to be from a different time period than the displayed chart data

**Impact**: Traders would see one price on charts but orders would execute at a different price, causing confusion and incorrect trading decisions.

### 2. Options Lot Size Requirements
**Issue**: Options trading requires quantities to be in multiples of lot sizes (e.g., NIFTY = 25, BANKNIFTY = 15).

**Root Cause**: 
- Stake amount calculations didn't account for lot size requirements
- Order placement didn't validate lot size multiples
- Quantity calculations were based on individual units rather than lots

**Impact**: Orders would fail or execute with incorrect quantities.

---

## Data Flow Architecture

### Complete Data Flow (Fixed)

```
┌─────────────────────────────────────────────────────────────────┐
│                     CSV Data Loading                             │
│  user_data/raw_data/SYMBOL_minute.csv                           │
│  → Load into DataFrame                                           │
│  → Initialize price_cache with LATEST close price               │
│  → Store current_csv_time for consistency                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                Market Data Retrieval                             │
├─────────────────────────────────────────────────────────────────┤
│  fetch_ohlcv(pair, timeframe, limit)                            │
│  → Returns LAST N candles from CSV                              │
│  → Resamples to requested timeframe                             │
│  → Used for: Charts, Indicators, Strategy Analysis              │
│                                                                   │
│  fetch_ticker(pair)                                              │
│  → Returns LATEST close price from CSV                          │
│  → Matches the rightmost candle in charts                       │
│  → Used for: Current price, Order execution                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              Stake Amount Calculation (Wallets)                  │
├─────────────────────────────────────────────────────────────────┤
│  get_trade_stake_amount(pair, max_open_trades)                  │
│  1. Get base stake amount from config                           │
│  2. Detect instrument type (EQUITY vs OPTIONS)                  │
│  3. If OPTIONS:                                                  │
│     a. Get current price via fetch_ticker()                     │
│     b. Get lot size from LotSizeManager                         │
│     c. Calculate: lots = stake_amount / (price * lot_size)     │
│     d. Adjust: stake_amount = lots * lot_size * price          │
│  4. Validate against available balance                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Order Creation (Exchange)                       │
├─────────────────────────────────────────────────────────────────┤
│  create_order(pair, side, amount, rate)                         │
│  1. Detect instrument type                                       │
│  2. If OPTIONS:                                                  │
│     a. Get lot size from LotSizeManager                         │
│     b. Validate: amount % lot_size == 0                         │
│     c. Adjust if needed: amount = (amount // lot_size) * lot_size│
│  3. Get execution price via _simulate_price()                   │
│     → Returns LATEST price (matches charts)                     │
│  4. Apply slippage for market orders                            │
│  5. Calculate cost = price * amount                             │
│  6. Validate sufficient balance                                 │
│  7. Execute order and update positions                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Fixes Implemented

### Fix 1: Consistent Price Source
**File**: `freqtrade/exchange/paperbroker.py`

**Changes**:
1. Modified `_simulate_price()` to always return the LATEST close price from CSV data
2. Removed sequential index advancement that caused time drift
3. Added `_current_csv_time` tracking for future enhancements

**Before**:
```python
def _simulate_price(self, pair: str) -> float:
    df = self._csv_data[pair]
    idx = self._csv_data_index[pair]
    current_candle = df.iloc[idx]
    self._csv_data_index[pair] = (idx + 1) % len(df)  # Advances!
    return float(current_candle['close'])
```

**After**:
```python
def _simulate_price(self, pair: str) -> float:
    df = self._csv_data[pair]
    last_idx = len(df) - 1
    latest_price = float(df.iloc[last_idx]['close'])  # Always latest!
    return latest_price
```

**Result**: Ticker price now matches the rightmost candle in FreqUI charts.

---

### Fix 2: Lot Size Validation in Orders
**File**: `freqtrade/exchange/paperbroker.py`

**Changes**:
1. Added lot size detection and validation in `create_order()`
2. Automatic quantity adjustment to nearest lot multiple
3. Clear logging of lot-based orders

**Implementation**:
```python
def create_order(self, pair, side, amount, ...):
    # Detect if this is an options instrument
    instrument_type = InstrumentType.from_symbol(pair)
    
    if instrument_type.requires_lot_size():
        lot_mgr = LotSizeManager(self._config)
        lot_size = lot_mgr.get_lot_size(pair)
        
        # Validate and adjust amount
        if amount % lot_size != 0:
            amount = int(amount / lot_size) * lot_size
            logger.warning(f"Adjusted amount to {amount} (lot size: {lot_size})")
        
        logger.info(f"Options order: {pair} amount={amount} (lots: {amount/lot_size})")
```

**Result**: All options orders are now lot-size compliant.

---

### Fix 3: Options Stake Calculation
**File**: `freqtrade/wallets.py` (Already implemented)

**Existing Implementation**:
```python
def calculate_options_stake(self, stake_amount, pair, instrument_type):
    if not instrument_type.requires_lot_size():
        return stake_amount
    
    # Get current price
    ticker = self._exchange.fetch_ticker(pair)
    current_price = ticker.get('last', 0)
    
    # Calculate lot-based quantity
    quantity, lots = self._lot_size_manager.calculate_quantity(
        stake_amount, current_price, pair, instrument_type
    )
    
    # Return adjusted stake
    return quantity * current_price
```

**Result**: Stake amounts are automatically adjusted to match lot size requirements.

---

## Lot Size Manager

### Default Lot Sizes
**File**: `freqtrade/data/lot_size_manager.py`

```python
# Index Options
'NIFTY': 25
'BANKNIFTY': 15
'FINNIFTY': 40
'MIDCPNIFTY': 75

# Stock Options
'RELIANCE': 250
'TCS': 150
'INFY': 300
'HDFCBANK': 550
```

### Usage Example

```python
from freqtrade.data.lot_size_manager import LotSizeManager
from freqtrade.enums import InstrumentType

lot_mgr = LotSizeManager(config)

# Get lot size
lot_size = lot_mgr.get_lot_size('NIFTY25DEC2450000CE')  # Returns 25

# Calculate quantity for stake amount
stake = 50000  # ₹50,000
price = 150    # ₹150 per option
quantity, lots = lot_mgr.calculate_quantity(
    stake, price, 'NIFTY25DEC2450000CE', InstrumentType.OPTIONS
)
# quantity = 75 (3 lots × 25)
# lots = 3
```

---

## Configuration for Options Trading

### Enable Options Trading
Add to your `config.json`:

```json
{
  "enable_options_trading": true,
  "stake_amount": 50000,
  "exchange": {
    "name": "paperbroker",
    "pair_whitelist": [
      "NIFTY25DEC2450000CE/INR",
      "BANKNIFTY25DEC2448000PE/INR"
    ]
  }
}
```

### Lot Size Configuration
Lot sizes are stored in `user_data/lot_sizes.json`:

```json
{
  "lot_sizes": {
    "indices": {
      "NIFTY": 25,
      "BANKNIFTY": 15
    },
    "stocks": {
      "RELIANCE": 250
    }
  },
  "last_updated": "2025-10-16T08:48:34+05:30"
}
```

---

## Testing

### Verify OHLCV Consistency
```bash
python test_paperbroker_ohlcv.py
```

This script:
1. Loads CSV data
2. Fetches OHLCV via PaperBroker
3. Fetches ticker price
4. Compares to ensure consistency

**Expected Output**:
```
✅ Ticker price matches last candle close
✅ OHLCV data matches CSV data
✅ All timestamps aligned
```

### Test Options Order
```python
from freqtrade.exchange.paperbroker import Paperbroker

exchange = Paperbroker(config)

# Place options order
order = exchange.create_order(
    pair='NIFTY25DEC2450000CE/INR',
    ordertype='market',
    side='buy',
    amount=25,  # 1 lot
    rate=None
)

# Check order details
print(f"Order ID: {order['id']}")
print(f"Amount: {order['amount']} (should be multiple of 25)")
print(f"Price: {order['price']}")
print(f"Cost: {order['cost']}")
```

---

## Benefits of These Fixes

### 1. **Accurate Price Display**
- Ticker price matches chart data
- No confusion between historical and current prices
- Consistent pricing across all UI elements

### 2. **Proper Lot Size Handling**
- Automatic quantity adjustment
- Prevents order rejection due to lot size violations
- Clear logging of lot-based calculations

### 3. **Correct Stake Calculations**
- Stake amounts respect lot size requirements
- Prevents over-trading or under-trading
- Accurate capital allocation

### 4. **Better Risk Management**
- Accurate position sizing
- Correct P&L calculations
- Proper margin requirements

---

## Common Issues & Solutions

### Issue: "Quantity not a multiple of lot size"
**Solution**: The system now auto-adjusts. Check logs for adjusted quantity.

### Issue: "Insufficient stake amount"
**Solution**: Increase stake_amount in config to at least `lot_size × option_price`.

### Issue: "Chart price doesn't match ticker"
**Solution**: Fixed! Both now use the latest CSV data.

### Issue: "Order executed at unexpected price"
**Solution**: Check slippage settings in PaperBroker config.

---

## Future Enhancements

1. **Real-time Price Updates**: Implement WebSocket for live price feeds
2. **Dynamic Lot Size Updates**: Auto-fetch lot sizes from NSE API
3. **Multi-leg Options Strategies**: Support for spreads, straddles, etc.
4. **Greeks Calculation**: Add Delta, Gamma, Theta, Vega calculations
5. **Expiry Management**: Auto-rollover or square-off before expiry

---

## Summary

The data flow is now consistent from CSV data → Charts → Ticker → Orders:

1. **CSV Data**: Loaded once, latest price cached
2. **Charts**: Show last N candles from CSV
3. **Ticker**: Returns latest close price (matches chart)
4. **Orders**: Use latest price, validate lot sizes
5. **Stake**: Auto-adjusted for lot requirements

All components now work together seamlessly for options trading! 🎯
