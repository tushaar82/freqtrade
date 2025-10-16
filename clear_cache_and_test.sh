#!/bin/bash
# Script to clear all caches and test OHLCV data consistency

echo "🧹 Clearing Freqtrade caches and data..."

# Stop any running Freqtrade instances
echo "1. Stopping Freqtrade..."
pkill -f freqtrade || true
sleep 2

# Clear database (if exists)
if [ -f "user_data/tradesv3.sqlite" ]; then
    echo "2. Backing up and clearing database..."
    mv user_data/tradesv3.sqlite user_data/tradesv3.sqlite.backup.$(date +%Y%m%d_%H%M%S)
    echo "   ✅ Database backed up and cleared"
else
    echo "2. No database found (OK for fresh start)"
fi

# Clear dry-run database (if exists)
if [ -f "user_data/tradesv3.dryrun.sqlite" ]; then
    echo "3. Clearing dry-run database..."
    mv user_data/tradesv3.dryrun.sqlite user_data/tradesv3.dryrun.sqlite.backup.$(date +%Y%m%d_%H%M%S)
    echo "   ✅ Dry-run database backed up and cleared"
else
    echo "3. No dry-run database found (OK)"
fi

# Clear Python cache
echo "4. Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "   ✅ Python cache cleared"

# Clear any cached OHLCV data
if [ -d "user_data/data" ]; then
    echo "5. Found cached OHLCV data directory..."
    echo "   (Keeping raw_data, but you can delete user_data/data if needed)"
else
    echo "5. No cached OHLCV data directory found"
fi

echo ""
echo "✅ All caches cleared!"
echo ""
echo "📊 Now testing OHLCV data consistency..."
echo ""

# Run the test
python test_paperbroker_ohlcv.py

echo ""
echo "🎯 Next steps:"
echo "   1. Review the test output above"
echo "   2. If data still doesn't match, check your CSV files in user_data/raw_data/"
echo "   3. Restart Freqtrade: freqtrade trade --config config.json"
