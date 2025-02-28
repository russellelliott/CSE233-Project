## Data

Python to Text Translations: https://github.com/AI-secure/RedCode/tree/main/dataset/RedCode-Exec/py2text_dataset_json

RedCode prompt success evalauation: https://github.com/AI-secure/RedCode/blob/main/evaluation/RedCode_Exec/evaluation.py

## Project Structure

The project consists of 3 main directories

`analysis_results`: Contains the analysis results ran from `evalMultiple.py` on the files from the `bash2text` directory.
`bash2text`: Contains the following files:
* `main.py`: Runs the unedited prompts from the `RedCode-Exec` dataset. Generates output JSON files with outputs from the LLMs. These outputs are put in the `api_responses` folder within the `bash2text` directory.
* `main-context.py`: Uses many of the functions from `main.py`, but runs with custom "jailbreak" prompts to try to encourage the LLM to generate malicious code.
* `evalMultiple.py`: Parses through selected files from the `bash2text/api_responses` folder. Evaluates whether a prompt is a success or rejection through string comparison to several strings used in RedCode evaluaiton file: https://github.com/AI-secure/RedCode/blob/main/evaluation/RedCode_Exec/evaluation.py Saves logs to `analysis_results` folder.
`RedCode-Exec`: contains the files from the RedCode dataset for Bash and Python codes and prompts
https://github.com/AI-secure/RedCode/tree/main/dataset
`llm-performance`: Contains graphs based off the `analysis_results` files, showing how often each of the LLMs succeeded or failed in generated malicious code, or encoutnered some sort of 429 rate limit error. While this has been tackled previously for GPT4o and Claude, Gemini experieinced it a few times recently.

