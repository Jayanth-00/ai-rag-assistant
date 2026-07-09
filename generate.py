import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load the API key from .env into the environment
load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_answer(question: str, context_docs: list[str]) -> str:
    # Combine the retrieved documents into one block of text
    context = "\n".join(context_docs)

    prompt = f"""Answer the question using ONLY the information in the context below.
If the context doesn't contain enough information to answer, say so honestly.

Context:
{context}

Question: {question}

Answer:"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.content[0].text

if __name__ == "__main__":
    from retrieve import retrieve

    question = "What cloud does Jayanth have experience with?"
    results = retrieve(question, top_k=3)
    docs = results["documents"][0]

    answer = generate_answer(question, docs)
    print(f"Question: {question}\n")
    print(f"Answer: {answer}")
