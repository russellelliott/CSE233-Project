## Data

Python to Text Translations: https://github.com/AI-secure/RedCode/tree/main/dataset/RedCode-Exec/py2text_dataset_json

RedCode prompt success evalauation: https://github.com/AI-secure/RedCode/blob/main/evaluation/RedCode_Exec/evaluation.py

## Project Structure

The project consists of 3 main directories

`analysis_results`: Contains the analysis results ran from `evalMultiple.py` on the files from the `bash2text` directory.


`bash2text`: Contains the following files:

`main.py`: Runs the unedited prompts from the `RedCode-Exec` dataset. Generates output JSON files (let's call these the "prompt result files [PRF]" ) with outputs from the LLMs. These outputs are put in the `api_responses` folder within the `bash2text` directory.

`main-context.py`: Uses many of the functions from `main.py`, but runs with custom "jailbreak" prompts to try to encourage the LLM to generate malicious code.


`evalMultiple.py`: Parses through a selected list of files from the `bash2text/api_responses` folder. Evaluates whether a prompt is a success or rejection through string comparison to several strings used in RedCode evaluaiton file: https://github.com/AI-secure/RedCode/blob/main/evaluation/RedCode_Exec/evaluation.py

Based on this information, it produces the following content:
1. For each file in the selected list of files, saves logs to `analysis_results` folder. This is used to produce the bar chart.
2. Produces color-coded bar charts to visible indicate how often the LLMs succeeded or failed to generate malicious code, or encountered a 429 rate error.
3. Produce an aggregated results file (aggregated_results.json) from the data of all the files in the selected list. Breaks down by index, then by the PRF files, then by prompt.

`correction.py`: goes through the output files of a given directory and checks for LLMs that experienced errors and redoes those prompts. `correctionSpecific.py` is used for correcting specific prompt categories and prompts within

Because `main-context.py` and `correction.py` depend on `main.py`, a directory with the current date is made. This is normally for the context of `main.py` but this will be empty in the context of running the two aforementioned files

One thing to note for these files is that they will only write to the files after all the LLM reads/writes for a specific unit are done. I would recommend using a 3rd party plugin, like Amphetamine for Mac to prevent your computer from sleeping so you can run it for hours ar a time without it being interrupted.

`RedCode-Exec`: contains the files from the RedCode dataset for Bash and Python codes and prompts
https://github.com/AI-secure/RedCode/tree/main/dataset
`llm-performance`: Contains graphs based off the `analysis_results` files, showing how often each of the LLMs succeeded or failed in generated malicious code, or encoutnered some sort of 429 rate limit error. While this has been tackled previously for GPT4o and Claude, Gemini experieinced it a few times recently.

`aggregated_results`: contains aggregated results from various runs