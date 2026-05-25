# Kế hoạch Nâng cấp Hệ thống Theo dõi Cổ phiếu Tự động (v5 – Phase 11)

Bản nâng cấp Phase 11 tích hợp sâu rộng các tính năng mới từ bản cập nhật **vnstock_data v3.2.0** dựa trên đề xuất và đánh giá chuyên gia của Claude Opus 4.6. Toàn bộ thiết kế đảm bảo tính **bổ sung, an toàn, không phá vỡ logic cũ**, có **cơ chế fallback hoàn chỉnh (try/except)** cho các endpoint thử nghiệm và tối ưu số lượng API call để tránh bị Rate Limit.

---

## 1. Phân chia các Giai đoạn Tích hợp

### Phase 11A: Bổ sung Dữ liệu Chuyên sâu vào Prompt AI (An toàn, Không phá vỡ)
- **Mục tiêu**: Cung cấp cho Gemini AI thông tin định lượng phong phú về sức mạnh tương đối (RRG), so sánh định giá ngành (Peer Compare) và độ rộng thị trường (Market Breadth).
- **Chi tiết**:
  - `fetch_rrg(symbol)`: Lấy các chỉ số RRG_RS và RRG_RM mới nhất từ `Insights().equity().rrg()`.
  - `fetch_peer_compare(symbol)`: Lấy so sánh định giá P/E, P/B, ROE... với ngành từ `Insights().equity().peer_compare()`.
  - `fetch_market_breadth()`: Lấy độ rộng thị trường (% cổ phiếu nằm trên MA20/MA50) từ `Insights().sentiment.breadth()`.
- **Tối ưu hóa**: Chỉ gọi `rrg` và `peer_compare` cho **mã mục tiêu (target symbol)**, không gọi cho các mã tham chiếu để tránh lãng phí API call. `fetch_market_breadth` chỉ được gọi 1 lần duy nhất mỗi chu kỳ cho sàn HOSE.

### Phase 11B: Tích hợp Dòng tiền Tự doanh & Áp lực Lệnh mua/bán chủ động
- **Mục tiêu**: Bổ sung phân tích dòng tiền chuyên sâu vào Scorecard và hiển thị trên tin nhắn Telegram.
- **Chi tiết**:
  - `fetch_all_proprietary_flow()`: Lấy dòng tiền tự doanh của toàn thị trường từ `Insights().flow.proprietary()` (chỉ tốn **1 API call** cho tất cả các mã mục tiêu).
  - Lọc dòng tiền tự doanh cho riêng mã mục tiêu theo các mốc 1D, 10D, 1M.
  - `fetch_order_flow(symbol)`: Lấy dữ liệu phân bổ lệnh chủ động mua/bán theo bước giá từ `Insights().equity().order_flow()`, tính toán **Tỷ lệ Áp lực Mua Chủ động** = `BuyActiveQtty / (BuyActiveQtty + SellActiveQtty) * 100`.

### Phase 11C: Vĩ mô & Hàng hóa (Chỉ dành cho Báo cáo Toàn diện)
- **Mục tiêu**: Bổ sung bối cảnh vĩ mô toàn cầu và giá hàng hóa tương ứng với danh mục theo dõi của người dùng.
- **Chi tiết**:
  - Chỉ kích hoạt và gọi API trong các chu kỳ **Báo cáo Toàn diện (is_full_report = True)** (mặc định mỗi 3 chu kỳ = 30 phút).
  - Mapped Watchlist to Commodities: Ví dụ HPG -> `steel`, PVD -> `oil_crude`.
  - `fetch_commodity_price(name)`: Lấy giá hàng hóa tương ứng từ `Macro().commodity()`.
  - `fetch_macro_global(method)`: Lấy tỷ suất trái phiếu chính phủ (`bond_yield`) hoặc lãi suất Fed (`fed_rate`) từ `Macro().global` bằng hàm `getattr()`.

---

## 2. Chi tiết Đề xuất Thay đổi (Proposed Changes)

### 2.1 [MODIFY] [config.py](file:///d:/Nghiên cứu AI/vnstock-agent-guide/bot_app/config.py)
- Thêm cấu hình ánh xạ cổ phiếu mục tiêu với hàng hóa tương ứng để AI tham chiếu:
```python
COMMODITY_MAPPING = {
    "HPG": "steel",
    # Mở rộng trong tương lai: "PVD": "oil_crude", "PVS": "oil_crude"
}
```

### 2.2 [MODIFY] [data_fetcher.py](file:///d:/Nghiên cứu AI/vnstock-agent-guide/bot_app/data_fetcher.py)
- Triển khai 7 hàm fetch mới an toàn với cơ chế bọc `try-except` và `_rate_limit_pause()`:
  - `fetch_rrg(symbol)`
  - `fetch_peer_compare(symbol)`
  - `fetch_market_breadth()`
  - `fetch_all_proprietary_flow()`
  - `fetch_order_flow(symbol)`
  - `fetch_commodity_price(commodity_name)`
  - `fetch_macro_global(method_name)`

### 2.3 [MODIFY] [ai_analyzer.py](file:///d:/Nghiên cứu AI/vnstock-agent-guide/bot_app/ai_analyzer.py)
- Cập nhật hàm `generate_prompt()` để bổ sung bảng dữ liệu Peer Compare, RRG, Tự doanh, Lệnh chủ động vào phân tích lẻ của mã mục tiêu.
- Cập nhật hàm `generate_overall_prompt()` để đưa Độ rộng Thị trường (Breadth) cùng với thông tin Vĩ mô / Giá hàng hóa thế giới vào báo cáo tổng hợp chéo.

### 2.4 [MODIFY] [telegram_bot.py](file:///d:/Nghiên cứu AI/vnstock-agent-guide/bot_app/telegram_bot.py)
- Cập nhật hàm `format_scorecard_message()` để bổ sung hiển thị trực quan trên Telegram các thông số:
  - Chỉ số RRG mới (RS & RM) và Trạng thái Drawdown.
  - Tỷ lệ Áp lực Mua chủ động (tính từ Order Flow).
  - Khối lượng mua ròng tự doanh (1D và 10D).

### 2.5 [MODIFY] [main.py](file:///d:/Nghiên cứu AI/vnstock-agent-guide/bot_app/main.py)
- Điều phối toàn bộ dữ liệu mới:
  - Gọi `fetch_market_breadth` và `fetch_all_proprietary_flow` 1 lần duy nhất ở đầu mỗi chu kỳ.
  - Khi xử lý từng cổ phiếu mục tiêu (target symbol), lấy dữ liệu RRG, Peer Compare, Order Flow và Tự doanh tương ứng.
  - Nếu `is_full_report` là True, tiến hành fetch thêm giá hàng hóa (nếu có ánh xạ trong `COMMODITY_MAPPING`) và các chỉ báo Vĩ mô Toàn cầu (`bond_yield`).
  - Gộp tất cả vào thông tin Scorecard/Kết quả để gửi cho AI Analyzer và Telegram Bot.

---

## 3. Kế hoạch Kiểm thử & Xác minh (Verification Plan)

### Kiểm thử Tự động
1. Chạy file `test_run.py` để chạy thử nghiệm 1 chu kỳ hoàn chỉnh của bot ở chế độ test.
2. Kiểm tra log `logs/bot.log` để xác nhận:
   - Các API `[Experimental]` mới được gọi thành công mà không bị lỗi.
   - Cơ chế fallback hoạt động tốt nếu ngắt kết nối mạng hoặc API lỗi (bot vẫn chạy tiếp).
   - Tốc độ gọi API ổn định nhờ các khoảng nghỉ `_rate_limit_pause(0.3)`.

### Kiểm thử Thủ công
1. Xác nhận các tin nhắn Telegram gửi về nhóm chứa đầy đủ thông tin:
   - Phần hiển thị chỉ số RRG, Tự doanh, Áp lực mua chủ động.
   - Nhận định AI lẻ chứa phân tích tương quan định giá ngành từ Peer Compare.
   - Báo cáo Chiến lược Tổng quan Thị trường (Báo cáo cuối) chứa nhận định về Độ rộng Thị trường và Vĩ mô thế giới.
