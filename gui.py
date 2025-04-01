import sys
import os
import traceback
import time
import subprocess
from datetime import datetime
import requests
import threading
import dearpygui.dearpygui as dpg

print("Starting DocumentAI GUI...")

# Prüfe, ob dotenv verfügbar ist
env_support = False
try:
    from dotenv import load_dotenv, find_dotenv, set_key
    env_support = True
    load_dotenv()
except ImportError:
    print("Python-dotenv not installed. Settings cannot be saved.")

# Prüfe, ob psutil verfügbar ist
system_monitoring = False
try:
    import psutil
    system_monitoring = True
except ImportError:
    print("Psutil not installed. System monitoring disabled.")

# ASCII-Art für die Fabrik
ASCII_FACTORY_IDLE = """
    +-------------------------------+
    |      DOCUMENT PROCESSING      |
    +-------------------------------+
    |                               |
    |         +---+      +---+      |
    |         |   |      |   |      |
    |         +---+      +---+      |
    |           |          |        |
    |     +---------------------+   |
    |     |                     |   |
    |     |      READY FOR      |   |
    |     |     PROCESSING      |   |
    |     |                     |   |
    |     +---------------------+   |
    |                               |
    |                               |
    |                               |
    +-------------------------------+
"""

ASCII_FACTORY_PROCESSING = """
    +-------------------------------+
    |      DOCUMENT PROCESSING      |
    +-------------------------------+
    |         +---+      +---+      |
    |    +--->| # |--+   | # |<--+  |
    |    |    +---+  |   +---+   |  |
    |    |           +-------+   |  |
    |    |                   v   |  |
    |    |    +---------------+  |  |
    |    |    | # # # # # # # |  |  |
    |    |    | # # # # # # # |  |  |
    |    |    | # # # # # # # |  |  |
    |    |    +---------------+  |  |
    |    |            |          |  |
    |    +------------+----------+  |
    |                               |
    +-------------------------------+
"""

ASCII_FACTORY_COMPLETE = """
    +-------------------------------+
    |      DOCUMENT PROCESSING      |
    +-------------------------------+
    |                               |
    |         +---+      +---+      |
    |         |   |      |   |      |
    |         +---+      +---+      |
    |                               |
    |     +---------------------+   |
    |     |                     |   |
    |     |     PROCESSING      |   |
    |     |     COMPLETE        |   |
    |     |                     |   |
    |     +---------------------+   |
    |              | |              |
    |              v v              |
    |         [DOCUMENTS]           |
    +-------------------------------+
"""

# Globale Variablen
processing_active = False
log_entries = []
process = None
log_file_path = os.path.abspath("log.txt")  # Pfad zur Log-Datei
preview_path = os.path.abspath("preview.png")  # Pfad zum Vorschaubild
current_preview_file = None  # Aktuell vorgeschaute Datei
current_document_name = "Keine Datei ausgewählt"  # Name des aktuellen Dokuments
preview_support = False  # Initialisiere die Variable hier!
debug_mode = True  # Debug-Modus für ausführliche Logs

# Lade die Einstellung für parallele Dokumente aus der .env-Datei
try:
    if env_support:
        num_parallel_docs = int(os.getenv("PARALLEL_DOCS", "1"))
        num_parallel_docs = max(1, min(4, num_parallel_docs))  # Begrenze auf 1-4
    else:
        num_parallel_docs = 1
except:
    num_parallel_docs = 1

# Dokumenten-Status-Tracking
document_statuses = {}  # Speichert Status für jedes Dokument: ID -> {progress, status, title}

# Hilfsfunktion für sicheres Hinzufügen von Text
def safe_add_text(text, **kwargs):
    try:
        return dpg.add_text(text, **kwargs)
    except Exception as e:
        print(f"Fehler beim Hinzufügen von Text: {str(e)}")
        return dpg.add_text(f"Fehler: {str(e)}")

# Verbesserte Fehlerbehandlung für GUI-Operationen
def safe_configure_item(tag, **kwargs):
    try:
        if dpg.does_item_exist(tag):
            dpg.configure_item(tag, **kwargs)
        else:
            if debug_mode:
                print(f"Warnung: Item mit Tag '{tag}' existiert nicht und kann nicht konfiguriert werden.")
    except Exception as e:
        print(f"Fehler beim Konfigurieren von '{tag}': {str(e)}")

# Funktion zum Aktualisieren des GUI-Layouts basierend auf der Anzahl der parallelen Dokumente
def update_gui_layout():
    try:
        # Aktualisiere die Log- und Animationsanzeige
        for i in range(1, 5):  # Maximal 4 parallele Dokumente
            if i <= num_parallel_docs:
                safe_configure_item(f"doc_panel_{i}", show=True)
            else:
                safe_configure_item(f"doc_panel_{i}", show=False)
                
                # Zurücksetzen der Anzeige für nicht verwendete Panels
                safe_configure_item(f"doc_progress_{i}", default_value=0.0)
                if dpg.does_item_exist(f"doc_status_{i}"):
                    dpg.set_value(f"doc_status_{i}", "Ready")
                if dpg.does_item_exist(f"doc_title_{i}"):
                    dpg.set_value(f"doc_title_{i}", "No document")
                if dpg.does_item_exist(f"doc_id_{i}"):
                    dpg.set_value(f"doc_id_{i}", "")
                if dpg.does_item_exist(f"ascii_art_{i}"):
                    dpg.set_value(f"ascii_art_{i}", ASCII_FACTORY_IDLE)
    except Exception as e:
        print(f"Fehler beim Aktualisieren des GUI-Layouts: {str(e)}")

# Funktion zum Aktualisieren der Anzahl der parallelen Dokumente
def update_parallel_docs(sender, app_data):
    global num_parallel_docs
    try:
        # Sichere Konvertierung und Begrenzung
        new_value = int(app_data)
        num_parallel_docs = max(1, min(4, new_value))  # Begrenze auf 1-4
        
        # Aktualisiere die .env-Datei
        try:
            if env_support:
                # Prüfe, ob die Datei existiert
                env_file = find_dotenv()
                if env_file:
                    # Verwende die set_key-Funktion aus dotenv
                    set_key(env_file, "PARALLEL_DOCS", str(num_parallel_docs))
                    log_entries.append(f"Parallel documents set to {num_parallel_docs}")
                else:
                    # Erstelle eine neue .env-Datei
                    with open(".env", "a") as f:
                        f.write(f"\nPARALLEL_DOCS={num_parallel_docs}\n")
                    log_entries.append(f"New .env file created with PARALLEL_DOCS={num_parallel_docs}")
            else:
                log_entries.append("Dotenv support not available, setting will not be saved")
        except Exception as e:
            log_entries.append(f"Error while saving setting: {str(e)}")
        
        # Aktualisiere das GUI-Layout
        update_gui_layout()
        update_log_display()
        
        # Debug-Ausgabe
        print(f"Parallel documents set to {num_parallel_docs}")
    except Exception as e:
        print(f"Error while updating parallel documents: {str(e)}")

# Verbesserte Funktion zum Filtern von Emojis und ANSI-Escape-Sequenzen
def filter_emojis(text):
    if not text:
        return ""
    
    try:
        # Entferne ANSI-Escape-Sequenzen
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text = ansi_escape.sub('', text)
        
        # Ersetze Fortschrittsbalken-Zeichen
        progress_chars = {
            '█': '#',  # Gefüllter Block
            '░': '-',  # Leerer Block
            '|': '|',  # Spinner
            '/': '/',
            '-': '-',
            '\\': '\\'
        }
        
        # Filtere Text
        filtered_text = ""
        i = 0
        while i < len(text):
            char = text[i]
            
            # Behandle Fortschrittsbalken und Spinner
            if char in progress_chars:
                filtered_text += progress_chars[char]
                i += 1
                continue
            
            # Behandle Emojis und andere Zeichen
            if ord(char) < 127:  # ASCII-Zeichen
                filtered_text += char
            else:
                # Spezielle Emoji-Ersetzungen
                if text[i:i+2] == "🤖":
                    filtered_text += "[BOT]"
                    i += 2
                    continue
                elif text[i:i+2] == "✅":
                    filtered_text += "[OK]"
                    i += 2
                    continue
                elif text[i:i+2] == "❌":
                    filtered_text += "[X]"
                    i += 2
                    continue
                elif text[i:i+2] == "⚠️":
                    filtered_text += "[!]"
                    i += 2
                    continue
            i += 1
        
        # Entferne doppelte Leerzeichen
        filtered_text = ' '.join(filtered_text.split())
        
        return filtered_text
    except Exception as e:
        print(f"Error while filtering emojis: {str(e)}")
        return text

# Funktion zum Extrahieren von Dokumenteninformationen aus Logzeilen
def extract_document_info(line):
    try:
        import re
        
        # Search for document ID
        doc_id_match = re.search(r"Document ID[:\s]+(\d+)", line)
        if not doc_id_match:
            doc_id_match = re.search(r"Document[:\s]+(\d+)", line)
            if not doc_id_match:
                doc_id_match = re.search(r"Dokument[:\s]+(\d+)", line)
        
        if doc_id_match:
            doc_id = int(doc_id_match.group(1))
            
            # Search for progress (x/y format)
            progress_match = re.search(r"verarbeitet \((\d+)/(\d+)\)", line)
            if not progress_match:
                progress_match = re.search(r"processed \((\d+)/(\d+)\)", line)
            
            progress = None
            if progress_match:
                current = int(progress_match.group(1))
                total = int(progress_match.group(2))
                progress = current / total
            
            # Search for status
            status = None
            if "Quality assessment" in line or "Qualitätsbewertung" in line:
                status = "Quality Assessment"
            elif "marked as 'Low Quality'" in line or "als 'Low Quality' markiert" in line:
                status = "Marked as Low Quality"
            elif "marked as 'High Quality'" in line or "als 'High Quality' markiert" in line:
                status = "Marked as High Quality"
            elif "Renaming process" in line or "Umbenennungsprozess" in line:
                status = "Renaming"
            elif "Processing completed" in line or "Verarbeitung abgeschlossen" in line:
                status = "Completed"
            elif "verarbeitet" in line or "processed" in line:
                status = "Processing"
            
            # Search for title
            title_match = re.search(r"Title: '([^']+)'|Titel: '([^']+)'", line)
            title = None
            if title_match:
                title = title_match.group(1) or title_match.group(2)
            
            # If we found any information, return it
            if any([progress is not None, status is not None, title is not None]):
                return {
                    "doc_id": doc_id,
                    "progress": progress,
                    "status": status,
                    "title": title
                }
        
        return None
    except Exception as e:
        if debug_mode:
            print(f"Error while extracting document information: {str(e)}")
        return None

# Funktion zum Aktualisieren des Fortschrittsbalkens für ein Dokument
def update_document_progress(doc_id, progress, status=None, title=None):
    try:
        # Save status
        if doc_id not in document_statuses:
            document_statuses[doc_id] = {"progress": 0, "status": "Initializing...", "title": "Unknown"}
        
        if progress is not None:
            document_statuses[doc_id]["progress"] = progress
        if status is not None:
            document_statuses[doc_id]["status"] = status
        if title is not None:
            document_statuses[doc_id]["title"] = title
        
        # Find panel index for this document
        panel_index = None
        for i in range(1, 5):
            if dpg.does_item_exist(f"doc_id_{i}") and dpg.get_value(f"doc_id_{i}") == str(doc_id):
                panel_index = i
                break
        
        # If no panel found, find a free panel
        if panel_index is None:
            for i in range(1, num_parallel_docs + 1):
                if dpg.does_item_exist(f"doc_id_{i}") and (not dpg.get_value(f"doc_id_{i}") or dpg.get_value(f"doc_id_{i}") == ""):
                    panel_index = i
                    dpg.set_value(f"doc_id_{i}", str(doc_id))
                    break
        
        # Update panel if found
        if panel_index is not None:
            safe_configure_item(f"doc_progress_{panel_index}", default_value=document_statuses[doc_id]["progress"])
            if dpg.does_item_exist(f"doc_status_{panel_index}"):
                dpg.set_value(f"doc_status_{panel_index}", document_statuses[doc_id]["status"])
            if dpg.does_item_exist(f"doc_title_{panel_index}"):
                dpg.set_value(f"doc_title_{panel_index}", document_statuses[doc_id]["title"])
            
            # Update ASCII art based on status
            if dpg.does_item_exist(f"ascii_art_{panel_index}"):
                if progress is not None and progress < 1.0:
                    dpg.set_value(f"ascii_art_{panel_index}", ASCII_FACTORY_PROCESSING)
                elif progress is not None and progress >= 1.0:
                    dpg.set_value(f"ascii_art_{panel_index}", ASCII_FACTORY_COMPLETE)
    except Exception as e:
        print(f"Error while updating document progress: {str(e)}")

# Verbesserte Funktion zum Lesen der Prozessausgabe
def read_output():
    try:
        if process and process.poll() is None:
            # Erstelle einen Thread, der kontinuierlich die Ausgabe liest
            def read_stream():
                try:
                    while process and process.poll() is None:
                        try:
                            line = process.stdout.readline()
                            if line:
                                # Filtere problematische Unicode-Zeichen/Emojis
                                clean_line = filter_emojis(line)
                                
                                # Logge bereinigte Prozessausgabe
                                log_entries.append(clean_line.strip())
                                
                                # Extrahiere Dokumenteninformationen
                                try:
                                    info = extract_document_info(clean_line)
                                    if info and "doc_id" in info:
                                        # Aktualisiere Dokumentenstatus
                                        doc_id = info["doc_id"]
                                        progress = info.get("progress")
                                        status = info.get("status")
                                        title = info.get("title")
                                        update_document_progress(doc_id, progress, status, title)
                                except Exception as e:
                                    if debug_mode:
                                        print(f"Error while extracting document information: {str(e)}")
                                
                                # Aktualisiere die GUI regelmäßig, aber nicht zu oft
                                # (zu häufige Updates können die GUI verlangsamen)
                                if len(log_entries) % 5 == 0:  # Alle 5 Zeilen aktualisieren
                                    update_log_display()
                            else:
                                # Keine Ausgabe mehr, kurz warten
                                time.sleep(0.1)
                        except Exception as e:
                            if debug_mode:
                                print(f"Error while reading output: {str(e)}")
                            time.sleep(0.5)  # Warte bei Fehlern etwas länger
                
                    # Prozess beendet
                    if process:
                        # Lese verbleibende Ausgabe
                        remaining_output = process.stdout.read()
                        if remaining_output:
                            lines = remaining_output.splitlines()
                            for line in lines:
                                clean_line = filter_emojis(line)
                                log_entries.append(clean_line.strip())
                        
                        log_entries.append(f"Process ended with exit code: {process.returncode}")
                        
                        # Aktualisiere GUI im Hauptthread
                        dpg.set_value("process_button", "START")
                        dpg.set_value("status_text", "Status: Ready")
                        safe_configure_item("stop_button", enabled=False)
                        
                        # Setze processing_active auf False
                        global processing_active
                        processing_active = False
                        
                        # Finale Aktualisierung der Log-Anzeige
                        update_log_display()
                except Exception as e:
                    print(f"Critical error in read thread: {str(e)}")
            
            # Starte Thread für kontinuierliches Lesen
            read_thread = threading.Thread(target=read_stream, daemon=True)
            read_thread.start()
            
            # Rückgabe des Threads für mögliche spätere Referenz
            return read_thread
        return None
    except Exception as e:
        print(f"Error while starting read thread: {str(e)}")
        return None

# Funktion zum Aktualisieren des Logs
def update_log_display():
    try:
        if dpg.does_item_exist("log_area"):
            log_lines = []
            
            # Kombiniere direkte Prozessausgabe mit Logdatei
            if log_entries:
                # Filtere Emojis aus allen Logeinträgen
                filtered_entries = [entry for entry in log_entries[-30:]]
                log_lines.extend(filtered_entries)
            
            # Beschränke auf maximal 30 Zeilen insgesamt
            if len(log_lines) > 30:
                log_lines = log_lines[-30:]
                
            # Aktualisiere GUI
            log_text = "\n".join(log_lines)
            dpg.set_value("log_area", log_text)
            
            # Scrolle zum Ende
            try:
                dpg.set_y_scroll("log_area", -1.0)
            except Exception as e:
                if debug_mode:
                    print(f"Error while scrolling: {str(e)}")
    except Exception as e:
        print(f"Error while updating log display: {str(e)}")

# Funktion zum Aktualisieren der Systeminfos
def update_system_info():
    if not system_monitoring:
        return
    
    try:
        # CPU-Auslastung
        cpu_percent = psutil.cpu_percent(interval=1)
        if dpg.does_item_exist("cpu_text"):
            dpg.set_value("cpu_text", f"CPU: {cpu_percent:.1f}%")
        
        # RAM-Auslastung
        ram = psutil.virtual_memory()
        ram_used_gb = ram.used / (1024 ** 3)
        ram_total_gb = ram.total / (1024 ** 3)
        if dpg.does_item_exist("ram_text"):
            dpg.set_value("ram_text", f"RAM: {ram_used_gb:.1f} GB / {ram_total_gb:.1f} GB")
        
        # Festplattennutzung
        disk = psutil.disk_usage('/')
        disk_used_gb = disk.used / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)
        if dpg.does_item_exist("disk_text"):
            dpg.set_value("disk_text", f"Disk: {disk_used_gb:.1f} GB / {disk_total_gb:.1f} GB")
    except Exception as e:
        print(f"Error while updating system information: {str(e)}")

# Funktion zum Speichern der Einstellungen
def save_settings():
    if not env_support:
        return
    
    try:
        # Sammle alle Einstellungen
        settings = {}
        for item in dpg.get_all_items():
            if dpg.get_item_alias(item).startswith("setting_"):
                key = dpg.get_item_alias(item)[8:]  # Entferne "setting_" Präfix
                value = dpg.get_value(item)
                
                # Konvertiere Boolean zu "yes"/"no"
                if isinstance(value, bool):
                    value = "yes" if value else "no"
                
                settings[key] = str(value)
        
        # Speichere in .env-Datei
        env_file = find_dotenv()
        if not env_file:
            # Erstelle neue .env-Datei
            with open(".env", "w") as f:
                for key, value in settings.items():
                    f.write(f"{key}={value}\n")
        else:
            # Aktualisiere bestehende .env-Datei
            for key, value in settings.items():
                set_key(env_file, key, value)
        
        log_entries.append("Settings saved")
        update_log_display()
    except Exception as e:
        log_entries.append(f"Error while saving settings: {str(e)}")
        update_log_display()

# Funktion zum Starten/Stoppen der Verarbeitung
def toggle_processing(sender, app_data):
    global processing_active, log_entries, process
    
    try:
        processing_active = not processing_active
        
        if processing_active:
            # Check if script exists
            script_path = os.path.abspath("main.py")
            if not os.path.exists(script_path):
                log_entries.append(f"WARNING: Script {script_path} not found!")
                processing_active = False
                update_log_display()
                return
            
            # Clear old log file
            try:
                if os.path.exists(log_file_path):
                    with open(log_file_path, "w") as f:
                        f.write("")
            except Exception as e:
                log_entries.append(f"Warning: Could not clear log file: {str(e)}")
            
            # Debug info
            if debug_mode:
                log_entries.append(f"DEBUG: Start script: {os.path.abspath(script_path)}")
                log_entries.append(f"DEBUG: Working directory: {os.getcwd()}")
                log_entries.append(f"DEBUG: Parallel documents: {num_parallel_docs}")
                
                # Show environment variables
                log_entries.append("DEBUG: Important environment variables:")
                for key in ["API_URL", "OLLAMA_URL", "MODEL_NAME", "PARALLEL_DOCS"]:
                    log_entries.append(f"  - {key}={os.getenv(key, 'not set')}")
            
            try:
                # Update UI
                dpg.set_value("process_button", "STOP")
                dpg.set_value("status_text", "Status: Active")
                safe_configure_item("stop_button", enabled=True)
                
                # Reset all document panels
                for i in range(1, 5):
                    if dpg.does_item_exist(f"doc_id_{i}"):
                        dpg.set_value(f"doc_id_{i}", "")
                    if dpg.does_item_exist(f"doc_title_{i}"):
                        dpg.set_value(f"doc_title_{i}", "No document")
                    if dpg.does_item_exist(f"doc_status_{i}"):
                        dpg.set_value(f"doc_status_{i}", "Ready")
                    safe_configure_item(f"doc_progress_{i}", default_value=0.0)
                    if dpg.does_item_exist(f"ascii_art_{i}"):
                        dpg.set_value(f"ascii_art_{i}", ASCII_FACTORY_IDLE)
                
                # Start main.py with extended options
                cmd = [sys.executable, script_path, "--no-confirm"]
                
                log_entries.append(f"Start process: {' '.join(cmd)}")
                update_log_display()
                
                # Modified environment with UTF-8 support
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                env["PARALLEL_DOCS"] = str(num_parallel_docs)
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    env=env,
                    errors='replace'
                )
                
                read_thread = read_output()
                if not read_thread:
                    log_entries.append("Error starting read thread!")
                    processing_active = False
                    dpg.set_value("process_button", "START")
                    safe_configure_item("stop_button", enabled=False)
                    update_log_display()
                
            except Exception as e:
                log_entries.append(f"Error starting process: {str(e)}")
                processing_active = False
                dpg.set_value("process_button", "START")
                safe_configure_item("stop_button", enabled=False)
                update_log_display()
        else:
            # End process
            if process and process.poll() is None:
                try:
                    process.terminate()
                    log_entries.append("Process terminated...")
                except Exception as e:
                    log_entries.append(f"Error while terminating process: {str(e)}")
            
            # Update UI
            dpg.set_value("process_button", "START")
            dpg.set_value("status_text", "Status: Ready")
            safe_configure_item("stop_button", enabled=False)
            update_log_display()
    except Exception as e:
        print(f"Critical error in toggle_processing: {str(e)}")
        try:
            dpg.set_value("process_button", "START")
            dpg.set_value("status_text", f"Status: Error - {str(e)}")
            safe_configure_item("stop_button", enabled=False)
            processing_active = False
        except:
            pass

# Funktion zum Protokollieren von Fehlern
def log_error(message, exception=None):
    try:
        with open("error_log.txt", "a") as f:
            f.write("\n-----------------------------------\n")
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
            if exception:
                f.write(f"Exception: {str(exception)}\n")
                import traceback
                f.write(traceback.format_exc())
            f.write("\n-----------------------------------\n")
    except:
        print("Error writing error log file")

# Funktion zum Abrufen der Bildschirmgröße
def get_display_size():
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Verstecke das Hauptfenster
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.destroy()
    return width, height

# Funktion zum Stoppen der Verarbeitung
def stop_processing(sender, app_data):
    global processing_active, process
    try:
        if process and process.poll() is None:
            process.terminate()
            log_entries.append("Process terminated...")
            update_log_display()
            
            # UI aktualisieren
            dpg.set_value("process_button", "START")
            dpg.set_value("status_text", "Status: Ready")
            safe_configure_item("stop_button", enabled=False)
            processing_active = False
    except Exception as e:
        log_entries.append(f"Error while terminating process: {str(e)}")
        update_log_display()

# Hauptprogramm
try:
    # Lade Einstellungen
    settings = {}
    if env_support:
        # Lade alle Umgebungsvariablen
        for key, value in os.environ.items():
            settings[key] = value
        
        # Lade spezifische Einstellungen aus .env
        settings["API_URL"] = os.getenv("API_URL", "http://localhost:8000/api")
        settings["API_TOKEN"] = os.getenv("API_TOKEN", "")
        settings["OLLAMA_URL"] = os.getenv("OLLAMA_URL", "http://localhost:11434")
        settings["OLLAMA_ENDPOINT"] = os.getenv("OLLAMA_ENDPOINT", "/api/generate")
        settings["MODEL_NAME"] = os.getenv("MODEL_NAME", "llama2")
        settings["SECOND_MODEL_NAME"] = os.getenv("SECOND_MODEL_NAME", "")
        settings["THIRD_MODEL_NAME"] = os.getenv("THIRD_MODEL_NAME", "")
        settings["NUM_LLM_MODELS"] = os.getenv("NUM_LLM_MODELS", "1")
        settings["LOW_QUALITY_TAG_ID"] = os.getenv("LOW_QUALITY_TAG_ID", "1")
        settings["HIGH_QUALITY_TAG_ID"] = os.getenv("HIGH_QUALITY_TAG_ID", "2")
        settings["MAX_DOCUMENTS"] = os.getenv("MAX_DOCUMENTS", "10")
        settings["IGNORE_ALREADY_TAGGED"] = os.getenv("IGNORE_ALREADY_TAGGED", "yes")
        settings["CONFIRM_PROCESS"] = os.getenv("CONFIRM_PROCESS", "yes")
        settings["RENAME_DOCUMENTS"] = os.getenv("RENAME_DOCUMENTS", "yes")
    
    # Hauptskript-Pfad
    script_path = "main.py"
    
    # Bestimme optimale 16:9 Fenstergröße
    width, height = get_display_size()
    
    # Stelle sicher, dass es immer ein genaues 16:9 Verhältnis hat
    height = int(width * 9/16)
    
    print(f"Using 16:9 window size: {width}x{height}")
    
    # DearPyGui initialisieren
    print("Creating GUI...")
    dpg.create_context()
    
    # Berechne die Spaltenbreiten proportional zur Gesamtbreite
    left_col_width = int(width * 0.20)      # 20% der Breite
    middle_col_width = int(width * 0.30)    # 30% der Breite
    right_col_width = int(width * 0.50)     # 50% der Breite
    content_height = height - 50            # Berücksichtigt Titelleiste
    
    with dpg.window(label="DocumentAI", tag="main_window", width=width, height=height):
        with dpg.tab_bar():
            # Tab: Verarbeitung
            with dpg.tab(label="Processing"):
                with dpg.group(horizontal=True):
                    # Linke Seite - Status
                    with dpg.child_window(width=left_col_width, height=content_height):
                        safe_add_text("SYSTEM STATUS", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        # Status
                        safe_add_text("Status: Ready", tag="status_text")
                        
                        # System-Info
                        if system_monitoring:
                            safe_add_text("SYSTEM INFO", color=[255, 255, 0])
                            dpg.add_separator()
                            safe_add_text("CPU: 0%", tag="cpu_text")
                            safe_add_text("RAM: 0 GB / 0 GB", tag="ram_text")
                            safe_add_text("Disk: 0 GB / 0 GB", tag="disk_text")
                        
                        # Diagnose-Bereich
                        safe_add_text("DIAGNOSTICS", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        # Direkter Aufruf
                        safe_add_text("Script Path:")
                        dpg.add_input_text(
                            default_value=script_path,
                            tag="script_path_input",
                            width=left_col_width-20
                        )
                        
                        # Argumente
                        dpg.add_text("Arguments:")
                        dpg.add_input_text(
                            default_value="--no-confirm",
                            tag="script_args_input",
                            width=left_col_width-20
                        )
                        
                        # Debug-Modus Checkbox
                        dpg.add_checkbox(
                            label="Debug Mode",
                            default_value=debug_mode,
                            callback=lambda sender, data: globals().update(debug_mode=data)
                        )
                    
                    # Mittlerer Teil - Verarbeitung & Log
                    with dpg.child_window(width=middle_col_width, height=content_height):
                        # Überschrift
                        safe_add_text("DOCUMENT PROCESSING", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        # Buttons in einer Gruppe
                        with dpg.group(horizontal=True):
                            # Start Button
                            dpg.add_button(
                                label="START", 
                                callback=toggle_processing,
                                width=middle_col_width//2-15, 
                                height=60, 
                                tag="process_button"
                            )
                            
                            # Stop Button - separat hinzugefügt
                            dpg.add_button(
                                label="STOPP", 
                                callback=stop_processing,
                                width=middle_col_width//2-15, 
                                height=60, 
                                tag="stop_button",
                                enabled=False  # Standardmäßig deaktiviert
                            )
                        
                        # Log-Bereich
                        safe_add_text("LOG", color=[255, 255, 0])
                        dpg.add_separator()
                        dpg.add_input_text(
                            multiline=True, 
                            readonly=True, 
                            width=middle_col_width-20, 
                            height=content_height-150, 
                            tag="log_area"
                        )
                    
                    # Rechter Teil - Dokumentenpanels statt einer einzelnen ASCII-Art
                    with dpg.child_window(width=right_col_width, height=content_height):
                        safe_add_text("DOCUMENT PROCESSING", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        # Slider für parallele Dokumente
                        dpg.add_slider_int(
                            label="Parallel documents", 
                            min_value=1, 
                            max_value=4, 
                            default_value=num_parallel_docs,
                            callback=update_parallel_docs,
                            width=right_col_width-40,
                            tag="parallel_docs_slider"
                        )
                        
                        dpg.add_separator()
                        
                        # Erstelle Panels für jedes parallele Dokument
                        panel_height = (content_height - 100) // 4  # Höhe pro Panel
                        
                        for i in range(1, 5):  # Maximal 4 parallele Dokumente
                            with dpg.collapsing_header(
                                label=f"Document #{i}", 
                                default_open=True,
                                tag=f"doc_panel_{i}",
                                show=(i <= num_parallel_docs)
                            ):
                                # Verstecktes Feld für Dokument-ID
                                dpg.add_input_text(
                                    default_value="",
                                    tag=f"doc_id_{i}",
                                    show=False
                                )
                                
                                # Titel des Dokuments
                                safe_add_text("Title:", tag=f"doc_title_label_{i}")
                                safe_add_text("No document", tag=f"doc_title_{i}", color=[200, 200, 200])
                                
                                # Fortschrittsbalken
                                dpg.add_progress_bar(
                                    default_value=0.0,
                                    overlay="0%",
                                    width=right_col_width-40,
                                    height=20,
                                    tag=f"doc_progress_{i}"
                                )
                                
                                # Status
                                safe_add_text("Status:", tag=f"doc_status_label_{i}")
                                safe_add_text("Ready", tag=f"doc_status_{i}", color=[200, 200, 200])
                                
                                # ASCII-Art für dieses Dokument
                                dpg.add_text(ASCII_FACTORY_IDLE, tag=f"ascii_art_{i}", wrap=0)
                                
                                dpg.add_separator()
            
            # Tab: Einstellungen
            with dpg.tab(label="Settings"):
                with dpg.child_window(width=width-20, height=content_height, horizontal_scrollbar=True):
                    if env_support:
                        input_width = width - 40
                        
                        with dpg.collapsing_header(label="API SETTINGS", default_open=True):
                            dpg.add_separator()
                            
                            # API URL
                            safe_add_text("API URL:")
                            dpg.add_input_text(
                                default_value=settings["API_URL"],
                                tag="setting_API_URL",
                                width=input_width
                            )
                            
                            safe_add_text("API Token:")
                            dpg.add_input_text(
                                default_value=settings["API_TOKEN"],
                                tag="setting_API_TOKEN",
                                password=True,
                                width=input_width
                            )
                        
                        with dpg.collapsing_header(label="OLLAMA SETTINGS", default_open=True):
                            dpg.add_separator()
                            
                            safe_add_text("Ollama URL:")
                            dpg.add_input_text(
                                default_value=settings["OLLAMA_URL"],
                                tag="setting_OLLAMA_URL",
                                width=input_width
                            )
                            
                            safe_add_text("Ollama Endpoint:")
                            dpg.add_input_text(
                                default_value=settings["OLLAMA_ENDPOINT"],
                                tag="setting_OLLAMA_ENDPOINT",
                                width=input_width
                            )
                        
                        with dpg.collapsing_header(label="MODEL SETTINGS", default_open=True):
                            dpg.add_separator()
                            
                            safe_add_text("Primary model:")
                            dpg.add_input_text(
                                default_value=settings["MODEL_NAME"],
                                tag="setting_MODEL_NAME",
                                width=input_width
                            )
                            
                            safe_add_text("Secondary model:")
                            dpg.add_input_text(
                                default_value=settings["SECOND_MODEL_NAME"],
                                tag="setting_SECOND_MODEL_NAME",
                                width=input_width
                            )
                            
                            safe_add_text("Tertiary model:")
                            dpg.add_input_text(
                                default_value=settings["THIRD_MODEL_NAME"],
                                tag="setting_THIRD_MODEL_NAME",
                                width=input_width
                            )
                            
                            safe_add_text("Number of models to use:")
                            dpg.add_slider_int(
                                default_value=int(settings["NUM_LLM_MODELS"]),
                                min_value=1,
                                max_value=3,
                                tag="setting_NUM_LLM_MODELS",
                                width=input_width
                            )
                        
                        with dpg.collapsing_header(label="TAG SETTINGS", default_open=True):
                            dpg.add_separator()
                            
                            safe_add_text("Tag ID for low quality:")
                            dpg.add_input_text(
                                default_value=settings["LOW_QUALITY_TAG_ID"],
                                tag="setting_LOW_QUALITY_TAG_ID",
                                width=input_width
                            )
                            
                            safe_add_text("Tag ID for high quality:")
                            dpg.add_input_text(
                                default_value=settings["HIGH_QUALITY_TAG_ID"],
                                tag="setting_HIGH_QUALITY_TAG_ID",
                                width=input_width
                            )
                        
                        with dpg.collapsing_header(label="PROCESS SETTINGS", default_open=True):
                            dpg.add_separator()
                            
                            safe_add_text("Maximum documents:")
                            dpg.add_input_text(
                                default_value=settings["MAX_DOCUMENTS"],
                                tag="setting_MAX_DOCUMENTS",
                                width=input_width
                            )
                            
                            dpg.add_checkbox(
                                label="Ignore already tagged documents",
                                default_value=settings["IGNORE_ALREADY_TAGGED"].lower() == "yes",
                                tag="setting_IGNORE_ALREADY_TAGGED"
                            )
                            
                            dpg.add_checkbox(
                                label="Confirm processing",
                                default_value=settings["CONFIRM_PROCESS"].lower() == "yes",
                                tag="setting_CONFIRM_PROCESS"
                            )
                            
                            dpg.add_checkbox(
                                label="Automatically rename documents",
                                default_value=settings["RENAME_DOCUMENTS"].lower() == "yes",
                                tag="setting_RENAME_DOCUMENTS"
                            )
                        
                        with dpg.collapsing_header(label="LOGGING SETTINGS", default_open=True):
                            dpg.add_separator()
                            
                            safe_add_text("Log level:")
                            dpg.add_combo(
                                items=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                default_value=settings["LOG_LEVEL"],
                                tag="setting_LOG_LEVEL",
                                width=input_width
                            )
                        
                        with dpg.collapsing_header(label="PATH SETTINGS", default_open=True):
                            dpg.add_separator()
                            
                            safe_add_text("Script path:")
                            dpg.add_input_text(
                                default_value=settings.get("SCRIPT_PATH", os.path.abspath("")),
                                tag="setting_SCRIPT_PATH",
                                width=input_width
                            )
                            
                            safe_add_text("Log path:")
                            dpg.add_input_text(
                                default_value=settings.get("LOG_PATH", os.path.abspath("log.txt")),
                                tag="setting_LOG_PATH",
                                width=input_width
                            )
                            
                            safe_add_text("Preview path:")
                            dpg.add_input_text(
                                default_value=settings.get("PREVIEW_PATH", os.path.abspath("preview.png")),
                                tag="setting_PREVIEW_PATH",
                                width=input_width
                            )
                        
                        # Speichern-Button
                        dpg.add_spacer(height=20)
                        dpg.add_button(
                            label="SAVE ALL SETTINGS",
                            callback=save_settings,
                            width=input_width,
                            height=60
                        )
                    else:
                        safe_add_text("Settings not available.\nPython-dotenv not installed.")
            
            # Tab: About
            with dpg.tab(label="About"):
                with dpg.child_window(width=width-20, height=content_height):
                    safe_add_text("DocumentAI System", color=[255, 255, 0], size=40)
                    dpg.add_separator()
                    dpg.add_spacer(height=20)
                    safe_add_text(
                        "Version: 1.0\n\n"
                        "This program processes documents using AI.\n\n"
                        "© 2025 Banthex and this Friend the stupid AI",
                        size=30
                    )
    
    # Initial-Logs
    log_entries.append("System started")
    log_entries.append("Ready for document processing")
    if not os.path.exists(script_path):
        log_entries.append(f"WARNING: Script {script_path} not found!")
    update_log_display()
    
    # Erstelle viewport (16:9 Größe)
    print("Creating Viewport...")
    dpg.create_viewport(title="DocumentAI", width=width, height=height)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    
    # Hauptschleife
    print("Starting main loop...")
    last_update = 0
    last_log_check = 0
    while dpg.is_dearpygui_running():
        # Frame rendern
        dpg.render_dearpygui_frame()
        
        current_time = time.time()
        
        # System-Info aktualisieren (alle 2 Sekunden)
        if current_time - last_update > 2:
            if system_monitoring:
                update_system_info()
            last_update = current_time
        
        # Log-Datei prüfen (alle 0.5 Sekunden)
        if current_time - last_log_check > 0.5:
            update_log_display()
            last_log_check = current_time
        
        # Prüfe, ob Prozess noch läuft
        if processing_active and process and process.poll() is not None:
            # Prozess ist beendet
            exit_code = process.poll()
            log_entries.append(f"Process ended with exit code: {exit_code}")
            
            # Versuche, Fehlerausgabe zu lesen, falls vorhanden
            if exit_code != 0:
                log_entries.append("Process ended with error!")
                # Füge weitere Diagnostik hinzu
                try:
                    # Prüfe, ob Python-Fehler in der Log-Datei sind
                    if os.path.exists(log_file_path):
                        with open(log_file_path, "r") as f:
                            log_content = f.read()
                        
                        if "Traceback" in log_content:
                            log_entries.append("Python error found, see log file")
                except:
                    pass
            
            process = None
            processing_active = False
            dpg.set_value("process_button", "START")
            dpg.set_value("status_text", "Status: Ready")
            update_log_display()
    
    # Aufräumen
    print("Ending program...")
    # Beende laufende Prozesse
    if process and process.poll() is None:
        try:
            process.terminate()
            print("Process ended")
        except:
            print("Could not end process")
    
    dpg.destroy_context()
    
except Exception as e:
    log_error("Critical error in main program", e)
    print("\nPlease open the file error_log.txt for details on the error")
    # Halte Konsolenfenster offen für Fehlerbericht
    input("\nPress Enter to end...")

print("Program ended.")

# Alternative Methode zum Aktualisieren der .env-Datei
def update_env_file(key, value):
    try:
        # Lese die aktuelle .env-Datei
        env_content = ""
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                env_content = f.read()
        
        # Prüfe, ob der Schlüssel bereits existiert
        import re
        if re.search(f"^{key}=.*$", env_content, re.MULTILINE):
            # Ersetze den vorhandenen Wert
            env_content = re.sub(f"^{key}=.*$", f"{key}={value}", env_content, flags=re.MULTILINE)
        else:
            # Füge einen neuen Schlüssel hinzu
            env_content += f"\n{key}={value}\n"
        
        # Schreibe die aktualisierte Datei
        with open(".env", "w") as f:
            f.write(env_content)
        
        return True
    except Exception as e:
        print(f"Error while updating .env file: {e}")
        return False

# Stelle sicher, dass der Slider den korrekten Wert anzeigt
try:
    if dpg.does_item_exist("parallel_docs_slider"):
        dpg.set_value("parallel_docs_slider", num_parallel_docs)
except Exception as e:
    print(f"Error setting slider value: {str(e)}")

# Timer für regelmäßige Updates
def update_timer_callback(sender, app_data):
    update_system_info()

dpg.create_timer(callback=update_timer_callback, time=1.0)
