# Tái Cấu Trúc Kiến Trúc bot_app (Resilient Architecture Upgrade)

Dựa trên các kỹ năng mới (`agentic-architecture-patterns`, `resilient-llm-pipeline`), bài học từ dự án Stock Hunt và đánh giá tối ưu hệ thống, dưới đây là lộ trình nâng cấp toàn diện (Refactoring Plan) cho `bot_app`.

## 1. Phân Tích Thực Trạng (System Audit)

### 1.1. Vi phạm "God Object" và Atomic Caching
- **`main.py`**: Chứa logic luồng nhưng lưu cache (`save_alert_cache`) không an toàn. Cần bọc `run_cycle()` trong khối `try...finally` (Atomic Caching).
- **`telegram_bot.py`**: Đang kiêm luôn việc parse Regex (`escape_ai_text`), vi phạm nguyên tắc "Tuyệt đối không dùng Regex" và "God Object". Cần tách logic định dạng sang `formatters.py`.

### 1.2. Đường ống LLM thiếu tính Kháng lỗi (`ai_analyzer.py`)
- Dù đã có `time.sleep(65s)` cho lỗi 429, hệ thống không có **API Key Rotation** và không có **Fallback Model** (chuyển sang `gemini-2.5-flash` khi gặp lỗi 503).
- Việc dùng `instructor` để ép output JSON là không cần thiết vì báo cáo gửi Telegram là văn bản dài. Thay vào đó, chỉ dùng `pydantic` để làm **Data Contract Nội bộ** (ràng buộc cấu trúc truyền dữ liệu giữa các file).

### 1.3. Rủi ro Hệ điều hành & DevOps
- Thiếu `GLOBAL_CONSTRAINTS.md`.
- Các file `.bat` đang chứa lệnh `pause` rác gây kẹt tiến trình ảo.

---

## 2. Chiến Lược Multi-Agent Tối Ưu (Shift-Left Testing & Branching)

Để chống xung đột file và thắt cổ chai, quá trình nâng cấp sẽ sử dụng cơ chế **Branch Workspace** (Mỗi Subagent làm việc trên một nhánh rẽ nhánh độc lập). 

### Bước 1: Thiết Lập & DevOps (Thực hiện bởi Orchestrator - Tự động)
- **Lockdown Interface Contract:** Hàm `analyze_scorecards(target_symbol: str, scorecards: Dict, strategy_result: Dict) -> str` bắt buộc giữ nguyên Signature để không vỡ tích hợp.
- **Data Contract First:** Khởi tạo file `data_contract.py` bằng Pydantic để chuẩn hoá schema đầu vào (Đã hủy bỏ/xóa trong đợt rà soát cuối do là dead code chưa dùng tới).
- **DevOps:** Dọn dẹp lệnh `pause` ở `.bat`, tạo `GLOBAL_CONSTRAINTS.md`.

### Bước 2: Phân bổ tác vụ song song (Branch Strategy)
1. **Agent 1 (AI Engineer):** Đảm nhiệm `ai_analyzer.py`.
   - **Nhiệm vụ:** Thiết lập vòng lặp Retry (3 lần), API Key Rotation từ `.env` và Model Fallback khi dính lỗi 503. KHÔNG sử dụng `instructor`.
   - **Shift-Left Test:** Viết script mock LLM, tự giả lập lỗi 503 để test tính năng fallback ngay trên nhánh của mình.
2. **Agent 2 (System Architect):** Đảm nhiệm `main.py` và `telegram_bot.py`.
   - **Nhiệm vụ:** Áp dụng `try...finally` vào `main.py` để Atomic Caching. Tách logic parse Regex/HTML từ `telegram_bot.py` sang module mới `formatters.py`.
   - **Shift-Left Test:** Tự chạy Dry-run `main.py` để đảm bảo file `.alert_cache` luôn được lưu thành công trên nhánh của mình.

### Bước 3: Tích hợp & Kiểm thử Toàn diện (Orchestrator Merge)
- Sau khi 2 Subagents báo cáo test `Pass` trên nhánh của họ, tôi (Orchestrator) sẽ gộp code lại (Merge) và chạy bài Test luồng hoàn chỉnh trên nhánh chính.

---

## User Review Required

> [!IMPORTANT]
> Bản cập nhật này đã gỡ bỏ thư viện `instructor` vì không phù hợp ngữ cảnh, đồng thời bổ sung module `formatters.py` để dọn dẹp "God Object" một cách triệt để.

## Open Questions

1. Cơ chế Interface Lockdown và Branch Strategy đã đúng ý bạn chưa?
2. Bạn có API Keys dự phòng nào để tôi điền vào file `.env` mẫu (`GEMINI_API_KEYS="key1,key2"`) không?

## Verification Plan

- Tự động chạy Unit Test từ các Subagents ở môi trường rẽ nhánh (Workspace: `branch`).
- Test thực tế luồng 503 Fallback và Telegram formatter sau khi hợp nhất.
