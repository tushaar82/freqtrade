# Testing OpenAlgo Trade Placement

## Overview

A test strategy has been created to verify that trades are being placed correctly through OpenAlgo.

## Test Strategy: TestOpenAlgoStrategy

### Features:
- ✅ Places random BUY signals (5% chance per candle)
- ✅ Places random SELL signals (10% chance per candle)  
- ✅ Limited to 3 test trades maximum
- ✅ 2% profit target, 2% stop loss
- ✅ Uses 5-minute timeframe

### Safety Features:
- Currently in **DRY RUN** mode (no real money)
- Limited to 2 concurrent trades
- Only 1000 INR stake per trade
- Maximum 3 trades total

## How to Test

### Step 1: Start Test (Dry Run Mode)

```bash
./test_openalgo_trades.sh
```

This will:
1. Stop any running Freqtrade instance
2. Start with TestOpenAlgoStrategy
3. Place random test trades
4. Log everything to `user_data/logs/test_trades.log`

### Step 2: Monitor Trades

Watch the terminal for messages like:
```
🎲 TEST TRADE SIGNAL: Generated BUY signal for RELIANCE/INR
📊 Placing order for RELIANCE/INR
✅ Order placed successfully
```

### Step 3: Check OpenAlgo

1. Open OpenAlgo dashboard: http://127.0.0.1:5000
2. Check "Orders" section
3. Verify test orders appear

## Enable REAL Trading

⚠️ **WARNING**: Only do this when you're ready for real trades!

### Method 1: Edit config.json

```json
{
  "dry_run": false,  // Change from true to false
  "stake_amount": 1000  // Adjust as needed
}
```

### Method 2: Command line

```bash
# Edit config
nano config.json

# Change dry_run to false
# Save and exit

# Restart
./test_openalgo_trades.sh
```

## What to Expect

### In Dry Run Mode:
- ✅ Strategy generates signals
- ✅ Orders are simulated
- ✅ No real money involved
- ✅ OpenAlgo API is NOT called for orders
- ✅ Safe for testing

### In Live Mode (dry_run: false):
- ✅ Strategy generates signals
- ✅ Real orders sent to OpenAlgo
- ✅ OpenAlgo places orders with your broker
- ⚠️ REAL MONEY IS USED
- ⚠️ Orders execute on NSE

## Monitoring

### View Logs:
```bash
tail -f user_data/logs/test_trades.log
```

### Check Trades:
```bash
# View open trades
./venv/bin/freqtrade show_trades --config config.json

# View trade history
./venv/bin/freqtrade show_trades --config config.json --trade-ids 1 2 3
```

### Web UI:
```bash
# If API is enabled
Open: http://localhost:8080
```

## Troubleshooting

### No Trades Being Placed

**Cause**: Random signals haven't triggered yet  
**Solution**: Wait a few minutes, or increase probability in strategy

### Orders Failing

**Cause**: OpenAlgo connection issue  
**Solution**: 
1. Check OpenAlgo is running: `curl http://127.0.0.1:5000`
2. Verify API key in config.json
3. Check OpenAlgo logs

### "Outdated history" Warnings

**Cause**: Market is closed  
**Solution**: Normal! Will resolve when market opens at 9:15 AM IST

## Strategy Customization

Edit `user_data/strategies/TestOpenAlgoStrategy.py`:

### Increase Trade Frequency:
```python
if random.random() < 0.20:  # Change from 0.05 to 0.20 (20% chance)
```

### Increase Max Trades:
```python
max_trades = 10  # Change from 3 to 10
```

### Change Profit Target:
```python
minimal_roi = {
    "0": 0.05,   # 5% profit target (was 2%)
}
```

### Change Stop Loss:
```python
stoploss = -0.05  # 5% stop loss (was 2%)
```

## Verification Checklist

Before enabling real trading, verify:

- [ ] OpenAlgo server is running
- [ ] API key is correct in config.json
- [ ] Symbol mapping is working (check logs for "Fetched X candles")
- [ ] Test trades work in dry-run mode
- [ ] You understand the risk
- [ ] Stake amount is appropriate
- [ ] Stop loss is set correctly

## Stop Testing

```bash
# Stop Freqtrade
pkill -f "freqtrade trade"

# Or press Ctrl+C in the terminal
```

## Switch Back to Production Strategy

```bash
# Edit config.json
nano config.json

# Change strategy back
{
  "strategy": "SampleStrategy"  // or your production strategy
}

# Restart
./start.sh
```

## Important Notes

1. **Dry Run First**: Always test in dry-run mode before live trading
2. **Small Stakes**: Start with small amounts (1000-5000 INR)
3. **Monitor Closely**: Watch the first few trades carefully
4. **Market Hours**: NSE trades 9:15 AM - 3:30 PM IST (Mon-Fri)
5. **Symbol Mapping**: Automatic conversion RELIANCE/INR → RELIANCE on NSE

## Example Output

### Successful Trade Placement:
```
2025-10-23 09:15:30 - INFO - 🎲 TEST TRADE SIGNAL: Generated BUY signal for RELIANCE/INR
2025-10-23 09:15:31 - INFO - Fetching OHLCV for RELIANCE/INR
2025-10-23 09:15:31 - INFO - Fetched 312 candles for RELIANCE/INR from OpenAlgo
2025-10-23 09:15:32 - INFO - Placing order: BUY RELIANCE/INR, amount: 1, price: 1450.50
2025-10-23 09:15:32 - INFO - OpenAlgo request: POST /api/v1/placeorder
2025-10-23 09:15:33 - INFO - ✅ Order placed successfully: order_id=OA12345
```

## Support

If you encounter issues:
1. Check logs: `user_data/logs/test_trades.log`
2. Verify OpenAlgo: `curl http://127.0.0.1:5000`
3. Check symbol mapping: Look for "Fetched X candles" in logs
4. Review config.json for correct settings

---

**Happy Testing! 🚀**

Remember: Start with dry-run, verify everything works, then enable live trading!
