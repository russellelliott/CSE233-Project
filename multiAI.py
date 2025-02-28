import os
import json
from dotenv import load_dotenv
from groq import Groq
from google import genai
from openai import OpenAI
import anthropic

def chat_with_models(prompt: str, max_tokens: int = 1024):
    load_dotenv()
    
    # Retrieve API keys
    api_keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY")
    }
    
    for key, value in api_keys.items():
        if not value:
            raise ValueError(f"{key} is missing from environment variables")
    
    responses = {}
    
    # Groq API
    groq_client = Groq(api_key=api_keys["GROQ_API_KEY"])
    groq_response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
    )
    responses["llama3-8b-8192"] = groq_response.choices[0].message.content
    
    # Google Gemini API
    gemini_client = genai.Client(api_key=api_keys["GEMINI_API_KEY"])
    gemini_response = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt
    )
    responses["gemini-2.0-flash"] = gemini_response.text
    
    # OpenAI API
    openai_client = OpenAI(api_key=api_keys["OPENAI_API_KEY"])
    openai_response = openai_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o",
        max_tokens=max_tokens
    )
    responses["gpt-4o"] = openai_response.choices[0].message.content
    
    # Anthropic API
    anthropic_client = anthropic.Anthropic(api_key=api_keys["ANTHROPIC_API_KEY"])
    anthropic_message = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    responses["claude-3-5-sonnet-20241022"] = anthropic_message.content[0].text
    
    return json.dumps(responses, indent=4)

# Example usage
if __name__ == "__main__":
    print(chat_with_models("Explain the importance of low latency LLMs", max_tokens=1024))
