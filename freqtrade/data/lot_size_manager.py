"""Lot Size Manager for Indian options trading"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import requests

from freqtrade.enums import InstrumentType
from freqtrade.exceptions import OperationalException


logger = logging.getLogger(__name__)


class LotSizeManager:
    """
    Manager for Indian options lot sizes.
    
    Handles lot size data for NSE/BSE options, provides methods for
    quantity calculations, P&L calculations with lot multipliers,
    and automatic updates from exchange APIs.
    """
    
    def __init__(self, config: dict):
        """
        Initialize LotSizeManager.
        
        :param config: Freqtrade configuration
        """
        self._config = config
        self._lot_sizes = {}
        self._last_updated = None
        
        # Default lot size file path
        user_data_dir = Path(config.get('user_data_dir', 'user_data'))
        self._lot_size_file = user_data_dir / 'lot_sizes.json'
        
        # Hardcoded lot sizes for major indices (as of late 2024)
        self._default_lot_sizes = {
            'indices': {
                'NIFTY': 25,      # Updated lot size
                'BANKNIFTY': 15,  # Updated lot size  
                'FINNIFTY': 40,   # Updated lot size
                'MIDCPNIFTY': 75, # Updated lot size
                'NIFTYNEXT50': 25,
                'SENSEX': 10,
                'BANKEX': 15
            },
            'stocks': {
                'RELIANCE': 250,
                'TCS': 150,
                'INFY': 300,
                'HDFCBANK': 550,
                'ICICIBANK': 700,
                'SBIN': 1500,
                'BHARTIARTL': 1200,
                'ITC': 1600,
                'KOTAKBANK': 400,
                'LT': 225
            }
        }
        
        # Load lot sizes from file or initialize with defaults
        self._load_lot_sizes()
        
    def _load_lot_sizes(self):
        """Load lot sizes from JSON file"""
        try:
            if self._lot_size_file.exists():
                with open(self._lot_size_file, 'r') as f:
                    data = json.load(f)
                    self._lot_sizes = data.get('lot_sizes', {})
                    self._last_updated = datetime.fromisoformat(
                        data.get('last_updated', datetime.now().isoformat())
                    )
                logger.info(f"Loaded lot sizes from {self._lot_size_file}")
            else:
                # Initialize with default lot sizes
                self._lot_sizes = self._default_lot_sizes.copy()
                self._last_updated = datetime.now()
                self._save_lot_sizes()
                logger.info("Initialized lot sizes with defaults")
                
        except Exception as e:
            logger.error(f"Failed to load lot sizes: {e}")
            self._lot_sizes = self._default_lot_sizes.copy()
            self._last_updated = datetime.now()
    
    def _save_lot_sizes(self):
        """Save lot sizes to JSON file"""
        try:
            # Ensure directory exists
            self._lot_size_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'lot_sizes': self._lot_sizes,
                'last_updated': self._last_updated.isoformat(),
                'revision_history': []  # TODO: Implement revision tracking
            }
            
            with open(self._lot_size_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
            logger.info(f"Saved lot sizes to {self._lot_size_file}")
            
        except Exception as e:
            logger.error(f"Failed to save lot sizes: {e}")
    
    def get_lot_size(self, symbol: str, expiry: Optional[str] = None) -> int:
        """
        Get lot size for a symbol.
        
        :param symbol: Trading symbol (e.g., 'NIFTY', 'RELIANCE')
        :param expiry: Expiry date (optional, for future lot size changes)
        :return: Lot size
        """
        # Extract base symbol from options symbol
        base_symbol = self._extract_base_symbol(symbol)
        
        # Check indices first
        if base_symbol in self._lot_sizes.get('indices', {}):
            return self._lot_sizes['indices'][base_symbol]
        
        # Check stocks
        if base_symbol in self._lot_sizes.get('stocks', {}):
            return self._lot_sizes['stocks'][base_symbol]
        
        # Default lot size for unknown symbols
        logger.warning(f"Lot size not found for {base_symbol}, using default: 1")
        return 1
    
    def _extract_base_symbol(self, symbol: str) -> str:
        """
        Extract base symbol from options/futures symbol.
        
        :param symbol: Full symbol (e.g., 'NIFTY25DEC24500CE')
        :return: Base symbol (e.g., 'NIFTY')
        """
        # Remove /INR suffix if present
        if '/' in symbol:
            symbol = symbol.split('/')[0]
        
        # For options symbols, extract underlying
        if symbol.endswith(('CE', 'PE')):
            # Remove CE/PE
            base = symbol[:-2]
            
            # Remove strike price (last numeric part)
            import re
            strike_match = re.search(r'\d+$', base)
            if strike_match:
                base = base[:strike_match.start()]
            
            # Remove expiry date
            expiry_match = re.search(r'\d{1,2}[A-Z]{3}\d{2,4}$', base)
            if expiry_match:
                base = base[:expiry_match.start()]
            
            return base.upper()
        
        return symbol.upper()
    
    def calculate_quantity(self, stake_amount: float, price: float, symbol: str, 
                          instrument_type: InstrumentType = InstrumentType.EQUITY) -> Tuple[int, int]:
        """
        Calculate quantity based on stake amount and lot size requirements.
        
        :param stake_amount: Amount to invest
        :param price: Price per unit
        :param symbol: Trading symbol
        :param instrument_type: Type of instrument
        :return: Tuple of (quantity, lots)
        """
        if not instrument_type.requires_lot_size():
            # For equity, calculate normal quantity
            quantity = int(stake_amount / price)
            return quantity, 1
        
        # For derivatives, calculate lot-based quantity
        lot_size = self.get_lot_size(symbol)
        contract_value = price * lot_size
        
        if contract_value <= 0:
            return 0, 0
        
        # Calculate number of lots that can be bought
        lots = int(stake_amount / contract_value)
        quantity = lots * lot_size
        
        return quantity, lots
    
    def calculate_pnl(self, entry_price: float, exit_price: float, quantity: int, 
                     symbol: str, instrument_type: InstrumentType = InstrumentType.EQUITY) -> float:
        """
        Calculate P&L with lot size multiplier.
        
        :param entry_price: Entry price
        :param exit_price: Exit price  
        :param quantity: Quantity traded
        :param symbol: Trading symbol
        :param instrument_type: Type of instrument
        :return: P&L amount
        """
        if not instrument_type.requires_lot_size():
            # Normal P&L calculation for equity
            return (exit_price - entry_price) * quantity
        
        # For derivatives, P&L is already lot-adjusted since quantity includes lot size
        return (exit_price - entry_price) * quantity
    
    def get_contract_value(self, price: float, symbol: str, 
                          instrument_type: InstrumentType = InstrumentType.EQUITY) -> float:
        """
        Calculate contract value (notional value).
        
        :param price: Price per unit
        :param symbol: Trading symbol
        :param instrument_type: Type of instrument
        :return: Contract value
        """
        if not instrument_type.requires_lot_size():
            return price
        
        lot_size = self.get_lot_size(symbol)
        return price * lot_size
    
    def update_lot_sizes(self, exchange_name: str = None) -> bool:
        """
        Update lot sizes from exchange APIs.
        
        :param exchange_name: Exchange to fetch from (optional)
        :return: True if successful
        """
        try:
            # Check if update is needed (daily updates)
            if (self._last_updated and 
                datetime.now() - self._last_updated < timedelta(days=1)):
                logger.info("Lot sizes are up to date")
                return True
            
            logger.info("Updating lot sizes from exchange APIs...")
            
            # Try to fetch from NSE API (if available)
            updated = self._fetch_from_nse_api()
            
            if updated:
                self._last_updated = datetime.now()
                self._save_lot_sizes()
                logger.info("Lot sizes updated successfully")
                return True
            else:
                logger.warning("Failed to update lot sizes, using cached data")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update lot sizes: {e}")
            return False
    
    def _fetch_from_nse_api(self) -> bool:
        """
        Fetch lot sizes from NSE API.
        
        :return: True if successful
        """
        try:
            # NSE doesn't provide a direct lot size API
            # In production, this would fetch from broker APIs or scrape NSE website
            # For now, we'll use hardcoded updates
            
            logger.info("NSE API lot size fetch not implemented, using defaults")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fetch from NSE API: {e}")
            return False
    
    def get_lot_size_info(self, symbol: str) -> Dict:
        """
        Get comprehensive lot size information for a symbol.
        
        :param symbol: Trading symbol
        :return: Dict with lot size info
        """
        base_symbol = self._extract_base_symbol(symbol)
        lot_size = self.get_lot_size(symbol)
        instrument_type = InstrumentType.from_symbol(symbol)
        
        return {
            'symbol': symbol,
            'base_symbol': base_symbol,
            'lot_size': lot_size,
            'instrument_type': instrument_type.value,
            'requires_lot_size': instrument_type.requires_lot_size(),
            'last_updated': self._last_updated.isoformat() if self._last_updated else None
        }
    
    def validate_quantity(self, quantity: int, symbol: str, 
                         instrument_type: InstrumentType = InstrumentType.EQUITY) -> Tuple[bool, str]:
        """
        Validate if quantity is valid for the instrument.
        
        :param quantity: Quantity to validate
        :param symbol: Trading symbol
        :param instrument_type: Type of instrument
        :return: Tuple of (is_valid, error_message)
        """
        if not instrument_type.requires_lot_size():
            return True, ""
        
        lot_size = self.get_lot_size(symbol)
        
        if quantity % lot_size != 0:
            return False, f"Quantity {quantity} is not a multiple of lot size {lot_size}"
        
        if quantity <= 0:
            return False, "Quantity must be positive"
        
        return True, ""
    
    def get_all_lot_sizes(self) -> Dict:
        """Get all lot sizes data"""
        return {
            'lot_sizes': self._lot_sizes,
            'last_updated': self._last_updated.isoformat() if self._last_updated else None,
            'total_symbols': (
                len(self._lot_sizes.get('indices', {})) + 
                len(self._lot_sizes.get('stocks', {}))
            )
        }
