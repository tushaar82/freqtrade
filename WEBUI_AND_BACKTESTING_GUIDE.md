# Freqtrade WebUI and Backtesting Guide for Indian NSE Trading

Complete guide for using Freqtrade's WebUI, backtesting, and API for Android app development.

## Table of Contents

1. [WebUI Setup](#webui-setup)
2. [Backtesting](#backtesting)
3. [CSV Data Management](#csv-data-management)
4. [API Endpoints](#api-endpoints)
5. [Android App Integration](#android-app-integration)
6. [Paper Trading](#paper-trading)

---

## WebUI Setup

### Quick Start

```bash
# Start WebUI only (for backtesting/analysis)
./start.sh --webui

# Or start with trading bot + WebUI
./start.sh
```

Access:
- **WebUI**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **Login**: admin / admin123 (change in config)

### Configuration

Copy and edit the WebUI config:

```bash
cp config_examples/config_paper_nse_webui.example.json config.json
nano config.json
```

Key settings:

```json
{
  "api_server": {
    "enabled": true,
    "listen_ip_address": "0.0.0.0",
    "listen_port": 8080,
    "username": "admin",
    "password": "change-this-password",
    "jwt_secret_key": "change-this-secret-key",
    "CORS_origins": ["*"]
  }
}
```

**Security Notes:**
- Change default username/password
- Change JWT secret key
- For production, restrict CORS_origins

---

## Backtesting

### Method 1: Using CSV Data

#### 1. Upload CSV via WebUI

Format your CSV file:

```csv
datetime,open,high,low,close,volume
2024-01-01 09:15:00,2450.50,2455.75,2448.25,2453.00,125000
2024-01-01 09:16:00,2453.00,2458.50,2452.00,2456.25,135000
```

Upload via:
- WebUI: Settings → Data Management → Upload CSV
- API: `POST /api/v1/csv/upload`
- CLI: Place in `user_data/raw_data/`

#### 2. Run Backtest

```bash
# Via CLI
freqtrade backtesting \
  --config config.json \
  --strategy YourStrategy \
  --timerange 20240101-20240131

# Via WebUI
# Navigate to: Backtesting → Select Strategy → Run
```

### Method 2: Fetch Data from NSE Broker

#### Using API:

```bash
curl -X GET "http://localhost:8080/api/v1/data/fetch_from_broker?pair=RELIANCE/INR&broker=openalgo&timeframe=1m&days=30" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Using CLI:

```python
# Python script to fetch and save
from freqtrade.resolvers import ExchangeResolver
from datetime import datetime, timedelta
import pandas as pd

# Initialize broker
config = {...}  # Your broker config
exchange = ExchangeResolver.load_exchange(config)

# Fetch data
since = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
ohlcv = exchange.fetch_ohlcv('RELIANCE/INR', '1m', since=since)

# Save to CSV
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
df.to_csv('user_data/raw_data/RELIANCE_1m.csv', index=False)
```

### Method 3: Using Paper Broker with CSV Playback

The paper broker automatically loads CSV files from `user_data/raw_data/` and replays them for realistic testing.

```bash
# Place CSV files in user_data/raw_data/
# Start paper broker
./start.sh --config config_paper_nse_webui.example.json
```

---

## CSV Data Management

### File Format

**Required columns:**
- `datetime`: ISO format or Unix timestamp
- `open`: Opening price
- `high`: High price
- `low`: Low price
- `close`: Closing price
- `volume`: Trading volume

**Naming convention:**
- `SYMBOL_1m.csv` → Pairs to SYMBOL/INR
- `SYMBOL_5m.csv` → 5-minute candles
- Example: `RELIANCE_1m.csv`, `NIFTY50_5m.csv`

### API Endpoints

#### Upload CSV

```bash
curl -X POST "http://localhost:8080/api/v1/csv/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@RELIANCE_1m.csv" \
  -F "pair=RELIANCE/INR"
```

#### List CSV Files

```bash
curl -X GET "http://localhost:8080/api/v1/csv/list" \
  -H "Authorization: Bearer $TOKEN"
```

#### Delete CSV

```bash
curl -X DELETE "http://localhost:8080/api/v1/csv/RELIANCE_1m.csv" \
  -H "Authorization: Bearer $TOKEN"
```

---

## API Endpoints

### Authentication

```bash
# Login
curl -X POST "http://localhost:8080/api/v1/token/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Returns:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "bearer"
# }
```

### Core Endpoints

#### Bot Control

```bash
# Get status
GET /api/v1/status

# Start/Stop
POST /api/v1/start
POST /api/v1/stop

# Force entry
POST /api/v1/forcebuy
POST /api/v1/forcesell
```

#### Balance & Performance

```bash
# Get balance
GET /api/v1/balance

# Paper broker specific
GET /api/v1/paper/balance
POST /api/v1/paper/reset

# Get profit
GET /api/v1/profit

# Trade statistics
GET /api/v1/trades
GET /api/v1/trades/{trade_id}
```

#### Market Data

```bash
# Get ticker
GET /api/v1/ticker/{pair}

# Get OHLCV
GET /api/v1/pair_candles

# Get available pairs
GET /api/v1/available_pairs
```

#### NSE-Specific

```bash
# NSE Calendar
GET /api/v1/nse/calendar
POST /api/v1/nse/calendar/holiday

# Fetch from broker
GET /api/v1/data/fetch_from_broker?pair=RELIANCE/INR&broker=openalgo&days=30
```

#### Backtesting

```bash
# Run backtest
POST /api/v1/backtest
{
  "strategy": "YourStrategy",
  "timerange": "20240101-20240131",
  "max_open_trades": 5,
  "stake_amount": 10000
}

# Get backtest results
GET /api/v1/backtest

# Get backtest history
GET /api/v1/backtest/history
```

#### Analytics

```bash
# Get summary
GET /api/v1/analytics/summary

# Get performance
GET /api/v1/performance

# Get daily profit
GET /api/v1/daily
```

### Complete API Documentation

Visit: http://localhost:8080/docs

Interactive Swagger UI with all endpoints, parameters, and response models.

---

## Android App Integration

### Setup

1. **Base URL**: `http://YOUR_SERVER_IP:8080/api/v1`
2. **Authentication**: JWT Bearer Token
3. **CORS**: Enabled for all origins

### Example Android Code (Kotlin)

```kotlin
// Retrofit API Interface
interface FreqtradeAPI {
    @FormUrlEncoded
    @POST("token/login")
    suspend fun login(
        @Field("username") username: String,
        @Field("password") password: String
    ): LoginResponse
    
    @GET("status")
    suspend fun getStatus(
        @Header("Authorization") token: String
    ): StatusResponse
    
    @GET("balance")
    suspend fun getBalance(
        @Header("Authorization") token: String
    ): BalanceResponse
    
    @POST("csv/upload")
    @Multipart
    suspend fun uploadCSV(
        @Header("Authorization") token: String,
        @Part file: MultipartBody.Part,
        @Part("pair") pair: RequestBody
    ): UploadResponse
    
    @GET("trades")
    suspend fun getTrades(
        @Header("Authorization") token: String
    ): List<Trade>
}

// Usage
class FreqtradeRepository {
    private val api: FreqtradeAPI = // Initialize Retrofit
    
    suspend fun login(username: String, password: String): String {
        val response = api.login(username, password)
        return "Bearer ${response.access_token}"
    }
    
    suspend fun getBotStatus(token: String): Status {
        return api.getStatus(token)
    }
    
    suspend fun uploadCSVFile(token: String, file: File, pair: String) {
        val filePart = MultipartBody.Part.createFormData(
            "file",
            file.name,
            file.asRequestBody("text/csv".toMediaType())
        )
        val pairPart = pair.toRequestBody("text/plain".toMediaType())
        api.uploadCSV(token, filePart, pairPart)
    }
}
```

### Recommended Libraries

- **Retrofit**: HTTP client
- **Gson/Moshi**: JSON parsing
- **OkHttp**: HTTP interceptors, logging
- **Coroutines**: Async operations

---

## Paper Trading

### Features

- **Realistic Simulation**: Slippage, commission, fill probability
- **NSE Market Hours**: Respects trading calendar
- **CSV Playback**: Uses real historical data
- **No Risk**: 100% virtual money

### Configuration

```json
{
  "exchange": {
    "name": "paperbroker",
    "initial_balance": 100000,
    "slippage_percent": 0.05,
    "commission_percent": 0.03,
    "fill_probability": 0.98,
    "nse_simulation": true,
    "simulate_holidays": true,
    "pair_whitelist": [
      "RELIANCE/INR",
      "TCS/INR",
      "INFY/INR"
    ]
  }
}
```

### Usage

```bash
# Start paper trading
./start.sh --config config_paper_nse_webui.example.json

# Check balance
curl -X GET "http://localhost:8080/api/v1/paper/balance" \
  -H "Authorization: Bearer $TOKEN"

# Reset to initial state
curl -X POST "http://localhost:8080/api/v1/paper/reset" \
  -H "Authorization: Bearer $TOKEN"
```

### CSV Data Playback

Place CSV files in `user_data/raw_data/`:

```
user_data/raw_data/
├── RELIANCE_1m.csv
├── TCS_1m.csv
└── NIFTY50_5m.csv
```

Paper broker will:
1. Load all CSV files on startup
2. Use real historical prices
3. Simulate order execution
4. Track realistic P&L

---

## Testing the Complete System

Run comprehensive tests:

```bash
./test_system.sh
```

This tests:
- ✅ Paper broker functionality
- ✅ NSE calendar integration
- ✅ Rate limiting
- ✅ Lot size management
- ✅ API endpoints
- ✅ CSV upload/download
- ✅ WebUI accessibility
- ✅ Backtesting

---

## Troubleshooting

### WebUI Not Loading

```bash
# Check if server is running
curl http://localhost:8080/api/v1/ping

# Check logs
tail -f user_data/logs/freqtrade.log

# Restart server
./stop.sh
./start.sh --webui
```

### CSV Upload Fails

- Check CSV format (required columns)
- Verify file permissions
- Check `user_data/raw_data/` exists
- Review API logs

### Backtest No Data

- Ensure CSV files in `user_data/raw_data/`
- Check date range matches data
- Verify pair names match
- Use `--timerange` parameter

### API Authentication Fails

- Check username/password
- Verify JWT secret key
- Token may have expired (re-login)
- Check CORS settings

---

## Advanced Features

### Custom Indicators in Backtesting

```python
# In your strategy
def populate_indicators(self, dataframe, metadata):
    # Use NSE-specific data
    if metadata['pair'] in self._nse_stocks:
        dataframe['custom_indicator'] = ...
    return dataframe
```

### Webhook Integration

```json
{
  "webhook": {
    "enabled": true,
    "url": "http://your-android-app/webhook",
    "webhookbuy": {
      "value1": "Bought {pair}",
      "value2": "Price: {current_rate}"
    }
  }
}
```

### Multi-Pair Backtesting

```bash
freqtrade backtesting \
  --config config.json \
  --strategy YourStrategy \
  --timerange 20240101-20240131 \
  --export trades \
  --export-filename user_data/backtest_results/multi_pair.json
```

---

## Resources

- **Main Docs**: README_INDIAN_BROKERS.md
- **API Docs**: http://localhost:8080/docs
- **Freqtrade Docs**: https://www.freqtrade.io
- **GitHub**: https://github.com/freqtrade/freqtrade

---

## Support

For issues:
1. Run `./test_system.sh` for diagnostics
2. Check logs in `user_data/logs/`
3. Review API docs at `/docs`
4. Report issues with logs and config
