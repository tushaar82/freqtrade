# 🚀 START HERE

## Welcome to Freqtrade with Custom Exchange Support!

Everything you need is ready. Here's how to get started in 3 commands:

---

## ⚡ Quick Start (Copy & Paste)

```bash
# 1. Install everything (takes ~5 minutes)
./freqtrade.sh install

# 2. Start trading (uses PaperBroker by default - no real money)
./freqtrade.sh run

# 3. Monitor what's happening
./freqtrade.sh logs
```

**That's it!** Freqtrade is now running with:
- ✅ PaperBroker (virtual trading)
- ✅ ₹100,000 virtual balance
- ✅ NSESampleStrategy (RSI + EMA + MACD)
- ✅ 3 stocks: RELIANCE, TCS, INFY

---

## 📋 All Commands

```bash
./freqtrade.sh install      # Install Freqtrade
./freqtrade.sh run          # Start trading
./freqtrade.sh stop         # Stop trading
./freqtrade.sh restart      # Restart
./freqtrade.sh status       # Check if running
./freqtrade.sh logs         # View live logs
./freqtrade.sh clean-db     # Clean database
./freqtrade.sh backtest     # Run backtest
./freqtrade.sh test         # Run tests
./freqtrade.sh help         # Show all commands
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** ⭐ | Command cheatsheet - fastest reference |
| **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** | Complete documentation index |
| **[CUSTOM_EXCHANGE_GUIDE.md](CUSTOM_EXCHANGE_GUIDE.md)** | Exchange setup & configuration |
| **[NSE_TRADING_COMPLETE_GUIDE.md](NSE_TRADING_COMPLETE_GUIDE.md)** | NSE-specific trading guide |

---

## 🎯 What's Configured

### Default Setup (PaperBroker)
- **Exchange:** PaperBroker (virtual trading, no real money)
- **Balance:** ₹100,000 (virtual)
- **Strategy:** NSESampleStrategy
- **Stocks:** RELIANCE/INR, TCS/INR, INFY/INR
- **Stake:** ₹1,000 per trade
- **Max Trades:** 3 concurrent

### Available Exchanges
1. **PaperBroker** - Virtual trading (default)
2. **OpenAlgo** - Real NSE/BSE/MCX trading
3. **SmartAPI** - Angel One direct

---

## 🔧 Configuration

Edit `config.json` to customize:
- Exchange (PaperBroker, OpenAlgo, SmartAPI)
- Stocks to trade
- Stake amount
- Number of concurrent trades
- Risk parameters

---

## 📊 Strategy Features

**NSESampleStrategy includes:**
- ✅ RSI indicator (oversold/overbought)
- ✅ EMA crossover (trend detection)
- ✅ Volume analysis
- ✅ MACD confirmation
- ✅ Bollinger Bands
- ✅ Trailing stoploss (1% trail after 1.5% profit)
- ✅ NSE market hours validation
- ✅ Force exit before market close

---

## 🎓 Learning Path

### Beginner (Start Here)
1. Run `./freqtrade.sh install`
2. Run `./freqtrade.sh run`
3. Monitor with `./freqtrade.sh logs`
4. Check **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** for commands

### Intermediate
1. Read **[CUSTOM_EXCHANGE_GUIDE.md](CUSTOM_EXCHANGE_GUIDE.md)**
2. Backtest strategies: `./freqtrade.sh backtest`
3. Modify `config.json` for your needs
4. Test with PaperBroker first

### Advanced
1. Read **[NSE_TRADING_COMPLETE_GUIDE.md](NSE_TRADING_COMPLETE_GUIDE.md)**
2. Configure OpenAlgo or SmartAPI for real trading
3. Create custom strategies in `user_data/strategies/`
4. Run integration tests: `./freqtrade.sh test`

---

## 🆘 Need Help?

```bash
# Show all commands
./freqtrade.sh help

# Check if running
./freqtrade.sh status

# View logs
./freqtrade.sh logs

# Test everything
./freqtrade.sh test
```

**For detailed help:**
- Check **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)**
- Read **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)**

---

## ⚠️ Important Notes

1. **Default is PaperBroker** - No real money involved
2. **Test before live trading** - Always backtest first
3. **Monitor regularly** - Check logs for errors
4. **NSE market hours** - Trading only 09:30-15:15
5. **Start small** - Begin with small stakes

---

## ✅ What Works

- ✅ Scanning all configured pairs
- ✅ Entry signals (RSI + EMA + Volume + MACD)
- ✅ Exit signals (Multiple conditions)
- ✅ Trailing stoploss (Profit protection)
- ✅ Force exits (EOD square-off)
- ✅ Error handling (Automatic retry)
- ✅ Database management
- ✅ Live monitoring

---

## 🎉 You're Ready!

Everything is installed and configured. Just run:

```bash
./freqtrade.sh install
./freqtrade.sh run
```

**Happy Trading! 📈**
