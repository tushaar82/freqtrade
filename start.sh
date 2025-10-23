#!/usr/bin/env bash
# Freqtrade Start Script for Indian Brokers

set -e

# Source virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Check if config exists
if [ ! -f "config.json" ]; then
    echo "ERROR: config.json not found"
    echo "Please run ./install.sh first or copy a config from config_examples/"
    exit 1
fi

# Check if strategy is configured
STRATEGY=$(python3 -c "import json; print(json.load(open('config.json')).get('strategy', ''))" 2>/dev/null || echo "")
if [ -z "$STRATEGY" ]; then
    echo "WARNING: No strategy configured in config.json"
fi

# Start Freqtrade
echo "Starting Freqtrade..."
echo "Press Ctrl+C to stop"
echo ""

# Start with UI if api_server is configured
freqtrade trade --config config.json --strategy ${STRATEGY:-SampleStrategy}
