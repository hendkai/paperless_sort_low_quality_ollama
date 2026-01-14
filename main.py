import requests
import os
import json
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv
import logging
from tenacity import retry, stop_after_attempt, wait_fixed
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List
from dataclasses import dataclass
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
PREVIEW_MODE = os.getenv("PREVIEW_MODE", "no").lower() == 'yes'
PREVIEW_SAMPLE_COUNT = int(os.getenv("PREVIEW_SAMPLE_COUNT", 5))

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

@dataclass
class PreviewResult:
    """Dataclass to store preview evaluation results for a document."""
    document_id: int
    title: str
    content_length: int
    quality_assessment: str
    consensus_reached: bool
    confidence: float
    individual_results: List[dict]
    existing_tags: List[int]
    error: Optional[str] = None

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

    def evaluate_content(self, content: str, prompt: str, document_id: int) -> dict:
        """
        Evaluate content using multiple models and return detailed results.

        Returns:
            dict: Contains:
                - consensus_result: The final quality assessment (e.g., 'high quality', 'low quality')
                - consensus_reached: Boolean indicating if models agreed
                - confidence: Float from 0.0 to 1.0 indicating agreement level
                - individual_results: List of dicts with 'model' and 'result' keys
        """
        individual_results = []
        for service in self.services:
            result = service.evaluate_content(content, prompt, document_id)
            logger.info(f"Model {service.model} result for document ID {document_id}: {result}")
            if result:
                individual_results.append({'model': service.model, 'result': result})

        consensus_result, consensus_reached = self.consensus_logic(individual_results)
        confidence = self._calculate_confidence(individual_results, consensus_result, consensus_reached)

        return {
            'consensus_result': consensus_result,
            'consensus_reached': consensus_reached,
            'confidence': confidence,
            'individual_results': individual_results
        }

    def consensus_logic(self, individual_results: list) -> tuple:
        """Determine consensus from individual model results."""
        if not individual_results:
            return '', False

        result_count = {}
        for item in individual_results:
            result = item['result']
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

    def _calculate_confidence(self, individual_results: list, consensus_result: str, consensus_reached: bool) -> float:
        """Calculate confidence score based on model agreement."""
        if not individual_results or not consensus_reached:
            return 0.0

        total_models = len(individual_results)
        if total_models == 0:
            return 0.0

        # Count how many models agreed with the consensus
        agreement_count = sum(1 for item in individual_results if item['result'] == consensus_result)

        # Confidence is the ratio of agreement to total models
        return round(agreement_count / total_models, 2)

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
        
        # Fortschrittsanzeige aktualisieren
        processed_count += 1
        print(f"{Fore.CYAN}🤖 Verarbeite Dokument {processed_count}/{total_documents} (ID: {document['id']}){Style.RESET_ALL}")
        
        # Dokument vollständig verarbeiten, bevor mit dem nächsten fortgefahren wird
        try:
            process_single_document(document, content, ensemble_service, api_url, api_token, csrf_token)
            print(f"{Fore.GREEN}✅ Dokument {document['id']} verarbeitet ({processed_count}/{total_documents}){Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung von Dokument {document['id']}: {e}")
            print(f"{Fore.RED}❌ Fehler bei Dokument {document['id']}: {str(e)[:100]}...{Style.RESET_ALL}")
        
        # Klare visuelle Trennung zwischen Dokumenten in der Konsole
        print(f"{Fore.YELLOW}{'=' * 80}{Style.RESET_ALL}\n")
    
    print(f"{Fore.GREEN}🤖 Verarbeitung aller Dokumente abgeschlossen!{Style.RESET_ALL}")

def process_single_document(document: dict, content: str, ensemble_service: EnsembleOllamaService, api_url: str, api_token: str, csrf_token: str) -> None:
    document_id = document['id']
    logger.info(f"==== Verarbeite Dokument ID: {document_id} ====")
    logger.info(f"Aktueller Titel: '{document.get('title', 'Kein Titel')}'")
    logger.info(f"Inhaltslänge: {len(content)} Zeichen")

    evaluation = ensemble_service.evaluate_content(content, PROMPT_DEFINITION, document_id)
    quality_response = evaluation['consensus_result']
    consensus_reached = evaluation['consensus_reached']
    confidence = evaluation['confidence']
    individual_results = evaluation['individual_results']

    logger.info(f"Ollama Qualitätsbewertung für Dokument ID {document_id}: {quality_response}")
    logger.info(f"Konsens erreicht: {consensus_reached}")
    logger.info(f"Konfidenz: {confidence}")
    logger.info(f"Individuelle Modellergebnisse: {individual_results}")

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

def preview_sample_documents(documents: list, api_url: str, api_token: str) -> list:
    """
    Process a sample of documents to preview quality assessments.
    Does not tag or rename documents - only evaluates and returns results.
    """
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

    # Take sample of documents
    sample_documents = documents[:PREVIEW_SAMPLE_COUNT]
    total_documents = len(sample_documents)
    processed_count = 0

    logger.info(f"Starting preview of {total_documents} sample documents...")
    print(f"{Fore.CYAN}🤖 Preview mode: Processing {total_documents} sample documents...{Style.RESET_ALL}")

    preview_results = []

    for document in sample_documents:
        content = document.get('content', '')
        document_id = document['id']

        # Progress display
        processed_count += 1
        print(f"{Fore.CYAN}🤖 Previewing document {processed_count}/{total_documents} (ID: {document_id}){Style.RESET_ALL}")

        try:
            logger.info(f"==== Previewing document ID: {document_id} ====")
            logger.info(f"Current title: '{document.get('title', 'No title')}'")
            logger.info(f"Content length: {len(content)} characters")

            # Evaluate quality (without tagging)
            evaluation = ensemble_service.evaluate_content(content, PROMPT_DEFINITION, document_id)
            quality_response = evaluation['consensus_result']
            consensus_reached = evaluation['consensus_reached']
            confidence = evaluation['confidence']
            individual_results = evaluation['individual_results']

            logger.info(f"Quality assessment for document ID {document_id}: {quality_response}")
            logger.info(f"Consensus reached: {consensus_reached}")
            logger.info(f"Confidence: {confidence}")
            logger.info(f"Individual model results: {individual_results}")

            # Build result dictionary
            result = {
                'document_id': document_id,
                'title': document.get('title', 'No title'),
                'content_length': len(content),
                'quality_assessment': quality_response,
                'consensus_reached': consensus_reached,
                'confidence': confidence,
                'individual_results': individual_results,
                'existing_tags': document.get('tags', [])
            }

            preview_results.append(result)

            if consensus_reached:
                if quality_response.lower() == 'low quality':
                    print(f"{Fore.YELLOW}⚠️  Would be tagged as: LOW QUALITY{Style.RESET_ALL}")
                elif quality_response.lower() == 'high quality':
                    print(f"{Fore.GREEN}✅ Would be tagged as: HIGH QUALITY{Style.RESET_ALL}")
                    if RENAME_DOCUMENTS:
                        print(f"{Fore.CYAN}   Would be renamed based on content{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️  No consensus reached - would be skipped{Style.RESET_ALL}")

            logger.info(f"==== Preview of document ID: {document_id} completed ====\n")

        except Exception as e:
            logger.error(f"Error previewing document {document_id}: {e}")
            print(f"{Fore.RED}❌ Error previewing document {document_id}: {str(e)[:100]}...{Style.RESET_ALL}")

            # Add error result
            preview_results.append({
                'document_id': document_id,
                'title': document.get('title', 'No title'),
                'content_length': len(content),
                'quality_assessment': 'ERROR',
                'consensus_reached': False,
                'existing_tags': document.get('tags', []),
                'error': str(e)
            })

        # Clear visual separation between documents
        print(f"{Fore.YELLOW}{'=' * 80}{Style.RESET_ALL}\n")
        time.sleep(1)

    print(f"{Fore.GREEN}🤖 Preview completed!{Style.RESET_ALL}")
    return preview_results

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
