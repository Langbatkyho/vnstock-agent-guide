import logging

logger = logging.getLogger(__name__)


def evaluate_strategy(scorecard):
    """
    Đánh giá tín hiệu chiến thuật dựa trên lý thuyết RSI Range Shift (40/60) và dòng tiền.
    Returns: dict chứa tên tín hiệu và chi tiết giải thích
    """
    symbol = scorecard.get('symbol', '???')
    signal = "Không có tín hiệu"
    details = []

    # Thu thập các chỉ số cần thiết
    rsi = scorecard.get('rsi_14', 50)
    price_vs_ma20 = scorecard.get('price_vs_ma20_pct', -100)
    vol_vs_sma20 = scorecard.get('vol_vs_sma20_pct', 100)
    
    # Ưu tiên lấy % Mua chủ động từ Order Flow (buy_active_ratio), fallback về Volume Profile (active_buy_pct)
    buy_active = scorecard.get('buy_active_ratio', scorecard.get('active_buy_pct', 50.0))
    if buy_active is None:
        buy_active = 50.0

    rs_3d = scorecard.get('rs_3D', 0.0)
    rs_1m = scorecard.get('rs_1M', 0.0)

    # 1. Kiểm tra tín hiệu "Bear-to-Bull Shift" (Khởi động Siêu sóng)
    is_bear_to_bull = True
    bear_to_bull_reasons = []

    if rsi <= 60:
        is_bear_to_bull = False
    else:
        bear_to_bull_reasons.append(f"RSI bứt phá vượt ngưỡng cản động 60 (Hiện tại: {rsi:.1f})")

    if price_vs_ma20 <= 0:
        is_bear_to_bull = False
    else:
        bear_to_bull_reasons.append(f"Giá nằm trên MA20 ({price_vs_ma20:+.1f}%) để xác nhận xu hướng")

    if vol_vs_sma20 < 150:
        is_bear_to_bull = False
    else:
        bear_to_bull_reasons.append(f"Thanh khoản bùng nổ vượt trung bình SMA20 ({vol_vs_sma20:.1f}%)")

    if buy_active < 55:
        is_bear_to_bull = False
    else:
        bear_to_bull_reasons.append(f"Lực mua chủ động cực mạnh (% Mua CĐ: {buy_active:.1f}%)")

    # 2. Kiểm tra tín hiệu "Vua Gặp Nạn" (Tạo đáy bứt phá nhanh)
    is_fallen_king = True
    fallen_king_reasons = []

    if rs_3d < 80:
        is_fallen_king = False
    else:
        fallen_king_reasons.append(f"Sức mạnh giá 3 ngày vượt trội thị trường (RS 3D: {rs_3d:.1f})")

    if rs_1m >= 30:
        is_fallen_king = False
    else:
        fallen_king_reasons.append(f"Sức mạnh trung-dài hạn còn yếu (RS 1M: {rs_1m:.1f} < 30)")

    # 3. Kiểm tra tín hiệu "Bull-to-Bear Shift" (Bẫy sập / Gãy xu hướng tăng)
    is_bull_to_bear = True
    bull_to_bear_reasons = []

    if rsi >= 40:
        is_bull_to_bear = False
    else:
        bull_to_bear_reasons.append(f"RSI gãy thủng ngưỡng hỗ trợ động tử thủ 40 (Hiện tại: {rsi:.1f})")

    # Quyết định tín hiệu (Ưu tiên Bear-to-Bull Shift -> Bull-to-Bear Shift -> Vua gặp nạn)
    if is_bear_to_bull:
        signal = "Bear-to-Bull Shift"
        details = bear_to_bull_reasons
    elif is_bull_to_bear:
        signal = "Bull-to-Bear Shift"
        details = bull_to_bear_reasons
    elif is_fallen_king:
        signal = "Vua Gặp Nạn"
        details = fallen_king_reasons

    logger.info(f"Strategy [{symbol}]: {signal} ({len(details)} conditions met)")

    return {
        "signal": signal,
        "details": details
    }

