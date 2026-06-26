# GLOBAL CONSTRAINTS - Ràng buộc Bất biến của Hệ thống

Đây là danh sách các quy tắc kiến trúc cấm vi phạm (Hard Constraints) cho dự án `bot_app`. Mọi Agent tham gia vào việc chỉnh sửa code đều phải tuân thủ tuyệt đối các ràng buộc này.

1. **Atomic Caching (Ghi trạng thái an toàn):** Việc lưu trạng thái (như `save_alert_cache`, `save_cycle_count`) bắt buộc phải đặt trong khối `finally` của vòng lặp chính (`run_cycle`). Tuyệt đối không được gọi trực tiếp giữa chừng luồng thực thi để tránh mất dữ liệu khi app crash.
2. **Cấm God Object ở Orchestrator:** `main.py` không được kiêm nhiệm việc parse HTML/Regex, không chứa cấu hình Prompt tĩnh dài dòng. Mọi logic format văn bản phải được ném sang `formatters.py` hoặc file tương tự.
3. **Data Contract (Pydantic):** Giao tiếp dữ liệu giữa các module (ví dụ từ `main.py` sang `ai_analyzer.py`) phải tham chiếu qua Schema của Pydantic định nghĩa tại `data_contract.py`.
4. **Tuyệt đối không dùng Regex cho LLM Output:** Mọi kết quả trả về từ LLM (như nội dung báo cáo Telegram) nếu có format lại thì đưa ra `formatters.py`, không dùng `import html` và Regex bừa bãi trong các module nghiệp vụ như `telegram_bot.py`.
5. **LLM Kháng Lỗi (Resilient LLM Pipeline):** Mọi module gọi API của LLM (Google Gemini) bắt buộc phải có cơ chế API Key Rotation (lấy từ `.env`), tự động Fallback Model khi gặp lỗi 503, và Exponential Backoff (sleep) khi gặp lỗi 429.
