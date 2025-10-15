# Analytics UI - PaperBroker Backtest Dashboard

## ✅ What's Been Implemented

A **beautiful, interactive analytics dashboard** that provides backtest-style metrics for your PaperBroker live trading!

---

## 🎯 Features

### **📊 Real-Time Metrics**
- Total trades (open + closed)
- Win rate percentage
- Total profit/loss
- Average profit per trade
- Average trade duration
- Current balance

### **📈 Visual Charts**
1. **Equity Curve** - Cumulative profit over time
2. **Daily Profit** - Bar chart of daily P&L

### **📋 Trade Table**
- Recent trades with full details
- Profit/loss color coding
- Open/Closed status badges
- Sortable columns

### **🔄 Auto-Refresh**
- Updates every 30 seconds
- Manual refresh button

---

## 🚀 How to Access

### **Method 1: Standalone HTML (Recommended)**

Simply open the HTML file in your browser:

```bash
# Using Python's built-in HTTP server
cd /home/tushka/Projects/freqtrade
python3 -m http.server 8081
```

Then open in browser:
```
http://localhost:8081/analytics_ui.html
```

**Login with your Freqtrade credentials:**
- Username: `admin` (or your configured username)
- Password: `admin123` (or your configured password)

---

### **Method 2: Direct API Access**

The analytics API is available at:

```
GET http://127.0.0.1:8080/api/v1/analytics/overview
GET http://127.0.0.1:8080/api/v1/analytics/trades?limit=100
```

**Authentication Required:**
- Use JWT token from login
- Or HTTP Basic Auth

---

## 📋 API Endpoints

### **1. Analytics Overview**

```bash
curl -X GET "http://127.0.0.1:8080/api/v1/analytics/overview" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "total_trades": 10,
  "open_trades": 2,
  "closed_trades": 8,
  "winning_trades": 5,
  "losing_trades": 3,
  "total_profit": 1250.50,
  "total_profit_percent": 1.25,
  "win_rate": 62.5,
  "avg_profit": 156.31,
  "avg_profit_winning": 350.20,
  "avg_profit_losing": -125.45,
  "avg_duration": 45.5,
  "best_trade": {
    "pair": "BANK/INR",
    "profit": 580.25,
    "profit_percent": 2.15
  },
  "worst_trade": {
    "pair": "RELIANCE/INR",
    "profit": -245.50,
    "profit_percent": -0.98
  },
  "equity_curve": [
    {"date": "2025-10-15T10:30:00", "profit": 120.50, "trade_id": 1},
    {"date": "2025-10-15T11:45:00", "profit": 250.75, "trade_id": 2}
  ],
  "daily_profit": [
    {"date": "2025-10-15", "profit": 450.25}
  ],
  "max_win_streak": 3,
  "max_loss_streak": 2,
  "current_balance": 101250.50
}
```

### **2. Trade List**

```bash
curl -X GET "http://127.0.0.1:8080/api/v1/analytics/trades?limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
[
  {
    "id": 1,
    "pair": "BANK/INR",
    "is_open": false,
    "open_date": "2025-10-15T10:30:00",
    "open_rate": 45250.50,
    "close_date": "2025-10-15T11:45:00",
    "close_rate": 45380.25,
    "amount": 0.5,
    "stake_amount": 22625.25,
    "profit_abs": 64.87,
    "profit_percent": 0.29,
    "duration": 75,
    "enter_tag": "rsi_oversold",
    "exit_reason": "roi"
  }
]
```

---

## 💡 Dashboard Features

### **Color-Coded Stats**
- 🟢 **Green**: Profitable trades/metrics
- 🔴 **Red**: Loss-making trades/metrics
- 🔵 **Blue**: Neutral metrics

### **Interactive Charts**
- Hover over data points for details
- Responsive design
- Beautiful gradients

### **Trade Table**
- ✅ **Closed** - Green badge
- 🔵 **Open** - Blue badge
- Color-coded profit/loss

---

## 🔧 Configuration

### **API Authentication**

Edit `analytics_ui.html` to automatically login:

```javascript
function getAuthToken() {
    // Option 1: Use stored token
    return localStorage.getItem('access_token');
    
    // Option 2: Use basic auth (not recommended for production)
    const username = 'admin';
    const password = 'admin123';
    return btoa(`${username}:${password}`);
}
```

### **Auto-Refresh Interval**

Change refresh rate (default: 30 seconds):

```javascript
// At bottom of analytics_ui.html
setInterval(loadAnalytics, 30000); // 30 seconds
```

---

## 📊 Screenshots

### Dashboard Layout:
```
┌──────────────────────────────────────────────────┐
│  🎯 PaperBroker Analytics Dashboard   🔄 Refresh │
│  Real-time trading performance metrics           │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐       │
│  │Total │  │Win   │  │Total │  │Avg   │       │
│  │Trades│  │Rate  │  │Profit│  │Profit│       │
│  │  10  │  │ 62.5%│  │₹1250 │  │₹156  │       │
│  └──────┘  └──────┘  └──────┘  └──────┘       │
│                                                  │
├──────────────────────────────────────────────────┤
│  📈 Equity Curve                                 │
│  ┌────────────────────────────────────────────┐ │
│  │                                   /        │ │
│  │                          /\      /         │ │
│  │                 /\      /  \    /          │ │
│  │        /\      /  \    /    \  /           │ │
│  │  /\   /  \    /    \  /      \/            │ │
│  │ /  \_/    \__/      \/                     │ │
│  └────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────┤
│  💰 Daily Profit                                 │
│  ┌────────────────────────────────────────────┐ │
│  │     ▄▄▄  ▄▄   ▄   ▄▄                      │ │
│  │     ███  ██   █   ██                      │ │
│  │     ███  ██   █   ██                      │ │
│  └────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────┤
│  📊 Recent Trades                                │
│  ┌────┬──────────┬────────┬─────────┬────────┐ │
│  │ID  │Pair      │Status  │Profit ₹ │Profit %│ │
│  ├────┼──────────┼────────┼─────────┼────────┤ │
│  │ 1  │BANK/INR  │CLOSED  │ +₹64.87 │ +0.29% │ │
│  │ 2  │TCS/INR   │OPEN    │   --    │   --   │ │
│  └────┴──────────┴────────┴─────────┴────────┘ │
└──────────────────────────────────────────────────┘
```

---

## 🎯 Use Cases

### **1. Strategy Testing**
- Monitor win rate in real-time
- See if strategy is profitable
- Identify best/worst performing pairs

### **2. Performance Analysis**
- Track equity curve growth
- Analyze daily profit patterns
- Calculate average trade duration

### **3. Risk Management**
- Monitor max loss streak
- Track current balance
- Identify losing patterns

---

## 🚨 Troubleshooting

### **Issue: "Error loading analytics"**
**Solution:**
1. Make sure bot is running: `./freqtrade.sh status`
2. Check API is accessible: `curl http://127.0.0.1:8080/api/v1/ping`
3. Verify credentials are correct

### **Issue: "Cross-Origin Request Blocked"**
**Solution:**
Serve the HTML file through a web server (Method 1 above), don't open it directly as `file://`

### **Issue: Charts not displaying**
**Solution:**
1. Check browser console for errors
2. Ensure internet connection (for Chart.js CDN)
3. Try refreshing the page

---

## 📝 Quick Start

```bash
# 1. Start bot
cd /home/tushka/Projects/freqtrade
./freqtrade.sh run

# 2. Start HTTP server for UI
python3 -m http.server 8081

# 3. Open browser
http://localhost:8081/analytics_ui.html

# 4. Login with credentials
Username: admin
Password: admin123

# 5. View analytics!
```

---

## 🎉 Benefits

✅ **Real-Time Monitoring** - See performance as trades execute  
✅ **Backtest-Style Metrics** - Same metrics as historical backtesting  
✅ **Visual Analysis** - Charts make patterns obvious  
✅ **No Setup Required** - Just open the HTML file  
✅ **Auto-Refresh** - Always up-to-date  
✅ **Mobile Friendly** - Responsive design  

---

## 📚 Technical Details

**Built With:**
- FastAPI (Backend API)
- Chart.js (Charts)
- Vanilla JavaScript (Frontend)
- HTML5 + CSS3 (UI)

**API Routes:**
- `/api/v1/analytics/overview` - Comprehensive metrics
- `/api/v1/analytics/trades` - Trade list

**Authentication:**
- JWT token (recommended)
- HTTP Basic Auth (fallback)

---

**Enjoy your analytics dashboard!** 📈✨
