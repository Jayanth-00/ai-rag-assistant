import os
import json
from datetime import date
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- Step 1: The actual Python function the tool will run ---
def get_current_date():
    return {"today": str(date.today())}

# --- Step 2: Describe this tool to Claude, so it knows the tool exists ---
tools = [
    {
        "name": "get_current_date",
        "description": "Get today's date. Use this when the question requires knowing the current date.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

def generate_answer(question: str, context_docs: list[str]) -> str:
    context = "\n".join(context_docs)

    prompt = f"""Answer the question using the context below when relevant.
You also have access to a tool for getting today's date if the question needs it.
If the context doesn't contain enough information and no tool applies, say so honestly.

Context:
{context}

Question: {question}"""

    messages = [{"role": "user", "content": prompt}]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        tools=tools,
        messages=messages
    )

    # --- Step 3: Check if Claude wants to call a tool ---
    if response.stop_reason == "tool_use":
        tool_use_block = next(block for block in response.content if block.type == "tool_use")
        tool_name = tool_use_block.name

        if tool_name == "get_current_date":
            tool_result = get_current_date()

        # Send the tool result back to Claude so it can finish answering
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use_block.id,
                "content": json.dumps(tool_result)
            }]
        })

        final_response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            tools=tools,
            messages=messages
        )
        return final_response.content[0].text

    # No tool needed -- just return the direct answer
    return response.content[0].text

if __name__ == "__main__":
    from retrieve import retrieve

    question = "What is today's date?"
    results = retrieve(question, top_k=3)
    docs = results["documents"][0]

    answer = generate_answer(question, docs)
    print(f"Question: {question}\n")
    print(f"Answer: {answer}")
