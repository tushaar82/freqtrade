# Complete NSE Trading Guide for Freqtrade

A comprehensive guide to trading NSE (National Stock Exchange) using Freqtrade with multiple exchange options.

## Overview

Freqtrade now supports NSE trading through three different exchange integrations:

1. **OpenAlgo** - Self-hosted, multi-broker platform
2. **Smart API** - Angel One's official trading API
3. **Paper Broker** - Virtual trading for testing

Each option suits different needs and use cases.

## Exchange Comparison

| Feature | OpenAlgo | Smart API | Paper Broker |
|---------|----------|-----------|--------------|
| **Real Trading** | ✅ Yes | ✅ Yes | ❌ No (Virtual) |
| **Broker Support** | Multiple | Angel One only | N/A |
| **Setup Complexity** | Medium | Easy | Very Easy |
| **API Keys** | API Key | API Key + TOTP | None required |
| **Cost** | Free (self-hosted) | Free | Free |
| **Data Quality** | Real-time | Real-time | Simulated |
| **Best For** | Multi-broker users | Angel One users | Testing/Learning |
| **NSE Support** | ✅ | ✅ | ✅ (Simulated) |
| **BSE Support** | ✅ | ✅ | ✅ (Simulated) |
| **MCX Support** | ✅ | ✅ | ✅ (Simulated) |

## Quick Start for Each Exchange

### OpenAlgo

**Best for**: Users with any Indian broker, prefer self-hosting

```bash
# 1. Install OpenAlgo
git clone https://github.com/marketcalls/openalgo
cd openalgo && python app.py

# 2. Get API key from OpenAlgo dashboard

# 3. Configure Freqtrade
cp config_examples/config_openalgo_nse.example.json config.json
# Edit config.json with your API key

# 4. Start trading
freqtrade trade --config config.json --strategy NSESampleStrategy
```

**Documentation**: `docs/openalgo-nse-integration.md`

### Smart API (Angel One)

**Best for**: Angel One account holders

```bash
# 1. Install dependencies
pip install smartapi-python pyotp

# 2. Get credentials from Angel One

# 3. Configure Freqtrade
cp config_examples/config_smartapi_nse.example.json config.json
# Edit with API key, client code, PIN, TOTP token

# 4. Start trading
freqtrade trade --config config.json --strategy NSESampleStrategy
```

**Documentation**: `docs/smartapi-integration.md`

### Paper Broker

**Best for**: Testing, learning, strategy development

```bash
# 1. Configure Freqtrade (no API keys needed!)
cp config_examples/config_paperbroker.example.json config.json

# 2. Start paper trading
freqtrade trade --config config.json --strategy NSESampleStrategy
```

**Documentation**: `docs/paperbroker-integration.md`

## Complete Setup Guide

### Step 1: Choose Your Exchange

#### Option A: OpenAlgo
- ✅ You have any Indian broker (Zerodha, Upstox, Fyers, etc.)
- ✅ You prefer self-hosting
- ✅ You want multi-broker support

#### Option B: Smart API
- ✅ You have an Angel One account
- ✅ You prefer cloud-based solution
- ✅ You want official broker integration

#### Option C: Paper Broker
- ✅ You're learning/testing
- ✅ You don't want to risk real money
- ✅ You're developing a new strategy

### Step 2: Installation

```bash
# Clone Freqtrade (if not already done)
git clone https://github.com/freqtrade/freqtrade.git
cd freqtrade

# Install dependencies
pip install -r requirements.txt

# For Smart API users
pip install smartapi-python pyotp
```

### Step 3: Configuration

#### For OpenAlgo:
```json
{
    "exchange": {
        "name": "openalgo",
        "key": "your_api_key",
        "urls": {"api": "http://127.0.0.1:5000"},
        "pair_whitelist": ["RELIANCE/INR", "TCS/INR"]
    }
}
```

#### For Smart API:
```json
{
    "exchange": {
        "name": "smartapi",
        "key": "your_api_key",
        "username": "client_code",
        "password": "pin",
        "totp_token": "totp_secret",
        "pair_whitelist": ["SBIN/INR", "RELIANCE/INR"]
    }
}
```

#### For Paper Broker:
```json
{
    "exchange": {
        "name": "paperbroker",
        "initial_balance": 100000,
        "pair_whitelist": ["RELIANCE/INR", "TCS/INR"]
    }
}
```

### Step 4: Strategy Selection

Use the included NSE sample strategy:

```bash
# View strategy
cat user_data/strategies/NSESampleStrategy.py

# Or create your own
cp user_data/strategies/NSESampleStrategy.py user_data/strategies/MyStrategy.py
```

### Step 5: Testing

#### Backtest First
```bash
# Download data
freqtrade download-data --config config.json --timerange 20240101-

# Backtest
freqtrade backtesting --config config.json --strategy NSESampleStrategy
```

#### Paper Trade (Recommended)
```bash
# Use Paper Broker first
freqtrade trade --config config_paperbroker.json --strategy NSESampleStrategy
```

#### Dry-Run with Real Exchange
```bash
# Set "dry_run": true in config
freqtrade trade --config config.json --strategy NSESampleStrategy
```

### Step 6: Live Trading

⚠️ **Only after thorough testing!**

```bash
# Set "dry_run": false in config
freqtrade trade --config config.json --strategy NSESampleStrategy
```

## NSE Trading Basics

### Market Hours (IST)

- **Pre-market**: 09:00 - 09:15
- **Regular Market**: 09:15 - 15:30
- **Post-market**: 15:40 - 16:00
- **Trading Days**: Monday - Friday

### Product Types

| Product | Full Name | Description | Auto Square-off |
|---------|-----------|-------------|-----------------|
| **MIS** | Margin Intraday | Intraday with margin | Before 15:20 |
| **CNC** | Cash and Carry | Delivery trading | No |
| **NRML** | Normal | F&O positions | No |

### Order Types

- **Market**: Execute at current price
- **Limit**: Execute at specified price or better
- **SL**: Stop loss order
- **SL-M**: Stop loss market order

### Symbol Format

All three exchanges use:
```
SYMBOL/INR
```

Examples:
- `RELIANCE/INR`
- `TCS/INR`
- `SBIN/INR`
- `INFY/INR`

## Sample Strategies

### 1. NSE Sample Strategy (Included)

**Location**: `user_data/strategies/NSESampleStrategy.py`

**Features**:
- RSI + EMA crossover
- Volume confirmation
- Market hours validation
- Auto-exit before market close
- Volatility-based position sizing

**Usage**:
```bash
freqtrade trade --config config.json --strategy NSESampleStrategy
```

### 2. Create Your Own

```python
from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta

class MyNSEStrategy(IStrategy):
    timeframe = '5m'
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict):
        # Your indicators
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict):
        # Your entry logic
        dataframe.loc[(dataframe['rsi'] < 30), 'enter_long'] = 1
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict):
        # Your exit logic
        dataframe.loc[(dataframe['rsi'] > 70), 'exit_long'] = 1
        return dataframe
```

## Best Practices

### 1. Start with Paper Broker

Always test risk-free first:
```bash
freqtrade trade --config config_paperbroker.json --strategy YourStrategy
```

### 2. Then Dry-Run

Test with real data, no execution:
```bash
# Set "dry_run": true
freqtrade trade --config config.json --strategy YourStrategy
```

### 3. Small Position Sizes

Start with minimal capital:
```json
{
    "stake_amount": 5000,  // Small amount
    "max_open_trades": 2   // Limited positions
}
```

### 4. Use Stop Losses

Always protect capital:
```python
stoploss = -0.03  # 3% stop loss
```

### 5. Monitor Closely

Watch initial trades carefully:
```bash
# Check status frequently
freqtrade status

# Monitor profit
freqtrade profit
```

### 6. Respect Market Hours

Avoid trading:
- First 15 minutes (09:15-09:30) - market stabilization
- Last 30 minutes (15:00-15:30) - exit existing MIS positions

### 7. Understand Product Types

- **MIS**: For intraday only
- **CNC**: For delivery/swing trading
- **Don't mix**: Use appropriate product type for your strategy

## Common Tasks

### Download Historical Data

```bash
# For any exchange
freqtrade download-data --config config.json --timerange 20240101-20241015

# Specific pairs
freqtrade download-data --config config.json --pairs RELIANCE/INR TCS/INR
```

### Backtesting

```bash
# Full backtest
freqtrade backtesting --config config.json --strategy YourStrategy --timerange 20240101-20241015

# With specific stake amount
freqtrade backtesting --config config.json --strategy YourStrategy --stake-amount 10000
```

### Live Trading

```bash
# Paper trading
freqtrade trade --config config_paperbroker.json --strategy YourStrategy

# Dry-run
freqtrade trade --config config.json --strategy YourStrategy  # dry_run: true

# Live trading
freqtrade trade --config config.json --strategy YourStrategy  # dry_run: false
```

### Monitoring

```bash
# Current status
freqtrade status

# Profit summary
freqtrade profit

# Show trades
freqtrade show_trades

# Detailed profit
freqtrade profit --show-pair
```

## Troubleshooting

### Common Issues

#### 1. Connection Error

**OpenAlgo**: Ensure server is running on port 5000
**Smart API**: Check credentials and TOTP token
**Paper Broker**: Should work without any setup

#### 2. Symbol Not Found

- Use exact NSE symbol names (uppercase)
- Format: `SYMBOL/INR`
- Verify symbol is tradable

#### 3. Order Rejected

- Check market hours
- Verify sufficient balance
- Check circuit limits
- Ensure correct product type

#### 4. Authentication Failed

**OpenAlgo**: Verify API key
**Smart API**: Check client code, PIN, TOTP token

### Debug Mode

Enable detailed logging:
```json
{
    "verbosity": 3,
    "logfile": "logs/freqtrade.log"
}
```

## Migration Between Exchanges

### OpenAlgo → Smart API

1. Export configuration
2. Get Smart API credentials
3. Update config with new exchange
4. Test in dry-run
5. Deploy

### Smart API → OpenAlgo

1. Install OpenAlgo
2. Configure broker in OpenAlgo
3. Get OpenAlgo API key
4. Update Freqtrade config
5. Test and deploy

### Any Exchange → Paper Broker

1. Copy config
2. Change exchange to "paperbroker"
3. Remove API keys
4. Start testing

## Advanced Topics

### Custom Indicators for NSE

```python
# In your strategy
def populate_indicators(self, dataframe: DataFrame, metadata: dict):
    # India VIX equivalent
    dataframe['volatility'] = ta.ATR(dataframe, timeperiod=14)
    
    # Volume analysis
    dataframe['volume_mean'] = dataframe['volume'].rolling(20).mean()
    
    # Gap analysis (for NSE)
    dataframe['gap'] = (dataframe['open'] - dataframe['close'].shift(1)) / dataframe['close'].shift(1)
    
    return dataframe
```

### NSE-Specific Risk Management

```python
def custom_stoploss(self, pair: str, trade, current_time, current_rate, current_profit, **kwargs):
    # Tighter stop loss for NSE volatility
    if current_profit < -0.02:
        return -0.025  # 2.5% stop loss
    
    # Trail stop loss in profit
    if current_profit > 0.02:
        return current_profit * 0.5  # Lock in 50% profit
    
    return self.stoploss
```

### Market Hours Management

```python
def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float,
                       time_in_force: str, current_time: datetime, **kwargs):
    # Avoid first 15 minutes
    if current_time.hour == 9 and current_time.minute < 30:
        return False
    
    # Avoid last 45 minutes for MIS
    if current_time.hour == 14 and current_time.minute >= 45:
        return False
    
    return True
```

## Resources

### Documentation

- **OpenAlgo**: `docs/openalgo-nse-integration.md`
- **Smart API**: `docs/smartapi-integration.md`
- **Paper Broker**: `docs/paperbroker-integration.md`

### Configuration Examples

- **OpenAlgo**: `config_examples/config_openalgo_nse.example.json`
- **Smart API**: `config_examples/config_smartapi_nse.example.json`
- **Paper Broker**: `config_examples/config_paperbroker.example.json`

### Sample Strategy

- **NSE Strategy**: `user_data/strategies/NSESampleStrategy.py`

### Quick Guides

- **OpenAlgo**: `OPENALGO_QUICKSTART.md`
- **Complete Summary**: `OPENALGO_INTEGRATION_SUMMARY.md`

## Support & Community

- **Freqtrade Docs**: [www.freqtrade.io](https://www.freqtrade.io)
- **OpenAlgo Docs**: [docs.openalgo.in](https://docs.openalgo.in)
- **Smart API Docs**: [smartapi.angelbroking.com/docs](https://smartapi.angelbroking.com/docs/)

## Disclaimer

⚠️ **Important**:

- Trading involves substantial risk of loss
- Past performance doesn't guarantee future results
- Start with paper trading
- Use small amounts initially
- Never invest more than you can afford to lose
- Understand all risks before trading
- Comply with local regulations
- This software is provided "as-is" without warranty

## Quick Decision Tree

```
Do you want to trade with real money?
├─ Yes
│  ├─ Do you have Angel One account?
│  │  ├─ Yes → Use Smart API
│  │  └─ No → Do you have another Indian broker?
│  │     ├─ Yes → Use OpenAlgo
│  │     └─ No → Get a broker account first
│  └─ Not yet
│     └─ Use Paper Broker for testing
```

## Summary

You now have three powerful options for NSE trading with Freqtrade:

1. **OpenAlgo** - Flexible, self-hosted, multi-broker
2. **Smart API** - Direct Angel One integration
3. **Paper Broker** - Risk-free testing and learning

All three are fully integrated, documented, and ready to use!

---

**Ready to trade NSE? Choose your exchange and start trading!** 🇮🇳🚀📈
