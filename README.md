# 📄 Document Quality Checker

This tool is designed to fetch and analyze documents from a Paperless server, tagging them as low or high quality based on a quality check using Ollama. It offers the flexibility to ignore already tagged documents during the analysis, making it efficient and user-friendly.

## 🏗️ Architecture

This project follows a modular architecture with clear separation of concerns:

```
src/
├── config/         # Configuration management
├── api/            # Paperless API client
├── llm/            # Ollama LLM service
├── quality/        # Quality analysis logic
├── processing/     # Document processing workflows
├── cli/            # Command-line interface
└── container.py    # Dependency injection container
```

### Key Design Principles

- **Modular Structure**: Each module has a single responsibility
- **Dependency Injection**: Loose coupling through container.py
- **Testability**: Clear interfaces enable easy mocking
- **Maintainability**: Modules are < 200 lines each

## ✨ Features

- 📥 **Fetch Documents**: Retrieve documents from a Paperless server based on a customizable search query.
- 🔍 **Analyze Content**: Utilize Ollama to assess the quality of document content.
- 🏷️ **Tag Documents**: Automatically tag documents as low or high quality based on the analysis results.
- ⚙️ **Configurable Settings**: User-configurable server URLs for both Paperless and Ollama, allowing for seamless integration with your environment.
- 🚫 **Ignore Tagged Documents**: Option to skip documents that have already been tagged, enhancing processing efficiency.
- ⚡ **Efficient Processing**: Detailed logging ensures efficient processing and easy troubleshooting.
- 🖥️ **Interactive CLI**: Implemented an interactive command-line interface (CLI) with options and menus for better user interaction.
- 📊 **Detailed Logging and Reporting**: Detailed logging of actions and events during script execution and a summary report generated at the end of the script.

## 🛠️ Requirements

To run this script, ensure you have the following prerequisites installed:

- Python 3.x

## 📦 Installation

Follow these steps to set up the Document Quality Checker:

1. **Clone the Repository**:
    ```sh
    git clone https://github.com/hendkai/paperless_sort_low_quality_ollama
    cd document-quality-checker
    ```

2. **Install Required Libraries**:
    ```sh
    pip install -r requirements.txt
    ```

## ⚙️ Configuration

Before running the tool, configure the necessary variables to match your environment. The configuration is managed through the `src/config/config.py` module. Set the following environment variables:

- `API_URL`: The URL of your Paperless server.
- `API_TOKEN`: Your Paperless API token for authentication.
- `OLLAMA_URL`: The URL of your Ollama server.
- `OLLAMA_ENDPOINT`: The specific endpoint for Ollama's quality check API.
- `PROMPT_DEFINITION`: The prompt definition to be used with Ollama's API for quality assessment.
- `LOW_QUALITY_TAG_ID`: The tag ID for documents classified as low quality.
- `HIGH_QUALITY_TAG_ID`: The tag ID for documents classified as high quality.
- `MODEL_NAME`: The name of the model to be used with Ollama for analysis.
- `SECOND_MODEL_NAME`: The name of the second model to be used with Ollama for analysis.
- `MAX_DOCUMENTS`: The maximum number of documents to process in a single run.
- `IGNORE_ALREADY_TAGGED`: Whether to ignore already tagged documents.
- `CONFIRM_PROCESS`: Whether to require confirmation before processing.

### Setting Environment Variables

To set environment variables, follow these steps:

1. **Copy `.env.example` to `.env`**:
    ```sh
    cp .env.example .env
    ```

2. **Update the values in `.env`**:
    Open the `.env` file in a text editor and update the values to match your environment.

3. **Ensure `.env` is not committed to version control**:
    Check your `.gitignore` file to ensure that `.env` is listed, preventing it from being committed to version control.

### Creating and Configuring Tags on Paperless-ngx

Before running the script, ensure that the tags for low and high quality documents are created and configured in your Paperless-ngx instance:

1. **Log in to Paperless-ngx**:
   - Open your web browser and navigate to your Paperless-ngx instance.
   - Log in with your credentials.

2. **Create Tags**:
   - Go to the **Tags** section in the Paperless-ngx interface.
   - Click on **Add Tag**.
   - Create a tag named "LOW_QUALITY".
   - In the dropdown, set **Assignment Algorithm** to "Disable automatic assignment".
   - Create another tag named "HIGH_QUALITY" and set the same option.

3. **Determine Tag IDs**:
   - After creating the tags, click on the tag name (e.g., "HIGH_QUALITY").
   - Click on the **Documents** button next to the tag name.
   - This will filter all documents with the tag and update the URL in your browser.
   - The URL will look something like `http://192.168.1.204:8000/documents?tags__id__all=2&sort=created&reverse=1&page=1`.
   - The tag ID for "HIGH_QUALITY" is the number after `tags__id__all=` (e.g., `2`).
   - Repeat the process for the "LOW_QUALITY" tag to determine its ID.

4. **Update Configuration**:
   - Update the `LOW_QUALITY_TAG_ID` and `HIGH_QUALITY_TAG_ID` in the script configuration with the determined IDs.

### Obtaining the Paperless-ngx API Token

To obtain the API token required for authentication:

1. **Log in to Paperless-ngx**:
   - Open your web browser and navigate to your Paperless-ngx instance.
   - Log in with your credentials.

2. **Generate API Token**:
   - Go to the **Settings** section.
   - Navigate to the **API** tab.
   - Click on **Generate Token**.
   - Copy the generated token for use in the script configuration.

## 🚀 Usage

1. **Run the Tool**:
    ```sh
    python -m src
    ```

    The entry point is in `src/__main__.py` which orchestrates the modular components through the dependency injection container.

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
* **Retry Mechanism**: A retry mechanism is implemented in the `src/llm/service.py` module to handle transient errors using the `tenacity` library.
* **Error Handling**: The `LLMService` class in `src/llm/service.py` includes specific error handling for various status codes. Errors are logged and appropriate actions are taken.

## Ensuring Correct `OLLAMA_URL` and `OLLAMA_ENDPOINT`

To ensure the correct `OLLAMA_URL` and `OLLAMA_ENDPOINT`, you can follow these steps:

* **Verify `.env` file**: Ensure that the `OLLAMA_URL` and `OLLAMA_ENDPOINT` values in your `.env` file are correct. The `.env.example` file provides a template for these values.
* **Check environment variables**: Confirm that the environment variables are being loaded correctly in `src/config/config.py` using the `load_dotenv()` function.
* **Test the URL and endpoint**: Manually test the `OLLAMA_URL` and `OLLAMA_ENDPOINT` by sending a request using tools like `curl` or Postman to ensure they are reachable and returning the expected response.

## Using the `tenacity` Library for Retry Mechanisms

The `tenacity` library is used in the modular architecture for retry mechanisms:

* **Installation**: The `tenacity` library is included in `requirements.txt`.
* **Implementation**: The `src/api/client.py` module uses `@retry` decorators for API calls to Paperless.
* **Configuration**: Functions are decorated with `@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))`, retrying up to 3 times with a 2-second wait between attempts.
* **Exception Handling**: Each module handles exceptions appropriately, with the `@retry` decorator automatically retrying failed requests.

## Environment Variables

The following environment variables are used by the `src/config/config.py` module and should be defined in the `.env` file:

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

## 📚 Module Documentation

### Core Modules

- **`src/config/config.py`**: Manages application configuration using environment variables
- **`src/api/client.py`**: Handles all Paperless API interactions with retry logic
- **`src/llm/service.py`**: Provides LLM functionality through Ollama API
- **`src/quality/analyzer.py`**: Analyzes document quality using LLM services
- **`src/processing/processor.py`**: Orchestrates document processing workflows
- **`src/cli/interface.py`**: Provides interactive command-line interface
- **`src/container.py`**: Dependency injection container wiring all modules

### Module Interactions

1. **CLI Interface** (`src/cli/interface.py`) receives user input
2. **Configuration** (`src/config/config.py`) loads environment settings
3. **Container** (`src/container.py`) injects dependencies
4. **API Client** (`src/api/client.py`) fetches documents from Paperless
5. **LLM Service** (`src/llm/service.py`) queries Ollama for analysis
6. **Quality Analyzer** (`src/quality/analyzer.py`) evaluates document quality
7. **Processor** (`src/processing/processor.py`) coordinates tagging and updates

## 🧪 Testing

The modular architecture enables comprehensive testing:

- Each module can be tested independently
- Clear interfaces make mocking dependencies easy
- Run tests with: `pytest tests/`

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/hendkai/paperless_sort_low_quality_ollama/blob/main/LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## 📬 Contact

If you have any questions or suggestions, feel free to open an issue or contact the repository owner.
