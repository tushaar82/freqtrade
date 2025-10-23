'use client';

import { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, LineData } from 'lightweight-charts';
import { apiClient } from '@/lib/api-client';
import { wsClient } from '@/lib/websocket-client';
import type { Trade, OHLCV } from '@/types';

interface TradingChartProps {
  pair: string;
  timeframe: string;
  trades?: Trade[];
  height?: number;
}

export default function TradingChart({ pair, timeframe, trades = [], height = 600 }: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const stopLossSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const trailingStopSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const entryPriceSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height,
      layout: {
        background: { color: '#1a1a1a' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2b2b2b' },
        horzLines: { color: '#2b2b2b' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#3c3c3c',
      },
      timeScale: {
        borderColor: '#3c3c3c',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    // Add candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });
    candleSeriesRef.current = candleSeries;

    // Add entry price line series
    const entryPriceSeries = chart.addLineSeries({
      color: '#2962FF',
      lineWidth: 2,
      lineStyle: 2, // Dashed
      priceLineVisible: false,
      lastValueVisible: false,
    });
    entryPriceSeriesRef.current = entryPriceSeries;

    // Add stop loss line series
    const stopLossSeries = chart.addLineSeries({
      color: '#FF6B6B',
      lineWidth: 2,
      priceLineVisible: true,
      lastValueVisible: true,
      title: 'Stop Loss',
    });
    stopLossSeriesRef.current = stopLossSeries;

    // Add trailing stop line series
    const trailingStopSeries = chart.addLineSeries({
      color: '#FFA500',
      lineWidth: 2,
      lineStyle: 2, // Dashed
      priceLineVisible: true,
      lastValueVisible: true,
      title: 'Trailing Stop',
    });
    trailingStopSeriesRef.current = trailingStopSeries;

    // Fetch and load historical data
    loadHistoricalData();

    // Subscribe to live price updates
    const unsubscribe = wsClient.on('ticker', (data) => {
      if (data.pair === pair) {
        setCurrentPrice(data.last);
        updateChart(data.last, data.timestamp);
      }
    });

    // Handle window resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      unsubscribe();
      chart.remove();
    };
  }, [pair, timeframe]);

  // Update chart with trailing stop loss
  useEffect(() => {
    if (!trades.length) return;

    const openTrade = trades.find((t) => t.status === 'open' && t.pair === pair);
    
    if (openTrade && candleSeriesRef.current) {
      const timeScale = chartRef.current?.timeScale();
      if (!timeScale) return;

      const visibleRange = timeScale.getVisibleRange();
      if (!visibleRange) return;

      // Calculate trailing stop loss
      const trailingStopPrice = calculateTrailingStop(openTrade, currentPrice || openTrade.current_price);

      // Update entry price line
      if (entryPriceSeriesRef.current) {
        const entryPriceData: LineData[] = [
          { time: Math.floor(openTrade.open_timestamp / 1000) as any, value: openTrade.entry_price },
          { time: Math.floor(Date.now() / 1000) as any, value: openTrade.entry_price },
        ];
        entryPriceSeriesRef.current.setData(entryPriceData);
      }

      // Update stop loss line
      if (stopLossSeriesRef.current) {
        const stopLossData: LineData[] = [
          { time: Math.floor(openTrade.open_timestamp / 1000) as any, value: openTrade.stoploss },
          { time: Math.floor(Date.now() / 1000) as any, value: openTrade.stoploss },
        ];
        stopLossSeriesRef.current.setData(stopLossData);
      }

      // Update trailing stop line
      if (trailingStopSeriesRef.current && openTrade.trailing_stop) {
        const trailingStopData: LineData[] = [
          { time: Math.floor(openTrade.open_timestamp / 1000) as any, value: trailingStopPrice },
          { time: Math.floor(Date.now() / 1000) as any, value: trailingStopPrice },
        ];
        trailingStopSeriesRef.current.setData(trailingStopData);
      }
    }
  }, [trades, currentPrice, pair]);

  async function loadHistoricalData() {
    try {
      setLoading(true);
      const response = await apiClient.getPairCandles(pair, timeframe, 500);
      
      if (response.data && candleSeriesRef.current) {
        const candleData: CandlestickData[] = response.data.map((candle: OHLCV) => ({
          time: Math.floor(candle.timestamp / 1000) as any,
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
        }));

        candleSeriesRef.current.setData(candleData);
        
        if (candleData.length > 0) {
          setCurrentPrice(candleData[candleData.length - 1].close);
        }
      }
    } catch (error) {
      console.error('Failed to load historical data:', error);
    } finally {
      setLoading(false);
    }
  }

  function updateChart(price: number, timestamp: number) {
    if (!candleSeriesRef.current) return;

    const candle: CandlestickData = {
      time: Math.floor(timestamp / 1000) as any,
      open: price,
      high: price,
      low: price,
      close: price,
    };

    candleSeriesRef.current.update(candle);
  }

  function calculateTrailingStop(trade: Trade, currentPrice: number): number {
    if (!trade.trailing_stop) {
      return trade.stoploss;
    }

    const entryPrice = trade.entry_price;
    const offset = trade.trailing_stop_offset || 0.01; // 1% default

    if (trade.side === 'long') {
      // For long positions, trailing stop moves up
      const trailingStop = currentPrice * (1 - offset);
      return Math.max(trailingStop, trade.stoploss);
    } else {
      // For short positions, trailing stop moves down
      const trailingStop = currentPrice * (1 + offset);
      return Math.min(trailingStop, trade.stoploss);
    }
  }

  return (
    <div className="relative w-full">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-10">
          <div className="text-white">Loading chart data...</div>
        </div>
      )}
      <div ref={chartContainerRef} className="w-full" style={{ height }} />
      
      {/* Price info overlay */}
      {currentPrice && (
        <div className="absolute top-4 left-4 bg-black/80 text-white p-3 rounded-lg">
          <div className="text-sm text-gray-400">{pair}</div>
          <div className="text-2xl font-bold">₹{currentPrice.toFixed(2)}</div>
          <div className="text-xs text-gray-400 mt-1">{timeframe}</div>
        </div>
      )}
      
      {/* Legend */}
      <div className="absolute top-4 right-4 bg-black/80 text-white p-3 rounded-lg text-sm">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-3 h-0.5 bg-blue-500"></div>
          <span>Entry Price</span>
        </div>
        <div className="flex items-center gap-2 mb-1">
          <div className="w-3 h-0.5 bg-red-500"></div>
          <span>Stop Loss</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-0.5 bg-orange-500 border-dashed"></div>
          <span>Trailing Stop</span>
        </div>
      </div>
    </div>
  );
}
