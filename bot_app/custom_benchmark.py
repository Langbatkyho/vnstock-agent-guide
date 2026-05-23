import pandas as pd
import datetime
import logging
from data_fetcher import fetch_ohlcv, fetch_summary
import config

logger = logging.getLogger(__name__)

# Cache weights so we don't fetch summary for all symbols every 10 minutes
_cap_weights_cache = {}
_last_weight_cache_date = None

# Cache benchmark DataFrame so it's only computed once per day
_benchmark_cache = None
_last_benchmark_cache_date = None


def get_market_caps():
    """Fetch market caps for benchmark calculation. Cached per day."""
    global _cap_weights_cache, _last_weight_cache_date
    today = datetime.date.today()

    if _last_weight_cache_date == today and _cap_weights_cache:
        return _cap_weights_cache

    logger.info("Fetching market caps to calculate custom benchmark weights...")

    # Try fetching VNINDEX market cap
    try:
        idx_summary = fetch_summary(config.BENCHMARK_INDEX, is_index=True)
        total_market_cap = 5_000_000 * 1e9  # Fallback: 5 quadrillion VND
        if idx_summary is not None and 'market_cap' in idx_summary.columns:
            total_market_cap = float(idx_summary['market_cap'].iloc[-1])
    except Exception as e:
        logger.warning(f"Could not get index market cap, using fallback. Error: {e}")
        total_market_cap = 5_000_000 * 1e9

    weights = {}
    for sym in config.EXCLUDED_FROM_BENCHMARK:
        try:
            sym_summary = fetch_summary(sym, is_index=False)
            if sym_summary is not None and 'market_cap' in sym_summary.columns:
                mcap = float(sym_summary['market_cap'].iloc[-1])
                weights[sym] = mcap / total_market_cap
            else:
                # Fallback approximations
                fallback_weights = {'VIC': 0.035, 'VHM': 0.030}
                weights[sym] = fallback_weights.get(sym, 0.01)
        except Exception as e:
            logger.error(f"Error getting market cap for {sym}: {e}")
            weights[sym] = 0.03  # generic fallback

    _cap_weights_cache = weights
    _last_weight_cache_date = today
    logger.info(f"Calculated excluded weights: {weights}")

    return weights


def get_custom_benchmark_ohlcv(length='1Y'):
    """
    Construct an OHLCV-like DataFrame for the Custom Benchmark.
    Cached per day to avoid redundant API calls across multiple targets.
    """
    global _benchmark_cache, _last_benchmark_cache_date
    today = datetime.date.today()

    # Trả về cache nếu cùng ngày
    if _last_benchmark_cache_date == today and _benchmark_cache is not None:
        logger.info("Using cached Custom Benchmark OHLCV.")
        return _benchmark_cache

    logger.info("Calculating Custom Benchmark (excluding specified symbols)...")

    # 1. Fetch VNINDEX data
    df_idx = fetch_ohlcv(config.BENCHMARK_INDEX, length=length, is_index=True)
    if df_idx is None or df_idx.empty:
        logger.error("Failed to fetch Index data for benchmark.")
        return None

    df_idx = df_idx.set_index('time')

    # 2. Get weights
    weights = get_market_caps()

    # Calculate daily returns for index
    idx_returns = df_idx['close'].pct_change()

    total_excluded_weight = sum(weights.values())
    adjusted_returns = idx_returns.copy()

    # 3. Adjust returns by subtracting weighted returns of excluded symbols
    for sym in config.EXCLUDED_FROM_BENCHMARK:
        df_sym = fetch_ohlcv(sym, length=length, is_index=False)
        if df_sym is not None and not df_sym.empty:
            df_sym = df_sym.set_index('time')
            sym_returns = df_sym['close'].pct_change()

            # Align by index
            aligned_returns = sym_returns.reindex(idx_returns.index).fillna(0)

            # Adjust
            adjusted_returns = adjusted_returns - (weights.get(sym, 0) * aligned_returns)

    # Normalize returns to the remaining weight (1 - total_excluded_weight)
    if total_excluded_weight < 1.0:
        adjusted_returns = adjusted_returns / (1.0 - total_excluded_weight)

    # 4. Reconstruct 'close' prices from adjusted returns
    base_value = df_idx['close'].iloc[0]
    cum_returns = (1 + adjusted_returns.fillna(0)).cumprod()
    custom_close = base_value * cum_returns

    # Create the result dataframe
    df_custom = df_idx.copy()
    df_custom['close'] = custom_close

    # Reset index to match standard format
    df_custom = df_custom.reset_index()

    # Lưu cache
    _benchmark_cache = df_custom
    _last_benchmark_cache_date = today
    logger.info("Custom Benchmark OHLCV cached for today.")

    return df_custom
