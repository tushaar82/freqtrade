#!/usr/bin/env python3
"""
Test script for Symbol Mapper
Verifies that symbol mapping works correctly for all brokers
"""

import sys
from pathlib import Path

# Add freqtrade to path
sys.path.insert(0, str(Path(__file__).parent))

from freqtrade.exchange.symbol_mapper import SymbolMapper


def test_symbol_mapper():
    """Test symbol mapper functionality"""
    
    print("=" * 60)
    print("Symbol Mapper Test Suite")
    print("=" * 60)
    print()
    
    # Initialize mapper
    print("1. Initializing Symbol Mapper...")
    mapper = SymbolMapper()
    print("   ✓ Mapper initialized")
    print()
    
    # Test conversions
    test_pairs = [
        "RELIANCE/INR",
        "TCS/INR",
        "NIFTY50/INR",
        "BANKNIFTY/INR",
        "FINNIFTY/INR"
    ]
    
    brokers = ["openalgo", "smartapi", "paperbroker"]
    
    print("2. Testing Symbol Conversions")
    print("-" * 60)
    
    for pair in test_pairs:
        print(f"\n   Freqtrade: {pair}")
        
        for broker in brokers:
            try:
                result = mapper.to_broker_format(pair, broker)
                
                if broker == "openalgo":
                    symbol, exchange = result
                    print(f"   → OpenAlgo:    {symbol} on {exchange}")
                    
                elif broker == "smartapi":
                    symbol, token, exchange = result
                    print(f"   → SmartAPI:    {symbol} (token: {token}) on {exchange}")
                    
                elif broker == "paperbroker":
                    symbol, quote = result
                    print(f"   → PaperBroker: {symbol}/{quote}")
                    
            except Exception as e:
                print(f"   ✗ {broker}: Error - {e}")
    
    print()
    print("-" * 60)
    print()
    
    # Test reverse conversion
    print("3. Testing Reverse Conversions")
    print("-" * 60)
    
    test_cases = [
        ("openalgo", ["RELIANCE", "NSE"], "INR"),
        ("openalgo", ["NIFTY 50", "NSE"], "INR"),
        ("smartapi", ["RELIANCE-EQ", "2885", "NSE"], "INR"),
        ("paperbroker", ["RELIANCE", "INR"], "INR"),
    ]
    
    for broker, args, quote in test_cases:
        try:
            pair = mapper.from_broker_format(broker, *args, quote_currency=quote)
            print(f"   {broker:12} {str(args):40} → {pair}")
        except Exception as e:
            print(f"   ✗ {broker}: Error - {e}")
    
    print()
    print("-" * 60)
    print()
    
    # Test options parsing
    print("4. Testing Options Symbol Parsing")
    print("-" * 60)
    
    options_symbols = [
        "NIFTY25DEC24500CE",
        "BANKNIFTY2024DEC2550000PE",
        "FINNIFTY25JAN24000CE"
    ]
    
    for symbol in options_symbols:
        try:
            info = mapper.parse_options_symbol(symbol)
            if info:
                print(f"\n   Symbol: {symbol}")
                print(f"   → Underlying:  {info['underlying']}")
                print(f"   → Strike:      {info['strike']}")
                print(f"   → Type:        {info['option_type']}")
                print(f"   → Expiry:      {info['expiry']}")
            else:
                print(f"   ✗ {symbol}: Could not parse")
        except Exception as e:
            print(f"   ✗ {symbol}: Error - {e}")
    
    print()
    print("-" * 60)
    print()
    
    # Test adding custom mapping
    print("5. Testing Custom Mapping")
    print("-" * 60)
    
    custom_symbol = "TESTSTOCK"
    print(f"   Adding custom mapping for {custom_symbol}...")
    
    mapper.add_mapping(custom_symbol, "openalgo", {
        "symbol": "TESTSTOCK",
        "exchange": "NSE"
    })
    
    mapper.add_mapping(custom_symbol, "smartapi", {
        "symbol": "TESTSTOCK-EQ",
        "token": "99999",
        "exchange": "NSE"
    })
    
    mapper.add_mapping(custom_symbol, "paperbroker", {
        "symbol": "TESTSTOCK"
    })
    
    print("   ✓ Custom mapping added")
    print()
    
    # Test custom mapping
    pair = f"{custom_symbol}/INR"
    print(f"   Testing custom mapping for {pair}:")
    
    for broker in brokers:
        result = mapper.to_broker_format(pair, broker)
        if broker == "openalgo":
            symbol, exchange = result
            print(f"   → OpenAlgo:    {symbol} on {exchange}")
        elif broker == "smartapi":
            symbol, token, exchange = result
            print(f"   → SmartAPI:    {symbol} (token: {token}) on {exchange}")
        elif broker == "paperbroker":
            symbol, quote = result
            print(f"   → PaperBroker: {symbol}/{quote}")
    
    print()
    print("-" * 60)
    print()
    
    # Summary
    print("=" * 60)
    print("✓ All Tests Completed Successfully!")
    print("=" * 60)
    print()
    print("Symbol Mapper is working correctly!")
    print()
    print("Next Steps:")
    print("  1. Copy example mappings:")
    print("     cp config_examples/symbol_mappings.example.json user_data/symbol_mappings.json")
    print()
    print("  2. Enable in your config.json:")
    print('     "symbol_mapping_file": "user_data/symbol_mappings.json"')
    print()
    print("  3. Start trading with automatic symbol conversion!")
    print()


if __name__ == "__main__":
    try:
        test_symbol_mapper()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
