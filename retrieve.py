import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="jayanth_profile")

def retrieve(question: str, top_k: int = 5):
    query_embedding = model.encode([question]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )
    return results

if __name__ == "__main__":
    question = "What cloud does Jayanth have experience with?"
    results = retrieve(question, top_k=5)

    print(f"Question: {question}\n")
    docs = results["documents"][0]
    distances = results["distances"][0]

    for i, (doc, dist) in enumerate(zip(docs, distances), start=1):
        print(f"{i}. (distance: {dist:.4f}) {doc}")
