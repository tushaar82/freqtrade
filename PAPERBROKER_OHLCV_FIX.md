# PaperBroker OHLCV Data Fix (Updated)

## Problem
The candlestick chart in FreqUI was not displaying OHLC data that matched the input CSV files when using PaperBroker. Additionally, the current ticker price didn't match the displayed chart data, causing confusion during trading.

### Issues Identified:
1. PaperBroker's `_fetch_ohlcv_from_csv()` was not returning candles correctly
2. `fetch_ticker()` returned prices from a different time period than the chart data
3. Options trading required lot size validation that wasn't implemented in order placement

## Root Causes

### 1. Initial Index Set to Zero
**File**: `freqtrade/exchange/paperbroker.py` (line 257)

**Problem**: The CSV data index was initialized to 0, which meant that when `_fetch_ohlcv_from_csv()` tried to return candles "up to the current index", it would return an empty slice (`df.iloc[0:0]`).

**Fix**: Changed the initial index to a reasonable value (500 candles in) to ensure there's data to return:
```python
# Before:
self._csv_data_index[pair] = 0  # Start at beginning

# After:
# Start index at a reasonable position (e.g., 500 candles in) to allow backfill
# This ensures we have data to return when fetch_ohlcv is called
self._csv_data_index[pair] = min(500, len(df))
```

### 2. Missing 'since' Parameter Handling
**File**: `freqtrade/exchange/paperbroker.py` (lines 592-602)

**Problem**: The `_fetch_ohlcv_from_csv()` method accepted a `since` parameter but never used it. This meant that when FreqUI or backtesting requested candles from a specific timestamp, they were ignored.

**Fix**: Added proper handling for the `since` parameter to filter data from the requested timestamp:
```python
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
```

### 3. Incorrect Candle Selection Logic
**File**: `freqtrade/exchange/paperbroker.py` (lines 600-602)

**Problem**: When no `since` parameter was provided, the method was returning candles from an arbitrary index position instead of the most recent candles.

**Fix**: Changed to return the most recent candles using negative indexing:
```python
# Before:
idx = self._csv_data_index[pair]
start_idx = max(0, idx - limit)
end_idx = idx
candle_slice = df.iloc[start_idx:end_idx]

# After:
candle_slice = df.iloc[-limit:]
```

## Verification

A test script (`test_paperbroker_ohlcv.py`) was created to verify that PaperBroker returns OHLCV data that exactly matches the CSV input after resampling. The test confirms:

✅ **Timestamps match**: The returned timestamps are correct and in milliseconds
✅ **OHLC values match**: Open, High, Low, Close values match the CSV data exactly
✅ **Resampling works**: 1-minute data is correctly resampled to 5-minute (or other timeframes)

### Test Results
```
Candle 0:
  PaperBroker: 2025-07-25 15:20:00+00:00 | O:56519.70 H:56542.55 L:56515.70 C:56521.45
  CSV:         2025-07-25 15:20:00+00:00 | O:56519.70 H:56542.55 L:56515.70 C:56521.45
  ✅ MATCH!

Candle 1:
  PaperBroker: 2025-07-25 15:25:00+00:00 | O:56521.45 H:56550.75 L:56475.75 C:56520.45
  CSV:         2025-07-25 15:25:00+00:00 | O:56521.45 H:56550.75 L:56475.75 C:56520.45
  ✅ MATCH!
```

## Impact

- **FreqUI**: Candlestick charts display correct OHLC data from CSV files
- **Ticker Price**: Current price now matches the rightmost candle in charts
- **Options Trading**: Orders are validated for lot size requirements
- **Backtesting**: Historical data correctly loaded from CSV files
- **Live Trading**: Most recent candles correctly returned for trading decisions
- **API Endpoints**: `/pair_candles` endpoint returns correct data

## Files Modified

### 1. `/home/tushka/Projects/freqtrade/freqtrade/exchange/paperbroker.py`

**Initial Fixes** (from previous update):
- Line 257-259: Initialize CSV data index to reasonable value
- Lines 592-602: Add proper `since` parameter handling and fix candle selection logic

**New Fixes** (current update):
- Line 149: Added `_current_csv_time` tracking for consistent pricing
- Lines 262-267: Initialize price cache with LATEST close price (not first)
- Lines 343-378: Updated `_simulate_price()` to always return latest price
- Lines 698-724: Added lot size validation in `create_order()`

### 2. `/home/tushka/Projects/freqtrade/freqtrade/wallets.py`
- Lines 364-405: Options stake calculation (already implemented)
- Lines 428-431: Automatic lot size adjustment in stake calculation

### 3. `/home/tushka/Projects/freqtrade/freqtrade/data/lot_size_manager.py`
- Complete lot size management system (already implemented)

## Testing

To test the fix:
```bash
source venv/bin/activate
python test_paperbroker_ohlcv.py
```

To test with FreqUI:
1. Start Freqtrade with PaperBroker: `./freqtrade.sh trade`
2. Open FreqUI: `http://127.0.0.1:8080`
3. View candlestick charts - they should now match the CSV data

## Notes

- The timestamp conversion (`// 10**6`) was already correct - it converts pandas datetime (nanoseconds) to milliseconds
- The resampling logic was already correct - it properly aggregates OHLC data
- The main issues were:
  1. Candle selection logic (fixed in previous update)
  2. Price consistency between ticker and charts (fixed in current update)
  3. Lot size validation for options (fixed in current update)

## Additional Documentation

For complete details on options trading data flow, see:
- `OPTIONS_TRADING_DATA_FLOW.md` - Comprehensive guide to data flow and lot size handling

## Summary of Current Update (2025-10-16)

### What Changed:
1. **Price Consistency**: `_simulate_price()` now always returns the LATEST close price from CSV data
2. **Chart Alignment**: Ticker price matches the rightmost candle in FreqUI charts
3. **Lot Size Validation**: Orders for options are automatically validated and adjusted to lot size multiples
4. **Better Logging**: Clear indication when lot-based orders are placed

### Why It Matters:
- **No More Confusion**: What you see on charts is what you get in orders
- **Options Compliance**: All orders respect NSE lot size requirements
- **Accurate Trading**: Prices are consistent across all components
- **Risk Management**: Proper position sizing with lot-based calculations
