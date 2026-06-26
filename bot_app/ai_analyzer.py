from google import genai
import config
import logging
import json
import time

logger = logging.getLogger(__name__)

# Khởi tạo Gemini Client (SDK mới: google-genai)
_client = None
_client_overall = None
_api_keys = []
_current_key_idx = 0

try:
    if hasattr(config, "GEMINI_API_KEYS") and config.GEMINI_API_KEYS:
        _api_keys = [k.strip() for k in config.GEMINI_API_KEYS.split(",") if k.strip() and k.strip() != "YOUR_API_KEYS"]
    elif hasattr(config, "GEMINI_API_KEY") and config.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
        _api_keys = [config.GEMINI_API_KEY]
        
    if _api_keys:
        _client = genai.Client(api_key=_api_keys[0])
        logger.info(f"Gemini Client initialized with {len(_api_keys)} keys (model: {getattr(config, 'GEMINI_MODEL', 'gemini-3.5-flash')})")
    else:
        logger.warning("GEMINI_API_KEYS not configured!")
except Exception as e:
    logger.error(f"Error initializing Gemini Client: {e}")

try:
    if hasattr(config, "GEMINI_API_KEY_OVERALL") and config.GEMINI_API_KEY_OVERALL != "YOUR_GEMINI_API_KEY_OVERALL" and config.GEMINI_API_KEY_OVERALL:
        _client_overall = genai.Client(api_key=config.GEMINI_API_KEY_OVERALL)
        logger.info(f"Gemini Overall Client initialized (model: {getattr(config, 'GEMINI_MODEL', 'gemini-3.5-flash')})")
    else:
        logger.warning("GEMINI_API_KEY_OVERALL not configured, overall analysis will use fallback to primary client.")
except Exception as e:
    logger.error(f"Error initializing Gemini Overall Client: {e}")

def rotate_api_key(is_overall=False):
    global _current_key_idx, _client, _client_overall
    if is_overall and _client_overall is not None:
        logger.warning("Overall client rate limited. Switching overall analysis to primary client pool.")
        _client_overall = None
        return True
        
    if not _api_keys:
        return False
    _current_key_idx = (_current_key_idx + 1) % len(_api_keys)
    _client = genai.Client(api_key=_api_keys[_current_key_idx])
    logger.info(f"Rotated to API key index {_current_key_idx}")
    return True



def _to_native(value):
    """Convert numpy/pandas types to native Python types for JSON serialization."""
    if hasattr(value, 'item'):
        return value.item()
    return value


def generate_prompt(target_symbol, scorecards, strategy_result):
    """Tạo prompt tiếng Việt cho Gemini — chỉ nhắc đến các chỉ số đang có."""

    scorecard_texts = []
    for sym, data in scorecards.items():
        filtered = {}
        for k, v in data.items():
            if k == 'symbol':
                continue
            v = _to_native(v)
            filtered[k] = round(v, 2) if isinstance(v, float) else v

        scorecard_texts.append(f"--- Cổ phiếu {sym} ---\n{json.dumps(filtered, indent=2, ensure_ascii=False)}")

    all_scorecards_text = "\n\n".join(scorecard_texts)

    # Format strategy
    strategy_text = f"Tín hiệu hệ thống Rule-based cho {target_symbol}: {strategy_result['signal']}\n"
    if strategy_result['details']:
        strategy_text += "Chi tiết tín hiệu:\n- " + "\n- ".join(strategy_result['details'])

    # Danh sách chỉ số khả dụng (tùy thuộc vnstock_ta có bật hay không)
    available_indicators = "% giá so với MA10/MA20/MA50, khối lượng so với SMA, % Mua chủ động, Sức mạnh tương đối RS, Khối ngoại ròng, Beta"
    sample_keys = list(scorecards.get(target_symbol, {}).keys())
    if 'rsi_14' in sample_keys:
        available_indicators += ", RSI(14)"
    if 'macd_hist' in sample_keys:
        available_indicators += ", MACD Histogram"
    if 'rrg_mid_term_rs' in sample_keys:
        available_indicators += ", Sức mạnh RRG (RS & RM Short/Mid/Standard, trạng thái Drawdown)"
    if 'Security_PE' in sample_keys:
        available_indicators += ", So sánh định giá ngành (Peer Compare PE/PB/ROE)"
    if 'proprietary_net_val_1d' in sample_keys:
        available_indicators += ", Dòng tiền Tự doanh (1D, 10D, 1M)"
    if 'buy_active_ratio' in sample_keys:
        available_indicators += ", Áp lực mua chủ động từ bước giá (Order Flow)"

    prompt = f"""Bạn là chuyên gia phân tích kỹ thuật chứng khoán Việt Nam.
Hãy phân tích dữ liệu kỹ thuật thời gian thực của cổ phiếu mục tiêu {target_symbol} so sánh với các cổ phiếu cùng ngành.

DỮ LIỆU ĐẦU VÀO:
{all_scorecards_text}

TÍN HIỆU TỰ ĐỘNG TỪ HỆ THỐNG:
{strategy_text}

CÁC CHỈ SỐ KHẢ DỤNG: {available_indicators}

YÊU CẦU:
Dựa vào các chỉ số kỹ thuật trên (hãy kết hợp cả các dữ liệu RRG, So sánh ngành Peer Compare, Tự doanh, Order Flow nếu có trong dữ liệu), hãy đưa ra nhận định ngắn gọn (tối đa 200 từ) theo cấu trúc sau:

1. So sánh Sức mạnh: {target_symbol} đang mạnh hay yếu hơn các mã tham chiếu? Dẫn chứng bằng các chỉ số sức mạnh kỹ thuật (RS, RRG, lực mua chủ động) và so sánh định giá (P/E, P/B, ROE) với trung bình ngành.
2. Xu hướng Ngắn hạn: Dự báo xu hướng tiếp theo của {target_symbol} (Tăng/Giảm/Tích lũy) kết hợp dòng tiền khối ngoại và tự doanh.
3. Khuyến nghị: (MUA / BÁN / QUAN SÁT) kèm một lý do quan trọng nhất. Tập trung phân tích kỹ thuật và định lượng dòng tiền, không cảnh báo chung chung.
"""
    return prompt


def analyze_scorecards(target_symbol: str, scorecards: dict, strategy_result: dict) -> str:
    """Gọi Gemini API để lấy phân tích."""
    global _client
    if _client is None:
        return "⚠️ Lỗi: Chưa cấu hình GEMINI_API_KEYS."

    prompt = generate_prompt(target_symbol, scorecards, strategy_result)
    logger.info(f"Sending prompt to Gemini for {target_symbol}")

    max_retries = 3
    current_model = getattr(config, 'GEMINI_MODEL', 'gemini-3.5-flash')
    
    for attempt in range(1, max_retries + 1):
        try:
            response = _client.models.generate_content(
                model=current_model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            err_str = str(e)
            logger.warning(f"Error calling Gemini API (attempt {attempt}/{max_retries}): {e}")
            
            is_503 = "UNAVAILABLE" in err_str or "Service Unavailable" in err_str
            is_429 = "RESOURCE_EXHAUSTED" in err_str or "ResourceExhausted" in err_str or "quota" in err_str.lower() or "429" in err_str
            
            if is_503 and not is_429:
                logger.warning(f"503 Service Unavailable. Fallback from {current_model} to gemini-2.5-flash...")
                current_model = "gemini-2.5-flash"
                time.sleep(1)
            elif is_429:
                logger.warning("Gemini API rate limited (429/ResourceExhausted). Rotating API key...")
                rotate_api_key(is_overall=False)
                time.sleep(2)
            else:
                if attempt == max_retries:
                    logger.error("All Gemini API attempts failed.")
                    return f"⚠️ Lỗi phân tích AI: {str(e)}"
                time.sleep(2)

    logger.error(f"All {max_retries} Gemini API attempts failed for {target_symbol}.")
    return f"⚠️ Lỗi phân tích AI: Đã thử {max_retries} lần nhưng đều thất bại."


def generate_overall_prompt(scorecards_by_target, ai_reports, total_targets=0, market_breadth=None, macro_data=None):
    """Tạo prompt tổng hợp chéo cho toàn bộ các nhóm cổ phiếu."""
    
    # 1. Bảng số liệu so sánh chéo để AI nhìn trực quan định lượng
    data_summary = []
    for target, scorecard in scorecards_by_target.items():
        if not scorecard:
            continue
        # Lấy một số chỉ số nổi bật
        price = scorecard.get('current_price', 0)
        c_1d = scorecard.get('1D_pct', 0)
        c_1m = scorecard.get('1M_pct', 0)
        rs = scorecard.get('rs_avg', 0)
        rsi = scorecard.get('rsi_14', 0)
        macd = scorecard.get('macd_hist', 0)
        vol_sma20 = scorecard.get('vol_vs_sma20_pct', 0)
        
        data_summary.append(
            f"- Nhóm {target}: Giá {price:,.0f} ({c_1d:+.2f}%), 1M: {c_1m:+.2f}%, RS TB: {rs:+.2f}, RSI: {rsi:.1f}, Vol/SMA20: {vol_sma20:.1f}%"
        )
    
    data_text = "\n".join(data_summary)
    
    # Ghi rõ số nhóm có dữ liệu vs tổng để AI không đưa kết luận sai khi thiếu dữ liệu
    n_ok = len(ai_reports)
    if total_targets > 0 and n_ok < total_targets:
        data_text += f"\n\n⚠️ LƯU Ý: Chỉ có {n_ok}/{total_targets} nhóm có dữ liệu. Một số nhóm thiếu do lỗi kết nối."
    
    # Bổ sung thông tin độ rộng và vĩ mô
    market_text = ""
    if market_breadth:
        above_ma20 = market_breadth.get('above_ma20_pct')
        above_ma50 = market_breadth.get('above_ma50_pct')
        avg_20_ma20 = market_breadth.get('avg_20d_above_ma20_pct')
        avg_20_ma50 = market_breadth.get('avg_20d_above_ma50_pct')
        market_text += "Độ rộng Thị trường HOSE:\n"
        if above_ma20 is not None:
            market_text += f"- % Cổ phiếu trên MA20: {above_ma20:.2f}% (Trung bình 20 phiên: {avg_20_ma20:.2f}%)\n"
        if above_ma50 is not None:
            market_text += f"- % Cổ phiếu trên MA50: {above_ma50:.2f}% (Trung bình 20 phiên: {avg_20_ma50:.2f}%)\n"
        if 'pe' in market_breadth:
            market_text += f"- P/E toàn thị trường: {market_breadth['pe']:.2f} | P/B: {market_breadth['pb']:.2f}\n"
        market_text += "\n"

    if macro_data:
        market_text += "Dữ liệu Vĩ mô & Giá Hàng hóa liên quan:\n"
        for key, val in macro_data.items():
            if isinstance(val, dict):
                # Chỉ lấy các trường có giá trị để tránh rối mắt
                val_str = ", ".join([f"{k}: {v}" for k, v in val.items() if v is not None])
                market_text += f"- {key}: {val_str}\n"
            else:
                market_text += f"- {key}: {val}\n"
        market_text += "\n"

    # 2. Các nhận định AI riêng lẻ
    report_text_list = []
    for item in ai_reports:
        target = item["target"]
        rep = item["report"]
        report_text_list.append(f"=== Báo cáo AI riêng lẻ cho {target} ===\n{rep}")
    
    reports_text = "\n\n".join(report_text_list)
    
    prompt = f"""Bạn là một chuyên gia phân tích chiến lược chứng khoán Việt Nam cao cấp.
Nhiệm vụ của bạn là tổng hợp bức tranh toàn cảnh thị trường dựa trên số liệu định lượng gốc, độ rộng thị trường, bối cảnh vĩ mô toàn cầu, giá hàng hóa liên quan và nhận định AI riêng lẻ của các nhóm ngành.

BẢNG SO SÁNH ĐỊNH LƯỢNG GỐC:
{data_text}

THÔNG TIN ĐỘ RỘNG THỊ TRƯỜNG HOSE & VĨ MÔ/HÀNG HÓA:
{market_text}

CÁC BÁO CÁO PHÂN TÍCH CHI TIẾT AI RIÊNG LẺ:
{reports_text}

YÊU CẦU:
Hãy đưa ra một Báo cáo Chiến lược Tổng quan Thị trường ngắn gọn (tối đa 250 từ), tuân thủ đúng cấu trúc:

1. ĐÁNH GIÁ CHÉO: Nhóm cổ phiếu nào đang thể hiện sức mạnh vượt trội nhất về cả xu hướng lẫn dòng tiền (dựa vào RS TB, Vol/SMA20, biến động giá)? Đánh giá độ đồng thuận của thị trường thông qua Độ rộng Thị trường (% cổ phiếu trên MA20/MA50).
2. KHUYẾN NGHỊ ƯU TIÊN: Đưa ra lựa chọn duy nhất về nhóm cần ưu tiên giải ngân lúc này (kèm 1 lý do cốt lõi), đối chiếu trực tiếp với xu hướng vĩ mô toàn cầu hoặc biến động giá hàng hóa liên quan (thép, dầu thô...). Nếu tất cả đều rủi ro, khuyến nghị đứng ngoài quan sát.
*Lưu ý: Không dùng các câu từ cảnh báo vĩ mô sáo rỗng. Hãy đi thẳng vào khuyến nghị cụ thể.*
"""
    return prompt


def analyze_overall_market(scorecards_by_target, ai_reports, total_targets=0, market_breadth=None, macro_data=None):
    """Gọi Gemini API để tạo nhận định tổng quan thị trường."""
    global _client, _client_overall
    client_to_use = _client_overall if _client_overall is not None else _client
    
    if client_to_use is None:
        return "⚠️ Lỗi: Chưa cấu hình GEMINI_API_KEYS hoặc GEMINI_API_KEY_OVERALL."
    if not ai_reports:
        return "⚠️ Không có báo cáo AI lẻ để tổng hợp."
        
    prompt = generate_overall_prompt(scorecards_by_target, ai_reports, total_targets, market_breadth, macro_data)
    
    if _client_overall is not None:
        logger.info("Sending overall market prompt to Gemini using GEMINI_API_KEY_OVERALL...")
    else:
        logger.info("Sending overall market prompt to Gemini using GEMINI_API_KEYS...")
        
    max_retries = 3
    current_model = getattr(config, 'GEMINI_MODEL', 'gemini-3.5-flash')
    
    for attempt in range(1, max_retries + 1):
        try:
            response = client_to_use.models.generate_content(
                model=current_model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            err_str = str(e)
            logger.warning(f"Error calling Gemini API for overall analysis (attempt {attempt}/{max_retries}): {e}")
            
            is_503 = "UNAVAILABLE" in err_str or "Service Unavailable" in err_str
            is_429 = "RESOURCE_EXHAUSTED" in err_str or "ResourceExhausted" in err_str or "quota" in err_str.lower() or "429" in err_str
            
            if is_503 and not is_429:
                logger.warning(f"503 Service Unavailable. Fallback from {current_model} to gemini-2.5-flash...")
                current_model = "gemini-2.5-flash"
                time.sleep(1)
            elif is_429:
                logger.warning("Gemini API rate limited (429). Rotating API key...")
                rotate_api_key(is_overall=(_client_overall is not None))
                client_to_use = _client_overall if _client_overall is not None else _client
                time.sleep(2)
            else:
                if attempt == max_retries:
                    logger.error("All Gemini API attempts for overall analysis failed.")
                    return f"⚠️ Lỗi phân tích AI tổng hợp: {str(e)}"
                time.sleep(2)

    logger.error(f"All {max_retries} Gemini API attempts for overall analysis failed.")
    return f"⚠️ Lỗi phân tích AI tổng hợp: Đã thử {max_retries} lần nhưng đều thất bại."
