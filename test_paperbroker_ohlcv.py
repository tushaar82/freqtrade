#!/usr/bin/env python3
"""Test script to verify PaperBroker OHLCV data matches CSV input"""

import sys
import pandas as pd
from pathlib import Path

# Add freqtrade to path
sys.path.insert(0, str(Path(__file__).parent))

from freqtrade.configuration import Configuration
from freqtrade.exchange.paperbroker import Paperbroker
from freqtrade.enums import CandleType

def test_paperbroker_ohlcv():
    """Test that PaperBroker returns correct OHLCV data from CSV"""
    
    # Load config
    config = Configuration.from_files(['config.json'])
    
    # Initialize PaperBroker directly
    exchange = Paperbroker(config)
    
    print(f"Exchange: {exchange.name}")
    print(f"Exchange ID: {exchange.id}")
    
    # Test pair
    pair = "RELIANCE/INR"
    timeframe = "5m"
    limit = 10
    
    print(f"\nFetching OHLCV for {pair} ({timeframe}, limit={limit})...")
    
    # Fetch OHLCV from PaperBroker
    ohlcv = exchange.fetch_ohlcv(pair, timeframe, limit=limit)
    
    print(f"\nReceived {len(ohlcv)} candles from PaperBroker:")
    print("Format: [timestamp_ms, open, high, low, close, volume]")
    for i, candle in enumerate(ohlcv[:5]):  # Show first 5
        ts_ms = candle[0]
        dt = pd.to_datetime(ts_ms, unit='ms', utc=True)
        print(f"  {i}: {dt} | O:{candle[1]:.2f} H:{candle[2]:.2f} L:{candle[3]:.2f} C:{candle[4]:.2f} V:{candle[5]:.0f}")
    
    # Load original CSV data
    csv_path = Path("user_data/raw_data/RELIANCE_minute.csv")
    if csv_path.exists():
        print(f"\nLoading original CSV data from {csv_path}...")
        # Load full CSV to get the last candles
        df = pd.read_csv(csv_path, parse_dates=['datetime'])
        
        # Ensure timezone-aware
        if df['datetime'].dt.tz is None:
            df['datetime'] = df['datetime'].dt.tz_localize('UTC')
        
        print(f"\nFirst 5 rows from CSV (1-minute data):")
        for i in range(min(5, len(df))):
            row = df.iloc[i]
            print(f"  {i}: {row['datetime']} | O:{row['open']:.2f} H:{row['high']:.2f} L:{row['low']:.2f} C:{row['close']:.2f} V:{row['volume']:.0f}")
        
        # Resample to 5m for comparison
        df_5m = df.set_index('datetime').resample('5T').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna().reset_index()
        
        print(f"\nAfter resampling to 5m (first 5 candles):")
        for i in range(min(5, len(df_5m))):
            row = df_5m.iloc[i]
            print(f"  {i}: {row['datetime']} | O:{row['open']:.2f} H:{row['high']:.2f} L:{row['low']:.2f} C:{row['close']:.2f} V:{row['volume']:.0f}")
        
        print(f"\nAfter resampling to 5m (LAST 5 candles - for comparison with PaperBroker):")
        for i in range(max(0, len(df_5m) - 5), len(df_5m)):
            row = df_5m.iloc[i]
            print(f"  {i}: {row['datetime']} | O:{row['open']:.2f} H:{row['high']:.2f} L:{row['low']:.2f} C:{row['close']:.2f} V:{row['volume']:.0f}")
        
        # Compare with PaperBroker data (compare with LAST candles from CSV)
        print("\n" + "="*80)
        print("COMPARISON: PaperBroker vs CSV (last candles)")
        print("="*80)
        
        # Get the last N candles from CSV to match PaperBroker output
        df_5m_last = df_5m.iloc[-len(ohlcv):]
        
        for i in range(min(3, len(ohlcv), len(df_5m_last))):
            pb_candle = ohlcv[i]
            csv_row = df_5m_last.iloc[i]
            
            pb_dt = pd.to_datetime(pb_candle[0], unit='ms', utc=True)
            csv_dt = csv_row['datetime']
            
            print(f"\nCandle {i}:")
            print(f"  PaperBroker: {pb_dt} | O:{pb_candle[1]:.2f} H:{pb_candle[2]:.2f} L:{pb_candle[3]:.2f} C:{pb_candle[4]:.2f}")
            print(f"  CSV:         {csv_dt} | O:{csv_row['open']:.2f} H:{csv_row['high']:.2f} L:{csv_row['low']:.2f} C:{csv_row['close']:.2f}")
            
            # Check if they match
            time_match = pb_dt == csv_dt
            ohlc_match = (
                abs(pb_candle[1] - csv_row['open']) < 0.01 and
                abs(pb_candle[2] - csv_row['high']) < 0.01 and
                abs(pb_candle[3] - csv_row['low']) < 0.01 and
                abs(pb_candle[4] - csv_row['close']) < 0.01
            )
            
            if time_match and ohlc_match:
                print(f"  ✅ MATCH!")
            else:
                if not time_match:
                    print(f"  ❌ TIME MISMATCH!")
                if not ohlc_match:
                    print(f"  ❌ OHLC MISMATCH!")
    else:
        print(f"\n⚠️  CSV file not found: {csv_path}")

if __name__ == "__main__":
    test_paperbroker_ohlcv()
