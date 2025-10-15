# Paper Broker - Virtual Trading

Complete guide to using Paper Broker for risk-free strategy testing and development.

## Overview

Paper Broker is a virtual trading exchange built into Freqtrade that simulates real trading without using real money. It's perfect for:

- **Strategy Development**: Test strategies before going live
- **Learning**: Practice algorithmic trading risk-free
- **Backtesting Validation**: Compare paper trading with backtest results
- **Experimentation**: Try new ideas without financial risk
- **Education**: Learn Freqtrade without real money

## Key Features

✅ **No Real Money**: 100% simulated trading  
✅ **Realistic Simulation**: Includes slippage and commissions  
✅ **Configurable**: Adjust balance, fees, slippage  
✅ **No API Keys**: Works without any credentials  
✅ **Complete History**: Full trade tracking  
✅ **Easy Reset**: Start fresh anytime  

## Quick Start

### 1. Configuration

Create `config_paper.json`:

```json
{
    "stake_currency": "INR",
    "stake_amount": 10000,
    "dry_run": false,
    "exchange": {
        "name": "paperbroker",
        "initial_balance": 100000,
        "slippage_percent": 0.05,
        "commission_percent": 0.1,
        "pair_whitelist": [
            "RELIANCE/INR",
            "TCS/INR",
            "SBIN/INR"
        ]
    },
    "strategy": "NSESampleStrategy"
}
```

### 2. Start Trading

```bash
# Start paper trading (note: dry_run should be false)
freqtrade trade --config config_paper.json --strategy YourStrategy
```

That's it! No API keys, no broker account needed.

## Configuration Options

### Exchange Settings

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `name` | Exchange name | - | `"paperbroker"` |
| `initial_balance` | Starting balance | 100000 | `50000` |
| `slippage_percent` | Simulated slippage | 0.05% | `0.1` |
| `commission_percent` | Trading fees | 0.1% | `0.05` |
| `fill_probability` | Order fill chance | 0.95 | `1.0` |
| `proxy_exchange` | Real data source | null | `"binance"` |

### Example Configurations

#### Conservative Setup
```json
{
    "exchange": {
        "name": "paperbroker",
        "initial_balance": 100000,
        "slippage_percent": 0.1,
        "commission_percent": 0.15,
        "fill_probability": 0.90
    }
}
```

#### Aggressive Setup
```json
{
    "exchange": {
        "name": "paperbroker",
        "initial_balance": 500000,
        "slippage_percent": 0.03,
        "commission_percent": 0.05,
        "fill_probability": 0.98
    }
}
```

#### Zero-Fee Testing
```json
{
    "exchange": {
        "name": "paperbroker",
        "initial_balance": 100000,
        "slippage_percent": 0.0,
        "commission_percent": 0.0,
        "fill_probability": 1.0
    }
}
```

## How It Works

### Order Execution

1. **Order Placement**: You place an order like on a real exchange
2. **Price Simulation**: Paper Broker generates realistic prices
3. **Slippage Applied**: Configurable slippage added to execution
4. **Commission Calculated**: Trading fees deducted
5. **Balance Updated**: Virtual balance adjusted
6. **History Tracked**: Trade recorded

### Price Simulation

Paper Broker simulates prices using:
- **Random Walk**: Realistic price movements
- **Bid-Ask Spread**: Simulated market spread (0.1%)
- **Order Book**: Generated depth data
- **OHLCV Candles**: Historical-style data

### Realistic Features

- **Slippage**: Simulates market impact
- **Commission**: Realistic trading fees
- **Fill Probability**: Not all orders always fill
- **Market Hours**: Optional time restrictions
- **Balance Tracking**: Accurate P&L calculation

## Usage Examples

### Basic Strategy Testing

```bash
# Test strategy with paper broker
freqtrade trade --config config_paper.json --strategy MyStrategy

# Monitor progress
freqtrade status

# Check profit
freqtrade profit

# View trades
freqtrade show_trades
```

### Comparing with Backtest

```bash
# 1. Backtest first
freqtrade backtesting --config config.json --strategy MyStrategy --timerange 20240101-20240331

# 2. Paper trade same period
freqtrade trade --config config_paper.json --strategy MyStrategy

# 3. Compare results
```

### Strategy Development Workflow

```bash
# 1. Develop strategy
vim user_data/strategies/MyNewStrategy.py

# 2. Backtest
freqtrade backtesting --config config.json --strategy MyNewStrategy

# 3. Paper trade
freqtrade trade --config config_paper.json --strategy MyNewStrategy

# 4. Monitor for 1 week
# 5. Analyze results
# 6. Refine strategy
# 7. Repeat
```

## Advanced Features

### Using Proxy Exchange for Real Data

Get real market data while trading virtually:

```json
{
    "exchange": {
        "name": "paperbroker",
        "proxy_exchange": "binance",
        "pair_whitelist": [
            "BTC/USDT",
            "ETH/USDT"
        ]
    }
}
```

Paper Broker will:
- Use real prices from Binance
- Execute trades virtually
- Track positions with real market movements

### Resetting Paper Broker

Reset to start fresh:

```python
from freqtrade.exchange import Exchange

config = {'exchange': {'name': 'paperbroker'}}
exchange = Exchange(config)

# Reset to initial state
exchange.reset()
```

### Accessing Trade History

```python
# Get complete trade history
trade_history = exchange.get_trade_history()

for trade in trade_history:
    print(f"{trade['timestamp']}: {trade['side']} {trade['amount']} {trade['pair']} @ {trade['price']}")
```

### Viewing Positions

```python
# Get current positions
positions = exchange.get_positions()

for pair, position in positions.items():
    print(f"{pair}: {position['amount']} units, cost: {position['cost']}")
```

## Testing Scenarios

### 1. Strategy Validation

Test if strategy logic works:
```bash
freqtrade trade --config config_paper.json --strategy NewStrategy
```

### 2. Risk Management Testing

Test with limited balance:
```json
{
    "exchange": {
        "initial_balance": 10000,
        "max_open_trades": 2,
        "stake_amount": 3000
    }
}
```

### 3. High-Frequency Testing

Test scalping strategies:
```json
{
    "timeframe": "1m",
    "exchange": {
        "slippage_percent": 0.02,
        "commission_percent": 0.05
    }
}
```

### 4. Long-Term Testing

Test holding strategies:
```json
{
    "exchange": {
        "initial_balance": 1000000,
        "commission_percent": 0.1
    },
    "strategy": "LongTermHolding"
}
```

## Comparison with Dry-Run

| Feature | Paper Broker | Dry-Run |
|---------|--------------|---------|
| **Purpose** | Realistic simulation | Testing without execution |
| **Balance** | Virtual, tracked | Not tracked |
| **Commissions** | Simulated | No fees |
| **Slippage** | Configurable | No slippage |
| **Order Fills** | Probabilistic | Always filled |
| **Market Data** | Simulated or proxy | Real exchange |
| **Reset** | Can reset | No state to reset |
| **Best For** | Strategy validation | Logic testing |

**When to Use What**:
- **Dry-Run**: Testing strategy logic, syntax, API connectivity
- **Paper Broker**: Realistic trading simulation, performance validation

## Best Practices

### 1. Realistic Settings

Use realistic slippage and commissions:
```json
{
    "slippage_percent": 0.05,  // Typical for liquid stocks
    "commission_percent": 0.1   // Typical broker fees
}
```

### 2. Adequate Balance

Start with realistic capital:
```json
{
    "initial_balance": 100000,  // Realistic starting amount
    "stake_amount": 10000       // 10% per trade
}
```

### 3. Long Enough Testing

Run for sufficient time:
- **Minimum**: 1 week
- **Recommended**: 1 month
- **Ideal**: 3+ months

### 4. Compare with Backtest

Always compare paper trading with backtest:
```bash
# Backtest
freqtrade backtesting --config config.json --strategy MyStrategy

# Paper trade
freqtrade trade --config config_paper.json --strategy MyStrategy

# Compare metrics
```

### 5. Monitor Performance

Track key metrics:
- Win rate
- Average profit per trade
- Maximum drawdown
- Sharpe ratio
- Trade frequency

## Limitations

⚠️ **Important Limitations**:

1. **Not Real Trading**: Simulated execution may differ from real market
2. **Price Simulation**: Generated prices may not match real market exactly
3. **No Market Impact**: Large orders don't affect price
4. **Simplified Model**: Doesn't capture all market complexities
5. **No Broker Delays**: Instant execution (no queue times)

## Transition to Live Trading

### Before Going Live

✅ Checklist:
- [ ] Paper traded for at least 1 month
- [ ] Consistent profitability
- [ ] Acceptable drawdown levels
- [ ] Understand all trades
- [ ] Stress-tested strategy
- [ ] Risk management in place
- [ ] Emergency procedures defined

### Moving to Real Broker

1. **Start Small**: Use minimal capital initially
2. **Monitor Closely**: Watch first week carefully
3. **Compare**: Track differences from paper trading
4. **Adjust**: Refine based on real results
5. **Scale Gradually**: Increase capital slowly

## Use Cases

### 1. Learning Freqtrade

Perfect for beginners:
```bash
# Start learning with no risk
freqtrade trade --config config_paper.json --strategy SampleStrategy
```

### 2. Strategy Development

Iterate quickly:
```bash
# Test new strategy idea
freqtrade trade --config config_paper.json --strategy NewIdea

# Refine
# Test again
# Repeat
```

### 3. Parameter Optimization

Test different parameters:
```bash
# Test conservative params
freqtrade trade --config config_paper_conservative.json

# Test aggressive params
freqtrade trade --config config_paper_aggressive.json

# Compare results
```

### 4. Educational Workshops

Teach without risk:
```bash
# Students can practice trading
freqtrade trade --config config_paper.json --strategy LearningStrategy
```

## Troubleshooting

### Balance Not Updating

**Issue**: Virtual balance stays same

**Solution**: Ensure `dry_run: false` in config

### No Price Data

**Issue**: "Failed to fetch ticker"

**Solution**: Prices are simulated; ensure pairs are configured

### Orders Always Fill

**Issue**: Want more realistic fills

**Solution**: Adjust `fill_probability`:
```json
{
    "fill_probability": 0.85  // 85% fill rate
}
```

## Tips & Tricks

### Realistic Testing

Make it as real as possible:
```json
{
    "initial_balance": 50000,      // Your actual planned capital
    "commission_percent": 0.1,      // Your broker's actual fees
    "slippage_percent": 0.05,       // Realistic slippage
    "fill_probability": 0.95        // Realistic fill rate
}
```

### Fast Iteration

For quick testing:
```json
{
    "initial_balance": 1000000,     // Large balance
    "commission_percent": 0.0,       // No fees
    "fill_probability": 1.0          // Always fill
}
```

### Stress Testing

Test worst-case scenarios:
```json
{
    "initial_balance": 10000,       // Limited capital
    "slippage_percent": 0.2,        // High slippage
    "commission_percent": 0.3,       // High fees
    "fill_probability": 0.8          // Low fill rate
}
```

## Monitoring & Analysis

### Check Status

```bash
# Current status
freqtrade status

# Profit summary
freqtrade profit

# Trade list
freqtrade show_trades
```

### Export Data

```bash
# Export trades to CSV
freqtrade show_trades --print-json > trades.json

# Analyze in Python
import json
with open('trades.json') as f:
    trades = json.load(f)
```

### Performance Metrics

Track these metrics:
- **Total Profit**: Overall P&L
- **Win Rate**: % profitable trades
- **Avg Profit**: Mean profit per trade
- **Max Drawdown**: Largest peak-to-trough decline
- **Trade Frequency**: Trades per day/week

## Quick Commands Reference

```bash
# Start paper trading
freqtrade trade --config config_paper.json --strategy YourStrategy

# Check status
freqtrade status

# View profit
freqtrade profit

# Show trades
freqtrade show_trades

# Stop bot
Ctrl+C

# Restart (keeps history)
freqtrade trade --config config_paper.json --strategy YourStrategy
```

## Summary

Paper Broker is your risk-free playground for:
- 🎓 Learning Freqtrade
- 🔬 Testing strategies
- 📊 Validating backtests
- 🚀 Developing new ideas
- 🛡️ Risk-free experimentation

**Remember**: Paper trading success doesn't guarantee live trading success, but it's an essential step before risking real money!

---

**Happy Paper Trading! 📄💰**
