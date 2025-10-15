# NSE Trading Brokers Guide

This Freqtrade setup supports **three NSE brokers** for Indian stock market trading.

---

## 📊 Available Brokers

### 1. **PaperBroker** - Virtual Trading (Testing)
**Purpose:** Strategy testing and learning without real money

**Features:**
- ✅ No API keys required
- ✅ ₹100,000 virtual balance
- ✅ Simulated slippage and commissions
- ✅ Complete trade history tracking
- ⚠️ **Limitation:** Simulated candles (not real-time data)

**Configuration:**
```json
{
  "exchange": {
    "name": "paperbroker",
    "initial_balance": 100000,
    "slippage_percent": 0.05,
    "commission_percent": 0.1,
    "pair_whitelist": ["RELIANCE/INR", "TCS/INR"]
  }
}
```

**Best For:**
- Learning algorithmic trading
- Testing strategies before going live
- Development and debugging

---

### 2. **OpenAlgo** - Multi-Broker Platform (Recommended for NSE)
**Purpose:** Real NSE trading through multiple broker APIs

**Features:**
- ✅ Real NSE market data (live tick-by-tick)
- ✅ Support for multiple brokers (Zerodha, Fyers, Angel One, etc.)
- ✅ NSE market hours validation (9:15 AM - 3:30 PM IST)
- ✅ MIS (intraday), CNC (delivery), NRML (F&O) support
- ✅ Self-hosted solution

**Requirements:**
1. OpenAlgo server running (http://127.0.0.1:5000)
2. Broker API credentials configured in OpenAlgo
3. OpenAlgo API key

**Configuration:**
```json
{
  "exchange": {
    "name": "openalgo",
    "key": "your_openalgo_api_key",
    "urls": {"api": "http://127.0.0.1:5000"},
    "pair_whitelist": ["RELIANCE/INR", "TCS/INR", "INFY/INR"]
  }
}
```

**Best For:**
- Real NSE trading
- Users with existing broker accounts
- Multi-broker support
- Production trading

---

### 3. **SmartAPI** - Angel One Direct Integration
**Purpose:** Direct integration with Angel One (Angel Broking)

**Features:**
- ✅ Direct Angel One API integration
- ✅ TOTP authentication
- ✅ NSE, BSE, MCX support
- ✅ WebSocket real-time data
- ✅ GTT (Good Till Triggered) orders

**Requirements:**
1. Angel One demat account
2. API credentials from Angel One
3. TOTP secret key

**Configuration:**
```json
{
  "exchange": {
    "name": "smartapi",
    "key": "your_api_key",
    "username": "client_code",
    "password": "pin",
    "totp_token": "totp_secret"
  }
}
```

**Best For:**
- Angel One customers
- Direct broker integration (no middleware)
- Real-time WebSocket data

---

## 🎯 Which Broker Should You Use?

| Scenario | Recommended Broker |
|----------|-------------------|
| **Testing strategies** | PaperBroker |
| **Real NSE trading with any broker** | OpenAlgo |
| **Angel One account holder** | SmartAPI |
| **Learning & Development** | PaperBroker |
| **Production trading** | OpenAlgo or SmartAPI |

---

## 🚀 Quick Start

### Current Setup: PaperBroker
```bash
# Already configured and running
./freqtrade.sh status
./freqtrade.sh logs
```

### Switch to OpenAlgo
```bash
# 1. Start OpenAlgo server first
# 2. Update config.json with OpenAlgo details
# 3. Restart
./freqtrade.sh restart
```

### Switch to SmartAPI
```bash
# 1. Get Angel One API credentials
# 2. Update config.json with SmartAPI details  
# 3. Restart
./freqtrade.sh restart
```

---

## 📁 Related Files

- `freqtrade/exchange/paperbroker.py` - PaperBroker implementation
- `freqtrade/exchange/openalgo.py` - OpenAlgo implementation
- `freqtrade/exchange/smartapi.py` - SmartAPI implementation
- `config.json` - Your current configuration
- `user_data/strategies/NSESampleStrategy.py` - Trading strategy

---

## 🔧 Management Commands

```bash
./freqtrade.sh install   # Install Freqtrade
./freqtrade.sh run       # Start trading
./freqtrade.sh stop      # Stop bot
./freqtrade.sh restart   # Restart bot
./freqtrade.sh status    # Check status
./freqtrade.sh logs      # View logs
./freqtrade.sh clean-db  # Clean database
```

---

**Note:** PaperBroker is currently active. For real-time NSE trading with actual market data, switch to OpenAlgo or SmartAPI.
