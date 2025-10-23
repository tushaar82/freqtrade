# Backtesting UI Guide

## Overview

Freqtrade includes a powerful **Web-based Backtesting UI** that allows you to:

- ✅ Run backtests directly from the browser
- ✅ View results in real-time
- ✅ Compare multiple strategies
- ✅ Analyze performance metrics
- ✅ Download backtest reports
- ✅ Manage backtest history

## Accessing the Backtesting UI

### 1. Start Freqtrade with Web UI

```bash
# Start with Paper Broker and UI
./run_paper.sh

# Or start any config with UI enabled
freqtrade trade --config config.json --strategy YourStrategy
```

### 2. Open Web UI

Navigate to: **http://localhost:8080**

Login credentials (from your config.json):
- **Username**: admin
- **Password**: admin123

### 3. Navigate to Backtest Tab

Click on **"Backtest"** in the left sidebar menu.

## Running a Backtest

### Step 1: Configure Backtest Parameters

In the Backtest UI, you'll see several configuration options:

#### Basic Settings

| Parameter | Description | Example |
|-----------|-------------|---------|
| **Strategy** | Strategy to backtest | `SampleStrategy` |
| **Timeframe** | Candle timeframe | `5m`, `15m`, `1h`, `1d` |
| **Timerange** | Date range to test | `20240101-20241231` |
| **Stake Amount** | Amount per trade | `10000` INR |
| **Max Open Trades** | Max concurrent trades | `5` |

#### Advanced Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| **Enable Protections** | Use strategy protections | `false` |
| **Dry Run Wallet** | Starting balance | `100000` INR |
| **Fee** | Trading fee percentage | `0.1%` |
| **Slippage** | Price slippage | `0.05%` |

### Step 2: Start Backtest

1. Click **"Start Backtest"** button
2. Monitor progress in real-time
3. Wait for completion (progress bar shows status)

### Step 3: View Results

Once complete, you'll see:

#### Performance Metrics

- **Total Profit**: Overall profit/loss
- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Ratio of gross profit to gross loss
- **Sharpe Ratio**: Risk-adjusted return
- **Max Drawdown**: Largest peak-to-trough decline
- **Total Trades**: Number of trades executed

#### Charts

- **Equity Curve**: Portfolio value over time
- **Daily Profit**: Profit/loss per day
- **Trade Distribution**: Win/loss distribution
- **Pair Performance**: Performance by trading pair

#### Trade List

- View all trades with entry/exit points
- Filter by profit/loss, pair, date
- Export to CSV

## Backtest History

### Viewing Past Backtests

1. Click **"Backtest History"** tab
2. See list of all previous backtests
3. Click on any backtest to view results

### Managing History

- **View**: Click on backtest to see full results
- **Delete**: Remove old backtests
- **Export**: Download results as JSON/CSV
- **Compare**: Compare multiple backtests side-by-side

## API Endpoints

The Backtesting UI uses these API endpoints:

### Start Backtest

```bash
POST /api/v1/backtest
Content-Type: application/json

{
  "strategy": "SampleStrategy",
  "timeframe": "5m",
  "timerange": "20240101-20241231",
  "stake_amount": "10000",
  "max_open_trades": 5,
  "enable_protections": false,
  "dry_run_wallet": 100000
}
```

### Get Backtest Status

```bash
GET /api/v1/backtest

Response:
{
  "status": "running",  // or "ended", "not_started", "error"
  "running": true,
  "progress": 0.45,
  "step": "backtesting",
  "trade_count": 123,
  "status_msg": "Backtest running"
}
```

### Get Backtest Results

```bash
GET /api/v1/backtest

Response (when complete):
{
  "status": "ended",
  "running": false,
  "progress": 1.0,
  "backtest_result": {
    "strategy": {
      "SampleStrategy": {
        "trades": [...],
        "results_per_pair": [...],
        "total_profit": 15234.56,
        "profit_mean": 152.34,
        "profit_total": 15234.56,
        "wins": 45,
        "losses": 23,
        "draws": 2
      }
    }
  }
}
```

### Get Backtest History

```bash
GET /api/v1/backtest/history

Response:
[
  {
    "filename": "backtest-2024-10-23_08-30-15",
    "strategy": "SampleStrategy",
    "run_id": "abc123",
    "backtest_start_time": 1729662015,
    "notes": "Test run with new parameters"
  }
]
```

### Delete Backtest

```bash
DELETE /api/v1/backtest

Response:
{
  "status": "reset",
  "running": false,
  "status_msg": "Backtest reset"
}
```

## Command Line Backtesting

You can also run backtests from the command line:

### Basic Backtest

```bash
freqtrade backtest \
  --config config.json \
  --strategy SampleStrategy \
  --timerange 20240101-20241231
```

### With Custom Parameters

```bash
freqtrade backtest \
  --config config.json \
  --strategy SampleStrategy \
  --timerange 20240101-20241231 \
  --stake-amount 10000 \
  --max-open-trades 5 \
  --timeframe 5m
```

### Export Results

```bash
freqtrade backtest \
  --config config.json \
  --strategy SampleStrategy \
  --timerange 20240101-20241231 \
  --export trades \
  --export-filename user_data/backtest_results/my_backtest.json
```

## Backtesting with NSE Data

### Using Paper Broker

Paper Broker can simulate NSE trading:

```json
{
  "exchange": {
    "name": "paperbroker",
    "nse_simulation": true,
    "simulate_holidays": true,
    "pair_whitelist": [
      "RELIANCE/INR",
      "TCS/INR",
      "NIFTY50/INR",
      "BANKNIFTY/INR"
    ]
  }
}
```

### Using Historical CSV Data

1. **Download NSE Data**:
   ```bash
   # Place CSV files in user_data/raw_data/
   # Format: SYMBOL_minute.csv or SYMBOL_1m.csv
   ```

2. **CSV Format**:
   ```csv
   datetime,open,high,low,close,volume
   2024-01-01 09:15:00,2500.00,2510.00,2495.00,2505.00,1000000
   2024-01-01 09:16:00,2505.00,2515.00,2500.00,2512.00,950000
   ```

3. **Run Backtest**:
   Paper Broker will automatically use CSV data if available.

## Optimization with Hyperopt

### Run Hyperopt from UI

1. Go to **"Hyperopt"** tab (if available)
2. Configure optimization parameters
3. Start optimization
4. View best parameters

### Command Line Hyperopt

```bash
freqtrade hyperopt \
  --config config.json \
  --hyperopt-loss SharpeHyperOptLoss \
  --strategy SampleStrategy \
  --timerange 20240101-20241231 \
  --epochs 100
```

## Best Practices

### 1. Data Quality

- ✅ Use sufficient historical data (at least 6 months)
- ✅ Ensure data covers different market conditions
- ✅ Check for data gaps and anomalies
- ✅ Use realistic slippage and fees

### 2. Timeframes

- **Short-term (1m-5m)**: Day trading, requires more data
- **Medium-term (15m-1h)**: Swing trading, balanced
- **Long-term (4h-1d)**: Position trading, less data needed

### 3. Avoiding Overfitting

- ❌ Don't optimize on the same data you test on
- ✅ Use train/test split (e.g., 70/30)
- ✅ Test on out-of-sample data
- ✅ Keep strategies simple
- ✅ Use walk-forward analysis

### 4. Realistic Parameters

```json
{
  "exchange": {
    "slippage_percent": 0.05,      // 0.05% slippage
    "commission_percent": 0.03,    // 0.03% commission
    "fill_probability": 0.98       // 98% fill rate
  }
}
```

### 5. Risk Management

- Set realistic `max_open_trades`
- Use proper `stake_amount`
- Enable protections (cooldown, max drawdown)
- Test different market conditions

## Interpreting Results

### Key Metrics Explained

#### Profit Metrics

- **Total Profit**: Absolute profit in INR
- **Profit %**: Percentage return on investment
- **Avg Profit per Trade**: Mean profit per trade
- **Profit Factor**: Gross profit / Gross loss (>1.5 is good)

#### Risk Metrics

- **Max Drawdown**: Largest decline from peak (lower is better)
- **Max Drawdown %**: Drawdown as percentage
- **Sharpe Ratio**: Risk-adjusted return (>1 is good, >2 is excellent)
- **Sortino Ratio**: Like Sharpe but only considers downside risk

#### Trade Metrics

- **Win Rate**: % of profitable trades (>50% is good)
- **Best/Worst Trade**: Largest single profit/loss
- **Avg Trade Duration**: How long trades are held
- **Trades per Day**: Trading frequency

### What Makes a Good Strategy?

✅ **Profit Factor > 1.5**: More profit than loss  
✅ **Win Rate > 50%**: More wins than losses  
✅ **Sharpe Ratio > 1**: Good risk-adjusted returns  
✅ **Max Drawdown < 20%**: Controlled risk  
✅ **Consistent Returns**: Profit across different periods  

## Troubleshooting

### Backtest Not Starting

1. Check if another backtest is running
2. Verify strategy file exists
3. Check logs for errors
4. Ensure data is available for timerange

### No Trades Generated

1. Check strategy entry/exit conditions
2. Verify data quality
3. Adjust timeframe
4. Check pair whitelist

### Poor Results

1. Review strategy logic
2. Check for overfitting
3. Test different timeframes
4. Adjust risk parameters
5. Use more historical data

### API Errors

1. Check if API server is running
2. Verify authentication
3. Check network connectivity
4. Review server logs

## Advanced Features

### Custom Backtest Plots

Add custom plots to your strategy:

```python
def plot_config(self):
    return {
        'main_plot': {
            'ema_short': {'color': 'blue'},
            'ema_long': {'color': 'red'}
        },
        'subplots': {
            "RSI": {
                'rsi': {'color': 'purple'}
            }
        }
    }
```

### Multiple Strategy Comparison

Compare multiple strategies in one backtest:

```bash
freqtrade backtest \
  --config config.json \
  --strategy-list Strategy1 Strategy2 Strategy3 \
  --timerange 20240101-20241231
```

### Detailed Trade Analysis

Export detailed trade data:

```bash
freqtrade backtest \
  --config config.json \
  --strategy SampleStrategy \
  --export trades \
  --export-filename user_data/backtest_results/detailed_trades.json
```

## Integration with Paper Broker

Paper Broker provides realistic NSE simulation:

```json
{
  "exchange": {
    "name": "paperbroker",
    "initial_balance": 100000,
    "nse_simulation": true,
    "simulate_holidays": true,
    "market_hours": {
      "open": "09:15",
      "close": "15:30"
    }
  }
}
```

Features:
- ✅ NSE market hours simulation
- ✅ Holiday calendar
- ✅ Realistic slippage
- ✅ Order fill probability
- ✅ Commission simulation

## Resources

- [Freqtrade Backtesting Docs](https://www.freqtrade.io/en/stable/backtesting/)
- [Strategy Optimization](https://www.freqtrade.io/en/stable/hyperopt/)
- [Performance Metrics](https://www.freqtrade.io/en/stable/strategy-analysis/)

## Quick Reference

### Common Timeranges

```bash
# Last 30 days
--timerange 20241001-20241031

# Last 3 months
--timerange 20240801-20241031

# Last year
--timerange 20230101-20231231

# Specific period
--timerange 20240615-20240915
```

### Common Commands

```bash
# Basic backtest
freqtrade backtest --config config.json --strategy MyStrategy

# With timerange
freqtrade backtest -c config.json -s MyStrategy --timerange 20240101-

# Export results
freqtrade backtest -c config.json -s MyStrategy --export trades

# Multiple strategies
freqtrade backtest -c config.json --strategy-list Strat1 Strat2 Strat3

# With custom parameters
freqtrade backtest -c config.json -s MyStrategy --stake-amount 5000 --max-open-trades 3
```

---

**Happy Backtesting! 📊**
