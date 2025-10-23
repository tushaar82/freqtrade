import { create } from 'zustand';
import type { Trade, BotStatus, Balance, Position } from '@/types';

interface TradingStore {
  botStatus: BotStatus | null;
  trades: Trade[];
  positions: Position[];
  balance: Balance[];
  activePair: string | null;
  
  setBotStatus: (status: BotStatus) => void;
  setTrades: (trades: Trade[]) => void;
  setPositions: (positions: Position[]) => void;
  setBalance: (balance: Balance[]) => void;
  setActivePair: (pair: string | null) => void;
  updateTrade: (trade: Trade) => void;
  removeTrade: (tradeId: string) => void;
}

export const useTradingStore = create<TradingStore>((set) => ({
  botStatus: null,
  trades: [],
  positions: [],
  balance: [],
  activePair: null,

  setBotStatus: (status) => set({ botStatus: status }),
  
  setTrades: (trades) => set({ trades }),
  
  setPositions: (positions) => set({ positions }),
  
  setBalance: (balance) => set({ balance }),
  
  setActivePair: (pair) => set({ activePair: pair }),
  
  updateTrade: (trade) =>
    set((state) => ({
      trades: state.trades.map((t) => (t.id === trade.id ? trade : t)),
    })),
  
  removeTrade: (tradeId) =>
    set((state) => ({
      trades: state.trades.filter((t) => t.id !== tradeId),
    })),
}));
