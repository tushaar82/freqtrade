"""
Symbol Mapper - Universal symbol conversion for different brokers/exchanges.

This module provides centralized symbol mapping between Freqtrade's internal format
and various broker-specific formats (OpenAlgo, SmartAPI, Paper Broker, etc.).

Features:
- Bidirectional symbol conversion
- Support for multiple brokers
- Configurable symbol mappings
- Options symbol parsing
- Token lookup for brokers that require it
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class SymbolMapper:
    """
    Universal symbol mapper for converting between Freqtrade format and broker-specific formats.
    
    Freqtrade Format: SYMBOL/QUOTE (e.g., "RELIANCE/INR", "NIFTY50/INR")
    
    Broker Formats:
    - OpenAlgo: symbol + exchange (e.g., "RELIANCE" on "NSE")
    - SmartAPI: trading_symbol + token + exchange (e.g., "RELIANCE-EQ", "3045", "NSE")
    - Paper Broker: Same as Freqtrade format
    """
    
    # Default symbol mappings (can be overridden by config file)
    DEFAULT_MAPPINGS = {
        "NIFTY50": {
            "openalgo": {"symbol": "NIFTY 50", "exchange": "NSE"},
            "smartapi": {"symbol": "NIFTY 50", "token": "99926000", "exchange": "NSE"},
            "paperbroker": {"symbol": "NIFTY50"},
        },
        "BANKNIFTY": {
            "openalgo": {"symbol": "NIFTY BANK", "exchange": "NSE"},
            "smartapi": {"symbol": "NIFTY BANK", "token": "99926009", "exchange": "NSE"},
            "paperbroker": {"symbol": "BANKNIFTY"},
        },
        "FINNIFTY": {
            "openalgo": {"symbol": "NIFTY FIN SERVICE", "exchange": "NSE"},
            "smartapi": {"symbol": "NIFTY FIN SERVICE", "token": "99926037", "exchange": "NSE"},
            "paperbroker": {"symbol": "FINNIFTY"},
        },
        "MIDCPNIFTY": {
            "openalgo": {"symbol": "NIFTY MID SELECT", "exchange": "NSE"},
            "smartapi": {"symbol": "NIFTY MID SELECT", "token": "99926074", "exchange": "NSE"},
            "paperbroker": {"symbol": "MIDCPNIFTY"},
        },
    }
    
    # Exchange suffixes for SmartAPI
    SMARTAPI_SUFFIXES = {
        "NSE": "-EQ",  # Equity
        "BSE": "-EQ",
        "NFO": "",     # Futures & Options (no suffix)
        "MCX": "",     # Commodities
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize symbol mapper.
        
        :param config_path: Path to custom symbol mapping config file (JSON)
        """
        self.mappings: Dict[str, Dict] = self.DEFAULT_MAPPINGS.copy()
        self.reverse_mappings: Dict[str, Dict] = {}
        
        # Load custom mappings if provided
        if config_path:
            self.load_mappings(config_path)
        
        # Build reverse mappings for quick lookup
        self._build_reverse_mappings()
    
    def load_mappings(self, config_path: str):
        """Load custom symbol mappings from JSON file."""
        try:
            path = Path(config_path)
            if path.exists():
                with open(path, 'r') as f:
                    custom_mappings = json.load(f)
                    self.mappings.update(custom_mappings)
                    logger.info(f"Loaded {len(custom_mappings)} custom symbol mappings from {config_path}")
            else:
                logger.warning(f"Symbol mapping file not found: {config_path}")
        except Exception as e:
            logger.error(f"Error loading symbol mappings: {e}")
    
    def _build_reverse_mappings(self):
        """Build reverse mappings for broker -> freqtrade conversion."""
        self.reverse_mappings = {
            'openalgo': {},
            'smartapi': {},
            'paperbroker': {},
        }
        
        for freqtrade_symbol, broker_mappings in self.mappings.items():
            for broker, mapping in broker_mappings.items():
                if broker in self.reverse_mappings:
                    key = mapping.get('symbol', freqtrade_symbol)
                    self.reverse_mappings[broker][key] = freqtrade_symbol
    
    def to_broker_format(self, pair: str, broker: str, default_exchange: str = "NSE") -> Tuple:
        """
        Convert Freqtrade pair to broker-specific format.
        
        :param pair: Freqtrade pair (e.g., "RELIANCE/INR")
        :param broker: Broker name ("openalgo", "smartapi", "paperbroker")
        :param default_exchange: Default exchange if not specified
        :return: Tuple with broker-specific format
        """
        # Extract base symbol and quote currency
        parts = pair.split('/')
        base_symbol = parts[0]
        quote_currency = parts[1] if len(parts) > 1 else "INR"
        
        # Check if we have a custom mapping
        if base_symbol in self.mappings and broker in self.mappings[base_symbol]:
            mapping = self.mappings[base_symbol][broker]
            
            if broker == "openalgo":
                return (
                    mapping.get('symbol', base_symbol),
                    mapping.get('exchange', default_exchange)
                )
            elif broker == "smartapi":
                return (
                    mapping.get('symbol', base_symbol),
                    mapping.get('token', '0'),
                    mapping.get('exchange', default_exchange)
                )
            elif broker == "paperbroker":
                return (mapping.get('symbol', base_symbol), quote_currency)
        
        # No custom mapping, use default conversion
        return self._default_conversion(base_symbol, quote_currency, broker, default_exchange)
    
    def _default_conversion(self, symbol: str, quote: str, broker: str, exchange: str) -> Tuple:
        """Default conversion when no custom mapping exists."""
        if broker == "openalgo":
            return (symbol, exchange)
        
        elif broker == "smartapi":
            # Add exchange suffix for SmartAPI
            suffix = self.SMARTAPI_SUFFIXES.get(exchange, "-EQ")
            trading_symbol = f"{symbol}{suffix}" if suffix else symbol
            return (trading_symbol, "0", exchange)  # Token needs to be looked up
        
        elif broker == "paperbroker":
            return (symbol, quote)
        
        return (symbol,)
    
    def from_broker_format(self, broker: str, *args, quote_currency: str = "INR") -> str:
        """
        Convert broker-specific format to Freqtrade pair.
        
        :param broker: Broker name
        :param args: Broker-specific arguments (symbol, exchange, token, etc.)
        :param quote_currency: Quote currency (default: INR)
        :return: Freqtrade pair format
        """
        if broker == "openalgo":
            symbol, exchange = args[0], args[1] if len(args) > 1 else "NSE"
        elif broker == "smartapi":
            symbol = args[0]
            # Remove SmartAPI suffix
            for suffix in self.SMARTAPI_SUFFIXES.values():
                if suffix and symbol.endswith(suffix):
                    symbol = symbol[:-len(suffix)]
                    break
        else:
            symbol = args[0]
        
        # Check reverse mapping
        if broker in self.reverse_mappings and symbol in self.reverse_mappings[broker]:
            symbol = self.reverse_mappings[broker][symbol]
        
        return f"{symbol}/{quote_currency}"
    
    def parse_options_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Parse options symbol to extract components.
        
        Supports formats like:
        - NIFTY25DEC24500CE
        - BANKNIFTY2024DEC2550000PE
        
        :param symbol: Options symbol
        :return: Dict with strike, expiry, option_type, underlying
        """
        if not symbol.endswith(('CE', 'PE')):
            return None
        
        try:
            # Extract option type
            option_type = 'CALL' if symbol.endswith('CE') else 'PUT'
            base_symbol = symbol[:-2]
            
            # Extract strike price (last numeric part)
            strike_match = re.search(r'(\d+)$', base_symbol)
            if not strike_match:
                return None
            
            strike_price = float(strike_match.group(1))
            symbol_without_strike = base_symbol[:strike_match.start()]
            
            # Extract expiry date
            expiry_match = re.search(
                r'(\d{1,2}[A-Z]{3}\d{2,4}|\d{4}[A-Z]{3}\d{1,2})$',
                symbol_without_strike
            )
            
            if expiry_match:
                expiry_str = expiry_match.group(1)
                underlying = symbol_without_strike[:expiry_match.start()]
            else:
                underlying = symbol_without_strike
                expiry_str = None
            
            return {
                'underlying': underlying,
                'strike': strike_price,
                'option_type': option_type,
                'expiry': expiry_str,
                'original': symbol
            }
        
        except Exception as e:
            logger.error(f"Error parsing options symbol {symbol}: {e}")
            return None
    
    def add_mapping(self, freqtrade_symbol: str, broker: str, mapping: Dict):
        """
        Add or update a symbol mapping.
        
        :param freqtrade_symbol: Freqtrade symbol (e.g., "RELIANCE")
        :param broker: Broker name
        :param mapping: Broker-specific mapping dict
        """
        if freqtrade_symbol not in self.mappings:
            self.mappings[freqtrade_symbol] = {}
        
        self.mappings[freqtrade_symbol][broker] = mapping
        self._build_reverse_mappings()
    
    def save_mappings(self, config_path: str):
        """Save current mappings to JSON file."""
        try:
            path = Path(config_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                json.dump(self.mappings, f, indent=2)
            
            logger.info(f"Saved symbol mappings to {config_path}")
        except Exception as e:
            logger.error(f"Error saving symbol mappings: {e}")


# Global instance
_mapper_instance: Optional[SymbolMapper] = None


def get_symbol_mapper(config_path: Optional[str] = None) -> SymbolMapper:
    """Get or create global symbol mapper instance."""
    global _mapper_instance
    
    if _mapper_instance is None:
        _mapper_instance = SymbolMapper(config_path)
    
    return _mapper_instance
