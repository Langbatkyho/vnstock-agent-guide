import os
import sys
import logging

# Thêm thư mục hiện tại vào sys.path để đảm bảo import config và các module khác đúng cách
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import run_cycle

from logger_config import setup_logger

# Kích hoạt hệ thống ghi log tập trung (ghi ra file logs/bot.log và console)
setup_logger()
logger = logging.getLogger("scheduled_run")

if __name__ == "__main__":
    logger.info("=== BẮT ĐẦU CHU KỲ QUÉT CỔ PHIẾU TỰ ĐỘNG ===")
    try:
        run_cycle()
        logger.info("=== HOÀN THÀNH CHU KỲ QUÉT CỔ PHIẾU THÀNH CÔNG ===")
    except Exception as e:
        logger.error(f"Lỗi khi thực hiện quét chu kỳ: {e}", exc_info=True)
        sys.exit(1)
