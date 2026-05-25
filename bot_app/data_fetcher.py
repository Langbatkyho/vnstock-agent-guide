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


def _to_native(value):
    """Convert numpy/pandas types to native Python types for JSON/dict usability."""
    if hasattr(value, 'item'):
        return value.item()
    return value


def fetch_rrg(symbol):
    """Fetch RRG metrics for the symbol."""
    logger.info(f"Fetching RRG for {symbol}")
    try:
        from vnstock_data import Insights
        ins = Insights()
        df = ins.equity(symbol).rrg()
        _rate_limit_pause()
        if df is not None and not df.empty:
            row = df.iloc[-1]
            res = {}
            for col in ['RRG_RS_Short_Term', 'RRG_RM_Short_Term',
                        'RRG_RS_Mid_Term', 'RRG_RM_Mid_Term',
                        'RRG_RS_Standard_Term', 'RRG_RM_Standard_Term',
                        'DRAW_DOWN_STATUS', 'DRAW_DOWN_VALUE']:
                if col in df.columns:
                    val = row[col]
                    res[col] = _to_native(val)
            return res
    except Exception as e:
        logger.error(f"Error fetching RRG for {symbol}: {e}")
    return None


def fetch_peer_compare(symbol):
    """Fetch industry peer comparison metrics for the symbol."""
    logger.info(f"Fetching peer compare for {symbol}")
    try:
        from vnstock_data import Insights
        ins = Insights()
        df = ins.equity(symbol).peer_compare()
        _rate_limit_pause()
        if df is not None and not df.empty:
            row = df.iloc[0]
            res = {}
            for col in df.columns:
                val = row[col]
                res[col] = _to_native(val)
            return res
    except Exception as e:
        logger.error(f"Error fetching peer compare for {symbol}: {e}")
    return None


def fetch_market_breadth():
    """Fetch overall market breadth (MA20/MA50 percentage) for HOSE."""
    logger.info("Fetching overall market breadth")
    try:
        from vnstock_data import Insights
        ins = Insights()
        df = ins.sentiment.breadth()
        _rate_limit_pause()
        if df is not None and not df.empty:
            if 'exchange' in df.columns:
                df_hose = df[df['exchange'] == 'HOSE']
            else:
                df_hose = df
            if not df_hose.empty:
                row = df_hose.iloc[-1]
                res = {}
                for col in ['above_ma20_pct', 'above_ma50_pct',
                            'avg_20d_above_ma20_pct', 'avg_20d_above_ma50_pct',
                            'pe', 'pb']:
                    if col in df_hose.columns:
                        val = row[col]
                        res[col] = _to_native(val)
                return res
    except Exception as e:
        logger.error(f"Error fetching market breadth: {e}")
    return None


def fetch_all_proprietary_flow():
    """Fetch self-trading proprietary flow for all symbols (1 single API call)."""
    logger.info("Fetching all proprietary flow")
    try:
        from vnstock_data import Insights
        ins = Insights()
        df = ins.flow.proprietary()
        _rate_limit_pause()
        return df
    except Exception as e:
        logger.error(f"Error fetching proprietary flow: {e}")
    return None


def fetch_order_flow(symbol):
    """Fetch order flow volume distribution by price step and calculate buy pressure."""
    logger.info(f"Fetching order flow for {symbol}")
    try:
        from vnstock_data import Insights
        ins = Insights()
        df = ins.equity(symbol).order_flow()
        _rate_limit_pause()
        if df is not None and not df.empty:
            total_buy = df['BuyActiveQtty'].sum() if 'BuyActiveQtty' in df.columns else 0
            total_sell = df['SellActiveQtty'].sum() if 'SellActiveQtty' in df.columns else 0
            total_active = total_buy + total_sell
            buy_ratio = (total_buy / total_active * 100) if total_active > 0 else 50.0
            return {
                "total_buy_active_qtty": _to_native(total_buy),
                "total_sell_active_qtty": _to_native(total_sell),
                "buy_active_ratio": _to_native(buy_ratio)
            }
    except Exception as e:
        logger.error(f"Error fetching order flow for {symbol}: {e}")
    return None


def fetch_commodity_price(commodity_name):
    """Fetch latest commodity price dynamically by name from Macro().commodity()."""
    logger.info(f"Fetching commodity price for {commodity_name}")
    try:
        from vnstock_data import Macro
        macro = Macro()
        commodity_obj = macro.commodity()
        if hasattr(commodity_obj, commodity_name):
            func = getattr(commodity_obj, commodity_name)
            df = func()
            _rate_limit_pause()
            if df is not None and not df.empty:
                row = df.iloc[-1]
                res = {}
                for col in df.columns:
                    val = row[col]
                    res[col] = _to_native(val)
                return res
    except Exception as e:
        logger.error(f"Error fetching commodity {commodity_name}: {e}")
    return None


def fetch_macro_global(method_name):
    """Fetch global macro metric (e.g. bond_yield, fed_rate, index) from Macro().global."""
    logger.info(f"Fetching macro global {method_name}")
    try:
        from vnstock_data import Macro
        macro = Macro()
        macro_global = getattr(macro, 'global', None)
        if macro_global is not None and hasattr(macro_global, method_name):
            func = getattr(macro_global, method_name)
            df = func()
            _rate_limit_pause()
            if df is not None and not df.empty:
                row = df.iloc[-1]
                res = {}
                for col in df.columns:
                    val = row[col]
                    res[col] = _to_native(val)
                return res
    except Exception as e:
        logger.error(f"Error fetching macro global {method_name}: {e}")
    return None
