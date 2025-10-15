# Freqtrade Quick Reference

## 🚀 Getting Started (3 Commands)

```bash
# 1. Install everything
./freqtrade.sh install

# 2. Edit config (optional - defaults to PaperBroker)
nano config.json

# 3. Start trading
./freqtrade.sh run
```

---

## 📋 Common Commands

### Installation & Setup
```bash
./freqtrade.sh install              # Install Freqtrade + dependencies
./freqtrade.sh test                 # Run integration tests
```

### Running Freqtrade
```bash
./freqtrade.sh run                  # Start with NSESampleStrategy
./freqtrade.sh run MyStrategy       # Start with custom strategy
./freqtrade.sh stop                 # Stop Freqtrade
./freqtrade.sh restart              # Restart Freqtrade
./freqtrade.sh status               # Check if running
```

### Monitoring
```bash
./freqtrade.sh logs                 # Show live logs (Ctrl+C to exit)
./freqtrade.sh status               # Show status, uptime, CPU, memory
```

### Database Management
```bash
./freqtrade.sh clean-db             # Clean/reset database (with backup)
```

### Testing & Backtesting
```bash
./freqtrade.sh backtest                              # Backtest default
./freqtrade.sh backtest MyStrategy 20231001-20231101 # Custom backtest
./freqtrade.sh test                                  # Run integration tests
```

---

## ⚙️ Configuration Files

### Main Config: `config.json`
```json
{
  "exchange": {
    "name": "paperbroker",          // or "openalgo", "smartapi"
    "initial_balance": 100000,      // PaperBroker only
    "pair_whitelist": [
      "RELIANCE/INR",
      "TCS/INR"
    ]
  },
  "stake_amount": 1000,
  "max_open_trades": 3
}
```

### For OpenAlgo:
```json
{
  "exchange": {
    "name": "openalgo",
    "key": "YOUR_API_KEY",
    "urls": {"api": "http://127.0.0.1:5000"},
    "pair_whitelist": ["RELIANCE/INR", "TCS/INR"]
  }
}
```

---

## 📊 File Locations

| File | Location | Purpose |
|------|----------|---------|
| Config | `config.json` | Main configuration |
| Database | `tradesv3.sqlite` | Trade history |
| Logs | `freqtrade.log` | Application logs |
| PID | `freqtrade.pid` | Process ID (when running) |
| Strategy | `user_data/strategies/` | Trading strategies |

---

## 🔥 Common Workflows

### First Time Setup
```bash
./freqtrade.sh install              # Install
./freqtrade.sh test                 # Verify installation
./freqtrade.sh run                  # Start with defaults
./freqtrade.sh logs                 # Monitor
```

### Daily Operation
```bash
./freqtrade.sh status               # Check status
./freqtrade.sh logs                 # Monitor logs
# Edit strategy if needed
./freqtrade.sh restart              # Apply changes
```

### Testing New Strategy
```bash
# 1. Backtest first
./freqtrade.sh backtest NewStrategy 20231001-20231101

# 2. Paper trade
# Edit config.json -> set "name": "paperbroker"
./freqtrade.sh restart NewStrategy

# 3. Monitor for a few days
./freqtrade.sh logs

# 4. If good, switch to real trading
# Edit config.json -> set "name": "openalgo"
./freqtrade.sh restart NewStrategy
```

### Troubleshooting
```bash
./freqtrade.sh status               # Check if running
./freqtrade.sh logs                 # Check errors
./freqtrade.sh stop                 # Stop if needed
./freqtrade.sh clean-db             # Reset if corrupted
./freqtrade.sh run                  # Start fresh
```

---

## 🎯 Quick Tips

1. **Always backtest first** before live trading
2. **Start with PaperBroker** to test your setup
3. **Monitor logs regularly** for errors
4. **Clean database** if you see weird behavior
5. **Backup your config** before major changes
6. **Test after updates** with `./freqtrade.sh test`

---

## 🆘 Help

```bash
./freqtrade.sh help                 # Show all commands
```

For detailed guides:
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - All documentation
- **[CUSTOM_EXCHANGE_GUIDE.md](CUSTOM_EXCHANGE_GUIDE.md)** - Exchange setup
- **[NSE_TRADING_COMPLETE_GUIDE.md](NSE_TRADING_COMPLETE_GUIDE.md)** - NSE details

---

**Happy Trading! 📈**
