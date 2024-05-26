import requests
from tqdm import tqdm
import concurrent.futures

# Konfiguration
API_URL = 'http://yourpaperlessserver/api'
API_TOKEN = 'YOURPAPERLESSAPITOKEN'
LIMIT = 20  # Limit der Dokumente pro Anfrage
SEARCH_QUERY = 'Entgelt'  # Suchanfrage
OLLAMA_URL = 'http://localhost:11434'  # Ollama-Server-URL

def fetch_all_tags():
    headers = {'Authorization': f'Token {API_TOKEN}'}
    response = requests.get(f'{API_URL}/tags/', headers=headers)
    if response.status_code == 200:
        return response.json()['results']
    else:
        print(f"Fehler beim Abrufen der Tags, Statuscode: {response.status_code}")
        return []

def select_tags(tags, prompt):
    print(prompt)
    for tag in tags:
        print(f"ID: {tag['id']}, Name: {tag['name']}")
    selected_tag_ids = input("Bitte geben Sie die IDs der Tags ein, die durch Komma getrennt sind: ").split(',')
    selected_tag_ids = [int(tag_id.strip()) for tag_id in selected_tag_ids]
    return selected_tag_ids

def get_document_content(document_id):
    headers = {'Authorization': f'Token {API_TOKEN}'}
    response = requests.get(f'{API_URL}/documents/{document_id}/text/', headers=headers)
    if response.status_code == 200:
        try:
            content = response.json().get('text', '')
            return content
        except ValueError:
            print(f"Kein JSON-Inhalt gefunden für Dokument {document_id}. Möglicherweise ist der Textinhalt leer.")
            return ""
    else:
        print(f"Fehler beim Abrufen des Inhalts für Dokument {document_id}, Statuscode: {response.status_code}")
        return ""

def is_content_valid(content, ollama_url):
    # Verwenden Sie Ollama, um die Qualität des Textes zu bewerten
    response = requests.post(ollama_url, json={"text": content})
    if response.status_code == 200:
        score = response.json().get('quality_score', 0)
        # Niedrige Qualität, wenn der Score unter 0.5 liegt
        return score < 0.5
    else:
        print(f"Fehler bei der Bewertung des Inhalts, Statuscode: {response.status_code}")
        return False

def tag_document_as_low_quality(document_id, tag_id):
    headers = {'Authorization': f'Token {API_TOKEN}', 'Content-Type': 'application/json'}
    data = {"tags": [tag_id]}
    response = requests.patch(f'{API_URL}/documents/{document_id}/', json=data, headers=headers)
    if response.status_code != 200:
        print(f"Fehler beim Taggen des Dokuments {document_id}, Statuscode: {response.status_code}")

def get_documents(page, search_query):
    headers = {'Authorization': f'Token {API_TOKEN}'}
    params = {'limit': LIMIT, 'offset': (page - 1) * LIMIT, 'query': search_query}
    response = requests.get(f'{API_URL}/documents/', headers=headers, params=params, timeout=30)
    if response.status_code == 200:
        data = response.json()
        print(f"Seite {page} erfolgreich abgerufen, {len(data['results'])} Dokumente gefunden.")
        return data['results']
    else:
        print(f"Fehler beim Abrufen der Dokumente, Statuscode: {response.status_code}")
        return []

def document_has_ignored_tags(document, ignored_tag_ids):
    document_tags = document.get('tags', [])
    return any(tag['id'] in ignored_tag_ids for tag in document_tags)

def process_document(doc, tag_id, ollama_url):
    doc_id = doc["id"]
    content = get_document_content(doc_id)
    if not is_content_valid(content, ollama_url):
        tag_document_as_low_quality(doc_id, tag_id)

def process_documents(tag_id, ignored_tag_ids, ollama_url):
    page = 1
    while True:
        documents = get_documents(page, SEARCH_QUERY)
        if not documents:
            print("Keine weiteren Dokumente zum Analysieren gefunden.")
            break
        documents_to_process = [doc for doc in documents if not document_has_ignored_tags(doc, ignored_tag_ids)]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            list(tqdm(executor.map(lambda doc: process_document(doc, tag_id, ollama_url), documents_to_process), total=len(documents_to_process), desc=f"Seite {page} verarbeiten"))
        page += 1

def main():
    tags = fetch_all_tags()
    if tags:
        tag_id = select_tags(tags, "Bitte wählen Sie den Tag aus, mit dem die Dokumente bei niedriger Qualität markiert werden sollen:")[0]
        print(f"Sie haben den Tag mit der ID {tag_id} ausgewählt.")
        ignored_tag_ids = select_tags(tags, "Bitte wählen Sie die Tags aus, deren Dokumente ignoriert werden sollen:")
        print(f"Dokumente mit den folgenden Tag-IDs werden ignoriert: {ignored_tag_ids}")
        process_documents(tag_id, ignored_tag_ids, OLLAMA_URL)
    else:
        print("Keine Tags verfügbar.")

if __name__ == '__main__':
    main()