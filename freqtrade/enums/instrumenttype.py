"""Instrument type enum for classifying trading instruments"""

from enum import Enum


class InstrumentType(str, Enum):
    """
    Enum for different types of trading instruments.
    
    Used to classify instruments and apply appropriate trading logic,
    lot size calculations, and risk management rules.
    """
    
    EQUITY = "EQUITY"
    FUTURES = "FUTURES"
    CALL_OPTION = "CALL_OPTION"
    PUT_OPTION = "PUT_OPTION"
    INDEX = "INDEX"
    
    def __str__(self):
        return self.value
    
    @classmethod
    def from_symbol(cls, symbol: str) -> 'InstrumentType':
        """
        Determine instrument type from symbol.
        
        :param symbol: Trading symbol
        :return: InstrumentType
        """
        symbol_upper = symbol.upper()
        
        # Check for options
        if symbol_upper.endswith('CE'):
            return cls.CALL_OPTION
        elif symbol_upper.endswith('PE'):
            return cls.PUT_OPTION
        
        # Check for futures (typically contain FUT or expiry dates)
        if 'FUT' in symbol_upper or any(month in symbol_upper for month in 
                                       ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                                        'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']):
            return cls.FUTURES
        
        # Check for indices
        if any(index in symbol_upper for index in 
               ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX']):
            return cls.INDEX
        
        # Default to equity
        return cls.EQUITY
    
    def is_options(self) -> bool:
        """Check if instrument is an options contract"""
        return self in (self.CALL_OPTION, self.PUT_OPTION)
    
    def is_derivative(self) -> bool:
        """Check if instrument is a derivative (futures or options)"""
        return self in (self.FUTURES, self.CALL_OPTION, self.PUT_OPTION)
    
    def requires_lot_size(self) -> bool:
        """Check if instrument requires lot size calculations"""
        return self.is_derivative()
