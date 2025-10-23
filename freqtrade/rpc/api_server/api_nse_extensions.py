"""
NSE-specific API Extensions for Mobile App and Advanced Features

Additional endpoints for:
- CSV data upload for backtesting
- NSE broker data fetching
- Paper broker controls
- Advanced analytics
- Market calendar
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from freqtrade.constants import Config
from freqtrade.exceptions import OperationalException
from freqtrade.exchange import get_nse_calendar
from freqtrade.rpc.api_server.api_auth import get_api_config
from freqtrade.rpc.api_server.deps import get_config, get_exchange

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/csv/upload", tags=["data"])
def upload_csv_data(
    file: UploadFile = File(...),
    pair: str = None,
    config: Config = Depends(get_config)
):
    """
    Upload CSV file for backtesting or paper trading.

    CSV Format:
    - Required columns: datetime, open, high, low, close, volume
    - datetime should be in ISO format or Unix timestamp

    Parameters:
    - file: CSV file to upload
    - pair: Trading pair name (e.g., RELIANCE/INR). If not specified, extracted from filename

    Returns:
    - Upload status and statistics
    """
    try:
        # Determine pair name
        if not pair:
            # Extract from filename: RELIANCE_1m.csv -> RELIANCE/INR
            pair_name = file.filename.replace('.csv', '').replace('_1m', '').replace('_minute', '').upper()
            pair = f"{pair_name}/INR"

        # Create raw_data directory
        user_data_dir = config.get('user_data_dir', 'user_data')
        raw_data_dir = Path(user_data_dir) / 'raw_data'
        raw_data_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = raw_data_dir / file.filename
        content = file.file.read()

        with open(file_path, 'wb') as f:
            f.write(content)

        # Validate CSV
        df = pd.read_csv(file_path)
        required_cols = ['datetime', 'open', 'high', 'low', 'close', 'volume']

        if not all(col in df.columns for col in required_cols):
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns. Required: {required_cols}, Found: {list(df.columns)}"
            )

        # Get statistics
        stats = {
            'pair': pair,
            'filename': file.filename,
            'rows': len(df),
            'columns': list(df.columns),
            'date_range': {
                'start': str(df['datetime'].iloc[0]),
                'end': str(df['datetime'].iloc[-1])
            },
            'price_range': {
                'min': float(df['close'].min()),
                'max': float(df['close'].max()),
                'current': float(df['close'].iloc[-1])
            },
            'volume': {
                'total': float(df['volume'].sum()),
                'average': float(df['volume'].mean())
            }
        }

        return {
            'status': 'success',
            'message': f'Uploaded {len(df)} candles for {pair}',
            'stats': stats,
            'file_path': str(file_path)
        }

    except Exception as e:
        logger.error(f"Failed to upload CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/csv/list", tags=["data"])
def list_csv_files(config: Config = Depends(get_config)):
    """
    List all uploaded CSV files.

    Returns:
    - List of CSV files with metadata
    """
    try:
        user_data_dir = config.get('user_data_dir', 'user_data')
        raw_data_dir = Path(user_data_dir) / 'raw_data'

        if not raw_data_dir.exists():
            return {'files': []}

        files = []
        for csv_file in raw_data_dir.glob('*.csv'):
            try:
                df = pd.read_csv(csv_file, nrows=1)
                files.append({
                    'filename': csv_file.name,
                    'size_bytes': csv_file.stat().st_size,
                    'modified': datetime.fromtimestamp(csv_file.stat().st_mtime).isoformat(),
                    'columns': list(df.columns)
                })
            except Exception as e:
                logger.warning(f"Failed to read {csv_file.name}: {e}")

        return {'files': files}

    except Exception as e:
        logger.error(f"Failed to list CSV files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/csv/{filename}", tags=["data"])
def delete_csv_file(filename: str, config: Config = Depends(get_config)):
    """
    Delete a CSV file.

    Parameters:
    - filename: Name of CSV file to delete

    Returns:
    - Deletion status
    """
    try:
        user_data_dir = config.get('user_data_dir', 'user_data')
        file_path = Path(user_data_dir) / 'raw_data' / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File {filename} not found")

        file_path.unlink()

        return {
            'status': 'success',
            'message': f'Deleted {filename}'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nse/calendar", tags=["nse"])
def get_calendar_info():
    """
    Get NSE market calendar information.

    Returns:
    - Market hours
    - Trading holidays
    - Current market status
    """
    try:
        calendar = get_nse_calendar()

        # Get upcoming holidays
        upcoming_holidays = calendar.get_upcoming_holidays(days=90)

        # Market status
        is_open = calendar.is_market_open()
        is_trading_day = calendar.is_trading_day()

        result = {
            'market_hours': {
                'open': str(calendar.MARKET_OPEN_TIME),
                'close': str(calendar.MARKET_CLOSE_TIME),
                'pre_market_open': str(calendar.PRE_MARKET_OPEN),
                'post_market_close': str(calendar.POST_MARKET_CLOSE)
            },
            'current_status': {
                'is_open': is_open,
                'is_trading_day': is_trading_day,
                'current_time': datetime.now().isoformat()
            },
            'upcoming_holidays': upcoming_holidays
        }

        # Add time until open/close
        if is_open:
            seconds_until_close = calendar.time_until_market_close()
            if seconds_until_close:
                result['current_status']['seconds_until_close'] = seconds_until_close
        else:
            seconds_until_open = calendar.time_until_market_open()
            if seconds_until_open:
                result['current_status']['seconds_until_open'] = seconds_until_open

        return result

    except Exception as e:
        logger.error(f"Failed to get calendar info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nse/calendar/holiday", tags=["nse"])
def add_custom_holiday(date: str):
    """
    Add a custom trading holiday.

    Parameters:
    - date: Date in YYYY-MM-DD format

    Returns:
    - Status
    """
    try:
        calendar = get_nse_calendar()
        calendar.add_holiday(date)

        return {
            'status': 'success',
            'message': f'Added holiday: {date}'
        }

    except Exception as e:
        logger.error(f"Failed to add holiday: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/paper/balance", tags=["paper"])
def get_paper_balance(exchange=Depends(get_exchange)):
    """
    Get paper broker balance and statistics.

    Returns:
    - Current balance
    - Initial balance
    - Profit/Loss
    - Trade statistics
    """
    try:
        if exchange.name.lower() != 'paperbroker':
            raise HTTPException(
                status_code=400,
                detail="This endpoint is only for paper broker"
            )

        balance = exchange.fetch_balance()

        # Calculate P&L
        initial_balance = getattr(exchange, '_initial_balance', 100000)
        current_balance = balance['INR']['total']
        pnl = current_balance - initial_balance
        pnl_percent = (pnl / initial_balance) * 100

        return {
            'initial_balance': initial_balance,
            'current_balance': current_balance,
            'free': balance['INR']['free'],
            'used': balance['INR']['used'],
            'profit_loss': {
                'absolute': pnl,
                'percent': pnl_percent
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get paper balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/paper/reset", tags=["paper"])
def reset_paper_broker(exchange=Depends(get_exchange)):
    """
    Reset paper broker to initial state.

    WARNING: This will clear all orders and reset balance!

    Returns:
    - Reset status
    """
    try:
        if exchange.name.lower() != 'paperbroker':
            raise HTTPException(
                status_code=400,
                detail="This endpoint is only for paper broker"
            )

        # Reset balance
        initial_balance = getattr(exchange, '_initial_balance', 100000)
        exchange._balance = {
            'INR': {
                'free': initial_balance,
                'used': 0.0,
                'total': initial_balance
            }
        }

        # Clear orders
        if hasattr(exchange, '_orders'):
            exchange._orders.clear()
        if hasattr(exchange, '_open_orders'):
            exchange._open_orders.clear()
        if hasattr(exchange, '_filled_orders'):
            exchange._filled_orders.clear()
        if hasattr(exchange, '_positions'):
            exchange._positions.clear()
        if hasattr(exchange, '_trade_history'):
            exchange._trade_history.clear()

        return {
            'status': 'success',
            'message': 'Paper broker reset to initial state',
            'balance': initial_balance
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset paper broker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/fetch_from_broker", tags=["data"])
def fetch_data_from_broker(
    pair: str,
    broker: str,
    timeframe: str = "1m",
    days: int = 30,
    config: Config = Depends(get_config)
):
    """
    Fetch historical data from NSE broker and save as CSV.

    Parameters:
    - pair: Trading pair (e.g., RELIANCE/INR)
    - broker: Broker name (openalgo, smartapi, zerodha)
    - timeframe: Candle timeframe (1m, 5m, 15m, 1h, 1d)
    - days: Number of days of history

    Returns:
    - Fetch status and saved file path
    """
    try:
        from datetime import timedelta
        from freqtrade.resolvers import ExchangeResolver

        # Create temporary config for the broker
        temp_config = config.copy()
        temp_config['exchange']['name'] = broker.lower()

        # Initialize broker
        try:
            broker_exchange = ExchangeResolver.load_exchange(temp_config, validate=False)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to initialize {broker}: {str(e)}"
            )

        # Fetch data
        since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

        try:
            ohlcv = broker_exchange.fetch_ohlcv(pair, timeframe, since=since)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch data from {broker}: {str(e)}"
            )

        if not ohlcv:
            raise HTTPException(
                status_code=404,
                detail=f"No data returned from {broker} for {pair}"
            )

        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Reorder columns
        df = df[['datetime', 'open', 'high', 'low', 'close', 'volume', 'timestamp']]

        # Save to CSV
        user_data_dir = config.get('user_data_dir', 'user_data')
        raw_data_dir = Path(user_data_dir) / 'raw_data'
        raw_data_dir.mkdir(parents=True, exist_ok=True)

        symbol = pair.split('/')[0]
        filename = f"{symbol}_{timeframe}.csv"
        file_path = raw_data_dir / filename

        df.to_csv(file_path, index=False)

        return {
            'status': 'success',
            'message': f'Fetched {len(df)} candles from {broker}',
            'pair': pair,
            'timeframe': timeframe,
            'candles': len(df),
            'date_range': {
                'start': str(df['datetime'].iloc[0]),
                'end': str(df['datetime'].iloc[-1])
            },
            'file_path': str(file_path),
            'filename': filename
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch data from broker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/summary", tags=["analytics"])
def get_analytics_summary(config: Config = Depends(get_config)):
    """
    Get comprehensive analytics summary.

    Returns:
    - System statistics
    - Performance metrics
    - Data availability
    """
    try:
        from freqtrade.persistence import Trade

        # Get trade statistics
        total_trades = Trade.get_trades([]).count() if hasattr(Trade, 'get_trades') else 0

        # Get data files
        user_data_dir = config.get('user_data_dir', 'user_data')
        raw_data_dir = Path(user_data_dir) / 'raw_data'

        csv_count = 0
        if raw_data_dir.exists():
            csv_count = len(list(raw_data_dir.glob('*.csv')))

        return {
            'trades': {
                'total': total_trades
            },
            'data_files': {
                'csv_files': csv_count
            },
            'exchange': {
                'name': config.get('exchange', {}).get('name', 'unknown')
            }
        }

    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
