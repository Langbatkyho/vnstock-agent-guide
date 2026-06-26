# Change Log - Lịch sử Nâng cấp Hệ thống

Tài liệu này lưu trữ toàn bộ các kế hoạch nâng cấp, các bản nháp thiết kế và thay đổi lịch sử trong suốt vòng đời dự án Hệ thống Theo dõi Cổ phiếu Tự động.

---

## [2026-06-25] Phase 13 - Tái Cấu Trúc Kiến Trúc bot_app (Resilient Architecture Upgrade)

Đợt nâng cấp Phase 13 tập trung vào tối ưu hóa độ bền bỉ của hệ thống (Resiliency) và dọn dẹp các lỗi kiến trúc (God Object, Atomic Caching, 503/429 Fallback) theo tiêu chuẩn Multi-Agent Workflow:

### 1. Tối ưu hóa API LLM & Bản Vá Kháng Lỗi
- **API Key Rotation:** Đảo API Keys dự phòng khi dính lỗi `429 Resource Exhausted`.
- **Model Fallback:** Khi model chính `gemini-3.5-flash` dính lỗi `503 Service Unavailable`, hệ thống tự động lùi xuống model `gemini-2.5-flash` để tiếp tục làm việc.
- **Sửa lỗi nhận diện ngoại lệ (Substring Bug):** Khắc phục lỗi so khớp chuỗi `"503" in err_str` (do chuỗi mili-giây thời gian chờ của lỗi 429 chứa số 503 như `17.844805033s`). Bản vá đã được áp dụng đồng bộ cho cả phân tích riêng lẻ (`analyze_scorecards`) và phân tích tổng quan (`analyze_overall_market`) dựa trên trạng thái `"UNAVAILABLE"` và `"RESOURCE_EXHAUSTED"`.

### 2. Dọn dẹp God Object & Áp dụng Atomic Caching
- **Atomic Caching:** Đưa logic lưu cache trạng thái (`save_alert_cache`, `save_cycle_count`) vào khối lệnh `finally` của `main.py` để bảo toàn dữ liệu khi app crash.
- **Tách biệt Parser:** Loại bỏ toàn bộ Regex và `html` parser khỏi file nghiệp vụ `telegram_bot.py`, di dời sang module chuyên trách `formatters.py`.
- **Dọn dẹp mã nguồn thừa (Dead Code):** Loại bỏ tệp `data_contract.py` sau đợt rà soát do không có sự tích hợp thực tế nào, giữ cho codebase tinh gọn.
- **Bảo mật môi trường:** Xác minh và cấu hình thành công `.gitignore` để loại trừ hoàn toàn `.env` khỏi Git tracking.

---

## [2026-05-29] Phase 12 - Tích hợp RSI Range Shift Engine & Tối ưu Thông báo

### 1. Tích hợp RSI Range Shift Engine
Mục tiêu là tích hợp tri thức phân tích dải sinh thái 40/60 từ skill `rsi-range-shift-engine` vào hệ thống `bot_app` của Gemini 3.5 Flash.
- **Lọc cảnh báo**: Thay thế hoàn toàn các rule cũ bằng các tín hiệu của RSI Range Shift.
- **Báo cáo AI**: Tạo ra báo cáo độc lập thứ 2 chuyên phân tích kỹ thuật RSI Range Shift, đi kèm báo cáo so sánh sức mạnh mục tiêu/tham chiếu.

**Kiến trúc 2 Lớp Tối Ưu (2-Layer Pipeline) được áp dụng:**
1. **Lớp 1 (Rule-based Filter)**: Xóa tín hiệu cũ, áp dụng tín hiệu Bear-to-Bull Shift, Bull-to-Bear Shift, Vua Gặp Nạn dựa trên mốc RSI 40/60 và các chỉ số lượng hóa từ vnstock_data (Volume, % Mua Chủ Động, Khảng cách MA).
2. **Lớp 2 (Dual-Report AI Analyzer)**: Sử dụng Prompt Kép trong `ai_analyzer.py` để sinh ra 2 phần báo cáo độc lập mà chỉ tốn 1 lần gọi API, tránh lỗi 429.

### 2. Tinh chỉnh Logic Thông báo (Notification State Caching)
- Xây dựng cơ chế lưu trạng thái (`alert_cache`) bằng file JSON (`logs/.alert_cache`) để bot ghi nhớ trạng thái tín hiệu cuối cùng.
- Khi có tín hiệu (ví dụ Bull-to-Bear) xuất hiện lần đầu, bot gọi AI và gửi Telegram.
- Nếu ở chu kỳ tiếp theo, tín hiệu vẫn giữ nguyên, bot sẽ im lặng (Silent) để tránh spam.
- Chu kỳ báo cáo toàn diện (mỗi 30 phút) sẽ luôn tạo cảnh báo tổng thể bất chấp cache.

---

## [2026-05-25] Phase 11 - Nâng cấp vnstock_data v3.2.0

Bản nâng cấp Phase 11 tích hợp sâu rộng các tính năng mới từ bản cập nhật **vnstock_data v3.2.0** dựa trên đề xuất và đánh giá chuyên gia của Claude Opus 4.6.

### Phase 11A: Bổ sung Dữ liệu Chuyên sâu vào Prompt AI
- Gọi `fetch_rrg(symbol)` để lấy các chỉ số RRG_RS và RRG_RM.
- Gọi `fetch_peer_compare(symbol)` để so sánh định giá P/E, P/B, ROE... với ngành.
- Gọi `fetch_market_breadth()` để lấy độ rộng thị trường.

### Phase 11B: Tích hợp Dòng tiền Tự doanh & Áp lực Lệnh mua/bán chủ động
- Gọi `fetch_all_proprietary_flow()` để lấy dòng tiền tự doanh.
- Gọi `fetch_order_flow(symbol)` để tính Tỷ lệ Áp lực Mua Chủ động.

### Phase 11C: Vĩ mô & Hàng hóa (Dành cho Báo cáo Toàn diện)
- Bổ sung cấu hình ánh xạ hàng hóa `COMMODITY_MAPPING`.
- Gọi `fetch_commodity_price(name)` và `fetch_macro_global(method)` trong các chu kỳ báo cáo toàn diện (Full Report).

---

## [2026-05-19] Các Phase 1 -> 10 - Xây dựng Nền tảng

- **Giai đoạn 1-3:** Lên kế hoạch cấu trúc thư mục, module hóa (`data_fetcher.py`, `indicators.py`, `strategy.py`, `ai_analyzer.py`, `telegram_bot.py`).
- **Giai đoạn 4-5:** Cài đặt Virtual Environment, tích hợp `vnstock_data` và xử lý các lỗi dữ liệu (ví dụ: `match_price` -> `close_price`).
- **Giai đoạn 6-7:** Khôi phục `vnstock_ta`, tái cấu trúc mã nguồn, thiết lập Windows Task Scheduler, và xây dựng hệ thống Logging tập trung.
- **Giai đoạn 8:** Tối ưu hóa hiệu năng, thêm cơ chế Cache cho Benchmark, và chuyển đổi từ SDK Google Generative AI cũ sang `google.genai` mới, xử lý lỗi Rate Limit bằng cơ chế Retry Backoff.
