# Quick Start: Testing with FreqUI

## What's Been Set Up

### 1. FreqUI Enabled ✅
- **URL**: http://localhost:8080
- **Username**: `freqtrader`
- **Password**: `SuperSecurePassword`

### 2. Aggressive Test Strategy ✅
- **Name**: AggressiveTestStrategy
- **Behavior**: Places trades continuously
- **Entry**: 30% chance every 5 seconds
- **Delay**: 30 seconds between trades per pair
- **Max Trades**: 5 concurrent
- **Stake**: 500 INR per trade

## How to Start

### Step 1: Start Freqtrade
```bash
./venv/bin/freqtrade trade --config config.json --strategy AggressiveTestStrategy
```

### Step 2: Open FreqUI
1. Open browser: http://localhost:8080
2. Login:
   - Username: `freqtrader`
   - Password: `SuperSecurePassword`
3. You'll see the dashboard with trades

### Step 3: Watch Trades
In the terminal, you'll see:
```
🎲 AGGRESSIVE TEST: Generated BUY signal for RELIANCE/INR
Creating order for RELIANCE/INR
Order placed successfully
```

In FreqUI, you'll see:
- Open trades
- Trade history
- Performance charts
- Real-time updates

## Current Status

### Mode: DRY RUN (Safe) ✅
- Orders are simulated
- No real money
- No calls to OpenAlgo for orders
- Perfect for testing UI

### To Enable Real Trading:
Edit `config.json`:
```json
{
  "dry_run": false
}
```

Then restart Freqtrade.

## Troubleshooting

### FreqUI Not Loading
```bash
# Install FreqUI
./venv/bin/freqtrade install-ui

# Restart
pkill -f "freqtrade trade"
./venv/bin/freqtrade trade --config config.json --strategy AggressiveTestStrategy
```

### No Trades Appearing
1. **Wait 30-60 seconds** - Strategy needs time to generate signals
2. **Check logs**:
   ```bash
   tail -f user_data/logs/freqtrade.log | grep "AGGRESSIVE TEST"
   ```
3. **Verify strategy is running**:
   ```bash
   ps aux | grep freqtrade
   ```

### Trades Not Showing in UI
1. **Refresh browser** (F5)
2. **Check API is enabled** in config.json:
   ```json
   "api_server": {
     "enabled": true
   }
   ```
3. **Check port 8080** is not blocked

## What You'll See

### In Terminal:
```
🎲 AGGRESSIVE TEST: Generated BUY signal for RELIANCE/INR
🎲 AGGRESSIVE TEST: Generated BUY signal for TCS/INR
Creating dry-run order for RELIANCE/INR
Order placed: order_id=123
```

### In FreqUI:
- **Dashboard**: Overview of performance
- **Trades**: List of open and closed trades
- **Performance**: Charts and statistics
- **Pairs**: Performance by trading pair
- **Logs**: Real-time log viewer

## Strategy Behavior

### Entry Logic:
- Checks every 5 seconds
- 30% chance to enter
- 30-second cooldown per pair
- Maximum 5 concurrent trades

### Exit Logic:
- 15% chance to exit per check
- 1% profit target (ROI)
- 2% stop loss

### Result:
- Trades placed continuously
- Realistic delays between trades
- Good for testing UI and order flow

## Quick Commands

```bash
# Start with UI
./venv/bin/freqtrade trade --config config.json --strategy AggressiveTestStrategy

# Watch logs
tail -f user_data/logs/freqtrade.log

# Check trades
./venv/bin/freqtrade show_trades --config config.json

# Stop
pkill -f "freqtrade trade"
```

## Access Points

- **FreqUI**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **API Health**: http://localhost:8080/api/v1/ping

## Next Steps

1. ✅ Start Freqtrade with aggressive strategy
2. ✅ Open FreqUI in browser
3. ✅ Watch trades appear in real-time
4. ✅ Verify everything works
5. ⚠️ When ready, set `dry_run: false` for real trading

---

**Happy Testing! 🚀**

The aggressive strategy will start placing trades within 30-60 seconds!
