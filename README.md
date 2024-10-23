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
- `requests` library
- `tqdm` library
- `inquirer` library

## 📦 Installation

Follow these steps to set up the Document Quality Checker:

1. **Clone the Repository**:
    ```sh
    git clone https://github.com/yourusername/document-quality-checker.git
    cd document-quality-checker
    ```

2. **Install Required Libraries**:
    ```sh
    pip install requests tqdm inquirer
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
- `MAX_DOCUMENTS`: The maximum number of documents to process in a single run.

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

## 📝 Example

Here is an example configuration snippet to help you get started:

```python
# Configuration
API_URL = 'http://yourpaperlessserver:port/api'
API_TOKEN = 'YOURPAPERLESSAPITOKEN'
OLLAMA_URL = 'http://localhost:11434'
OLLAMA_ENDPOINT = '/api/generate'
PROMPT_DEFINITION = """
Please review the following document content and determine if it is of low quality or high quality.
Low quality means the content contains many meaningless or unrelated words or sentences.
High quality means the content is clear, organized, and meaningful.
Respond strictly with "low quality" or "high quality".
Content:
"""
LOW_QUALITY_TAG_ID = 1  # Replace with the actual tag ID for low quality
HIGH_QUALITY_TAG_ID = 2  # Replace with the actual tag ID for high quality
MODEL_NAME = 'llama3'  # Replace with the actual model name to be used
MAX_DOCUMENTS = 5  # Set the maximum number of documents to process

# Run the script
if __name__ == '__main__':
    main()
```

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/hendkai/paperless_sort_low_quality_ollama/blob/main/LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## 📬 Contact

If you have any questions or suggestions, feel free to open an issue or contact the repository owner.
