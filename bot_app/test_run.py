import config
import logging
from main import run_cycle
from logger_config import setup_logger

# Kích hoạt hệ thống ghi log tập trung (ghi ra file logs/bot.log và console)
setup_logger()
logger = logging.getLogger("test_run")

print("Starting test run of the overall loop...")
try:
    logger.info("Executing one integrated cycle run...")
    run_cycle()
    print("Test run completed successfully!")
except Exception as e:
    print(f"Test run failed: {e}")
    import traceback
    traceback.print_exc()
