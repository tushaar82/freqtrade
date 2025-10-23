# Fix: Quantity = 0 and Trades Not Closing

## Status
✅ Orders ARE being placed on OpenAlgo  
❌ FreqUI shows Amount = 0  
❌ Trades not closing automatically  

## Root Causes

### 1. Quantity = 0 Issue
**Problem**: Order is placed with correct quantity (3) to OpenAlgo, but Freqtrade stores the original fractional amount (0.003) in the database.

**Why**: Freqtrade calculates `amount = stake_amount / price` BEFORE calling create_order, and stores this fractional value in the trade record.

**Solution Applied**: Added `get_valid_pair_amount()` method to override amount calculation.

### 2. Trades Not Closing
**Problem**: AggressiveTestStrategy generates random BUY signals but may not be generating SELL signals properly.

**Why**: The strategy needs to:
1. Generate exit signals
2. Place sell orders on OpenAlgo
3. Wait for order fills
4. Close the trade

## Solutions

### Fix 1: Force Correct Amounts (Applied)

Added to `openalgo.py`:
```python
def get_valid_pair_amount(self, pair: str, amount: float, price: float) -> float:
    """Override amount calculation for NSE"""
    fixed_qty = self._config.get('exchange', {}).get('fixed_quantity')
    if fixed_qty and fixed_qty > 0:
        return float(fixed_qty)
    else:
        return float(max(1, int(round(amount))))
```

### Fix 2: Update Strategy for Better Exit Signals

The AggressiveTestStrategy needs to generate exit signals. Add this to your strategy:

```python
def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
    """
    Generate exit signals - more aggressive than entry
    """
    import random
    
    # Random exit with 30% probability (higher than 10% entry)
    dataframe['exit_long'] = dataframe.apply(
        lambda row: 1 if random.random() < 0.3 else 0, 
        axis=1
    )
    
    return dataframe
```

### Fix 3: Enable ROI-based Exits

In `config.json`, ensure you have:
```json
{
  "minimal_roi": {
    "0": 0.01  // Exit at 1% profit
  },
  "stoploss": -0.02,  // Exit at 2% loss
  "trailing_stop": false
}
```

This ensures trades close automatically at profit/loss targets.

### Fix 4: Check Order Status Updates

The issue might be that OpenAlgo orders are filled, but Freqtrade doesn't know. Ensure `fetch_order` is working:

```bash
# Check logs for order status updates
tail -f /tmp/ft_live.log | grep -E "(fetch_order|order status|filled)"
```

## Immediate Actions

### 1. Restart with Fixes
```bash
pkill -f "freqtrade trade"
./start.sh
```

### 2. Monitor New Trades
```bash
# Watch for order placement and fills
tail -f /tmp/ft_live.log | grep -E "(Order calculation|quantity|placeorder|filled|closed)"
```

### 3. Check OpenAlgo Dashboard
- Go to http://127.0.0.1:5000
- Verify orders show quantity = 3
- Check if orders are getting filled
- Check if SELL orders are being placed

### 4. Force Exit Old Trades (if needed)
In FreqUI:
- Go to Trade tab
- Click on each trade
- Click "Force Exit" button

Or use API:
```bash
# Get auth token from FreqUI (F12 > Application > Local Storage > jwt_token)
curl -X POST "http://localhost:8080/api/v1/forceexit" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tradeid": "all"}'
```

## Debugging

### Check if Quantity Fix Works
```bash
# Look for this in logs:
grep "Using fixed quantity from config" /tmp/ft_live.log
# Should show: "Using fixed quantity from config: 3 shares"

grep "Final quantity" /tmp/ft_live.log
# Should show: "Final quantity: 3 shares"
```

### Check Exit Signals
```bash
# Look for exit signals in logs:
grep -E "(exit_long|SELL|Exiting)" /tmp/ft_live.log
```

### Check Order Fills
```bash
# Look for order status updates:
grep -E "(filled|complete|closed)" /tmp/ft_live.log
```

## Expected Behavior

### When Working Correctly:

**1. Order Placement:**
```
Order calculation for RELIANCE/INR:
  - Original amount: 0.003
  - Price/Rate: 1500.50
  - Final quantity: 3 shares
  - Order value: 4501.50 INR
OpenAlgo request: POST .../placeorder
Order placed: orderid=25102300000020
```

**2. Trade in FreqUI:**
```
Pair: RELIANCE/INR
Amount: 3.00          ← Should be 3, not 0
Stake: 4501.50
Open Rate: 1500.50
Current Rate: 1505.25
PnL: +0.32%
```

**3. Exit Signal:**
```
Exit signal for RELIANCE/INR
Placing SELL order: 3 shares @ 1505.25
OpenAlgo request: POST .../placeorder (action=SELL)
Order placed: orderid=25102300000021
```

**4. Order Fill:**
```
Checking order status: 25102300000021
Order status: complete, filled: 3
Closing trade #1
Trade closed with profit: +14.25 INR
```

## Why Trades Might Not Close

### Possible Reasons:

1. **No Exit Signals**
   - Strategy not generating exit_long signals
   - Check: `populate_exit_trend` method

2. **ROI Not Reached**
   - Profit target not met
   - Check: `minimal_roi` in config

3. **Orders Not Filling**
   - OpenAlgo orders pending
   - Check: OpenAlgo dashboard

4. **Order Status Not Updating**
   - `fetch_order` not being called
   - Check: Logs for "fetch_order" calls

5. **Market Closed**
   - NSE closed, can't place sell orders
   - Check: Current time vs 9:15-15:30 IST

## Testing

### Test 1: Verify Quantity
1. Wait for new trade
2. Check FreqUI - Amount should be 3
3. Check OpenAlgo - Quantity should be 3

### Test 2: Force Exit
1. In FreqUI, click "Force Exit" on a trade
2. Should place SELL order on OpenAlgo
3. Trade should close

### Test 3: Automatic Exit
1. Wait for ROI target (1% profit)
2. Should automatically place SELL order
3. Trade should close

## Configuration Check

Verify your `config.json` has:
```json
{
  "exchange": {
    "name": "openalgo",
    "fixed_quantity": 3
  },
  "stake_amount": "unlimited",
  "minimal_roi": {
    "0": 0.01
  },
  "stoploss": -0.02,
  "dry_run": false
}
```

## Next Steps

1. ✅ Restart Freqtrade (fixes applied)
2. ⏳ Wait for new trade (should show Amount=3)
3. ⏳ Wait for exit signal or ROI
4. ⏳ Verify trade closes properly

If trades still show Amount=0 after restart, there may be a deeper issue with how Freqtrade stores trade amounts. We may need to patch the trade creation logic directly.

