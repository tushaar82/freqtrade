#!/bin/bash
# Test OpenAlgo Trade Placement
# This script runs Freqtrade with the test strategy to verify order placement

set -e

echo "========================================="
echo "OpenAlgo Trade Placement Test"
echo "========================================="
echo ""
echo "⚠️  WARNING: This will place test trades!"
echo ""
echo "Current settings:"
echo "  - Strategy: TestOpenAlgoStrategy"
echo "  - Dry Run: Check config.json"
echo "  - Max Trades: 2"
echo "  - Stake: 1000 INR per trade"
echo ""
echo "The strategy will:"
echo "  ✓ Place random BUY signals (5% chance per candle)"
echo "  ✓ Place random SELL signals (10% chance per candle)"
echo "  ✓ Maximum 3 test trades total"
echo ""
echo "To enable REAL trading:"
echo "  1. Edit config.json"
echo "  2. Set 'dry_run': false"
echo "  3. Restart this script"
echo ""
read -p "Press Enter to start test, or Ctrl+C to cancel..."
echo ""

# Stop any running instance
pkill -f "freqtrade trade" 2>/dev/null || true
sleep 2

# Start Freqtrade with test strategy
echo "Starting Freqtrade with TestOpenAlgoStrategy..."
echo ""
./venv/bin/freqtrade trade \
    --config config.json \
    --strategy TestOpenAlgoStrategy \
    --logfile user_data/logs/test_trades.log

