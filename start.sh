#!/usr/bin/env bash
# Freqtrade Start Script for Indian Brokers

set -e

# Source virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Parse arguments
MODE="trade"
CONFIG="config.json"

while [[ $# -gt 0 ]]; do
    case $1 in
        --webui|--ui)
            MODE="webserver"
            shift
            ;;
        --config)
            CONFIG="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --webui, --ui    Start in WebUI mode (for backtesting/analysis)"
            echo "  --config FILE    Use specific config file (default: config.json)"
            echo "  --help, -h       Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                          # Start trading bot"
            echo "  $0 --webui                  # Start WebUI for backtesting"
            echo "  $0 --config my_config.json  # Use custom config"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if config exists
if [ ! -f "$CONFIG" ]; then
    echo "ERROR: $CONFIG not found"
    echo "Please run ./install.sh first or copy a config from config_examples/"
    echo ""
    echo "Available example configs:"
    ls config_examples/*.json 2>/dev/null || echo "  None found"
    exit 1
fi

# Check if strategy is configured (only for trade mode)
if [ "$MODE" = "trade" ]; then
    STRATEGY=$(python3 -c "import json; print(json.load(open('$CONFIG')).get('strategy', ''))" 2>/dev/null || echo "")
    if [ -z "$STRATEGY" ]; then
        echo "WARNING: No strategy configured in $CONFIG"
        echo "Using default strategy: SampleStrategy"
        STRATEGY="SampleStrategy"
    fi
fi

# Display startup info
echo "========================================="
echo "Freqtrade NSE Trading System"
echo "========================================="
echo "Mode: $MODE"
echo "Config: $CONFIG"
if [ "$MODE" = "trade" ]; then
    echo "Strategy: $STRATEGY"
fi
echo ""

# Start based on mode
if [ "$MODE" = "webserver" ]; then
    echo "Starting Freqtrade WebUI..."
    echo "Access at: http://localhost:8080"
    echo "API docs: http://localhost:8080/docs"
    echo ""
    echo "Press Ctrl+C to stop"
    echo ""

    freqtrade webserver --config "$CONFIG"
else
    echo "Starting Freqtrade Trading Bot..."
    echo ""

    # Check if WebUI is enabled in config
    HAS_API=$(python3 -c "import json; config=json.load(open('$CONFIG')); print('yes' if config.get('api_server', {}).get('enabled', False) else 'no')" 2>/dev/null || echo "no")

    if [ "$HAS_API" = "yes" ]; then
        echo "WebUI enabled - Access at: http://localhost:8080"
        echo "API docs: http://localhost:8080/docs"
        echo ""
    fi

    echo "Press Ctrl+C to stop"
    echo ""

    freqtrade trade --config "$CONFIG" --strategy "$STRATEGY"
fi
