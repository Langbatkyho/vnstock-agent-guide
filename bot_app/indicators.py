import pandas as pd
from vnstock_ta import Indicator  # Khôi phục vnstock_ta
import logging

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 1. Biến động Giá
# ──────────────────────────────────────────────
def calc_price_changes(df_ohlcv, df_ohlcv_long=None):
    """Tính % thay đổi giá (1D, 1M, 1Y, 5Y)."""
    res = {}
    if df_ohlcv is None or df_ohlcv.empty:
        return res

    closes = df_ohlcv['close']

    if len(closes) >= 2:
        res['1D_pct'] = (closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2] * 100
    if len(closes) >= 22:
        res['1M_pct'] = (closes.iloc[-1] - closes.iloc[-22]) / closes.iloc[-22] * 100
    if len(closes) >= 250:
        res['1Y_pct'] = (closes.iloc[-1] - closes.iloc[-250]) / closes.iloc[-250] * 100

    if df_ohlcv_long is not None and not df_ohlcv_long.empty:
        closes_l = df_ohlcv_long['close']
        if len(closes_l) >= 1250:
            res['5Y_pct'] = (closes_l.iloc[-1] - closes_l.iloc[-1250]) / closes_l.iloc[-1250] * 100

    return res


def calc_consecutive_up(df_ohlcv):
    """Đếm số phiên tăng liên tiếp (tính từ phiên gần nhất trở về trước)."""
    if df_ohlcv is None or len(df_ohlcv) < 2:
        return 0

    # Bỏ qua phiên hiện tại (dòng cuối cùng) để không bị rung lắc trong phiên làm ngắt chuỗi
    closes = df_ohlcv['close'].values[:-1]
    count = 0
    for i in range(len(closes) - 1, 0, -1):
        if closes[i] > closes[i - 1]:
            count += 1
        else:
            break
    return count


# ──────────────────────────────────────────────
# 2. Khối lượng
# ──────────────────────────────────────────────
def calc_volume_vs_sma(df_ohlcv):
    """Tính % khối lượng hôm nay so với SMA10 và SMA20."""
    res = {}
    if df_ohlcv is None or len(df_ohlcv) < 20:
        return res

    volumes = df_ohlcv['volume']
    curr_vol = volumes.iloc[-1]
    sma10_vol = volumes.rolling(10).mean().iloc[-1]
    sma20_vol = volumes.rolling(20).mean().iloc[-1]

    res['vol_vs_sma10_pct'] = (curr_vol / sma10_vol * 100) if sma10_vol else 0
    res['vol_vs_sma20_pct'] = (curr_vol / sma20_vol * 100) if sma20_vol else 0
    return res


def calc_active_buy_pct(df_vol_profile):
    """Tính % Mua chủ động từ Volume Profile.
    Schema: price, buy_volume, sell_volume, unknown_volume, total_volume
    """
    if df_vol_profile is None or df_vol_profile.empty:
        return 0

    try:
        total_buy = df_vol_profile['buy_volume'].sum()
        total_vol = df_vol_profile['total_volume'].sum()
        if total_vol > 0:
            return (total_buy / total_vol) * 100
    except Exception as e:
        logger.error(f"Error calculating active buy pct: {e}")
    return 0


# ──────────────────────────────────────────────
# 3. Chỉ báo Kỹ thuật (RSI, MACD, MA từ vnstock_ta)
# ──────────────────────────────────────────────
def calc_ta_indicators(df_ohlcv):
    """Tính RSI(14), MACD Histogram, và % Giá vs MA10/MA20/MA50 bằng vnstock_ta."""
    res = {}
    if df_ohlcv is None or len(df_ohlcv) < 50:
        return res

    try:
        ta = Indicator(data=df_ohlcv)

        # ── RSI ──
        rsi_series = ta.momentum.rsi(length=14)
        if not rsi_series.empty:
            rsi_val = rsi_series.iloc[-1]
            res['rsi_14'] = rsi_val
            # Trích xuất 30 giá trị RSI gần nhất loại bỏ NaN
            rsi_history_series = rsi_series.dropna().tail(30)
            res['rsi_14_history'] = rsi_history_series.tolist()
            # Trạng thái RSI (Theo lý thuyết RSI Range Shift dải sinh thái 40/60)
            if rsi_val >= 60:
                res['rsi_status'] = 'Bull Market Range (Xu hướng tăng thống trị)'
            elif rsi_val <= 40:
                res['rsi_status'] = 'Bear Market Range (Xu hướng giảm thống trị)'
            else:
                res['rsi_status'] = 'Vùng giằng co (Đang dịch chuyển xu hướng)'

        # ── MACD ──
        macd_df = ta.momentum.macd(fast=12, slow=26, signal=9)
        if not macd_df.empty:
            hist = macd_df['MACDh_12_26_9'].iloc[-1]
            hist_prev = macd_df['MACDh_12_26_9'].iloc[-2]
            res['macd_hist'] = hist
            res['macd_hist_prev'] = hist_prev
            # Trạng thái MACD (theo plan: MACD Histogram + Trạng thái)
            if hist > 0 and hist > hist_prev:
                res['macd_status'] = 'Dương & Tăng'
            elif hist > 0:
                res['macd_status'] = 'Dương & Giảm'
            elif hist < 0 and hist < hist_prev:
                res['macd_status'] = 'Âm & Giảm'
            else:
                res['macd_status'] = 'Âm & Tăng'

        # ── MA distance bằng vnstock_ta (theo plan: dùng ta.trend.sma) ──
        close = df_ohlcv['close'].iloc[-1]
        for period in [10, 20, 50]:
            sma_series = ta.trend.sma(length=period)
            if not sma_series.empty:
                sma_val = sma_series.iloc[-1]
                if pd.notna(sma_val) and sma_val != 0:
                    res[f'price_vs_ma{period}_pct'] = (close - sma_val) / sma_val * 100

    except Exception as e:
        logger.error(f"Error calculating TA indicators: {e}")

    return res


# ──────────────────────────────────────────────
# 4. Relative Strength (RS) so với Benchmark
# ──────────────────────────────────────────────
def calc_rs(df_stock, df_benchmark):
    """Tính RS 3 ngày, 1 tháng, 3 tháng, 1 năm và RS trung bình."""
    res = {}
    if df_stock is None or df_benchmark is None or df_stock.empty or df_benchmark.empty:
        return res

    try:
        df_s = df_stock.set_index('time') if 'time' in df_stock.columns else df_stock
        df_b = df_benchmark.set_index('time') if 'time' in df_benchmark.columns else df_benchmark

        # Align indexes — chỉ giữ các ngày cả 2 đều có dữ liệu
        df_s, df_b = df_s.align(df_b, join='inner')

        close_s = df_s['close']
        close_b = df_b['close']

        periods = {'3D': 3, '1M': 22, '3M': 66, '1Y': 250}
        rs_values = []

        for name, period in periods.items():
            if len(close_s) > period:
                stock_ret = (close_s.iloc[-1] - close_s.iloc[-(period + 1)]) / close_s.iloc[-(period + 1)]
                bench_ret = (close_b.iloc[-1] - close_b.iloc[-(period + 1)]) / close_b.iloc[-(period + 1)]

                # RS = ((1 + stock_ret) / (1 + bench_ret) - 1) * 100
                rs_val = ((1 + stock_ret) / (1 + bench_ret) - 1) * 100
                res[f'rs_{name}'] = rs_val
                rs_values.append(rs_val)

        # RS trung bình = trung bình cộng các RS
        if rs_values:
            res['rs_avg'] = sum(rs_values) / len(rs_values)

    except Exception as e:
        logger.error(f"Error calculating RS: {e}")

    return res


# ──────────────────────────────────────────────
# 5. Khối ngoại
# ──────────────────────────────────────────────
def calc_foreign_net_vol(df_foreign):
    """Tính tổng mua/bán ròng khối ngoại.
    Schema: trading_date, buy_vol, buy_val, sell_vol, sell_val, net_vol, net_val
    """
    if df_foreign is None or df_foreign.empty:
        return 0

    try:
        if 'net_vol' in df_foreign.columns:
            return df_foreign['net_vol'].sum()
    except Exception as e:
        logger.error(f"Error calculating foreign net: {e}")
    return 0


# ──────────────────────────────────────────────
# 6. Tổng hợp Scorecard
# ──────────────────────────────────────────────
def build_scorecard(symbol, df_ohlcv, df_benchmark,
                    df_ohlcv_long=None, df_vol_profile=None,
                    df_foreign=None, quote=None, summary=None):
    """Tổng hợp tất cả chỉ số thành 1 dict — tương ứng 1 dòng trong bảng chi_so.md."""
    scorecard = {'symbol': symbol}

    # 1. Price changes & consecutive up
    scorecard.update(calc_price_changes(df_ohlcv, df_ohlcv_long))
    scorecard['consecutive_up'] = calc_consecutive_up(df_ohlcv)

    # 2. Volume
    scorecard.update(calc_volume_vs_sma(df_ohlcv))
    scorecard['active_buy_pct'] = calc_active_buy_pct(df_vol_profile)

    # 3. TA Indicators (RSI, MACD, MA — vnstock_ta)
    scorecard.update(calc_ta_indicators(df_ohlcv))

    # 4. Relative Strength vs Custom Benchmark
    scorecard.update(calc_rs(df_ohlcv, df_benchmark))

    # 5. Summary fields (beta, market_cap)
    if summary is not None and not summary.empty:
        for col in ['beta', 'pe', 'pb', 'market_cap']:
            if col in summary.columns:
                scorecard[col] = summary[col].iloc[-1]

    # 6. Current price from quote (realtime) — fallback to OHLCV close
    if quote is not None and not quote.empty:
        if 'close_price' in quote.columns:
            scorecard['current_price'] = quote['close_price'].iloc[-1]
        elif 'match_price' in quote.columns:
            scorecard['current_price'] = quote['match_price'].iloc[-1]

    if 'current_price' not in scorecard and df_ohlcv is not None and not df_ohlcv.empty:
        scorecard['current_price'] = df_ohlcv['close'].iloc[-1]

    # 7. Foreign net volume
    scorecard['foreign_net_vol_20d'] = calc_foreign_net_vol(df_foreign)

    return scorecard
