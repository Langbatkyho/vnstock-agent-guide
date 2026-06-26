import requests
import time
import config
import logging

logger = logging.getLogger(__name__)

# Cấu hình retry
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

def send_telegram_message(text):

    """Send message to Telegram with retry logic and character limit chunking (4096 chars)."""
    token = config.TELEGRAM_BOT_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID

    if token == "YOUR_TELEGRAM_BOT_TOKEN" or chat_id == "YOUR_TELEGRAM_CHAT_ID":
        logger.warning("Telegram Bot Token or Chat ID is not configured. Message not sent.")
        print("\n=== MÔ PHỎNG TELEGRAM MESSAGE ===")
        print(text)
        print("=================================\n")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Chia nhá» tin nháº¯n náº¿u vÆ°á»£t quÃ¡ 4000 kÃ½ tá»± (giá»›i háº¡n Telegram lÃ  4096)
    max_length = 4000
    chunks = []
    if len(text) <= max_length:
        chunks.append(text)
    else:
        logger.info(f"Message length ({len(text)}) exceeds limit. Chunking...")
        current_chunk = ""
        for line in text.split("\n"):
            if len(current_chunk) + len(line) + 1 > max_length:
                chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        if current_chunk:
            chunks.append(current_chunk)

    success = True
    for i, chunk in enumerate(chunks):
        if len(chunks) > 1:
            logger.info(f"Sending chunk {i+1}/{len(chunks)}")
        
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "HTML"
        }

        chunk_success = False
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status()
                logger.info(f"Message chunk {i+1} sent successfully")
                chunk_success = True
                break
            except requests.exceptions.Timeout:
                logger.warning(f"Telegram send timeout (attempt {attempt}/{MAX_RETRIES})")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Telegram connection error (attempt {attempt}/{MAX_RETRIES})")
            except Exception as e:
                logger.error(f"Failed to send Telegram message chunk (attempt {attempt}/{MAX_RETRIES}): {e}")

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

        if not chunk_success:
            success = False

    return success

