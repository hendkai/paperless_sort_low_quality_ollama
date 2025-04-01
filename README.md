# Document Quality Assessment and Processing Tool

A powerful tool that leverages Large Language Models (LLMs) to automatically evaluate document quality, tag documents, and intelligently rename high-quality content with contextually relevant titles.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen)

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Setup and Installation](#setup-and-installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Processing Flow](#processing-flow)
- [Logging and Monitoring](#logging-and-monitoring)
- [Advanced Options](#advanced-options)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [License](#license)

## ✨ Features

- **AI-Powered Quality Assessment**: Utilizes up to three LLM models to evaluate document quality
- **Consensus-Based Decision Making**: Makes reliable quality judgments by aggregating multiple AI opinions
- **Automatic Document Tagging**: Tags documents as high or low quality based on AI evaluation
- **Intelligent Title Generation**: Automatically creates meaningful titles for high-quality documents
- **Sequential Processing**: Processes documents one at a time for maximum reliability and clarity
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Progress Visualization**: Clear console output showing processing status
- **Error Handling**: Robust error recovery to continue processing despite individual failures

## 🏗️ Architecture

The tool follows a sequential processing architecture:

1. **Document Retrieval**: Fetches documents from the configured API
2. **Quality Assessment**: Uses multiple LLM models for quality evaluation
3. **Consensus Determination**: Aggregates model opinions to reach a decision
4. **Tagging**: Applies appropriate tags based on quality assessment
5. **Title Generation**: For high-quality documents, generates meaningful titles
6. **Renaming**: Updates document titles in the system

## 🚀 Setup and Installation

### Prerequisites

- Python 3.8 or higher
- Ollama installed and running locally or on an accessible server
- Access credentials for your document management API

### Installation Steps

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/document-quality-tool.git
   cd document-quality-tool
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Linux/Mac
   source venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your configuration (see [Configuration](#configuration))

5. Verify Ollama is running:
   ```bash
   curl http://127.0.0.1:11434/api/version
   ```

## ⚙️ Configuration

Create a `.env` file in the project root with the following variables:

```
# Complete URL to your Paperless-ngx API
# Example: http://192.168.2.10:8000/api
API_URL=http://your.paperless.instance:8000/api

# Your Paperless-ngx API Token
# Can be found in: Paperless web interface -> Settings -> API Token
API_TOKEN=your_api_token_here

# URL to your Ollama server
# Default port is 11434
OLLAMA_URL=http://your.ollama.server:11434

# Endpoint for Ollama API requests
# Default is /api/generate for text generation
OLLAMA_ENDPOINT=/api/generate

# Name of the AI model to use
# Available models can be listed using 'ollama list'
MODEL_NAME=llama3.2

# Name of the second AI model to use
# Available models can be listed using 'ollama list'
SECOND_MODEL_NAME=mistral

# Tag ID for low quality documents in Paperless-ngx
# Find the ID in Paperless interface under Tags
LOW_QUALITY_TAG_ID=1

# Tag ID for high quality documents in Paperless-ngx
# Find the ID in Paperless interface under Tags
HIGH_QUALITY_TAG_ID=2

# Maximum number of documents to process
# Set to 0 for unlimited
MAX_DOCUMENTS=1000

# Whether to ignore already tagged documents
# Possible values: yes/no
IGNORE_ALREADY_TAGGED=yes

# Whether to require confirmation before processing
# Possible values: yes/no
CONFIRM_PROCESS=yes
```

## 🚀 Usage

1. **Run the Script**:
    ```sh
    python main.py
    ```

2. **Follow the Prompts**:
   - Choose whether to ignore documents that have already been tagged.
   - Confirm the processing of documents to proceed with the analysis.
   - Select specific documents to process or skip from a list.
   - Review the summary of actions to be taken before executing them.
   - Choose whether to rename documents based on their content.

## 📝 Example

Here is an example configuration snippet to help you get started:

```
# Complete URL to your Paperless-ngx API
# Example: http://192.168.2.10:8000/api
API_URL=http://your.paperless.instance:8000/api

# Your Paperless-ngx API Token
# Can be found in: Paperless web interface -> Settings -> API Token
API_TOKEN=your_api_token_here

# URL to your Ollama server
# Default port is 11434
OLLAMA_URL=http://your.ollama.server:11434

# Endpoint for Ollama API requests
# Default is /api/generate for text generation
OLLAMA_ENDPOINT=/api/generate

# Name of the AI model to use
# Available models can be listed using 'ollama list'
MODEL_NAME=llama3.2

# Name of the second AI model to use
# Available models can be listed using 'ollama list'
SECOND_MODEL_NAME=mistral

# Tag ID for low quality documents in Paperless-ngx
# Find the ID in Paperless interface under Tags
LOW_QUALITY_TAG_ID=1

# Tag ID for high quality documents in Paperless-ngx
# Find the ID in Paperless interface under Tags
HIGH_QUALITY_TAG_ID=2

# Maximum number of documents to process
# Set to 0 for unlimited
MAX_DOCUMENTS=1000

# Whether to ignore already tagged documents
# Possible values: yes/no
IGNORE_ALREADY_TAGGED=yes

# Whether to require confirmation before processing
# Possible values: yes/no
CONFIRM_PROCESS=yes
```

## Handling 404 Client Error from Ollama

To handle the 404 Client Error from Ollama, you can implement the following strategies:

* **Check the URL and Endpoint**: Ensure that the `OLLAMA_URL` and `OLLAMA_ENDPOINT` in your `.env` file are correct. The error might be due to an incorrect URL or endpoint.
* **Retry Mechanism**: Implement a retry mechanism to handle transient errors. The `tenacity` library is already used in the project, so you can wrap the request to Ollama with a retry decorator.
* **Error Handling**: Add specific error handling for the 404 status code in the `evaluate_content` method of the `OllamaService` class in `main.py`. Log the error and return a meaningful message or take appropriate action.

## Ensuring Correct `OLLAMA_URL` and `OLLAMA_ENDPOINT`

To ensure the correct `OLLAMA_URL` and `OLLAMA_ENDPOINT`, you can follow these steps:

* **Verify `.env` file**: Ensure that the `OLLAMA_URL` and `OLLAMA_ENDPOINT` values in your `.env` file are correct. The `.env.example` file provides a template for these values.
* **Check environment variables**: Confirm that the environment variables are being loaded correctly in `main.py` using the `load_dotenv()` function.
* **Test the URL and endpoint**: Manually test the `OLLAMA_URL` and `OLLAMA_ENDPOINT` by sending a request using tools like `curl` or Postman to ensure they are reachable and returning the expected response.

## Using the `tenacity` Library for Retry Mechanisms

To learn about using the `tenacity` library for retry mechanisms, you can follow these steps:

* **Install the `tenacity` library**: Ensure that the `tenacity` library is included in your `requirements.txt` file. It is already listed in the provided `requirements.txt` file.
* **Import the `tenacity` library**: Import the necessary components from the `tenacity` library in your script. For example, in `main.py`, you can see the import statements for `retry`, `stop_after_attempt`, and `wait_fixed`.
* **Define retry logic**: Use the `@retry` decorator to define the retry logic for your functions. For example, in `main.py`, the `fetch_documents_with_content` and `tag_document` functions are decorated with `@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))`, which means they will retry up to 3 times with a 2-second wait between attempts.
* **Handle exceptions**: Ensure that your functions handle exceptions properly. The `@retry` decorator will automatically retry the function if an exception is raised. You can customize the retry behavior by specifying different stop and wait conditions.

By following these steps, you can effectively use the `tenacity` library to implement retry mechanisms in your code.

## Environment Variables

The following environment variables are used in the script and should be defined in the `.env` file:

- `API_URL`: The URL of your Paperless server.
- `API_TOKEN`: Your Paperless API token for authentication.
- `OLLAMA_URL`: The URL of your Ollama server.
- `OLLAMA_ENDPOINT`: The specific endpoint for Ollama's quality check API.
- `MODEL_NAME`: The name of the model to be used with Ollama for analysis.
- `SECOND_MODEL_NAME`: The name of the second model to be used with Ollama for analysis.
- `THIRD_MODEL_NAME`: The name of the third model to be used with Ollama for analysis.
- `LOW_QUALITY_TAG_ID`: The tag ID for documents classified as low quality.
- `HIGH_QUALITY_TAG_ID`: The tag ID for documents classified as high quality.
- `MAX_DOCUMENTS`: The maximum number of documents to process in a single run.
- `NUM_LLM_MODELS`: The number of LLM models to use.
- `IGNORE_ALREADY_TAGGED`: Whether to ignore already tagged documents.
- `CONFIRM_PROCESS`: Whether to require confirmation before processing.
- `LOG_LEVEL`: The logging level for the script.
- `RENAME_DOCUMENTS`: Whether to rename document titles based on their content.

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/hendkai/paperless_sort_low_quality_ollama/blob/main/LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## 📬 Contact

If you have any questions or suggestions, feel free to open an issue or contact the repository owner.
