# Cấu trúc Thư mục Chuẩn cho Dự án Multi-Agent

Khi được yêu cầu khởi tạo một dự án Agent mới, hãy sử dụng cây thư mục sau đây làm tiêu chuẩn:

```text
my_agent_project/
├── .env.example
├── .gitignore
├── GLOBAL_CONSTRAINTS.md    # Bắt buộc tự tạo ở bước Planning (Rule Hệ thống)
├── main.py                  # Pipeline Coordinator (không chứa logic hẹp)
├── models/
│   └── schemas.py           # Pydantic Data Contracts (End-to-End)
├── utils/
│   ├── filters.py           # Logic lọc dữ liệu
│   └── formatters.py        # Xử lý chuỗi, HTML, Markdown
├── agents/                  # Các module xử lý của Subagent
│   ├── crawler.py           # Lấy dữ liệu thô
│   └── ai_analyzer.py       # Tích hợp LLM + Instructor
├── docs/
│   ├── implementation_plan.md
│   └── changelog.md
└── logs/                    # Chứa metrics và cache trạng thái
```
