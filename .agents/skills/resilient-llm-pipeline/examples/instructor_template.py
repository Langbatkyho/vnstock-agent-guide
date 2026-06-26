import instructor
from google import genai
from pydantic import BaseModel, Field
import time

# 1. Định nghĩa Data Contract
class UserInfoSchema(BaseModel):
    name: str = Field(description="Tên người dùng")
    age: int = Field(description="Tuổi")

def call_llm_with_retry(prompt: str, api_keys: list[str]) -> UserInfoSchema:
    """Gọi LLM với cơ chế xoay vòng key, tự sửa lỗi và chống spam."""
    for key in api_keys:
        try:
            # 2. Khởi tạo LLM Client với Instructor (Hỗ trợ cả OpenAI, Anthropic bằng cách đổi adapter)
            genai_client = genai.Client(api_key=key)
            client = instructor.from_genai(
                client=genai_client,
                mode=instructor.Mode.GEMINI_JSON,
            )
            
            # 3. Thực thi gọi LLM (tự động parse ra Schema + tự sửa lỗi 3 lần)
            response = client.chat.completions.create(
                model="gemini-1.5-flash-latest",
                messages=[{"role": "user", "content": prompt}],
                response_model=UserInfoSchema,
                max_retries=3,
            )
            
            time.sleep(2) # 4. Chống spam để qua mặt Rate Limit
            return response
            
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e) or "503" in str(e):
                print(f"Key {key[-4:]} bị lỗi hạn ngạch/Server. Thử key tiếp theo...")
                continue
            raise e
    raise Exception("Đã thử hết tất cả API Keys nhưng đều thất bại!")
