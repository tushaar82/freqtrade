'use client';

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useTradingStore } from '@/store/useTradingStore';
import type { PnLData, Trade, Balance } from '@/types';
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Bar, BarChart } from 'recharts';

export default function DashboardPage() {
  const { botStatus, setBotStatus, trades, setTrades, balance, setBalance } = useTradingStore();
  const [selectedTimeframe, setSelectedTimeframe] = useState<'1d' | '7d' | '30d' | 'all'>('7d');

  // Fetch bot status
  const { data: statusData } = useQuery({
    queryKey: ['botStatus'],
    queryFn: () => apiClient.getBotStatus(),
    refetchInterval: 5000,
  });

  // Fetch trades
  const { data: tradesData } = useQuery({
    queryKey: ['trades'],
    queryFn: () => apiClient.getTrades(),
    refetchInterval: 3000,
  });

  // Fetch balance
  const { data: balanceData } = useQuery({
    queryKey: ['balance'],
    queryFn: () => apiClient.getBalance(),
    refetchInterval: 10000,
  });

  // Fetch PnL data
  const { data: pnlData } = useQuery<PnLData>({
    queryKey: ['pnl', selectedTimeframe],
    queryFn: () => apiClient.getPnL(selectedTimeframe),
    refetchInterval: 10000,
  });

  useEffect(() => {
    if (statusData) setBotStatus(statusData);
    if (tradesData) setTrades(tradesData);
    if (balanceData) setBalance(balanceData);
  }, [statusData, tradesData, balanceData, setBotStatus, setTrades, setBalance]);

  const openTrades = trades.filter((t) => t.status === 'open');
  const totalPnL = openTrades.reduce((sum, t) => sum + t.profit_abs, 0);
  const totalPnLPct = openTrades.length > 0
    ? openTrades.reduce((sum, t) => sum + t.profit_pct, 0) / openTrades.length
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Trading Dashboard</h1>
          <p className="text-gray-400 mt-1">Real-time market overview and performance analytics</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-2 bg-gray-800 rounded-lg border border-gray-700">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-300">Live</span>
          </div>
          {botStatus && (
            <span
              className={`px-4 py-2 rounded-lg text-sm font-semibold ${
                botStatus.state === 'running'
                  ? 'status-running'
                  : botStatus.state === 'stopped'
                  ? 'status-stopped'
                  : 'status-paused'
              }`}
            >
              {botStatus.state.toUpperCase()}
            </span>
          )}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Balance"
          value={`₹${balance[0]?.total.toFixed(2) || '0.00'}`}
          change={pnlData?.total_profit_pct}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatCard
          title="Unrealized P/L"
          value={`₹${totalPnL.toFixed(2)}`}
          change={totalPnLPct}
          showChangeColor
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          }
        />
        <StatCard
          title="Open Trades"
          value={openTrades.length.toString()}
          subtitle={`of ${botStatus?.max_open_trades || 0} max`}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          }
        />
        <StatCard
          title="Win Rate"
          value={`${pnlData?.win_rate?.toFixed(1) || '0.0'}%`}
          subtitle={`${pnlData?.winning_trades || 0}W / ${pnlData?.losing_trades || 0}L`}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      </div>

      {/* PnL Chart */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-white">Profit & Loss</h2>
            <p className="text-sm text-gray-400 mt-1">Daily performance overview</p>
          </div>
          <div className="flex gap-2">
            {(['1d', '7d', '30d', 'all'] as const).map((tf) => (
              <button
                key={tf}
                onClick={() => setSelectedTimeframe(tf)}
                className={`px-3 py-1.5 text-sm font-medium rounded-lg transition ${
                  selectedTimeframe === tf
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                }`}
              >
                {tf.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {pnlData?.daily_profit && pnlData.daily_profit.length > 0 ? (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={pnlData.daily_profit}>
                <XAxis
                  dataKey="date"
                  stroke="#6B7280"
                  fontSize={12}
                  tickFormatter={(value) => new Date(value).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
                />
                <YAxis stroke="#6B7280" fontSize={12} tickFormatter={(value) => `₹${value}`} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: '#9CA3AF' }}
                  itemStyle={{ color: '#fff' }}
                  formatter={(value: any) => [`₹${value.toFixed(2)}`, 'Profit']}
                />
                <Line
                  type="monotone"
                  dataKey="profit"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  dot={{ fill: '#3B82F6', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-64 flex items-center justify-center text-gray-500">
            No profit data available
          </div>
        )}

        {/* Performance Metrics */}
        {pnlData && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-700">
            <MetricItem label="Total Profit" value={`₹${pnlData.total_profit?.toFixed(2) || '0.00'}`} />
            <MetricItem label="Avg Profit" value={`₹${pnlData.avg_profit?.toFixed(2) || '0.00'}`} />
            <MetricItem label="Profit Factor" value={pnlData.profit_factor?.toFixed(2) || '0.00'} />
            <MetricItem label="Sharpe Ratio" value={pnlData.sharpe_ratio?.toFixed(2) || '0.00'} />
            <MetricItem label="Best Trade" value={`₹${pnlData.best_trade?.toFixed(2) || '0.00'}`} positive />
            <MetricItem label="Worst Trade" value={`₹${pnlData.worst_trade?.toFixed(2) || '0.00'}`} negative />
            <MetricItem label="Max Drawdown" value={`${pnlData.max_drawdown?.toFixed(2) || '0.00'}%`} negative />
            <MetricItem label="Total Trades" value={pnlData.total_trades?.toString() || '0'} />
          </div>
        )}
      </div>

      {/* Open Trades */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 card-glow overflow-hidden">
        <div className="p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">Active Positions</h2>
          <p className="text-sm text-gray-400 mt-1">{openTrades.length} open trades</p>
        </div>
        <div className="overflow-x-auto">
          {openTrades.length > 0 ? (
            <table className="w-full">
              <thead className="bg-gray-900/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Pair</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Side</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">Entry</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">Current</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">Amount</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">P/L</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">P/L %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {openTrades.map((trade) => (
                  <tr key={trade.id} className="hover:bg-gray-700/50 transition">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-white">{trade.pair}</div>
                      <div className="text-xs text-gray-400">{new Date(trade.open_timestamp).toLocaleString('en-IN')}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded ${trade.side === 'long' ? 'trade-long' : 'trade-short'}`}>
                        {trade.side.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-300">
                      ₹{trade.entry_price.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-white">
                      ₹{trade.current_price.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-300">
                      {trade.amount.toFixed(4)}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-right text-sm font-semibold ${trade.profit_abs >= 0 ? 'profit-positive' : 'profit-negative'}`}>
                      ₹{trade.profit_abs.toFixed(2)}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-right text-sm font-semibold ${trade.profit_pct >= 0 ? 'profit-positive' : 'profit-negative'}`}>
                      {trade.profit_pct >= 0 ? '+' : ''}{trade.profit_pct.toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-12 text-center text-gray-500">
              <svg className="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p className="text-lg">No active positions</p>
              <p className="text-sm mt-1">Trades will appear here when the bot opens positions</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  change,
  subtitle,
  icon,
  showChangeColor = false,
}: {
  title: string;
  value: string;
  change?: number;
  subtitle?: string;
  icon: React.ReactNode;
  showChangeColor?: boolean;
}) {
  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
      <div className="flex items-center justify-between mb-4">
        <div className="p-2 bg-blue-500/10 rounded-lg text-blue-500">{icon}</div>
        {change !== undefined && (
          <span
            className={`text-sm font-semibold ${
              showChangeColor
                ? change >= 0
                  ? 'profit-positive'
                  : 'profit-negative'
                : 'text-gray-400'
            }`}
          >
            {change >= 0 ? '+' : ''}
            {change.toFixed(2)}%
          </span>
        )}
      </div>
      <div>
        <p className="text-sm text-gray-400 mb-1">{title}</p>
        <p className="text-2xl font-bold text-white number-transition">{value}</p>
        {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
}

function MetricItem({
  label,
  value,
  positive = false,
  negative = false,
}: {
  label: string;
  value: string;
  positive?: boolean;
  negative?: boolean;
}) {
  return (
    <div>
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p
        className={`text-lg font-semibold ${
          positive ? 'profit-positive' : negative ? 'profit-negative' : 'text-white'
        }`}
      >
        {value}
      </p>
    </div>
  );
}
