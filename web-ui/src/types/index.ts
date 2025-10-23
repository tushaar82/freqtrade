// Core Types for NSE Trading Platform

export interface User {
  username: string;
  email?: string;
  role: 'admin' | 'trader' | 'viewer';
  preferences?: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark';
  defaultTimeframe: string;
  notifications: boolean;
  soundAlerts: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
}

export interface Trade {
  id: string;
  pair: string;
  side: 'long' | 'short';
  entry_price: number;
  current_price: number;
  amount: number;
  stake_amount: number;
  profit_pct: number;
  profit_abs: number;
  open_timestamp: number;
  stoploss: number;
  stoploss_pct: number;
  trailing_stop: boolean;
  trailing_stop_offset: number;
  status: 'open' | 'closed';
  strategy: string;
}

export interface BotStatus {
  state: 'running' | 'stopped' | 'paused';
  strategy: string;
  max_open_trades: number;
  open_trades: number;
  total_stake: number;
  dry_run: boolean;
  exchange: string;
}

export interface Balance {
  currency: string;
  free: number;
  used: number;
  total: number;
}

export interface PnLData {
  initial_balance: number;
  current_balance: number;
  total_profit: number;
  total_profit_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  best_trade: number;
  worst_trade: number;
  avg_profit: number;
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
  daily_profit: DailyProfit[];
}

export interface DailyProfit {
  date: string;
  profit: number;
  profit_pct: number;
  trades: number;
}

export interface OHLCV {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartData {
  pair: string;
  timeframe: string;
  data: OHLCV[];
  trades: ChartTrade[];
}

export interface ChartTrade {
  timestamp: number;
  type: 'buy' | 'sell';
  price: number;
  amount: number;
  profit?: number;
}

export interface OrderBook {
  bids: [number, number][];
  asks: [number, number][];
  timestamp: number;
}

export interface Position {
  pair: string;
  side: 'long' | 'short';
  amount: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  leverage: number;
  liquidation_price?: number;
}

export interface Strategy {
  name: string;
  description: string;
  timeframe: string;
  minimal_roi: Record<string, number>;
  stoploss: number;
  trailing_stop: boolean;
  trailing_stop_positive: number;
  trailing_stop_positive_offset: number;
  trailing_only_offset_is_reached: boolean;
}

export interface BacktestResult {
  strategy: string;
  timerange: string;
  total_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  profit_total: number;
  profit_total_pct: number;
  avg_profit: number;
  max_drawdown: number;
  sharpe_ratio: number;
  trades: BacktestTrade[];
}

export interface BacktestTrade {
  pair: string;
  open_timestamp: number;
  close_timestamp: number;
  open_price: number;
  close_price: number;
  profit_pct: number;
  profit_abs: number;
  duration: number;
}

export interface NSECalendar {
  market_hours: {
    open: string;
    close: string;
    pre_market_open: string;
    post_market_close: string;
  };
  current_status: {
    is_open: boolean;
    is_trading_day: boolean;
    current_time: string;
    seconds_until_close?: number;
    seconds_until_open?: number;
  };
  upcoming_holidays: string[];
}

export interface AlertConfig {
  pair: string;
  condition: 'above' | 'below' | 'crosses_above' | 'crosses_below';
  price: number;
  enabled: boolean;
  sound: boolean;
  notification: boolean;
}

export interface WebSocketMessage {
  type: 'status' | 'trade' | 'balance' | 'ticker' | 'order';
  data: any;
  timestamp: number;
}

export interface ApiError {
  error: string;
  detail?: string;
  status: number;
}

export interface OpenAlgoOrder {
  symbol: string;
  exchange: string;
  action: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  price_type: 'MARKET' | 'LIMIT';
  product: 'MIS' | 'CNC' | 'NRML';
  strategy: string;
}

export interface OpenAlgoPosition {
  symbol: string;
  exchange: string;
  quantity: number;
  avg_price: number;
  ltp: number;
  pnl: number;
  pnl_pct: number;
}
