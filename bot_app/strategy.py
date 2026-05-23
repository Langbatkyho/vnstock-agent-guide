import logging

logger = logging.getLogger(__name__)


def evaluate_strategy(scorecard):
    """
    Đánh giá tín hiệu chiến thuật dựa trên scorecard.
    Returns: dict chứa tên tín hiệu và chi tiết giải thích
    """
    symbol = scorecard.get('symbol', '???')
    signal = "Không có tín hiệu"
    details = []

    # Safely get values with defaults
    rsi = scorecard.get('rsi_14', 0)
    macd_hist = scorecard.get('macd_hist', 0)
    macd_hist_prev = scorecard.get('macd_hist_prev', 0)
    price_vs_ma10 = scorecard.get('price_vs_ma10_pct', -100)
    price_vs_ma20 = scorecard.get('price_vs_ma20_pct', -100)
    price_vs_ma50 = scorecard.get('price_vs_ma50_pct', -100)
    vol_vs_sma20 = scorecard.get('vol_vs_sma20_pct', 0)
    rs_avg = scorecard.get('rs_avg', 0)

    # Helper checks
    macd_increasing = (macd_hist > 0) and (macd_hist > macd_hist_prev)

    # 1. Kiểm tra tín hiệu "Từ đáy bật lên"
    is_bottom_bounce = True
    bounce_reasons = []

    if not (30 <= rsi <= 50):
        is_bottom_bounce = False
    else:
        bounce_reasons.append("RSI thoát quá bán (30-50)")

    if not macd_increasing:
        is_bottom_bounce = False
    else:
        bounce_reasons.append("MACD Histogram dương và đang tăng")

    if price_vs_ma10 < 0:
        is_bottom_bounce = False
    else:
        bounce_reasons.append("Giá cắt lên/nằm trên MA10")

    if vol_vs_sma20 < 150:
        is_bottom_bounce = False
    else:
        bounce_reasons.append("Volume > 1.5 lần trung bình 20 phiên")

    # 2. Kiểm tra tín hiệu "Phá nền"
    is_breakout = True
    breakout_reasons = []

    if price_vs_ma20 <= 0 or price_vs_ma50 <= 0:
        is_breakout = False
    else:
        breakout_reasons.append("Giá vượt cả MA20 và MA50")

    if price_vs_ma50 <= 3:
        is_breakout = False
    else:
        breakout_reasons.append("Giá cách MA50 > 3%")

    if not macd_increasing:
        is_breakout = False
    else:
        breakout_reasons.append("MACD Histogram dương và đang tăng")

    if vol_vs_sma20 < 200:
        is_breakout = False
    else:
        breakout_reasons.append("Volume đột biến > 2.0 lần trung bình 20 phiên")

    if rs_avg < 50:
        is_breakout = False
    else:
        breakout_reasons.append("RS trung bình > 50 (mạnh hơn TT chung)")

    # Quyết định tín hiệu (Ưu tiên Phá nền nếu thỏa cả 2)
    if is_breakout:
        signal = "Phá nền"
        details = breakout_reasons
    elif is_bottom_bounce:
        signal = "Từ đáy bật lên"
        details = bounce_reasons

    logger.info(f"Strategy [{symbol}]: {signal} ({len(details)} conditions met)")

    return {
        "signal": signal,
        "details": details
    }
