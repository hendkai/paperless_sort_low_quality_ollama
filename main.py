import requests
import os
import json
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv
import logging
from tenacity import retry, stop_after_attempt, wait_fixed
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import sys
import time
from colorama import init, Fore, Style

# Initialize Colorama
init()

# Load environment variables
load_dotenv()
API_URL = os.getenv("API_URL")
API_TOKEN = os.getenv("API_TOKEN")
OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT")
MODEL_NAME = os.getenv("MODEL_NAME")
SECOND_MODEL_NAME = os.getenv("SECOND_MODEL_NAME")
THIRD_MODEL_NAME = os.getenv("THIRD_MODEL_NAME")
LOW_QUALITY_TAG_ID = int(os.getenv("LOW_QUALITY_TAG_ID"))
HIGH_QUALITY_TAG_ID = int(os.getenv("HIGH_QUALITY_TAG_ID"))
MAX_DOCUMENTS = int(os.getenv("MAX_DOCUMENTS"))
NUM_LLM_MODELS = int(os.getenv("NUM_LLM_MODELS", 3))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
RENAME_DOCUMENTS = os.getenv("RENAME_DOCUMENTS", "no").lower() == 'yes'

PROMPT_DEFINITION = """
Please review the following document content and determine if it is of low quality or high quality.
Low quality means the content contains many meaningless or unrelated words or sentences.
High quality means the content is clear, organized, and meaningful.
Step-by-step evaluation process:
1. Check for basic quality indicators such as grammar and coherence.
2. Assess the overall organization and meaningfulness of the content.
3. Make a final quality determination based on the above criteria.
Respond strictly with "low quality" or "high quality".
Content:
"""

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def show_robot_animation():
    frames = [
        f"{Fore.CYAN}🤖 Searching Documents {Fore.GREEN}[{Fore.YELLOW}═══════{Fore.GREEN}] |{Style.RESET_ALL}",
        f"{Fore.CYAN}🤖 Searching Documents {Fore.GREEN}[{Fore.YELLOW}═══════{Fore.GREEN}] /{Style.RESET_ALL}",
        f"{Fore.CYAN}🤖 Searching Documents {Fore.GREEN}[{Fore.YELLOW}═══════{Fore.GREEN}] -{Style.RESET_ALL}",
        f"{Fore.CYAN}🤖 Searching Documents {Fore.GREEN}[{Fore.YELLOW}═══════{Fore.GREEN}] \\{Style.RESET_ALL}"
    ]
    for frame in frames:
        sys.stdout.write('\r' + frame)
        sys.stdout.flush()
        time.sleep(0.2)

class OllamaService:
    def __init__(self, url: str, endpoint: str, model: str) -> None:
        self.url = url
        self.endpoint = endpoint
        self.model = model

    def evaluate_content(self, content: str, prompt: str, document_id: int) -> str:
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
                    logger.error(f"Error decoding JSON object for document ID {document_id}: {e}")
                    logger.error(f"Response text: {res}")
            if "high quality" in full_response.lower():
                return "high quality"
            elif "low quality" in full_response.lower():
                return "low quality"
            else:
                return ''
        except requests.exceptions.RequestException as e:
            if response.status_code == 404:
                logger.error(f"404 Client Error: Not Found for document ID {document_id}: {e}")
                return '404 Client Error: Not Found'
            else:
                logger.error(f"Error sending request to Ollama for document ID {document_id}: {e}")
                return ''

class EnsembleOllamaService:
    def __init__(self, services: list) -> None:
        self.services = services

    def evaluate_content(self, content: str, prompt: str, document_id: int) -> str:
        results = []
        for service in self.services:
            result = service.evaluate_content(content, prompt, document_id)
            logger.info(f"Model {service.model} result for document ID {document_id}: {result}")
            if result:
                results.append(result)
        
        consensus_result, consensus_reached = self.consensus_logic(results)
        return consensus_result, consensus_reached

    def consensus_logic(self, results: list) -> tuple:
        if not results:
            return '', False
        
        result_count = {}
        for result in results:
            if result in result_count:
                result_count[result] += 1
            else:
                result_count[result] = 1
        
        max_count = max(result_count.values())
        majority_results = [result for result, count in result_count.items() if count == max_count]
        
        if len(majority_results) == 1:
            return majority_results[0], True
        else:
            return '', False

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_documents_with_content(api_url: str, api_token: str, max_documents: int) -> list:
    headers = {'Authorization': f'Token {api_token}'}
    params = {'page_size': 100}
    documents = []
    total_collected = 0

    while True:
        show_robot_animation()
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

    sys.stdout.write('\r' + ' ' * 50 + '\r')  # Clear animation
    return documents[:max_documents]

def get_csrf_token(session: requests.Session, api_url: str, api_token: str) -> Optional[str]:
    headers = {'Authorization': f'Token {api_token}'}
    response = session.get(api_url, headers=headers)
    response.raise_for_status()
    csrf_token = response.cookies.get('csrftoken')
    if not csrf_token:
        raise ValueError("CSRF Token not found in response cookies.")
    logger.info(f"CSRF Token: {csrf_token}")
    return csrf_token

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def tag_document(document_id: int, api_url: str, api_token: str, tag_id: int, csrf_token: str) -> None:
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

def process_documents(documents: list, api_url: str, api_token: str, ignore_already_tagged: bool) -> None:
    session = requests.Session()
    csrf_token = get_csrf_token(session, api_url, api_token)
    services = []
    if NUM_LLM_MODELS >= 1:
        services.append(OllamaService(OLLAMA_URL, OLLAMA_ENDPOINT, MODEL_NAME))
    if NUM_LLM_MODELS >= 2:
        services.append(OllamaService(OLLAMA_URL, OLLAMA_ENDPOINT, SECOND_MODEL_NAME))
    if NUM_LLM_MODELS >= 3:
        services.append(OllamaService(OLLAMA_URL, OLLAMA_ENDPOINT, THIRD_MODEL_NAME))
    ensemble_service = EnsembleOllamaService(services)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for document in documents:
            content = document.get('content', '')
            if ignore_already_tagged and document.get('tags'):
                logger.info(f"Skipping document ID {document['id']} as it is already tagged.")
                continue
            futures.append(executor.submit(process_single_document, document, content, ensemble_service, api_url, api_token, csrf_token))
        
        for future in tqdm(futures, desc=f"{Fore.CYAN}🤖 Processing Documents{Style.RESET_ALL}", 
                          unit="doc", bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
                          colour='green'):
            future.result()

def process_single_document(document: dict, content: str, ensemble_service: EnsembleOllamaService, api_url: str, api_token: str, csrf_token: str) -> None:
    document_id = document['id']
    logger.info(f"==== Verarbeite Dokument ID: {document_id} ====")
    logger.info(f"Aktueller Titel: '{document.get('title', 'Kein Titel')}'")
    logger.info(f"Inhaltslänge: {len(content)} Zeichen")
    
    quality_response, consensus_reached = ensemble_service.evaluate_content(content, PROMPT_DEFINITION, document_id)
    logger.info(f"Ollama Qualitätsbewertung für Dokument ID {document_id}: {quality_response}")
    logger.info(f"Konsensus erreicht: {consensus_reached}")

    if consensus_reached:
        if quality_response.lower() == 'low quality':
            try:
                logger.info(f"Dokument {document_id} wird als 'Low Quality' markiert (Tag ID: {LOW_QUALITY_TAG_ID})")
                tag_document(document_id, api_url, api_token, LOW_QUALITY_TAG_ID, csrf_token)
                logger.info(f"Dokument ID {document_id} erfolgreich als 'Low Quality' markiert.")
                print(f"Die KI-Modelle haben entschieden, die Datei als 'Low Quality' einzustufen.")
            except requests.exceptions.HTTPError as e:
                logger.error(f"Fehler beim Markieren des Dokuments ID {document_id} als 'Low Quality': {e}")
        elif quality_response.lower() == 'high quality':
            try:
                logger.info(f"Dokument {document_id} wird als 'High Quality' markiert (Tag ID: {HIGH_QUALITY_TAG_ID})")
                tag_document(document_id, api_url, api_token, HIGH_QUALITY_TAG_ID, csrf_token)
                logger.info(f"Dokument ID {document_id} erfolgreich als 'High Quality' markiert.")
                print(f"Die KI-Modelle haben entschieden, die Datei als 'High Quality' einzustufen.")
                
                # Dokument sofort umbenennen, wenn es als high quality eingestuft wurde
                logger.info(f"Beginne Umbenennungsprozess für High-Quality-Dokument {document_id}...")
                details = fetch_document_details(api_url, api_token, document_id)
                old_title = details.get('title', '')
                logger.info(f"Aktueller Titel vor Umbenennung: '{old_title}'")
                
                logger.info(f"Generiere neuen Titel basierend auf Inhalt (Länge: {len(details.get('content', ''))} Zeichen)")
                new_title = generate_new_title(details.get('content', ''))
                logger.info(f"Neuer generierter Titel: '{new_title}'")
                
                update_document_title(api_url, api_token, document_id, new_title, csrf_token, old_title)
                logger.info(f"Umbenennung für Dokument {document_id} abgeschlossen!")
                
            except requests.exceptions.HTTPError as e:
                logger.error(f"Fehler beim Markieren oder Umbenennen des Dokuments ID {document_id}: {e}")
    else:
        logger.warning(f"Die KI-Modelle konnten keinen Konsensus für Dokument ID {document_id} finden. Das Dokument wird übersprungen.")
        print(f"Die KI-Modelle konnten keinen Konsensus für Dokument ID {document_id} finden. Das Dokument wird übersprungen.")

    logger.info(f"==== Verarbeitung von Dokument ID: {document_id} abgeschlossen ====\n")
    time.sleep(1)  # Add delay between requests

def fetch_document_details(api_url: str, api_token: str, document_id: int) -> dict:
    headers = {'Authorization': f'Token {api_token}'}
    response = requests.get(f'{api_url}/documents/{document_id}/details', headers=headers)
    response.raise_for_status()
    return response.json()

def generate_new_title(content: str) -> str:
    logger.info("Beginne Titelgenerierungsprozess...")
    if not content:
        logger.warning("Kein Inhalt vorhanden für Titelgenerierung. Verwende Standardtitel.")
        return "Untitled Document"
    
    # Einfache Implementierung: Verwende die ersten Wörter als Titel
    words = content.split()
    logger.info(f"Inhalt enthält {len(words)} Wörter.")
    
    title_words = words[:5] if len(words) > 5 else words
    title = " ".join(title_words)
    logger.info(f"Erster Titelentwurf: '{title}'")
    
    # Begrenze auf 100 Zeichen und entferne Zeilenumbrüche
    title = title.replace("\n", " ").strip()
    if len(title) > 100:
        logger.info(f"Titel zu lang ({len(title)} Zeichen). Kürze auf 100 Zeichen...")
        title = title[:97] + "..."
    
    logger.info(f"Finaler generierter Titel: '{title}'")
    return title

def update_document_title(api_url: str, api_token: str, document_id: int, new_title: str, csrf_token: str, old_title: str) -> None:
    logger.info(f"Beginne API-Aufruf zur Umbenennung von Dokument {document_id}...")
    logger.info(f"Ändere Titel von '{old_title}' zu '{new_title}'")
    
    headers = {
        'Authorization': f'Token {api_token}',
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    payload = {"title": new_title}
    
    try:
        response = requests.patch(f'{api_url}/documents/{document_id}/', json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"API-Antwort: Status {response.status_code}")
        logger.info(f"Dokument ID {document_id} erfolgreich umbenannt von '{old_title}' zu '{new_title}'")
        print(f"Dokument ID {document_id} wurde umbenannt von '{old_title}' zu '{new_title}'")
    except requests.exceptions.RequestException as e:
        logger.error(f"Fehler beim API-Aufruf zur Umbenennung: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Antwort vom Server: {e.response.text}")
        raise

def main() -> None:
    print(f"{Fore.CYAN}🤖 Welcome to the Document Quality Analyzer!{Style.RESET_ALL}")
    logger.info("Searching for documents with content...")
    documents = fetch_documents_with_content(API_URL, API_TOKEN, MAX_DOCUMENTS)

    if documents:
        logger.info(f"{Fore.CYAN}🤖 {len(documents)} documents with content found.{Style.RESET_ALL}")
        for doc in documents:
            logger.info(f"Document ID: {doc['id']}, Title: {doc['title']}")

        ignore_already_tagged = os.getenv("IGNORE_ALREADY_TAGGED", "yes").lower() == 'yes'
        confirm = os.getenv("CONFIRM_PROCESS", "yes").lower()

        if confirm == "yes":
            print(f"{Fore.CYAN}🤖 Starting processing...{Style.RESET_ALL}")
            process_documents(documents, API_URL, API_TOKEN, ignore_already_tagged)
            print(f"{Fore.GREEN}🤖 Processing completed!{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}🤖 Processing aborted.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}🤖 No documents with content found.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
