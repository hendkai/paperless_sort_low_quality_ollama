# 📄 Document Quality Checker

This script fetches and analyzes documents from a Paperless server, tagging them as low or high quality based on a quality check using Ollama. It supports ignoring already tagged documents during the analysis.

## ✨ Features

- 📥 Fetch documents from a Paperless server based on a search query.
- 🔍 Analyze document content using Ollama for quality assessment.
- 🏷️ Tag documents as low or high quality based on the analysis.
- ⚙️ User-configurable server URLs for Paperless and Ollama.
- 🚫 Option to ignore documents that are already tagged.
- ⚡ Efficient processing with detailed logging.

## 🛠️ Requirements

- Python 3.x
- `requests` library
- `tqdm` library

## 📦 Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/document-quality-checker.git
    cd document-quality-checker
    ```

2. Install the required libraries:
    ```sh
    pip install requests tqdm
    ```

## ⚙️ Configuration

Edit the configuration variables in the script to match your environment:

- `API_URL`: The URL of your Paperless server.
- `API_TOKEN`: Your Paperless API token.
- `OLLAMA_URL`: The URL of your Ollama server.
- `OLLAMA_ENDPOINT`: The endpoint for Ollama's quality check API.
- `PROMPT_DEFINITION`: The prompt definition for Ollama's API.
- `LOW_QUALITY_TAG_ID`: The tag ID for low-quality documents.
- `HIGH_QUALITY_TAG_ID`: The tag ID for high-quality documents.
- `MODEL_NAME`: The model name to be used with Ollama.
- `MAX_DOCUMENTS`: The maximum number of documents to process.

## 🚀 Usage

1. Run the script:
    ```sh
    python script.py
    ```

2. Follow the prompts to:
   - Choose whether to ignore already tagged documents.
   - Confirm the processing of documents.

## 📝 Example

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
LOW_QUALITY_TAG_ID = 23  # Replace with the actual tag ID for low quality
HIGH_QUALITY_TAG_ID = 24  # Replace with the actual tag ID for high quality
MODEL_NAME = 'llama3'  # Replace with the actual model name to be used
MAX_DOCUMENTS = 5  # Set the maximum number of documents to process

# Run the script
if __name__ == '__main__':
    main()
```

## 📜 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## 📬 Contact

If you have any questions or suggestions, feel free to open an issue or contact the repository owner.
```
