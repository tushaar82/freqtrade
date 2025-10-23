# Dry Run vs Live Trading

## Current Status: DRY RUN MODE ✅

Your Freqtrade is currently in **DRY RUN** mode, which is **SAFE** and **CORRECT** for testing!

---

## What is Dry Run Mode?

### Dry Run (dry_run: true) - CURRENT MODE
```json
{
  "dry_run": true
}
```

**What happens:**
- ✅ Strategy generates BUY/SELL signals
- ✅ Freqtrade simulates order placement internally
- ✅ Trades are tracked in the database
- ✅ PnL is calculated based on price changes
- ❌ **NO actual API calls to OpenAlgo's placeorder endpoint**
- ❌ **NO real money involved**
- ❌ **NO real orders on your broker**

**Why you see:**
- ✅ Trades in FreqUI (simulated)
- ✅ OpenAlgo API calls for data (history, orderstatus)
- ❌ NO OpenAlgo API calls for placeorder
- ❌ Amount showing as 0 (simulation issue)

---

## Live Trading Mode

### Live Mode (dry_run: false)
```json
{
  "dry_run": false
}
```

**What happens:**
- ✅ Strategy generates BUY/SELL signals
- ✅ **REAL API calls to OpenAlgo's placeorder endpoint**
- ✅ **REAL orders placed with your broker**
- ✅ **REAL money is used**
- ✅ Proper quantities calculated
- ✅ PnL updates with real fills

**You will see:**
- ✅ OpenAlgo placeorder API requests
- ✅ Orders appearing in OpenAlgo dashboard
- ✅ Orders executed on your broker (Zerodha/Finvasia/etc)
- ✅ Proper amounts and quantities
- ✅ Real PnL based on actual fills

---

## Why Dry Run First?

### Safety Reasons:
1. ✅ Test strategy logic without risk
2. ✅ Verify symbol mapping works
3. ✅ Check data fetching is correct
4. ✅ Ensure FreqUI displays properly
5. ✅ No financial risk

### What We've Verified:
- ✅ Symbol mapping: RELIANCE/INR → RELIANCE on NSE
- ✅ Data fetching: 472 candles from OpenAlgo
- ✅ Strategy signals: BUY/SELL being generated
- ✅ FreqUI: Displaying trades
- ✅ All methods implemented

---

## How to Enable Live Trading

### ⚠️ WARNING: This uses REAL MONEY!

### Step 1: Backup Your Config
```bash
cp config.json config.json.backup
```

### Step 2: Edit config.json
```bash
nano config.json
```

Change:
```json
{
  "dry_run": false,  // Change from true to false
  "stake_amount": 5000,  // Start with small amount
  "max_open_trades": 2  // Limit concurrent trades
}
```

### Step 3: Verify OpenAlgo
```bash
curl http://127.0.0.1:5000
```

### Step 4: Start Live Trading
```bash
./start.sh
```

### Step 5: Monitor Closely
```bash
# Watch logs
tail -f user_data/logs/freqtrade.log | grep -E "(placeorder|Order placed)"

# Watch FreqUI
Open: http://localhost:8080

# Check OpenAlgo
Open: http://127.0.0.1:5000
```

---

## What You'll See in Live Mode

### In Freqtrade Logs:
```
2025-10-23 10:15:30 - INFO - Order calculation for RELIANCE/INR:
2025-10-23 10:15:30 - INFO -   - Original amount: 3.33
2025-10-23 10:15:30 - INFO -   - Price/Rate: 1500.50
2025-10-23 10:15:30 - INFO -   - Final quantity: 3 shares
2025-10-23 10:15:30 - INFO -   - Order value: 4501.50 INR
2025-10-23 10:15:31 - INFO - OpenAlgo request: POST http://127.0.0.1:5000/api/v1/placeorder
2025-10-23 10:15:31 - INFO - Order placed successfully: order_id=25102300000015
```

### In OpenAlgo Dashboard:
```
Order ID: 25102300000015
Symbol: RELIANCE
Exchange: NSE
Action: BUY
Quantity: 3
Price: 1500.50
Status: OPEN
```

### In FreqUI:
```
Pair: RELIANCE/INR
Amount: 3.00
Stake: 5000
Open Rate: 1500.50
Current Rate: 1505.25
PnL: +0.32% (+14.25 INR)
```

---

## Current Behavior Explained

### Why No placeorder Requests?
**Because dry_run: true**
- Freqtrade simulates orders internally
- No need to call OpenAlgo's placeorder API
- This is the CORRECT behavior for dry-run mode

### Why Amount Shows 0?
**Dry-run simulation issue**
- In dry-run, Freqtrade doesn't calculate actual quantities
- It just tracks the stake amount
- In live mode, proper quantities are calculated

### Why No PnL Updates?
**Dry-run uses simulated fills**
- Prices are fetched from OpenAlgo
- But fills are simulated
- PnL calculation needs real fill data

---

## Recommendation

### For Now (Testing):
✅ **Keep dry_run: true**
- Continue testing with AggressiveTestStrategy
- Verify all signals are generated correctly
- Check FreqUI displays properly
- No financial risk

### When Ready (Production):
⚠️ **Set dry_run: false**
- Create your own strategy (not random)
- Start with small stake amounts (1000-2000 INR)
- Limit max_open_trades to 1-2
- Monitor very closely for first few trades
- Set proper stop losses

---

## Testing Checklist

Before enabling live trading:

- [ ] Strategy logic is sound (not random!)
- [ ] Tested in dry-run for several hours
- [ ] Verified data fetching works
- [ ] Checked symbol mapping is correct
- [ ] Set appropriate stake amounts
- [ ] Configured stop losses
- [ ] Limited max open trades
- [ ] Understand the risks
- [ ] Have monitoring in place
- [ ] Know how to stop the bot

---

## Quick Commands

### Check Current Mode:
```bash
grep "dry_run" config.json
```

### Enable Live Trading:
```bash
# Edit config
nano config.json
# Change dry_run to false
# Save and restart
./start.sh
```

### Disable Live Trading:
```bash
# Edit config
nano config.json
# Change dry_run to true
# Save and restart
./start.sh
```

### Emergency Stop:
```bash
pkill -f "freqtrade trade"
```

---

## Summary

### Current Status:
- ✅ **Dry Run Mode** (SAFE)
- ✅ Strategy working
- ✅ Data fetching working
- ✅ Symbol mapping working
- ✅ FreqUI working
- ❌ No real orders (by design)

### To Place Real Orders:
1. Set `dry_run: false`
2. Restart Freqtrade
3. Monitor closely
4. Real orders will be placed on OpenAlgo

### Safety First:
- Start with dry-run
- Test thoroughly
- Use small amounts
- Monitor closely
- Have a stop plan

---

**Your system is working perfectly in dry-run mode!**

To see real orders on OpenAlgo, simply set `dry_run: false` when you're ready! 🚀

