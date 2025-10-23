'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { PnLData, Trade } from '@/types';
import {
  Line,
  LineChart,
  Bar,
  BarChart,
  Pie,
  PieChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
  CartesianGrid,
} from 'recharts';

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d');

  // Fetch PnL data
  const { data: pnlData } = useQuery<PnLData>({
    queryKey: ['pnl', timeRange],
    queryFn: () => apiClient.getPnL(timeRange),
    refetchInterval: 30000,
  });

  // Fetch all trades
  const { data: allTrades } = useQuery<Trade[]>({
    queryKey: ['allTrades'],
    queryFn: () => apiClient.getTrades(),
    refetchInterval: 10000,
  });

  // Calculate trade distribution by pair
  const tradesByPair = allTrades?.reduce((acc, trade) => {
    acc[trade.pair] = (acc[trade.pair] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const pairDistribution = Object.entries(tradesByPair || {})
    .map(([pair, count]) => ({ name: pair, value: count }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 6);

  // Calculate hourly performance
  const hourlyPerformance = Array.from({ length: 24 }, (_, hour) => {
    const tradesInHour = allTrades?.filter((trade) => {
      const tradeHour = new Date(trade.open_timestamp).getHours();
      return tradeHour === hour;
    }) || [];

    const avgProfit = tradesInHour.length > 0
      ? tradesInHour.reduce((sum, t) => sum + t.profit_pct, 0) / tradesInHour.length
      : 0;

    return {
      hour: `${hour}:00`,
      trades: tradesInHour.length,
      avgProfit: avgProfit,
    };
  });

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Analytics & Insights</h1>
          <p className="text-gray-400 mt-1">Comprehensive trading performance analysis</p>
        </div>
        <div className="flex gap-2">
          {(['7d', '30d', '90d', 'all'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition ${
                timeRange === range
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700 border border-gray-700'
              }`}
            >
              {range === 'all' ? 'All Time' : range.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <KPICard
          title="Total Profit"
          value={`₹${pnlData?.total_profit?.toFixed(2) || '0.00'}`}
          change={pnlData?.total_profit_pct}
          icon="💰"
        />
        <KPICard
          title="Win Rate"
          value={`${pnlData?.win_rate?.toFixed(1) || '0.0'}%`}
          subtitle={`${pnlData?.winning_trades || 0}W / ${pnlData?.losing_trades || 0}L`}
          icon="🎯"
        />
        <KPICard
          title="Avg Profit"
          value={`₹${pnlData?.avg_profit?.toFixed(2) || '0.00'}`}
          subtitle={`per trade`}
          icon="📊"
        />
        <KPICard
          title="Profit Factor"
          value={pnlData?.profit_factor?.toFixed(2) || '0.00'}
          subtitle={pnlData && pnlData.profit_factor > 1 ? 'Profitable' : 'Loss'}
          icon="⚡"
        />
        <KPICard
          title="Sharpe Ratio"
          value={pnlData?.sharpe_ratio?.toFixed(2) || '0.00'}
          subtitle="Risk-adjusted"
          icon="📈"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cumulative Profit Chart */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
          <h2 className="text-xl font-bold text-white mb-4">Cumulative Profit</h2>
          {pnlData?.daily_profit && pnlData.daily_profit.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={pnlData.daily_profit.map((d, idx, arr) => ({
                    ...d,
                    cumulative: arr.slice(0, idx + 1).reduce((sum, item) => sum + item.profit, 0),
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis
                    dataKey="date"
                    stroke="#6B7280"
                    fontSize={12}
                    tickFormatter={(value) =>
                      new Date(value).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
                    }
                  />
                  <YAxis stroke="#6B7280" fontSize={12} tickFormatter={(value) => `₹${value}`} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                    }}
                    formatter={(value: any) => [`₹${value.toFixed(2)}`, 'Cumulative']}
                  />
                  <Line
                    type="monotone"
                    dataKey="cumulative"
                    stroke="#3B82F6"
                    strokeWidth={3}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-80 flex items-center justify-center text-gray-500">
              No data available
            </div>
          )}
        </div>

        {/* Trade Distribution by Pair */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
          <h2 className="text-xl font-bold text-white mb-4">Trade Distribution by Pair</h2>
          {pairDistribution.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pairDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pairDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-80 flex items-center justify-center text-gray-500">
              No trades available
            </div>
          )}
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Trades Count */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
          <h2 className="text-xl font-bold text-white mb-4">Daily Trading Activity</h2>
          {pnlData?.daily_profit && pnlData.daily_profit.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={pnlData.daily_profit}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis
                    dataKey="date"
                    stroke="#6B7280"
                    fontSize={12}
                    tickFormatter={(value) =>
                      new Date(value).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
                    }
                  />
                  <YAxis stroke="#6B7280" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                    }}
                    formatter={(value: any) => [value, 'Trades']}
                  />
                  <Bar dataKey="trades" fill="#3B82F6" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-80 flex items-center justify-center text-gray-500">
              No data available
            </div>
          )}
        </div>

        {/* Hourly Performance */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
          <h2 className="text-xl font-bold text-white mb-4">Hourly Performance Heatmap</h2>
          <div className="h-80 overflow-y-auto">
            <div className="grid grid-cols-6 gap-2">
              {hourlyPerformance.map((data, idx) => {
                const intensity = Math.abs(data.avgProfit);
                const isPositive = data.avgProfit >= 0;
                const opacity = Math.min(intensity / 2, 1);

                return (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg text-center transition-all hover:scale-105 cursor-pointer ${
                      data.trades === 0
                        ? 'bg-gray-700/20'
                        : isPositive
                        ? 'bg-green-500'
                        : 'bg-red-500'
                    }`}
                    style={{ opacity: data.trades === 0 ? 0.3 : 0.3 + opacity * 0.7 }}
                    title={`${data.hour}: ${data.trades} trades, Avg: ${data.avgProfit.toFixed(2)}%`}
                  >
                    <div className="text-xs font-medium text-white">{idx}</div>
                    <div className="text-[10px] text-gray-300 mt-1">{data.trades}</div>
                  </div>
                );
              })}
            </div>
            <div className="mt-4 text-xs text-gray-400 text-center">
              Darker colors indicate higher trading activity and profitability
            </div>
          </div>
        </div>
      </div>

      {/* Risk Metrics */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
        <h2 className="text-xl font-bold text-white mb-4">Risk & Performance Metrics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
          <MetricCard label="Max Drawdown" value={`${pnlData?.max_drawdown?.toFixed(2) || '0.00'}%`} type="negative" />
          <MetricCard label="Best Trade" value={`₹${pnlData?.best_trade?.toFixed(2) || '0.00'}`} type="positive" />
          <MetricCard label="Worst Trade" value={`₹${pnlData?.worst_trade?.toFixed(2) || '0.00'}`} type="negative" />
          <MetricCard label="Total Trades" value={pnlData?.total_trades?.toString() || '0'} />
          <MetricCard label="Winning Trades" value={pnlData?.winning_trades?.toString() || '0'} type="positive" />
          <MetricCard label="Losing Trades" value={pnlData?.losing_trades?.toString() || '0'} type="negative" />
        </div>
      </div>

      {/* Recent Closed Trades */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden card-glow">
        <div className="p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">Recent Closed Trades</h2>
        </div>
        <div className="overflow-x-auto">
          {allTrades && allTrades.filter((t) => t.status === 'closed').length > 0 ? (
            <table className="w-full">
              <thead className="bg-gray-900/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Pair</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Side</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase">Entry</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase">Exit</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase">P/L</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase">P/L %</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {allTrades
                  .filter((t) => t.status === 'closed')
                  .slice(0, 10)
                  .map((trade) => (
                    <tr key={trade.id} className="hover:bg-gray-700/50 transition">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                        {trade.pair}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded ${
                            trade.side === 'long' ? 'trade-long' : 'trade-short'
                          }`}
                        >
                          {trade.side.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-300">
                        ₹{trade.entry_price.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-300">
                        ₹{trade.current_price.toFixed(2)}
                      </td>
                      <td
                        className={`px-6 py-4 whitespace-nowrap text-right text-sm font-semibold ${
                          trade.profit_abs >= 0 ? 'profit-positive' : 'profit-negative'
                        }`}
                      >
                        ₹{trade.profit_abs.toFixed(2)}
                      </td>
                      <td
                        className={`px-6 py-4 whitespace-nowrap text-right text-sm font-semibold ${
                          trade.profit_pct >= 0 ? 'profit-positive' : 'profit-negative'
                        }`}
                      >
                        {trade.profit_pct >= 0 ? '+' : ''}
                        {trade.profit_pct.toFixed(2)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                        {new Date(trade.open_timestamp).toLocaleDateString('en-IN')}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          ) : (
            <div className="p-12 text-center text-gray-500">
              <p className="text-lg">No closed trades yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function KPICard({
  title,
  value,
  change,
  subtitle,
  icon,
}: {
  title: string;
  value: string;
  change?: number;
  subtitle?: string;
  icon: string;
}) {
  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 card-glow">
      <div className="flex items-start justify-between mb-3">
        <span className="text-2xl">{icon}</span>
        {change !== undefined && (
          <span
            className={`text-xs font-semibold ${change >= 0 ? 'profit-positive' : 'profit-negative'}`}
          >
            {change >= 0 ? '+' : ''}
            {change.toFixed(2)}%
          </span>
        )}
      </div>
      <p className="text-xs text-gray-400 mb-1">{title}</p>
      <p className="text-xl font-bold text-white mb-1">{value}</p>
      {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
    </div>
  );
}

function MetricCard({
  label,
  value,
  type,
}: {
  label: string;
  value: string;
  type?: 'positive' | 'negative';
}) {
  return (
    <div className="text-center">
      <p className="text-xs text-gray-400 mb-2">{label}</p>
      <p
        className={`text-2xl font-bold ${
          type === 'positive'
            ? 'profit-positive'
            : type === 'negative'
            ? 'profit-negative'
            : 'text-white'
        }`}
      >
        {value}
      </p>
    </div>
  );
}
