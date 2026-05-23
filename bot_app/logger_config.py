import os
import logging
from logging.handlers import RotatingFileHandler

# Guard flag — đảm bảo logger chỉ được cấu hình đúng 1 lần duy nhất
# dù setup_logger() bị gọi nhiều lần từ các entry point khác nhau.
_initialized = False


def setup_logger(name=None):
    """
    Cấu hình logger dùng chung cho toàn bộ hệ thống bot.
    Ghi log song song ra cả Console và tệp tin logs/bot.log
    với cơ chế xoay vòng (Rotating File Handler).

    An toàn khi gọi nhiều lần — chỉ cấu hình 1 lần duy nhất.
    """
    global _initialized

    if _initialized:
        # Đã cấu hình rồi — chỉ trả về logger theo tên nếu cần
        if name:
            return logging.getLogger(name)
        return logging.getLogger()

    # Lấy thư mục chứa file logger_config.py này (bot_app)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, "logs")

    # Tạo thư mục logs nếu chưa tồn tại
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "bot.log")

    # Định dạng log thống nhất
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handler ghi ra File xoay vòng (tối đa 5MB/file, giữ lại 5 file backup)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)

    # Handler ghi ra Console (màn hình CMD/PowerShell)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)

    # Cấu hình root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Xóa handler cũ (nếu có) để tránh lặp log
    root_logger.handlers.clear()

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    _initialized = True

    # Trả về logger theo tên nếu có yêu cầu cụ thể
    if name:
        return logging.getLogger(name)
    return root_logger
