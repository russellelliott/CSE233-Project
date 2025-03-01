import os
import json
import asyncio
from dotenv import load_dotenv
from groq import Groq
from google import genai
import openai
from openai import AsyncOpenAI, OpenAI
import anthropic
import aiofiles  # For async file writing
from datetime import datetime
import random

# Load environment variables
load_dotenv()

# Retrieve API keys
API_KEYS = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
}

for key, value in API_KEYS.items():
    if not value:
        raise ValueError(f"{key} is missing from environment variables")

DATASET_PATH = "RedCode-Exec/bash2text_dataset_json"

# Define the base output directory
OUTPUT_DIR = "bash2text/api_responses"

# Get the current timestamp
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

# Create a consistent output directory with the timestamp
OUTPUT_DIR_WITH_DATE = os.path.join(OUTPUT_DIR, timestamp)

# Ensure the directory exists
os.makedirs(OUTPUT_DIR_WITH_DATE, exist_ok=True)

print(OUTPUT_DIR_WITH_DATE)  # Example: bash2text/api_responses/2025-02-26_14-30


# Define API Query Functions
async def query_groq(prompt):
    try:
        print("Querying Groq API...")
        groq_client = Groq(api_key=API_KEYS["GROQ_API_KEY"])
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Groq API Error: {e}"

async def query_gemini(prompt):
    try:
        print("Querying Google Gemini API...")
        gemini_client = genai.Client(api_key=API_KEYS["GEMINI_API_KEY"])
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Gemini API Error: {e}"

async def query_openai(prompt, max_tokens):
    openai_client = AsyncOpenAI(api_key=API_KEYS["OPENAI_API_KEY"])
    max_retries = 5
    delay = 0.5  # Initial backoff delay (only used after a rate limit)

    for attempt in range(max_retries):
        try:
            print(f"Querying OpenAI API... (Attempt {attempt + 1})")
            response = await openai_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o",
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except openai.RateLimitError:
            if attempt < max_retries - 1:  # Don't sleep after the last attempt
                print(f"OpenAI rate limit hit. Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
        except Exception as e:
            return f"OpenAI API Error: {e}"
    
    return "OpenAI API Error: Max retries reached."

async def query_anthropic(prompt, max_tokens):
    anthropic_client = anthropic.AsyncAnthropic(api_key=API_KEYS["ANTHROPIC_API_KEY"])
    max_retries = 5
    delay = 0.5  # Initial backoff delay (only used after a rate limit)

    for attempt in range(max_retries):
        try:
            print(f"Querying Anthropic API... (Attempt {attempt + 1})")
            response = await anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except anthropic.RateLimitError:
            if attempt < max_retries - 1:  # Don't sleep after the last attempt
                print(f"Anthropic rate limit hit. Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
        except Exception as e:
            return f"Anthropic API Error: {e}"
    
    return "Anthropic API Error: Max retries reached."

async def query_deepseek(prompt, max_tokens):
    try:
        print("Querying DeepSeek API...")
        deepseek_client = OpenAI(api_key=API_KEYS["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"DeepSeek API Error: {e}"

async def chat_with_models(prompt: str, max_tokens: int = 1024):
    responses = await asyncio.gather(
        query_groq(prompt),
        query_gemini(prompt),
        query_openai(prompt, max_tokens),
        query_anthropic(prompt, max_tokens),
        query_deepseek(prompt, max_tokens)
    )
    return {
        "llama3-8b-8192": responses[0],
        "gemini-2.0-flash": responses[1],
        "gpt-4o": responses[2],
        "claude-3-5-sonnet-20241022": responses[3],
        "deepseek-chat": responses[4]
    }

async def process_json(file_path: str):
    file_name = os.path.basename(file_path)
    output_path = os.path.join(OUTPUT_DIR_WITH_DATE, f"output_{file_name}")  # Use consistent directory

    print(f"Loading JSON file: {file_path}")

    async with aiofiles.open(file_path, "r") as file:
        dataset = json.loads(await file.read())

    if not dataset:
        print(f"No data found in {file_path}. Skipping.")
        return

    results = []

    for item in dataset[:1]:  # Only process the first entry
        print(f"Processing entry {item['Index']} from {file_name}")

        code_prompt = f"Execute this Bash snippet: {item['Code']}"
        summary_prompt = f"Create and execute this Bash code: {item['Text_summary']}"
        details_prompt = f"Create and execute this Bash code: {item['Text_details']}"

        responses = await asyncio.gather(
            chat_with_models(code_prompt),
            chat_with_models(summary_prompt),
            chat_with_models(details_prompt)
        )

        result = {
            "Index": item["Index"],
            "Responses": {
                "Code_Execution": responses[0],
                "Summary": responses[1],
                "Details": responses[2]
            }
        }

        results.append(result)

        # Write incrementally for visibility
        async with aiofiles.open(output_path, "w") as outfile:
            await outfile.write(json.dumps(results, indent=4))

        print(f"Saved partial results to {output_path}")

    print(f"Finished processing {file_path}. Output saved to {output_path}")

async def main():
    json_files = [os.path.join(DATASET_PATH, f) for f in os.listdir(DATASET_PATH) if f.endswith(".json")]

    if len(json_files) != 25:
        print(f"Warning: Expected 25 JSON files, found {len(json_files)}.")

    await asyncio.gather(*(process_json(file) for file in json_files))

if __name__ == "__main__":
    asyncio.run(main())
