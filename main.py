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
import argparse
from colorama import init, Fore, Style
from progress_tracker import ProgressTracker

# Initialize Colorama
init()

# Load environment variables
load_dotenv()

def get_env_int(key: str, default: int = 0) -> int:
    """Safely get integer environment variable with default."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning(f"Invalid value for {key}: {value}, using default: {default}")
        return default

API_URL = os.getenv("API_URL")
API_TOKEN = os.getenv("API_TOKEN")
OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT")
MODEL_NAME = os.getenv("MODEL_NAME")
SECOND_MODEL_NAME = os.getenv("SECOND_MODEL_NAME")
THIRD_MODEL_NAME = os.getenv("THIRD_MODEL_NAME")
LOW_QUALITY_TAG_ID = get_env_int("LOW_QUALITY_TAG_ID")
HIGH_QUALITY_TAG_ID = get_env_int("HIGH_QUALITY_TAG_ID")
MAX_DOCUMENTS = get_env_int("MAX_DOCUMENTS", 100)
NUM_LLM_MODELS = get_env_int("NUM_LLM_MODELS", 3)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
RENAME_DOCUMENTS = os.getenv("RENAME_DOCUMENTS", "no").lower() == 'yes'
PROGRESS_STATE_FILE = os.getenv("PROGRESS_STATE_FILE", "progress_state.json")

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

# Initialize progress tracker
progress_tracker = ProgressTracker(PROGRESS_STATE_FILE)

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

    def generate_title(self, prompt: str, content_for_id: str) -> str:
        payload = {"model": self.model, "prompt": prompt}
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
                    logger.error(f"Error decoding JSON object for title generation: {e}")
                    logger.error(f"Response text: {res}")
            
            # Bereinige die Antwort von Anführungszeichen oder anderen Formatierungen
            title = full_response.strip().replace('"', '').replace("'", '')
            logger.info(f"LLM hat folgenden Titel generiert: '{title}'")
            return title
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending request to Ollama for title generation: {e}")
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

    # Sequentielle Verarbeitung statt mit ThreadPoolExecutor
    total_documents = len([doc for doc in documents if not (ignore_already_tagged and doc.get('tags'))])
    processed_count = 0
    
    print(f"{Fore.CYAN}🤖 Starte sequentielle Verarbeitung von {total_documents} Dokumenten...{Style.RESET_ALL}")
    
    for document in documents:
        content = document.get('content', '')
        if ignore_already_tagged and document.get('tags'):
            logger.info(f"Überspringe Dokument ID {document['id']}, da es bereits markiert ist.")
            continue

        # Check if document was already processed (resume capability)
        if progress_tracker.is_processed(document['id']):
            logger.info(f"Überspringe Dokument ID {document['id']}, da es bereits verarbeitet wurde (Progress-Check).")
            continue

        # Fortschrittsanzeige aktualisieren
        processed_count += 1
        print(f"{Fore.CYAN}🤖 Verarbeite Dokument {processed_count}/{total_documents} (ID: {document['id']}){Style.RESET_ALL}")

        # Startzeit für die Verarbeitungsmessung
        start_time = time.time()

        # Dokument vollständig verarbeiten, bevor mit dem nächsten fortgefahren wird
        try:
            result = process_single_document(document, content, ensemble_service, api_url, api_token, csrf_token)
            processing_time = time.time() - start_time

            # Save checkpoint after successful or failed processing
            progress_tracker.save_checkpoint(
                document_id=result['document_id'],
                quality_response=result['quality_response'],
                consensus_reached=result['consensus_reached'],
                new_title=result.get('new_title'),
                error=result.get('error'),
                processing_time=processing_time
            )

            if result.get('error'):
                print(f"{Fore.RED}⚠️ Dokument {document['id']} mit Fehlern verarbeitet ({processed_count}/{total_documents}){Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✅ Dokument {document['id']} verarbeitet ({processed_count}/{total_documents}){Style.RESET_ALL}")
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Fehler bei der Verarbeitung von Dokument {document['id']}: {e}")
            print(f"{Fore.RED}❌ Fehler bei Dokument {document['id']}: {str(e)[:100]}...{Style.RESET_ALL}")

            # Save checkpoint even when an unexpected error occurs
            progress_tracker.save_checkpoint(
                document_id=document['id'],
                quality_response='',
                consensus_reached=False,
                new_title=None,
                error=str(e),
                processing_time=processing_time
            )

        # Klare visuelle Trennung zwischen Dokumenten in der Konsole
        print(f"{Fore.YELLOW}{'=' * 80}{Style.RESET_ALL}\n")
    
    print(f"{Fore.GREEN}🤖 Verarbeitung aller Dokumente abgeschlossen!{Style.RESET_ALL}")

def process_single_document(document: dict, content: str, ensemble_service: EnsembleOllamaService, api_url: str, api_token: str, csrf_token: str) -> dict:
    document_id = document['id']
    logger.info(f"==== Verarbeite Dokument ID: {document_id} ====")
    logger.info(f"Aktueller Titel: '{document.get('title', 'Kein Titel')}'")
    logger.info(f"Inhaltslänge: {len(content)} Zeichen")

    result = {
        'document_id': document_id,
        'quality_response': '',
        'consensus_reached': False,
        'new_title': None,
        'error': None
    }

    try:
        quality_response, consensus_reached = ensemble_service.evaluate_content(content, PROMPT_DEFINITION, document_id)
        logger.info(f"Ollama Qualitätsbewertung für Dokument ID {document_id}: {quality_response}")
        logger.info(f"Konsensus erreicht: {consensus_reached}")
        result['quality_response'] = quality_response
        result['consensus_reached'] = consensus_reached

        if consensus_reached:
            if quality_response.lower() == 'low quality':
                try:
                    logger.info(f"Dokument {document_id} wird als 'Low Quality' markiert (Tag ID: {LOW_QUALITY_TAG_ID})")
                    tag_document(document_id, api_url, api_token, LOW_QUALITY_TAG_ID, csrf_token)
                    logger.info(f"Dokument ID {document_id} erfolgreich als 'Low Quality' markiert.")
                    print(f"Die KI-Modelle haben entschieden, die Datei als 'Low Quality' einzustufen.")
                except requests.exceptions.HTTPError as e:
                    logger.error(f"Fehler beim Markieren des Dokuments ID {document_id} als 'Low Quality': {e}")
                    result['error'] = str(e)
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
                    result['new_title'] = new_title

                    update_document_title(api_url, api_token, document_id, new_title, csrf_token, old_title)
                    logger.info(f"Umbenennung für Dokument {document_id} abgeschlossen!")

                except requests.exceptions.HTTPError as e:
                    logger.error(f"Fehler beim Markieren oder Umbenennen des Dokuments ID {document_id}: {e}")
                    result['error'] = str(e)
        else:
            logger.warning(f"Die KI-Modelle konnten keinen Konsensus für Dokument ID {document_id} finden. Das Dokument wird übersprungen.")
            print(f"Die KI-Modelle konnten keinen Konsensus für Dokument ID {document_id} finden. Das Dokument wird übersprungen.")

        logger.info(f"==== Verarbeitung von Dokument ID: {document_id} abgeschlossen ====\n")
        time.sleep(1)  # Add delay between requests
    except Exception as e:
        logger.error(f"Unexpected error processing document {document_id}: {e}")
        result['error'] = str(e)

    return result

def fetch_document_details(api_url: str, api_token: str, document_id: int) -> dict:
    headers = {'Authorization': f'Token {api_token}'}
    try:
        logger.info(f"Rufe Dokumentdetails ab für ID {document_id}...")
        response = requests.get(f'{api_url}/documents/{document_id}/', headers=headers)
        logger.info(f"Details-Antwort Status: {response.status_code}")
        response.raise_for_status()
        document_data = response.json()
        logger.info(f"Dokumentdetails für ID {document_id} erfolgreich abgerufen")
        return document_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Fehler beim Abrufen der Dokumentdetails für ID {document_id}: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Server-Antwort: {e.response.text}")
        return {}

def generate_new_title(content: str) -> str:
    logger.info("Beginne Titelgenerierungsprozess mit dem ersten LLM-Modell...")
    if not content:
        logger.warning("Kein Inhalt vorhanden für Titelgenerierung. Verwende Standardtitel.")
        return "Untitled Document"
    
    # Gekürzte Version des Inhalts für die LLM-Anfrage vorbereiten
    # Begrenzen wir auf die ersten 1000 Zeichen, um die API-Anfrage effizient zu halten
    truncated_content = content[:1000] if len(content) > 1000 else content
    logger.info(f"Verwende die ersten {len(truncated_content)} Zeichen des Inhalts für die Titelgenerierung")
    
    # Verwende das erste LLM-Modell aus der .env-Datei (MODEL_NAME)
    title_prompt = f"""
    Du bist ein Experte für die Erstellung sinnvoller Dokumenttitel.
    Analysiere den folgenden Inhalt und erstelle einen prägnanten, aussagekräftigen Titel, 
    der den Inhalt treffend zusammenfasst.
    Der Titel sollte nicht länger als 100 Zeichen sein.
    Antworte nur mit dem Titel, ohne Erklärung oder zusätzlichen Text.
    
    Inhalt:
    {truncated_content}
    """
    
    logger.info("Sende Anfrage an LLM-Modell für Titelgenerierung...")
    
    try:
        # Verwende das erste Modell für die Titelgenerierung
        ollama_service = OllamaService(OLLAMA_URL, OLLAMA_ENDPOINT, MODEL_NAME)
        title = ollama_service.generate_title(title_prompt, truncated_content)
        
        # Fallback, falls das Modell keinen Titel zurückgibt
        if not title or len(title.strip()) == 0:
            logger.warning("LLM-Modell hat keinen Titel zurückgegeben. Verwende Fallback-Methode.")
            words = content.split()
            title_words = words[:5] if len(words) > 5 else words
            title = " ".join(title_words)
        
        # Begrenze auf 100 Zeichen und entferne Zeilenumbrüche
        title = title.replace("\n", " ").strip()
        if len(title) > 100:
            logger.info(f"Titel zu lang ({len(title)} Zeichen). Kürze auf 100 Zeichen...")
            title = title[:97] + "..."
        
        logger.info(f"Finaler generierter Titel: '{title}'")
        return title
    except Exception as e:
        logger.error(f"Fehler bei der LLM-Titelgenerierung: {e}")
        # Fallback-Methode im Fehlerfall
        words = content.split()
        title_words = words[:5] if len(words) > 5 else words
        title = " ".join(title_words)
        title = title.replace("\n", " ").strip()[:100]
        logger.info(f"Fallback-Titel generiert: '{title}'")
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
        logger.info(f"Sende PATCH-Anfrage an: {api_url}/documents/{document_id}/")
        logger.info(f"Headers: {headers}")
        logger.info(f"Payload: {payload}")
        
        response = requests.patch(f'{api_url}/documents/{document_id}/', json=payload, headers=headers)
        
        logger.info(f"API-Antwort Status: {response.status_code}")
        logger.info(f"API-Antwort Headers: {response.headers}")
        logger.info(f"API-Antwort Text: {response.text[:500]}...")  # Nur die ersten 500 Zeichen
        
        response.raise_for_status()  # Dies wird einen Fehler auslösen, wenn der Status-Code nicht erfolgreich ist
        
        # Prüfen, ob die Umbenennung erfolgreich war
        details = fetch_document_details(api_url, api_token, document_id)
        current_title = details.get('title', '')
        
        # Immer den aktuellen Titel nach der Änderung protokollieren
        logger.info(f"Aktueller Titel nach der Änderung: '{current_title}'")
        
        if current_title == new_title:
            logger.info(f"✅ ERFOLG: Dokument ID {document_id} wurde erfolgreich umbenannt von '{old_title}' zu '{current_title}'")
            print(f"✅ Dokument ID {document_id} wurde erfolgreich umbenannt von '{old_title}' zu '{current_title}'")
        else:
            logger.warning(f"⚠️ WARNUNG: Titel wurde möglicherweise nicht aktualisiert. Gewünschter neuer Titel: '{new_title}', Aktueller Titel: '{current_title}'")
            print(f"⚠️ Umbenennung möglicherweise fehlgeschlagen. Gewünschter Titel: '{new_title}', Aktueller Titel: '{current_title}'")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ FEHLER beim API-Aufruf zur Umbenennung: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Server-Antwort: Status {e.response.status_code}")
            logger.error(f"Antwort vom Server: {e.response.text}")
        else:
            logger.error("Keine Antwort vom Server erhalten (Verbindungsfehler)")
        print(f"❌ Fehler bei der Umbenennung von Dokument {document_id}: {e}")
        raise

def show_progress() -> None:
    """
    Display the current progress state summary.

    Shows statistics about processed documents including total count,
    consensus count, error count, and processing time.
    """
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}📊 Processing Progress Summary{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")

    summary = progress_tracker.get_progress_summary()

    print(f"\n{Fore.GREEN}Total Documents Processed:{Style.RESET_ALL} {summary['total_processed']}")
    print(f"{Fore.GREEN}Consensus Reached:{Style.RESET_ALL} {summary['consensus_count']}")
    print(f"{Fore.RED}Errors:{Style.RESET_ALL} {summary['error_count']}")
    print(f"{Fore.YELLOW}Total Processing Time:{Style.RESET_ALL} {summary['total_processing_time']:.2f} seconds")

    if summary['created_at']:
        created_time = datetime.fromisoformat(summary['created_at']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n{Fore.CYAN}State Created:{Style.RESET_ALL} {created_time}")

    if summary['last_updated']:
        updated_time = datetime.fromisoformat(summary['last_updated']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{Fore.CYAN}Last Updated:{Style.RESET_ALL} {updated_time}")

    # Show recent processed documents
    if progress_tracker.state.get('documents'):
        print(f"\n{Fore.CYAN}Recently Processed Documents:{Style.RESET_ALL}")
        recent_docs = progress_tracker.state['documents'][-5:]  # Show last 5 documents
        for doc in reversed(recent_docs):
            status_icon = f"{Fore.GREEN}✅{Style.RESET_ALL}" if not doc.get('error') else f"{Fore.RED}❌{Style.RESET_ALL}"
            timestamp = datetime.fromisoformat(doc['processed_at']).strftime('%H:%M:%S')
            quality = doc.get('quality_response', 'N/A')
            print(f"  {status_icon} ID {doc['document_id']} | {quality} | {timestamp}")

    print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")

def main() -> None:
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Document Quality Analyzer - Process and classify documents using LLM ensemble',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--show-progress',
        action='store_true',
        help='Display current processing progress and exit'
    )

    parser.add_argument(
        '--clear-state',
        action='store_true',
        help='Clear all processing state and restart from scratch'
    )

    args = parser.parse_args()

    # Handle --show-progress flag
    if args.show_progress:
        show_progress()
        return

    # Handle --clear-state flag
    if args.clear_state:
        print(f"{Fore.YELLOW}⚠️ Clearing all processing state...{Style.RESET_ALL}")
        progress_tracker.clear_state()
        print(f"{Fore.GREEN}✅ State cleared successfully! All documents will be re-processed on next run.{Style.RESET_ALL}")
        return

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
