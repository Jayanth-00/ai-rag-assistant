import os
import json
from datetime import date
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- The real Python functions each tool runs ---
def get_current_date():
    return {"today": str(date.today())}

def calculate_experience_duration(start_date: str):
    start = date.fromisoformat(start_date)
    today = date.today()
    total_days = (today - start).days
    years = total_days // 365
    months = (total_days % 365) // 30
    return {
        "start_date": start_date,
        "as_of": str(today),
        "years": years,
        "months": months,
        "total_days": total_days
    }

# --- A lookup table connecting tool names to the real functions ---
TOOL_FUNCTIONS = {
    "get_current_date": get_current_date,
    "calculate_experience_duration": calculate_experience_duration,
}

# --- Descriptions Claude reads to decide when/how to use each tool ---
tools = [
    {
        "name": "get_current_date",
        "description": "Get today's date. Use this when the question requires knowing the current date.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "calculate_experience_duration",
        "description": "Calculate exact work experience duration (years, months, days) from a given start date to today. Use this when asked how much experience Jayanth currently has, since stored documents may say a rough or outdated figure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "The job start date in YYYY-MM-DD format"
                }
            },
            "required": ["start_date"]
        }
    }
]

def generate_answer(question: str, context_docs: list[str]) -> str:
    context = "\n".join(context_docs)

    prompt = f"""Answer the question using the context below when relevant.
You also have tools available: one for getting today's date, and one for calculating
exact work experience duration from a start date. Jayanth started at Voya India on 2024-02-14.
Use tools when the question needs live/calculated information rather than relying on
possibly outdated figures in the context.

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

    # Keep handling tool calls until Claude gives a final text answer
    while response.stop_reason == "tool_use":
        tool_use_block = next(block for block in response.content if block.type == "tool_use")
        tool_name = tool_use_block.name
        tool_input = tool_use_block.input

        # Look up and run the real function, passing along whatever input Claude provided
        tool_function = TOOL_FUNCTIONS[tool_name]
        tool_result = tool_function(**tool_input)

        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use_block.id,
                "content": json.dumps(tool_result)
            }]
        })

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            tools=tools,
            messages=messages
        )

    return response.content[0].text

if __name__ == "__main__":
    from retrieve import retrieve

    question = "Exactly how much work experience does Jayanth have right now?"
    results = retrieve(question, top_k=3)
    docs = results["documents"][0]

    answer = generate_answer(question, docs)
    print(f"Question: {question}\n")
    print(f"Answer: {answer}")
