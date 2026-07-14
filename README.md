# AI RAG Assistant — Portfolio Project

Built to demonstrate skills for AI Engineer roles: RAG applications, agentic workflows,
vector databases, Python backend APIs, CI/CD, and observability for AI systems.

**Live demo:** https://ai-rag-assistant-app.jollycliff-05a0f948.eastus.azurecontainerapps.io/docs

## Roadmap

- [x] Phase 0: Core AI concepts (LLMs, embeddings, vector DBs, RAG, agentic workflows)
- [x] Phase 1: Python fundamentals -- FastAPI app with GET/POST endpoints, Pydantic models
- [x] Phase 2: Full RAG pipeline -- document ingestion, embedding, vector search (Chroma),
      and LLM generation (Claude API), wired into a working /ask endpoint
- [x] Phase 3: Agentic tool-calling -- live date lookup and precise experience-duration
      calculation, with multi-tool chaining
- [x] Phase 4: Containerization + Infrastructure as Code -- Dockerized app, deployed to
      Azure Container Apps via Terraform, with a remote state backend
- [ ] Phase 5: CI/CD automation (GitHub Actions) + observability & evaluation

## Stack

- Backend: Python, FastAPI
- Vector DB: ChromaDB (local, persistent)
- Embeddings: sentence-transformers (all-MiniLM-L6-v2)
- LLM: Anthropic Claude API (with tool-calling)
- Containerization: Docker (CPU-only torch build, 2.33GB image)
- Infrastructure as Code: Terraform, remote state backend (Azure Storage)
- Cloud: Azure Container Registry (ACR) + Azure Container Apps
- CI/CD: GitHub Actions (planned -- Phase 5)
- Observability: TBD (Phase 5)

## How it works

1. Documents are embedded and stored in a Chroma vector database (`ingest.py`), which
   runs automatically on container startup
2. A user question is embedded and matched against stored documents using semantic
   search (`retrieve.py`)
3. The matched documents are passed to Claude as grounding context; Claude can also call
   tools (`generate.py`) for live information -- e.g. today's date, or exact work
   experience duration calculated from a real start date
4. All of this is exposed through a FastAPI endpoint (`main.py`), containerized with
   Docker, and deployed on Azure Container Apps

## Infrastructure

Provisioned entirely via Terraform (`infra/`):
- Resource Group
- Azure Container Registry (ACR) -- stores the built Docker image
- Log Analytics Workspace -- log destination for the Container App
- Container App Environment
- Container App -- runs the image, exposes a public HTTPS endpoint

Terraform state is stored remotely in Azure Storage (not locally), with state locking
enabled, following standard IaC practice for safe, shareable infrastructure management.

**Cost note:** this deployment uses real, billable Azure resources (Container Apps,
ACR, Log Analytics, Storage). `min_replicas = 1` keeps the app always-on; for a
portfolio project this can be set to `0` for scale-to-zero, or torn down entirely with
`terraform destroy` between active work sessions.

## Running locally

```bash
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt

# Add your Anthropic API key to a .env file:
# ANTHROPIC_API_KEY=your-key-here

python ingest.py       # one-time: embed and store sample documents
uvicorn main:app --reload
```

## Running with Docker

```bash
docker build -t ai-rag-assistant .
docker run -p 8000:8000 --env-file .env ai-rag-assistant
```

## Deploying infrastructure

```bash
cd infra
terraform init
$env:TF_VAR_anthropic_api_key = "your-key-here"   # PowerShell
terraform plan
terraform apply
```

## API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health message |
| `/health` | GET | Health check |
| `/ask` | POST | Ask a question; returns retrieved context, match distances, and a generated answer |

## Known limitations (being worked on)

- Sample dataset is small (5 short sentences) -- retrieval quality on nuanced questions
  can be inconsistent (documented and analyzed during Phase 2 testing)
- No authentication or rate limiting yet
- Deployment is currently manual (Docker build/push + terraform apply) -- CI/CD
  automation via GitHub Actions is next (Phase 5)
- No automated evaluation of retrieval or answer quality yet (Phase 5)
