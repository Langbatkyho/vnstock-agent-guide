# Phân tích Workflow và Đề xuất Cải tiến (Workflow Analysis)

Dựa trên toàn bộ phiên làm việc ngày 19/05/2026 xây dựng Hệ thống Theo dõi Cổ phiếu Tự động, dưới đây là phân tích về luồng công việc (workflow) đã thực hiện và những bài học rút ra để tối ưu hóa cho các dự án tiếp theo.

## 1. Phân tích Luồng công việc (Workflow Analysis)

Workflow của chúng ta đã trải qua 5 giai đoạn chính rất bài bản:

### Giai đoạn 1: Lên kế hoạch lặp (Iterative Planning)
Thay vì code ngay lập tức, chúng ta đã tinh chỉnh Kế hoạch Triển khai (Implementation Plan) qua 3 phiên bản:
- **V1:** Khung sườn cơ bản theo tài liệu `chi_so.md`.
- **V2:** Tích hợp Telegram, thêm cổ phiếu tham chiếu (SSI, VIX) và dữ liệu Intraday.
- **V3:** Tích hợp Gemini AI và Custom Benchmark (loại bỏ VIC/VHM).
**Đánh giá:** Rất thành công. Việc chốt thiết kế kiến trúc trước giúp tránh phải đập đi xây lại khi phát sinh yêu cầu mới.

### Giai đoạn 2: Rà soát khả thi (Feasibility Audit)
Trước khi chốt V3, AI đã đọc sâu vào tài liệu của `vnstock_data` và `vnstock_ta` để ánh xạ từng chỉ số yêu cầu sang API tương ứng.
**Đánh giá:** Bước này giúp phát hiện ra việc tính % Mua chủ động qua lệnh `trades()` sẽ tốn API call, dẫn đến quyết định chuyển sang dùng `volume_profile()`.

### Giai đoạn 3: Triển khai Code theo Module
Mã nguồn được chia nhỏ hợp lý ngay từ đầu: `data_fetcher`, `indicators`, `strategy`, `ai_analyzer`, `telegram_bot`.
**Đánh giá:** Tính module hóa giúp việc vô hiệu hóa thư viện `vnstock_ta` sau này diễn ra nhanh chóng, gọn gàng mà không làm sập toàn bộ hệ thống.

### Giai đoạn 4: Quản lý Môi trường & Gỡ lỗi (Environment & Debugging)
Xử lý các vấn đề thực tế phát sinh:
- Cài đặt Virtual Environment và thư viện bản quyền.
- Xử lý việc thiếu bản quyền `vnstock_ta` bằng cách viết lại logic bằng `pandas`.

### Giai đoạn 5: Kiểm thử thực tế và Tối ưu hóa (Testing & Refactoring)
Người dùng phát hiện lỗi `Giá hiện tại = 0`. AI tiến hành audit lại toàn bộ hệ thống:
- Sửa lỗi schema API (đổi `match_price` thành `close_price`).
- Sửa lỗi JSON serialize của Numpy.
- Thêm cơ chế chống Rate Limit (sleep) và tối ưu hóa Singleton (tái sử dụng Market instance).

### Giai đoạn 6: Khôi phục và Tái cấu trúc (Restoration & Refactoring)
Người dùng nâng cấp bản quyền `vnstock_ta`. AI tiến hành khôi phục code và rà soát lại toàn bộ:
- Tích hợp thành công `vnstock_ta` cho RSI và MACD.
- Phát hiện 5 điểm chưa bám sát kế hoạch ban đầu (sai keyword `data=`, sai ngưỡng RSI, thiếu label trạng thái).
- Khắc phục lỗi kiểu dữ liệu pandas Series không có thuộc tính `.values` khi gọi API.
- Tái cấu trúc (Refactor) lại MA để dùng chung đối tượng `Indicator` của `vnstock_ta` thay vì dùng Pandas rời rạc, giúp code nhất quán và gọn gàng hơn.

### Giai đoạn 7: Vận hành Tự động và Kiểm soát Log (Automation & Logging)
Thiết lập Task Scheduler cho Windows và thêm cơ chế Logging chuyên nghiệp (RotatingFileHandler).
**Đánh giá:** Phát hiện ra các rủi ro ngầm của Windows Task Scheduler như mất môi trường UTF-8 và sai thư mục làm việc hiện tại (CWD). Việc thiết kế hệ thống Logging tập trung (chạy ra cả file log xoay vòng và Console) giúp truy vết lỗi tự động dễ dàng hơn. Script Batch được cải thiện để tự tìm `.venv` và ép kiểu encoding `utf-8`.

### Giai đoạn 8: Tối ưu hiệu năng và Nâng cấp SDK (Optimization & SDK Migration)
Khách hàng yêu cầu rà soát tối ưu code và chuyển đổi SDK AI sang thư viện `google.genai` mới nhất.
**Đánh giá:** Quá trình Audit phát hiện và sửa 8 lỗi logic/hiệu năng (cache benchmark DataFrame theo ngày, invalidate cache 5Y, bảo vệ API key trong `.gitignore`, v.v.). Việc chuyển đổi từ SDK cũ (`google.generativeai`) sang SDK mới (`google.genai`) thành công bằng cách áp dụng mô hình `Client` object-oriented. Xử lý triệt để lỗi `503 Service Unavailable` từ Google bằng cơ chế Retry Loop.

---

## 2. Đề xuất Cải tiến Tối ưu cho Dự án tiếp theo

Để các dự án xây dựng ứng dụng tài chính/chứng khoán bằng Vnstock trong tương lai diễn ra trơn tru hơn, nhanh hơn và ít lỗi hơn, tôi đề xuất quy trình chuẩn sau:

### Cải tiến 1: Xác thực Schema API thực tế từ sớm (Live API Auditing)
**Vấn đề:** Lỗi `giá = 0` xảy ra do API `vnstock_data` phiên bản mới đổi tên cột từ `match_price` sang `close_price`.
**Giải pháp:** Trước khi viết code xử lý dữ liệu (`indicators.py`), AI nên chạy các script test nhỏ bằng terminal để in ra chính xác danh sách các cột (schema) trả về từ thư viện tại thời điểm hiện tại. Không nên phụ thuộc hoàn toàn vào trí nhớ hoặc tài liệu cũ.

### Cải tiến 2: Kiểm tra bản quyền trước khi thiết kế (License Pre-check)
**Vấn đề:** Viết code sử dụng `vnstock_ta` nhưng sau đó phải comment lại vì người dùng chưa có bản quyền module này.
**Giải pháp:** Ngay trong khâu "Requirement Gathering", AI cần xác nhận rõ người dùng đang sở hữu license của những thư viện nào (`vnstock_data`, `vnstock_ta`, `vnstock_news`, v.v.) để lên thiết kế phù hợp ngay từ đầu.

### Cải tiến 3: Xử lý định dạng dữ liệu (Data Serialization By Default)
**Vấn đề:** Lỗi không gửi được prompt cho Gemini vì dữ liệu numpy không tương thích JSON.
**Giải pháp:** Bất kỳ dự án nào có sự kết hợp giữa Pandas/Numpy và các thư viện gọi API (REST API, OpenAI, Gemini...), luôn luôn xây dựng sẵn hàm `_to_native_python_types()` ngay từ đầu để ép kiểu int64/float64 về int/float native của Python.

### Cải tiến 4: Thiết kế "Rate-Limit-Safe" làm mặc định
**Vấn đề:** Việc gọi API trong vòng lặp liên tục có nguy cơ bị ngắt kết nối hoặc block IP.
**Giải pháp:** 
- Áp dụng Singleton pattern cho các session như `Market()` hoặc `Quote()` ngay từ file template đầu tiên.
- Luôn mặc định thêm tham số độ trễ `time.sleep()` giữa các vòng lặp đối với các pipeline quét danh sách nhiều cổ phiếu.

### Cải tiến 5: Prompt AI tự thích ứng (Dynamic Prompting)
**Vấn đề:** Nếu một số dữ liệu bị thiếu (vd: bỏ RSI, MACD), AI LLM (Gemini) vẫn có thể bị ảo giác (hallucination) dựa trên prompt tĩnh.
**Giải pháp:** Xây dựng prompt động dựa trên dữ liệu đầu vào. Thay vì viết cứng: *"Nhận định sức mạnh dựa trên RSI"*, hãy lập trình prompt để chỉ liệt kê các chỉ báo *thực sự đang có* trong scorecard truyền vào.

### Cải tiến 6: Bám sát Implementation Plan và Tài liệu API (Strict Plan Adherence)
**Vấn đề:** Trong quá trình triển khai, đôi khi AI tự ý dùng thư viện khác (như `pandas.rolling()`) hoặc truyền sai keyword argument (`Indicator(df)` thay vì `Indicator(data=df)`) so với kế hoạch ban đầu, dẫn đến rủi ro khó bảo trì hoặc code bị lỗi ngầm.
**Giải pháp:** Luôn có bước "Cross-Check" (Đối chiếu chéo) mỗi module sau khi viết xong với Implementation Plan và tài liệu chính thức của thư viện. Đảm bảo 100% các ngưỡng thông số (như RSI 30-50), định dạng output (thêm label Trạng thái) và phương thức gọi hàm đều khớp với thiết kế.

### Cải tiến 7: Chuẩn hóa Môi trường cho Background Tasks (Automation Robustness)
**Vấn đề:** Task Scheduler trên Windows chạy ẩn thường thiếu biến môi trường, sai thư mục làm việc (CWD) và gây lỗi Unicode.
**Giải pháp:** Các file script tự động (như `.bat`, `.sh`) phải thiết lập rõ ràng thư mục làm việc, ép kiểu UTF-8 (ví dụ: `PYTHONUTF8=1`) và định tuyến output log ra file độc lập (`RotatingFileHandler`) để dễ chẩn đoán khi có lỗi ngầm.

### Cải tiến 8: Thiết kế Kháng lỗi (Resilient Design) cho Dịch vụ Bên ngoài
**Vấn đề:** Gửi tin nhắn Telegram bị nghẽn mạng, hoặc gọi Gemini bị lỗi 503 do tải cao dẫn đến sập chu kỳ xử lý.
**Giải pháp:** Mọi kết nối gọi API ra ngoài hệ thống bắt buộc phải bọc trong một **Retry Loop** (ví dụ: thử lại 3 lần, delay 2s) trước khi văng lỗi, nhằm chịu đựng các lỗi thoáng qua (transient errors).

---
**Kết luận:** Sự kết hợp giữa khả năng bóc tách vấn đề của người dùng và khả năng truy vết lỗi hệ thống của AI đã giúp chúng ta có một sản phẩm rất chất lượng. Việc áp dụng 8 cải tiến trên sẽ giúp rút ngắn thời gian phát triển các hệ thống tương đương trong tương lai, đạt chuẩn "production-ready" ngay từ lần chạy đầu tiên.
