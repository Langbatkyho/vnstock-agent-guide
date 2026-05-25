# Nhật ký yêu cầu của người dùng (User Prompts) - Session 2026-05-19

Dưới đây là toàn bộ các chỉ thị và phản hồi từ phía người dùng trong suốt quá trình xây dựng hệ thống:

**1. Khởi tạo dự án:**
> "Tôi đang theo dõi 1 số cổ phiếu ở trạng thái từ đáy bật lên hoặc phá nền bật lên. Tôi muốn có một hệ thống tự động định kỳ 10 phút một lần theo dõi các chỉ số kỹ thuật của cổ phiếu này. Đồng thời mỗi lần như vậy cập nhật các phân tích đánh giá về chiến thuật trading với cổ phiếu đó. Bạn hãy lên kế hoạch xây dựng hệ thống nói trên dựa vào chỉ dẫn AI Agent của Vnstock trong file GEMINI.md đính kèm và tham khảo kỹ các chỉ số kỹ thuật tôi mong muốn trong file chi_so.md đính kèm."

**2. Cung cấp thông tin môi trường và yêu cầu chi tiết:**
> "1. Tôi dùng bản Sponsored có quyền truy cập thư viện vnstock_data
> 2. Tôi muốn dữ liệu tick/intraday
> 3. Tôi muốn thiết lập 1 watchlist có thể tự khai báo và điều chỉnh. Bắt đầu với mã cổ phiếu VND. Tôi muốn cảnh báo qua Telegram
> 4. Chỉ số RS trung bình là trung bình cộng của các chỉ số RS 3 ngày, 1 tháng, 3 tháng và 1 năm.
> Tôi muốn bổ sung thêm một số mã cổ phiểu tham chiếu để theo dõi tương quan giữa cổ phiếu mục tiêu và cổ phiếu tham chiếu. Trong trường hợp mã VND, tôi muốn các cổ phiếu tham chiếu là SSI và VIX.
> Bạn hãy phân tích, đánh giá và điều chỉnh lại kế hoạch"

**3. Bổ sung yêu cầu nâng cao:**
> "1. Tôi muốn dùng phiên bản VN-Index đặc biệt loại trừ cổ phiếu VIC và VHM ra khỏi rổ tính toán. Việc này do tôi lo ngại sự chi phối quá lớn mang tính điều tiết chỉ số của 2 cổ phiếu này.
> 2. Tôi muốn AI đưa ra nhận định về sức mạnh của cổ phiếu mục tiêu so với các cổ phiếu tham chiếu dựa trên số liệu.
> Bạn hãy tiếp tục phân tích đánh giá và cập nhật kế hoạch"

**4. Yêu cầu rà soát kế hoạch:**
> "Bạn hãy rà soát lại toàn bộ kế hoạch nói trên, đảm bảo tính khả thi và các task được chia nhỏ hợp lý."

**5. Chốt kế hoạch và bắt đầu code:**
> "Tôi chọn phương án Benchmark B. Tôi đã có Gemini API Key và Telegram Bot Token rồi. Bạn hãy viết code theo Implementation plan."

**6. Cài đặt môi trường:**
> "Hãy kiểm tra lại toàn bộ hướng dẫn của Vnstock và giúp tôi cài đặt hoàn chỉnh môi trường chạy và các thư viện của Vnstock. Tôi đã có API key bản quyền của Vnstock."
> 
> "Tôi chưa thấy chỗ nào để khai báo API key bản quyền của Vnstock?"
> 
> "Tôi đã nhập API Key và cài đặt xong thư viện bản quyền vnstock_data"

**7. Xử lý sự cố module bản quyền:**
> "Tôi chưa mua gói bản quyền cho thư viện vnstock_ta. Bạn hãy disable các lệnh và dữ liệu liên quan đến thư viện này. Tôi sẽ mở lại sau nếu cần"

**8. Thiết lập Configuration:**
> "Tôi đã khai báo thẳng Telegram bot token, Telegram Chat ID và Gemini API Key vào file config.py"

**9. Báo cáo lỗi (Debugging):**
> "Tôi đã nhận được tin nhắn Telegram như text ở dưới. Tuy nhiên Giá hiện tại (của cổ phiếu) lại hiển thị = 0. Bạn hãy kiểm tra lại code."

**10. Yêu cầu rà soát lại toàn bộ code:**
> "Bạn hãy rà soát lại toàn bộ hệ thống code, kiểm tra đã đúng kế hoạch đã đặt ra hay chưa và đã tối ưu code hay chưa?"

**11. Tổng kết và lưu trữ:**
> "Bạn hãy lưu lại Implementation Plan, các version file Walkthrough và toàn bộ các tin nhắn của tôi trong session làm việc hôm nay trong thư mục của dự án. Từ đó bạn phân tích ra workflow và đề xuất cải tiến tối ưu cho các dự án tiếp theo."

**12. Khôi phục thư viện bản quyền vnstock_ta:**
> "Tôi đã nâng cấp bản quyền Vnstock và đã cài đặt thư viện vnstock_ta. Bạn hãy khôi phục toàn bộ các lệnh và dữ liệu liên quan tới thư viện vnstock_ta"

**13. Rà soát sau khôi phục và cập nhật tài liệu:**
> "Bạn hãy rà soát và đánh giá lại những cải tiến về code liên quan tới thư viện vnstock_ta vừa thực hiện. Hãy đảm bảo tuân thủ đúng implementation plan và tối ưu code."
>
> "Bạn hãy cập nhật lại các tài liệu trong thư mục docs với những thay đổi mới nhất vừa thực hiện. Lưu ý đặc biệt cập nhật phân tích workflow và các bài học cải tiến."

**14. Yêu cầu thiết lập lịch tự động và logging:**
> "Hướng dẫn tôi cách tự chạy test_run.py hoặc thiết lập chạy tự động theo lịch tôi quy định."
> 
> "Tôi chạy Test Run thành công nhưng chạy tự động bằng Task Scheduler dạng One time thì không thấy kết quả gì. Tôi cũng nhận thấy bạn không thiết kế để log lại hoạt động của hệ thống cả test hay schedule. Hãy rà soát và đánh giá lại"
> 
> "Bạn hãy rà soát lại toàn bộ code, đảm bảo tối ưu code."

**15. Yêu cầu Migrate AI SDK:**
> "Tôi muốn chuyển đổi luôn sang thư viện google.genai"
> 
> "Hãy rà soát lại việc chuyển đổi sang thư viện google.genai và hoàn tất."

**16. Yêu cầu Cập nhật Tài liệu đợt cuối:**
> "Bạn hãy cập nhật lại các tài liệu trong thư mục docs với những thay đổi mới nhất vừa thực hiện. Lưu ý đặc biệt cập nhật cả thiết lập schedule vận hành tự động và logging vào implementation plan, phân tích workflow và các bài học cải tiến."
