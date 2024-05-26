# Document Quality Checker

This script fetches and analyzes documents from a Paperless server, tagging them as low quality if they fail a quality check using Ollama. It supports parallel processing for efficiency and allows users to specify tags to ignore during the analysis.

## Features

- Fetch documents from a Paperless server based on a search query.
- Analyze document content using Ollama for quality assessment.
- Tag documents as low quality if they fail the quality check.
- User-configurable server URLs for Paperless and Ollama.
- Option to ignore documents based on user-selected tags.
- Parallel processing for faster document analysis.

## Requirements

- Python 3.x
- `requests` library
- `tqdm` library
- `concurrent.futures` (part of the Python standard library)

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/document-quality-checker.git
    cd document-quality-checker
    ```

2. Install the required libraries:
    ```sh
    pip install requests tqdm
    ```

## Configuration

Edit the configuration variables in the script to match your environment:

- `API_URL`: The URL of your Paperless server.
- `API_TOKEN`: Your Paperless API token.
- `LIMIT`: The number of documents to fetch per request.
- `SEARCH_QUERY`: The search query to filter documents.
- `OLLAMA_URL`: The URL of your Ollama server.

## Usage

1. Run the script:
    ```sh
    python script.py
    ```

2. Follow the prompts to select tags for:
   - Tagging documents as low quality.
   - Ignoring documents based on tags.

## Example

```python
# Konfiguration
API_URL = 'http://yourpaperlessserver:port/api'
API_TOKEN = 'YOURPAPERLESSAPITOKEN'
LIMIT = 20  # Limit der Dokumente pro Anfrage
SEARCH_QUERY = 'Entgelt'  # Suchanfrage
OLLAMA_URL = 'http://yourollamaserver:port/validate'  # Ollama-Server-URL

# Run the script
if __name__ == '__main__':
    main()
