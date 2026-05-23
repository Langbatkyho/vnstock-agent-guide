import time
import schedule
import logging
import config

from data_fetcher import (
    fetch_ohlcv, fetch_ohlcv_long, fetch_quote,
    fetch_summary, fetch_volume_profile, fetch_foreign_flow,
    reset_market,
)
from custom_benchmark import get_custom_benchmark_ohlcv
from indicators import build_scorecard
from strategy import evaluate_strategy
from ai_analyzer import analyze_scorecards, analyze_overall_market
from telegram_bot import format_scorecard_message, send_telegram_message, format_overall_message

from logger_config import setup_logger

# Kích hoạt hệ thống ghi log tập trung (ghi ra file logs/bot.log và console)
setup_logger()
logger = logging.getLogger("bot_main")


import os

CYCLE_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", ".cycle_state")

# Track cycles to manage AI API rate limits
_cycle_count = 0


def load_cycle_count():
    """Đọc cycle_count từ file tạm để đồng bộ trạng thái khi chạy từ Windows Task Scheduler."""
    if os.path.exists(CYCLE_STATE_FILE):
        try:
            with open(CYCLE_STATE_FILE, "r") as f:
                return int(f.read().strip())
        except Exception as e:
            logger.warning(f"Không thể đọc file cycle_state: {e}. Sử dụng 0.")
    return 0


def save_cycle_count(count):
    """Lưu cycle_count vào file tạm."""
    try:
        os.makedirs(os.path.dirname(CYCLE_STATE_FILE), exist_ok=True)
        with open(CYCLE_STATE_FILE, "w") as f:
            f.write(str(count))
    except Exception as e:
        logger.warning(f"Không thể lưu file cycle_state: {e}")


def process_target(target_symbol, reference_symbols):
    """Lấy dữ liệu và tính toán scorecard + strategy cho một target. Không gửi Telegram hay gọi AI trực tiếp."""
    logger.info(f"--- Processing Target: {target_symbol} ---")

    all_symbols = [target_symbol] + reference_symbols
    scorecards = {}

    # 1. Fetch Custom Benchmark (cached per day internally)
    df_benchmark = get_custom_benchmark_ohlcv(length='1Y')
    if df_benchmark is None or df_benchmark.empty:
        logger.error(f"Cannot proceed for {target_symbol} without Custom Benchmark.")
        return None

    # 2. Build scorecards for target + references
    for sym in all_symbols:
        logger.info(f"Gathering data for {sym}...")
        df_ohlcv = fetch_ohlcv(sym, length='1Y')
        df_ohlcv_long = fetch_ohlcv_long(sym)
        df_vol_profile = fetch_volume_profile(sym)
        df_foreign = fetch_foreign_flow(sym, days=30)
        quote = fetch_quote(sym)
        summary = fetch_summary(sym)

        scorecards[sym] = build_scorecard(
            sym, df_ohlcv, df_benchmark, df_ohlcv_long,
            df_vol_profile, df_foreign, quote, summary
        )

    # 3. Evaluate Strategy (rule-based) for target only
    target_scorecard = scorecards.get(target_symbol)
    if not target_scorecard:
        logger.error(f"Failed to generate scorecard for target {target_symbol}")
        return None
        
    strategy_result = evaluate_strategy(target_scorecard)

    return {
        "target": target_symbol,
        "scorecard": target_scorecard,
        "scorecards": scorecards,
        "strategy": strategy_result,
        "has_signal": strategy_result['signal'] != "Không có tín hiệu"
    }


def run_cycle():
    """Main execution loop called by scheduler."""
    global _cycle_count
    
    # Đồng bộ cycle_count từ file (đặc biệt quan trọng khi chạy scheduled_run.py một lần)
    _cycle_count = load_cycle_count()
    
    logger.info(f"===== Starting cycle #{_cycle_count} =====")

    # Reset Market instance for fresh connections each cycle
    reset_market()

    is_full_report = (_cycle_count % config.REPORT_INTERVAL_CYCLES == 0)
    logger.info(f"Cycle mode: {'FULL REPORT' if is_full_report else 'SIGNAL DIRECTED ONLY'}")

    results = []
    
    # Bước 1: Thu thập dữ liệu cho tất cả các target
    for target, refs in config.WATCHLIST.items():
        try:
            res = process_target(target, refs)
            if res:
                results.append(res)
        except Exception as e:
            logger.error(f"Error processing target {target}: {e}", exc_info=True)

    # Bước 2: Xử lý AI lẻ và gửi tin Telegram lẻ theo điều kiện
    ai_reports = []
    scorecards_by_target = {}
    
    for r in results:
        target = r["target"]
        scorecards_by_target[target] = r["scorecard"]
        
        # Điều kiện gọi AI lẻ: Có tín hiệu đột biến OR Chu kỳ báo cáo đầy đủ
        call_ai = r["has_signal"] or is_full_report
        
        ai_analysis = ""
        if call_ai:
            logger.info(f"Calling Gemini AI for analysis of target {target}...")
            ai_analysis = analyze_scorecards(target, r["scorecards"], r["strategy"])
            if ai_analysis and not ai_analysis.startswith("⚠️"):
                ai_reports.append({"target": target, "report": ai_analysis})
                
                # Chỉ delay khi AI call thành công — tránh delay vô nghĩa sau khi đã sleep 65s×3 do 429
                if len(results) > 1:
                    logger.info("Tạm dừng 5 giây giữa các lần gọi AI thành công...")
                    time.sleep(5)
        
        # Điều kiện gửi Telegram lẻ: Có tín hiệu đột biến OR Chu kỳ báo cáo đầy đủ
        if call_ai:
            msg = format_scorecard_message(target, r["scorecard"], r["strategy"])
            if ai_analysis:
                from telegram_bot import escape_ai_text
                escaped_ai = escape_ai_text(ai_analysis)
                msg += f"\n<b>🤖 NHẬN ĐỊNH TỪ AI (Gemini):</b>\n{escaped_ai}\n"
            send_telegram_message(msg)

    # Bước 3: Tổng hợp vĩ mô và Báo cáo Cuối
    # Chỉ gọi AI Tổng hợp khi có ít nhất 1 báo cáo lẻ được tạo (hoặc chu kỳ 30 phút đầy đủ)
    if ai_reports and (is_full_report or any(r["has_signal"] for r in results)):
        logger.info("Chủ động tạm dừng 5 giây trước khi thực hiện phân tích tổng quan...")
        time.sleep(5)
        logger.info("Processing overall market analysis...")
        overall_summary = analyze_overall_market(scorecards_by_target, ai_reports, total_targets=len(config.WATCHLIST))
        
        overall_msg = format_overall_message(overall_summary)
        send_telegram_message(overall_msg)

    _cycle_count += 1
    save_cycle_count(_cycle_count)
    logger.info("===== Cycle completed. Waiting for next schedule... =====")


def main():
    logger.info("Starting Automated Stock Monitoring System...")
    logger.info(f"Watchlist: {config.WATCHLIST}")
    logger.info(f"Interval: {config.INTERVAL_MINUTES} minutes")

    # Run once immediately
    run_cycle()

    # Schedule subsequent runs
    schedule.every(config.INTERVAL_MINUTES).minutes.do(run_cycle)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("System stopped by user.")


if __name__ == "__main__":
    main()
