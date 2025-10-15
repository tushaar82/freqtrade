#!/bin/bash
# Freqtrade Installation Script for NSE Trading
# Supports: OpenAlgo, Smart API, and Paper Broker

set -e  # Exit on error

echo "============================================="
echo "  Freqtrade NSE Trading - Installation"
echo "============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in virtual environment
check_venv() {
    if [[ -z "${VIRTUAL_ENV}" ]]; then
        echo -e "${YELLOW}Warning: Not running in a virtual environment${NC}"
        echo "It's recommended to use a virtual environment"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}✓ Running in virtual environment: $VIRTUAL_ENV${NC}"
    fi
}

# Check Python version
check_python() {
    echo "Checking Python version..."
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python 3 is not installed${NC}"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    REQUIRED_VERSION="3.8"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        echo -e "${RED}✗ Python 3.8+ required, found $PYTHON_VERSION${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
}

# Install system dependencies
install_system_deps() {
    echo ""
    echo "Installing system dependencies..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y build-essential python3-dev python3-pip python3-venv curl git
        elif command -v yum &> /dev/null; then
            sudo yum install -y gcc gcc-c++ python3-devel python3-pip git
        fi
        echo -e "${GREEN}✓ System dependencies installed${NC}"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install python3 git
            echo -e "${GREEN}✓ System dependencies installed${NC}"
        else
            echo -e "${YELLOW}Please install Homebrew: https://brew.sh${NC}"
        fi
    fi
}

# Install Python dependencies
install_python_deps() {
    echo ""
    echo "Installing Freqtrade core dependencies..."
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Core dependencies installed${NC}"
}

# Install exchange-specific dependencies
install_exchange_deps() {
    echo ""
    echo "Which exchange will you use?"
    echo "1) Paper Broker (No dependencies needed)"
    echo "2) OpenAlgo (No extra dependencies needed)"
    echo "3) Smart API (Angel One)"
    echo "4) All of the above"
    read -p "Enter choice (1-4): " exchange_choice
    
    case $exchange_choice in
        3|4)
            echo "Installing Smart API dependencies..."
            pip install smartapi-python pyotp
            echo -e "${GREEN}✓ Smart API dependencies installed${NC}"
            ;;
    esac
}

# Install TA-Lib (optional but recommended)
install_talib() {
    echo ""
    read -p "Install TA-Lib for technical indicators? (recommended) (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if [ ! -f "build_helpers/ta-lib/lib/libta_lib.a" ]; then
                echo "Building TA-Lib from source..."
                ./build_helpers/install_ta-lib.sh
            fi
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install ta-lib
        fi
        pip install TA-Lib
        echo -e "${GREEN}✓ TA-Lib installed${NC}"
    fi
}

# Create directories
setup_directories() {
    echo ""
    echo "Setting up directories..."
    mkdir -p user_data/strategies
    mkdir -p user_data/data
    mkdir -p user_data/logs
    mkdir -p user_data/notebooks
    echo -e "${GREEN}✓ Directories created${NC}"
}

# Setup configuration
setup_config() {
    echo ""
    echo "Setting up configuration..."
    
    if [ ! -f "config.json" ]; then
        echo "Which exchange configuration would you like to use?"
        echo "1) Paper Broker (Virtual trading - recommended for beginners)"
        echo "2) OpenAlgo (Multi-broker NSE)"
        echo "3) Smart API (Angel One)"
        read -p "Enter choice (1-3): " config_choice
        
        case $config_choice in
            1)
                cp config_examples/config_paperbroker.example.json config.json
                echo -e "${GREEN}✓ Paper Broker configuration created${NC}"
                echo -e "${YELLOW}No API keys needed - ready to use!${NC}"
                ;;
            2)
                cp config_examples/config_openalgo_nse.example.json config.json
                echo -e "${GREEN}✓ OpenAlgo configuration created${NC}"
                echo -e "${YELLOW}Please edit config.json and add your OpenAlgo API key${NC}"
                ;;
            3)
                cp config_examples/config_smartapi_nse.example.json config.json
                echo -e "${GREEN}✓ Smart API configuration created${NC}"
                echo -e "${YELLOW}Please edit config.json and add your Angel One credentials${NC}"
                ;;
        esac
    else
        echo -e "${YELLOW}config.json already exists, skipping...${NC}"
    fi
}

# Download UI
setup_ui() {
    echo ""
    read -p "Install FreqUI (Web interface)? (recommended) (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Downloading FreqUI..."
        # Use python module instead of freqtrade command
        if python3 -m freqtrade install-ui 2>/dev/null; then
            echo -e "${GREEN}✓ FreqUI installed${NC}"
        else
            echo -e "${YELLOW}⚠ FreqUI installation failed${NC}"
            echo -e "${YELLOW}You can install it later with: freqtrade install-ui${NC}"
        fi
    fi
}

# Main installation
main() {
    echo "Starting installation..."
    echo ""
    
    check_python
    check_venv
    install_system_deps
    install_python_deps
    install_exchange_deps
    install_talib
    setup_directories
    setup_config
    setup_ui
    
    echo ""
    echo "============================================="
    echo -e "${GREEN}  Installation Complete! 🎉${NC}"
    echo "============================================="
    echo ""
    echo "Next steps:"
    echo "1. If using OpenAlgo or Smart API, edit config.json with your credentials"
    echo "2. Run: ./run_paper.sh to start paper trading with UI"
    echo "3. Access UI at: http://localhost:8080"
    echo ""
    echo "Quick commands:"
    echo "  ./run_paper.sh          - Start paper trading"
    echo "  freqtrade --help        - View all commands"
    echo "  freqtrade download-data - Download historical data"
    echo ""
    echo "Documentation:"
    echo "  NSE_TRADING_COMPLETE_GUIDE.md - Complete guide"
    echo "  docs/paperbroker-integration.md - Paper Broker guide"
    echo "  docs/smartapi-integration.md - Smart API guide"
    echo "  docs/openalgo-nse-integration.md - OpenAlgo guide"
    echo ""
}

# Run installation
main
