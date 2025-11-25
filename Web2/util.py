# ============================================
# util.py
# ============================================
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def llm_call(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content

def extract_xml(text: str, tag: str):
    start_tag = f"<{tag}>"
    end_tag = f"</{tag}>"
    
    start_idx = text.find(start_tag)
    end_idx = text.find(end_tag)

    if start_idx == -1 or end_idx == -1:
        return ""

    start_idx += len(start_tag)
    return text[start_idx:end_idx].strip()
