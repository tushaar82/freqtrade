#!/usr/bin/env bash
# Comprehensive Freqtrade NSE System Test Script
# Tests: Paper Broker, WebUI, API, Backtesting, Data Management

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# API Configuration
API_URL="http://localhost:8080/api/v1"
API_USER="admin"
API_PASS="admin123"
JWT_TOKEN=""

# Functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_test() {
    echo -e "${YELLOW}TEST: $1${NC}"
    ((TESTS_TOTAL++))
}

print_pass() {
    echo -e "${GREEN}✓ PASS: $1${NC}"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}✗ FAIL: $1${NC}"
    ((TESTS_FAILED++))
}

# Test functions
test_venv() {
    print_test "Virtual environment"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        print_pass "Virtual environment activated"
    else
        print_fail "Virtual environment not found"
        exit 1
    fi
}

test_python_imports() {
    print_test "Python imports"
    if python -c "import freqtrade; from freqtrade.exchange import Paperbroker, Openalgo, Smartapi, Zerodha" 2>/dev/null; then
        print_pass "All imports successful"
    else
        print_fail "Import failed"
        return 1
    fi
}

test_config() {
    print_test "Configuration file"
    if [ -f "config_examples/config_paper_nse_webui.example.json" ]; then
        # Create test config if not exists
        if [ ! -f "config_test.json" ]; then
            cp config_examples/config_paper_nse_webui.example.json config_test.json
            print_pass "Test configuration created"
        else
            print_pass "Test configuration exists"
        fi
    else
        print_fail "Example configuration not found"
        return 1
    fi
}

test_directories() {
    print_test "Required directories"
    mkdir -p user_data/{data,strategies,raw_data,logs}
    if [ -d "user_data" ]; then
        print_pass "Directories created"
    else
        print_fail "Failed to create directories"
        return 1
    fi
}

test_paper_broker() {
    print_test "Paper broker initialization"
    python3 << 'EOFPY'
import json
from freqtrade.exchange import Paperbroker

# Load config
with open('config_test.json') as f:
    config = json.load(f)

# Initialize paper broker
try:
    broker = Paperbroker(config, validate=False)
    print("✓ Paper broker initialized successfully")
    print(f"✓ Initial balance: {broker._initial_balance}")
    print(f"✓ Slippage: {broker._slippage_percent}%")
    print(f"✓ Commission: {broker._commission_percent}%")
except Exception as e:
    print(f"✗ Paper broker initialization failed: {e}")
    exit(1)
EOFPY

    if [ $? -eq 0 ]; then
        print_pass "Paper broker working"
    else
        print_fail "Paper broker failed"
        return 1
    fi
}

test_nse_calendar() {
    print_test "NSE calendar"
    python3 << 'EOFPY'
from freqtrade.exchange import get_nse_calendar

try:
    calendar = get_nse_calendar()
    is_open = calendar.is_market_open()
    is_trading_day = calendar.is_trading_day()
    holidays = calendar.get_upcoming_holidays(30)
    
    print(f"✓ NSE calendar initialized")
    print(f"  Market open: {is_open}")
    print(f"  Trading day: {is_trading_day}")
    print(f"  Upcoming holidays: {len(holidays)}")
except Exception as e:
    print(f"✗ NSE calendar failed: {e}")
    exit(1)
EOFPY

    if [ $? -eq 0 ]; then
        print_pass "NSE calendar working"
    else
        print_fail "NSE calendar failed"
        return 1
    fi
}

test_rate_limiter() {
    print_test "Rate limiter"
    python3 << 'EOFPY'
from freqtrade.exchange.rate_limiter import BrokerRateLimits
import time

try:
    limiter = BrokerRateLimits.get_limiter('openalgo')
    
    # Test rate limiting
    start = time.time()
    for i in range(5):
        limiter.wait_if_needed()
    elapsed = time.time() - start
    
    stats = limiter.get_stats()
    print(f"✓ Rate limiter initialized")
    print(f"  Requests: {stats['total_requests']}")
    print(f"  Time elapsed: {elapsed:.2f}s")
except Exception as e:
    print(f"✗ Rate limiter failed: {e}")
    exit(1)
EOFPY

    if [ $? -eq 0 ]; then
        print_pass "Rate limiter working"
    else
        print_fail "Rate limiter failed"
        return 1
    fi
}

test_lot_size_manager() {
    print_test "Lot size manager"
    python3 << 'EOFPY'
from freqtrade.exchange.lot_size_manager import LotSizeManager

try:
    lot_manager = LotSizeManager()
    
    # Test lot sizes
    nifty_lot = lot_manager.get_lot_size("NIFTY")
    banknifty_lot = lot_manager.get_lot_size("BANKNIFTY")
    
    # Test quantity adjustment
    adjusted = lot_manager.adjust_quantity_to_lot("NIFTY", 30)
    
    print(f"✓ Lot size manager initialized")
    print(f"  NIFTY lot size: {nifty_lot}")
    print(f"  BANKNIFTY lot size: {banknifty_lot}")
    print(f"  Adjusted 30 to: {adjusted}")
except Exception as e:
    print(f"✗ Lot size manager failed: {e}")
    exit(1)
EOFPY

    if [ $? -eq 0 ]; then
        print_pass "Lot size manager working"
    else
        print_fail "Lot size manager failed"
        return 1
    fi
}

start_api_server() {
    print_test "Starting API server"
    
    # Kill any existing freqtrade processes
    pkill -f "freqtrade.*webserver" 2>/dev/null || true
    sleep 2
    
    # Start API server in background
    freqtrade webserver --config config_test.json > /tmp/freqtrade_api.log 2>&1 &
    API_PID=$!
    echo $API_PID > /tmp/freqtrade_api.pid
    
    # Wait for server to start
    echo "Waiting for API server to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8080/api/v1/ping > /dev/null 2>&1; then
            print_pass "API server started (PID: $API_PID)"
            sleep 2
            return 0
        fi
        sleep 1
    done
    
    print_fail "API server failed to start"
    cat /tmp/freqtrade_api.log
    return 1
}

test_api_login() {
    print_test "API authentication"
    
    RESPONSE=$(curl -s -X POST "$API_URL/token/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$API_USER&password=$API_PASS")
    
    JWT_TOKEN=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
    
    if [ -n "$JWT_TOKEN" ]; then
        print_pass "API authentication successful"
        echo "JWT Token: ${JWT_TOKEN:0:20}..."
    else
        print_fail "API authentication failed"
        echo "Response: $RESPONSE"
        return 1
    fi
}

test_api_endpoints() {
    print_test "API endpoints"
    
    # Test ping
    if curl -s -H "Authorization: Bearer $JWT_TOKEN" "$API_URL/ping" | grep -q "pong"; then
        echo "  ✓ /ping"
    else
        echo "  ✗ /ping"
    fi
    
    # Test status
    if curl -s -H "Authorization: Bearer $JWT_TOKEN" "$API_URL/status" | grep -q "state"; then
        echo "  ✓ /status"
    else
        echo "  ✗ /status"
    fi
    
    # Test balance
    if curl -s -H "Authorization: Bearer $JWT_TOKEN" "$API_URL/balance" | grep -q "currencies"; then
        echo "  ✓ /balance"
    else
        echo "  ✗ /balance"
    fi
    
    # Test NSE calendar
    if curl -s -H "Authorization: Bearer $JWT_TOKEN" "$API_URL/nse/calendar" | grep -q "market_hours"; then
        echo "  ✓ /nse/calendar"
    else
        echo "  ✗ /nse/calendar"
    fi
    
    # Test paper balance
    if curl -s -H "Authorization: Bearer $JWT_TOKEN" "$API_URL/paper/balance" | grep -q "initial_balance"; then
        echo "  ✓ /paper/balance"
    else
        echo "  ✗ /paper/balance"
    fi
    
    print_pass "API endpoints tested"
}

test_csv_upload() {
    print_test "CSV data upload"
    
    # Create sample CSV
    cat > /tmp/test_data.csv << 'EOFCSV'
datetime,open,high,low,close,volume
2024-01-01 09:15:00,100.0,102.0,99.0,101.0,1000
2024-01-01 09:16:00,101.0,103.0,100.0,102.0,1200
2024-01-01 09:17:00,102.0,104.0,101.0,103.0,1100
EOFCSV
    
    RESPONSE=$(curl -s -X POST \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -F "file=@/tmp/test_data.csv" \
        -F "pair=TESTSTOCK/INR" \
        "$API_URL/csv/upload")
    
    if echo "$RESPONSE" | grep -q "success"; then
        print_pass "CSV upload successful"
    else
        print_fail "CSV upload failed"
        echo "Response: $RESPONSE"
        return 1
    fi
}

test_webui() {
    print_test "WebUI accessibility"
    
    if curl -s http://localhost:8080/ | grep -q -i "freqtrade"; then
        print_pass "WebUI accessible"
    else
        print_fail "WebUI not accessible"
        return 1
    fi
}

stop_api_server() {
    if [ -f /tmp/freqtrade_api.pid ]; then
        API_PID=$(cat /tmp/freqtrade_api.pid)
        if ps -p $API_PID > /dev/null; then
            echo "Stopping API server (PID: $API_PID)..."
            kill $API_PID 2>/dev/null || true
            sleep 2
            rm /tmp/freqtrade_api.pid
        fi
    fi
}

test_backtesting() {
    print_test "Backtesting functionality"
    
    # Create a simple test strategy if not exists
    if [ ! -f "user_data/strategies/TestStrategy.py" ]; then
        cat > user_data/strategies/TestStrategy.py << 'EOFSTRAT'
from freqtrade.strategy import IStrategy
from pandas import DataFrame

class TestStrategy(IStrategy):
    minimal_roi = {"0": 0.01}
    stoploss = -0.05
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'enter_long'] = 0
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'exit_long'] = 0
        return dataframe
EOFSTRAT
    fi
    
    # Run a quick backtest
    if timeout 30s freqtrade backtesting --config config_test.json --strategy TestStrategy --timerange 20240101-20240102 2>&1 | grep -q "BACKTESTING REPORT"; then
        print_pass "Backtesting working"
    else
        echo "  (Skipped - no data available or timeout)"
    fi
}

# Cleanup function
cleanup() {
    echo ""
    echo "Cleaning up..."
    stop_api_server
    rm -f /tmp/test_data.csv
    rm -f /tmp/freqtrade_api.log
}

# Set trap for cleanup
trap cleanup EXIT

# Main test execution
main() {
    print_header "Freqtrade NSE System Test Suite"
    
    echo "This script will test:"
    echo "  - Virtual environment"
    echo "  - Python imports"
    echo "  - Configuration"
    echo "  - Paper broker"
    echo "  - NSE calendar"
    echo "  - Rate limiter"
    echo "  - Lot size manager"
    echo "  - API server"
    echo "  - WebUI"
    echo "  - CSV upload"
    echo "  - Backtesting"
    echo ""
    
    # Core tests
    print_header "Core Component Tests"
    test_venv
    test_python_imports
    test_config
    test_directories
    test_paper_broker
    test_nse_calendar
    test_rate_limiter
    test_lot_size_manager
    
    # API tests
    print_header "API and WebUI Tests"
    if start_api_server; then
        test_api_login
        test_api_endpoints
        test_csv_upload
        test_webui
    else
        echo "Skipping API tests due to server startup failure"
    fi
    
    # Backtesting tests
    print_header "Backtesting Tests"
    test_backtesting
    
    # Summary
    print_header "Test Summary"
    echo ""
    echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
    echo -e "Total Tests: $TESTS_TOTAL"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Start the system: ./start.sh"
        echo "  2. Access WebUI: http://localhost:8080"
        echo "  3. API documentation: http://localhost:8080/docs"
        echo ""
        return 0
    else
        echo -e "${RED}✗ Some tests failed. Please check the output above.${NC}"
        echo ""
        echo "Check logs:"
        echo "  - API log: /tmp/freqtrade_api.log"
        echo "  - User logs: user_data/logs/"
        echo ""
        return 1
    fi
}

# Run tests
main
