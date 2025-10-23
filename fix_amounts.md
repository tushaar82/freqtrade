# Fix for Amount = 0 Issue

## Problem
Trades show Amount: 0 in FreqUI because:
1. Freqtrade calculates: `amount = stake_amount / price`
2. For 5000 INR stake at 1500 INR price = 3.33 shares
3. But somewhere this is being stored as 0

## Solution

The issue is that we need to ensure Freqtrade uses integer quantities for NSE.

### Quick Test

1. **Check if orders are being placed:**
   ```bash
   # Start Freqtrade and watch for order placement
   ./start.sh 2>&1 | grep -E "(placeorder|Order calculation|quantity)"
   ```

2. **Check OpenAlgo dashboard:**
   - Go to http://127.0.0.1:5000
   - Check if orders appear with quantity > 0

### If Orders Show Quantity = 0 in OpenAlgo

The problem is in the `create_order` method. We need to ensure the quantity calculation happens BEFORE the amount is used.

### If Orders Show Proper Quantity in OpenAlgo

The problem is in how Freqtrade stores the trade. The order is placed correctly, but the trade record has the wrong amount.

## Immediate Fix

Add this to your strategy to force proper amounts:

```python
def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                       proposed_stake: float, min_stake: float | None, max_stake: float,
                       leverage: float, entry_tag: str | None, side: str,
                       **kwargs) -> float:
    # Calculate number of shares
    shares = int(proposed_stake / current_rate)
    # Return stake that gives us integer shares
    return shares * current_rate if shares > 0 else min_stake
```

This ensures Freqtrade calculates amounts that result in integer shares.

## Check Current Status

Run Freqtrade and check:
1. Console output for "Order calculation" messages
2. OpenAlgo dashboard for orders
3. FreqUI for trade amounts

The logs will show:
```
Order calculation for RELIANCE/INR:
  - Original amount: 3.33
  - Price/Rate: 1500.50
  - Final quantity: 3 shares
  - Order value: 4501.50 INR
```

If you see this, orders ARE being placed with correct quantities!

