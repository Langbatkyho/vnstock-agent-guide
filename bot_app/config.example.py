import os

# 1. Watchlist configuration
# Key: Target Stock, Value: Reference Stocks for comparison
WATCHLIST = {
    "HPG": ["NKG", "HSG"],
    "VND": ["SSI", "VIX"]
}

# 1.1 Commodity Mapping for Targets
COMMODITY_MAPPING = {
    "HPG": "steel"
}

# 2. Benchmark Configuration (Option B: Custom VN-Index excluding VIC and VHM)
BENCHMARK_INDEX = "VNINDEX"
EXCLUDED_FROM_BENCHMARK = ["VIC", "VHM"]

# 3. Time interval for scheduler
INTERVAL_MINUTES = 10
REPORT_INTERVAL_CYCLES = 3  # Báo cáo toàn diện mỗi 3 chu kỳ (30 phút)

# 4. Data source to use
DATA_SOURCE = "KBS"

# 5. APIs Keys and Tokens
# Please set these as environment variables before running the application, or replace them here directly (not recommended for security)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_FIRST_GEMINI_API_KEY")
GEMINI_API_KEYS = os.environ.get("GEMINI_API_KEYS", "KEY1,KEY2,KEY3")
GEMINI_API_KEY_OVERALL = os.environ.get("GEMINI_API_KEY_OVERALL", "YOUR_SECOND_GEMINI_API_KEY_FOR_OVERALL_REPORT")

# Model configuration
GEMINI_MODEL = "gemini-3.5-flash"
