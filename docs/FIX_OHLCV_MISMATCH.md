# Fix OHLCV Data Mismatch Issue

## Problem
OHLCV values in FreqUI charts don't match the input CSV files.

## Root Causes

### 1. **Cached Data**
Freqtrade and PaperBroker cache OHLCV data for performance. Old cached data may be displayed instead of fresh CSV data.

### 2. **Database State**
The database may contain old trade data that affects wallet calculations and displayed prices.

### 3. **Browser Cache**
FreqUI in the browser may cache old chart data.

---

## Solution: Step-by-Step Fix

### Quick Fix (Recommended)

```bash
# 1. Make the script executable
chmod +x clear_cache_and_test.sh

# 2. Run the cache clearing script
./clear_cache_and_test.sh
```

This will:
- Stop Freqtrade
- Backup and clear databases
- Clear Python cache
- Test OHLCV consistency
- Show you if data matches

---

### Manual Fix (If Quick Fix Doesn't Work)

#### Step 1: Stop Freqtrade
```bash
pkill -f freqtrade
```

#### Step 2: Clear Database
```bash
# Backup existing database
mv user_data/tradesv3.sqlite user_data/tradesv3.sqlite.backup

# Clear dry-run database too
mv user_data/tradesv3.dryrun.sqlite user_data/tradesv3.dryrun.sqlite.backup
```

#### Step 3: Clear Python Cache
```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
```

#### Step 4: Run Diagnostic
```bash
python diagnose_ohlcv_mismatch.py
```

This will show you:
- Which CSV files are loaded
- Current ticker prices
- OHLCV data from PaperBroker
- Comparison with CSV data
- Exact mismatches (if any)

#### Step 5: Restart Freqtrade
```bash
freqtrade trade --config config.json
```

#### Step 6: Clear Browser Cache
In FreqUI:
1. Press `Ctrl + Shift + Delete`
2. Clear cached images and files
3. Hard refresh: `Ctrl + F5`

---

## Verification

### Test 1: Run OHLCV Test
```bash
python test_paperbroker_ohlcv.py
```

**Expected Output:**
```
✅ Ticker price matches last candle close
✅ OHLCV data matches CSV data
✅ All timestamps aligned
```

### Test 2: Check in FreqUI
1. Open FreqUI: http://127.0.0.1:8080
2. View a chart for any pair
3. Check the rightmost candle value
4. Compare with ticker price shown
5. They should match!

### Test 3: Manual Verification
```python
from freqtrade.exchange.paperbroker import Paperbroker
from freqtrade.configuration import Configuration

config = Configuration.from_files(['config.json'])
exchange = Paperbroker(config)

# Clear cache
exchange.clear_cache()

# Get ticker
ticker = exchange.fetch_ticker('RELIANCE/INR')
print(f"Ticker: {ticker['last']}")

# Get last candle
ohlcv = exchange.fetch_ohlcv('RELIANCE/INR', '5m', limit=1)
print(f"Last candle close: {ohlcv[-1][4]}")

# Should match!
```

---

## Why This Happens

### Before Fix:
```
CSV Data (loaded once) → Cached in memory
    ↓
_simulate_price() → Uses sequential index (advances over time)
    ↓
Charts show: Last N candles from CSV
Ticker shows: Price from index position (different time!)
    ↓
MISMATCH!
```

### After Fix:
```
CSV Data (loaded fresh) → No stale cache
    ↓
_simulate_price() → Always returns LATEST price
    ↓
Charts show: Last N candles from CSV
Ticker shows: LATEST price (same as rightmost candle)
    ↓
MATCH! ✅
```

---

## Additional Checks

### Check CSV File Format
Your CSV should look like this:
```csv
datetime,open,high,low,close,volume
2025-07-25 09:15:00,2500.00,2505.50,2498.00,2503.25,150000
2025-07-25 09:16:00,2503.25,2508.00,2502.00,2506.50,145000
...
```

**Requirements:**
- Column names: `datetime,open,high,low,close,volume`
- Datetime format: `YYYY-MM-DD HH:MM:SS`
- No missing values
- Sorted by datetime (oldest first)

### Check CSV File Location
```bash
ls -lh user_data/raw_data/*.csv
```

Should show files like:
- `RELIANCE_minute.csv`
- `NIFTY_minute.csv`
- etc.

### Check CSV Data Range
```bash
# First line (after header)
head -2 user_data/raw_data/RELIANCE_minute.csv

# Last line
tail -1 user_data/raw_data/RELIANCE_minute.csv
```

Make sure the last datetime is recent and matches what you expect to see.

---

## Common Issues

### Issue 1: "No CSV files found"
**Solution:**
```bash
# Check directory exists
ls user_data/raw_data/

# If not, create it
mkdir -p user_data/raw_data/

# Add your CSV files there
cp /path/to/your/data/*.csv user_data/raw_data/
```

### Issue 2: "CSV data not loaded"
**Solution:**
Check logs:
```bash
tail -f user_data/logs/freqtrade.log | grep CSV
```

Look for:
- "Loading X CSV file(s)"
- "Loaded Y candles for PAIR"
- Any error messages

### Issue 3: "Data matches but FreqUI shows different"
**Solution:**
This is a browser cache issue:
1. Open DevTools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"
4. Or use Incognito mode

### Issue 4: "Ticker price is 0 or very wrong"
**Solution:**
```python
# Check if CSV data is loaded
from freqtrade.exchange.paperbroker import Paperbroker
from freqtrade.configuration import Configuration

config = Configuration.from_files(['config.json'])
exchange = Paperbroker(config)

print(f"CSV data loaded: {exchange._use_csv_data}")
print(f"Pairs: {list(exchange._csv_data.keys())}")

# If False or empty, CSV loading failed
# Check CSV file format and location
```

---

## Prevention

To avoid this issue in the future:

### 1. Always Clear Cache After CSV Updates
```bash
# After updating CSV files
./clear_cache_and_test.sh
```

### 2. Use Fresh Database for Testing
```bash
# Start with clean slate
rm user_data/tradesv3.dryrun.sqlite
freqtrade trade --config config.json
```

### 3. Monitor Logs
```bash
# Watch for CSV loading messages
tail -f user_data/logs/freqtrade.log | grep -E "CSV|OHLCV|price"
```

### 4. Regular Testing
```bash
# Run test after any changes
python test_paperbroker_ohlcv.py
```

---

## Summary

**The fix ensures:**
1. ✅ Fresh CSV data loaded on startup
2. ✅ No stale cache affecting prices
3. ✅ Ticker price = Last candle close
4. ✅ Charts show actual CSV data
5. ✅ Consistent prices across all components

**To apply:**
```bash
./clear_cache_and_test.sh
```

**To verify:**
```bash
python diagnose_ohlcv_mismatch.py
```

If issues persist after following all steps, check:
- CSV file format and content
- File permissions
- Freqtrade logs for errors
- Python version compatibility

---

## Need Help?

Run the diagnostic tool for detailed analysis:
```bash
python diagnose_ohlcv_mismatch.py
```

This will show you exactly where the mismatch is occurring and provide specific recommendations.
