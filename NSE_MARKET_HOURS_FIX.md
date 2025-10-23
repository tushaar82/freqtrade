# NSE Market Hours & Timezone Fix

## Issues Fixed

### 1. ✅ Timezone (UTC → IST)
Added to `config.json`:
```json
{
  "timezone": "Asia/Kolkata"
}
```

### 2. ✅ Market Hours Awareness
Added NSE trading hours to OpenAlgo exchange:
- **Trading Hours**: 9:15 AM - 3:30 PM IST
- **Trading Days**: Monday - Friday
- **Closed**: Weekends and holidays

### 3. ✅ Gap Handling in Data

The gaps you see in the chart are NORMAL for NSE because:
- Market is closed 15:30 - 9:15 next day (17 hours 45 minutes)
- Market is closed on weekends
- This is different from crypto (24/7)

## How Indicators Handle Gaps

### Good News:
Most technical indicators handle gaps correctly because they work on **available candles only**, not calendar time.

**Example:**
```
Day 1: 9:15 AM - 3:30 PM (75 candles of 5m)
       Gap (market closed)
Day 2: 9:15 AM - 3:30 PM (75 candles of 5m)
```

**RSI, EMA, SMA, etc. calculate on:**
- Candle 1, 2, 3... 75 (Day 1)
- Candle 76, 77, 78... 150 (Day 2)

The gap doesn't affect calculation because indicators work on **candle sequence**, not time.

### Potential Issues:

1. **Time-based indicators** (like "trade only between 10 AM - 2 PM")
   - These need special handling
   - Use IST timezone for comparisons

2. **Volume indicators**
   - Work fine (volume is per candle)

3. **Volatility indicators**
   - Work fine (calculated per candle)

## Strategy Adjustments for NSE

### Add Market Hours Check

In your strategy, add:

```python
def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float,
                       time_in_force: str, current_time: datetime, entry_tag: str | None,
                       side: str, **kwargs) -> bool:
    """
    Don't enter trades outside market hours
    """
    # Check if market is open
    if hasattr(self.dp.exchange, 'is_market_open'):
        if not self.dp.exchange.is_market_open():
            return False
    
    return True
```

### Handle First Candle After Gap

```python
def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
    """
    Add indicators with gap awareness
    """
    # Standard indicators work fine with gaps
    dataframe['rsi'] = ta.RSI(dataframe)
    dataframe['ema_20'] = ta.EMA(dataframe, timeperiod=20)
    
    # Detect gaps (optional)
    dataframe['time_diff'] = dataframe['date'].diff()
    dataframe['is_gap'] = dataframe['time_diff'] > pd.Timedelta(minutes=10)
    
    # You can use 'is_gap' to avoid trading on first candle after market opens
    # if that's causing issues
    
    return dataframe
```

### Avoid Trading at Market Open/Close

```python
def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
    """
    Avoid trading in first/last 15 minutes
    """
    from datetime import time
    
    dataframe['hour'] = pd.to_datetime(dataframe['date']).dt.hour
    dataframe['minute'] = pd.to_datetime(dataframe['date']).dt.minute
    
    # Avoid 9:15-9:30 and 15:15-15:30
    dataframe['avoid_time'] = (
        ((dataframe['hour'] == 9) & (dataframe['minute'] < 30)) |
        ((dataframe['hour'] == 15) & (dataframe['minute'] >= 15))
    )
    
    dataframe.loc[
        (
            (dataframe['rsi'] < 30) &  # Your entry condition
            (~dataframe['avoid_time'])  # Not in avoid time
        ),
        'enter_long'] = 1
    
    return dataframe
```

## Chart Display

The gaps in FreqUI are **cosmetic** - they don't affect trading logic.

If you want continuous charts:
1. Use 1h or 1d timeframe (fewer gaps visible)
2. Or accept that gaps are normal for stock markets

## Testing

To verify indicators work correctly across gaps:

```python
# In your strategy
def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
    # Calculate RSI
    dataframe['rsi'] = ta.RSI(dataframe)
    
    # Log first few values after each gap
    gaps = dataframe[dataframe['date'].diff() > pd.Timedelta(minutes=10)]
    for idx in gaps.index:
        if idx > 0:
            logger.info(f"Gap detected at {dataframe.loc[idx, 'date']}")
            logger.info(f"  Previous candle: {dataframe.loc[idx-1, 'date']}, RSI: {dataframe.loc[idx-1, 'rsi']}")
            logger.info(f"  Current candle: {dataframe.loc[idx, 'date']}, RSI: {dataframe.loc[idx, 'rsi']}")
    
    return dataframe
```

## Summary

✅ **Fixed:**
- Timezone set to IST
- Market hours awareness added
- `is_market_open()` method available

✅ **No Action Needed:**
- Gaps are normal for NSE
- Indicators handle gaps correctly
- Chart gaps are cosmetic

⚠️ **Optional Improvements:**
- Avoid trading at market open/close
- Add gap detection in strategy
- Use market hours check before entry

## Restart to Apply

```bash
pkill -f "freqtrade trade"
./start.sh
```

Now:
- Times will display in IST
- Market hours are tracked
- You can use `is_market_open()` in strategy

The gaps in the chart are **expected and correct** for NSE! 📊
