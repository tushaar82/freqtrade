'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useTradingStore } from '@/store/useTradingStore';

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { botStatus } = useTradingStore();
  const [maxOpenTrades, setMaxOpenTrades] = useState(botStatus?.max_open_trades || 3);
  const [dryRun, setDryRun] = useState(botStatus?.dry_run ?? true);

  // Bot control mutations
  const startBotMutation = useMutation({
    mutationFn: () => apiClient.startBot(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['botStatus'] });
    },
  });

  const stopBotMutation = useMutation({
    mutationFn: () => apiClient.stopBot(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['botStatus'] });
    },
  });

  const reloadConfigMutation = useMutation({
    mutationFn: () => apiClient.reloadConfig(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['botStatus'] });
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Settings</h1>
        <p className="text-gray-400 mt-1">Configure your trading bot and preferences</p>
      </div>

      {/* Bot Controls */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
        <h2 className="text-xl font-bold text-white mb-4">Bot Controls</h2>

        <div className="space-y-4">
          {/* Bot Status */}
          <div className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg">
            <div>
              <div className="text-sm font-medium text-white">Bot Status</div>
              <div className="text-xs text-gray-400 mt-1">
                {botStatus?.state === 'running' ? 'Bot is currently running' : 'Bot is stopped'}
              </div>
            </div>
            <span
              className={`px-4 py-2 rounded-lg text-sm font-semibold ${
                botStatus?.state === 'running' ? 'status-running' : 'status-stopped'
              }`}
            >
              {botStatus?.state?.toUpperCase() || 'UNKNOWN'}
            </span>
          </div>

          {/* Control Buttons */}
          <div className="flex gap-3">
            <button
              onClick={() => startBotMutation.mutate()}
              disabled={botStatus?.state === 'running' || startBotMutation.isPending}
              className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition"
            >
              {startBotMutation.isPending ? 'Starting...' : 'Start Bot'}
            </button>

            <button
              onClick={() => stopBotMutation.mutate()}
              disabled={botStatus?.state !== 'running' || stopBotMutation.isPending}
              className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition"
            >
              {stopBotMutation.isPending ? 'Stopping...' : 'Stop Bot'}
            </button>

            <button
              onClick={() => reloadConfigMutation.mutate()}
              disabled={reloadConfigMutation.isPending}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition"
            >
              {reloadConfigMutation.isPending ? 'Reloading...' : 'Reload Config'}
            </button>
          </div>
        </div>
      </div>

      {/* Bot Configuration */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
        <h2 className="text-xl font-bold text-white mb-4">Bot Configuration</h2>

        <div className="space-y-6">
          {/* Current Settings Display */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-gray-900/50 rounded-lg">
              <div className="text-xs text-gray-400 mb-1">Exchange</div>
              <div className="text-lg font-semibold text-white">{botStatus?.exchange || 'N/A'}</div>
            </div>

            <div className="p-4 bg-gray-900/50 rounded-lg">
              <div className="text-xs text-gray-400 mb-1">Strategy</div>
              <div className="text-lg font-semibold text-white">{botStatus?.strategy || 'N/A'}</div>
            </div>

            <div className="p-4 bg-gray-900/50 rounded-lg">
              <div className="text-xs text-gray-400 mb-1">Max Open Trades</div>
              <div className="text-lg font-semibold text-white">
                {botStatus?.max_open_trades || 0}
              </div>
            </div>

            <div className="p-4 bg-gray-900/50 rounded-lg">
              <div className="text-xs text-gray-400 mb-1">Open Trades</div>
              <div className="text-lg font-semibold text-white">{botStatus?.open_trades || 0}</div>
            </div>

            <div className="p-4 bg-gray-900/50 rounded-lg">
              <div className="text-xs text-gray-400 mb-1">Total Stake</div>
              <div className="text-lg font-semibold text-white">
                ₹{botStatus?.total_stake?.toFixed(2) || '0.00'}
              </div>
            </div>

            <div className="p-4 bg-gray-900/50 rounded-lg">
              <div className="text-xs text-gray-400 mb-1">Mode</div>
              <div className="text-lg font-semibold text-white">
                {botStatus?.dry_run ? 'Dry Run' : 'Live Trading'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* NSE Calendar */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
        <h2 className="text-xl font-bold text-white mb-4">NSE Market Calendar</h2>

        <NSECalendarInfo />
      </div>

      {/* API Endpoints */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 card-glow">
        <h2 className="text-xl font-bold text-white mb-4">API Information</h2>

        <div className="space-y-3">
          <div className="p-4 bg-gray-900/50 rounded-lg">
            <div className="text-xs text-gray-400 mb-2">Freqtrade API</div>
            <code className="text-sm text-blue-400">http://localhost:8080/api/v1</code>
          </div>

          <div className="p-4 bg-gray-900/50 rounded-lg">
            <div className="text-xs text-gray-400 mb-2">OpenAlgo API</div>
            <code className="text-sm text-blue-400">http://localhost:5000/api/v1</code>
          </div>

          <div className="p-4 bg-gray-900/50 rounded-lg">
            <div className="text-xs text-gray-400 mb-2">WebSocket</div>
            <code className="text-sm text-blue-400">ws://localhost:8080/ws</code>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-gray-800 rounded-xl border border-red-500/50 p-6">
        <h2 className="text-xl font-bold text-red-400 mb-4">Danger Zone</h2>

        <div className="space-y-3">
          <div className="p-4 bg-red-500/10 rounded-lg border border-red-500/30">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-white">Force Exit All Trades</div>
                <div className="text-xs text-gray-400 mt-1">
                  Immediately close all open positions
                </div>
              </div>
              <button className="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg transition">
                Force Exit
              </button>
            </div>
          </div>

          <div className="p-4 bg-red-500/10 rounded-lg border border-red-500/30">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-white">Clear Trade History</div>
                <div className="text-xs text-gray-400 mt-1">
                  Delete all closed trade records
                </div>
              </div>
              <button className="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg transition">
                Clear History
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function NSECalendarInfo() {
  const { data: calendarInfo } = useQuery({
    queryKey: ['nseCalendar'],
    queryFn: () => apiClient.getNSECalendar(),
    refetchInterval: 60000, // Refresh every minute
  });

  if (!calendarInfo) {
    return <div className="text-gray-400">Loading calendar info...</div>;
  }

  const { market_hours, current_status, upcoming_holidays } = calendarInfo;

  return (
    <div className="space-y-4">
      {/* Market Status */}
      <div className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg">
        <div>
          <div className="text-sm font-medium text-white">Market Status</div>
          <div className="text-xs text-gray-400 mt-1">{current_status.current_time}</div>
        </div>
        <span
          className={`px-4 py-2 rounded-lg text-sm font-semibold ${
            current_status.is_open ? 'status-running' : 'status-stopped'
          }`}
        >
          {current_status.is_open ? 'OPEN' : 'CLOSED'}
        </span>
      </div>

      {/* Market Hours */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-gray-900/50 rounded-lg">
          <div className="text-xs text-gray-400 mb-1">Market Open</div>
          <div className="text-lg font-semibold text-white">{market_hours.open}</div>
        </div>

        <div className="p-4 bg-gray-900/50 rounded-lg">
          <div className="text-xs text-gray-400 mb-1">Market Close</div>
          <div className="text-lg font-semibold text-white">{market_hours.close}</div>
        </div>

        <div className="p-4 bg-gray-900/50 rounded-lg">
          <div className="text-xs text-gray-400 mb-1">Pre-Market Open</div>
          <div className="text-sm font-semibold text-white">{market_hours.pre_market_open}</div>
        </div>

        <div className="p-4 bg-gray-900/50 rounded-lg">
          <div className="text-xs text-gray-400 mb-1">Post-Market Close</div>
          <div className="text-sm font-semibold text-white">{market_hours.post_market_close}</div>
        </div>
      </div>

      {/* Upcoming Holidays */}
      {upcoming_holidays && upcoming_holidays.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-white mb-2">Upcoming Holidays</h3>
          <div className="space-y-2">
            {upcoming_holidays.slice(0, 5).map((holiday, idx) => (
              <div key={idx} className="px-3 py-2 bg-gray-900/50 rounded text-sm text-gray-300">
                {new Date(holiday).toLocaleDateString('en-IN', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
