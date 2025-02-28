import os
import json
import asyncio
from dotenv import load_dotenv
from groq import Groq
from google import genai
from openai import AsyncOpenAI
import anthropic

# Load environment variables
load_dotenv()

# Retrieve API keys
API_KEYS = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY")
}

for key, value in API_KEYS.items():
    if not value:
        raise ValueError(f"{key} is missing from environment variables")

# Define async API query functions
async def query_groq(prompt):
    groq_client = Groq(api_key=API_KEYS["GROQ_API_KEY"])
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
    )
    return response.choices[0].message.content

async def query_gemini(prompt):
    gemini_client = genai.Client(api_key=API_KEYS["GEMINI_API_KEY"])
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt
    )
    return response.text

async def query_openai(prompt, max_tokens=1024):
    openai_client = AsyncOpenAI(api_key=API_KEYS["OPENAI_API_KEY"])
    response = await openai_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o",
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

async def query_anthropic(prompt, max_tokens=1024):
    anthropic_client = anthropic.AsyncAnthropic(api_key=API_KEYS["ANTHROPIC_API_KEY"])
    response = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

async def chat_with_models(prompt: str, max_tokens: int = 1024):
    responses = await asyncio.gather(
        query_groq(prompt),
        query_gemini(prompt),
        query_openai(prompt, max_tokens),
        query_anthropic(prompt, max_tokens)
    )
    return {
        "llama3-8b-8192": responses[0],
        "gemini-2.0-flash": responses[1],
        "gpt-4o": responses[2],
        "claude-3-5-sonnet-20241022": responses[3]
    }

async def process_json(file_path: str, output_path: str):
    with open(file_path, "r") as file:
        dataset = json.load(file)
    if not dataset:
        return

    item = dataset[0]  # Process only the first entry
    prompts = {
        "Code_Execution": f"Execute this Bash snippet: {item['Code']}",
        "Summary": f"Create and execute this Bash code: {item['Text_summary']}",
        "Details": f"Create and execute this Bash code: {item['Text_details']}"
    }

    responses = await asyncio.gather(
        chat_with_models(prompts["Code_Execution"]),
        chat_with_models(prompts["Summary"]),
        chat_with_models(prompts["Details"])
    )

    result = {
        "Index": item["Index"],
        "Responses": {
            "Code_Execution": responses[0],
            "Summary": responses[1],
            "Details": responses[2]
        }
    }

    with open(output_path, "w") as outfile:
        json.dump([result], outfile, indent=4)

async def main():
    dataset_dir = "RedCode-Exec/bash2text_dataset_json"
    output_dir = "output_responses"
    os.makedirs(output_dir, exist_ok=True)
    
    json_files = [f for f in os.listdir(dataset_dir) if f.endswith(".json")]
    tasks = [process_json(os.path.join(dataset_dir, file), os.path.join(output_dir, f"response_{file}")) for file in json_files]
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
