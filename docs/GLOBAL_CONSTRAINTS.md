# Quy Tắc Ràng Buộc Toàn Cục (Global Constraints) Cho Các Subagent

Tài liệu này xác định các quy tắc cứng mà **tất cả** các Subagent trong hệ thống Stock News Bot phải tuân thủ nghiêm ngặt để đảm bảo sự ổn định tại các ranh giới giao tiếp (Boundaries).

## 1. Data Contracts (Bắt Buộc)
- **Kiểu Dữ Liệu**: Tuyệt đối không truyền các đối tượng của thư viện bên thứ ba (như `numpy.int64`, `pandas.Timestamp`, `pandas.DataFrame`) qua các ranh giới (boundary) giữa các Subagent. 
- Mọi dữ liệu giao tiếp phải được ép về kiểu dữ liệu gốc của Python (native types: `int`, `float`, `str`, `list`, `dict`) và xác thực bằng **Pydantic Schemas** định nghĩa tại `models/schemas.py`.

## 2. Đầu Ra HTML/Markdown
- **AI Analyzer Agent**: KHÔNG được trả về bất kỳ thẻ HTML hay định dạng Markdown phức tạp nào (trừ khi được cấu trúc cụ thể trong Pydantic schema). Việc escape HTML/Markdown là trách nhiệm của `utils/formatters.py` trước khi gửi lên Telegram.
- Phải trả dữ liệu đúng cấu trúc JSON, không kèm giải thích tự do.

## 3. Atomic State Management
- Việc đọc và ghi cache (`state_cache.py`) phải diễn ra toàn vẹn ở cuối chu kỳ. 
- Không ghi state giữa chừng trong một chu kỳ quét tin nhằm chống hỏng file JSON hoặc lệch dữ liệu nếu hệ thống crash nửa chừng.

## 4. Log Metrics
- Bất cứ khi nào Subagent tương tác với LLM, bắt buộc phải ghi nhận vào file `logs/agent_metrics.jsonl`.
- Phải bắt lỗi đầy đủ các HTTP Code của API (VD: 429 Resource Exhausted) và báo lại cho Orchestrator biết nguyên nhân thất bại (thông qua Exception hoặc Metric).

## 5. Tự Trị (Self-Correction)
- Subagent có trách nhiệm tự sửa lỗi định dạng của chính mình (sử dụng `instructor` với `max_retries`). 
- Nếu sau 3 lần thử mà vẫn không tuân thủ Schema, trả kết quả lỗi (Fail Gracefully) về Orchestrator. Orchestrator sẽ không có trách nhiệm parse code dở dang của Subagent.
