"""API endpoints for mobile app support"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from freqtrade.exceptions import OperationalException
from freqtrade.rpc.api_server.api_auth import get_rpc_optional, validate_auth
from freqtrade.rpc.api_server.deps import get_config
from freqtrade.rpc.rpc import RPC, RPCException


logger = logging.getLogger(__name__)

# Create the router
router = APIRouter()


@router.get('/dashboard', tags=['mobile'])
def get_mobile_dashboard(
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Get mobile dashboard summary with key metrics.
    """
    try:
        if not rpc:
            raise HTTPException(status_code=503, detail="Bot is not running")
        
        # Get basic stats
        try:
            status = rpc._rpc_status()
            profit = rpc._rpc_profit(0, None, None)
            balance = rpc._rpc_balance(rpc._freqtrade.config['stake_currency'])
            
            # Calculate summary metrics
            total_trades = len(status) if status else 0
            open_trades = len([t for t in status if t.get('is_open', False)]) if status else 0
            
            # Get profit metrics
            total_profit = profit.get('profit_closed_coin', 0) if profit else 0
            profit_ratio = profit.get('profit_closed_ratio_mean', 0) if profit else 0
            
            # Get balance
            available_balance = balance.get('free', 0) if balance else 0
            total_balance = balance.get('total', 0) if balance else 0
            
            return {
                "summary": {
                    "total_trades": total_trades,
                    "open_trades": open_trades,
                    "closed_trades": total_trades - open_trades,
                    "total_profit": round(total_profit, 2),
                    "profit_percentage": round(profit_ratio * 100, 2) if profit_ratio else 0,
                    "available_balance": round(available_balance, 2),
                    "total_balance": round(total_balance, 2),
                    "bot_status": "running"
                },
                "recent_trades": _get_recent_trades_summary(status[:5] if status else []),
                "timestamp": "2025-10-16T04:59:41+05:30"
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            # Return minimal dashboard if RPC fails
            return {
                "summary": {
                    "total_trades": 0,
                    "open_trades": 0,
                    "closed_trades": 0,
                    "total_profit": 0.0,
                    "profit_percentage": 0.0,
                    "available_balance": 0.0,
                    "total_balance": 0.0,
                    "bot_status": "error"
                },
                "recent_trades": [],
                "error": str(e),
                "timestamp": "2025-10-16T04:59:41+05:30"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get mobile dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/watchlist', tags=['mobile'])
def get_watchlist(
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Get user's watchlist.
    """
    try:
        # In a real implementation, this would fetch from user preferences
        # For now, return the pair whitelist from config
        pair_whitelist = config.get('exchange', {}).get('pair_whitelist', [])
        
        watchlist = []
        for pair in pair_whitelist[:10]:  # Limit to 10 for mobile
            try:
                # Get current price if bot is running
                if rpc:
                    ticker = rpc._freqtrade.exchange.fetch_ticker(pair)
                    current_price = ticker.get('last', 0)
                    change_24h = ticker.get('percentage', 0)
                else:
                    current_price = 0
                    change_24h = 0
                
                watchlist.append({
                    "symbol": pair,
                    "current_price": current_price,
                    "change_24h": change_24h,
                    "is_trading": pair in [t.get('pair') for t in (rpc._rpc_status() if rpc else [])]
                })
                
            except Exception as e:
                logger.warning(f"Failed to get data for {pair}: {e}")
                watchlist.append({
                    "symbol": pair,
                    "current_price": 0,
                    "change_24h": 0,
                    "is_trading": False,
                    "error": "Data unavailable"
                })
        
        return {
            "watchlist": watchlist,
            "timestamp": "2025-10-16T04:59:41+05:30"
        }
        
    except Exception as e:
        logger.error(f"Failed to get watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/watchlist', tags=['mobile'])
def add_to_watchlist(
    symbol_data: Dict[str, Any],
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Add symbol to watchlist.
    """
    try:
        symbol = symbol_data.get('symbol')
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        # In a real implementation, this would save to user preferences
        # For now, just validate the symbol format
        if '/' not in symbol:
            raise HTTPException(status_code=400, detail="Invalid symbol format. Use SYMBOL/QUOTE format")
        
        return {
            "status": "success",
            "message": f"Added {symbol} to watchlist",
            "symbol": symbol,
            "timestamp": "2025-10-16T04:59:41+05:30"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/alerts', tags=['mobile'])
def get_price_alerts(
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Get user's price alerts.
    """
    try:
        # Mock price alerts - in production, fetch from database
        alerts = [
            {
                "id": 1,
                "symbol": "NIFTY/INR",
                "alert_type": "price_above",
                "target_price": 19600,
                "current_price": 19550,
                "is_active": True,
                "created_at": "2025-10-15T10:00:00Z"
            },
            {
                "id": 2,
                "symbol": "BANKNIFTY/INR",
                "alert_type": "price_below",
                "target_price": 44800,
                "current_price": 45000,
                "is_active": True,
                "created_at": "2025-10-15T11:30:00Z"
            }
        ]
        
        return {
            "alerts": alerts,
            "total_alerts": len(alerts),
            "active_alerts": len([a for a in alerts if a['is_active']]),
            "timestamp": "2025-10-16T04:59:41+05:30"
        }
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/alerts', tags=['mobile'])
def create_price_alert(
    alert_data: Dict[str, Any],
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Create a new price alert.
    """
    try:
        symbol = alert_data.get('symbol')
        alert_type = alert_data.get('alert_type')  # 'price_above', 'price_below'
        target_price = alert_data.get('target_price')
        
        if not all([symbol, alert_type, target_price]):
            raise HTTPException(status_code=400, detail="symbol, alert_type, and target_price are required")
        
        if alert_type not in ['price_above', 'price_below']:
            raise HTTPException(status_code=400, detail="alert_type must be 'price_above' or 'price_below'")
        
        # In production, save to database
        alert_id = 123  # Mock ID
        
        return {
            "status": "success",
            "message": "Price alert created successfully",
            "alert": {
                "id": alert_id,
                "symbol": symbol,
                "alert_type": alert_type,
                "target_price": target_price,
                "is_active": True,
                "created_at": "2025-10-16T04:59:41+05:30"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/notifications', tags=['mobile'])
def get_notifications(
    limit: int = Query(20, description="Number of notifications to fetch"),
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Get push notifications for mobile app.
    """
    try:
        # Mock notifications - in production, fetch from database
        notifications = [
            {
                "id": 1,
                "type": "trade_opened",
                "title": "New Trade Opened",
                "message": "Opened long position in NIFTY/INR at ₹19,550",
                "timestamp": "2025-10-16T04:30:00+05:30",
                "is_read": False,
                "data": {"pair": "NIFTY/INR", "side": "long", "price": 19550}
            },
            {
                "id": 2,
                "type": "trade_closed",
                "title": "Trade Closed",
                "message": "Closed position in BANKNIFTY/INR with +2.5% profit",
                "timestamp": "2025-10-16T03:45:00+05:30",
                "is_read": True,
                "data": {"pair": "BANKNIFTY/INR", "profit_pct": 2.5}
            },
            {
                "id": 3,
                "type": "price_alert",
                "title": "Price Alert Triggered",
                "message": "NIFTY/INR crossed above ₹19,600",
                "timestamp": "2025-10-16T02:15:00+05:30",
                "is_read": False,
                "data": {"pair": "NIFTY/INR", "price": 19600, "alert_type": "price_above"}
            }
        ]
        
        # Apply limit
        notifications = notifications[:limit]
        
        return {
            "notifications": notifications,
            "total_count": len(notifications),
            "unread_count": len([n for n in notifications if not n['is_read']]),
            "timestamp": "2025-10-16T04:59:41+05:30"
        }
        
    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/orders/quick', tags=['mobile'])
def place_quick_order(
    order_data: Dict[str, Any],
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Place a quick order from mobile app.
    """
    try:
        if not rpc:
            raise HTTPException(status_code=503, detail="Bot is not running")
        
        pair = order_data.get('pair')
        side = order_data.get('side')  # 'buy' or 'sell'
        amount = order_data.get('amount')
        order_type = order_data.get('order_type', 'market')
        price = order_data.get('price')
        
        if not all([pair, side, amount]):
            raise HTTPException(status_code=400, detail="pair, side, and amount are required")
        
        if side not in ['buy', 'sell']:
            raise HTTPException(status_code=400, detail="side must be 'buy' or 'sell'")
        
        # Place order through RPC
        try:
            if side == 'buy':
                result = rpc._rpc_force_entry(pair, price, order_type)
            else:
                # For sell, we need to find an open trade
                open_trades = rpc._rpc_status()
                trade_to_exit = None
                for trade in open_trades:
                    if trade.get('pair') == pair and trade.get('is_open'):
                        trade_to_exit = trade
                        break
                
                if trade_to_exit:
                    result = rpc._rpc_force_exit(trade_to_exit['trade_id'], order_type)
                else:
                    raise HTTPException(status_code=400, detail=f"No open position found for {pair}")
            
            return {
                "status": "success",
                "message": f"Order placed successfully",
                "order": {
                    "pair": pair,
                    "side": side,
                    "amount": amount,
                    "order_type": order_type,
                    "price": price,
                    "result": result
                },
                "timestamp": "2025-10-16T04:59:41+05:30"
            }
            
        except RPCException as e:
            raise HTTPException(status_code=400, detail=str(e))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to place quick order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/portfolio', tags=['mobile'])
def get_portfolio_summary(
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Get portfolio summary for mobile app.
    """
    try:
        if not rpc:
            raise HTTPException(status_code=503, detail="Bot is not running")
        
        # Get portfolio data
        status = rpc._rpc_status()
        profit = rpc._rpc_profit(0, None, None)
        balance = rpc._rpc_balance(rpc._freqtrade.config['stake_currency'])
        
        # Calculate portfolio metrics
        total_value = balance.get('total', 0) if balance else 0
        available_cash = balance.get('free', 0) if balance else 0
        invested_amount = total_value - available_cash
        
        # Get positions
        positions = []
        if status:
            for trade in status:
                if trade.get('is_open'):
                    positions.append({
                        "pair": trade.get('pair'),
                        "side": "long" if not trade.get('is_short', False) else "short",
                        "amount": trade.get('amount', 0),
                        "entry_price": trade.get('open_rate', 0),
                        "current_price": trade.get('current_rate', 0),
                        "unrealized_pnl": trade.get('profit_abs', 0),
                        "unrealized_pnl_pct": trade.get('profit_ratio', 0) * 100 if trade.get('profit_ratio') else 0,
                        "instrument_type": trade.get('instrument_type', 'EQUITY')
                    })
        
        # Separate equity and options positions
        equity_positions = [p for p in positions if p['instrument_type'] == 'EQUITY']
        options_positions = [p for p in positions if p['instrument_type'] in ['CALL_OPTION', 'PUT_OPTION']]
        
        return {
            "portfolio": {
                "total_value": round(total_value, 2),
                "available_cash": round(available_cash, 2),
                "invested_amount": round(invested_amount, 2),
                "total_pnl": round(profit.get('profit_closed_coin', 0) if profit else 0, 2),
                "total_pnl_pct": round(profit.get('profit_closed_ratio_mean', 0) * 100 if profit else 0, 2),
                "positions_count": len(positions),
                "equity_positions": len(equity_positions),
                "options_positions": len(options_positions)
            },
            "positions": positions,
            "timestamp": "2025-10-16T04:59:41+05:30"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/pnl/realtime', tags=['mobile'])
def get_realtime_pnl(
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Get real-time P&L data for mobile app.
    """
    try:
        if not rpc:
            raise HTTPException(status_code=503, detail="Bot is not running")
        
        # Get current trades and calculate real-time P&L
        status = rpc._rpc_status()
        
        total_unrealized_pnl = 0
        total_unrealized_pnl_pct = 0
        open_trades_count = 0
        
        daily_pnl = 0  # This would need to be calculated from today's trades
        
        if status:
            for trade in status:
                if trade.get('is_open'):
                    open_trades_count += 1
                    total_unrealized_pnl += trade.get('profit_abs', 0)
                    total_unrealized_pnl_pct += trade.get('profit_ratio', 0) * 100 if trade.get('profit_ratio') else 0
        
        # Average P&L percentage
        avg_pnl_pct = total_unrealized_pnl_pct / open_trades_count if open_trades_count > 0 else 0
        
        return {
            "realtime_pnl": {
                "total_unrealized_pnl": round(total_unrealized_pnl, 2),
                "avg_unrealized_pnl_pct": round(avg_pnl_pct, 2),
                "daily_pnl": round(daily_pnl, 2),
                "open_positions": open_trades_count,
                "last_updated": "2025-10-16T04:59:41+05:30"
            },
            "timestamp": "2025-10-16T04:59:41+05:30"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get real-time P&L: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/charts/{pair}', tags=['mobile'])
def get_chart_data(
    pair: str,
    timeframe: str = Query('5m', description="Chart timeframe"),
    limit: int = Query(100, description="Number of candles"),
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Get chart data for mobile app.
    """
    try:
        if not rpc:
            raise HTTPException(status_code=503, detail="Bot is not running")
        
        # Get OHLCV data
        try:
            ohlcv = rpc._freqtrade.exchange.fetch_ohlcv(pair, timeframe, limit=limit)
            
            # Format for mobile chart
            chart_data = []
            for candle in ohlcv:
                chart_data.append({
                    "timestamp": candle[0],
                    "open": candle[1],
                    "high": candle[2],
                    "low": candle[3],
                    "close": candle[4],
                    "volume": candle[5]
                })
            
            return {
                "pair": pair,
                "timeframe": timeframe,
                "data": chart_data,
                "count": len(chart_data),
                "timestamp": "2025-10-16T04:59:41+05:30"
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch chart data for {pair}: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to fetch chart data: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chart data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/strategy/toggle', tags=['mobile'])
def toggle_strategy(
    action_data: Dict[str, Any],
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Start or stop trading strategy from mobile app.
    """
    try:
        if not rpc:
            raise HTTPException(status_code=503, detail="Bot is not running")
        
        action = action_data.get('action')  # 'start' or 'stop'
        
        if action not in ['start', 'stop']:
            raise HTTPException(status_code=400, detail="action must be 'start' or 'stop'")
        
        try:
            if action == 'start':
                result = rpc._rpc_start()
                message = "Strategy started successfully"
            else:
                result = rpc._rpc_stop()
                message = "Strategy stopped successfully"
            
            return {
                "status": "success",
                "message": message,
                "action": action,
                "result": result,
                "timestamp": "2025-10-16T04:59:41+05:30"
            }
            
        except RPCException as e:
            raise HTTPException(status_code=400, detail=str(e))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/settings', tags=['mobile'])
def get_mobile_settings(
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Get mobile app settings.
    """
    try:
        # Return relevant config settings for mobile app
        settings = {
            "trading": {
                "max_open_trades": config.get('max_open_trades', 3),
                "stake_amount": config.get('stake_amount', 10000),
                "stake_currency": config.get('stake_currency', 'INR'),
                "timeframe": config.get('timeframe', '5m'),
                "dry_run": config.get('dry_run', True)
            },
            "notifications": {
                "trade_notifications": True,
                "price_alerts": True,
                "profit_alerts": True,
                "loss_alerts": True
            },
            "display": {
                "currency_format": "INR",
                "decimal_places": 2,
                "theme": "light"
            },
            "bot_status": "running" if rpc else "stopped"
        }
        
        return {
            "settings": settings,
            "timestamp": "2025-10-16T04:59:41+05:30"
        }
        
    except Exception as e:
        logger.error(f"Failed to get mobile settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/device/register', tags=['mobile'])
def register_device(
    device_data: Dict[str, Any],
    config=Depends(get_config)
):
    """
    Register mobile device for push notifications.
    """
    try:
        device_token = device_data.get('device_token')
        platform = device_data.get('platform')  # 'android' or 'ios'
        app_version = device_data.get('app_version')
        
        if not device_token:
            raise HTTPException(status_code=400, detail="device_token is required")
        
        # In production, save device token to database for push notifications
        device_id = "mobile_device_123"  # Mock device ID
        
        return {
            "status": "success",
            "message": "Device registered successfully",
            "device_id": device_id,
            "device_token": device_token,
            "platform": platform,
            "registered_at": "2025-10-16T04:59:41+05:30"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_recent_trades_summary(trades: List[Dict]) -> List[Dict]:
    """Get summary of recent trades for mobile dashboard"""
    summary = []
    for trade in trades:
        summary.append({
            "pair": trade.get('pair'),
            "side": "long" if not trade.get('is_short', False) else "short",
            "profit_abs": trade.get('profit_abs', 0),
            "profit_pct": trade.get('profit_ratio', 0) * 100 if trade.get('profit_ratio') else 0,
            "is_open": trade.get('is_open', False),
            "open_date": trade.get('open_date'),
            "instrument_type": trade.get('instrument_type', 'EQUITY')
        })
    return summary
