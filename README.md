# 📄 Document Quality Checker

This script is designed to fetch and analyze documents from a Paperless server, tagging them as low or high quality based on a quality check using Ollama. It offers the flexibility to ignore already tagged documents during the analysis, making it efficient and user-friendly.

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

Before running the script, configure the necessary variables to match your environment. Edit the following settings in the script:

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
