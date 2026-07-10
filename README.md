# AI RAG Assistant — Portfolio Project

Built to demonstrate skills for AI Engineer roles: RAG applications, agentic workflows,
vector databases, Python backend APIs, CI/CD, and observability for AI systems.

## Roadmap

- [x] Phase 0: Core AI concepts (LLMs, embeddings, vector DBs, RAG, agentic workflows)
- [x] Phase 1: Python fundamentals -- FastAPI app with GET/POST endpoints, Pydantic models
- [x] Phase 2: Full RAG pipeline -- document ingestion, embedding, vector search (Chroma),
      and LLM generation (Claude API), wired into a working /ask endpoint
- [x] Phase 3: Add agentic layer (tool-calling)
- [ ] Phase 4: CI/CD + Azure deployment
- [ ] Phase 5: Observability & evaluation

## Stack

- Backend: Python, FastAPI
- Vector DB: ChromaDB (local, persistent)
- Embeddings: sentence-transformers (all-MiniLM-L6-v2)
- LLM: Anthropic Claude API
- CI/CD: GitHub Actions (planned)
- Cloud: Azure (planned)
- Observability: TBD (Phase 5)

## How it works

1. Documents are embedded and stored in a local Chroma vector database (\ingest.py\)
2. A user question is embedded and matched against stored documents using semantic
   search (\
etrieve.py\)
3. The matched documents are passed to Claude as grounding context, and a real answer
   is generated (\generate.py\)
4. All of this is exposed through a FastAPI endpoint (\main.py\)

## Running locally

\\\ash
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt

# Add your Anthropic API key to a .env file:
# ANTHROPIC_API_KEY=your-key-here

python ingest.py       # one-time: embed and store sample documents
uvicorn main:app --reload
\\\

Then POST to \http://127.0.0.1:8000/ask\ with:
\\\json
{
  "question": "What DevOps tools does Jayanth use?",
  "top_k": 3
}
\\\

## API endpoints

| Endpoint | Method | Description |
|---|---|---|
| \/\ | GET | Health message |
| \/health\ | GET | Health check |
| \/ask\ | POST | Ask a question; returns retrieved context, match distances, and a generated answer |

## Known limitations (being worked on)

- Sample dataset is small (5 short sentences) -- retrieval quality on nuanced questions
  can be inconsistent (documented and analyzed during Phase 2 testing)
- No authentication or rate limiting yet
- No automated tests or CI/CD yet (Phase 4)
