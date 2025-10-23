"""
NSE Trading Calendar

Provides utilities to check NSE market hours and trading holidays.
"""

import logging
from datetime import datetime, time as dt_time
from typing import List, Optional, Set

logger = logging.getLogger(__name__)


class NSECalendar:
    """
    NSE (National Stock Exchange of India) trading calendar.

    Handles:
    - Market hours validation
    - Trading holidays
    - Weekend detection
    - Special trading sessions
    """

    # NSE Regular Market Hours (IST)
    MARKET_OPEN_TIME = dt_time(9, 15)  # 09:15 AM
    MARKET_CLOSE_TIME = dt_time(15, 30)  # 03:30 PM

    # Pre-market session (optional)
    PRE_MARKET_OPEN = dt_time(9, 0)  # 09:00 AM
    PRE_MARKET_CLOSE = dt_time(9, 15)  # 09:15 AM

    # Post-market session (optional)
    POST_MARKET_OPEN = dt_time(15, 40)  # 03:40 PM
    POST_MARKET_CLOSE = dt_time(16, 0)  # 04:00 PM

    # NSE Trading Holidays 2024-2025 (update annually)
    # Format: 'YYYY-MM-DD'
    HOLIDAYS_2024 = {
        '2024-01-26',  # Republic Day
        '2024-03-08',  # Maha Shivratri
        '2024-03-25',  # Holi
        '2024-03-29',  # Good Friday
        '2024-04-11',  # Id-Ul-Fitr (Ramadan Eid)
        '2024-04-17',  # Ram Navami
        '2024-04-21',  # Mahavir Jayanti
        '2024-05-01',  # Maharashtra Day
        '2024-05-20',  # Buddha Pournima
        '2024-06-17',  # Bakri Id
        '2024-07-17',  # Moharram
        '2024-08-15',  # Independence Day
        '2024-08-26',  # Janmashtami
        '2024-10-02',  # Mahatma Gandhi Jayanti
        '2024-10-12',  # Dussehra
        '2024-10-31',  # Diwali-Laxmi Pujan
        '2024-11-01',  # Diwali-Balipratipada
        '2024-11-15',  # Guru Nanak Jayanti
        '2024-12-25',  # Christmas
    }

    HOLIDAYS_2025 = {
        '2025-01-26',  # Republic Day
        '2025-02-26',  # Maha Shivratri
        '2025-03-14',  # Holi
        '2025-03-31',  # Id-Ul-Fitr (Ramadan Eid)
        '2025-04-06',  # Ram Navami
        '2025-04-10',  # Mahavir Jayanti
        '2025-04-14',  # Dr. Ambedkar Jayanti / Mahavir Jayanti
        '2025-04-18',  # Good Friday
        '2025-05-01',  # Maharashtra Day
        '2025-05-12',  # Buddha Pournima
        '2025-06-07',  # Bakri Id
        '2025-08-15',  # Independence Day
        '2025-08-16',  # Parsi New Year
        '2025-08-26',  # Janmashtami
        '2025-10-02',  # Mahatma Gandhi Jayanti
        '2025-10-02',  # Dussehra
        '2025-10-20',  # Diwali-Laxmi Pujan
        '2025-10-21',  # Diwali-Balipratipada
        '2025-11-05',  # Guru Nanak Jayanti
        '2025-12-25',  # Christmas
    }

    def __init__(self):
        """Initialize NSE calendar"""
        # Combine all holidays
        self._holidays: Set[str] = set()
        self._holidays.update(self.HOLIDAYS_2024)
        self._holidays.update(self.HOLIDAYS_2025)

        logger.info(f"NSE calendar initialized with {len(self._holidays)} holidays")

    def is_market_open(
        self,
        check_time: Optional[datetime] = None,
        include_pre_market: bool = False,
        include_post_market: bool = False
    ) -> bool:
        """
        Check if NSE market is currently open.

        :param check_time: Time to check (default: now)
        :param include_pre_market: Include pre-market session
        :param include_post_market: Include post-market session
        :return: True if market is open
        """
        if check_time is None:
            check_time = datetime.now()

        # Check if it's a weekend
        if check_time.weekday() > 4:  # Saturday (5) or Sunday (6)
            return False

        # Check if it's a holiday
        date_str = check_time.strftime('%Y-%m-%d')
        if date_str in self._holidays:
            return False

        # Check market hours
        current_time = check_time.time()

        # Regular market hours
        if self.MARKET_OPEN_TIME <= current_time <= self.MARKET_CLOSE_TIME:
            return True

        # Pre-market session
        if include_pre_market and self.PRE_MARKET_OPEN <= current_time < self.PRE_MARKET_CLOSE:
            return True

        # Post-market session
        if include_post_market and self.POST_MARKET_OPEN <= current_time <= self.POST_MARKET_CLOSE:
            return True

        return False

    def is_trading_day(self, check_date: Optional[datetime] = None) -> bool:
        """
        Check if given date is a trading day (not weekend or holiday).

        :param check_date: Date to check (default: today)
        :return: True if it's a trading day
        """
        if check_date is None:
            check_date = datetime.now()

        # Check weekend
        if check_date.weekday() > 4:
            return False

        # Check holiday
        date_str = check_date.strftime('%Y-%m-%d')
        return date_str not in self._holidays

    def get_next_trading_day(self, from_date: Optional[datetime] = None) -> datetime:
        """
        Get the next trading day from given date.

        :param from_date: Starting date (default: today)
        :return: Next trading day
        """
        from datetime import timedelta

        if from_date is None:
            from_date = datetime.now()

        next_day = from_date + timedelta(days=1)

        # Keep incrementing until we find a trading day
        while not self.is_trading_day(next_day):
            next_day += timedelta(days=1)

        return next_day

    def get_upcoming_holidays(self, days: int = 30) -> List[str]:
        """
        Get upcoming holidays within specified days.

        :param days: Number of days to look ahead
        :return: List of holiday dates (YYYY-MM-DD)
        """
        from datetime import timedelta

        today = datetime.now()
        end_date = today + timedelta(days=days)

        upcoming = []
        for holiday in sorted(self._holidays):
            holiday_date = datetime.strptime(holiday, '%Y-%m-%d')
            if today <= holiday_date <= end_date:
                upcoming.append(holiday)

        return upcoming

    def add_holiday(self, date_str: str):
        """
        Add a custom holiday.

        :param date_str: Date in 'YYYY-MM-DD' format
        """
        # Validate format
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            self._holidays.add(date_str)
            logger.info(f"Added holiday: {date_str}")
        except ValueError:
            logger.error(f"Invalid date format: {date_str}, expected YYYY-MM-DD")

    def remove_holiday(self, date_str: str):
        """
        Remove a holiday (e.g., if NSE announces special trading session).

        :param date_str: Date in 'YYYY-MM-DD' format
        """
        if date_str in self._holidays:
            self._holidays.remove(date_str)
            logger.info(f"Removed holiday: {date_str}")

    def time_until_market_open(self, check_time: Optional[datetime] = None) -> Optional[int]:
        """
        Get seconds until next market open.

        :param check_time: Time to check from (default: now)
        :return: Seconds until market open, or None if market is open
        """
        from datetime import timedelta

        if check_time is None:
            check_time = datetime.now()

        if self.is_market_open(check_time):
            return None  # Market is already open

        # If after market close today, return time until next trading day's open
        if check_time.time() > self.MARKET_CLOSE_TIME:
            next_day = self.get_next_trading_day(check_time)
            next_open = datetime.combine(next_day.date(), self.MARKET_OPEN_TIME)
            return int((next_open - check_time).total_seconds())

        # If before market open today
        if self.is_trading_day(check_time):
            today_open = datetime.combine(check_time.date(), self.MARKET_OPEN_TIME)
            return int((today_open - check_time).total_seconds())

        # If today is not a trading day
        next_day = self.get_next_trading_day(check_time)
        next_open = datetime.combine(next_day.date(), self.MARKET_OPEN_TIME)
        return int((next_open - check_time).total_seconds())

    def time_until_market_close(self, check_time: Optional[datetime] = None) -> Optional[int]:
        """
        Get seconds until market close.

        :param check_time: Time to check from (default: now)
        :return: Seconds until market close, or None if market is closed
        """
        if check_time is None:
            check_time = datetime.now()

        if not self.is_market_open(check_time):
            return None  # Market is not open

        today_close = datetime.combine(check_time.date(), self.MARKET_CLOSE_TIME)
        return int((today_close - check_time).total_seconds())


# Global instance
_nse_calendar = None


def get_nse_calendar() -> NSECalendar:
    """Get global NSE calendar instance"""
    global _nse_calendar
    if _nse_calendar is None:
        _nse_calendar = NSECalendar()
    return _nse_calendar
