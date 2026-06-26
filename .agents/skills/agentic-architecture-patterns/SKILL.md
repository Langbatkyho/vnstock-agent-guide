---
name: agentic-architecture-patterns
description: Mẫu thiết kế chuẩn mực cho dự án Multi-Agent, chia nhỏ module, tránh God Object, kiến trúc Atomic Caching.
---

# Agentic Architecture Patterns

Kỹ năng này hướng dẫn xây dựng hoặc refactor một dự án Multi-Agent theo mô hình chuẩn, tách biệt trách nhiệm rõ ràng.

## 1. Checklist Xóa bỏ Bệnh "God Object" ở file Orchestrator
`main.py` (hoặc file orchestrator tương tự) KHÔNG ĐƯỢC CHỨA các phần tử sau:
- [ ] Logic bóc tách HTML/String (`import html` hoặc `re` thay thế chuỗi -> Ném ra `formatters.py`).
- [ ] Cấu hình Prompt tĩnh của LLM (-> Ném ra module `ai_analyzer.py`).
- [ ] Các khối lệnh if/else lặp đi lặp lại để lọc dữ liệu (-> Ném ra `filters.py`).
*Quy tắc ngầm:* Nếu `main.py` vượt quá 150 dòng HOẶC thực thi nhiều hơn 1 vòng lặp pipeline (Fetch -> Filter -> Process -> Save), hệ thống đang vi phạm Separation of Concerns. Cần refactor ngay lập tức!

## 2. Kiến trúc Thư mục Chuẩn
Tham khảo tệp template: `references/project_structure.md` (cùng thư mục với kỹ năng này) để tạo khung thư mục chuẩn (Scaffold) khi khởi tạo dự án mới.

## 3. Atomic Caching (Ghi trạng thái an toàn)
- Việc lưu trạng thái bộ nhớ lâu dài (cache, sent_urls) chỉ được phép thực hiện 1 lần duy nhất ở khối lệnh `finally` vào cuối chu kỳ vòng lặp chính (main loop).
- TUYỆT ĐỐI NGHIÊM CẤM lệnh `json.dump()` hoặc lệnh lưu DB nằm bên trong vòng lặp đang duyệt dữ liệu dở dang (ví dụ trong vòng lặp `for article in articles:`) để chống hỏng/rò rỉ dữ liệu khi app crash.

## 4. Chống Kiến Trúc Ảo (Dead Architecture Prevention)
- Mọi file chuẩn hóa (Data Contract, Utils, Constants) được tạo ra mà không có `import` tương ứng trong codebase sẽ bị phân loại là **Dead Architecture** và phải bị xóa hoặc tích hợp hoàn chỉnh trước khi kết thúc Phase.
