import datetime
import time
from vnstock_data import Market
import config
import logging

logger = logging.getLogger(__name__)

# Cache for long-term historical data (5Y) — fetched once per session
_ohlcv_long_cache = {}
_ohlcv_long_cache_date = None

# Reusable Market instance — created once per cycle to reduce overhead
_market_instance = None


def get_market():
    """Get or create a reusable Market instance."""
    global _market_instance
    if _market_instance is None:
        _market_instance = Market(random_agent=True)
    return _market_instance


def reset_market():
    """Reset Market instance at the start of each cycle (fresh session).
    Also invalidate the 5Y OHLCV cache if it's from a previous day.
    """
    global _market_instance, _ohlcv_long_cache, _ohlcv_long_cache_date
    _market_instance = None

    # Invalidate 5Y cache nếu đã sang ngày mới
    today = datetime.date.today()
    if _ohlcv_long_cache_date != today:
        logger.info("Invalidating 5Y OHLCV cache (new trading day).")
        _ohlcv_long_cache.clear()
        _ohlcv_long_cache_date = today


def _rate_limit_pause(seconds=0.3):
    """Small pause between API calls to avoid rate limiting."""
    time.sleep(seconds)


def fetch_ohlcv(symbol, length='1Y', is_index=False):
    """Fetch OHLCV data for technical indicators (default 1Y)."""
    logger.info(f"Fetching {length} OHLCV for {symbol}")
    mkt = get_market()
    try:
        if is_index:
            df = mkt.index(symbol).ohlcv(length=length, interval='1D')
        else:
            df = mkt.equity(symbol).ohlcv(length=length, interval='1D')
        _rate_limit_pause()
        return df
    except Exception as e:
        logger.error(f"Error fetching OHLCV for {symbol}: {e}")
        return None


def fetch_ohlcv_long(symbol):
    """Fetch 5Y OHLCV data. Uses cache to optimize rate limits."""
    if symbol in _ohlcv_long_cache:
        logger.info(f"Using cached 5Y OHLCV for {symbol}")
        return _ohlcv_long_cache[symbol]

    logger.info(f"Fetching 5Y OHLCV for {symbol} (Cache Miss)")
    df = fetch_ohlcv(symbol, length='5Y', is_index=False)
    if df is not None:
        _ohlcv_long_cache[symbol] = df
    return df


def fetch_quote(symbol):
    """Fetch realtime snapshot (quote)."""
    logger.info(f"Fetching quote for {symbol}")
    mkt = get_market()
    try:
        df = mkt.equity(symbol).quote()
        _rate_limit_pause()
        return df
    except Exception as e:
        logger.error(f"Error fetching quote for {symbol}: {e}")
        return None


def fetch_summary(symbol, is_index=False):
    """Fetch company summary (beta, market_cap, etc.)."""
    logger.info(f"Fetching summary for {symbol}")
    mkt = get_market()
    try:
        if is_index:
            df = mkt.index(symbol).summary()
        else:
            df = mkt.equity(symbol).summary()
        _rate_limit_pause()
        return df
    except Exception as e:
        logger.error(f"Error fetching summary for {symbol}: {e}")
        return None


def fetch_volume_profile(symbol):
    """Fetch volume profile to calculate active buy percentage."""
    logger.info(f"Fetching volume profile for {symbol}")
    mkt = get_market()
    try:
        df = mkt.equity(symbol).volume_profile()
        _rate_limit_pause()
        return df
    except Exception as e:
        logger.error(f"Error fetching volume profile for {symbol}: {e}")
        return None


def fetch_foreign_flow(symbol, days=30):
    """Fetch foreign trade flow for the last `days` calendar days."""
    logger.info(f"Fetching foreign flow for {symbol} (last {days} days)")
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days)

    mkt = get_market()
    try:
        df = mkt.equity(symbol).foreign_flow(
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d')
        )
        _rate_limit_pause()
        return df
    except Exception as e:
        logger.error(f"Error fetching foreign flow for {symbol}: {e}")
        return None
