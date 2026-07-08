from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "AI RAG Assistant is alive"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/ask")
def ask_question(question: str):
    return {
        "you_asked": question,
        "answer": f"You asked: '{question}' — real answering logic comes in Phase 2"
    }
