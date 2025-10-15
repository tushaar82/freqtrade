# CSV Data Mode - Real Market Simulation

## ✅ What's Been Implemented

PaperBroker now supports **REAL OHLCV data from CSV files** for realistic market simulation!

---

## 📊 How It Works

### 1. **CSV Data Loading**
- Place CSV files in `user_data/raw_data/` directory
- Supported format: `SYMBOL_minute.csv` or `SYMBOL_1m.csv`
- Example: `BANK_minute.csv` → `BANK/INR` pair

### 2. **Required CSV Format**
```csv
datetime,open,high,low,close,volume
2015-01-09 09:15:00,18845.9,18845.9,18801.7,18801.7,0
2015-01-09 09:16:00,18801.7,18806.05,18790.2,18794.65,0
...
```

**Required columns:**
- `datetime` - Timestamp (any format pandas can parse)
- `open` - Opening price
- `high` - High price
- `low` - Low price
- `close` - Closing price
- `volume` - Trading volume

### 3. **Automatic Detection**
When bot starts, it automatically:
1. Scans `user_data/raw_data/` for CSV files
2. Loads all CSV files found
3. Maps to trading pairs (e.g., `BANK_minute.csv` → `BANK/INR`)
4. Enables CSV data mode
5. Uses real data for price simulation and candle generation

---

## 🎯 Current Status

### ✅ Successfully Loaded:
```
Loading 1 CSV file(s) from /home/tushka/Projects/freqtrade/user_data/raw_data
Loading BANK_minute.csv...
Loaded 975,275 candles for BANK/INR (from 2015-01-09 09:15:00 to 2025-07-25 15:29:00)
✅ CSV data mode enabled with 1 pair(s): BANK/INR
```

### 📁 Data Available:
- **BANK/INR**: 975,275 1-minute candles
- **Time Range**: ~10 years of data (2015-2025)

---

## 🚀 Features

### ✅ **Real Price Movement**
- Uses actual historical OHLCV data
- Tick-by-tick replay of market movements
- No random simulation for CSV pairs

### ✅ **Timeframe Resampling**
- CSV data is 1-minute candles
- Automatically resamples to any timeframe:
  - 1m, 3m, 5m, 10m, 15m, 30m, 1h, 1d
- Uses proper OHLCV aggregation

### ✅ **Tick-by-Tick Playback**
- Advances through CSV data sequentially
- Each `fetch_ticker()` call gets next candle
- Simulates real market progression

### ✅ **Automatic Looping**
- When data ends, loops back to beginning
- Unlimited testing cycles
- Perfect for strategy development

---

## 📋 Usage

### **Current Configuration**

**Pair Whitelist:**
```json
{
  "pair_whitelist": [
    "BANK/INR",        ← Has CSV data (real)
    "RELIANCE/INR",    ← No CSV (simulated)
    "TCS/INR",         ← No CSV (simulated)
    ...
  ]
}
```

### **Behavior:**
- **BANK/INR**: Uses real CSV data
- **Other pairs**: Use random simulation

---

## 💡 Recommendations

### For Best Results:

1. **Use Only CSV Pairs:**
   ```bash
   # Edit config.json to only include BANK/INR
   python3 << 'PYTHON'
   import json
   with open('config.json', 'r') as f:
       config = json.load(f)
   config['exchange']['pair_whitelist'] = ['BANK/INR']
   with open('config.json', 'w') as f:
       json.dump(config, f, indent=4)
   PYTHON
   ```

2. **Add More CSV Files:**
   - Add `RELIANCE_minute.csv` for RELIANCE/INR
   - Add `TCS_minute.csv` for TCS/INR
   - All files in `user_data/raw_data/` are auto-loaded

3. **Clean Start:**
   ```bash
   ./freqtrade.sh run --clean-db
   ```

---

## 🔧 Technical Details

### **Modified Methods:**

1. **`_load_csv_data()`**
   - Scans raw_data directory
   - Loads all CSV files
   - Validates format
   - Stores in memory

2. **`_simulate_price()`**
   - Checks if CSV data exists
   - Returns real price from CSV
   - Advances to next candle
   - Falls back to simulation

3. **`fetch_ohlcv()`**
   - Uses CSV data when available
   - Calls `_fetch_ohlcv_from_csv()`
   - Returns real historical candles

4. **`_fetch_ohlcv_from_csv()`**
   - Extracts candles from CSV
   - Resamples to requested timeframe
   - Returns proper OHLCV format

5. **`_resample_candles()`**
   - Converts 1m to any timeframe
   - Proper OHLC aggregation
   - Volume summation

---

## 📊 Example Output

### **On Bot Start:**
```
✅ CSV data mode enabled with 1 pair(s): BANK/INR
Loaded 975,275 candles for BANK/INR
  From: 2015-01-09 09:15:00
  To:   2025-07-25 15:29:00
```

### **During Trading:**
- Prices advance through CSV data
- Each analysis gets next real candle
- Realistic market simulation

---

## 🎯 Benefits

✅ **Realistic Testing**
- Real market movements
- Actual price patterns
- True volatility

✅ **Reproducible Results**
- Same data every time
- Consistent testing
- Predictable behavior

✅ **Strategy Validation**
- Test on real history
- See how strategy performs
- Optimize parameters

✅ **No Internet Required**
- All data local
- Fast execution
- No API limits

---

## 🚨 Important Notes

1. **Time/Date Ignored:**
   - System time doesn't matter
   - Only OHLCV values used
   - Perfect for offline testing

2. **Sequential Playback:**
   - Data plays in order
   - Loops when finished
   - Cannot jump to specific date

3. **Memory Usage:**
   - Large CSV files loaded in RAM
   - 975K candles ≈ 150-200 MB
   - Multiple files use more memory

4. **Mixed Mode:**
   - CSV pairs use real data
   - Non-CSV pairs simulated
   - Works simultaneously

---

## 🎉 Summary

✅ **Working Features:**
- CSV data loading: ✓
- Real price simulation: ✓
- OHLCV fetching: ✓
- Timeframe resampling: ✓
- Tick-by-tick playback: ✓
- Automatic looping: ✓

**Your PaperBroker now simulates real market conditions!**

---

## 📝 Quick Commands

```bash
# View loaded data
./freqtrade.sh logs | grep -i csv

# Restart with clean DB
./freqtrade.sh run --clean-db

# Check status
./freqtrade.sh status

# Monitor trades
./freqtrade.sh logs
```

**Enjoy realistic market simulation!** 📈✨
