#!/usr/bin/env bash
# Freqtrade Clean Script for Indian Brokers
# Removes cache files, logs, and temporary data

set -e

echo "Freqtrade Cleanup Script"
echo "======================="
echo ""

# Stop freqtrade if running
if pgrep -f "freqtrade" > /dev/null; then
    echo "Stopping Freqtrade..."
    ./stop.sh 2>/dev/null || true
    sleep 2
fi

# Clean cache files
echo "Cleaning cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Clean user data (with confirmation)
read -p "Clean log files? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleaning logs..."
    rm -rf user_data/logs/* 2>/dev/null || true
    echo "Logs cleaned"
fi

read -p "Clean temporary data files? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleaning temporary data..."
    rm -rf user_data/data/*.json.tmp 2>/dev/null || true
    rm -rf user_data/data/*.h5.tmp 2>/dev/null || true
    echo "Temporary data cleaned"
fi

read -p "Clean downloaded market data? (WARNING: You'll need to re-download) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleaning market data..."
    rm -rf user_data/data/*-*.json 2>/dev/null || true
    rm -rf user_data/data/*.h5 2>/dev/null || true
    echo "Market data cleaned"
fi

# Clean broker-specific caches
echo "Cleaning broker-specific caches..."
rm -f ~/.freqtrade_lot_sizes.json 2>/dev/null || true
rm -f ~/.freqtrade_zerodha_token 2>/dev/null || true
echo "Broker caches cleaned"

# Clean build artifacts
if [ -d "build" ] || [ -d "dist" ]; then
    read -p "Clean build artifacts? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Cleaning build artifacts..."
        rm -rf build dist 2>/dev/null || true
        echo "Build artifacts cleaned"
    fi
fi

echo ""
echo "Cleanup complete!"
echo ""
echo "To perform a full reinstall:"
echo "  1. Remove virtual environment: rm -rf .venv"
echo "  2. Run installation: ./install.sh"
