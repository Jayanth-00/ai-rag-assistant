from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "AI RAG Assistant is alive"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
