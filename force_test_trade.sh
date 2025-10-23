#!/bin/bash
# Force a test trade via FreqUI API

echo "Force Test Trade via API"
echo "========================"
echo ""

# Get JWT token (you need to login to FreqUI first to get this)
# For now, we'll use the forcebuy command directly

echo "Attempting to force a buy order..."
echo ""

# Use freqtrade forcebuy command
./venv/bin/freqtrade forcebuy RELIANCE/INR --config config.json --strategy AggressiveTestStrategy

echo ""
echo "Check FreqUI to see the trade!"
echo "http://localhost:8080"
