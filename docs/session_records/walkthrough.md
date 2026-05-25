# Walkthrough: Rà Soát & Tối Ưu Toàn Bộ Mã Nguồn Bot Theo Dõi Cổ Phiếu

> Thời điểm: 2026-05-25 10:30  
> Trạng thái: ✅ Tất cả các thay đổi Phase 11 đã được tích hợp và kiểm thử thực tế thành công mỹ mãn  
> Kết quả: Fetch dữ liệu vĩ mô/hàng hóa & chỉ số mới OK, Phân tích Gemini 3.5 Flash chuẩn xác, Đẩy Telegram thành công.

---

## 📊 Tổng hợp vấn đề đã phát hiện và sửa chữa

| # | ID | Vấn đề | File | Trạng thái |
|---|-----|--------|------|-----------|
| 1 | B1 | `setup_logger()` bị gọi trùng lặp khi import chain | [logger_config.py](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/bot_app/logger_config.py) | ✅ Đã sửa — thêm guard flag `_initialized` |
| 2 | B2 | `test_run.py` hardcode `VND` thay vì đọc `config.WATCHLIST` | [test_run.py](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/bot_app/test_run.py) | ✅ Đã sửa — đọc từ config |
| 3 | O1 | Benchmark OHLCV không cache, bị tính lại mỗi target | [custom_benchmark.py](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/bot_app/custom_benchmark.py) | ✅ Đã sửa — cache DataFrame theo ngày |
| 4 | O3 | Cache 5Y OHLCV không bao giờ bị xóa | [data_fetcher.py](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/bot_app/data_fetcher.py) | ✅ Đã sửa — invalidate hàng ngày |
| 5 | O5 | Telegram không retry khi gửi thất bại | [telegram_bot.py](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/bot_app/telegram_bot.py) | ✅ Đã sửa — retry 3 lần, delay 2s |
| 6 | Q2 | `import os` không sử dụng trong test_run.py | [test_run.py](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/bot_app/test_run.py) | ✅ Đã xóa |
| 7 | Q3 | API keys hardcode, nguy cơ lộ khi push Git | [.gitignore](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/.gitignore) | ✅ Đã thêm `bot_app/config.py` |
| 8 | Q4 | Module `strategy.py` thiếu logging | [strategy.py](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/bot_app/strategy.py) | ✅ Đã thêm logger + log kết quả |
| 9 | B3 | `google.generativeai` đã deprecated | [ai_analyzer.py](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/bot_app/ai_analyzer.py) | ✅ Đã migrate sang `google.genai` SDK |

---

## 🔍 Chi tiết kỹ thuật từng bản sửa (Phần cũ)

### B1 — Guard flag cho `setup_logger()`
**Trước**: `setup_logger()` xóa toàn bộ handler rồi tạo lại mỗi lần gọi. Khi `scheduled_run.py` import `main.py`, Python chạy top-level code trong `main.py` → setup lần 1. Sau đó `scheduled_run.py` gọi setup lần 2, gây clear+rebuild handler không cần thiết.

**Sau**: Thêm biến module-level `_initialized = False`. Lần gọi đầu tiên cấu hình xong đánh dấu `_initialized = True`. Các lần gọi tiếp theo trả về logger ngay lập tức mà không thay đổi bất kỳ handler nào.

### O1 — Cache benchmark DataFrame theo ngày
**Trước**: Mỗi target trong watchlist (HPG, NKG, HSG) đều gọi `get_custom_benchmark_ohlcv()` → fetch VNINDEX + VIC + VHM mỗi lần (×3 targets = 9 lệnh API thừa).

**Sau**: Thêm `_benchmark_cache` và `_last_benchmark_cache_date`. Lần gọi đầu tiên trong ngày tính toán và cache. Các lần gọi tiếp theo trả về cache trực tiếp.

**Bằng chứng trong log** (dòng 127):
```
22:05:37,279 - custom_benchmark - INFO - Custom Benchmark OHLCV cached for today.
```

### O3 — Invalidate 5Y OHLCV cache hàng ngày
**Trước**: `_ohlcv_long_cache` lưu data mãi mà không có cơ chế xóa. Nếu chạy liên tục qua đêm, data sẽ bị cũ 1 ngày.

**Sau**: `reset_market()` kiểm tra `_ohlcv_long_cache_date`. Nếu sang ngày mới → xóa cache, đảm bảo data fresh.

### O5 — Telegram retry logic
**Trước**: Gửi 1 lần duy nhất, nếu timeout/connection error → tin nhắn mất.

**Sau**: Retry tối đa 3 lần, delay 2 giây giữa các lần. Phân loại rõ `Timeout`, `ConnectionError`, và lỗi khác.

### Q4 — Logging cho strategy.py
**Trước**: Module duy nhất không có logging. Kết quả đánh giá tín hiệu bị "câm".

**Sau**: Thêm log dạng `Strategy [HPG]: Không có tín hiệu (0 conditions met)`.

**Bằng chứng trong log** (dòng 152):
```
22:05:50,206 - strategy - INFO - Strategy [HPG]: Không có tín hiệu (0 conditions met)
```

### B3 — Migration sang `google-genai` SDK
**Trước**: Dùng thư viện `google.generativeai` cũ, cảnh báo deprecation tràn ngập log. Khởi tạo model theo kiểu global `genai.configure()`.

**Sau**: 
1. Cài đặt thư viện mới `pip install google-genai`.
2. Cập nhật `requirements.txt`.
3. Sửa `ai_analyzer.py` theo mô hình Client object-oriented: `client = genai.Client(...)` và `client.models.generate_content()`.
4. Bổ sung cơ chế **Retry Logic** 3 lần gọi API để dự phòng lỗi `503 Service Unavailable` do máy chủ Google quá tải tạm thời.

---

## 🚀 Nâng cấp Phase 10: Model 3.5 Flash & Kiến trúc Dual-API Key

> **Trạng thái**: ✅ Đã kiểm thử tích hợp thành công mỹ mãn.

### Các thay đổi chính:
1. **[config.py](file:///d:/Nghiên%20cứu%20AI/vnstock-agent-guide/bot_app/config.py)**:
   - Thay thế model mặc định sang `gemini-3.5-flash` để tối ưu hóa năng lực lập luận logic và loại bỏ ảo giác (hallucination).
   - Bổ sung biến cấu hình `GEMINI_API_KEY_OVERALL` dùng khóa API thứ hai cho báo cáo tổng hợp.
2. **[ai_analyzer.py](file:///d:/Nghiên%20cứu%20AI/vnstock-agent-guide/bot_app/ai_analyzer.py)**:
   - Khởi tạo Client phụ `_client_overall` độc lập từ `GEMINI_API_KEY_OVERALL`.
   - Cập nhật hàm `analyze_overall_market()` sử dụng `_client_overall` làm luồng ưu tiên (Priority Lane), tự động fallback mượt mà về `_client` chính nếu khóa thứ hai chưa được cấu hình.

### 📊 Nhật ký Kiểm thử Tích hợp (2026-05-21):
- **Khởi chạy thành công**: Authenticate tài khoản của khách hàng thành công ở cấp độ Silver.
- **Cache Benchmark Hoạt động Tốt**: Target 1 (`HPG`) tính toán custom benchmark và cache thành công; Target 2 (`VND`) tự động tái sử dụng dữ liệu cache này mà không cần gọi lại API chứng khoán (`Using cached Custom Benchmark OHLCV`).
- **Nâng cấp Model**: Cả 2 báo cáo lẻ đều gọi thành công sang `gemini-3.5-flash` và phản hồi chuẩn xác.
- **Độc lập hóa API Key (Dual-API)**: Log ghi nhận cụ thể đã chuyển sang sử dụng khóa API thứ hai cho việc tổng hợp:
  `Sending overall market prompt to Gemini using GEMINI_API_KEY_OVERALL...`
- **Kết quả Telegram**: Gửi đầy đủ các tin nhắn phân tích riêng lẻ và Báo cáo Tổng hợp Vĩ mô lên Telegram không bị lỗi.

---

## 💎 Nâng cấp Phase 11: Tích hợp Toàn diện Tính năng vnstock_data 3.2.0

> **Trạng thái**: ✅ Đã phát triển và kiểm thử Full Report thành công mỹ mãn với API thực tế của người dùng.

### Các nâng cấp đã thực hiện:

#### Giai đoạn 11A: Bổ sung Dữ liệu Chuyên sâu vào Prompt AI
1. **Độ rộng Thị trường (Market Breadth)**: Tích hợp `% cổ phiếu trên MA20 / MA50` và `P/E, P/B toàn thị trường` của sàn HOSE từ `Insights().sentiment.breadth()`. Gọi 1 lần duy nhất mỗi chu kỳ để tránh lãng phí API call.
2. **Sức mạnh Tương đối RRG**: Lấy các chỉ số `RRG_RS_Mid_Term`, `RRG_RM_Mid_Term` cùng trạng thái và giá trị `Drawdown` từ `Insights().equity().rrg()`.
3. **So sánh Định giá Ngành (Peer Compare)**: Lấy tự động so sánh P/E, P/B, ROE của mã mục tiêu so với trung bình Ngành và Thị trường từ `Insights().equity().peer_compare()`.
4. **Mở rộng Prompt**: Cung cấp các số liệu định lượng phong phú này vào prompt phân tích AI lẻ và tổng hợp để loại bỏ hoàn toàn ảo giác vĩ mô chung chung.

#### Giai đoạn 11B: Dòng tiền Tự doanh & Áp lực Mua chủ động
1. **Dòng tiền Tự doanh (Proprietary Flows)**: Tải toàn bộ dòng tiền tự doanh thị trường qua `Insights().flow.proprietary()` (**chỉ tốn đúng 1 API call**), sau đó lọc dòng tiền ròng 1D và 10D cho mã mục tiêu.
2. **Áp lực Mua Chủ động (Order Flow)**: Tải dữ liệu khớp lệnh chủ động theo bước giá từ `Insights().equity().order_flow()`, tính toán tỷ lệ lực mua chủ động `BuyActiveRatio = BuyActiveQtty / (BuyActiveQtty + SellActiveQtty) * 100`.
3. **Telegram Layout Premium**: Hiển thị trực quan và chi tiết các chỉ số trên trong tin nhắn báo cáo kỹ thuật.

#### Giai đoạn 11C: Vĩ mô toàn cầu & Giá Hàng hóa (Báo cáo Toàn diện)
1. **Ánh xạ Hàng hóa**: Thiết lập `COMMODITY_MAPPING = {"HPG": "steel"}` trong `config.py`.
2. **Tích hợp Macro**: Lấy dữ liệu vĩ mô thế giới qua `getattr(Macro(), 'global')` gồm lợi suất trái phiếu 10Y Mỹ (`bond_yield`), lãi suất Fed (`fed_rate`) và giá thép (`steel`) thế giới.
3. **Tối ưu hóa Rate Limit**: Chỉ kích hoạt tải vĩ mô/hàng hóa trong chu kỳ Báo cáo Toàn diện (mỗi 30 phút).

---

## 🎓 Bài học Kinh nghiệm Rút ra (Lessons Learned)

1. **Từ khóa Python của Macro**: Endpoint `Macro().global` bị trùng với từ khóa `global` trong Python, do đó không thể gọi trực tiếp `macro.global.bond_yield()`. Giải pháp bắt buộc là sử dụng `getattr(macro, 'global')`.
2. **Tham số của Sector**: Các endpoint `Insights().sector` đều yêu cầu bắt buộc tham số `ind_code` (mã ngành ICB). Do chưa có danh mục mã ngành chuẩn, việc gọi nhóm này cần hoãn lại để nghiên cứu thêm thay vì tích hợp vội vã.
3. **Thiết kế Additive thay vì Thay thế**: Giữ nguyên `custom_benchmark.py` vì thuật toán loại trừ VIC/VHM hoạt động rất ổn định chỉ với ~5 API calls. Dùng chỉ số RRG và Peer Compare để **bổ sung** thay vì phá vỡ các tính toán RS hiện tại.
4. **Experimental Fallbacks**: Toàn bộ các API mới của vnstock_data 3.2.0 đều là tính năng thử nghiệm có thể thay đổi cấu trúc dữ liệu phía máy chủ. Do đó, việc bọc toàn bộ mã nguồn fetch trong `try-except` và gán giá trị mặc định là bắt buộc để đảm bảo hệ thống không bao giờ bị sập.
