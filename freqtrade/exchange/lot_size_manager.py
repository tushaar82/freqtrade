"""
Lot Size Manager for Indian F&O Trading

Manages lot sizes for Indian futures and options contracts.
Provides utilities to fetch, cache, and validate lot sizes for NSE/NFO instruments.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import json
import os

logger = logging.getLogger(__name__)


class LotSizeManager:
    """
    Manager for Indian F&O lot sizes.

    Handles:
    - Lot size lookup for options and futures
    - Caching of lot size data
    - Validation of order quantities
    - Automatic lot size adjustments
    """

    # Default lot sizes for common indices (as of 2024)
    DEFAULT_LOT_SIZES = {
        'NIFTY': 25,
        'BANKNIFTY': 15,
        'FINNIFTY': 25,
        'MIDCPNIFTY': 50,
        'NIFTYIT': 25,
        'SENSEX': 10,
        'BANKEX': 15,
    }

    def __init__(self, cache_file: Optional[str] = None, cache_ttl: int = 86400):
        """
        Initialize lot size manager.

        :param cache_file: Path to cache file for lot sizes
        :param cache_ttl: Cache time-to-live in seconds (default 24 hours)
        """
        self._lot_sizes: Dict[str, int] = {}
        self._cache_file = cache_file or os.path.expanduser('~/.freqtrade_lot_sizes.json')
        self._cache_ttl = cache_ttl
        self._last_update: Optional[datetime] = None

        # Load default lot sizes
        self._lot_sizes.update(self.DEFAULT_LOT_SIZES)

        # Load from cache if available
        self._load_cache()

        logger.info(f"Lot size manager initialized with {len(self._lot_sizes)} instruments")

    def get_lot_size(self, symbol: str) -> int:
        """
        Get lot size for a symbol.

        :param symbol: Trading symbol (e.g., 'NIFTY25DEC24500CE', 'RELIANCE')
        :return: Lot size (1 for equity, actual lot size for F&O)
        """
        # Extract underlying from options/futures symbol
        underlying = self._extract_underlying(symbol)

        # Check cache
        if underlying in self._lot_sizes:
            return self._lot_sizes[underlying]

        # Check if it's a derivative
        if self._is_derivative(symbol):
            # Try without -EQ suffix if present
            clean_symbol = underlying.replace('-EQ', '')
            if clean_symbol in self._lot_sizes:
                return self._lot_sizes[clean_symbol]

            logger.warning(f"Lot size not found for {symbol}, using default 1")
            return 1

        # Equity instruments have lot size 1
        return 1

    def set_lot_size(self, underlying: str, lot_size: int):
        """
        Set lot size for an underlying.

        :param underlying: Underlying symbol (e.g., 'NIFTY', 'RELIANCE')
        :param lot_size: Lot size
        """
        self._lot_sizes[underlying] = lot_size
        logger.debug(f"Set lot size for {underlying}: {lot_size}")

    def update_lot_sizes(self, lot_size_dict: Dict[str, int]):
        """
        Update multiple lot sizes at once.

        :param lot_size_dict: Dictionary of symbol -> lot_size
        """
        self._lot_sizes.update(lot_size_dict)
        self._last_update = datetime.now()
        self._save_cache()
        logger.info(f"Updated {len(lot_size_dict)} lot sizes")

    def validate_quantity(self, symbol: str, quantity: float) -> bool:
        """
        Validate if quantity is a valid multiple of lot size.

        :param symbol: Trading symbol
        :param quantity: Order quantity
        :return: True if valid
        """
        lot_size = self.get_lot_size(symbol)
        return quantity % lot_size == 0

    def adjust_quantity_to_lot(self, symbol: str, quantity: float, round_up: bool = False) -> int:
        """
        Adjust quantity to nearest lot multiple.

        :param symbol: Trading symbol
        :param quantity: Desired quantity
        :param round_up: If True, round up; otherwise round down
        :return: Adjusted quantity
        """
        lot_size = self.get_lot_size(symbol)

        if lot_size == 1:
            return int(quantity)

        if round_up:
            lots = int((quantity + lot_size - 1) / lot_size)
        else:
            lots = int(quantity / lot_size)

        adjusted = lots * lot_size

        if adjusted != quantity:
            logger.info(f"Adjusted quantity for {symbol} from {quantity} to {adjusted} "
                       f"(lot size: {lot_size})")

        return adjusted

    def get_lot_count(self, symbol: str, quantity: float) -> int:
        """
        Get number of lots for a given quantity.

        :param symbol: Trading symbol
        :param quantity: Quantity
        :return: Number of lots
        """
        lot_size = self.get_lot_size(symbol)
        return int(quantity / lot_size)

    def _extract_underlying(self, symbol: str) -> str:
        """
        Extract underlying from options/futures symbol.

        :param symbol: Full symbol (e.g., 'NIFTY25DEC24500CE', 'RELIANCE-EQ')
        :return: Underlying symbol
        """
        # Remove /INR or other quote currencies
        if '/' in symbol:
            symbol = symbol.split('/')[0]

        # Handle options symbols
        if symbol.endswith(('CE', 'PE')):
            # Remove CE/PE
            base = symbol[:-2]

            # Remove strike price (last numeric part)
            import re
            match = re.search(r'(\d+)$', base)
            if match:
                base = base[:match.start()]

            # Remove expiry date
            # Try different formats: 25DEC24, 2024DEC25, DEC24, etc.
            patterns = [
                r'\d{1,2}[A-Z]{3}\d{2,4}$',  # 25DEC24 or 2024DEC25
                r'[A-Z]{3}\d{2}$',            # DEC24
                r'\d{4}[A-Z]{3}\d{1,2}$',     # 2024DEC25
            ]

            for pattern in patterns:
                match = re.search(pattern, base)
                if match:
                    base = base[:match.start()]
                    break

            return base

        # Handle futures symbols
        if 'FUT' in symbol.upper():
            return symbol.split('FUT')[0]

        # Return as-is for equity
        return symbol

    def _is_derivative(self, symbol: str) -> bool:
        """Check if symbol is a derivative"""
        return (symbol.endswith(('CE', 'PE')) or
                'FUT' in symbol.upper() or
                any(month in symbol.upper() for month in
                    ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                     'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']))

    def _load_cache(self):
        """Load lot sizes from cache file"""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r') as f:
                    data = json.load(f)

                # Check if cache is still valid
                cache_time = datetime.fromisoformat(data.get('timestamp', '2000-01-01'))
                if datetime.now() - cache_time < timedelta(seconds=self._cache_ttl):
                    self._lot_sizes.update(data.get('lot_sizes', {}))
                    self._last_update = cache_time
                    logger.info(f"Loaded {len(data.get('lot_sizes', {}))} lot sizes from cache")
                else:
                    logger.info("Cache expired, using defaults")
        except Exception as e:
            logger.warning(f"Failed to load lot size cache: {e}")

    def _save_cache(self):
        """Save lot sizes to cache file"""
        try:
            data = {
                'timestamp': (self._last_update or datetime.now()).isoformat(),
                'lot_sizes': self._lot_sizes,
            }

            with open(self._cache_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug("Saved lot sizes to cache")
        except Exception as e:
            logger.warning(f"Failed to save lot size cache: {e}")

    def clear_cache(self):
        """Clear lot size cache"""
        self._lot_sizes = self.DEFAULT_LOT_SIZES.copy()
        self._last_update = None
        try:
            if os.path.exists(self._cache_file):
                os.remove(self._cache_file)
            logger.info("Cleared lot size cache")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")


class NSELotSizeManager(LotSizeManager):
    """
    NSE-specific lot size manager with support for loading from NSE master data.
    """

    def __init__(self, master_file: Optional[str] = None, **kwargs):
        """
        Initialize NSE lot size manager.

        :param master_file: Path to NSE master CSV file
        """
        super().__init__(**kwargs)
        self._master_file = master_file

        if master_file and os.path.exists(master_file):
            self._load_from_master()

    def _load_from_master(self):
        """Load lot sizes from NSE master file (CSV format)"""
        try:
            import csv

            with open(self._master_file, 'r') as f:
                reader = csv.DictReader(f)
                count = 0

                for row in reader:
                    # Extract relevant fields
                    # Adjust field names based on actual NSE master format
                    symbol = row.get('symbol', row.get('SYMBOL', ''))
                    lot_size = row.get('lot_size', row.get('LOT_SIZE', '1'))

                    if symbol and lot_size:
                        try:
                            self.set_lot_size(symbol, int(lot_size))
                            count += 1
                        except ValueError:
                            pass

                logger.info(f"Loaded {count} lot sizes from NSE master file")
                self._save_cache()

        except Exception as e:
            logger.error(f"Failed to load NSE master file: {e}")

    def refresh_from_nse(self):
        """
        Refresh lot sizes from NSE (placeholder for future implementation).

        In production, this would download the latest master file from NSE.
        """
        logger.warning("NSE refresh not implemented - using cached data")
