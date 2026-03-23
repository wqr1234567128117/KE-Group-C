from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str

@app.post("/api/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    # 这里你可以接入真实的 AI 模型（如 LangChain、HuggingFace、OpenAI 等）
    # 示例：简单回复
    return AnswerResponse(answer=f"你问的是：'{request.question}'，这是个很好的问题！")

# 启动命令：uvicorn main:app --reload