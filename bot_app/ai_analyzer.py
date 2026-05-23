from google import genai
import config
import logging
import json
import time

logger = logging.getLogger(__name__)

# Khởi tạo Gemini Client (SDK mới: google-genai)
_client = None
_client_overall = None

try:
    if config.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
        logger.info(f"Gemini Client initialized (model: {config.GEMINI_MODEL})")
    else:
        logger.warning("GEMINI_API_KEY not configured!")
except Exception as e:
    logger.error(f"Error initializing Gemini Client: {e}")

try:
    if hasattr(config, "GEMINI_API_KEY_OVERALL") and config.GEMINI_API_KEY_OVERALL != "YOUR_GEMINI_API_KEY_OVERALL" and config.GEMINI_API_KEY_OVERALL:
        _client_overall = genai.Client(api_key=config.GEMINI_API_KEY_OVERALL)
        logger.info(f"Gemini Overall Client initialized (model: {config.GEMINI_MODEL})")
    else:
        logger.warning("GEMINI_API_KEY_OVERALL not configured, overall analysis will use fallback to primary client.")
except Exception as e:
    logger.error(f"Error initializing Gemini Overall Client: {e}")



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

    prompt = f"""Bạn là chuyên gia phân tích kỹ thuật chứng khoán Việt Nam.
Hãy phân tích dữ liệu kỹ thuật thời gian thực của cổ phiếu mục tiêu {target_symbol} so sánh với các cổ phiếu cùng ngành.

DỮ LIỆU ĐẦU VÀO:
{all_scorecards_text}

TÍN HIỆU TỰ ĐỘNG TỪ HỆ THỐNG:
{strategy_text}

CÁC CHỈ SỐ KHẢ DỤNG: {available_indicators}

YÊU CẦU:
Dựa vào các chỉ số kỹ thuật trên, hãy đưa ra nhận định ngắn gọn (tối đa 200 từ) theo cấu trúc sau:

1. So sánh Sức mạnh: {target_symbol} đang mạnh hay yếu hơn các mã tham chiếu? Dẫn chứng bằng chỉ số cụ thể.
2. Xu hướng Ngắn hạn: Dự báo xu hướng tiếp theo của {target_symbol} (Tăng/Giảm/Tích lũy) dựa trên tín hiệu tự động và dữ liệu.
3. Khuyến nghị: (MUA / BÁN / QUAN SÁT) kèm một lý do quan trọng nhất. Tập trung phân tích kỹ thuật, không cảnh báo chung chung.
"""
    return prompt


def analyze_scorecards(target_symbol, scorecards, strategy_result):
    """Gọi Gemini API để lấy phân tích."""
    if _client is None:
        return "⚠️ Lỗi: Chưa cấu hình GEMINI_API_KEY."

    prompt = generate_prompt(target_symbol, scorecards, strategy_result)
    logger.info(f"Sending prompt to Gemini for {target_symbol}")

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = _client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt
            )
            return response.text
        except Exception as e:
            err_str = str(e)
            logger.warning(f"Error calling Gemini API (attempt {attempt}/{max_retries}): {e}")
            
            # Kiểm tra lỗi Rate Limit 429 / ResourceExhausted
            if "429" in err_str or "ResourceExhausted" in err_str or "Resource exhausted" in err_str or "quota" in err_str.lower():
                sleep_time = 65
                logger.warning(f"Gemini API rate limited (429/ResourceExhausted). Sleeping for {sleep_time}s before retry...")
                time.sleep(sleep_time)
            else:
                if attempt == max_retries:
                    logger.error("All Gemini API attempts failed.")
                    return f"⚠️ Lỗi phân tích AI: {str(e)}"
                time.sleep(2)

    # Fallback: tất cả retry đều thất bại (ví dụ 429 liên tục)
    logger.error(f"All {max_retries} Gemini API attempts failed for {target_symbol} (likely rate limited).")
    return f"⚠️ Lỗi phân tích AI: Đã thử {max_retries} lần nhưng đều bị Rate Limit."


def generate_overall_prompt(scorecards_by_target, ai_reports, total_targets=0):
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
    
    # 2. Các nhận định AI riêng lẻ
    report_text_list = []
    for item in ai_reports:
        target = item["target"]
        rep = item["report"]
        report_text_list.append(f"=== Báo cáo AI riêng lẻ cho {target} ===\n{rep}")
    
    reports_text = "\n\n".join(report_text_list)
    
    prompt = f"""Bạn là một chuyên gia phân tích chiến lược chứng khoán Việt Nam cao cấp.
Nhiệm vụ của bạn là tổng hợp bức tranh toàn cảnh thị trường dựa trên số liệu định lượng gốc và nhận định AI riêng lẻ của các nhóm ngành.

BẢNG SO SÁNH ĐỊNH LƯỢNG GỐC:
{data_text}

CÁC BÁO CÁO PHÂN TÍCH CHI TIẾT AI RIÊNG LẺ:
{reports_text}

YÊU CẦU:
Hãy đưa ra một Báo cáo Chiến lược Tổng quan Thị trường ngắn gọn (tối đa 150 từ), tuân thủ đúng cấu trúc:

1. ĐÁNH GIÁ CHÉO: Nhóm cổ phiếu nào đang thể hiện sức mạnh vượt trội nhất về cả xu hướng lẫn dòng tiền (dựa vào RS TB, Vol/SMA20, biến động giá)? 
2. KHUYẾN NGHỊ ƯU TIÊN: Đưa ra lựa chọn duy nhất về nhóm cần ưu tiên giải ngân lúc này (kèm 1 lý do cốt lõi). Nếu tất cả đều rủi ro, khuyến nghị đứng ngoài quan sát.
*Lưu ý: Không dùng các câu từ cảnh báo vĩ mô sáo rỗng. Hãy đi thẳng vào khuyến nghị cụ thể.*
"""
    return prompt


def analyze_overall_market(scorecards_by_target, ai_reports, total_targets=0):
    """Gọi Gemini API để tạo nhận định tổng quan thị trường."""
    client_to_use = _client_overall if _client_overall is not None else _client
    
    if client_to_use is None:
        return "⚠️ Lỗi: Chưa cấu hình GEMINI_API_KEY hoặc GEMINI_API_KEY_OVERALL."
    if not ai_reports:
        return "⚠️ Không có báo cáo AI lẻ để tổng hợp."
        
    prompt = generate_overall_prompt(scorecards_by_target, ai_reports, total_targets)
    
    if _client_overall is not None:
        logger.info("Sending overall market prompt to Gemini using GEMINI_API_KEY_OVERALL...")
    else:
        logger.info("Sending overall market prompt to Gemini using GEMINI_API_KEY (fallback)...")
        
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = client_to_use.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt
            )
            return response.text
        except Exception as e:
            err_str = str(e)
            logger.warning(f"Error calling Gemini API for overall analysis (attempt {attempt}/{max_retries}): {e}")
            
            # Kiểm tra lỗi Rate Limit 429 / ResourceExhausted
            if "429" in err_str or "ResourceExhausted" in err_str or "Resource exhausted" in err_str or "quota" in err_str.lower():
                sleep_time = 65
                logger.warning(f"Gemini API rate limited (429/ResourceExhausted) for overall analysis. Sleeping for {sleep_time}s before retry...")
                time.sleep(sleep_time)
            else:
                if attempt == max_retries:
                    logger.error("All Gemini API attempts for overall analysis failed.")
                    return f"⚠️ Lỗi phân tích AI tổng hợp: {str(e)}"
                time.sleep(2)

    # Fallback: tất cả retry đều thất bại (ví dụ 429 liên tục)
    logger.error(f"All {max_retries} Gemini API attempts for overall analysis failed (likely rate limited).")
    return f"⚠️ Lỗi phân tích AI tổng hợp: Đã thử {max_retries} lần nhưng đều bị Rate Limit."
