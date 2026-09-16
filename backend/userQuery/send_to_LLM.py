from openai import OpenAI
from dotenv import load_dotenv
import os


# Load variables from .env
load_dotenv()

# Read API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env")

# Create OpenAI client
client = OpenAI(api_key=api_key)


def send_to_LLM(question, results):

    retrieved_chunks = results["documents"][0]

    context = "\n\n".join(retrieved_chunks)

    prompt = f"""
    You are a helpful assistant.

    Answer the user's question using only the context provided below.

    If the answer is not available in the context, say:
    "I don't have enough information to answer that question."

    Context:
    {context}

    Question:
    {question}
    """

    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    print(response.output_text)

    return response.output_text