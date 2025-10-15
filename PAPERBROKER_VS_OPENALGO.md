# PaperBroker vs OpenAlgo - Understanding the Difference

## 🔴 PaperBroker (Current Setup)

**What it does:**
- Generates SIMULATED historical candles on startup
- Creates fake price movements
- Useful for TESTING strategies, NOT real-time trading

**Behavior:**
```
15:44 - Bot starts
15:44 - Generates 500 fake candles (going back ~42 hours)
15:44 - Analyzes all 500 candles
15:44 - Places trades on "old" simulated candles
```

**Result:** You see "trades" from hours/days ago (simulated times)

---

## ✅ OpenAlgo (Recommended for Real Trading)

**What it does:**
- Fetches REAL NSE market data from your broker
- Gets actual live prices
- Only trades when NEW candles form in real-time

**Behavior:**
```
15:44 - Bot starts
15:44 - Loads 100 real historical candles (for indicators)
15:45 - NEW candle closes → Analyzes → Trades (if signal)
15:50 - NEW candle closes → Analyzes → Trades (if signal)
```

**Result:** ONLY future trades, no historical simulated data

---

## 📊 Comparison Table

| Feature | PaperBroker | OpenAlgo |
|---------|-------------|----------|
| Data Source | Simulated | Real NSE |
| Historical Trades | ❌ Shows fake old trades | ✅ No old trades |
| Real-time Updates | ❌ No | ✅ Yes |
| Actual Broker | ❌ Virtual | ✅ Yes (Zerodha, etc.) |
| Real Money | ❌ No | ✅ Yes (if dry_run=false) |
| Use Case | Strategy testing | Real trading |

---

## 🚀 How to Switch to OpenAlgo

### Prerequisites:
1. OpenAlgo server running (http://127.0.0.1:5000)
2. Broker account (Zerodha/Fyers/Angel One/etc)
3. OpenAlgo API key

### Quick Switch:
```bash
# 1. Stop current bot
./freqtrade.sh stop

# 2. Update config.json - change exchange section to:
{
  "exchange": {
    "name": "openalgo",
    "key": "your_openalgo_api_key",
    "urls": {"api": "http://127.0.0.1:5000"},
    "pair_whitelist": ["RELIANCE/INR", "TCS/INR", "INFY/INR"]
  }
}

# 3. Restart
./freqtrade.sh restart
```

---

## 💡 Bottom Line

**If you want ONLY real-time future trades (no historical):**
→ **You MUST use OpenAlgo or SmartAPI**

**If you want to test strategies with simulated data:**
→ PaperBroker is perfect

**Current issue:** You're using PaperBroker but expecting OpenAlgo behavior!

