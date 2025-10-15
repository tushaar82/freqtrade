"""
Analytics API for PaperBroker - Provides backtest-style metrics for live paper trading
"""
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends

from freqtrade.persistence import Trade
from freqtrade.rpc.api_server.deps import get_config, get_rpc
from freqtrade.rpc.rpc import RPC, RPCException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/analytics/overview', response_model=dict[str, Any], tags=['analytics'])
async def analytics_overview(rpc: RPC = Depends(get_rpc)):
    """
    Get comprehensive analytics overview for Paper Trading
    Returns backtest-style metrics for current trading session
    """
    try:
        # Get all trades
        trades = Trade.get_trades([]).all()
        
        if not trades:
            return {
                'total_trades': 0,
                'open_trades': 0,
                'closed_trades': 0,
                'total_profit': 0,
                'total_profit_percent': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'avg_duration': 0,
                'best_trade': None,
                'worst_trade': None,
                'equity_curve': [],
                'daily_profit': [],
            }
        
        # Separate open and closed trades
        open_trades = [t for t in trades if t.is_open]
        closed_trades = [t for t in trades if not t.is_open]
        
        # Calculate metrics
        total_profit = sum(t.close_profit_abs or 0 for t in closed_trades)
        winning_trades = [t for t in closed_trades if (t.close_profit_abs or 0) > 0]
        losing_trades = [t for t in closed_trades if (t.close_profit_abs or 0) <= 0]
        
        win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0
        avg_profit = (total_profit / len(closed_trades)) if closed_trades else 0
        
        # Average duration
        durations = []
        for t in closed_trades:
            if t.close_date and t.open_date:
                duration = (t.close_date - t.open_date).total_seconds() / 60  # minutes
                durations.append(duration)
        avg_duration = (sum(durations) / len(durations)) if durations else 0
        
        # Best and worst trades
        best_trade = None
        worst_trade = None
        if closed_trades:
            best = max(closed_trades, key=lambda t: t.close_profit_abs or 0)
            worst = min(closed_trades, key=lambda t: t.close_profit_abs or 0)
            
            best_trade = {
                'pair': best.pair,
                'profit': best.close_profit_abs,
                'profit_percent': best.close_profit,
                'open_date': best.open_date.isoformat() if best.open_date else None,
                'close_date': best.close_date.isoformat() if best.close_date else None,
            }
            
            worst_trade = {
                'pair': worst.pair,
                'profit': worst.close_profit_abs,
                'profit_percent': worst.close_profit,
                'open_date': worst.open_date.isoformat() if worst.open_date else None,
                'close_date': worst.close_date.isoformat() if worst.close_date else None,
            }
        
        # Equity curve (cumulative profit over time)
        equity_curve = []
        cumulative_profit = 0
        for t in sorted(closed_trades, key=lambda x: x.close_date or datetime.min):
            cumulative_profit += (t.close_profit_abs or 0)
            equity_curve.append({
                'date': t.close_date.isoformat() if t.close_date else None,
                'profit': cumulative_profit,
                'trade_id': t.id,
                'pair': t.pair,
            })
        
        # Daily profit aggregation
        daily_profits = {}
        for t in closed_trades:
            if t.close_date:
                date_key = t.close_date.strftime('%Y-%m-%d')
                daily_profits[date_key] = daily_profits.get(date_key, 0) + (t.close_profit_abs or 0)
        
        daily_profit = [
            {'date': date, 'profit': profit}
            for date, profit in sorted(daily_profits.items())
        ]
        
        # Win/Loss streak
        streaks = []
        current_streak = 0
        current_type = None
        
        for t in sorted(closed_trades, key=lambda x: x.close_date or datetime.min):
            is_win = (t.close_profit_abs or 0) > 0
            if current_type is None:
                current_type = 'win' if is_win else 'loss'
                current_streak = 1
            elif (current_type == 'win' and is_win) or (current_type == 'loss' and not is_win):
                current_streak += 1
            else:
                streaks.append({'type': current_type, 'count': current_streak})
                current_type = 'win' if is_win else 'loss'
                current_streak = 1
        
        if current_streak > 0:
            streaks.append({'type': current_type, 'count': current_streak})
        
        max_win_streak = max([s['count'] for s in streaks if s['type'] == 'win'], default=0)
        max_loss_streak = max([s['count'] for s in streaks if s['type'] == 'loss'], default=0)
        
        return {
            'total_trades': len(trades),
            'open_trades': len(open_trades),
            'closed_trades': len(closed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'total_profit': round(total_profit, 2),
            'total_profit_percent': round((total_profit / 100000) * 100, 2) if total_profit else 0,
            'win_rate': round(win_rate, 2),
            'avg_profit': round(avg_profit, 2),
            'avg_profit_winning': round(sum(t.close_profit_abs or 0 for t in winning_trades) / len(winning_trades), 2) if winning_trades else 0,
            'avg_profit_losing': round(sum(t.close_profit_abs or 0 for t in losing_trades) / len(losing_trades), 2) if losing_trades else 0,
            'avg_duration': round(avg_duration, 2),
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'equity_curve': equity_curve,
            'daily_profit': daily_profit,
            'max_win_streak': max_win_streak,
            'max_loss_streak': max_loss_streak,
            'current_balance': rpc._freqtrade.wallets.get_total_stake_amount(),
        }
        
    except Exception as e:
        logger.exception("Error generating analytics overview")
        raise RPCException(f"Error generating analytics: {str(e)}")


@router.get('/analytics/trades', response_model=list[dict[str, Any]], tags=['analytics'])
async def analytics_trades(limit: int = 100, rpc: RPC = Depends(get_rpc)):
    """
    Get detailed trade list for analysis
    """
    try:
        trades = Trade.get_trades([]).limit(limit).all()
        
        trade_list = []
        for t in sorted(trades, key=lambda x: x.open_date or datetime.min, reverse=True):
            trade_list.append({
                'id': t.id,
                'pair': t.pair,
                'is_open': t.is_open,
                'open_date': t.open_date.isoformat() if t.open_date else None,
                'open_rate': t.open_rate,
                'close_date': t.close_date.isoformat() if t.close_date else None,
                'close_rate': t.close_rate,
                'amount': t.amount,
                'stake_amount': t.stake_amount,
                'profit_abs': t.close_profit_abs,
                'profit_percent': t.close_profit,
                'duration': (t.close_date - t.open_date).total_seconds() / 60 if t.close_date and t.open_date else None,
                'enter_tag': t.enter_tag,
                'exit_reason': t.exit_reason,
            })
        
        return trade_list
        
    except Exception as e:
        logger.exception("Error getting trades")
        raise RPCException(f"Error getting trades: {str(e)}")
