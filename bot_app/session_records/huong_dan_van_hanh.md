# HƯỚNG DẪN VẬN HÀNH, GHI LOG & LẬP LỊCH TỰ ĐỘNG BOT THEO DÕI CỔ PHIẾU (WINDOWS)

Tài liệu này hướng dẫn chi tiết cách vận hành hệ thống Bot theo dõi cổ phiếu Việt Nam (tích hợp Vnstock, Indicators, Gemini AI và Telegram) và cách chẩn đoán lỗi qua hệ thống **Ghi nhận hoạt động (Logging System)** mới thiết lập.

Để hỗ trợ bạn tốt nhất trên Windows, hệ thống đã được trang bị **3 tệp Batch thực thi nhanh (`.bat`)** thông minh, **1 script chuyên dụng (`scheduled_run.py`)** và **hệ thống tự động ghi Log ra File** chuyên nghiệp.

---

## 📂 Tổng quan về các tệp vận hành & Cấu trúc Log

Trong thư mục `bot_app/` của bạn hiện tại có các tệp hỗ trợ chạy bot sau:

| Tên tệp | Vai trò | Cách sử dụng phù hợp |
| :--- | :--- | :--- |
| **`run_test.bat`** | Chạy nhanh `test_run.py` | Kiểm tra nhanh kết nối dữ liệu, Gemini AI và Telegram |
| **`run_continuous.bat`** | Chạy `main.py` (vòng lặp liên tục) | Thích hợp nếu treo máy 24/7, tự động lặp theo phút cấu hình |
| **`run_scheduled.bat`** | Chạy `scheduled_run.py` (1 chu kỳ duy nhất) | **Khuyên dùng** - Dùng phối hợp với **Windows Task Scheduler** |

### 📝 Hệ thống ghi Log hoạt động mới thiết lập
Hệ thống hiện tại tự động ghi nhận hoạt động và lưu trữ vào thư mục **`bot_app/logs/`** nhằm hỗ trợ bạn theo dõi và gỡ lỗi khi chạy ngầm:
* **`logs/bot.log`**: Lưu nhật ký nghiệp vụ của Python (kết nối dữ liệu Vnstock, tính TA, gọi AI, kết quả gửi Telegram, các lỗi phát sinh trong mã nguồn). Tệp này tự động xoay vòng khi đạt 5MB (tối đa 5 file backup) để không tốn đĩa.
* **`logs/run_scheduled_batch.log`**: Lưu nhật ký khởi động của tệp Batch khi chạy tự động từ Task Scheduler. **Cực kỳ quan trọng** để phát hiện lỗi không kích hoạt được môi trường ảo hoặc Python bị lỗi crash trước khi kịp chạy chương trình.

---

## 🔑 Cấu hình API Keys (Đặc biệt quan trọng: Kiến trúc Dual-API)

Hệ thống được thiết kế tối ưu với **Kiến trúc Dual-API Key** để vượt qua giới hạn Rate Limit của Google Gemini (gói Free). Bạn cần đảm bảo đã cấu hình đúng trong file `bot_app/config.py`:

1. **`GEMINI_API_KEY`**: Khóa API chính, dùng để "cày ải" phân tích dữ liệu cho từng nhóm cổ phiếu lẻ (ví dụ: quét HPG, VND, MWG).
2. **`GEMINI_API_KEY_OVERALL`**: Khóa API phụ (Luồng ưu tiên - Priority Lane), được dành riêng ĐỘC QUYỀN cho tác vụ cuối cùng: **Tổng hợp Báo cáo Toàn cảnh**. Điều này đảm bảo dù các báo cáo lẻ có gọi API liên tục làm cạn kiệt Quota, báo cáo quan trọng nhất vẫn luôn thành công.

**Cách cập nhật**:
* Mở file `bot_app/config.py`.
* Tìm đến dòng định nghĩa biến và điền 2 API Keys khác nhau mà bạn lấy từ Google AI Studio.
* *(Hệ thống có cơ chế fallback tự động: nếu bạn chưa cấu hình khóa thứ hai, nó sẽ tự động dùng lại khóa chính, nhưng rủi ro dính lỗi 429 Rate Limit sẽ cao hơn).*

---


## 🚀 1. Cách chạy thử thủ công (Test Run)

Để kiểm tra nhanh xem hệ thống có hoạt động ổn định hay không, bạn chỉ cần:

1. Mở thư mục `d:\Nghiên cứu AI\vnstock-agent-guide\bot_app`.
2. Click đúp chuột vào tệp **`run_test.bat`**.
3. Cửa sổ Command Prompt sẽ xuất hiện, tự động kích hoạt môi trường ảo Python của bạn (`.venv`) và tiến hành quét cổ phiếu.
4. Mở file **`bot_app/logs/bot.log`** để xem các thông tin đã được ghi nhận song song một cách tự động.

---

## ⏰ 2. Thiết lập chạy tự động theo lịch & Gỡ lỗi Task Scheduler

Khi bạn chạy bằng tay (Click đúp `run_test.bat`) thì thành công, nhưng lên lịch bằng Windows Task Scheduler dạng **One time / Daily** lại không thấy gửi Telegram. **Lý do phổ biến nhất trên Windows:**
* **Thiếu môi trường hoạt động ngầm (Non-interactive session)**: Khi chạy ngầm từ Task Scheduler, biến môi trường hệ thống `%USERPROFILE%` bị trống hoặc bị trỏ sai, dẫn đến tệp Batch cũ không thể tìm thấy thư mục môi trường ảo `.venv` để kích hoạt. Khi đó, nó dùng Python mặc định của Windows (không có sẵn thư viện `vnstock_data` hay `vnstock_ta`) dẫn đến chương trình bị crash ngay lập tức mà không có thông báo lỗi ra màn hình.

### 🛠️ Giải pháp thông minh đã được áp dụng:
1. **Tìm kiếm môi trường ảo đa hướng (Robust Search)**: File `.bat` mới đã được nâng cấp để tìm kiếm môi trường ảo theo cả biến `%USERPROFILE%`, đường dẫn cứng trực tiếp `C:\Users\Langbatkyho\.venv` và đường dẫn tương đối `%~dp0..\.venv`. Đảm bảo kích hoạt thành công 100% dù chạy ngầm.
2. **Ghi đè log từ CMD**: Khi chạy từ Task Scheduler với đối số `--scheduled`, mọi lỗi phát sinh (bao gồm cả lỗi crash thư viện) đều được tệp batch chuyển hướng ghi vào **`logs/run_scheduled_batch.log`**. Bạn có thể mở tệp này để biết chính xác nguyên nhân lỗi.

---

### Hướng dẫn cấu hình chuẩn xác trong Windows Task Scheduler

Để đảm bảo tác vụ tự động hoạt động hoàn hảo, bạn vui lòng cấu hình chính xác theo các bước sau:

1. **Mở Windows Task Scheduler**: Nhấn phím `Windows`, gõ **Task Scheduler** và mở nó lên.
2. **Tạo tác vụ mới (Create Task)**: Chọn *Create Task...* ở cột Actions bên phải.
3. **Cấu hình Tab General (Chung)**:
   * **Name**: Đặt tên (ví dụ: `Bot_Theo_Doi_Co_Phieu`).
   * **Security Options**:
     * Chọn **Run only when user is logged on** (Chạy khi người dùng đã đăng nhập - **Khuyên dùng** cho máy cá nhân vì chế độ này có đầy đủ quyền truy cập biến môi trường và thư mục người dùng tốt nhất).
     * Nếu bắt buộc phải chọn *Run whether user is logged on or not*, hãy đảm bảo tài khoản chạy tác vụ là tài khoản chính của bạn (`Langbatkyho`), tích chọn **Run with highest privileges**.
4. **Cấu hình Tab Triggers (Lịch trình)**:
   * Nhấn *New...* -> Thiết lập lịch chạy.
   * Để chạy thử nghiệm One time: Đặt thời gian chạy trong tương lai vài phút.
   * Để chạy định kỳ trong giờ giao dịch: Chọn *Weekly*, chọn từ *Monday* đến *Friday*, đặt giờ bắt đầu là `9:00:00 AM`, tích chọn **Repeat task every 10 minutes** với khoảng thời gian **for a duration of: 6 hours** (hết giờ giao dịch 15h00 sẽ tự dừng).
   * **Lưu ý về chu kỳ báo cáo:** Hệ thống được thiết kế chạy 10 phút/lần, nhưng sẽ chỉ báo cáo nếu có tín hiệu đột biến. Cứ mỗi 30 phút, hệ thống sẽ tự động gửi một **Báo cáo Toàn diện** (bao gồm toàn bộ các nhóm cổ phiếu và Nhận định Tổng quan Thị trường).
5. **Cấu hình Tab Actions (Hành động) - BƯỚC QUAN TRỌNG NHẤT**:
   * Nhấn *New...* -> Chọn Action là **Start a program**.
   * **Program/script**: Bấm *Browse...* trỏ tới file:
     `d:\Nghiên cứu AI\vnstock-agent-guide\bot_app\run_scheduled.bat`
   * **Add arguments (optional)**: Nhập chính xác đối số: `--scheduled`
     *(Đối số này giúp file batch ghi log ra file và tự động đóng cửa sổ CMD sau khi chạy xong)*.
   * **Start in (optional)**: Nhập chính xác thư mục chứa bot (không có dấu ngoặc kép):
     `d:\Nghiên cứu AI\vnstock-agent-guide\bot_app`
     *(Nếu bỏ trống ô này, Windows Task Scheduler sẽ chạy từ thư mục hệ thống `System32`, khiến bot không tìm thấy các file script khác và bị lỗi ngay lập tức!)*
6. **Nhấn OK** để lưu lại.

---

## 🔍 Hướng dẫn đọc Log để Gỡ lỗi (Troubleshooting)

Khi Task Scheduler kích hoạt nhưng bạn không thấy tin nhắn gửi về Telegram, bạn hãy mở thư mục **`bot_app/logs/`** và kiểm tra theo trình tự sau:

### Bước 1: Kiểm tra `logs/run_scheduled_batch.log`
Tệp này lưu lại quá trình khởi động của file Batch.
* Nếu tệp này **trống trơn hoặc không được tạo ra**: Chứng tỏ Windows Task Scheduler chưa hề kích hoạt tệp `.bat` (hãy kiểm tra lại lịch trình hoặc quyền chạy của Task).
* Nếu tệp này **có nội dung**: Xem thông báo lỗi trong đó. Ví dụ:
  * `[BATCH LOG] CANH BAO: Khong tim thay moi truong ao.`: Lỗi do không tìm thấy thư mục `.venv`.
  * `ModuleNotFoundError: No module named 'vnstock_data'`: Lỗi do chưa kích hoạt thành công môi trường ảo (đang dùng Python hệ thống).

### Bước 2: Kiểm tra `logs/bot.log`
Nếu file batch khởi động thành công và gọi được Python, toàn bộ tiến trình quét cổ phiếu sẽ ghi nhận ở đây.
* Xem các dòng log dạng:
  * `INFO - Gathering data for VND...`
  * `INFO - Calling Gemini AI for analysis...`
  * `ERROR - Lỗi khi thực hiện quét chu kỳ: ...`
* Nếu có bất kỳ lỗi nào từ phía API Vnstock, phân tích AI hay gửi Telegram, log sẽ hiển thị chi tiết dòng lỗi và lý do lỗi để bạn dễ dàng xử lý.

---
*Hệ thống ghi log chuyên nghiệp này sẽ giúp bạn hoàn toàn làm chủ được hoạt động của bot cả ở chế độ chạy bằng tay và chạy ngầm tự động!*
