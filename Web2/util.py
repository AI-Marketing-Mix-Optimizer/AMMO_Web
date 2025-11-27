import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def llm_call(prompt: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content

def extract_xml(text: str, tag: str):
    start = text.find(f"<{tag}>")
    end = text.find(f"</{tag}>")
    if start == -1 or end == -1:
        return ""
    start += len(tag) + 2
    return text[start:end].strip()
