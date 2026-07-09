import chromadb
from sentence_transformers import SentenceTransformer

# Sample documents -- later this will be your real files
documents = [
    "Jayanth has around 2.5 years of experience as an Associate DevOps Engineer at Voya India.",
    "His core stack includes Jenkins, GitHub Actions, Docker, Kubernetes, OpenShift, Helm, and Terraform.",
    "He has hands-on experience with Azure Databricks and Azure Data Factory, including building a metadata-driven ELT pipeline using Medallion Architecture.",
    "Jayanth is currently learning Python and AI/ML concepts to pivot toward AI Engineer roles.",
    "He is building a RAG-based AI assistant as a portfolio project to demonstrate these new skills.",
]

# Step 1: Load the embedding model (downloads once, then runs locally)
print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Step 2: Convert each document into an embedding vector
print("Creating embeddings...")
embeddings = model.encode(documents).tolist()

# Step 3: Connect to a local Chroma database (creates a folder to store it)
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="jayanth_profile")

# Step 4: Store the documents and their embeddings together
collection.add(
    documents=documents,
    embeddings=embeddings,
    ids=[f"doc_{i}" for i in range(len(documents))]
)

print(f"Stored {len(documents)} documents in the vector database.")
