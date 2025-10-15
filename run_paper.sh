#!/bin/bash
# Start Freqtrade Paper Broker with Web UI
# Perfect for risk-free strategy testing and learning

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
CONFIG_FILE="${1:-config.json}"
STRATEGY="${2:-NSESampleStrategy}"
UI_PORT="${3:-8080}"
UI_HOST="${4:-127.0.0.1}"

# Banner
show_banner() {
    clear
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════╗"
    echo "║                                               ║"
    echo "║      Freqtrade Paper Broker with UI          ║"
    echo "║      Risk-Free NSE Trading Simulator         ║"
    echo "║                                               ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check if config exists
check_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo -e "${RED}✗ Configuration file not found: $CONFIG_FILE${NC}"
        echo ""
        echo "Creating Paper Broker configuration..."
        
        if [ -f "config_examples/config_paperbroker.example.json" ]; then
            cp config_examples/config_paperbroker.example.json "$CONFIG_FILE"
            echo -e "${GREEN}✓ Created $CONFIG_FILE${NC}"
        else
            echo -e "${RED}✗ Example config not found. Please run install.sh first${NC}"
            exit 1
        fi
    fi
    
    # Check if it's using paperbroker
    if grep -q '"name": "paperbroker"' "$CONFIG_FILE"; then
        echo -e "${GREEN}✓ Using Paper Broker (Virtual Trading)${NC}"
    else
        echo -e "${YELLOW}⚠ Warning: Config may not be using Paper Broker${NC}"
        echo "   Make sure 'exchange.name' is set to 'paperbroker' for virtual trading"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check if strategy exists
check_strategy() {
    if [ ! -f "user_data/strategies/${STRATEGY}.py" ]; then
        echo -e "${YELLOW}⚠ Strategy not found: $STRATEGY${NC}"
        echo ""
        echo "Available strategies:"
        ls -1 user_data/strategies/*.py 2>/dev/null | xargs -n 1 basename | sed 's/.py$//' || echo "  None found"
        echo ""
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}✓ Strategy found: $STRATEGY${NC}"
    fi
}

# Update config for UI
update_config_for_ui() {
    echo ""
    echo "Ensuring UI is enabled in config..."
    
    # Create a temporary Python script to update config
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
    
    # Ensure dry_run is false for paper broker to work
    config['dry_run'] = False
    
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

# Check if UI is installed
check_ui() {
    if [ ! -d "freqtrade/rpc/api_server/ui" ] || [ -z "$(ls -A freqtrade/rpc/api_server/ui 2>/dev/null)" ]; then
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

# Show configuration summary
show_config() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}Configuration Summary${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "Config File:    ${GREEN}$CONFIG_FILE${NC}"
    echo -e "Strategy:       ${GREEN}$STRATEGY${NC}"
    echo -e "UI Address:     ${GREEN}http://$UI_HOST:$UI_PORT${NC}"
    echo -e "Trading Mode:   ${GREEN}Paper Trading (Virtual)${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo ""
}

# Start Freqtrade
start_freqtrade() {
    echo -e "${GREEN}Starting Freqtrade Paper Broker...${NC}"
    echo ""
    echo "Press Ctrl+C to stop"
    echo ""
    
    # Start Freqtrade using Python module
    python3 -m freqtrade trade \
        --config "$CONFIG_FILE" \
        --strategy "$STRATEGY" \
        --db-url "sqlite:///user_data/tradesv3_paper.sqlite" \
        --logfile user_data/logs/freqtrade_paper.log
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
    echo "Usage: $0 [CONFIG_FILE] [STRATEGY] [UI_PORT] [UI_HOST]"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Use defaults"
    echo "  $0 config.json                        # Specify config"
    echo "  $0 config.json MyStrategy             # Specify config and strategy"
    echo "  $0 config.json MyStrategy 8081        # Custom port"
    echo "  $0 config.json MyStrategy 8081 0.0.0.0  # Listen on all interfaces"
    echo ""
    echo "Default values:"
    echo "  Config:   config.json"
    echo "  Strategy: NSESampleStrategy"
    echo "  UI Port:  8080"
    echo "  UI Host:  127.0.0.1"
    echo ""
    echo "After starting, access the UI at: http://127.0.0.1:8080"
    echo ""
    echo "Quick start with different exchanges:"
    echo "  Paper Broker:  $0 config.json"
    echo "  OpenAlgo:      $0 config_openalgo.json"
    echo "  Smart API:     $0 config_smartapi.json"
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
    check_strategy
    update_config_for_ui
    check_ui
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
    echo -e "${GREEN}🚀 Starting Paper Trading...${NC}"
    echo ""
    echo -e "${BLUE}Access the UI at: http://$UI_HOST:$UI_PORT${NC}"
    echo ""
    echo "═══════════════════════════════════════"
    echo ""
    
    # Start Freqtrade
    start_freqtrade
}

# Run
main "$@"
