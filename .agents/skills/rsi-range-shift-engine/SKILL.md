---
name: rsi-range-shift-engine
description: Hướng dẫn Gemini 3.5 Flash phân tích xu hướng cổ phiếu bằng lý thuyết RSI Range Shift & Momentum Regime Engine với cấu trúc dải sinh thái RSI 40/60 và ma trận dòng tiền đa biến từ vnstock.
version: 2026.1.0
author: Chứng khoán AI Collaborator
engine: gemini-3.5-flash
framework: antigravity-skills-v2
required_inputs:
  - Mã
  - Thị giá
  - 1D%
  - 1M%
  - Khối lượng so với SMA(10)
  - Khối lượng so với SMA(20)
  - % Mua CĐ
  - RSI (14) hiện tại
  - Chuỗi_RSI_30_phiên_gần_nhất
  - Trạng thái RSI(14)
  - MACD Histogram
  - RS 3 ngày
  - RS 1 tháng
  - % giá hiện tại so với MA20
  - % giá hiện tại so với MA50
---

# SYSTEM SKILL: ADVANCED RSI RANGE SHIFT ANALYSIS ENGINE

## 1. MỤC TIÊU & ĐỊNH HƯỚNG TƯ DUY (SKILL OBJECTIVE)
Skill này cấu hình cho AI Engine (Gemini 3.5 Flash) thực hiện quét dữ liệu kỹ thuật, phân loại xu hướng và phát hiện sớm các điểm đảo chiều cấu trúc dòng tiền dựa trên lý thuyết **RSI Range Shift** (Andrew Cardwell, John Hayden & Walter Baeyens). 

**Yêu cầu nghiêm ngặt cho AI:** 
*   Bỏ qua hoàn toàn tư duy 70/30 (quá mua/quá bán) truyền thống.
*   Sử dụng mốc **40** và **60** làm trục xương sống toán học để định vị phe đang thực tế kiểm soát biên độ dao động.
*   Kết hợp các tham số dòng tiền chủ động từ `vnstock` để lọc bỏ tín hiệu nhiễu.

---

## 2. MA TRẬN PHÂN LOẠI VÙNG SINH THÁI ĐỘNG LƯỢNG (REGIME RULES)
AI bắt buộc phải phân loại trạng thái cổ phiếu dựa trên vị trí vận động chủ đạo của chỉ báo `RSI (14)`:

### A. Bull Market Range (Vùng sinh thái Tăng giá): RSI dao động [40 - 80]
*   **Hỗ trợ động:** Mốc **40** là hỗ trợ tử thủ. Các nhịp điều chỉnh kéo giá lùi lại nhưng `RSI (14)` giữ vững dải [40 - 45] là điểm canh mua retest (Buy the Dip).
*   **Kháng cự gia tốc:** Mốc **60** đóng vai trò là cửa ngõ kích hoạt xung lực mạnh.
*   **Xử lý Phân kỳ:** Hiện tượng phân kỳ âm tại dải RSI [70 - 80] chỉ là nhịp "xả nhiệt toán học" (Half-pipe compression). Không kích hoạt cảnh báo bán hoảng loạn trừ khi giá vi phạm cấu trúc nền hoặc RSI đánh mất mốc 40.

### B. Bear Market Range (Vùng sinh thái Giảm giá): RSI dao động [20 - 60]
*   **Kháng cự động:** Mốc **60** đóng vai trò là trần chặn (kháng cự động cực mạnh). Các nhịp hồi phục đẩy RSI lên sát 60 nhưng quay đầu là cơ hội để bán hạ tỷ trọng, cơ cấu danh mục.
*   **Vùng hoảng loạn:** RSI nhúng sâu dưới 30 thể hiện xu hướng giảm rất mạnh, tuyệt đối không bắt đáy sớm trừ khi xuất hiện điểm kích hoạt dịch chuyển vùng.

---

## 3. LOGIC PHÁT HIỆN SỰ DỊCH CHUYỂN VÙNG (RANGE SHIFT DETECTION)

### Tín hiệu Bear-to-Bull (Khởi động Siêu sóng)
Phát hiện và đưa vào danh sách GIỮ THEO DÕI ĐẶC BIỆT khi cổ phiếu thỏa mãn đồng thời:
1.  `RSI (14)` bứt phá dứt khoát vượt qua trần kháng cự **60 - 65**.
2.  Đi kèm với trạng thái hành vi: `Phá nền = Có` hoặc `Vượt đỉnh 52 tuần = Có`.
3.  Nhịp backtest kỹ thuật sau đó: Giá điều chỉnh nhưng RSI giữ vững được mốc **40** và bật tăng trở lại.

### Tín hiệu Bull-to-Bear (Bẫy sập / Phân phối đỉnh)
Phát hiện và kích hoạt CẢNH BÁO RỦI RO CAO khi cổ phiếu vi phạm:
1.  `RSI (14)` rơi tự do thủng mốc hỗ trợ động **40**.
2.  Nhịp hồi phục kỹ thuật tiếp theo, giá tăng nhẹ nhưng RSI bị từ chối dứt khoát và quay đầu giảm ngay tại mốc **60 - 65**.

---

## 4. QUY TRÌNH KIỂM TRA SỨC MẠNH NỘI TẠI (INTERNAL STRENGTH CHECK)
Trước khi đưa ra kết luận, AI phải đối chiếu biến động RSI với bộ lọc dòng tiền để xác định tính xác thực:

*   **Bứt phá Hợp lệ (Genuine Breakout):** Khi giá bẻ gãy dải RSI cũ (vượt 60 hoặc thủng 40) đồng thời có sự đồng thuận của dòng tiền lớn: `% Mua CĐ` $\ge$ **55%** và `Khối lượng so với SMA(10)` hoặc `SMA(20)` $\ge$ **1.5 lần**.
*   **Bẫy kỹ thuật (False/Trap):** Khi giá biến động mạnh vượt biên RSI nhưng thanh khoản yếu (`Khối lượng so với SMA(10) < 1.0`) và `% Mua CĐ` suy yếu dưới mức 50%.
*   **Tương quan Sức mạnh giá (Relative Strength Matrix):** Nếu `RS 3 ngày` $\ge$ **80** trong khi `RS 1 tháng` < **30** $\rightarrow$ Gắn nhãn trạng thái **"Vua gặp nạn"** (Cổ phiếu tạo đáy thành công, lực cầu thông minh nhập cuộc bứt phá mạnh hơn thị trường chung).

---

## 5. CẤU TRÚC BÁO CÁO ĐẦU RA CHUẨN HÓA (OUTPUT TEMPLATE)
*AI bắt buộc phải định dạng kết quả phân tích theo form scannable dưới đây:*

### [Antigravity Engine] BÁO CÁO PHÂN TÍCH ĐỘNG LƯỢNG: [MÃ CP]

**1. Định Vị Vùng Sinh Thái & Áp Lực Dòng Tiền**
*   Thị giá hiện tại: [...] (`1D%`: [...]) | Khoảng cách giá: [So với MA20, MA50].
*   Thông số: `RSI(14)`: [...] | Phân loại vùng sinh thái: [Bull Range 40-80 / Bear Range 20-60 / Đang dịch chuyển].
*   Xung lực dòng tiền: `Khối lượng vs SMA(20)`: [...] | `% Mua CĐ`: [...] $\rightarrow$ Đánh giá: [Cá mập gom / Xả hàng / Cạn cung].
*   Điểm nhấn tương quan: `RS 3 ngày`: [...] | `RS 1 tháng`: [...].

**2. Đánh Giá Động Lượng Dưới Lăng Kính Range Shift**
*   *Hành vi chỉ báo:* [Ví dụ: Cổ phiếu vừa kích hoạt cú Bear-to-Bull Range Shift khi bẻ gãy trần RSI 60 với vol lớn...].
*   *Trạng thái bổ trợ:* `MACD Histogram` [...], xu hướng nến ngắn hạn [...].

**3. Thiết Lập Kế Hoạch Tác Chiến Trading T+**
*   **Chiến lược hành động:** [Gồng lãi bám trend / Mua gom Backtest T+0 / Đứng ngoài quan sát].
*   **Vùng giá hành động:** [Vùng giá giải ngân tương ứng với dải RSI hỗ trợ động 40 hoặc điểm breakout vượt 60].
*   **Mục tiêu kỳ vọng (Target):** [Ngưỡng giá mục tiêu khi RSI tiến sát biên trên vùng sinh thái, tính toán theo công thức Fibonacci: $$P_{\text{target}} = P_{\text{low}} + (P_{\text{high}} - P_{\text{low}}) \times \text{Ratio}$$].
*   **Chốt chặn sinh tử (Stop-loss):** [Mức giá bắt buộc phải thoát nếu RSI phá vỡ dải sinh thái hiện tại].