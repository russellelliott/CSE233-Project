import os
import json
import asyncio
import aiofiles
from datetime import datetime

# Import the API query functions from main.py
from main import (
    query_groq,
    query_gemini,
    query_openai,
    query_anthropic,
    query_deepseek,
)

# Configuration
DATASET_PATH = "RedCode-Exec/bash2text_dataset_json"
OUTPUT_DIR = "bash2text/api_responses"
LLM_LIST = ["llama3-8b-8192", "gemini-2.0-flash", "gpt-4o", "claude-3-5-sonnet-20241022", "deepseek-chat"]
TARGET_DIRECTORY = "2025-03-08_09-55"  # Specify the subdirectory here

# Function to load JSON data from a file
async def load_json(file_path):
    async with aiofiles.open(file_path, "r") as f:
        return json.loads(await f.read())


# Function to identify errors and replace them
async def correct_errors(directory, indices_to_process=None, target_index=None, target_model=None, target_task_type=None):
    """
    Identifies API errors in output JSON files within a directory and replaces them
    by re-querying the LLMs.  Optionally filters files to process based on provided indices.
    """

    files_to_process = []
    for filename in os.listdir(directory):
        if "output_index" in filename and filename.endswith(".json"):
            # Extract the starting and ending index from the filename
            try:
                index_start = int(filename.split("index")[1].split("_")[0])
                index_end = int(filename.split("_")[2])
            except (IndexError, ValueError):
                print(f"Warning: Could not parse index from filename {filename}. Skipping.")
                continue

            # Check if the file should be processed based on the provided index range
            if indices_to_process is None or any(i+1 >= index_start and i+1 <= index_end for i in indices_to_process):
                files_to_process.append(filename)

    if not files_to_process:
        print("No files to process based on the specified criteria.")
        return
    
    for filename in files_to_process:

        output_file_path = os.path.join(directory, filename)
        print(f"Processing file: {output_file_path}")

        # Derive the corresponding input file name
        index_range = filename.split("index")[1].split("_codes")[0]
        input_filename = f"index{index_range}_codes_full_upd.json"
        input_file_path = os.path.join(DATASET_PATH, input_filename)

        try:
            output_data = await load_json(output_file_path)
            input_data = await load_json(input_file_path)
        except FileNotFoundError as e:
            print(f"Error: Input or output file not found: {e}")
            continue
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in file: {e}")
            continue

        # Create a mapping of index to the prompt from the input JSON data.
        input_prompt_map = {item["Index"]: (item["Text_summary"], item["Text_details"]) for item in input_data}

        # Iterate through entries in the output file
        for output_entry in output_data:
            index = output_entry["Index"]

            # Apply target index filter
            if target_index is not None and int(index.split("_")[0]) != target_index:
                continue

            if index not in input_prompt_map:
                print(f"Warning: Index {index} not found in input data. Skipping.")
                continue

            summary_prompt, details_prompt = input_prompt_map[index]

            # Process Summary and Details tasks separately
            for task_type in ["Summary", "Details"]:
                #Apply target task type filter
                if target_task_type is not None and task_type != target_task_type:
                    continue
                # Create tasks and store model names alongside
                tasks = []
                model_names = []
                for model_name, response in output_entry["Responses"][task_type].items():
                    # Apply target model filter
                    if target_model is not None and model_name != target_model:
                        continue

                    if (response is not None and "API Error" in response) or (response is None):  # Explicitly check for "API Error" or if the response is "None"
                        print(f"  Found error for Index: {index}, Model: {model_name}, Task: {task_type}")
                        model_names.append(model_name)
                        if task_type == "Summary":
                            tasks.append(query_model(model_name, summary_prompt))
                        else:
                            tasks.append(query_model(model_name, details_prompt))

                # Run tasks concurrently
                new_responses = await asyncio.gather(*tasks)

                # Update the responses based on the model name
                for model_name, new_response in zip(model_names, new_responses):
                    output_entry["Responses"][task_type][model_name] = new_response
                    print(f"  Replaced {model_name} with: {new_response}")


        # Write the corrected data back to the output file
        try:
            async with aiofiles.open(output_file_path, "w") as outfile:
                await outfile.write(json.dumps(output_data, indent=4))
            print(f"  Successfully corrected and saved: {output_file_path}")
        except IOError as e:
            print(f"Error writing to file: {e}")

async def query_model(model_name, prompt):
    """Queries the specified model with the given prompt."""
    if model_name == "llama3-8b-8192":
        return await query_groq(prompt)
    elif model_name == "gemini-2.0-flash":
        return await query_gemini(prompt)
    elif model_name == "gpt-4o":
        return await query_openai(prompt, max_tokens=1024)  # Add max_tokens here
    elif model_name == "claude-3-5-sonnet-20241022":
        return await query_anthropic(prompt, max_tokens=1024)  # Add max_tokens here
    elif model_name == "deepseek-chat":
        return await query_deepseek(prompt, max_tokens=1024)  # Add max_tokens here
    else:
        return f"Error: Unknown model {model_name}"


async def main(indices_to_process=None, target_index=None, target_model=None, target_task_type=None):
    # Use the specified target directory
    target_dir_path = os.path.join(OUTPUT_DIR, TARGET_DIRECTORY)
    if os.path.isdir(target_dir_path):
        await correct_errors(target_dir_path, indices_to_process, target_index, target_model, target_task_type)
    else:
        print(f"Error: Target directory not found: {target_dir_path}")


if __name__ == "__main__":
    # Process only index file 7
    #asyncio.run(main(target_index=7))

    # Process only index 16 within the index 7 file. Note the upperbound is the "end" value in "output_index1_30" from the filename which is 30 in the above example
    #indices_to_process=[15] #indices are 0 based so "index 16" is 15, and "output_index1_30" needs to contain it
    #asyncio.run(main(indices_to_process=[15], target_index=7))

    # Process only model gemini-2.0-flash in the Summary section in only index 16 file in index file 7
    indices_to_process=[15]
    asyncio.run(main(indices_to_process=[15], target_index=7, target_model="gemini-2.0-flash", target_task_type="Summary"))