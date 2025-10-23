# flake8: noqa: F401
# isort: off
from freqtrade.exchange.common import MAP_EXCHANGE_CHILDCLASS
from freqtrade.exchange.exchange import Exchange

# isort: on
from freqtrade.exchange.binance import Binance
from freqtrade.exchange.bingx import Bingx
from freqtrade.exchange.bitget import Bitget
from freqtrade.exchange.bitmart import Bitmart
from freqtrade.exchange.bitpanda import Bitpanda
from freqtrade.exchange.bitvavo import Bitvavo
from freqtrade.exchange.bybit import Bybit
from freqtrade.exchange.coinex import Coinex
from freqtrade.exchange.cryptocom import Cryptocom
from freqtrade.exchange.exchange_utils import (
    ROUND_DOWN,
    ROUND_UP,
    amount_to_contract_precision,
    amount_to_contracts,
    amount_to_precision,
    available_exchanges,
    ccxt_exchanges,
    contracts_to_amount,
    date_minus_candles,
    is_exchange_known_ccxt,
    list_available_exchanges,
    market_is_active,
    price_to_precision,
    validate_exchange,
)
from freqtrade.exchange.exchange_utils_timeframe import (
    timeframe_to_minutes,
    timeframe_to_msecs,
    timeframe_to_next_date,
    timeframe_to_prev_date,
    timeframe_to_resample_freq,
    timeframe_to_seconds,
)
from freqtrade.exchange.gate import Gate
from freqtrade.exchange.hitbtc import Hitbtc
from freqtrade.exchange.htx import Htx
from freqtrade.exchange.hyperliquid import Hyperliquid
from freqtrade.exchange.idex import Idex
from freqtrade.exchange.kraken import Kraken
from freqtrade.exchange.kucoin import Kucoin
from freqtrade.exchange.lbank import Lbank
from freqtrade.exchange.luno import Luno
from freqtrade.exchange.modetrade import Modetrade
from freqtrade.exchange.okx import MyOkx, Okx
from freqtrade.exchange.openalgo import Openalgo
from freqtrade.exchange.paperbroker import Paperbroker
from freqtrade.exchange.smartapi import Smartapi
from freqtrade.exchange.zerodha import Zerodha

# Indian broker utilities
from freqtrade.exchange.rate_limiter import RateLimiter, BrokerRateLimits
from freqtrade.exchange.lot_size_manager import LotSizeManager, NSELotSizeManager
from freqtrade.exchange.nse_calendar import NSECalendar, get_nse_calendar

# Register custom exchanges with the factory
from freqtrade.exchange.exchange_factory import register_custom_exchange

# Register all custom (non-CCXT) exchanges
register_custom_exchange('openalgo', Openalgo)
register_custom_exchange('paperbroker', Paperbroker)
register_custom_exchange('smartapi', Smartapi)
register_custom_exchange('zerodha', Zerodha)
