#!/usr/bin/env python3
"""
Diagnostic script to identify why OHLCV data doesn't match CSV input.
This will check all potential sources of mismatch.
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add freqtrade to path
sys.path.insert(0, str(Path(__file__).parent))

from freqtrade.configuration import Configuration
from freqtrade.exchange.paperbroker import Paperbroker
from freqtrade.enums import CandleType

def diagnose_ohlcv_mismatch():
    """Comprehensive diagnostic for OHLCV data mismatch"""
    
    print("=" * 80)
    print("🔍 OHLCV Data Mismatch Diagnostic Tool")
    print("=" * 80)
    print()
    
    # Step 1: Load config
    print("Step 1: Loading configuration...")
    try:
        config = Configuration.from_files(['config.json'])
        print("   ✅ Config loaded successfully")
    except Exception as e:
        print(f"   ❌ Failed to load config: {e}")
        return
    print()
    
    # Step 2: Check CSV files
    print("Step 2: Checking CSV files...")
    user_data_dir = config.get('user_data_dir', 'user_data')
    raw_data_dir = Path(user_data_dir) / 'raw_data'
    
    if not raw_data_dir.exists():
        print(f"   ❌ Raw data directory not found: {raw_data_dir}")
        return
    
    csv_files = list(raw_data_dir.glob('*.csv'))
    if not csv_files:
        print(f"   ❌ No CSV files found in {raw_data_dir}")
        return
    
    print(f"   ✅ Found {len(csv_files)} CSV file(s):")
    for csv_file in csv_files:
        print(f"      - {csv_file.name}")
    print()
    
    # Step 3: Initialize PaperBroker
    print("Step 3: Initializing PaperBroker...")
    try:
        exchange = Paperbroker(config)
        print(f"   ✅ PaperBroker initialized")
        print(f"   - CSV data loaded: {exchange._use_csv_data}")
        print(f"   - Pairs with CSV data: {list(exchange._csv_data.keys())}")
    except Exception as e:
        print(f"   ❌ Failed to initialize PaperBroker: {e}")
        import traceback
        traceback.print_exc()
        return
    print()
    
    # Step 4: Clear cache and reload
    print("Step 4: Clearing cache and reloading data...")
    try:
        exchange.clear_cache()
        print("   ✅ Cache cleared and data reloaded")
    except Exception as e:
        print(f"   ⚠️  Cache clear failed: {e}")
    print()
    
    # Step 5: Test each pair
    print("Step 5: Testing OHLCV data for each pair...")
    print()
    
    for pair in exchange._csv_data.keys():
        print(f"📊 Testing pair: {pair}")
        print("-" * 80)
        
        # Load original CSV
        csv_file = None
        for f in csv_files:
            symbol_name = f.stem.replace('_minute', '').replace('_1m', '').upper()
            if f"{symbol_name}/INR" == pair:
                csv_file = f
                break
        
        if not csv_file:
            print(f"   ⚠️  Could not find CSV file for {pair}")
            continue
        
        # Read CSV
        df_csv = pd.read_csv(csv_file, parse_dates=['datetime'])
        if df_csv['datetime'].dt.tz is None:
            df_csv['datetime'] = df_csv['datetime'].dt.tz_localize('UTC')
        
        print(f"   CSV file: {csv_file.name}")
        print(f"   Total candles in CSV: {len(df_csv)}")
        print(f"   Date range: {df_csv.iloc[0]['datetime']} to {df_csv.iloc[-1]['datetime']}")
        print()
        
        # Get last 5 candles from CSV
        print("   Last 5 candles from CSV (1-minute):")
        for i in range(max(0, len(df_csv) - 5), len(df_csv)):
            row = df_csv.iloc[i]
            print(f"      {i}: {row['datetime']} | O:{row['open']:.2f} H:{row['high']:.2f} "
                  f"L:{row['low']:.2f} C:{row['close']:.2f}")
        print()
        
        # Fetch ticker from PaperBroker
        print("   Fetching ticker from PaperBroker...")
        try:
            ticker = exchange.fetch_ticker(pair)
            ticker_price = ticker.get('last', 0)
            print(f"   ✅ Ticker price: ₹{ticker_price:.2f}")
            
            # Compare with last CSV candle
            last_csv_close = float(df_csv.iloc[-1]['close'])
            print(f"   📈 Last CSV close: ₹{last_csv_close:.2f}")
            
            if abs(ticker_price - last_csv_close) < 0.01:
                print(f"   ✅ MATCH! Ticker matches last CSV candle")
            else:
                print(f"   ❌ MISMATCH! Difference: ₹{abs(ticker_price - last_csv_close):.2f}")
                print(f"      This suggests the price cache is not using latest data")
        except Exception as e:
            print(f"   ❌ Failed to fetch ticker: {e}")
        print()
        
        # Fetch OHLCV from PaperBroker (5m timeframe)
        print("   Fetching OHLCV from PaperBroker (5m, last 5 candles)...")
        try:
            ohlcv = exchange.fetch_ohlcv(pair, '5m', limit=5)
            print(f"   ✅ Received {len(ohlcv)} candles")
            
            if ohlcv:
                print("   Last 5 candles from PaperBroker (5m):")
                for i, candle in enumerate(ohlcv):
                    dt = pd.to_datetime(candle[0], unit='ms', utc=True)
                    print(f"      {i}: {dt} | O:{candle[1]:.2f} H:{candle[2]:.2f} "
                          f"L:{candle[3]:.2f} C:{candle[4]:.2f}")
                print()
                
                # Resample CSV to 5m for comparison
                df_5m = df_csv.set_index('datetime').resample('5T').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna().reset_index()
                
                print("   Last 5 candles from CSV (resampled to 5m):")
                for i in range(max(0, len(df_5m) - 5), len(df_5m)):
                    row = df_5m.iloc[i]
                    print(f"      {i}: {row['datetime']} | O:{row['open']:.2f} H:{row['high']:.2f} "
                          f"L:{row['low']:.2f} C:{row['close']:.2f}")
                print()
                
                # Compare last candle
                pb_last = ohlcv[-1]
                csv_last = df_5m.iloc[-1]
                pb_dt = pd.to_datetime(pb_last[0], unit='ms', utc=True)
                
                print("   Comparison of LAST candle:")
                print(f"      PaperBroker: {pb_dt} | O:{pb_last[1]:.2f} H:{pb_last[2]:.2f} "
                      f"L:{pb_last[3]:.2f} C:{pb_last[4]:.2f}")
                print(f"      CSV:         {csv_last['datetime']} | O:{csv_last['open']:.2f} "
                      f"H:{csv_last['high']:.2f} L:{csv_last['low']:.2f} C:{csv_last['close']:.2f}")
                
                # Check match
                time_match = pb_dt == csv_last['datetime']
                ohlc_match = (
                    abs(pb_last[1] - csv_last['open']) < 0.01 and
                    abs(pb_last[2] - csv_last['high']) < 0.01 and
                    abs(pb_last[3] - csv_last['low']) < 0.01 and
                    abs(pb_last[4] - csv_last['close']) < 0.01
                )
                
                if time_match and ohlc_match:
                    print(f"   ✅ PERFECT MATCH!")
                else:
                    if not time_match:
                        print(f"   ❌ TIME MISMATCH!")
                        print(f"      Difference: {abs((pb_dt - csv_last['datetime']).total_seconds())} seconds")
                    if not ohlc_match:
                        print(f"   ❌ OHLC VALUES MISMATCH!")
                        print(f"      Open diff: {abs(pb_last[1] - csv_last['open']):.2f}")
                        print(f"      High diff: {abs(pb_last[2] - csv_last['high']):.2f}")
                        print(f"      Low diff: {abs(pb_last[3] - csv_last['low']):.2f}")
                        print(f"      Close diff: {abs(pb_last[4] - csv_last['close']):.2f}")
            else:
                print("   ❌ No OHLCV data returned!")
                
        except Exception as e:
            print(f"   ❌ Failed to fetch OHLCV: {e}")
            import traceback
            traceback.print_exc()
        
        print()
        print("=" * 80)
        print()
    
    # Step 6: Recommendations
    print("🎯 Recommendations:")
    print()
    print("If data STILL doesn't match after running this diagnostic:")
    print()
    print("1. **Clear all caches and restart:**")
    print("   bash clear_cache_and_test.sh")
    print()
    print("2. **Check CSV file format:**")
    print("   - Required columns: datetime, open, high, low, close, volume")
    print("   - Datetime should be in format: YYYY-MM-DD HH:MM:SS")
    print("   - No missing values or gaps")
    print()
    print("3. **Verify CSV data is recent:**")
    print("   - Check the last datetime in your CSV files")
    print("   - Ensure it's the data you expect to see")
    print()
    print("4. **Restart Freqtrade completely:**")
    print("   pkill -f freqtrade")
    print("   freqtrade trade --config config.json")
    print()
    print("5. **Check FreqUI cache:**")
    print("   - Clear browser cache (Ctrl+Shift+Delete)")
    print("   - Hard refresh (Ctrl+F5)")
    print()

if __name__ == "__main__":
    diagnose_ohlcv_mismatch()
