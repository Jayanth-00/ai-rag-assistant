from fastapi import FastAPI
from pydantic import BaseModel
from retrieve import retrieve
from generate import generate_answer

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
    results = retrieve(payload.question, top_k=payload.top_k)
    matched_docs = results["documents"][0]
    distances = results["distances"][0]

    answer = generate_answer(payload.question, matched_docs)

    return {
        "you_asked": payload.question,
        "retrieved_documents": matched_docs,
        "distances": distances,
        "answer": answer
    }
