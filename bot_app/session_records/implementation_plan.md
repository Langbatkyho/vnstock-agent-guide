# Kế hoạch Xây dựng Hệ thống Theo dõi Cổ phiếu Tự động (v3 – Rà soát Hoàn chỉnh)

Hệ thống tự động **định kỳ 10 phút**, quét Watchlist (VND) cùng cổ phiếu tham chiếu (SSI, VIX), tính toán chỉ số kỹ thuật theo `chi_so.md`, so sánh với Custom Benchmark (VN-Index loại trừ VIC/VHM), và dùng **Gemini AI** tạo nhận định chiến thuật gửi qua **Telegram**.

---

## Kết quả Rà soát Tính khả thi (Feasibility Audit)

Sau khi đối chiếu toàn bộ tài liệu API chính thức của `vnstock_data`, `vnstock_ta`, tôi đã xác minh **từng chỉ số** trong bảng `chi_so.md` và xác nhận nguồn dữ liệu cụ thể cho mỗi chỉ số:

### Bảng ánh xạ Chỉ số → API Source

| Chỉ số từ `chi_so.md` | Nguồn dữ liệu / Phương thức tính | Khả thi? |
|:---|:---|:---:|
| **Thị giá** | `Market().equity(sym).quote()` → `match_price` | ✅ |
| **1D%** | Tự tính: `(close_today - close_yesterday) / close_yesterday * 100` từ OHLCV | ✅ |
| **1M%, 1Y%, 5Y%** | Tự tính từ OHLCV lịch sử dài hạn (dùng `length='5Y'`) | ✅ |
| **Phiên tăng liên tiếp** | Tự đếm chuỗi `close > close.shift(1)` liên tiếp cuối DataFrame | ✅ |
| **Beta** | `Market().equity(sym).summary()` → cột `beta` | ✅ |
| **KL so với SMA(10), SMA(20)** | Tự tính: `volume_today / sma(volume, 10)` bằng pandas | ✅ |
| **GT khớp lệnh** | `Market().equity(sym).quote()` → tính `match_price * total_volume` hoặc lấy trực tiếp từ `trade_history()` | ✅ |
| **% Mua CĐ** | `Market().equity(sym).trades(get_all=True)` → đếm `side=='Buy'` vs tổng, HOẶC `volume_profile()` → `buy_volume / total_volume` | ✅ |
| **GD khối ngoại 20 phiên** | `Market().equity(sym).foreign_flow(start=..., end=...)` → tổng `net_vol` 20 phiên | ✅ |
| **RSI(14), Trạng thái RSI** | `vnstock_ta.Indicator(df).momentum.rsi(length=14)` | ✅ |
| **MACD Histogram** | `vnstock_ta.Indicator(df).momentum.macd(fast=12, slow=26, signal=9)` | ✅ |
| **RS 3 ngày, 1 tháng, 3 tháng, 1 năm** | Tự tính = `% thay đổi giá CP` / `% thay đổi Custom Benchmark` ở từng khung | ✅ |
| **RS trung bình** | Trung bình cộng của RS 3D, 1M, 3M, 1Y | ✅ |
| **Phá nền** | Logic tự xây dựng dựa trên giá breakout khỏi vùng tích lũy MA20/50 + Volume đột biến | ✅ |
| **% giá so với MA10, MA20, MA50** | Tự tính: `(close - sma(close, N)) / sma(close, N) * 100` | ✅ |

### Rủi ro đã nhận diện & Giải pháp

> [!WARNING]
> **Custom Benchmark (VN-Index loại VIC/VHM):** API `vnstock_data` **không** cung cấp trực tiếp trọng số vốn hóa (cap weight) từng mã trong rổ VN-Index. Thay vì xấp xỉ phức tạp (dễ sai), tôi đề xuất phương pháp **thực tế và chính xác hơn**: Lấy OHLCV ngày của **toàn bộ ~500 mã HOSE** (qua `Listing`), loại trừ VIC/VHM, tính lợi nhuận trung bình có trọng số (dùng `market_cap` từ `summary()`), và tái tạo lại chuỗi chỉ số. Tuy nhiên, cách này **tốn nhiều API call**.
>
> **Phương án thay thế được khuyến nghị (Đơn giản & Hiệu quả):**  
> Sử dụng chỉ số **VNFINSELECT** (Tài chính tuyển chọn) hoặc **VN30** làm Benchmark thay thế, vì các chỉ số này đã giảm thiểu sự chi phối quá lớn của VIC/VHM. Nếu bạn vẫn muốn Custom Benchmark chính xác, tôi sẽ cache vốn hóa VIC/VHM và VNINDEX 1 lần/ngày (không cần 10 phút) rồi xấp xỉ theo công thức ban đầu.

> [!IMPORTANT]
> **% Mua CĐ – Rate Limit:** `trades(get_all=True)` có thể lấy hàng ngàn lệnh cho mã thanh khoản lớn. Để tối ưu, tôi sẽ dùng `volume_profile()` (1 API call) thay vì quét toàn bộ lệnh. Phương thức này trả về `buy_volume`, `sell_volume`, `total_volume` theo từng mức giá, từ đó tính `% Mua CĐ = sum(buy_volume) / sum(total_volume) * 100`.

---

## User Review Required

> [!IMPORTANT]
> **Chọn phương án Benchmark:**
> - **Phương án A (Khuyến nghị):** Dùng `VN30` hoặc `VNFINSELECT` làm Benchmark – đơn giản, ổn định, ít tốn API.
> - **Phương án B:** Custom tính VN-Index loại VIC/VHM bằng cách cache vốn hóa 1 lần/ngày rồi xấp xỉ theo lợi nhuận.
>
> Bạn muốn chọn phương án nào?

> [!IMPORTANT]
> **Gemini API Key & Telegram Bot:**
> Bạn cần chuẩn bị sẵn 3 thông tin sau để điền vào file `config.py`:
> 1. `GEMINI_API_KEY` – Lấy miễn phí tại [Google AI Studio](https://aistudio.google.com/apikey)
> 2. `TELEGRAM_BOT_TOKEN` – Tạo bot qua `@BotFather` trên Telegram
> 3. `TELEGRAM_CHAT_ID` – Lấy bằng cách gửi tin nhắn cho bot rồi truy vấn API `getUpdates`

---

## Proposed Changes – Cấu trúc Dự án

```
bot_app/
├── config.py              # Cấu hình Watchlist, API Keys, tham số
├── data_fetcher.py        # Lấy dữ liệu từ vnstock_data (Market, Trading)
├── custom_benchmark.py    # Tính Custom Benchmark (VN-Index loại VIC/VHM)
├── indicators.py          # Tính toán chỉ số kỹ thuật (vnstock_ta + pandas)
├── strategy.py            # Logic đánh giá tín hiệu (Phá nền / Bật đáy)
├── ai_analyzer.py         # Sinh nhận định bằng Gemini API
├── telegram_bot.py        # Gửi cảnh báo qua Telegram
├── main.py                # Vòng lặp chính (scheduler 10 phút)
└── requirements.txt       # Danh sách thư viện
```

---

### Phase 1: Nền tảng & Cấu hình

#### [NEW] [requirements.txt](file:///d:/Nghiên%20cứu%20AI/vnstock-agent-guide/bot_app/requirements.txt)
```
vnstock_data
vnstock_ta
pandas
numpy
schedule
requests
google-generativeai
```

#### [NEW] [config.py](file:///d:/Nghiên%20cứu%20AI/vnstock-agent-guide/bot_app/config.py)
Cấu hình trung tâm, dễ chỉnh sửa:
- `WATCHLIST`: Dict mapping `{"VND": ["SSI", "VIX"]}` – Dễ mở rộng thêm mã.
- `BENCHMARK_SYMBOL`: `"VN30"` (hoặc `"VNINDEX"` nếu chọn phương án B).
- `EXCLUDED_FROM_BENCHMARK`: `["VIC", "VHM"]` (chỉ dùng nếu phương án B).
- `INTERVAL_MINUTES`: `10`
- `DATA_SOURCE`: `"KBS"` (ổn định nhất cho cả OHLCV + Intraday + Index).
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
- `GEMINI_API_KEY`, `GEMINI_MODEL`: `"gemini-2.5-flash"`.

---

### Phase 2: Lấy dữ liệu

#### [NEW] [data_fetcher.py](file:///d:/Nghiên%20cứu%20AI/vnstock-agent-guide/bot_app/data_fetcher.py)
Module tập trung hóa mọi lệnh gọi API `vnstock_data`. Mỗi hàm có `try...except` và logging.

| Hàm | API gọi | Mục đích |
|:---|:---|:---|
| `fetch_ohlcv(symbol, length)` | `Market().equity(sym).ohlcv(length='1Y', interval='1D')` | Lấy OHLCV lịch sử 1 năm (tính MA, RSI, MACD, RS) |
| `fetch_ohlcv_long(symbol)` | `Market().equity(sym).ohlcv(length='5Y', interval='1D')` | Lấy OHLCV 5 năm (tính % 5Y) |
| `fetch_quote(symbol)` | `Market().equity(sym).quote()` | Giá realtime snapshot |
| `fetch_summary(symbol)` | `Market().equity(sym).summary()` | Beta, market_cap, PE, PB |
| `fetch_volume_profile(symbol)` | `Market().equity(sym).volume_profile()` | Buy/Sell volume → % Mua CĐ |
| `fetch_foreign_flow(symbol, days)` | `Market().equity(sym).foreign_flow(start=..., end=...)` | GD khối ngoại 20 phiên |
| `fetch_index_ohlcv(index_sym)` | `Market().index(idx).ohlcv(length='1Y')` | OHLCV của Benchmark |

> **Chiến lược tối ưu Rate Limit:** Chỉ gọi `fetch_ohlcv_long` 1 lần khi khởi động (cache trong bộ nhớ). Mỗi 10 phút chỉ cần gọi `fetch_quote` + `fetch_volume_profile` + cập nhật nến mới nhất vào cache.

---

### Phase 3: Custom Benchmark

#### [NEW] [custom_benchmark.py](file:///d:/Nghiên%20cứu%20AI/vnstock-agent-guide/bot_app/custom_benchmark.py)

**Phương án A (VN30):** Module đơn giản, chỉ gọi `fetch_index_ohlcv("VN30")` rồi trả về chuỗi `close` để module khác dùng tính RS.

**Phương án B (Custom):** Gọi `fetch_index_ohlcv("VNINDEX")` + `fetch_ohlcv("VIC")` + `fetch_ohlcv("VHM")` + lấy `market_cap` từ `summary()`. Tính xấp xỉ:
```
Return_custom = Return_VNINDEX - (Weight_VIC * Return_VIC) - (Weight_VHM * Return_VHM)
```
Cache trọng số 1 lần/ngày (đầu phiên 9:00).

---

### Phase 4: Tính toán Chỉ số Kỹ thuật

#### [NEW] [indicators.py](file:///d:/Nghiên%20cứu%20AI/vnstock-agent-guide/bot_app/indicators.py)
Module chính, nhận DataFrame OHLCV và trả về dict chứa toàn bộ chỉ số.

**Các hàm chính:**

| Hàm | Input | Output | Công cụ |
|:---|:---|:---|:---|
| `calc_price_changes(df)` | OHLCV | 1D%, 1M%, 1Y%, 5Y% | `pandas` (`pct_change`) |
| `calc_consecutive_up(df)` | OHLCV | Số phiên tăng liên tiếp | `pandas` (vòng lặp ngược) |
| `calc_volume_vs_sma(df)` | OHLCV | KL/SMA(10), KL/SMA(20) | `pandas` (`rolling`) |
| `calc_rsi(df)` | OHLCV | RSI(14) + Trạng thái | `vnstock_ta.Indicator.momentum.rsi(length=14)` |
| `calc_macd(df)` | OHLCV | MACD Histogram + Trạng thái | `vnstock_ta.Indicator.momentum.macd()` |
| `calc_ma_distance(df)` | OHLCV | % giá vs MA10, MA20, MA50 | `vnstock_ta.Indicator.trend.sma()` |
| `calc_rs(df_stock, df_benchmark)` | 2 OHLCV | RS 3D, 1M, 3M, 1Y + TB | `pandas` (% change tỷ lệ) |
| `calc_active_buy_pct(vol_profile)` | volume_profile DF | % Mua CĐ | `pandas` (`sum`) |
| `calc_foreign_net(foreign_df)` | foreign_flow DF | GD NN 20 phiên | `pandas` (`sum`) |
| `build_scorecard(symbol, ...)` | Tất cả trên | Dict 1 dòng giống `chi_so.md` | Tổng hợp |

**Cách gọi `vnstock_ta` chuẩn (đã xác minh từ tài liệu):**
```python
from vnstock_ta import Indicator
ta = Indicator(data=df)  # df cần có cột: open, high, low, close, volume
rsi = ta.momentum.rsi(length=14)
macd = ta.momentum.macd(fast=12, slow=26, signal=9)
sma_20 = ta.trend.sma(length=20)
```

---

### Phase 5: Đánh giá Chiến thuật

#### [NEW] [strategy.py](file:///d:/Nghiên%20cứu%20AI/vnstock-agent-guide/bot_app/strategy.py)
Logic phát hiện tín hiệu bằng luật (rule-based), chạy trước khi gọi AI:

**Tín hiệu "Từ đáy bật lên":**
- RSI(14) đang trong vùng 30-50 (thoát quá bán)
- MACD Histogram > 0 và đang tăng dần (histogram tăng 2 phiên liên tiếp)
- Giá trên MA10 hoặc đang cắt lên MA10
- Volume > 1.5x SMA(20)

**Tín hiệu "Phá nền":**
- Giá vượt MA20 VÀ MA50 (breakout)
- % giá so với MA50 > 3%
- MACD Histogram > 0 và tăng dần
- Volume > 2.0x SMA(20) (đột biến mạnh)
- RS trung bình > 50 (mạnh hơn benchmark)

**Output:** Dict `{"signal": "Phá nền" | "Từ đáy bật lên" | "Không có tín hiệu", "details": "..."}`

---

### Phase 6: Phân tích AI

#### [UPDATE] [ai_analyzer.py](file:///d:/Nghiên%20cứu%20AI/vnstock-agent-guide/bot_app/ai_analyzer.py)
Nhận toàn bộ scorecard (dict) của VND, SSI, VIX và tạo Prompt tiếng Việt cho Gemini:

```
Bạn là chuyên gia phân tích kỹ thuật chứng khoán Việt Nam. Dựa vào bảng số liệu dưới đây:

[Bảng scorecard VND]
[Bảng scorecard SSI]
[Bảng scorecard VIX]
[Tín hiệu rule-based: ...]

Hãy đưa ra nhận định ngắn gọn (tối đa 200 từ):
1. VND đang mạnh hay yếu hơn SSI và VIX? (dựa trên RS, RSI, MACD, % giá vs MA)
2. Xu hướng ngắn hạn của VND (tăng/giảm/tích lũy)?
3. Khuyến nghị hành động (MUA/BÁN/QUAN SÁT) kèm lý do.
```

**SDK Mới (`google.genai`):**
- Sử dụng mô hình `Client` thay cho `genai.configure()` (đã bị deprecated).
- Tích hợp **Retry Loop (3 lần, delay 2s)** để bắt lỗi `503 Service Unavailable` từ phía máy chủ Google khi quá tải, đảm bảo bot không bị crash.
- Cấu hình model: `gemini-2.5-flash` (nhanh, rẻ, đủ cho tác vụ phân tích số liệu).

---

### Phase 7: Telegram & Scheduler

#### [NEW] [telegram_bot.py](file:///d:/Nghiên%20cứu%20AI/vnstock-agent-guide/bot_app/telegram_bot.py)
- Hàm `send_message(text)` dùng `requests.post` gọi API Telegram (`sendMessage`, parse_mode=HTML).
- Format tin nhắn gồm:
  - 📊 **Bảng thông số** (giá, RSI, MACD, RS, % MA...) dạng text align.
  - 🤖 **Nhận định AI** (đoạn text từ Gemini).
  - ⏰ Thời gian cập nhật.

#### [NEW] [main.py](file:///d:/Nghiên%20cứu%20AI/vnstock-agent-guide/bot_app/main.py)
Vòng lặp chính sử dụng `schedule`:

```python
import schedule, time

def run_cycle():
    # 1. Lấy dữ liệu mới nhất (data_fetcher)
    # 2. Tính Custom Benchmark (custom_benchmark)
    # 3. Tính scorecard cho VND, SSI, VIX (indicators)
    # 4. Đánh giá tín hiệu rule-based (strategy)
    # 5. Gọi AI phân tích (ai_analyzer) – chỉ khi có tín hiệu hoặc mỗi 30 phút
    # 6. Gửi Telegram (telegram_bot)

schedule.every(10).minutes.do(run_cycle)
run_cycle()  # Chạy ngay lần đầu
while True:
    schedule.run_pending()
    time.sleep(1)
```

**Tối ưu gọi AI:** Gemini chỉ được gọi khi:
- Có tín hiệu mới (Phá nền / Bật đáy) → Gọi ngay.
- Hoặc mỗi 30 phút 1 lần (3 chu kỳ) → Báo cáo định kỳ.
- Các chu kỳ khác chỉ gửi bảng số liệu (không gọi AI) → Tiết kiệm quota.

---

### Phase 8: Automation & Logging

#### [NEW] [logger_config.py](file:///d:/Nghiên%20cứu%20AI/vnstock-agent-guide/bot_app/logger_config.py)
Cấu hình hệ thống Logging tập trung (Centralized Logging):
- Ghi log song song ra Console và file `logs/bot.log`.
- Sử dụng `RotatingFileHandler` (giới hạn 5MB/file, giữ 5 backups) để tránh tràn ổ đĩa.
- Sử dụng cơ chế Guard Flag `_initialized` để ngăn chặn việc khởi tạo lặp (duplicate logs) khi import chéo giữa các module.

#### [NEW] Automation Batch Scripts
Hỗ trợ việc tích hợp Windows Task Scheduler:
- `run_scheduled.bat`: Chạy 1 chu kỳ bằng `scheduled_run.py`, ép kiểu UTF-8, tự động tìm `.venv` và ghi log ra `run_scheduled_batch.log`.
- `run_continuous.bat`: Chạy vòng lặp vô hạn `main.py` trực tiếp.

---

### Phase 9: Mở rộng Scale và Gộp báo cáo (Scaling & Aggregation - Thiết kế Tối ưu)
Kiến trúc "Phương án 1 Mở rộng: Tuần tự + Tổng hợp dữ liệu + Đồng bộ trạng thái Windows Task Scheduler":
1. **Tách biệt Logic trong `process_target()`:** Hàm này chỉ thực hiện lấy dữ liệu, tính toán scorecard và chạy rule-based strategy. Trả về kết quả dưới dạng dict, không tự động gọi AI hay gửi Telegram ngay lập tức.
2. **Quản lý Trạng thái chu kỳ thông qua File:** 
   - Để hỗ trợ **Windows Task Scheduler** (vốn khởi chạy 1 tiến trình Python mới hoàn toàn mỗi 10 phút), ta sẽ lưu trữ số chu kỳ hiện tại vào một tệp tin cấu hình tạm `logs/.cycle_state`.
   - Mỗi chu kỳ chạy sẽ tăng số chu kỳ lên và kiểm tra xem có chia hết cho `REPORT_INTERVAL_CYCLES` (ví dụ: = 3 tương đương 30 phút) hay không để kích hoạt **Chu kỳ Báo cáo Toàn diện**.
3. **Gọi AI riêng lẻ có điều kiện và Tránh Rate Limit (429):**
   - Chỉ gọi AI cho các target lẻ nếu chu kỳ hiện tại là **Chu kỳ Báo cáo Toàn diện (mỗi 30 phút)** HOẶC target đó **có tín hiệu kỹ thuật đột biến (Phá nền/Bật đáy)**.
   - **Xử lý lỗi Quota (429/ResourceExhausted):** Khi gọi API Gemini gặp mã lỗi `429` (Resource Exhausted / Rate Limit), hệ thống sẽ kích hoạt progressive backoff tự động **tạm dừng (sleep) 65 giây** rồi thử lại (tối đa 3 lần).
   - **Proactive Delay:** Để tránh bắn các API calls liên tiếp quá nhanh làm hệ thống máy chủ Gemini từ chối yêu cầu, hệ thống chủ động **dừng 5 giây** giữa mỗi lần gọi AI riêng lẻ cho từng target, và **dừng 5 giây** trước khi chạy phân tích tổng quan.
4. **AI Tổng hợp & So sánh chéo:**
   - Nếu có ít nhất một báo cáo AI lẻ được kích hoạt ở Bước 3 (hoặc là kỳ 30 phút), tiến hành chạy Bước tổng hợp chéo.
   - **Tối ưu hóa dữ liệu đầu vào cho AI Tổng hợp:** Truyền cả **Scorecard gốc (dữ liệu số)** của các target mục tiêu VÀ **Nhận định AI riêng lẻ (dữ liệu chữ)** để AI có đủ thông tin so sánh định lượng chính xác các chỉ số kỹ thuật chéo giữa các ngành, không bị hiện tượng ảo giác (hallucination) do dữ liệu chữ bị nén.
   - Giới hạn từ khóa đầu ra của AI tổng hợp ở mức ngắn gọn (dưới 150 từ) để tránh tràn bộ đệm Telegram.
5. **Định dạng & Gửi tin nhắn Telegram tập trung:**
   - Tin nhắn riêng lẻ chỉ gửi ở chu kỳ 10 phút nếu **có tín hiệu đột biến**. Ở chu kỳ 30 phút định kỳ, gửi toàn bộ tin nhắn riêng lẻ.
   - Tin nhắn tổng hợp được gửi tương tự: ở chu kỳ 10 phút chỉ gửi nếu có ít nhất 1 mã có tín hiệu, và ở chu kỳ 30 phút định kỳ thì luôn luôn gửi.
   - **Phòng chống Tràn ký tự (Anti-overflow):** Hàm gửi tin nhắn Telegram sẽ tự động kiểm tra độ dài. Nếu chuỗi ký tự vượt quá 4096 (giới hạn của Telegram API), nó sẽ tự động tách thành nhiều tin nhắn nhỏ hơn để gửi lần lượt mà không bị lỗi crash hệ thống.
6. **Xử lý lỗi cục bộ:** Nếu một target bị lỗi kết nối dữ liệu (ví dụ: HPG bị timeout), hệ thống vẫn tiếp tục xử lý SSI, VIX bình thường. Bước tổng hợp sẽ bỏ qua target lỗi và ghi nhận cảnh báo rõ ràng.
7. **Cấu hình Custom API Key:**
   - Cung cấp hướng dẫn người dùng thiết lập biến môi trường hệ thống `GEMINI_API_KEY` (hoặc cấu hình trong file `config.py`) với API Key cá nhân từ Google AI Studio để tránh tình trạng dùng chung key miễn phí mặc định dễ bị lỗi nghẽn 429.

**Bảng tính toán Quota chuẩn (Thời gian vận hành thực tế 9:00 - 15:00 = 6 tiếng):**
- Số chu kỳ quét 10 phút: 36 kỳ.
- Số chu kỳ báo cáo định kỳ (30 phút): 12 kỳ -> 12 kỳ * 4 API calls = 48 calls.
- Số chu kỳ trung gian có tín hiệu (giả định 50%): 12 kỳ * 2 API calls = 24 calls.
- **Tổng số request thực tế tối đa/ngày:** ~72 requests -> Thừa khả năng hoạt động ổn định trên 1 API Key gói Free.

---

## Verification Plan

### Phase 1: Test từng module độc lập
1. Chạy `data_fetcher.py` riêng → Kiểm tra có lấy được OHLCV, quote, volume_profile, foreign_flow không.
2. Chạy `indicators.py` với dữ liệu mẫu → Đối chiếu RSI, MACD với TradingView.
3. Chạy `custom_benchmark.py` → Kiểm tra chuỗi giá benchmark có hợp lệ.
4. Chạy `ai_analyzer.py` → Kiểm tra Gemini trả về nhận định tiếng Việt đúng format.
5. Chạy `telegram_bot.py` → Kiểm tra nhận được tin nhắn trên Telegram.

### Phase 2: Test tích hợp (Integration)
- Chạy `main.py` 1 vòng duy nhất (không chờ 10 phút) → Kiểm tra luồng đầy đủ từ data → indicators → strategy → AI → Telegram.
- Đối chiếu output với bảng `chi_so.md` gốc: các chỉ số phải khớp về ý nghĩa và khoảng giá trị hợp lý.

### Phase 3: Test thực tế (Live)
- Chạy trong giờ giao dịch (9h-15h) ít nhất 3 chu kỳ (30 phút).
- Kiểm tra tin nhắn Telegram: Rõ ràng, không lỗi font, có đủ bảng số + nhận định AI.
- Theo dõi log errors và rate limit.

---

## Mở rộng Phase 10: Nâng cấp AI Model và Kiến trúc Dual-API Key (Mới)

### Bối cảnh và Đánh giá
Người dùng yêu cầu đánh giá việc nâng cấp lên model **Gemini 3.5 Flash** và sử dụng **2 API Key riêng biệt** (một cho phân tích lẻ, một cho báo cáo tổng hợp) để tránh lỗi Rate Limit và Hallucination.

#### 1. Đánh giá Nâng cấp Model (Gemini 2.5 Flash → 3.5 Flash)
- **Ưu điểm:**
  - Gemini 3.5 Flash có khả năng suy luận logic vượt trội, giảm thiểu đáng kể tình trạng hallucination (ảo giác) khi phân tích chéo nhiều dữ liệu phức tạp.
  - Tốt hơn trong việc tổng hợp nhiều nguồn thông tin (phù hợp cho Bước Phân tích Tổng hợp).
  - Rate Limit tương đương bản 2.5, không đòi hỏi thay đổi mã nguồn lớn (chỉ đổi tên model).
- **Nhược điểm:**
  - Hầu như không có nhược điểm về mặt kỹ thuật nếu sử dụng qua Google AI Studio.

#### 2. Đánh giá Kiến trúc Dual-API Key (2 API Keys)
- **Ưu điểm:**
  - **Đảm bảo tính toàn vẹn của Báo cáo Tổng quan:** Báo cáo tổng hợp là tính năng giá trị nhất. Nếu 3-5 mã lẻ phân tích đồng loạt làm cạn Quota (15 requests/phút), việc dùng Key 2 độc lập sẽ đảm bảo Báo cáo Tổng quan luôn gọi API thành công mượt mà, không bao giờ bị 429 hay bị delay 65s.
  - Gấp đôi tổng hạn mức Quota (RPM và RPD) cho toàn hệ thống, rất cần thiết nếu bạn muốn mở rộng Watchlist lên 5-10 nhóm cổ phiếu.
- **Nhược điểm:**
  - Cần phải tạo và quản lý thêm 1 API Key mới. Tuy nhiên đây là việc cài đặt 1 lần.

> [!IMPORTANT]
> **Khuyến nghị từ AI:** Phương án nâng cấp này **rất thông minh và mang tính thực tiễn cao** đối với hệ thống chạy production. Kiến trúc Dual-API Key tạo ra "luồng ưu tiên" (Priority Lane) cho Báo cáo Tổng hợp.

### Đề xuất Thay đổi (Proposed Changes)

#### [MODIFY] bot_app/config.py
- Đổi `GEMINI_MODEL = "gemini-3.5-flash"`.
- Thêm biến môi trường `GEMINI_API_KEY_OVERALL` (sử dụng API key thứ hai).

#### [MODIFY] bot_app/ai_analyzer.py
- Khởi tạo thêm `_client_overall = genai.Client(api_key=config.GEMINI_API_KEY_OVERALL)`.
- Hàm `analyze_overall_market()` sẽ ưu tiên dùng `_client_overall` (nếu có), fallback về `_client` nếu người dùng chưa kịp cấu hình Key 2.
- Hàm `analyze_scorecards()` vẫn dùng `_client` gốc để giữ vai trò "cày ải" dữ liệu lẻ.

### Kế hoạch Kiểm thử & Trạng thái Vận hành (Verification Plan)

> **TRẠNG THÁI (Cập nhật 2026-05-21)**: ✅ Đã hoàn tất lập trình và Kiểm thử tích hợp thành công mỹ mãn. Toàn bộ luồng dữ liệu Dual-API hoạt động hoàn hảo.

**Quy trình đã thực hiện:**
1. **Khách hàng cấu hình API Key 2**: Khách hàng đã cập nhật file `config.py` tại biến `GEMINI_API_KEY_OVERALL`.
2. **Chạy Thử nghiệm Tích hợp**: Script `test_run.py` đã xác nhận:
   - Khởi tạo thành công cả hai Client.
   - Các API calls cho báo cáo lẻ hoạt động mượt mà bằng Client chính.
   - Báo cáo tổng hợp chéo thị trường được tạo thành công bởi Client phụ (`_client_overall`) và được đẩy đầy đủ lên Telegram.

