# Documentation Index

## ⚡ Quick Start

**New to Freqtrade? Start here:**

0. **[START_HERE.md](START_HERE.md)** 🎯 **ABSOLUTE BEGINNER? READ THIS FIRST!**
   - Complete getting started guide
   - What's installed and configured
   - Learning path from beginner to advanced

1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** ⭐ **COMMAND CHEATSHEET**
   - 3 commands to get running
   - All commands reference
   - Common workflows

2. **Management Script:** `./freqtrade.sh`
   - Single script for everything
   - Run `./freqtrade.sh help` for all commands

---

## 📚 Available Documentation

### For Users

1. **[CUSTOM_EXCHANGE_GUIDE.md](CUSTOM_EXCHANGE_GUIDE.md)** ⭐ **START HERE**
   - Quick start guide
   - All supported exchanges (PaperBroker, OpenAlgo, SmartAPI)
   - How to configure and run
   - Adding new exchanges
   - Troubleshooting

2. **[NSE_TRADING_COMPLETE_GUIDE.md](NSE_TRADING_COMPLETE_GUIDE.md)**
   - Detailed NSE-specific trading guide
   - Market hours, regulations
   - Best practices for Indian markets

3. **[README.md](README.md)**
   - Main Freqtrade documentation
   - General setup and usage

### For Developers

4. **[CONTRIBUTING.md](CONTRIBUTING.md)**
   - How to contribute to the project
   - Code standards and guidelines

### Testing

5. **[test_broker_integration.py](test_broker_integration.py)**
   - Automated test suite
   - Validates all exchange functionality
   - Run with: `python3 test_broker_integration.py`

---

## 🚀 Management Script

**`./freqtrade.sh`** - All-in-one management script

### Commands:
```bash
./freqtrade.sh install      # Install everything
./freqtrade.sh run          # Start trading
./freqtrade.sh stop         # Stop trading
./freqtrade.sh restart      # Restart
./freqtrade.sh status       # Check status
./freqtrade.sh logs         # View logs
./freqtrade.sh clean-db     # Clean database
./freqtrade.sh backtest     # Run backtest
./freqtrade.sh test         # Run tests
./freqtrade.sh help         # Show help
```

### Legacy Scripts (still available):
- **`run_paper.sh`** - Quick start with PaperBroker
- **`setup.sh`** - Installation script
- **`install.sh`** - Dependency installation

---

## 🎯 Recommended Reading Order

**Absolute Beginner:**
1. **QUICK_REFERENCE.md** - Get running in 3 commands
2. Run `./freqtrade.sh install && ./freqtrade.sh run`
3. Monitor with `./freqtrade.sh logs`

**Understanding the System:**
1. **CUSTOM_EXCHANGE_GUIDE.md** - How exchanges work
2. **NSE_TRADING_COMPLETE_GUIDE.md** - NSE-specific details
3. Code documentation in `freqtrade/exchange/` for implementation

---

## ✨ What's Implemented

- ✅ **PaperBroker** - Virtual trading for testing
- ✅ **OpenAlgo** - NSE/BSE/MCX trading
- ✅ **SmartAPI** - Angel One direct integration
- ✅ **Adapter Pattern** - No CCXT dependency for custom exchanges
- ✅ **Trailing Stoploss** - Automated profit protection
- ✅ **NSE Market Hours** - Automatic validation
- ✅ **Force Exits** - EOD square-off
- ✅ **Error Handling** - Comprehensive retry logic

---

**Everything is production-ready! Happy trading! 📈**
