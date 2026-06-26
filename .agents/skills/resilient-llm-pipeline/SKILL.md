---
name: resilient-llm-pipeline
description: Triển khai luồng gọi LLM kháng lỗi (Gemini/OpenAI/Anthropic) với Pydantic, Instructor và API Key Rotation.
---

# Hướng dẫn Xây dựng LLM Pipeline Kháng Lỗi

Kỹ năng này hướng dẫn bạn cách gọi LLM an toàn, không phụ thuộc vào Regex và tự động sửa lỗi khi kết quả trả về sai định dạng.

## 1. Yêu cầu Bắt buộc
- **Tuyệt đối không dùng Regex** để parse JSON từ LLM.
- **Bắt buộc dùng `pydantic`** để khai báo Data Contract (Schema).
- **Bắt buộc dùng `instructor`** để bọc model (Gemini, OpenAI, Anthropic) với tham số `max_retries=3`.

## 2. Hướng dẫn Triển khai
Hãy tham khảo tệp code mẫu tại: `examples/instructor_template.py` (nằm cùng thư mục với kỹ năng này).
Bạn có thể copy-paste cấu trúc này và thay đổi tên Schema/Model cho phù hợp.

## 3. Cấu trúc Xoay vòng API & Chống Spam
- Bọc luồng gọi LLM trong khối `try-except`.
- Nếu gặp lỗi `429` (Resource Exhausted) hoặc `503`, chuyển sang API Key dự phòng trong danh sách (nếu có).
- Bắt buộc chèn `time.sleep(2)` (hoặc tương đương) giữa các lượt gọi API để tránh vi phạm Rate Limit.
