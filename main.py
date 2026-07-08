from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Question(BaseModel):
    question: str
    top_k: int = 3

@app.get("/")
def read_root():
    return {"message": "AI RAG Assistant is alive"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/ask")
def ask_question(payload: Question):
    return {
        "you_asked": payload.question,
        "top_k": payload.top_k,
        "answer": f"You asked: '{payload.question}' — real answering logic comes in Phase 2"
    }
