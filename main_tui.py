#!/usr/bin/env python3
"""
Document Quality Analyzer - TUI Dashboard Version
Ein interaktives Terminal User Interface für die Dokumentenanalyse.
"""

import requests
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed
from typing import Optional
import asyncio
from dataclasses import dataclass, field
from enum import Enum

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, ProgressBar, DataTable, Log, Label, Button, Input
from textual.reactive import reactive
from textual.timer import Timer
from textual import work
from textual.worker import Worker, get_current_worker
from textual.message import Message

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


class DocumentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    HIGH_QUALITY = "high_quality"
    LOW_QUALITY = "low_quality"
    NO_CONSENSUS = "no_consensus"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class DocumentInfo:
    id: int
    title: str
    content: str
    status: DocumentStatus = DocumentStatus.PENDING
    model_responses: dict = field(default_factory=dict)
    new_title: Optional[str] = None


@dataclass
class ProcessingStats:
    total: int = 0
    processed: int = 0
    high_quality: int = 0
    low_quality: int = 0
    no_consensus: int = 0
    errors: int = 0
    skipped: int = 0


class OllamaService:
    def __init__(self, url: str, endpoint: str, model: str) -> None:
        self.url = url
        self.endpoint = endpoint
        self.model = model

    def evaluate_content(self, content: str, prompt: str, document_id: int) -> str:
        max_content_length = 4000
        if len(content) > max_content_length:
            content = content[:max_content_length]

        if "/v1/" in self.endpoint:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": f"{prompt}{content}"}],
                "temperature": 0.0
            }
            try:
                response = requests.post(f"{self.url}{self.endpoint}", json=payload, timeout=120)
                response.raise_for_status()
                res_json = response.json()
                full_response = res_json.get('choices', [{}])[0].get('message', {}).get('content', '') or ''

                if "high quality" in full_response.lower():
                    return "high quality"
                elif "low quality" in full_response.lower():
                    return "low quality"
                return ''
            except Exception:
                return ''
        else:
            payload = {"model": self.model, "prompt": f"{prompt}{content}"}
            try:
                response = requests.post(f"{self.url}{self.endpoint}", json=payload, timeout=120)
                response.raise_for_status()
                responses = response.text.strip().split("\n")
                full_response = ""
                for res in responses:
                    try:
                        res_json = json.loads(res)
                        if 'response' in res_json:
                            full_response += res_json['response']
                    except json.JSONDecodeError:
                        pass
                if "high quality" in full_response.lower():
                    return "high quality"
                elif "low quality" in full_response.lower():
                    return "low quality"
                return ''
            except requests.exceptions.RequestException:
                return ''

    def generate_title(self, prompt: str, content_for_id: str) -> str:
        if "/v1/" in self.endpoint:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": f"{prompt}\n\n{content_for_id}"}],
                "temperature": 0.7
            }
            try:
                response = requests.post(f"{self.url}{self.endpoint}", json=payload, timeout=120)
                response.raise_for_status()
                res_json = response.json()
                title = res_json.get('choices', [{}])[0].get('message', {}).get('content', '') or ''
                title = re.sub(r'\[THINK\].*?\[/THINK\]', '', title, flags=re.DOTALL).strip()
                title = title.strip().replace('"', '').replace("'", '')
                return title
            except Exception:
                return ''
        else:
            payload = {"model": self.model, "prompt": prompt}
            try:
                response = requests.post(f"{self.url}{self.endpoint}", json=payload, timeout=120)
                response.raise_for_status()
                responses = response.text.strip().split("\n")
                full_response = ""
                for res in responses:
                    try:
                        res_json = json.loads(res)
                        if 'response' in res_json:
                            full_response += res_json['response']
                    except json.JSONDecodeError:
                        pass
                title = re.sub(r'\[THINK\].*?\[/THINK\]', '', full_response, flags=re.DOTALL).strip()
                title = title.replace('"', '').replace("'", '')
                return title
            except requests.exceptions.RequestException:
                return ''


class EnsembleOllamaService:
    def __init__(self, services: list) -> None:
        self.services = services

    def evaluate_content(self, content: str, prompt: str, document_id: int) -> tuple:
        results = []
        model_responses = {}
        for service in self.services:
            result = service.evaluate_content(content, prompt, document_id)
            model_responses[service.model] = result if result else "No response"
            if result:
                results.append(result)

        consensus_result, consensus_reached = self.consensus_logic(results)
        return consensus_result, consensus_reached, model_responses

    def consensus_logic(self, results: list) -> tuple:
        if not results:
            return '', False

        result_count = {}
        for result in results:
            result_count[result] = result_count.get(result, 0) + 1

        max_count = max(result_count.values())
        majority_results = [r for r, c in result_count.items() if c == max_count]

        if len(majority_results) == 1:
            return majority_results[0], True
        return '', False


# ============== TUI Widgets ==============

class StatsPanel(Static):
    """Panel zeigt Verarbeitungsstatistiken"""

    stats = reactive(ProcessingStats())

    def compose(self) -> ComposeResult:
        yield Static(self._render_stats(), id="stats-content")

    def _render_stats(self) -> str:
        s = self.stats
        progress = (s.processed / s.total * 100) if s.total > 0 else 0
        return f"""[bold cyan]Statistiken[/bold cyan]

[bold]Gesamt:[/bold]        {s.total}
[bold]Verarbeitet:[/bold]   {s.processed} ({progress:.1f}%)
[green]High Quality:[/green]  {s.high_quality}
[red]Low Quality:[/red]   {s.low_quality}
[yellow]Kein Konsens:[/yellow] {s.no_consensus}
[magenta]Fehler:[/magenta]       {s.errors}
[dim]Übersprungen:[/dim]  {s.skipped}"""

    def watch_stats(self, stats: ProcessingStats) -> None:
        try:
            self.query_one("#stats-content", Static).update(self._render_stats())
        except Exception:
            pass  # Widget not yet mounted


class CurrentDocPanel(Static):
    """Panel zeigt aktuelles Dokument"""

    current_doc = reactive(None)

    def compose(self) -> ComposeResult:
        yield Static(self._render_doc(), id="doc-content")

    def _render_doc(self) -> str:
        if not self.current_doc:
            return "[bold cyan]Aktuelles Dokument[/bold cyan]\n\n[dim]Warte auf Start...[/dim]"

        doc = self.current_doc
        status_colors = {
            DocumentStatus.PENDING: "dim",
            DocumentStatus.PROCESSING: "yellow",
            DocumentStatus.HIGH_QUALITY: "green",
            DocumentStatus.LOW_QUALITY: "red",
            DocumentStatus.NO_CONSENSUS: "yellow",
            DocumentStatus.ERROR: "magenta",
            DocumentStatus.SKIPPED: "dim",
        }
        color = status_colors.get(doc.status, "white")
        content_preview = doc.content[:200].replace('\n', ' ') + "..." if len(doc.content) > 200 else doc.content.replace('\n', ' ')

        new_title_info = ""
        if doc.new_title:
            new_title_info = f"\n[bold]Neuer Titel:[/bold] [green]{doc.new_title}[/green]"

        return f"""[bold cyan]Aktuelles Dokument[/bold cyan]

[bold]ID:[/bold] {doc.id}
[bold]Titel:[/bold] {doc.title[:50]}{'...' if len(doc.title) > 50 else ''}{new_title_info}
[bold]Status:[/bold] [{color}]{doc.status.value}[/{color}]

[bold]Vorschau:[/bold]
[dim]{content_preview}[/dim]"""

    def watch_current_doc(self, doc) -> None:
        try:
            self.query_one("#doc-content", Static).update(self._render_doc())
        except Exception:
            pass  # Widget not yet mounted


class DocumentLimitPanel(Static):
    """Panel zum Einstellen der maximalen Dokumentenanzahl"""

    max_docs = reactive(MAX_DOCUMENTS)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("[bold cyan]Dokumente[/bold cyan]", id="limit-header")
            with Horizontal(id="limit-controls"):
                yield Button("-10", id="decrease-btn", variant="error")
                yield Input(value=str(self.max_docs), id="doc-limit-input", type="integer", placeholder="Anzahl")
                yield Button("+10", id="increase-btn", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id not in ("decrease-btn", "increase-btn"):
            return

        input_widget = self.query_one("#doc-limit-input", Input)
        try:
            current = int(input_widget.value) if input_widget.value and input_widget.value.isdigit() else MAX_DOCUMENTS
        except (ValueError, AttributeError):
            current = MAX_DOCUMENTS

        if event.button.id == "decrease-btn":
            new_value = max(1, current - 10)
        else:  # increase-btn
            new_value = current + 10

        input_widget.value = str(new_value)
        self.max_docs = new_value
        self.post_message(self.LimitChanged(new_value))
        # Direkt auf der App setzen
        if hasattr(self.app, 'max_documents'):
            self.app.max_documents = new_value
            self.app.log_message(f"[cyan]Dokumentenlimit: {new_value}[/cyan]")
        event.stop()  # Verhindere dass das Event weitergeleitet wird

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Wenn Enter gedrückt wird im Input-Feld"""
        if event.input.id == "doc-limit-input":
            self._update_value_from_input(event.value)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Wenn sich der Input ändert"""
        if event.input.id == "doc-limit-input":
            self._update_value_from_input(event.value)

    def _update_value_from_input(self, value_str: str) -> None:
        """Hilfsmethode zum Aktualisieren des Werts"""
        try:
            if value_str and value_str.strip():
                value = int(value_str.strip())
                value = max(1, value)
                if value != self.max_docs:
                    self.max_docs = value
                    # Poste die Message und aktualisiere direkt die App
                    self.post_message(self.LimitChanged(value))
                    # Auch direkt auf der App setzen falls Message nicht ankommt
                    if hasattr(self.app, 'max_documents'):
                        self.app.max_documents = value
                        self.app.log_message(f"[cyan]Dokumentenlimit: {value}[/cyan]")
        except ValueError:
            pass

    class LimitChanged(Message):
        """Event wenn das Limit geändert wird"""
        def __init__(self, value: int):
            self.value = value
            super().__init__()

        @property
        def control(self):
            """Damit Textual das Event richtig routen kann"""
            return self._sender


class LLMResponsesPanel(Static):
    """Panel zeigt LLM Model Responses"""

    responses = reactive({})

    def compose(self) -> ComposeResult:
        yield Static(self._render_responses(), id="llm-content")

    def _render_responses(self) -> str:
        if not self.responses:
            return "[bold cyan]LLM Responses[/bold cyan]\n\n[dim]Warte auf Bewertung...[/dim]"

        lines = ["[bold cyan]LLM Responses[/bold cyan]\n"]
        for model, response in self.responses.items():
            if response == "high quality":
                color = "green"
                icon = "+"
            elif response == "low quality":
                color = "red"
                icon = "-"
            else:
                color = "yellow"
                icon = "?"

            model_short = model[:25] + "..." if len(model) > 25 else model
            lines.append(f"[{color}]{icon}[/{color}] [bold]{model_short}[/bold]")
            lines.append(f"  [{color}]{response}[/{color}]")

        return "\n".join(lines)

    def watch_responses(self, responses: dict) -> None:
        try:
            self.query_one("#llm-content", Static).update(self._render_responses())
        except Exception:
            pass  # Widget not yet mounted


class DocumentQualityApp(App):
    """TUI Dashboard für Document Quality Analyzer"""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 3 3;
        grid-columns: 1fr 2fr 1fr;
        grid-rows: auto 1fr auto;
    }

    #header-container {
        column-span: 3;
        height: 3;
        background: $primary-darken-2;
        text-align: center;
        padding: 1;
    }

    #stats-panel {
        row-span: 1;
        border: solid $primary;
        padding: 1;
        height: 100%;
    }

    #main-container {
        row-span: 1;
        layout: vertical;
    }

    #current-doc-panel {
        border: solid $secondary;
        padding: 1;
        height: auto;
        max-height: 12;
    }

    #log-panel {
        border: solid $accent;
        height: 100%;
    }

    #llm-panel {
        row-span: 1;
        border: solid $success;
        padding: 1;
        height: 100%;
    }

    #doc-table-container {
        column-span: 3;
        height: 12;
        border: solid $warning;
    }

    #progress-container {
        column-span: 3;
        height: 3;
        padding: 0 1;
    }

    #button-container {
        column-span: 3;
        height: 5;
        layout: horizontal;
        align: center middle;
    }

    #limit-panel {
        height: 6;
        width: 35;
        border: solid $primary;
        padding: 0 1;
        margin-right: 2;
    }

    #limit-controls {
        height: 3;
        align: center middle;
    }

    #limit-controls Button {
        width: 6;
        min-width: 6;
        margin: 0 1;
    }

    #limit-controls Input {
        width: 12;
        min-width: 12;
        text-align: center;
    }

    #doc-limit-input {
        width: 12;
        min-width: 12;
    }

    Button {
        margin: 0 2;
    }

    ProgressBar {
        width: 100%;
    }

    DataTable {
        height: 100%;
    }

    .status-pending { color: $text-muted; }
    .status-processing { color: yellow; }
    .status-high { color: green; }
    .status-low { color: red; }
    .status-error { color: magenta; }
    """

    BINDINGS = [
        ("q", "quit", "Beenden"),
        ("s", "start", "Start"),
        ("p", "pause", "Pause"),
        ("r", "refresh", "Refresh"),
    ]

    processing = reactive(False)
    paused = reactive(False)
    loading = reactive(True)
    stats = reactive(ProcessingStats())
    documents: list[DocumentInfo] = []
    current_doc_index = reactive(0)
    max_documents = reactive(MAX_DOCUMENTS)

    def compose(self) -> ComposeResult:
        yield Static("[bold]Document Quality Analyzer - TUI Dashboard[/bold]", id="header-container")

        yield StatsPanel(id="stats-panel")

        with Vertical(id="main-container"):
            yield CurrentDocPanel(id="current-doc-panel")
            yield Log(id="log-panel", highlight=True)

        yield LLMResponsesPanel(id="llm-panel")

        with ScrollableContainer(id="doc-table-container"):
            yield DataTable(id="doc-table")

        with Container(id="progress-container"):
            yield ProgressBar(id="progress-bar", total=100, show_eta=True)

        with Horizontal(id="button-container"):
            yield DocumentLimitPanel(id="limit-panel")
            yield Button("Laden", id="reload-btn", variant="primary")
            yield Button("Start", id="start-btn", variant="success")
            yield Button("Pause", id="pause-btn", variant="warning", disabled=True)
            yield Button("Beenden", id="quit-btn", variant="error")

        yield Footer()

    def on_mount(self) -> None:
        self.loading = False  # Nicht mehr beim Start laden
        self.log_message("[bold green]Dashboard gestartet![/bold green]")
        self.log_message(f"API URL: {API_URL}")
        self.log_message(f"Ollama URL: {OLLAMA_URL}")
        self.log_message(f"Modelle: {NUM_LLM_MODELS}")
        self.log_message(f"[cyan]Dokumentenlimit: {self.max_documents} - Klicke 'Laden' um Dokumente zu laden[/cyan]")

        # DataTable setup
        table = self.query_one("#doc-table", DataTable)
        table.add_columns("ID", "Titel", "Status", "Qualität")
        table.cursor_type = "row"

        # Dokumente werden NICHT automatisch geladen - Benutzer muss erst Limit einstellen und dann auf "Laden" klicken

    def log_message(self, message: str) -> None:
        log = self.query_one("#log-panel", Log)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log.write_line(f"[dim]{timestamp}[/dim] {message}")

    @work(exclusive=True, thread=True)
    def load_documents(self) -> None:
        """Lädt Dokumente von der API"""
        worker = get_current_worker()
        max_docs = self.max_documents
        self.call_from_thread(self.log_message, f"[yellow]Lade bis zu {max_docs} Dokumente...[/yellow]")

        try:
            headers = {'Authorization': f'Token {API_TOKEN}'}
            params = {'page_size': 100}
            documents = []

            while len(documents) < max_docs:
                if worker.is_cancelled:
                    return

                response = requests.get(f'{API_URL}/documents/', headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                new_docs = data.get('results', [])

                for doc in new_docs:
                    if doc.get('content', '').strip():
                        # Skip already tagged
                        if os.getenv("IGNORE_ALREADY_TAGGED", "yes").lower() == 'yes' and doc.get('tags'):
                            continue
                        documents.append(DocumentInfo(
                            id=doc['id'],
                            title=doc.get('title', 'Unbekannt'),
                            content=doc.get('content', ''),
                            status=DocumentStatus.PENDING
                        ))

                if not data.get('next') or len(documents) >= max_docs:
                    break
                params['page'] = data['next'].split('page=')[1].split('&')[0]

            self.documents = documents[:max_docs]
            self.call_from_thread(self._update_after_load)

        except Exception as e:
            self.call_from_thread(self.log_message, f"[red]Fehler beim Laden: {e}[/red]")
            self.call_from_thread(self._set_loading_false)

    def _set_loading_false(self) -> None:
        self.loading = False

    def _update_after_load(self) -> None:
        """Update UI after documents are loaded"""
        self.loading = False
        self.stats = ProcessingStats(total=len(self.documents))
        self.query_one("#stats-panel", StatsPanel).stats = self.stats
        self.query_one("#progress-bar", ProgressBar).update(total=max(len(self.documents), 1))

        table = self.query_one("#doc-table", DataTable)
        table.clear()
        for doc in self.documents[:50]:  # Nur die ersten 50 anzeigen
            table.add_row(
                str(doc.id),
                doc.title[:40] + "..." if len(doc.title) > 40 else doc.title,
                doc.status.value,
                "-"
            )

        self.log_message(f"[green]{len(self.documents)} Dokumente geladen - bereit zum Starten (s)[/green]")

    def on_document_limit_panel_limit_changed(self, event: DocumentLimitPanel.LimitChanged) -> None:
        """Handle document limit changes from LimitChanged message"""
        self.max_documents = event.value
        self.log_message(f"[cyan]Dokumentenlimit geändert: {event.value}[/cyan]")

    def watch_max_documents(self, value: int) -> None:
        """Watcher für max_documents Änderungen"""
        try:
            # Synchronisiere mit dem Input-Feld
            limit_panel = self.query_one("#limit-panel", DocumentLimitPanel)
            if limit_panel.max_docs != value:
                limit_panel.max_docs = value
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-btn":
            self.action_start()
        elif event.button.id == "pause-btn":
            self.action_pause()
        elif event.button.id == "quit-btn":
            self.action_quit()
        elif event.button.id == "reload-btn":
            self.action_refresh()

    def action_start(self) -> None:
        if self.loading:
            self.log_message("[yellow]Dokumente werden noch geladen, bitte warten...[/yellow]")
            return
        if not self.documents:
            self.log_message("[red]Keine Dokumente zum Verarbeiten gefunden![/red]")
            return
        if not self.processing:
            self.processing = True
            self.paused = False
            self.query_one("#start-btn", Button).disabled = True
            self.query_one("#pause-btn", Button).disabled = False
            self.log_message("[green]Verarbeitung gestartet![/green]")
            self.process_documents()

    def action_pause(self) -> None:
        self.paused = not self.paused
        btn = self.query_one("#pause-btn", Button)
        if self.paused:
            btn.label = "Fortsetzen"
            self.log_message("[yellow]Verarbeitung pausiert[/yellow]")
        else:
            btn.label = "Pause"
            self.log_message("[green]Verarbeitung fortgesetzt[/green]")

    def action_refresh(self) -> None:
        self.loading = True
        self.load_documents()

    @work(exclusive=True, thread=True)
    def process_documents(self) -> None:
        """Verarbeitet alle Dokumente"""
        worker = get_current_worker()

        # Initialize services
        services = []
        if NUM_LLM_MODELS >= 1:
            services.append(OllamaService(OLLAMA_URL, OLLAMA_ENDPOINT, MODEL_NAME))
        if NUM_LLM_MODELS >= 2:
            services.append(OllamaService(OLLAMA_URL, OLLAMA_ENDPOINT, SECOND_MODEL_NAME))
        if NUM_LLM_MODELS >= 3:
            services.append(OllamaService(OLLAMA_URL, OLLAMA_ENDPOINT, THIRD_MODEL_NAME))

        ensemble_service = EnsembleOllamaService(services)

        # Get CSRF token
        try:
            session = requests.Session()
            headers = {'Authorization': f'Token {API_TOKEN}'}
            response = session.get(API_URL, headers=headers)
            csrf_token = response.cookies.get('csrftoken', '')
        except Exception as e:
            self.call_from_thread(self.log_message, f"[red]CSRF Token Fehler: {e}[/red]")
            return

        for i, doc in enumerate(self.documents):
            if worker.is_cancelled:
                break

            # Pause handling
            while self.paused and not worker.is_cancelled:
                import time
                time.sleep(0.5)

            if worker.is_cancelled:
                break

            self.call_from_thread(self._update_current_doc, i, DocumentStatus.PROCESSING)
            self.call_from_thread(self.log_message, f"[cyan]Verarbeite Dokument {doc.id}...[/cyan]")

            try:
                # Evaluate with ensemble
                quality, consensus, model_responses = ensemble_service.evaluate_content(
                    doc.content, PROMPT_DEFINITION, doc.id
                )

                self.call_from_thread(self._update_llm_responses, model_responses)

                if consensus:
                    if quality.lower() == 'high quality':
                        # Tag as high quality
                        self._tag_document(doc.id, HIGH_QUALITY_TAG_ID, csrf_token)

                        # Generate new title
                        new_title = self._generate_title(doc.content, services[0])
                        if new_title:
                            self._update_doc_title(doc.id, new_title, csrf_token)
                            doc.new_title = new_title

                        doc.status = DocumentStatus.HIGH_QUALITY
                        self.call_from_thread(self._increment_stat, 'high_quality')
                        self.call_from_thread(self.log_message, f"[green]Dokument {doc.id}: HIGH QUALITY[/green]")

                    elif quality.lower() == 'low quality':
                        self._tag_document(doc.id, LOW_QUALITY_TAG_ID, csrf_token)
                        doc.status = DocumentStatus.LOW_QUALITY
                        self.call_from_thread(self._increment_stat, 'low_quality')
                        self.call_from_thread(self.log_message, f"[red]Dokument {doc.id}: LOW QUALITY[/red]")
                else:
                    doc.status = DocumentStatus.NO_CONSENSUS
                    self.call_from_thread(self._increment_stat, 'no_consensus')
                    self.call_from_thread(self.log_message, f"[yellow]Dokument {doc.id}: Kein Konsens[/yellow]")

            except Exception as e:
                doc.status = DocumentStatus.ERROR
                self.call_from_thread(self._increment_stat, 'errors')
                self.call_from_thread(self.log_message, f"[red]Fehler bei {doc.id}: {str(e)[:50]}[/red]")

            self.call_from_thread(self._update_current_doc, i, doc.status)
            self.call_from_thread(self._increment_stat, 'processed')
            self.call_from_thread(self._update_progress, i + 1)
            self.call_from_thread(self._update_table_row, i, doc)

            # Small delay between documents
            import time
            time.sleep(0.5)

        self.call_from_thread(self._processing_complete)

    def _tag_document(self, document_id: int, tag_id: int, csrf_token: str) -> None:
        headers = {
            'Authorization': f'Token {API_TOKEN}',
            'X-CSRFToken': csrf_token,
            'Content-Type': 'application/json'
        }
        url = f'{API_URL}/documents/bulk_edit/'
        payload = {
            "documents": [document_id],
            "method": "modify_tags",
            "parameters": {"add_tags": [tag_id], "remove_tags": []}
        }
        requests.post(url, json=payload, headers=headers)

    def _generate_title(self, content: str, service: OllamaService) -> str:
        if not content:
            return ""

        truncated_content = content[:1000]
        title_prompt = f"""
Du bist ein Experte für die Erstellung sinnvoller Dokumenttitel.
Analysiere den folgenden Inhalt und erstelle einen prägnanten, aussagekräftigen Titel.
Der Titel sollte nicht länger als 100 Zeichen sein.
Antworte nur mit dem Titel, ohne Erklärung.

Inhalt:
{truncated_content}
"""
        title = service.generate_title(title_prompt, truncated_content)
        if title:
            title = title.replace("\n", " ").strip()[:100]
        return title

    def _update_doc_title(self, document_id: int, new_title: str, csrf_token: str) -> None:
        headers = {
            'Authorization': f'Token {API_TOKEN}',
            'X-CSRFToken': csrf_token,
            'Content-Type': 'application/json'
        }
        payload = {"title": new_title}
        requests.patch(f'{API_URL}/documents/{document_id}/', json=payload, headers=headers)

    def _update_current_doc(self, index: int, status: DocumentStatus) -> None:
        if 0 <= index < len(self.documents):
            self.documents[index].status = status
            doc_panel = self.query_one("#current-doc-panel", CurrentDocPanel)
            doc_panel.current_doc = self.documents[index]

    def _update_llm_responses(self, responses: dict) -> None:
        llm_panel = self.query_one("#llm-panel", LLMResponsesPanel)
        llm_panel.responses = responses

    def _increment_stat(self, stat_name: str) -> None:
        new_stats = ProcessingStats(
            total=self.stats.total,
            processed=self.stats.processed + (1 if stat_name == 'processed' else 0),
            high_quality=self.stats.high_quality + (1 if stat_name == 'high_quality' else 0),
            low_quality=self.stats.low_quality + (1 if stat_name == 'low_quality' else 0),
            no_consensus=self.stats.no_consensus + (1 if stat_name == 'no_consensus' else 0),
            errors=self.stats.errors + (1 if stat_name == 'errors' else 0),
            skipped=self.stats.skipped + (1 if stat_name == 'skipped' else 0),
        )
        self.stats = new_stats
        self.query_one("#stats-panel", StatsPanel).stats = self.stats

    def _update_progress(self, current: int) -> None:
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_bar.update(progress=current)

    def _update_table_row(self, index: int, doc: DocumentInfo) -> None:
        if index >= 50:  # Nur die ersten 50 sind in der Tabelle
            return

        table = self.query_one("#doc-table", DataTable)
        status_display = doc.status.value
        quality = "-"

        if doc.status == DocumentStatus.HIGH_QUALITY:
            quality = "[green]HIGH[/green]"
        elif doc.status == DocumentStatus.LOW_QUALITY:
            quality = "[red]LOW[/red]"
        elif doc.status == DocumentStatus.NO_CONSENSUS:
            quality = "[yellow]?[/yellow]"
        elif doc.status == DocumentStatus.ERROR:
            quality = "[magenta]ERR[/magenta]"

        # Update row
        try:
            table.update_cell_at((index, 2), status_display)
            table.update_cell_at((index, 3), quality)
        except Exception:
            pass

    def _processing_complete(self) -> None:
        self.processing = False
        self.query_one("#start-btn", Button).disabled = False
        self.query_one("#pause-btn", Button).disabled = True
        self.log_message("[bold green]Verarbeitung abgeschlossen![/bold green]")

        s = self.stats
        self.log_message(f"Ergebnis: {s.high_quality} High, {s.low_quality} Low, {s.no_consensus} Kein Konsens, {s.errors} Fehler")


def main():
    app = DocumentQualityApp()
    app.run()


if __name__ == "__main__":
    main()
