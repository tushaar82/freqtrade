#!/bin/bash
# Quick Start Backtesting UI
# Opens Freqtrade with Web UI for easy backtesting

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
CONFIG_FILE="${1:-config.json}"
UI_PORT="${2:-8080}"
UI_HOST="${3:-127.0.0.1}"

# Banner
show_banner() {
    clear
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════╗"
    echo "║                                               ║"
    echo "║      Freqtrade Backtesting UI                ║"
    echo "║      Test Strategies with Web Interface      ║"
    echo "║                                               ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check if config exists
check_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo -e "${RED}✗ Configuration file not found: $CONFIG_FILE${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Config file found: $CONFIG_FILE${NC}"
}

# Check if UI is installed
check_ui() {
    if [ ! -d "freqtrade/rpc/api_server/ui/installed" ]; then
        echo -e "${YELLOW}⚠ FreqUI not installed${NC}"
        echo ""
        read -p "Install FreqUI now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Downloading FreqUI..."
            python3 -m freqtrade install-ui
            echo -e "${GREEN}✓ FreqUI installed${NC}"
        else
            echo -e "${YELLOW}⚠ Running without UI (API only)${NC}"
        fi
    else
        echo -e "${GREEN}✓ FreqUI is installed${NC}"
    fi
}

# Update config for UI
update_config_for_ui() {
    echo ""
    echo "Ensuring UI is enabled in config..."
    
    python3 << EOF
import json
import sys

try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    
    # Enable API server
    if 'api_server' not in config:
        config['api_server'] = {}
    
    config['api_server']['enabled'] = True
    config['api_server']['listen_ip_address'] = '$UI_HOST'
    config['api_server']['listen_port'] = $UI_PORT
    config['api_server']['verbosity'] = 'info'
    
    # Set CORS for UI
    if 'CORS_origins' not in config['api_server']:
        config['api_server']['CORS_origins'] = []
    
    with open('$CONFIG_FILE', 'w') as f:
        json.dump(config, f, indent=4)
    
    print("✓ Config updated for UI")
except Exception as e:
    print(f"Error updating config: {e}", file=sys.stderr)
    sys.exit(1)
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ UI configuration updated${NC}"
    else
        echo -e "${RED}✗ Failed to update config${NC}"
        exit 1
    fi
}

# Show configuration summary
show_config() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}Configuration Summary${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "Config File:    ${GREEN}$CONFIG_FILE${NC}"
    echo -e "UI Address:     ${GREEN}http://$UI_HOST:$UI_PORT${NC}"
    echo -e "Mode:           ${GREEN}Backtesting UI${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo ""
}

# Start Freqtrade in webserver mode
start_freqtrade() {
    echo -e "${GREEN}Starting Freqtrade Backtesting UI...${NC}"
    echo ""
    echo "Press Ctrl+C to stop"
    echo ""
    
    # Start Freqtrade in webserver mode (for backtesting)
    python3 -m freqtrade webserver \
        --config "$CONFIG_FILE"
}

# Open browser (optional)
open_browser() {
    sleep 3  # Wait for server to start
    
    URL="http://$UI_HOST:$UI_PORT"
    
    if command -v xdg-open &> /dev/null; then
        xdg-open "$URL" 2>/dev/null &
    elif command -v open &> /dev/null; then
        open "$URL" 2>/dev/null &
    else
        echo -e "${YELLOW}Please open your browser and navigate to: $URL${NC}"
    fi
}

# Show help
show_help() {
    echo "Usage: $0 [CONFIG_FILE] [UI_PORT] [UI_HOST]"
    echo ""
    echo "Start Freqtrade Backtesting UI for testing strategies"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Use defaults"
    echo "  $0 config.json                        # Specify config"
    echo "  $0 config.json 8081                   # Custom port"
    echo "  $0 config.json 8081 0.0.0.0          # Listen on all interfaces"
    echo ""
    echo "Default values:"
    echo "  Config:   config.json"
    echo "  UI Port:  8080"
    echo "  UI Host:  127.0.0.1"
    echo ""
    echo "After starting:"
    echo "  1. Open http://127.0.0.1:8080 in your browser"
    echo "  2. Login with credentials from config.json"
    echo "  3. Click 'Backtest' tab"
    echo "  4. Configure and run backtests"
    echo ""
    echo "Features:"
    echo "  ✓ Web-based backtesting interface"
    echo "  ✓ Real-time progress monitoring"
    echo "  ✓ Performance metrics and charts"
    echo "  ✓ Backtest history management"
    echo "  ✓ Strategy comparison"
    echo ""
    exit 0
}

# Trap Ctrl+C
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping Freqtrade...${NC}"
    echo -e "${GREEN}Goodbye! 👋${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Main
main() {
    # Check for help
    if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
        show_help
    fi
    
    show_banner
    
    echo "Performing pre-flight checks..."
    echo ""
    
    check_config
    check_ui
    update_config_for_ui
    show_config
    
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo ""
    
    # Ask to open browser
    read -p "Open web UI in browser? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open_browser &
    fi
    
    echo ""
    echo -e "${GREEN}🚀 Starting Backtesting UI...${NC}"
    echo ""
    echo -e "${BLUE}Access the UI at: http://$UI_HOST:$UI_PORT${NC}"
    echo ""
    echo -e "${YELLOW}How to use:${NC}"
    echo "  1. Navigate to the 'Backtest' tab"
    echo "  2. Select your strategy"
    echo "  3. Configure timeframe and timerange"
    echo "  4. Click 'Start Backtest'"
    echo "  5. View results and metrics"
    echo ""
    echo "═══════════════════════════════════════"
    echo ""
    
    # Start Freqtrade
    start_freqtrade
}

# Run
main "$@"
