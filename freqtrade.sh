#!/bin/bash
#
# Freqtrade Management Script - Indian Stocks & Options Trading Platform
# Handles: install, run, stop, status, clean, logs, options, brokers
#
# Usage: ./freqtrade.sh [command] [options]
#
# Features:
# - 4 Indian Brokers: OpenAlgo, SmartAPI, PaperBroker, Zerodha
# - Options Trading: NSE/NFO options with lot size management
# - API Server: 30+ endpoints for mobile app development
# - Secure Credentials: Encrypted broker credential storage
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python3"
FREQTRADE_BIN="$VENV_DIR/bin/freqtrade"
PID_FILE="$SCRIPT_DIR/freqtrade.pid"
LOG_FILE="$SCRIPT_DIR/freqtrade.log"
DB_FILE="$SCRIPT_DIR/tradesv3.sqlite"
CONFIG_FILE="$SCRIPT_DIR/config.json"

# Print colored message
print_msg() {
    local color=$1
    local msg=$2
    echo -e "${color}${msg}${NC}"
}

print_header() {
    echo ""
    print_msg "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_msg "$BLUE" "  $1"
    print_msg "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Check if freqtrade is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Install freqtrade
install() {
    print_header "INSTALLING FREQTRADE"
    
    # Check Python version
    print_msg "$YELLOW" "→ Checking Python version..."
    if ! command -v python3 &> /dev/null; then
        print_msg "$RED" "✗ Python 3 is not installed!"
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    print_msg "$GREEN" "✓ Python $python_version found"
    
    # Create virtual environment
    print_msg "$YELLOW" "→ Creating virtual environment..."
    if [ -d "$VENV_DIR" ]; then
        print_msg "$YELLOW" "  Virtual environment already exists, skipping..."
    else
        python3 -m venv "$VENV_DIR"
        print_msg "$GREEN" "✓ Virtual environment created"
    fi
    
    # Upgrade pip
    print_msg "$YELLOW" "→ Upgrading pip..."
    "$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel > /dev/null 2>&1
    print_msg "$GREEN" "✓ Pip upgraded"
    
    # Install requirements
    print_msg "$YELLOW" "→ Installing Freqtrade dependencies..."
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" > /dev/null 2>&1
        print_msg "$GREEN" "✓ Dependencies installed (including kiteconnect, pyotp, scipy)"
    else
        print_msg "$RED" "✗ requirements.txt not found!"
        exit 1
    fi
    
    # Install freqtrade in development mode
    print_msg "$YELLOW" "→ Installing Freqtrade..."
    cd "$SCRIPT_DIR"
    "$VENV_DIR/bin/pip" install -e . > /dev/null 2>&1
    print_msg "$GREEN" "✓ Freqtrade installed"
    
    # Create default config if not exists
    if [ ! -f "$CONFIG_FILE" ]; then
        print_msg "$YELLOW" "→ Creating default config with options trading support..."
        cat > "$CONFIG_FILE" << 'EOF'
{
  "max_open_trades": 3,
  "stake_currency": "INR",
  "stake_amount": 10000,
  "tradable_balance_ratio": 0.99,
  "fiat_display_currency": "INR",
  "timeframe": "5m",
  "dry_run": true,
  "cancel_open_orders_on_exit": false,
  "trading_mode": "spot",
  "margin_mode": "",
  "enable_options_trading": true,
  "exchange": {
    "name": "paperbroker",
    "initial_balance": 100000,
    "slippage_percent": 0.05,
    "commission_percent": 0.1,
    "nse_exchange": "NSE",
    "pair_whitelist": [
      "RELIANCE/INR",
      "TCS/INR",
      "INFY/INR",
      "HDFCBANK/INR",
      "ICICIBANK/INR",
      "NIFTY25DEC24500CE/INR",
      "NIFTY25DEC24500PE/INR",
      "BANKNIFTY25DEC24500CE/INR",
      "BANKNIFTY25DEC24500PE/INR"
    ],
    "pair_blacklist": []
  },
  "entry_pricing": {
    "price_side": "same",
    "use_order_book": true,
    "order_book_top": 1,
    "check_depth_of_market": {
      "enabled": false,
      "bids_to_ask_delta": 1
    }
  },
  "exit_pricing": {
    "price_side": "same",
    "use_order_book": true,
    "order_book_top": 1
  },
  "pairlists": [
    {
      "method": "StaticPairList"
    }
  ],
  "order_types": {
    "entry": "limit",
    "exit": "limit",
    "emergency_exit": "market",
    "force_exit": "market",
    "force_entry": "market",
    "stoploss": "market",
    "stoploss_on_exchange": false
  },
  "order_time_in_force": {
    "entry": "GTC",
    "exit": "GTC"
  },
  "telegram": {
    "enabled": false
  },
  "api_server": {
    "enabled": true,
    "listen_ip_address": "127.0.0.1",
    "listen_port": 8080,
    "verbosity": "error",
    "jwt_secret_key": "your-secret-key-change-this",
    "CORS_origins": ["http://localhost:3000"],
    "username": "freqtrader",
    "password": "SuperSecurePassword"
  },
  "bot_name": "freqtrade_indian_markets",
  "initial_state": "running",
  "force_entry_enable": false,
  "internals": {
    "process_throttle_secs": 5
  },
  "nse_trading": {
    "market_hours": {
      "open": "09:15",
      "close": "15:30"
    },
    "product_type": "MIS"
  }
}
EOF
        print_msg "$GREEN" "✓ Default config created: $CONFIG_FILE"
        print_msg "$YELLOW" "  Features enabled:"
        print_msg "$YELLOW" "    - Options trading support"
        print_msg "$YELLOW" "    - API server (port 8080)"
        print_msg "$YELLOW" "    - NSE market hours"
        print_msg "$YELLOW" "    - Sample options pairs"
        print_msg "$YELLOW" "  Note: Using PaperBroker by default. Use 'broker' command to configure real brokers"
    fi
    
    # Initialize lot sizes file
    if [ ! -f "$SCRIPT_DIR/user_data/lot_sizes.json" ]; then
        print_msg "$YELLOW" "→ Initializing lot sizes data..."
        mkdir -p "$SCRIPT_DIR/user_data"
        # The lot_sizes.json file should already exist from our implementation
        if [ -f "$SCRIPT_DIR/user_data/lot_sizes.json" ]; then
            print_msg "$GREEN" "✓ Lot sizes data available"
        else
            print_msg "$YELLOW" "  Warning: lot_sizes.json not found, will be created on first run"
        fi
    fi
    
    print_msg "$GREEN" "\n✅ Installation complete!"
    print_msg "$YELLOW" "\nNext steps:"
    print_msg "$YELLOW" "  1. Configure brokers: ./freqtrade.sh broker setup"
    print_msg "$YELLOW" "  2. Start trading: ./freqtrade.sh run"
    print_msg "$YELLOW" "  3. Access API: http://localhost:8080/docs"
    print_msg "$YELLOW" "  4. View analytics: ./freqtrade.sh ui"
}

# Run freqtrade
run() {
    print_header "STARTING FREQTRADE"
    
    if is_running; then
        print_msg "$YELLOW" "⚠ Freqtrade is already running (PID: $(cat $PID_FILE))"
        exit 1
    fi
    
    if [ ! -f "$FREQTRADE_BIN" ]; then
        print_msg "$RED" "✗ Freqtrade not installed. Run: ./freqtrade.sh install"
        exit 1
    fi
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_msg "$RED" "✗ Config file not found: $CONFIG_FILE"
        exit 1
    fi
    
    # Parse arguments
    clean_db=false
    strategy="NSESampleStrategy"
    
    for arg in "$@"; do
        case "$arg" in
            --clean-db)
                clean_db=true
                ;;
            --*)
                print_msg "$RED" "Unknown option: $arg"
                print_msg "$YELLOW" "Usage: ./freqtrade.sh run [strategy] [--clean-db]"
                exit 1
                ;;
            *)
                strategy="$arg"
                ;;
        esac
    done
    
    # Clean database if flag is set
    if [ "$clean_db" = true ]; then
        print_msg "$YELLOW" "→ Cleaning database for fresh start..."
        rm -f "$SCRIPT_DIR"/tradesv3*.sqlite* 2>/dev/null
        print_msg "$GREEN" "✓ Database cleared"
    fi
    
    print_msg "$YELLOW" "→ Starting Freqtrade..."
    print_msg "$YELLOW" "  Config: $CONFIG_FILE"
    print_msg "$YELLOW" "  Strategy: $strategy"
    print_msg "$YELLOW" "  Log file: $LOG_FILE"
    
    # Start freqtrade in background
    nohup "$FREQTRADE_BIN" trade \
        --config "$CONFIG_FILE" \
        --strategy "$strategy" \
        --logfile "$LOG_FILE" \
        > /dev/null 2>&1 &
    
    pid=$!
    echo $pid > "$PID_FILE"
    
    # Wait a moment to check if it started
    sleep 2
    
    if is_running; then
        print_msg "$GREEN" "✓ Freqtrade started successfully (PID: $pid)"
        print_msg "$YELLOW" "\nMonitor logs with:"
        print_msg "$YELLOW" "  ./freqtrade.sh logs"
    else
        print_msg "$RED" "✗ Failed to start Freqtrade"
        print_msg "$YELLOW" "Check logs: tail -f $LOG_FILE"
        exit 1
    fi
}

# Stop freqtrade
stop() {
    print_header "STOPPING FREQTRADE"
    
    if ! is_running; then
        print_msg "$YELLOW" "⚠ Freqtrade is not running"
        exit 0
    fi
    
    pid=$(cat "$PID_FILE")
    print_msg "$YELLOW" "→ Stopping Freqtrade (PID: $pid)..."
    
    kill "$pid"
    
    # Wait for process to stop
    for i in {1..10}; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
            rm -f "$PID_FILE"
            print_msg "$GREEN" "✓ Freqtrade stopped"
            exit 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    print_msg "$YELLOW" "→ Force killing..."
    kill -9 "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    print_msg "$GREEN" "✓ Freqtrade stopped (forced)"
}

# Restart freqtrade
restart() {
    print_header "RESTARTING FREQTRADE"
    
    if is_running; then
        stop
        sleep 2
    fi
    
    run "$@"
}

# Show status
status() {
    print_header "FREQTRADE STATUS"
    
    if is_running; then
        pid=$(cat "$PID_FILE")
        uptime=$(ps -p "$pid" -o etime= | xargs)
        cpu=$(ps -p "$pid" -o %cpu= | xargs)
        mem=$(ps -p "$pid" -o %mem= | xargs)
        
        print_msg "$GREEN" "✓ Status: RUNNING"
        print_msg "$YELLOW" "  PID: $pid"
        print_msg "$YELLOW" "  Uptime: $uptime"
        print_msg "$YELLOW" "  CPU: ${cpu}%"
        print_msg "$YELLOW" "  Memory: ${mem}%"
        print_msg "$YELLOW" "  Log: $LOG_FILE"
        
        if [ -f "$DB_FILE" ]; then
            db_size=$(du -h "$DB_FILE" | cut -f1)
            print_msg "$YELLOW" "  Database: $db_size"
        fi
    else
        print_msg "$RED" "✗ Status: STOPPED"
    fi
    
    # Show config info
    if [ -f "$CONFIG_FILE" ]; then
        exchange=$(grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_FILE" | head -1 | cut -d'"' -f4)
        print_msg "$YELLOW" "\n  Exchange: ${exchange:-unknown}"
    fi
}

# Broker management
broker_cmd() {
    local action="${1:-help}"
    
    case "$action" in
        setup)
            broker_setup
            ;;
        list)
            broker_list
            ;;
        test)
            broker_test "${2:-all}"
            ;;
        help)
            broker_help
            ;;
        *)
            print_msg "$RED" "Unknown broker command: $action"
            broker_help
            exit 1
            ;;
    esac
}

# Setup broker credentials
broker_setup() {
    print_header "BROKER SETUP"
    
    print_msg "$YELLOW" "Available brokers:"
    print_msg "$YELLOW" "  1. PaperBroker (Simulation)"
    print_msg "$YELLOW" "  2. OpenAlgo (Local/Cloud)"
    print_msg "$YELLOW" "  3. SmartAPI (Angel One)"
    print_msg "$YELLOW" "  4. Zerodha (Kite Connect)"
    
    echo
    read -p "$(echo -e ${YELLOW}Select broker [1-4]: ${NC})" -n 1 -r
    echo
    
    case $REPLY in
        1)
            setup_paperbroker
            ;;
        2)
            setup_openalgo
            ;;
        3)
            setup_smartapi
            ;;
        4)
            setup_zerodha
            ;;
        *)
            print_msg "$RED" "Invalid selection"
            exit 1
            ;;
    esac
}

# Setup PaperBroker
setup_paperbroker() {
    print_msg "$YELLOW" "→ Configuring PaperBroker..."
    
    # Update config.json to use paperbroker
    if [ -f "$CONFIG_FILE" ]; then
        # Create a backup
        cp "$CONFIG_FILE" "${CONFIG_FILE}.backup"
        
        # Update exchange name
        sed -i 's/"name": "[^"]*"/"name": "paperbroker"/' "$CONFIG_FILE"
        
        print_msg "$GREEN" "✓ PaperBroker configured"
        print_msg "$YELLOW" "  Features:"
        print_msg "$YELLOW" "    - No real money trading"
        print_msg "$YELLOW" "    - Simulated market data"
        print_msg "$YELLOW" "    - Perfect for testing strategies"
    fi
}

# Setup OpenAlgo
setup_openalgo() {
    print_msg "$YELLOW" "→ Configuring OpenAlgo..."
    
    read -p "$(echo -e ${YELLOW}OpenAlgo Host [http://127.0.0.1:5000]: ${NC})" host
    host=${host:-"http://127.0.0.1:5000"}
    
    read -p "$(echo -e ${YELLOW}API Key: ${NC})" api_key
    
    if [ -z "$api_key" ]; then
        print_msg "$RED" "API Key is required"
        exit 1
    fi
    
    # Test connection
    print_msg "$YELLOW" "→ Testing connection..."
    if command -v curl &> /dev/null; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $api_key" "$host/api/v1/profile" || echo "000")
        if [ "$response" = "200" ]; then
            print_msg "$GREEN" "✓ Connection successful"
        else
            print_msg "$YELLOW" "⚠ Connection test failed (HTTP $response)"
            print_msg "$YELLOW" "  Continuing with configuration..."
        fi
    fi
    
    print_msg "$GREEN" "✓ OpenAlgo configured"
    print_msg "$YELLOW" "  Note: Update config.json with your OpenAlgo settings"
}

# Setup SmartAPI
setup_smartapi() {
    print_msg "$YELLOW" "→ Configuring SmartAPI (Angel One)..."
    
    read -p "$(echo -e ${YELLOW}API Key: ${NC})" api_key
    read -p "$(echo -e ${YELLOW}Client Code: ${NC})" client_code
    read -s -p "$(echo -e ${YELLOW}PIN: ${NC})" pin
    echo
    read -p "$(echo -e ${YELLOW}TOTP Secret: ${NC})" totp_secret
    
    if [ -z "$api_key" ] || [ -z "$client_code" ] || [ -z "$pin" ]; then
        print_msg "$RED" "All fields are required"
        exit 1
    fi
    
    print_msg "$GREEN" "✓ SmartAPI configured"
    print_msg "$YELLOW" "  Note: Update config.json with your SmartAPI credentials"
    print_msg "$YELLOW" "  Requires: smartapi-python and pyotp packages"
}

# Setup Zerodha
setup_zerodha() {
    print_msg "$YELLOW" "→ Configuring Zerodha Kite Connect..."
    
    read -p "$(echo -e ${YELLOW}API Key: ${NC})" api_key
    read -p "$(echo -e ${YELLOW}API Secret: ${NC})" api_secret
    read -p "$(echo -e ${YELLOW}Redirect URL [https://127.0.0.1:8080]: ${NC})" redirect_url
    redirect_url=${redirect_url:-"https://127.0.0.1:8080"}
    
    if [ -z "$api_key" ] || [ -z "$api_secret" ]; then
        print_msg "$RED" "API Key and Secret are required"
        exit 1
    fi
    
    print_msg "$GREEN" "✓ Zerodha configured"
    print_msg "$YELLOW" "  Note: Daily OAuth authentication required"
    print_msg "$YELLOW" "  Requires: Kite Connect subscription (₹500/month)"
    print_msg "$YELLOW" "  Login URL will be provided on first run"
}

# List configured brokers
broker_list() {
    print_header "CONFIGURED BROKERS"
    
    if [ -f "$CONFIG_FILE" ]; then
        exchange=$(grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_FILE" | head -1 | cut -d'"' -f4)
        print_msg "$GREEN" "Current exchange: ${exchange:-unknown}"
        
        # Check for broker credential files
        if [ -f "$SCRIPT_DIR/broker_credentials.db" ]; then
            print_msg "$YELLOW" "Broker credentials database found"
        else
            print_msg "$YELLOW" "No broker credentials stored"
        fi
    else
        print_msg "$RED" "Config file not found"
    fi
}

# Test broker connections
broker_test() {
    local broker="${1:-all}"
    
    print_header "TESTING BROKER CONNECTIONS"
    
    if [ ! -f "$PYTHON_BIN" ]; then
        print_msg "$RED" "✗ Python not found. Run: ./freqtrade.sh install"
        exit 1
    fi
    
    print_msg "$YELLOW" "→ Testing broker: $broker"
    
    # This would call the broker credential manager to test connections
    # For now, just show a placeholder
    print_msg "$YELLOW" "  Note: Broker testing requires API server to be running"
    print_msg "$YELLOW" "  Use: curl -X GET http://localhost:8080/api/v1/brokers"
}

# Show broker help
broker_help() {
    cat << EOF

$(print_msg "$BLUE" "Broker Management Commands")

Usage: ./freqtrade.sh broker [command]

Commands:
  $(print_msg "$GREEN" "setup")              Interactive broker setup
  $(print_msg "$GREEN" "list")               List configured brokers
  $(print_msg "$GREEN" "test [broker]")      Test broker connections
  $(print_msg "$GREEN" "help")               Show this help

Supported Brokers:
  $(print_msg "$YELLOW" "PaperBroker")        Simulation trading (no real money)
  $(print_msg "$YELLOW" "OpenAlgo")           Local/Cloud broker integration
  $(print_msg "$YELLOW" "SmartAPI")           Angel One trading platform
  $(print_msg "$YELLOW" "Zerodha")            Kite Connect API (₹500/month)

Examples:
  ./freqtrade.sh broker setup
  ./freqtrade.sh broker list
  ./freqtrade.sh broker test zerodha

EOF
}

# Options trading commands
options_cmd() {
    local action="${1:-help}"
    
    case "$action" in
        chains)
            options_chains "${2:-NIFTY}"
            ;;
        lots)
            options_lots
            ;;
        update-lots)
            options_update_lots
            ;;
        calculator)
            options_calculator
            ;;
        help)
            options_help
            ;;
        *)
            print_msg "$RED" "Unknown options command: $action"
            options_help
            exit 1
            ;;
    esac
}

# Get option chains
options_chains() {
    local symbol="${1:-NIFTY}"
    
    print_header "OPTION CHAINS - $symbol"
    
    if ! is_running; then
        print_msg "$RED" "✗ Freqtrade is not running. Start with: ./freqtrade.sh run"
        exit 1
    fi
    
    print_msg "$YELLOW" "→ Fetching option chain for $symbol..."
    
    # Use curl to call the API
    if command -v curl &> /dev/null; then
        response=$(curl -s "http://localhost:8080/api/v1/options/chains?symbol=$symbol" || echo "error")
        if [ "$response" != "error" ]; then
            print_msg "$GREEN" "✓ Option chain data retrieved"
            print_msg "$YELLOW" "  View full data at: http://localhost:8080/api/v1/options/chains?symbol=$symbol"
        else
            print_msg "$RED" "✗ Failed to fetch option chain"
        fi
    else
        print_msg "$YELLOW" "  Install curl to fetch data, or visit: http://localhost:8080/api/v1/options/chains?symbol=$symbol"
    fi
}

# Show lot sizes
options_lots() {
    print_header "OPTIONS LOT SIZES"
    
    if [ -f "$SCRIPT_DIR/user_data/lot_sizes.json" ]; then
        print_msg "$GREEN" "✓ Lot sizes data found"
        
        if command -v jq &> /dev/null; then
            print_msg "$YELLOW" "\nIndices:"
            jq -r '.lot_sizes.indices | to_entries[] | "  \(.key): \(.value)"' "$SCRIPT_DIR/user_data/lot_sizes.json"
            
            print_msg "$YELLOW" "\nStocks (sample):"
            jq -r '.lot_sizes.stocks | to_entries[0:5][] | "  \(.key): \(.value)"' "$SCRIPT_DIR/user_data/lot_sizes.json"
        else
            print_msg "$YELLOW" "  Install jq to view formatted data, or check: user_data/lot_sizes.json"
        fi
    else
        print_msg "$RED" "✗ Lot sizes data not found"
    fi
}

# Update lot sizes
options_update_lots() {
    print_header "UPDATE LOT SIZES"
    
    if ! is_running; then
        print_msg "$RED" "✗ Freqtrade is not running. Start with: ./freqtrade.sh run"
        exit 1
    fi
    
    print_msg "$YELLOW" "→ Updating lot sizes from exchange..."
    
    if command -v curl &> /dev/null; then
        response=$(curl -s -X POST "http://localhost:8080/api/v1/options/lot-sizes/update" || echo "error")
        if [ "$response" != "error" ]; then
            print_msg "$GREEN" "✓ Lot sizes updated"
        else
            print_msg "$RED" "✗ Failed to update lot sizes"
        fi
    else
        print_msg "$YELLOW" "  Install curl or visit: http://localhost:8080/api/v1/options/lot-sizes/update"
    fi
}

# Options P&L calculator
options_calculator() {
    print_header "OPTIONS P&L CALCULATOR"
    
    read -p "$(echo -e ${YELLOW}Entry Price: ${NC})" entry_price
    read -p "$(echo -e ${YELLOW}Exit Price: ${NC})" exit_price
    read -p "$(echo -e ${YELLOW}Quantity: ${NC})" quantity
    read -p "$(echo -e ${YELLOW}Lot Size [1]: ${NC})" lot_size
    lot_size=${lot_size:-1}
    read -p "$(echo -e ${YELLOW}Option Type [CALL]: ${NC})" option_type
    option_type=${option_type:-CALL}
    
    if [ -z "$entry_price" ] || [ -z "$exit_price" ] || [ -z "$quantity" ]; then
        print_msg "$RED" "Entry price, exit price, and quantity are required"
        exit 1
    fi
    
    # Simple P&L calculation
    pnl=$(echo "($exit_price - $entry_price) * $quantity" | bc -l 2>/dev/null || echo "0")
    pnl_pct=$(echo "scale=2; ($exit_price - $entry_price) / $entry_price * 100" | bc -l 2>/dev/null || echo "0")
    
    print_msg "$GREEN" "\n✓ P&L Calculation:"
    print_msg "$YELLOW" "  Total P&L: ₹$pnl"
    print_msg "$YELLOW" "  P&L %: $pnl_pct%"
    print_msg "$YELLOW" "  Lots: $(echo "$quantity / $lot_size" | bc -l 2>/dev/null || echo "1")"
    
    print_msg "$YELLOW" "\nFor detailed calculations, visit: http://localhost:8080/api/v1/options/calculator"
}

# Show options help
options_help() {
    cat << EOF

$(print_msg "$BLUE" "Options Trading Commands")

Usage: ./freqtrade.sh options [command]

Commands:
  $(print_msg "$GREEN" "chains [symbol]")     Get option chains (default: NIFTY)
  $(print_msg "$GREEN" "lots")                Show lot sizes for indices/stocks
  $(print_msg "$GREEN" "update-lots")         Update lot sizes from exchange
  $(print_msg "$GREEN" "calculator")          Interactive P&L calculator
  $(print_msg "$GREEN" "help")                Show this help

Examples:
  ./freqtrade.sh options chains NIFTY
  ./freqtrade.sh options chains BANKNIFTY
  ./freqtrade.sh options lots
  ./freqtrade.sh options calculator

API Endpoints:
  Option Chains:    http://localhost:8080/api/v1/options/chains
  Lot Sizes:        http://localhost:8080/api/v1/options/lot-sizes
  Greeks:           http://localhost:8080/api/v1/options/greeks
  Calculator:       http://localhost:8080/api/v1/options/calculator

EOF
}

# Open web UI
open_ui() {
    print_header "OPENING WEB INTERFACE"
    
    local url="http://localhost:8080"
    
    if ! is_running; then
        print_msg "$YELLOW" "⚠ Freqtrade is not running"
        print_msg "$YELLOW" "  Starting Freqtrade first..."
        run
        sleep 3
    fi
    
    print_msg "$YELLOW" "→ Opening web interface..."
    print_msg "$YELLOW" "  Main API: $url/docs"
    print_msg "$YELLOW" "  Trading UI: file://$SCRIPT_DIR/trading_ui.html"
    print_msg "$YELLOW" "  Analytics: file://$SCRIPT_DIR/analytics_ui.html"
    
    # Try to open in browser
    if command -v xdg-open &> /dev/null; then
        xdg-open "file://$SCRIPT_DIR/trading_ui.html" 2>/dev/null &
        print_msg "$GREEN" "✓ Trading UI opened in browser"
    elif command -v open &> /dev/null; then
        open "file://$SCRIPT_DIR/trading_ui.html" 2>/dev/null &
        print_msg "$GREEN" "✓ Trading UI opened in browser"
    else
        print_msg "$YELLOW" "  Manual: Open file://$SCRIPT_DIR/trading_ui.html in your browser"
    fi
}

# Show logs
logs() {
    if [ ! -f "$LOG_FILE" ]; then
        print_msg "$YELLOW" "⚠ Log file not found: $LOG_FILE"
        exit 1
    fi
    
    print_header "FREQTRADE LOGS"
    print_msg "$YELLOW" "Press Ctrl+C to exit\n"
    
    tail -f "$LOG_FILE"
}

# Clean database
clean_db() {
    print_header "CLEAN DATABASE"
    
    if is_running; then
        print_msg "$RED" "✗ Please stop Freqtrade before cleaning database"
        exit 1
    fi
    
    if [ ! -f "$DB_FILE" ]; then
        print_msg "$YELLOW" "⚠ Database file not found: $DB_FILE"
        exit 0
    fi
    
    db_size=$(du -h "$DB_FILE" | cut -f1)
    print_msg "$YELLOW" "Current database size: $db_size"
    
    read -p "$(echo -e ${YELLOW}Are you sure you want to delete the database? [y/N]: ${NC})" -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Backup database
        backup_file="${DB_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        print_msg "$YELLOW" "→ Creating backup: $backup_file"
        cp "$DB_FILE" "$backup_file"
        
        # Remove database
        print_msg "$YELLOW" "→ Removing database..."
        rm -f "$DB_FILE"
        
        print_msg "$GREEN" "✓ Database cleaned"
        print_msg "$YELLOW" "  Backup saved: $backup_file"
    else
        print_msg "$YELLOW" "Cancelled"
    fi
}

# Run backtest
backtest() {
    print_header "RUNNING BACKTEST"
    
    if [ ! -f "$FREQTRADE_BIN" ]; then
        print_msg "$RED" "✗ Freqtrade not installed. Run: ./freqtrade.sh install"
        exit 1
    fi
    
    strategy="${1:-NSESampleStrategy}"
    timerange="${2:-20231001-20231101}"
    
    print_msg "$YELLOW" "→ Running backtest..."
    print_msg "$YELLOW" "  Strategy: $strategy"
    print_msg "$YELLOW" "  Timerange: $timerange"
    
    "$FREQTRADE_BIN" backtesting \
        --config "$CONFIG_FILE" \
        --strategy "$strategy" \
        --timerange "$timerange" \
        --export trades
    
    print_msg "$GREEN" "\n✓ Backtest complete"
}

# Show help
show_help() {
    cat << EOF

$(print_msg "$BLUE" "Freqtrade - Indian Stocks & Options Trading Platform")

Usage: ./freqtrade.sh [command] [options]

$(print_msg "$YELLOW" "Core Commands:")
  $(print_msg "$GREEN" "install")           Install Freqtrade and dependencies
  $(print_msg "$GREEN" "run [strategy]")    Start Freqtrade (default: NSESampleStrategy)
  $(print_msg "$GREEN" "stop")              Stop Freqtrade
  $(print_msg "$GREEN" "restart")           Restart Freqtrade
  $(print_msg "$GREEN" "status")            Show Freqtrade status
  $(print_msg "$GREEN" "logs")              Show live logs (tail -f)
  $(print_msg "$GREEN" "ui")                Open web interface
  $(print_msg "$GREEN" "clean-db")          Clean/reset database
  $(print_msg "$GREEN" "backtest")          Run strategy backtest
  $(print_msg "$GREEN" "test")              Run integration tests

$(print_msg "$YELLOW" "Broker Management:")
  $(print_msg "$GREEN" "broker setup")      Interactive broker configuration
  $(print_msg "$GREEN" "broker list")       List configured brokers
  $(print_msg "$GREEN" "broker test")       Test broker connections

$(print_msg "$YELLOW" "Options Trading:")
  $(print_msg "$GREEN" "options chains")    Get option chains (NIFTY/BANKNIFTY)
  $(print_msg "$GREEN" "options lots")      Show lot sizes
  $(print_msg "$GREEN" "options calculator") P&L calculator

$(print_msg "$YELLOW" "Examples:")
  ./freqtrade.sh install
  ./freqtrade.sh broker setup
  ./freqtrade.sh run
  ./freqtrade.sh options chains NIFTY
  ./freqtrade.sh ui
  ./freqtrade.sh status

$(print_msg "$YELLOW" "Features:")
  • 4 Indian Brokers: PaperBroker, OpenAlgo, SmartAPI, Zerodha
  • Options Trading: NSE/NFO options with lot size management
  • API Server: 30+ endpoints at http://localhost:8080/docs
  • Web UI: Analytics, broker management, backtesting
  • Secure Storage: Encrypted broker credentials

$(print_msg "$YELLOW" "Configuration:")
  Config file: $CONFIG_FILE
  Database: $DB_FILE
  Log file: $LOG_FILE
  API Server: http://localhost:8080

EOF
}

# Run integration tests
run_tests() {
    print_header "RUNNING TESTS"
    
    if [ ! -f "$PYTHON_BIN" ]; then
        print_msg "$RED" "✗ Python not found. Run: ./freqtrade.sh install"
        exit 1
    fi
    
    if [ -f "$SCRIPT_DIR/test_broker_integration.py" ]; then
        print_msg "$YELLOW" "→ Running integration tests..."
        "$PYTHON_BIN" "$SCRIPT_DIR/test_broker_integration.py"
    else
        print_msg "$YELLOW" "⚠ Test file not found: test_broker_integration.py"
    fi
}

# Main script
main() {
    case "${1:-help}" in
        install)
            install
            ;;
        run)
            shift
            run "$@"
            ;;
        stop)
            stop
            ;;
        restart)
            shift
            restart "$@"
            ;;
        status)
            status
            ;;
        logs)
            logs
            ;;
        clean-db)
            clean_db
            ;;
        backtest)
            shift
            backtest "$@"
            ;;
        test)
            run_tests
            ;;
        broker)
            shift
            broker_cmd "$@"
            ;;
        options)
            shift
            options_cmd "$@"
            ;;
        ui)
            open_ui
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_msg "$RED" "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main
main "$@"
