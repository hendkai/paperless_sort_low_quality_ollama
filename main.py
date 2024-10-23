import requests
from datetime import datetime
from tqdm import tqdm
import json
import inquirer
import logging
import time

# Configuration
API_URL = 'http://paperlessngx:8777/api'
API_TOKEN = 'YOURAPITOKEN'
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

# Setup logging
logging.basicConfig(filename='document_quality_checker.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
            next_page = data['next'].split('page=')[1].split('&')[0]
            params['page'] = next_page

    return documents[:max_documents]

def get_csrf_token(session, api_url, api_token):
    headers = {'Authorization': f'Token {api_token}'}
    response = session.get(api_url, headers=headers)
    response.raise_for_status()
    csrf_token = response.cookies.get('csrftoken')
    logging.info(f"CSRF Token: {csrf_token}")
    return csrf_token

def send_to_ollama(content, ollama_url, endpoint, prompt, model):
    url = f"{ollama_url}{endpoint}"
    payload = {"model": model, "prompt": f"{prompt}{content}"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        responses = response.text.strip().split("\n")
        full_response = ""
        for res in responses:
            try:
                res_json = json.loads(res)
                if 'response' in res_json:
                    full_response += res_json['response']
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON object: {e}")
                logging.error(f"Response text: {res}")
        if "high quality" in full_response.lower():
            return "high quality"
        elif "low quality" in full_response.lower():
            return "low quality"
        else:
            return ''
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending request to Ollama: {e}")
        return ''

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
        logging.info(f"Tagging Response: {response.status_code} - {response.text}")
        response.raise_for_status()
    else:
        logging.info(f"Document {document_id} already has the selected tag.")

def process_documents(documents, api_url, api_token, ignore_already_tagged):
    session = requests.Session()
    csrf_token = get_csrf_token(session, api_url, api_token)
    
    for document in tqdm(documents, desc="Processing documents", unit="doc"):
        content = document.get('content', '')
        if ignore_already_tagged and document.get('tags'):
            logging.info(f"Skipping Document ID {document['id']} as it is already tagged.")
            continue
        quality_response = send_to_ollama(content, OLLAMA_URL, OLLAMA_ENDPOINT, PROMPT_DEFINITION, MODEL_NAME)
        logging.info(f"Ollama Response for Document ID {document['id']}: {quality_response}")
        
        if quality_response.lower() == 'low quality':
            try:
                tag_document(document['id'], api_url, api_token, LOW_QUALITY_TAG_ID, csrf_token)
                logging.info(f"Document ID {document['id']} tagged as low quality.")
            except requests.exceptions.HTTPError as e:
                logging.error(f"Failed to tag document ID {document['id']} as low quality: {e}")
        elif quality_response.lower() == 'high quality':
            try:
                tag_document(document['id'], api_url, api_token, HIGH_QUALITY_TAG_ID, csrf_token)
                logging.info(f"Document ID {document['id']} tagged as high quality.")
            except requests.exceptions.HTTPError as e:
                logging.error(f"Failed to tag document ID {document['id']} as high quality: {e}")

def generate_summary_report(documents, report_file):
    with open(report_file, 'w') as file:
        file.write("Summary Report\n")
        file.write("====================\n")
        for document in documents:
            file.write(f"Document ID: {document['id']}, Title: {document['title']}\n")
            file.write(f"Tags: {document.get('tags', [])}\n")
            file.write("--------------------\n")
    logging.info(f"Summary report saved to {report_file}")

def main():
    print("Searching for documents with content...")
    documents = fetch_documents_with_content(API_URL, API_TOKEN, MAX_DOCUMENTS)

    if documents:
        print(f"Found {len(documents)} documents with content.")
        for doc in documents:
            print(f"Document ID: {doc['id']}, Title: {doc['title']}")

        questions = [
            inquirer.List('ignore_tagged',
                          message="Do you want to ignore already tagged documents?",
                          choices=['yes', 'no']),
            inquirer.List('confirm',
                          message="Do you want to process these documents?",
                          choices=['yes', 'no'])
        ]
        answers = inquirer.prompt(questions)
        
        if answers['confirm'] == 'yes':
            ignore_already_tagged = answers['ignore_tagged'] == 'yes'
            process_documents(documents, API_URL, API_TOKEN, ignore_already_tagged)
            print("Processing completed.")
            generate_summary_report(documents, 'summary_report.txt')
        else:
            print("Processing canceled.")
    else:
        print("No documents with content found.")

if __name__ == "__main__":
    main()
