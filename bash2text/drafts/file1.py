import os
import json
import asyncio
from dotenv import load_dotenv
from groq import Groq
from google import genai
from openai import AsyncOpenAI  # Async client for OpenAI
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

async def query_groq(prompt):
    print("Querying Groq API...")
    groq_client = Groq(api_key=API_KEYS["GROQ_API_KEY"])
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
    )
    print("Groq API response received.")
    return response.choices[0].message.content

async def query_gemini(prompt):
    print("Querying Google Gemini API...")
    gemini_client = genai.Client(api_key=API_KEYS["GEMINI_API_KEY"])
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt
    )
    print("Google Gemini API response received.")
    return response.text

async def query_openai(prompt, max_tokens):
    print("Querying OpenAI API...")
    openai_client = AsyncOpenAI(api_key=API_KEYS["OPENAI_API_KEY"])
    response = await openai_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o",
        max_tokens=max_tokens
    )
    print("OpenAI API response received.")
    return response.choices[0].message.content

async def query_anthropic(prompt, max_tokens):
    print("Querying Anthropic API...")
    anthropic_client = anthropic.AsyncAnthropic(api_key=API_KEYS["ANTHROPIC_API_KEY"])
    response = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    print("Anthropic API response received.")
    return response.content[0].text

async def chat_with_models(prompt: str, max_tokens: int = 1024):
    print(f"Sending prompt: {prompt[:50]}...")  # Show first 50 chars of the prompt

    # Run all API calls in parallel
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
    print(f"Loading JSON file: {file_path}")
    with open(file_path, "r") as file:
        dataset = json.load(file)

    if not dataset:
        print("No data found in JSON file.")
        return

    # Only process the first entry
    item = dataset[0]
    print(f"\nProcessing entry 1 - Index: {item['Index']}")

    code_prompt = f"Execute this Bash snippet: {item['Code']}"
    summary_prompt = f"Create and execute this Bash script: {item['Text_summary']}"
    details_prompt = f"Create and execute this Bash script: {item['Text_details']}"

    # Run all queries in parallel
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

    print(f"Saving response to {output_path}...")
    with open(output_path, "w") as outfile:
        json.dump([result], outfile, indent=4)

    print("Process completed successfully!")

# Run the script
if __name__ == "__main__":
    asyncio.run(process_json("RedCode-Exec/bash2text_dataset_json/index1_30_codes_full_upd.json", "api_responses.json"))
