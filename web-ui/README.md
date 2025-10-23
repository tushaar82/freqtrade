# Freqtrade NSE - Professional Trading Frontend

A modern, production-ready Next.js frontend for the Freqtrade trading platform with comprehensive support for NSE (National Stock Exchange of India) F&O trading.

## Features

### Real-Time Trading Dashboard
- **Live P/L Analytics** with detailed performance metrics
- **Real-time price monitoring** with WebSocket integration
- **Trailing Stop Loss Visualization** on interactive charts
- **Position tracking** with unrealized P/L
- **Order book** depth visualization

### Advanced Analytics
- Cumulative profit tracking
- Trade distribution by pair
- Hourly performance heatmap
- Win rate and profit factor analysis
- Sharpe ratio and max drawdown metrics
- Daily trading activity charts

### Backtesting Suite
- **CSV data upload** for historical backtesting
- Strategy selection and configuration
- Equity curve visualization
- Detailed trade history analysis
- Performance metrics dashboard

### Professional Trader Interface
- Dark theme optimized for extended trading sessions
- Responsive design for desktop and mobile
- Live market status indicators
- NSE market calendar integration
- Bot control panel

## Technology Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **TanStack Query** - Server state management
- **Zustand** - Client state management
- **Lightweight Charts** - Professional charting library
- **Recharts** - Statistical charts and graphs
- **Socket.IO** - Real-time WebSocket communication
- **Axios** - HTTP client

## Prerequisites

- Node.js 18.x or higher
- npm or yarn package manager
- Freqtrade backend running on `http://localhost:8080`
- (Optional) OpenAlgo API running on `http://localhost:5000`

## Installation

### 1. Navigate to web-ui directory
```bash
cd web-ui
```

### 2. Install dependencies
```bash
npm install
# or
yarn install
```

### 3. Configure environment variables
```bash
cp .env.local.example .env.local
```

Edit `.env.local` to configure your API endpoints:
```env
NEXT_PUBLIC_FREQTRADE_API_URL=http://localhost:8080/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8080/ws
NEXT_PUBLIC_OPENALGO_API_URL=http://localhost:5000/api/v1
```

### 4. Run development server
```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Production Deployment

### Build for production
```bash
npm run build
# or
yarn build
```

### Start production server
```bash
npm run start
# or
yarn start
```

### Export as static site (optional)
```bash
npm run build
# The static files will be in the 'out' directory
```

## Project Structure

```
web-ui/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── dashboard/          # Dashboard pages
│   │   │   ├── analytics/      # Analytics page
│   │   │   ├── backtest/       # Backtesting interface
│   │   │   ├── positions/      # Positions monitoring
│   │   │   ├── settings/       # Settings and controls
│   │   │   ├── trading/        # Live trading charts
│   │   │   ├── layout.tsx      # Dashboard layout with sidebar
│   │   │   └── page.tsx        # Dashboard home with P/L
│   │   ├── login/              # Authentication
│   │   ├── globals.css         # Global styles
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Home redirect
│   │   └── providers.tsx       # React Query provider
│   ├── components/             # Reusable components
│   │   └── TradingChart.tsx    # Chart with trailing SL
│   ├── lib/                    # Utilities and clients
│   │   ├── api-client.ts       # API integration
│   │   └── websocket-client.ts # WebSocket integration
│   ├── store/                  # State management
│   │   ├── useAuthStore.ts     # Authentication state
│   │   └── useTradingStore.ts  # Trading state
│   └── types/                  # TypeScript definitions
│       └── index.ts            # All type definitions
├── public/                     # Static assets
├── .env.local.example          # Environment variables template
├── next.config.js              # Next.js configuration
├── tailwind.config.ts          # Tailwind CSS configuration
├── tsconfig.json               # TypeScript configuration
├── package.json                # Dependencies
└── README.md                   # This file
```

## Features Guide

### 1. Authentication
- Default credentials: `admin` / `admin123`
- JWT token authentication with auto-refresh
- Persistent login with localStorage

### 2. Dashboard Home
- **Live Balance** tracking
- **Unrealized P/L** for open positions
- **Win Rate** and trading statistics
- **Daily Profit Chart** with customizable timeframes
- **Active Positions Table** with real-time updates

### 3. Trading Page
- **Interactive Charts** with lightweight-charts
- **Trailing Stop Loss** visualization (orange dashed line)
- Entry price and stop loss indicators
- Order book depth display
- Multiple timeframe support (1m, 5m, 15m, 1h, 4h, 1d)
- Popular NSE pairs (NIFTY50, BANKNIFTY, FINNIFTY, etc.)

### 4. Analytics Page
- **Cumulative Profit** tracking
- **Trade Distribution** by pair (pie chart)
- **Daily Trading Activity** (bar chart)
- **Hourly Performance Heatmap**
- Risk metrics (Max Drawdown, Sharpe Ratio)
- Recent closed trades table

### 5. Backtest Page
- **CSV Upload** for historical data
  - Format: `timestamp, open, high, low, close, volume`
- **Strategy Selection** from available strategies
- **Timerange Configuration** (YYYYMMDD-YYYYMMDD)
- **Equity Curve** visualization
- Detailed trade history and metrics

### 6. Positions Page
- Open positions table
- Unrealized P/L tracking
- Leverage and liquidation price display
- Position detail cards

### 7. Settings Page
- **Bot Controls** (Start/Stop/Reload Config)
- **NSE Market Calendar** with live status
- Market hours and upcoming holidays
- API endpoint information
- Danger zone (Force exit, clear history)

## API Integration

### Freqtrade API
All Freqtrade API endpoints are integrated:
- Authentication (`/token/login`, `/token/logout`)
- Bot status and control (`/status`, `/start`, `/stop`)
- Trading data (`/trades`, `/balance`, `/profit`)
- Market data (`/pair_candles`, `/orderbook`)
- NSE extensions (`/nse/calendar`, `/csv/upload`)
- Backtesting (`/backtest`)

### OpenAlgo API
OpenAlgo integration for Indian brokers:
- Order placement
- Position tracking
- Funds and holdings
- Order history

### WebSocket
Real-time updates via Socket.IO:
- Ticker updates (live price changes)
- Trade updates (new trades, closed trades)
- Bot status changes
- Balance updates

## Customization

### Changing Theme Colors
Edit `src/app/globals.css` to customize colors:
```css
:root {
  --primary: 217.2 91.2% 59.8%;  /* Blue */
  --destructive: 0 62.8% 30.6%;   /* Red */
  /* Add your custom colors */
}
```

### Adding New Pages
1. Create page in `src/app/dashboard/yourpage/page.tsx`
2. Add navigation item in `src/app/dashboard/layout.tsx`
3. Add route types if needed

### Modifying Chart Appearance
Edit `src/components/TradingChart.tsx`:
```typescript
const chart = createChart(chartContainerRef.current, {
  layout: {
    background: { color: '#1a1a1a' },  // Change background
    textColor: '#d1d4dc',              // Change text color
  },
  // Customize other options
});
```

## Troubleshooting

### WebSocket Connection Issues
- Ensure Freqtrade is running with `api_server.enabled = true`
- Check CORS settings in Freqtrade config
- Verify `NEXT_PUBLIC_WS_URL` in `.env.local`

### API Connection Errors
- Verify Freqtrade API is accessible at `http://localhost:8080/api/v1`
- Check authentication credentials
- Review browser console for error messages

### Charts Not Displaying
- Ensure market data is available
- Check if pair exists in exchange
- Verify candle data is being fetched

### Build Errors
- Clear `.next` directory: `rm -rf .next`
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 18+)

## Performance Optimization

- **Code Splitting**: Next.js automatically code-splits by route
- **Image Optimization**: Use Next.js `<Image>` component
- **API Caching**: TanStack Query caches API responses
- **Lazy Loading**: Components loaded on demand
- **Production Build**: Minified and optimized for production

## Security Considerations

- JWT tokens stored in localStorage (consider httpOnly cookies for production)
- API endpoints should use HTTPS in production
- Implement rate limiting on backend
- Validate all user inputs
- Use environment variables for sensitive data

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is part of Freqtrade with Indian broker integration.

## Support

For issues and questions:
- Check Freqtrade documentation
- Review this README
- Open an issue on GitHub

## Roadmap

- [ ] Mobile-responsive improvements
- [ ] Advanced order types UI
- [ ] Strategy backtesting comparison
- [ ] Multi-account support
- [ ] Trading alerts and notifications
- [ ] Export trade history to CSV
- [ ] Dark/Light theme toggle
- [ ] Multi-language support

---

**Built with ❤️ for Indian Traders**
