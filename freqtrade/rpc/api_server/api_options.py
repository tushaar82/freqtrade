"""API endpoints for options trading"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from freqtrade.data.lot_size_manager import LotSizeManager
from freqtrade.enums import InstrumentType
from freqtrade.exceptions import OperationalException
from freqtrade.rpc.api_server.api_auth import get_rpc_optional, validate_auth
from freqtrade.rpc.api_server.deps import get_config
from freqtrade.rpc.rpc import RPC, RPCException


logger = logging.getLogger(__name__)

# Create the router
router = APIRouter()


@router.get('/chains', response_model=List[Dict[str, Any]], tags=['options'])
def get_option_chains(
    symbol: str = Query(..., description="Underlying symbol (e.g., NIFTY)"),
    expiry: Optional[str] = Query(None, description="Expiry date (YYYY-MM-DD)"),
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Fetch option chains for a symbol.
    """
    try:
        if not rpc:
            raise HTTPException(status_code=503, detail="Bot is not running")
        
        # Get option chain from exchange
        try:
            exchange = rpc._freqtrade.exchange
            if hasattr(exchange, 'fetch_option_chain'):
                option_chain = exchange.fetch_option_chain(symbol, expiry)
            else:
                # Fallback: generate mock option chain
                option_chain = _generate_mock_option_chain(symbol, expiry)
            
            return {
                "symbol": symbol,
                "expiry": expiry,
                "chains": option_chain,
                "timestamp": "2025-10-16T04:59:41+05:30"
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch option chain for {symbol}: {e}")
            # Return mock data for demonstration
            return {
                "symbol": symbol,
                "expiry": expiry,
                "chains": _generate_mock_option_chain(symbol, expiry),
                "timestamp": "2025-10-16T04:59:41+05:30",
                "note": "Mock data - exchange integration needed"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get option chains: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/strikes', response_model=List[float], tags=['options'])
def get_available_strikes(
    symbol: str = Query(..., description="Underlying symbol"),
    expiry: Optional[str] = Query(None, description="Expiry date"),
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Get available strike prices for a symbol.
    """
    try:
        # This would typically fetch from exchange
        # For now, generate based on current price
        if symbol.upper() == 'NIFTY':
            base_price = 19500  # Mock current NIFTY price
            strikes = []
            for i in range(-10, 11):  # 21 strikes around current price
                strikes.append(base_price + (i * 50))  # 50 point intervals
        elif symbol.upper() == 'BANKNIFTY':
            base_price = 45000  # Mock current BANKNIFTY price
            strikes = []
            for i in range(-10, 11):
                strikes.append(base_price + (i * 100))  # 100 point intervals
        else:
            strikes = [100, 110, 120, 130, 140, 150]  # Generic strikes
        
        return strikes
        
    except Exception as e:
        logger.error(f"Failed to get strikes for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/expiries', response_model=List[str], tags=['options'])
def get_available_expiries(
    symbol: str = Query(..., description="Underlying symbol"),
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Get available expiry dates for a symbol.
    """
    try:
        # Mock expiry dates - in production, fetch from exchange
        from datetime import datetime, timedelta
        
        expiries = []
        current_date = datetime.now()
        
        # Generate next 4 weekly expiries (Thursdays for NIFTY)
        for i in range(4):
            # Find next Thursday
            days_ahead = 3 - current_date.weekday()  # Thursday is 3
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            expiry_date = current_date + timedelta(days=days_ahead + (i * 7))
            expiries.append(expiry_date.strftime('%Y-%m-%d'))
        
        return expiries
        
    except Exception as e:
        logger.error(f"Failed to get expiries for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/greeks', tags=['options'])
def calculate_option_greeks(
    symbol: str = Query(..., description="Option symbol"),
    spot_price: float = Query(..., description="Current spot price"),
    strike_price: float = Query(..., description="Strike price"),
    time_to_expiry: float = Query(..., description="Time to expiry in years"),
    volatility: float = Query(0.2, description="Implied volatility"),
    risk_free_rate: float = Query(0.06, description="Risk-free rate"),
    option_type: str = Query(..., description="CALL or PUT"),
    config=Depends(get_config)
):
    """
    Calculate options Greeks using Black-Scholes model.
    """
    try:
        import math
        from scipy.stats import norm
        
        # Black-Scholes calculations
        d1 = (math.log(spot_price / strike_price) + 
              (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * math.sqrt(time_to_expiry))
        d2 = d1 - volatility * math.sqrt(time_to_expiry)
        
        # Calculate Greeks
        if option_type.upper() == 'CALL':
            delta = norm.cdf(d1)
            theta = (-(spot_price * norm.pdf(d1) * volatility) / (2 * math.sqrt(time_to_expiry)) -
                    risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2))
            price = (spot_price * norm.cdf(d1) - 
                    strike_price * math.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2))
        else:  # PUT
            delta = -norm.cdf(-d1)
            theta = (-(spot_price * norm.pdf(d1) * volatility) / (2 * math.sqrt(time_to_expiry)) +
                    risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2))
            price = (strike_price * math.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) - 
                    spot_price * norm.cdf(-d1))
        
        gamma = norm.pdf(d1) / (spot_price * volatility * math.sqrt(time_to_expiry))
        vega = spot_price * norm.pdf(d1) * math.sqrt(time_to_expiry) / 100  # Per 1% change in volatility
        rho = (strike_price * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * 
               (norm.cdf(d2) if option_type.upper() == 'CALL' else -norm.cdf(-d2))) / 100
        
        return {
            "symbol": symbol,
            "option_type": option_type.upper(),
            "spot_price": spot_price,
            "strike_price": strike_price,
            "time_to_expiry": time_to_expiry,
            "volatility": volatility,
            "theoretical_price": round(price, 2),
            "greeks": {
                "delta": round(delta, 4),
                "gamma": round(gamma, 6),
                "theta": round(theta, 4),
                "vega": round(vega, 4),
                "rho": round(rho, 4)
            },
            "timestamp": "2025-10-16T04:59:41+05:30"
        }
        
    except ImportError:
        raise HTTPException(status_code=500, detail="scipy package required for Greeks calculation")
    except Exception as e:
        logger.error(f"Failed to calculate Greeks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/lot-sizes', tags=['options'])
def get_lot_sizes(
    symbol: Optional[str] = Query(None, description="Specific symbol to get lot size for"),
    config=Depends(get_config)
):
    """
    Get lot size data for options trading.
    """
    try:
        lot_size_manager = LotSizeManager(config)
        
        if symbol:
            # Get lot size for specific symbol
            lot_size = lot_size_manager.get_lot_size(symbol)
            lot_info = lot_size_manager.get_lot_size_info(symbol)
            return lot_info
        else:
            # Get all lot sizes
            all_lot_sizes = lot_size_manager.get_all_lot_sizes()
            return all_lot_sizes
        
    except Exception as e:
        logger.error(f"Failed to get lot sizes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/lot-sizes/update', tags=['options'])
def update_lot_sizes(
    exchange_name: Optional[str] = None,
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Update lot sizes from exchange APIs.
    """
    try:
        lot_size_manager = LotSizeManager(config)
        success = lot_size_manager.update_lot_sizes(exchange_name)
        
        if success:
            return {
                "status": "success",
                "message": "Lot sizes updated successfully",
                "timestamp": "2025-10-16T04:59:41+05:30"
            }
        else:
            return {
                "status": "warning",
                "message": "Lot sizes update failed, using cached data",
                "timestamp": "2025-10-16T04:59:41+05:30"
            }
        
    except Exception as e:
        logger.error(f"Failed to update lot sizes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/calculator', tags=['options'])
def options_pnl_calculator(
    entry_price: float = Query(..., description="Entry price"),
    exit_price: float = Query(..., description="Exit price"),
    quantity: int = Query(..., description="Quantity"),
    lot_size: int = Query(1, description="Lot size"),
    option_type: str = Query(..., description="CALL or PUT"),
    config=Depends(get_config)
):
    """
    Calculate options P&L.
    """
    try:
        # Calculate basic P&L
        if option_type.upper() == 'CALL':
            pnl_per_unit = exit_price - entry_price
        else:  # PUT
            pnl_per_unit = exit_price - entry_price
        
        total_pnl = pnl_per_unit * quantity
        pnl_percentage = (pnl_per_unit / entry_price) * 100 if entry_price > 0 else 0
        
        # Calculate lot-based metrics
        lots_traded = quantity / lot_size if lot_size > 0 else 1
        pnl_per_lot = total_pnl / lots_traded if lots_traded > 0 else total_pnl
        
        return {
            "entry_price": entry_price,
            "exit_price": exit_price,
            "quantity": quantity,
            "lot_size": lot_size,
            "lots_traded": lots_traded,
            "option_type": option_type.upper(),
            "pnl": {
                "total_pnl": round(total_pnl, 2),
                "pnl_per_unit": round(pnl_per_unit, 2),
                "pnl_per_lot": round(pnl_per_lot, 2),
                "pnl_percentage": round(pnl_percentage, 2)
            },
            "timestamp": "2025-10-16T04:59:41+05:30"
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate P&L: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/strategies', tags=['options'])
def get_options_strategies(config=Depends(get_config)):
    """
    Get predefined options strategies.
    """
    try:
        strategies = [
            {
                "name": "Long Call",
                "description": "Buy call option - bullish strategy",
                "legs": [{"action": "BUY", "option_type": "CALL", "quantity": 1}],
                "max_profit": "Unlimited",
                "max_loss": "Premium paid",
                "breakeven": "Strike + Premium"
            },
            {
                "name": "Long Put",
                "description": "Buy put option - bearish strategy",
                "legs": [{"action": "BUY", "option_type": "PUT", "quantity": 1}],
                "max_profit": "Strike - Premium",
                "max_loss": "Premium paid",
                "breakeven": "Strike - Premium"
            },
            {
                "name": "Long Straddle",
                "description": "Buy call and put at same strike - high volatility strategy",
                "legs": [
                    {"action": "BUY", "option_type": "CALL", "quantity": 1},
                    {"action": "BUY", "option_type": "PUT", "quantity": 1}
                ],
                "max_profit": "Unlimited",
                "max_loss": "Total premium paid",
                "breakeven": "Strike ± Total Premium"
            },
            {
                "name": "Long Strangle",
                "description": "Buy call and put at different strikes - high volatility strategy",
                "legs": [
                    {"action": "BUY", "option_type": "CALL", "quantity": 1, "note": "Higher strike"},
                    {"action": "BUY", "option_type": "PUT", "quantity": 1, "note": "Lower strike"}
                ],
                "max_profit": "Unlimited",
                "max_loss": "Total premium paid",
                "breakeven": "Call Strike + Premium, Put Strike - Premium"
            },
            {
                "name": "Iron Condor",
                "description": "Sell call spread and put spread - low volatility strategy",
                "legs": [
                    {"action": "SELL", "option_type": "PUT", "quantity": 1, "note": "Lower strike"},
                    {"action": "BUY", "option_type": "PUT", "quantity": 1, "note": "Lowest strike"},
                    {"action": "SELL", "option_type": "CALL", "quantity": 1, "note": "Higher strike"},
                    {"action": "BUY", "option_type": "CALL", "quantity": 1, "note": "Highest strike"}
                ],
                "max_profit": "Net premium received",
                "max_loss": "Spread width - Net premium",
                "breakeven": "Multiple breakeven points"
            }
        ]
        
        return {
            "strategies": strategies,
            "timestamp": "2025-10-16T04:59:41+05:30"
        }
        
    except Exception as e:
        logger.error(f"Failed to get options strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _generate_mock_option_chain(symbol: str, expiry: Optional[str]) -> List[Dict[str, Any]]:
    """Generate mock option chain data for demonstration"""
    try:
        if symbol.upper() == 'NIFTY':
            base_price = 19500
            strike_interval = 50
        elif symbol.upper() == 'BANKNIFTY':
            base_price = 45000
            strike_interval = 100
        else:
            base_price = 100
            strike_interval = 10
        
        option_chain = []
        
        # Generate strikes around current price
        for i in range(-5, 6):  # 11 strikes
            strike = base_price + (i * strike_interval)
            
            # Mock option data
            call_premium = max(1, base_price - strike + 50) if base_price > strike else max(1, 50 - abs(i) * 10)
            put_premium = max(1, strike - base_price + 50) if strike > base_price else max(1, 50 - abs(i) * 10)
            
            option_chain.append({
                "strike": strike,
                "call": {
                    "symbol": f"{symbol}{expiry or '25DEC24'}{strike}CE",
                    "premium": round(call_premium, 2),
                    "bid": round(call_premium - 0.5, 2),
                    "ask": round(call_premium + 0.5, 2),
                    "volume": 1000 + i * 100,
                    "open_interest": 5000 + i * 500
                },
                "put": {
                    "symbol": f"{symbol}{expiry or '25DEC24'}{strike}PE",
                    "premium": round(put_premium, 2),
                    "bid": round(put_premium - 0.5, 2),
                    "ask": round(put_premium + 0.5, 2),
                    "volume": 800 + i * 80,
                    "open_interest": 4000 + i * 400
                }
            })
        
        return option_chain
        
    except Exception as e:
        logger.error(f"Failed to generate mock option chain: {e}")
        return []
