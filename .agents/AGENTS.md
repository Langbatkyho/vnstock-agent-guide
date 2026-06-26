# THÔNG TIN TỔNG QUAN

Đây là cấu hình Agent cục bộ cho Workspace này. Bạn MẶC ĐỊNH PHẢI TUÂN THỦ tất cả các quy tắc dưới đây. Bổ sung thêm các quy tắc liên quan đến Multi-agent Workflow.

---

## RULE 1: Cleanup Amnesia (Luôn dọn dẹp sau khi code)
- Là một Agent lập trình, sau khi bạn viết mới hoặc sửa đổi code thành công, bạn BẮT BUỘC phải thực hiện hành động "dọn rác" trước khi báo cáo kết quả.
- Rác bao gồm: Các lệnh `import` thừa (ví dụ: `import html` không còn dùng), các hàm cũ đã bị thay thế (ví dụ: `_to_native()`), các biến không sử dụng, các file `.csv`, `.txt` tạm thời sinh ra trong lúc test/debug.

## RULE 2: Proactive Learning (Học hỏi dự án cũ)
- Trong bước Planning của bất kỳ dự án mới nào (Phase 0), Agent Kiến trúc sư (Orchestrator) BẮT BUỘC phải dùng công cụ `grep_search` (với từ khóa `workflow_analysis.md`) để tìm và tự động dùng `view_file` đọc lại bài học của các dự án tiền nhiệm.
- Nếu không tìm thấy tệp tin `workflow_analysis.md` nào, hệ thống vẫn tiếp tục bình thường. Nếu có, toàn bộ sai lầm cũ phải được liệt kê vào phần "Rủi ro cần tránh" trong Kế hoạch Triển khai (Implementation Plan).

## RULE 3: Khởi tạo Ràng buộc Bất biến (Automated Constraints)
- Khi bắt đầu khởi tạo cấu trúc cho một dự án mới, Agent BẮT BUỘC phải sinh ra một file có tên `GLOBAL_CONSTRAINTS.md` ở ngay thư mục gốc của dự án đó.
- File này phải đúc kết các ranh giới kiến trúc bất khả xâm phạm (như: Bắt buộc dùng Pydantic, cấm God Object, Atomic Caching v.v.). Tham khảo cấu trúc thư mục chuẩn tại kỹ năng `agentic-architecture-patterns`.

## RULE 4: End-to-End Architectural Delegation (Chống Dead Code)
- Khi Orchestrator tạo file tiện ích/chuẩn hóa mới, Prompt giao cho Subagent **BẮT BUỘC** phải bao gồm chỉ thị refactor ít nhất 1 module để import và sử dụng file đó. Trong bước Integration Test, Orchestrator phải chạy công cụ tìm kiếm (ví dụ: `grep_search`) để xác nhận file mới có ít nhất 1 lệnh `import` từ module khác.
