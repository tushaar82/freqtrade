"""
Exchange Factory

Creates the appropriate exchange adapter based on configuration.
"""

import logging
from typing import Type

import ccxt

from freqtrade.exceptions import OperationalException
from freqtrade.exchange.ccxt_adapter import CCXTAdapter
from freqtrade.exchange.exchange_adapter import ExchangeAdapter


logger = logging.getLogger(__name__)


# Registry of custom (non-CCXT) exchanges
CUSTOM_EXCHANGES: dict[str, Type[ExchangeAdapter]] = {}


def register_custom_exchange(name: str, exchange_class: Type[ExchangeAdapter]):
    """
    Register a custom exchange.
    
    :param name: Exchange name (lowercase)
    :param exchange_class: Exchange class
    """
    CUSTOM_EXCHANGES[name.lower()] = exchange_class
    logger.info(f"Registered custom exchange: {name}")


def is_ccxt_exchange(exchange_name: str) -> bool:
    """
    Check if exchange is available in CCXT.
    
    :param exchange_name: Exchange name
    :return: True if exchange is in CCXT
    """
    return hasattr(ccxt, exchange_name.lower())


def is_custom_exchange(exchange_name: str) -> bool:
    """
    Check if exchange is a registered custom exchange.
    
    :param exchange_name: Exchange name
    :return: True if exchange is custom
    """
    return exchange_name.lower() in CUSTOM_EXCHANGES


def create_exchange(config: dict) -> ExchangeAdapter:
    """
    Create an exchange adapter based on configuration.
    
    This is the main factory method. It determines whether to use:
    1. A custom exchange (if registered)
    2. A CCXT exchange (if available in CCXT)
    3. Raises error if neither is available
    
    :param config: Freqtrade configuration
    :return: Exchange adapter instance
    :raises OperationalException: If exchange is not supported
    """
    exchange_name = config.get('exchange', {}).get('name', '').lower()
    
    if not exchange_name:
        raise OperationalException(
            "No exchange specified in configuration"
        )
    
    # Check if it's a custom exchange first
    if is_custom_exchange(exchange_name):
        exchange_class = CUSTOM_EXCHANGES[exchange_name]
        logger.info(f"Creating custom exchange: {exchange_name}")
        return exchange_class(config)
    
    # Check if it's a CCXT exchange
    if is_ccxt_exchange(exchange_name):
        logger.info(f"Creating CCXT exchange: {exchange_name}")
        return CCXTAdapter(config)
    
    # Exchange not found
    available_custom = ", ".join(CUSTOM_EXCHANGES.keys())
    raise OperationalException(
        f"Exchange '{exchange_name}' is not supported.\n"
        f"Custom exchanges available: {available_custom}\n"
        f"Or use any CCXT-supported exchange."
    )


def list_available_exchanges() -> dict[str, list[str]]:
    """
    List all available exchanges.
    
    :return: Dictionary with 'custom' and 'ccxt' exchange lists
    """
    custom = list(CUSTOM_EXCHANGES.keys())
    ccxt_exchanges = ccxt.exchanges if hasattr(ccxt, 'exchanges') else []
    
    return {
        'custom': sorted(custom),
        'ccxt': sorted(ccxt_exchanges),
        'all': sorted(custom + ccxt_exchanges)
    }


def get_exchange_info(exchange_name: str) -> dict:
    """
    Get information about an exchange.
    
    :param exchange_name: Exchange name
    :return: Exchange information
    """
    exchange_name = exchange_name.lower()
    
    info = {
        'name': exchange_name,
        'type': None,
        'available': False,
        'class': None,
    }
    
    if is_custom_exchange(exchange_name):
        info['type'] = 'custom'
        info['available'] = True
        info['class'] = CUSTOM_EXCHANGES[exchange_name].__name__
    elif is_ccxt_exchange(exchange_name):
        info['type'] = 'ccxt'
        info['available'] = True
        info['class'] = 'CCXTAdapter'
    
    return info
