import requests
import os
import json
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv
import logging
from tenacity import retry, stop_after_attempt, wait_fixed
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()
API_URL = os.getenv("API_URL")
API_TOKEN = os.getenv("API_TOKEN")
OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT")
MODEL_NAME = os.getenv("MODEL_NAME")
LOW_QUALITY_TAG_ID = int(os.getenv("LOW_QUALITY_TAG_ID"))
HIGH_QUALITY_TAG_ID = int(os.getenv("HIGH_QUALITY_TAG_ID"))
MAX_DOCUMENTS = int(os.getenv("MAX_DOCUMENTS"))

PROMPT_DEFINITION = """
Please review the following document content and determine if it is of low quality or high quality.
Low quality means the content contains many meaningless or unrelated words or sentences.
High quality means the content is clear, organized, and meaningful.
Respond strictly with "low quality" or "high quality".
Content:
"""

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self, url, endpoint, model):
        self.url = url
        self.endpoint = endpoint
        self.model = model

    def evaluate_content(self, content, prompt):
        payload = {"model": self.model, "prompt": f"{prompt}{content}"}
        try:
            response = requests.post(f"{self.url}{self.endpoint}", json=payload)
            response.raise_for_status()
            responses = response.text.strip().split("\n")
            full_response = ""
            for res in responses:
                try:
                    res_json = json.loads(res)
                    if 'response' in res_json:
                        full_response += res_json['response']
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON object: {e}")
                    logger.error(f"Response text: {res}")
            if "high quality" in full_response.lower():
                return "high quality"
            elif "low quality" in full_response.lower():
                return "low quality"
            else:
                return ''
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending request to Ollama: {e}")
            return ''

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_documents_with_content(api_url, api_token, max_documents):
    headers = {'Authorization': f'Token {api_token}'}
    params = {'page_size': 100}
    documents = []
    total_collected = 0

    while True:
        response = requests.get(f'{api_url}/documents/', headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        new_docs = data.get('results', [])
        documents.extend([doc for doc in new_docs if doc.get('content', '').strip()])
        total_collected += len(new_docs)

        if total_collected >= max_documents or not data.get('next'):
            break
        else:
            params['page'] = data['next'].split('page=')[1].split('&')[0]

    return documents[:max_documents]

def get_csrf_token(session, api_url, api_token):
    headers = {'Authorization': f'Token {api_token}'}
    response = session.get(api_url, headers=headers)
    response.raise_for_status()
    csrf_token = response.cookies.get('csrftoken')
    if not csrf_token:
        raise ValueError("CSRF Token not found in response cookies.")
    logger.info(f"CSRF Token: {csrf_token}")
    return csrf_token

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def tag_document(document_id, api_url, api_token, tag_id, csrf_token):
    headers = {
        'Authorization': f'Token {api_token}',
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    url = f'{api_url}/documents/{document_id}/'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    existing_tags = response.json().get('tags', [])

    if tag_id not in existing_tags:
        payload = {"tags": existing_tags + [tag_id]}
        response = requests.patch(url, json=payload, headers=headers)
        logger.info(f"Tagging Response: {response.status_code} - {response.text}")
        response.raise_for_status()
    else:
        logger.info(f"Document {document_id} already has the selected tag.")

def process_documents(documents, api_url, api_token, ignore_already_tagged):
    session = requests.Session()
    csrf_token = get_csrf_token(session, api_url, api_token)
    ollama_service = OllamaService(OLLAMA_URL, OLLAMA_ENDPOINT, MODEL_NAME)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for document in documents:
            content = document.get('content', '')
            if ignore_already_tagged and document.get('tags'):
                logger.info(f"Skipping Document ID {document['id']} as it is already tagged.")
                continue
            futures.append(executor.submit(process_single_document, document, content, ollama_service, api_url, api_token, csrf_token))
        
        for future in tqdm(futures, desc="Processing documents", unit="doc"):
            future.result()

def process_single_document(document, content, ollama_service, api_url, api_token, csrf_token):
    quality_response = ollama_service.evaluate_content(content, PROMPT_DEFINITION)
    logger.info(f"Ollama Response for Document ID {document['id']}: {quality_response}")

    if quality_response.lower() == 'low quality':
        try:
            tag_document(document['id'], api_url, api_token, LOW_QUALITY_TAG_ID, csrf_token)
            logger.info(f"Document ID {document['id']} tagged as low quality.")
        except requests.exceptions.HTTPError as e:
            logger.error(f"Failed to tag document ID {document['id']} as low quality: {e}")
    elif quality_response.lower() == 'high quality':
        try:
            tag_document(document['id'], api_url, api_token, HIGH_QUALITY_TAG_ID, csrf_token)
            logger.info(f"Document ID {document['id']} tagged as high quality.")
        except requests.exceptions.HTTPError as e:
            logger.error(f"Failed to tag document ID {document['id']} as high quality: {e}")

def main():
    logger.info("Searching for documents with content...")
    documents = fetch_documents_with_content(API_URL, API_TOKEN, MAX_DOCUMENTS)

    if documents:
        logger.info(f"Found {len(documents)} documents with content.")
        for doc in documents:
            logger.info(f"Document ID: {doc['id']}, Title: {doc['title']}")

        ignore_already_tagged = os.getenv("IGNORE_ALREADY_TAGGED", "yes").lower() == 'yes'
        confirm = os.getenv("CONFIRM_PROCESS", "yes").lower()

        if confirm == "yes":
            process_documents(documents, API_URL, API_TOKEN, ignore_already_tagged)
            logger.info("Processing completed.")
        else:
            logger.info("Processing canceled.")
    else:
        logger.info("No documents with content found.")

if __name__ == "__main__":
    main()
