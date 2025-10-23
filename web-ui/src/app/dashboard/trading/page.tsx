'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import TradingChart from '@/components/TradingChart';
import { apiClient } from '@/lib/api-client';
import { useTradingStore } from '@/store/useTradingStore';
import type { OrderBook } from '@/types';

const POPULAR_PAIRS = [
  'NIFTY50',
  'BANKNIFTY',
  'FINNIFTY',
  'RELIANCE',
  'TCS',
  'INFY',
  'HDFC',
  'ICICIBANK',
];

const TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d'];

export default function TradingPage() {
  const [selectedPair, setSelectedPair] = useState('NIFTY50');
  const [selectedTimeframe, setSelectedTimeframe] = useState('5m');
  const { trades } = useTradingStore();

  // Fetch order book
  const { data: orderBook } = useQuery<OrderBook>({
    queryKey: ['orderBook', selectedPair],
    queryFn: () => apiClient.getOrderBook(selectedPair),
    refetchInterval: 2000,
    enabled: !!selectedPair,
  });

  const activeTrade = trades.find((t) => t.status === 'open' && t.pair === selectedPair);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Live Trading</h1>
          <p className="text-gray-400 mt-1">Real-time price charts with trailing stop loss visualization</p>
        </div>
      </div>

      {/* Main Trading View */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Chart - Takes 3 columns */}
        <div className="lg:col-span-3 space-y-4">
          {/* Pair and Timeframe Selector */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
            <div className="flex flex-wrap items-center gap-4">
              {/* Pair Selector */}
              <div className="flex-1 min-w-[200px]">
                <label className="block text-xs text-gray-400 mb-2">Trading Pair</label>
                <select
                  value={selectedPair}
                  onChange={(e) => setSelectedPair(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {POPULAR_PAIRS.map((pair) => (
                    <option key={pair} value={pair}>
                      {pair}
                    </option>
                  ))}
                </select>
              </div>

              {/* Timeframe Selector */}
              <div className="flex-1 min-w-[200px]">
                <label className="block text-xs text-gray-400 mb-2">Timeframe</label>
                <div className="flex gap-2">
                  {TIMEFRAMES.map((tf) => (
                    <button
                      key={tf}
                      onClick={() => setSelectedTimeframe(tf)}
                      className={`px-3 py-2 text-sm font-medium rounded-lg transition ${
                        selectedTimeframe === tf
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                      }`}
                    >
                      {tf}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden card-glow">
            <TradingChart
              pair={selectedPair}
              timeframe={selectedTimeframe}
              trades={trades}
              height={600}
            />
          </div>

          {/* Active Trade Info */}
          {activeTrade && (
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
              <h3 className="text-lg font-bold text-white mb-4">Active Position</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <InfoItem label="Entry Price" value={`₹${activeTrade.entry_price.toFixed(2)}`} />
                <InfoItem label="Current Price" value={`₹${activeTrade.current_price.toFixed(2)}`} />
                <InfoItem label="Stop Loss" value={`₹${activeTrade.stoploss.toFixed(2)}`} />
                <InfoItem
                  label="P/L"
                  value={`₹${activeTrade.profit_abs.toFixed(2)} (${activeTrade.profit_pct >= 0 ? '+' : ''}${activeTrade.profit_pct.toFixed(2)}%)`}
                  colored
                  isPositive={activeTrade.profit_abs >= 0}
                />
                <InfoItem label="Amount" value={activeTrade.amount.toFixed(4)} />
                <InfoItem label="Stake" value={`₹${activeTrade.stake_amount.toFixed(2)}`} />
                <InfoItem label="Strategy" value={activeTrade.strategy} />
                <InfoItem
                  label="Trailing SL"
                  value={activeTrade.trailing_stop ? `${(activeTrade.trailing_stop_offset * 100).toFixed(1)}%` : 'Disabled'}
                />
              </div>
            </div>
          )}
        </div>

        {/* Order Book - Takes 1 column */}
        <div className="lg:col-span-1 space-y-4">
          {/* Order Book */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden card-glow">
            <div className="p-4 border-b border-gray-700">
              <h3 className="text-lg font-bold text-white">Order Book</h3>
              <p className="text-xs text-gray-400 mt-1">{selectedPair}</p>
            </div>

            <div className="p-4 space-y-4">
              {/* Asks (Sell Orders) */}
              <div>
                <div className="text-xs text-gray-400 mb-2 font-medium">ASKS</div>
                <div className="space-y-1">
                  {orderBook?.asks.slice(0, 10).map((ask, idx) => (
                    <OrderBookRow
                      key={idx}
                      price={ask[0]}
                      amount={ask[1]}
                      type="ask"
                      maxAmount={Math.max(...(orderBook?.asks.slice(0, 10).map(a => a[1]) || [1]))}
                    />
                  ))}
                </div>
              </div>

              {/* Current Price */}
              {orderBook && (
                <div className="py-3 border-y border-gray-700">
                  <div className="text-center">
                    <div className="text-xs text-gray-400 mb-1">Current Price</div>
                    <div className="text-2xl font-bold text-white">
                      ₹{((orderBook.asks[0]?.[0] || 0) + (orderBook.bids[0]?.[0] || 0)) / 2}
                    </div>
                  </div>
                </div>
              )}

              {/* Bids (Buy Orders) */}
              <div>
                <div className="text-xs text-gray-400 mb-2 font-medium">BIDS</div>
                <div className="space-y-1">
                  {orderBook?.bids.slice(0, 10).map((bid, idx) => (
                    <OrderBookRow
                      key={idx}
                      price={bid[0]}
                      amount={bid[1]}
                      type="bid"
                      maxAmount={Math.max(...(orderBook?.bids.slice(0, 10).map(b => b[1]) || [1]))}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 card-glow">
            <h3 className="text-sm font-bold text-white mb-3">Market Info</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-400">24h High</span>
                <span className="text-sm font-semibold text-green-400">₹0.00</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-400">24h Low</span>
                <span className="text-sm font-semibold text-red-400">₹0.00</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-400">24h Volume</span>
                <span className="text-sm font-semibold text-white">0</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-400">24h Change</span>
                <span className="text-sm font-semibold text-gray-400">0.00%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function InfoItem({
  label,
  value,
  colored = false,
  isPositive = true,
}: {
  label: string;
  value: string;
  colored?: boolean;
  isPositive?: boolean;
}) {
  return (
    <div>
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p
        className={`text-sm font-semibold ${
          colored ? (isPositive ? 'profit-positive' : 'profit-negative') : 'text-white'
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function OrderBookRow({
  price,
  amount,
  type,
  maxAmount,
}: {
  price: number;
  amount: number;
  type: 'bid' | 'ask';
  maxAmount: number;
}) {
  const percentage = (amount / maxAmount) * 100;

  return (
    <div className="relative h-6 overflow-hidden rounded">
      {/* Background bar */}
      <div
        className={`absolute top-0 right-0 h-full ${
          type === 'bid' ? 'bg-green-500/10' : 'bg-red-500/10'
        }`}
        style={{ width: `${percentage}%` }}
      />

      {/* Content */}
      <div className="relative flex justify-between items-center h-full px-2 text-xs">
        <span className={type === 'bid' ? 'text-green-400' : 'text-red-400'}>
          ₹{price.toFixed(2)}
        </span>
        <span className="text-gray-400">{amount.toFixed(4)}</span>
      </div>
    </div>
  );
}
