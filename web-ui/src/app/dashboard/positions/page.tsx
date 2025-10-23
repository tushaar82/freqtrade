'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useTradingStore } from '@/store/useTradingStore';
import type { Position } from '@/types';

export default function PositionsPage() {
  const { positions, setPositions } = useTradingStore();

  // Fetch positions
  const { data: positionsData, isLoading } = useQuery<Position[]>({
    queryKey: ['positions'],
    queryFn: () => apiClient.getPositions(),
    refetchInterval: 5000,
  });

  if (positionsData && positionsData !== positions) {
    setPositions(positionsData);
  }

  const totalUnrealizedPnL = positions.reduce((sum, p) => sum + p.unrealized_pnl, 0);
  const totalUnrealizedPnLPct =
    positions.length > 0
      ? positions.reduce((sum, p) => sum + p.unrealized_pnl_pct, 0) / positions.length
      : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Open Positions</h1>
          <p className="text-gray-400 mt-1">Monitor your active positions and unrealized P/L</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="bg-gray-800 rounded-lg border border-gray-700 px-4 py-2">
            <div className="text-xs text-gray-400">Positions</div>
            <div className="text-2xl font-bold text-white">{positions.length}</div>
          </div>
          <div className="bg-gray-800 rounded-lg border border-gray-700 px-4 py-2 min-w-[150px]">
            <div className="text-xs text-gray-400">Unrealized P/L</div>
            <div
              className={`text-2xl font-bold ${
                totalUnrealizedPnL >= 0 ? 'profit-positive' : 'profit-negative'
              }`}
            >
              ₹{totalUnrealizedPnL.toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* Positions Table */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden card-glow">
        {isLoading ? (
          <div className="p-12 text-center">
            <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-gray-400 mt-4">Loading positions...</p>
          </div>
        ) : positions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-900/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Pair
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Side
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Entry Price
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Current Price
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Leverage
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Unrealized P/L
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                    P/L %
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Liq. Price
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {positions.map((position, idx) => (
                  <tr key={idx} className="hover:bg-gray-700/50 transition">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-white">{position.pair}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded ${
                          position.side === 'long' ? 'trade-long' : 'trade-short'
                        }`}
                      >
                        {position.side.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-300">
                      {position.amount.toFixed(4)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-300">
                      ₹{position.entry_price.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-white">
                      ₹{position.current_price.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-300">
                      {position.leverage}x
                    </td>
                    <td
                      className={`px-6 py-4 whitespace-nowrap text-right text-sm font-semibold ${
                        position.unrealized_pnl >= 0 ? 'profit-positive' : 'profit-negative'
                      }`}
                    >
                      ₹{position.unrealized_pnl.toFixed(2)}
                    </td>
                    <td
                      className={`px-6 py-4 whitespace-nowrap text-right text-sm font-semibold ${
                        position.unrealized_pnl_pct >= 0 ? 'profit-positive' : 'profit-negative'
                      }`}
                    >
                      {position.unrealized_pnl_pct >= 0 ? '+' : ''}
                      {position.unrealized_pnl_pct.toFixed(2)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-red-400">
                      {position.liquidation_price ? `₹${position.liquidation_price.toFixed(2)}` : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-12 text-center text-gray-500">
            <svg
              className="w-16 h-16 mx-auto mb-4 text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
            <p className="text-lg">No open positions</p>
            <p className="text-sm mt-1">Positions will appear here when trades are active</p>
          </div>
        )}
      </div>

      {/* Position Details Cards */}
      {positions.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {positions.map((position, idx) => (
            <div key={idx} className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-white">{position.pair}</h3>
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded ${
                    position.side === 'long' ? 'trade-long' : 'trade-short'
                  }`}
                >
                  {position.side.toUpperCase()}
                </span>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-400">Entry Price</span>
                  <span className="text-sm font-medium text-white">
                    ₹{position.entry_price.toFixed(2)}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-400">Current Price</span>
                  <span className="text-sm font-medium text-white">
                    ₹{position.current_price.toFixed(2)}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-400">Amount</span>
                  <span className="text-sm font-medium text-white">{position.amount.toFixed(4)}</span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-400">Leverage</span>
                  <span className="text-sm font-medium text-white">{position.leverage}x</span>
                </div>

                <div className="border-t border-gray-700 pt-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-gray-400">Unrealized P/L</span>
                    <span
                      className={`text-lg font-bold ${
                        position.unrealized_pnl >= 0 ? 'profit-positive' : 'profit-negative'
                      }`}
                    >
                      ₹{position.unrealized_pnl.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">P/L Percentage</span>
                    <span
                      className={`text-sm font-semibold ${
                        position.unrealized_pnl_pct >= 0 ? 'profit-positive' : 'profit-negative'
                      }`}
                    >
                      {position.unrealized_pnl_pct >= 0 ? '+' : ''}
                      {position.unrealized_pnl_pct.toFixed(2)}%
                    </span>
                  </div>
                </div>

                {position.liquidation_price && (
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mt-3">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-red-400">Liquidation Price</span>
                      <span className="text-sm font-bold text-red-400">
                        ₹{position.liquidation_price.toFixed(2)}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
