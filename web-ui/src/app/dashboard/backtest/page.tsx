'use client';

import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { BacktestResult } from '@/types';
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from 'recharts';

export default function BacktestPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedStrategy, setSelectedStrategy] = useState('SampleStrategy');
  const [timerange, setTimerange] = useState('');
  const [uploadPair, setUploadPair] = useState('NIFTY50');
  const [uploadProgress, setUploadProgress] = useState(0);

  // Fetch available strategies
  const { data: strategies } = useQuery<string[]>({
    queryKey: ['strategies'],
    queryFn: () => apiClient.getStrategies(),
  });

  // Fetch uploaded CSV files
  const { data: csvFiles } = useQuery<string[]>({
    queryKey: ['csvFiles'],
    queryFn: () => apiClient.listCSVFiles(),
  });

  // Fetch backtest results
  const { data: backtestResult, isLoading: isBacktesting } = useQuery<BacktestResult | null>({
    queryKey: ['backtestResult'],
    enabled: false,
  });

  // CSV upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      return apiClient.uploadCSVData(file, uploadPair, (progress) => {
        setUploadProgress(progress);
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['csvFiles'] });
      setUploadProgress(0);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    },
  });

  // Run backtest mutation
  const backtestMutation = useMutation({
    mutationFn: async () => {
      return apiClient.runBacktest({
        strategy: selectedStrategy,
        timerange: timerange || undefined,
      });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['backtestResult'], data);
    },
  });

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadMutation.mutate(file);
    }
  };

  const handleRunBacktest = () => {
    backtestMutation.mutate();
  };

  const handleDeleteCSV = async (filename: string) => {
    try {
      await apiClient.deleteCSVData(filename);
      queryClient.invalidateQueries({ queryKey: ['csvFiles'] });
    } catch (error) {
      console.error('Failed to delete CSV:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Backtesting</h1>
        <p className="text-gray-400 mt-1">Test your strategies with historical data</p>
      </div>

      {/* Configuration Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CSV Upload */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
          <h2 className="text-xl font-bold text-white mb-4">Upload Historical Data</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Trading Pair</label>
              <input
                type="text"
                value={uploadPair}
                onChange={(e) => setUploadPair(e.target.value)}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., NIFTY50, BANKNIFTY"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">CSV File</label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleFileUpload}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-500 file:text-white hover:file:bg-blue-600 file:cursor-pointer"
              />
              <p className="text-xs text-gray-500 mt-2">
                CSV format: timestamp, open, high, low, close, volume
              </p>
            </div>

            {uploadProgress > 0 && uploadProgress < 100 && (
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            )}

            {uploadMutation.isSuccess && (
              <div className="bg-green-500/10 border border-green-500/30 text-green-400 px-4 py-3 rounded-lg text-sm">
                CSV file uploaded successfully!
              </div>
            )}

            {uploadMutation.isError && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg text-sm">
                Failed to upload CSV file
              </div>
            )}
          </div>

          {/* Uploaded Files */}
          {csvFiles && csvFiles.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Uploaded Files</h3>
              <div className="space-y-2">
                {csvFiles.map((file) => (
                  <div
                    key={file}
                    className="flex items-center justify-between bg-gray-900/50 px-3 py-2 rounded-lg"
                  >
                    <span className="text-sm text-white">{file}</span>
                    <button
                      onClick={() => handleDeleteCSV(file)}
                      className="text-red-400 hover:text-red-300 text-sm"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Backtest Configuration */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
          <h2 className="text-xl font-bold text-white mb-4">Backtest Configuration</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Strategy</label>
              <select
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {strategies?.map((strategy) => (
                  <option key={strategy} value={strategy}>
                    {strategy}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Time Range (Optional)
              </label>
              <input
                type="text"
                value={timerange}
                onChange={(e) => setTimerange(e.target.value)}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="YYYYMMDD-YYYYMMDD"
              />
              <p className="text-xs text-gray-500 mt-2">Example: 20240101-20241231</p>
            </div>

            <button
              onClick={handleRunBacktest}
              disabled={isBacktesting || backtestMutation.isPending}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition flex items-center justify-center"
            >
              {isBacktesting || backtestMutation.isPending ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  Running Backtest...
                </>
              ) : (
                'Run Backtest'
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Results Section */}
      {backtestResult && (
        <div className="space-y-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <StatCard label="Total Trades" value={backtestResult.total_trades.toString()} />
            <StatCard
              label="Win Rate"
              value={`${backtestResult.win_rate.toFixed(1)}%`}
              positive={backtestResult.win_rate >= 50}
            />
            <StatCard
              label="Total Profit"
              value={`₹${backtestResult.profit_total.toFixed(2)}`}
              positive={backtestResult.profit_total >= 0}
            />
            <StatCard
              label="Profit %"
              value={`${backtestResult.profit_total_pct.toFixed(2)}%`}
              positive={backtestResult.profit_total_pct >= 0}
            />
            <StatCard
              label="Avg Profit"
              value={`₹${backtestResult.avg_profit.toFixed(2)}`}
              positive={backtestResult.avg_profit >= 0}
            />
            <StatCard
              label="Max Drawdown"
              value={`${backtestResult.max_drawdown.toFixed(2)}%`}
              negative
            />
          </div>

          {/* Equity Curve */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
            <h2 className="text-xl font-bold text-white mb-4">Equity Curve</h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={backtestResult.trades.map((trade, idx, arr) => ({
                    index: idx,
                    equity: arr.slice(0, idx + 1).reduce((sum, t) => sum + t.profit_abs, 10000),
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="index" stroke="#6B7280" fontSize={12} />
                  <YAxis stroke="#6B7280" fontSize={12} tickFormatter={(value) => `₹${value}`} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                    }}
                  />
                  <Line type="monotone" dataKey="equity" stroke="#3B82F6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Trades Table */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden card-glow">
            <div className="p-6 border-b border-gray-700">
              <h2 className="text-xl font-bold text-white">Trade History</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-900/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                      Pair
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase">
                      Open
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase">
                      Close
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase">
                      Profit %
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase">
                      Profit
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase">
                      Duration
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {backtestResult.trades.map((trade, idx) => (
                    <tr key={idx} className="hover:bg-gray-700/50">
                      <td className="px-6 py-4 text-sm text-white">{trade.pair}</td>
                      <td className="px-6 py-4 text-sm text-gray-300 text-right">
                        ₹{trade.open_price.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-300 text-right">
                        ₹{trade.close_price.toFixed(2)}
                      </td>
                      <td
                        className={`px-6 py-4 text-sm font-semibold text-right ${
                          trade.profit_pct >= 0 ? 'profit-positive' : 'profit-negative'
                        }`}
                      >
                        {trade.profit_pct >= 0 ? '+' : ''}
                        {trade.profit_pct.toFixed(2)}%
                      </td>
                      <td
                        className={`px-6 py-4 text-sm font-semibold text-right ${
                          trade.profit_abs >= 0 ? 'profit-positive' : 'profit-negative'
                        }`}
                      >
                        ₹{trade.profit_abs.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-400 text-right">
                        {Math.round(trade.duration / 60)} min
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
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
    <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p
        className={`text-2xl font-bold ${
          positive ? 'profit-positive' : negative ? 'profit-negative' : 'text-white'
        }`}
      >
        {value}
      </p>
    </div>
  );
}
