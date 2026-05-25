# Đánh giá Chuyên gia: Phản biện Báo cáo Gemini Flash 3.5 về Vnstock 3.2.0

**Ngày lập**: 25/05/2026  
**Model**: Claude Opus 4.6 (Thinking)  
**Mục tiêu**: Đối chiếu thực tế vs nhận định, chỉ ra sai sót, và đề xuất lộ trình thực tế

---

## I. Kết quả Kiểm chứng Thực tế (Audit)

Tôi đã viết và chạy một tập lệnh kiểm tra chuyên sâu trực tiếp trên môi trường `.venv` của bạn. Dưới đây là **bảng đối chiếu thực tế** giữa những gì changelog quảng cáo vs những gì thực sự tồn tại:

### Insights Endpoints

| Endpoint | Changelog nói | Thực tế | Dữ liệu trả về |
|---|---|---|---|
| `Insights().equity().order_flow()` | ✅ | ✅ Hoạt động | DataFrame: MatchPrice, BuyActiveQtty, SellActiveQtty (theo **bước giá**) |
| `Insights().equity().order_flow_history()` | ✅ | ✅ Tồn tại | Chưa test dữ liệu |
| `Insights().equity().peer_compare()` | ✅ | ✅ Hoạt động | 1 row × 25 cols: Security_PE, Security_ROE, Industry_ROE, Market_ROE... |
| `Insights().equity().rrg()` | ✅ | ✅ Hoạt động | 250 rows × 14 cols: RRG_RS, RRG_RM (Short/Mid/Standard), RSI_14, Drawdown |
| `Insights().sector()` | ✅ 6 hàm | ⚠️ Yêu cầu `ind_code` | Cần truyền mã ngành — **chưa rõ danh sách mã ngành hợp lệ** |
| `Insights().flow.active()` | ✅ | ✅ Tồn tại | — |
| `Insights().flow.foreign()` | ✅ | ✅ Tồn tại | — |
| `Insights().flow.proprietary()` | ✅ | ✅ Hoạt động | 660 rows × 11 cols: volume/value theo 1d, 10d, 1m, 3m, 6m |
| `Insights().sentiment.breadth()` | ✅ | ✅ Hoạt động | 744 rows × 10 cols: PE, PB, above_ma50_pct, above_ma20_pct, position_line |
| `Insights().sentiment.contribution()` | ✅ | ✅ Tồn tại | — |
| `Insights().sentiment.heatmap()` | ✅ | ✅ Tồn tại | — |

### Macro Unified UI

| Endpoint | Changelog nói | Thực tế | Ghi chú |
|---|---|---|---|
| `Macro().economy()` | ✅ | ✅ 12 hàm | gdp, cpi, credit, fdi, import_export, money_supply, state_budget, total_investment... |
| `Macro().currency()` | ✅ | ✅ 7 hàm | deposit_rate, exchange_rate, interbank_rate, omo, policy_rate... |
| `Macro().commodity()` | ✅ | ✅ 15 hàm | gold, steel, oil_crude, iron_ore, corn, soybean, pork, listing... |
| `Macro().global` | ✅ | ✅ 3 hàm | bond_yield, fed_rate, index — **truy cập bằng `getattr(macro, 'global')`** |

> [!IMPORTANT]
> **Phiên bản thực tế**: `vnstock_data.__version__` trả về **`3.0.0`**, KHÔNG phải `3.2.0`. Tuy nhiên, toàn bộ endpoints mới đã có mặt và hoạt động. Điều này cho thấy các tính năng được bổ sung phía server hoặc qua các gói phụ thuộc (vnii), không phải qua version bump của vnstock_data.

> [!WARNING]
> **Gói vnii chưa cập nhật**: Dù bạn nói đã nâng lên `0.2.3`, banner khởi động vẫn hiển thị `Current: 0.2.1`. Bạn cần kiểm tra lại bằng lệnh:
> ```bash
> pip show vnii
> ```

---

## II. Phản biện Báo cáo của Gemini Flash 3.5

### ❌ Sai sót 1: "Custom Benchmark tải ~500 mã HOSE" — SAI HOÀN TOÀN

Báo cáo trước viết:
> *"Việc tính RS trong custom_benchmark.py đang phải tải toàn bộ ~500 mã HOSE... tốn cực kỳ nhiều API call"*

**Thực tế**: Tôi đã đọc kỹ [custom_benchmark.py](file:///d:/Nghiên cứu AI/vnstock-agent-guide/bot_app/custom_benchmark.py). Module này chỉ thực hiện **~5 API calls**:
1. `fetch_ohlcv(VNINDEX)` — 1 call
2. `fetch_summary(VNINDEX)` — 1 call
3. `fetch_summary("VIC")` — 1 call
4. `fetch_summary("VHM")` — 1 call
5. `fetch_ohlcv("VIC")` + `fetch_ohlcv("VHM")` — 2 calls

Thuật toán lấy dữ liệu VN-Index rồi **trừ đi phần đóng góp theo trọng số** của VIC và VHM. Nó KHÔNG hề quét 500 mã. Con số "giảm 95% API call" là suy luận dựa trên tiền đề sai.

### ❌ Sai sót 2: "Thay thế custom_benchmark.py bằng RRG" — NHẦM LẪN CHỨC NĂNG

Báo cáo trước đề xuất:
> *"Thay thế module tự tính custom_benchmark.py bằng việc gọi chỉ số RRG"*

**Đây là lỗi logic nghiêm trọng**. Custom benchmark và RRG phục vụ **hai mục đích hoàn toàn khác nhau**:

| | Custom Benchmark | RRG |
|---|---|---|
| **Mục đích** | Tạo chỉ số VN-Index loại trừ VIC/VHM làm **chuỗi tham chiếu** | Đo sức mạnh tương đối & động lượng của 1 mã so với VNINDEX gốc |
| **Output** | DataFrame OHLCV giả lập (dùng để tính RS thủ công) | Điểm RS-Ratio, RS-Momentum, RSI, Drawdown |
| **Tùy biến** | Có — bạn chọn loại trừ mã nào | Không — luôn so với VNINDEX nguyên bản |

Nếu thay thế custom benchmark bằng RRG, bạn **mất hoàn toàn** ý đồ thiết kế ban đầu (so sánh với VN-Index đã loại VIC/VHM). Đây là quyết định thiết kế cần bạn cân nhắc, không phải một tối ưu kỹ thuật đơn giản.

### ❌ Sai sót 3: "peer_compare sẽ loại bỏ watchlist thủ công" — NHẦM LẪN VAI TRÒ

Báo cáo trước viết:
> *"Tích hợp peer_compare để loại bỏ việc cấu hình watchlist thủ công"*

**Thực tế**: Watchlist (`config.WATCHLIST`) xác định **bạn muốn theo dõi mã nào**. `peer_compare()` cung cấp **số liệu so sánh** cho mã đó. Chúng bổ sung cho nhau, không thay thế nhau. Bạn vẫn cần watchlist để bot biết cần giám sát HPG hay VND.

### ❌ Sai sót 4: "order_flow phân bổ theo Lệnh Lớn/Trung bình/Nhỏ" — MÔ TẢ SAI DỮ LIỆU

Báo cáo trước mô tả:
> *"order_flow phân bổ dòng tiền chủ động mua/bán theo các phân khúc lệnh (Lớn/Trung bình/Nhỏ)"*

**Dữ liệu thực tế** từ `order_flow()`:
```
   MatchPrice  BuyActiveQtty  SellActiveQtty  NoneActiveQtty
0       26350              0         1042000               0
1       26400        1721100         5873100               0
```
Dữ liệu phân bổ theo **bước giá** (MatchPrice), KHÔNG phải theo kích thước lệnh. Đây vẫn là dữ liệu cực kỳ giá trị (cho biết áp lực mua/bán ở từng mức giá), nhưng mô tả sai sẽ dẫn đến hiểu sai khi thiết kế chiến lược.

### ⚠️ Thiếu sót: Không kiểm tra `Insights().sector()` cần tham số `ind_code`

Changelog quảng cáo 6 hàm sector (flow, rrg, valuation, members...), nhưng báo cáo trước không phát hiện `sector()` yêu cầu tham số bắt buộc `ind_code`. Nếu không biết danh sách mã ngành ICB hợp lệ, ta không thể dùng được nhóm endpoint này.

---

## III. Những gì Báo cáo trước ĐÚNG

Mặc dù có nhiều sai sót về chi tiết, hướng đi tổng thể là hợp lý:

1. **✅ Tích hợp `breadth()` vào báo cáo tổng quan** — Đúng và cực kỳ có giá trị. Dữ liệu breadth (% mã trên MA20, MA50) cho phép AI đánh giá thị trường "xanh vỏ đỏ lòng" hay tăng đồng thuận.

2. **✅ Tích hợp `proprietary()` (dòng tiền tự doanh)** — Đúng. Dữ liệu tự doanh 660 mã theo nhiều khung thời gian (1d, 10d, 1m, 3m, 6m) là chỉ báo quan trọng ở thị trường VN.

3. **✅ Cần fallback cho endpoints `[Experimental]`** — Đúng. Mọi lệnh gọi mới phải được bọc trong try/except để không làm sập bot.

4. **✅ `peer_compare()` bổ sung giá trị cho prompt AI** — Đúng. 25 cột so sánh định giá tự động là thông tin cực kỳ phong phú cho Gemini phân tích.

5. **✅ Giá hàng hóa liên quan đến watchlist** — Đúng. HPG→steel, PVD→oil_crude là tương quan ngành hữu ích.

---

## IV. Đánh giá Chuyên gia: Ưu tiên Thực tế

Dựa trên dữ liệu kiểm chứng, tôi phân loại các cơ hội nâng cấp theo **giá trị thực tế / chi phí triển khai / rủi ro**:

### 🏆 Ưu tiên 1 (Giá trị cao, Rủi ro thấp): Bổ sung dữ liệu vào Prompt AI

Các endpoint sau trả về dữ liệu sẵn có, gọi 1 lần, không ảnh hưởng đến logic hiện tại:

| Endpoint | Tích hợp vào | Giá trị |
|---|---|---|
| `peer_compare()` | Prompt của `analyze_scorecards()` | AI có bảng so sánh PE/PB/ROE tự động với ngành |
| `rrg()` | Scorecard — thêm trường `rrg_rs`, `rrg_momentum` | Sức mạnh tương đối chuyên nghiệp (bổ sung, KHÔNG thay thế RS hiện tại) |
| `breadth()` | Prompt của `analyze_overall_market()` | Bức tranh toàn cảnh: % mã trên MA20/MA50 |

**Thay đổi code**: Chỉ cần thêm hàm fetch mới trong `data_fetcher.py`, thêm vài trường vào scorecard, và mở rộng prompt. Không đụng đến kiến trúc hiện tại.

### 🥈 Ưu tiên 2 (Giá trị trung bình, Rủi ro trung bình): Dòng tiền chuyên sâu

| Endpoint | Tích hợp vào | Lưu ý |
|---|---|---|
| `order_flow()` | Scorecard — tính tỷ lệ mua/bán chủ động theo bước giá | Bổ sung cho `volume_profile` hiện tại, không thay thế |
| `flow.proprietary()` | Scorecard — lọc dòng tiền tự doanh cho mã mục tiêu | Dữ liệu 660 mã → cần filter theo symbol |

**Rủi ro**: Thêm 2-3 API call mỗi chu kỳ. Với rate limit hiện tại (đã gặp vấn đề), cần pause hợp lý giữa các call.

### 🥉 Ưu tiên 3 (Giá trị bổ sung, Đánh giá thêm): Vĩ mô & Hàng hóa

| Endpoint | Lưu ý |
|---|---|
| `Macro().commodity().steel()` | Chỉ gọi trong chu kỳ báo cáo toàn diện (30 phút), không gọi mỗi 10 phút |
| `Macro().global.bond_yield()` | Thông tin bổ sung cho AI, không cần thiết cho strategy rule-based |
| `Insights().sector(ind_code=?)` | **Chưa rõ danh sách `ind_code`** — cần khám phá thêm trước khi tích hợp |

### ⛔ KHÔNG nên làm ngay:

1. **Thay thế `custom_benchmark.py`** — Module này hoạt động ổn định, chỉ tốn ~5 API calls, và phục vụ ý đồ thiết kế riêng (loại VIC/VHM). Đừng phá bỏ thứ đang chạy tốt.
2. **Loại bỏ watchlist thủ công** — Watchlist là cấu hình ý định của người dùng, không nên tự động hóa.
3. **Tích hợp toàn bộ Macro vào mỗi chu kỳ** — Quá tốn API calls và không cần thiết cho phân tích kỹ thuật intraday.

---

## V. Lộ trình Đề xuất (Thực tế)

### Phase 11A: Bổ sung Dữ liệu Chuyên sâu vào Prompt AI (An toàn, Không phá vỡ)

Thêm 3 hàm fetch mới vào `data_fetcher.py`:
- `fetch_rrg(symbol)` → trả về RRG_RS, RRG_RM mới nhất
- `fetch_peer_compare(symbol)` → trả về bảng so sánh ngành
- `fetch_market_breadth()` → trả về % mã trên MA20/MA50

Tích hợp vào prompt AI mà **không thay đổi** logic của scorecard, strategy, hay benchmark hiện tại.

### Phase 11B: Tích hợp Dòng tiền Tự doanh & Order Flow

Sau khi 11A ổn định:
- Thêm `fetch_proprietary_flow(symbol)` — lọc từ 660 mã
- Thêm `fetch_order_flow(symbol)` — tính % áp lực mua/bán
- Bổ sung vào scorecard và tin nhắn Telegram

### Phase 11C: Vĩ mô & Hàng hóa (Chỉ cho Báo cáo Toàn diện)

Chỉ gọi trong chu kỳ `is_full_report`:
- Giá thép/dầu thô cho HPG/nhóm dầu khí
- Breadth + contribution cho báo cáo tổng quan

---

## VI. Tóm tắt Đánh giá

| Khía cạnh | Gemini Flash 3.5 | Đánh giá của tôi |
|---|---|---|
| Hướng đi tổng thể | ✅ Đúng | Các endpoint mới thực sự có giá trị |
| Mô tả custom_benchmark | ❌ Sai (nói 500 mã, thực tế 5 call) | Cần giữ nguyên, không thay thế |
| Đề xuất thay RRG cho benchmark | ❌ Nhầm chức năng | RRG bổ sung, không thay thế |
| Mô tả order_flow | ❌ Sai (nói phân lệnh lớn/nhỏ) | Thực tế phân theo bước giá |
| Đề xuất bỏ watchlist | ❌ Nhầm vai trò | Watchlist là cấu hình người dùng |
| Tích hợp breadth/peer_compare | ✅ Đúng | Ưu tiên cao nhất |
| Fallback cho Experimental | ✅ Đúng | Bắt buộc |
| Ước tính giảm 95% API | ❌ Sai (dựa trên tiền đề sai) | Thực tế thêm vài call, không giảm |
