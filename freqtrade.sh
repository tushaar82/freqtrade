#!/bin/bash
#
# Freqtrade Management Script
# Handles: install, run, stop, status, clean, logs
#
# Usage: ./freqtrade.sh [command] [options]
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
        print_msg "$GREEN" "✓ Dependencies installed"
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
        print_msg "$YELLOW" "→ Creating default config..."
        cat > "$CONFIG_FILE" << 'EOF'
{
  "max_open_trades": 3,
  "stake_currency": "INR",
  "stake_amount": 1000,
  "tradable_balance_ratio": 0.99,
  "fiat_display_currency": "INR",
  "dry_run": false,
  "cancel_open_orders_on_exit": false,
  "trading_mode": "spot",
  "margin_mode": "",
  "exchange": {
    "name": "paperbroker",
    "initial_balance": 100000,
    "slippage_percent": 0.05,
    "commission_percent": 0.1,
    "pair_whitelist": [
      "RELIANCE/INR",
      "TCS/INR",
      "INFY/INR"
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
  "telegram": {
    "enabled": false
  },
  "api_server": {
    "enabled": false,
    "listen_ip_address": "127.0.0.1",
    "listen_port": 8080,
    "verbosity": "error",
    "jwt_secret_key": "changeme",
    "CORS_origins": [],
    "username": "freqtrader",
    "password": "changeme"
  },
  "bot_name": "freqtrade",
  "initial_state": "running",
  "force_entry_enable": false,
  "internals": {
    "process_throttle_secs": 5
  }
}
EOF
        print_msg "$GREEN" "✓ Default config created: $CONFIG_FILE"
        print_msg "$YELLOW" "  Note: Using PaperBroker by default. Edit config.json to use OpenAlgo/SmartAPI"
    fi
    
    print_msg "$GREEN" "\n✅ Installation complete!"
    print_msg "$YELLOW" "\nNext steps:"
    print_msg "$YELLOW" "  1. Edit config.json to configure your exchange"
    print_msg "$YELLOW" "  2. Run: ./freqtrade.sh run"
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

$(print_msg "$BLUE" "Freqtrade Management Script")

Usage: ./freqtrade.sh [command] [options]

Commands:
  $(print_msg "$GREEN" "install")           Install Freqtrade and dependencies
  $(print_msg "$GREEN" "run [strategy]")    Start Freqtrade (default: NSESampleStrategy)
  $(print_msg "$GREEN" "stop")              Stop Freqtrade
  $(print_msg "$GREEN" "restart")           Restart Freqtrade
  $(print_msg "$GREEN" "status")            Show Freqtrade status
  $(print_msg "$GREEN" "logs")              Show live logs (tail -f)
  $(print_msg "$GREEN" "clean-db")          Clean/reset database
  $(print_msg "$GREEN" "backtest")          Run strategy backtest
  $(print_msg "$GREEN" "test")              Run integration tests
  $(print_msg "$GREEN" "help")              Show this help message

Examples:
  ./freqtrade.sh install
  ./freqtrade.sh run
  ./freqtrade.sh run MyStrategy
  ./freqtrade.sh status
  ./freqtrade.sh logs
  ./freqtrade.sh stop
  ./freqtrade.sh clean-db
  ./freqtrade.sh backtest NSESampleStrategy 20231001-20231101

Configuration:
  Config file: $CONFIG_FILE
  Database: $DB_FILE
  Log file: $LOG_FILE

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
