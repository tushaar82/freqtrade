# PnL Display Fix - Status

## Changes Made

### 1. Added `amount_to_precision()` Method
```python
def amount_to_precision(self, pair: str, amount: float) -> float:
    """
    Override to ensure amount is always an integer for NSE.
    Called by Freqtrade when storing trade amounts.
    """
    fixed_qty = self._config.get('exchange', {}).get('fixed_quantity')
    if fixed_qty and fixed_qty > 0:
        return float(fixed_qty)
    else:
        return float(max(1, int(round(amount))))
```

### 2. Enhanced `get_valid_pair_amount()` with Logging
```python
def get_valid_pair_amount(self, pair: str, amount: float, price: float) -> float:
    """
    Override amount calculation for NSE.
    Returns integer quantity based on fixed_quantity config.
    """
    fixed_qty = self._config.get('exchange', {}).get('fixed_quantity')
    if fixed_qty and fixed_qty > 0:
        result = float(fixed_qty)
        logger.info(f"get_valid_pair_amount: returning {result}")
        return result
    ...
```

### 3. Order Response Enhancements
- Set `filled` = quantity immediately for market orders
- Set `amount` = quantity explicitly
- Set `cost` = quantity × price
- Added logging for verification

---

## How to Test

### Option 1: Wait for Natural Signal
```bash
# Monitor logs
tail -f /tmp/ft_amount_fix.log | grep -E "(ORDER CALCULATION|get_valid_pair_amount|Amount)"
```

### Option 2: Force a Trade (Recommended)
```bash
# Force buy a specific pair
./force_test_trade.sh
```

This will:
1. Place an immediate buy order
2. Show amount calculation in logs
3. Create trade in database
4. Display in FreqUI

---

## Verification Steps

### 1. Check Logs
```bash
grep "get_valid_pair_amount" /tmp/ft_amount_fix.log
```

Should show:
```
get_valid_pair_amount called for RELIANCE/INR: returning fixed quantity 3.0
```

### 2. Check Database
```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect("tradesv3.sqlite")
cursor = conn.cursor()
cursor.execute("SELECT id, pair, amount, stake_amount FROM trades WHERE is_open = 1 ORDER BY id DESC LIMIT 1")
trade = cursor.fetchone()
if trade:
    trade_id, pair, amount, stake = trade
    print(f"Latest Trade:")
    print(f"  ID: {trade_id}")
    print(f"  Pair: {pair}")
    print(f"  Amount: {amount}")
    print(f"  Stake: ₹{stake:.2f}")
    if amount > 0:
        print(f"  ✅ Amount is correct!")
    else:
        print(f"  ❌ Amount is still 0")
conn.close()
EOF
```

### 3. Check FreqUI
- Go to http://localhost:8080
- Look at open trades
- Amount should show 3.00 (not 0)
- PnL should calculate correctly

### 4. Check OpenAlgo
- Go to http://127.0.0.1:5000
- Verify order has quantity=3
- Should match FreqUI

---

## Expected Results

### In Logs:
```
============================================================
ORDER CALCULATION for RELIANCE/INR:
  Input amount from Freqtrade: 3.0
  Price/Rate: 1500.50
  Fixed quantity config: 3
  FINAL QUANTITY TO ORDER: 3 shares
  Order value: ₹4501.50
============================================================
get_valid_pair_amount called for RELIANCE/INR: returning fixed quantity 3.0
✓ Order created: 25102300000035
  Amount in order response: 3.0
  Filled: 3.0
```

### In Database:
```sql
SELECT * FROM trades WHERE id = (SELECT MAX(id) FROM trades);

id: 10
pair: RELIANCE/INR
amount: 3.0          ← Should be 3.0, not 0!
stake_amount: 4501.50
open_rate: 1500.50
is_open: 1
```

### In FreqUI:
```
Open Trades:
  Pair: RELIANCE/INR
  Amount: 3.00       ← Should show 3.00
  Stake: 4501.50
  Open Rate: 1500.50
  Current Rate: 1505.25
  Current Profit: +0.32% (+14.25 INR)  ← PnL calculates!
```

### In OpenAlgo:
```
Order ID: 25102300000035
Symbol: RELIANCE
Quantity: 3        ← Matches FreqUI
Status: COMPLETE
```

---

## If Amount Still Shows 0

### Possible Causes:

1. **Method Not Being Called**
   - Check logs for "get_valid_pair_amount"
   - If not present, Freqtrade isn't calling it

2. **Freqtrade Core Override**
   - Freqtrade might recalculate after our method
   - May need to patch freqtradebot.py directly

3. **Timing Issue**
   - Amount might be set later (after order fills)
   - Check after a few seconds

### Debug Commands:

```bash
# Watch for method calls
tail -f /tmp/ft_amount_fix.log | grep "get_valid_pair_amount"

# Check what Freqtrade receives
tail -f /tmp/ft_amount_fix.log | grep "Amount in order response"

# Monitor database changes
watch -n 2 'python3 -c "import sqlite3; conn=sqlite3.connect(\"tradesv3.sqlite\"); cursor=conn.cursor(); cursor.execute(\"SELECT id, pair, amount FROM trades WHERE is_open=1\"); print(cursor.fetchall())"'
```

---

## Alternative Solution

If amount still shows 0 after all fixes, we can:

### Option A: Patch Freqtrade Core
Modify `freqtrade/freqtradebot.py` to use amount from order response directly.

### Option B: Post-Process Database
Add a script that runs periodically to fix amounts:

```python
# fix_amounts.py
import sqlite3
conn = sqlite3.connect("tradesv3.sqlite")
cursor = conn.cursor()

# Update trades with amount=0 to use stake/price
cursor.execute("""
    UPDATE trades 
    SET amount = ROUND(stake_amount / open_rate)
    WHERE is_open = 1 AND amount = 0
""")

conn.commit()
print(f"Fixed {cursor.rowcount} trades")
conn.close()
```

Run every minute:
```bash
watch -n 60 python3 fix_amounts.py
```

### Option C: Accept OpenAlgo as Source of Truth
- FreqUI shows amount=0 (display issue)
- OpenAlgo has correct quantity=3
- Use OpenAlgo for PnL tracking
- FreqUI for strategy monitoring only

---

## Current Status

✅ Methods added to OpenAlgo exchange
✅ Logging enhanced
✅ Order response sets amount correctly
✅ Freqtrade restarted with fixes
⏳ Waiting for trade to test

---

## Next Steps

1. **Force a test trade:**
   ```bash
   ./force_test_trade.sh
   ```

2. **Verify amount in database**

3. **Check PnL in FreqUI**

4. **If still 0, implement Alternative Solution B**

---

## Files Modified

1. `freqtrade/exchange/openalgo.py`
   - Added `amount_to_precision()`
   - Enhanced `get_valid_pair_amount()`
   - Enhanced order response

2. `force_test_trade.sh`
   - Script to force a trade for testing

---

**The fixes are in place. Test with `./force_test_trade.sh` to verify!**

