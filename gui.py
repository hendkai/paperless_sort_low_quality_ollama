import sys
import os
import traceback
import time
import subprocess
from datetime import datetime
import requests

print("Starte DokumentenKI GUI...")

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

# Hilfsfunktionen für Fehlerprotokollierung
def log_error(message, exception=None):
    try:
        with open("error_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
            if exception:
                f.write(f"Exception: {str(exception)}\n")
                f.write(traceback.format_exc())
                f.write("\n-----------------------------------\n")
    except:
        pass  # Stiller Fehler, wenn auch das Loggen fehlschlägt
    
    print(f"FEHLER: {message}")
    if exception:
        print(f"Exception: {str(exception)}")

# Verbesserte PIL-Erkennung und Import
def setup_pillow():
    global preview_support
    
    try:
        # Versuche direkt zu importieren
        from PIL import Image
        
        # Teste, ob PIL tatsächlich funktioniert, indem ein leeres Bild erstellt wird
        test_img = Image.new('RGB', (10, 10), color='red')
        # Wenn es bis hierhin klappt, ist PIL funktionsfähig
        
        preview_support = True
        print("✅ PIL (Pillow) erfolgreich erkannt und getestet.")
        return True
    except ImportError as e:
        preview_support = False
        print(f"❌ PIL ImportError: {e}")
        print("PIL nicht installiert, versuche Installation...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pillow"], 
                          check=True, capture_output=True)
            
            # Nach Installation erneut versuchen
            from PIL import Image
            preview_support = True
            print("✅ PIL erfolgreich installiert!")
            return True
        except Exception as e:
            log_error(f"Konnte PIL nicht installieren: {e}", e)
            preview_support = False
            return False
    except Exception as e:
        # Andere Fehler beim Import oder bei der Verwendung von PIL
        log_error(f"Fehler bei PIL-Setup: {e}", e)
        preview_support = False
        return False

# Angepasste Anzeigegröße mit 16:9 Seitenverhältnis
def get_display_size():
    try:
        # Versuche, Bildschirmgröße zu ermitteln
        if 'ctypes' in sys.modules or True:
            import ctypes
            user32 = ctypes.windll.user32
            screen_width = user32.GetSystemMetrics(0)
            screen_height = user32.GetSystemMetrics(1)
            
            # Gib 85% der verfügbaren Bildschirmgröße als Ausgangswert
            avail_width = int(screen_width * 0.85)
            avail_height = int(screen_height * 0.85)
            
            # Berechne die optimale 16:9 Größe innerhalb der verfügbaren Fläche
            if avail_width / avail_height > 16/9:
                # Wenn der Bildschirm breiter als 16:9 ist, höhenbegrenzt
                height = avail_height
                width = int(height * 16/9)
            else:
                # Wenn der Bildschirm schmaler als 16:9 ist, breitenbegrenzt
                width = avail_width
                height = int(width * 9/16)
            
            print(f"Optimale 16:9 Größe: {width}x{height}")
            return width, height
    except Exception as e:
        print(f"Fehler bei Bildschirmgrößenermittlung: {str(e)}")
    
    # Fallback auf Standard 16:9 Größe
    return 1600, 900  # 16:9 Standardgröße

# Verbesserte Funktion zum Filtern von Emoji und Sonderzeichen
def filter_emojis(text):
    if not text:
        return text
        
    try:
        # Ersetze bekannte Emojis mit lesbarem Text
        text_replacements = {
            '🤖': '[ROBOT]',
            '✅': '[OK]',
            '❌': '[ERROR]',
            '⚠️': '[WARNING]',
            '🔄': '[RELOAD]',
            '🔍': '[SEARCH]',
            '📄': '[DOC]',
            '⏳': '[WAIT]'
        }
        
        # Ersetze bekannte Fortschrittsbalken und ASCII-Art
        progress_patterns = [
            # Fortschrittsbalken-Muster
            (r'\[═+\]', '[==PROGRESS==]'),
            # Spinner-Symbole
            (r'[\\|/-](\s*)$', '.')
        ]
        
        # Wende Emoji-Ersetzungen an
        for emoji, replacement in text_replacements.items():
            if emoji in text:
                text = text.replace(emoji, replacement)
        
        # Wende reguläre Ausdrücke für Fortschrittsbalken an
        import re
        for pattern, replacement in progress_patterns:
            text = re.sub(pattern, replacement, text)
        
        # Allgemeine Unicode-Bereinigung für restliche problematische Zeichen
        result = ""
        for char in text:
            # Grundlegende lateinische Zeichen, Zahlen und gängige Symbole beibehalten
            if ord(char) < 128:
                result += char
            else:
                # Ersetze unbekannte Unicode-Zeichen
                result += '.'
                
        return result
    except Exception as e:
        # Absoluter Fallback - nur ASCII-Zeichen behalten
        return ''.join(c for c in text if ord(c) < 128)

# Sichere Text-Hinzufügungsfunktion 
def safe_add_text(text, **kwargs):
    try:
        # Stelle sicher, dass text ein String ist
        if text is None:
            text = ""
        else:
            text = str(text)
            
        # Stelle sicher, dass color-Parameter korrekt ist, falls vorhanden
        if 'color' in kwargs and kwargs['color'] is not None:
            color = kwargs['color']
            # Überprüfe, ob color eine Liste mit 3 oder 4 Elementen ist
            if not (isinstance(color, list) and (len(color) == 3 or len(color) == 4)):
                # Setze einen Standardwert, wenn das Format ungültig ist
                kwargs['color'] = [255, 255, 255]
                
        # Sichere size-Parameter
        if 'size' in kwargs and kwargs['size'] is not None:
            try:
                kwargs['size'] = int(kwargs['size'])
            except (ValueError, TypeError):
                # Entferne size bei ungültigem Format
                del kwargs['size']
                
        # Teste auf ungültigen tag-Parameter
        if 'tag' in kwargs and dpg.does_item_exist(kwargs['tag']):
            # Wenn der Tag bereits existiert, löschen wir ihn erst
            try:
                dpg.delete_item(kwargs['tag'])
            except:
                # Falls das Löschen fehlschlägt, generieren wir einen neuen Tag
                import uuid
                kwargs['tag'] = f"text_{uuid.uuid4().hex[:8]}"
                
        # Füge den Text sicher hinzu
        return dpg.add_text(text, **kwargs)
    except Exception as e:
        # Fallback: Füge Text ohne spezielle Formatierung hinzu
        try:
            return dpg.add_text(f"Text-Fehler: {str(text)[:20]}...")
        except:
            # Äußerster Fallback
            return None

# Funktion zum Abrufen der Vorschau aus Paperless NGX
def fetch_preview_from_paperless(document_id):
    try:
        # Beispiel-URL für die Vorschau, anpassen je nach API-Dokumentation von Paperless NGX
        preview_url = f"http://your-paperless-ngx-url/api/documents/{document_id}/preview"
        
        # Anfrage an die API senden
        response = requests.get(preview_url, headers={"Authorization": f"Token {API_TOKEN}"})
        
        if response.status_code == 200:
            # Vorschau-Bilddaten erhalten
            image_data = response.content
            
            # Bild aus den Daten erstellen
            from PIL import Image
            from io import BytesIO
            image = Image.open(BytesIO(image_data))
            image.thumbnail((300, 300))  # Vorschaugröße anpassen
            
            # Konvertiere das Bild in ein Format, das DearPyGUI anzeigen kann
            image_data = image.tobytes("raw", "RGB")
            width, height = image.size
            
            # Aktualisiere die Textur
            dpg.set_value("preview_texture", image_data)
            dpg.configure_item("preview_image", width=width, height=height, show=True)
            dpg.set_value("document_name", f"Dokument ID: {document_id}")
        else:
            log_error(f"Fehler beim Abrufen der Vorschau: {response.status_code} {response.text}")
            dpg.set_value("document_name", "Fehler beim Abrufen der Vorschau")
            dpg.configure_item("preview_image", show=False)
    except Exception as e:
        log_error(f"Fehler beim Abrufen der Vorschau: {e}", e)
        dpg.set_value("document_name", "Fehler beim Abrufen der Vorschau")
        dpg.configure_item("preview_image", show=False)

# Verbesserte Fehlerbehandlung für GUI-Operationen
def safe_configure_item(tag, **kwargs):
    try:
        if dpg.does_item_exist(tag):
            dpg.configure_item(tag, **kwargs)
        else:
            print(f"Warnung: Item mit Tag '{tag}' existiert nicht und kann nicht konfiguriert werden.")
    except Exception as e:
        print(f"Fehler beim Konfigurieren von '{tag}': {str(e)}")

# Funktion zum Stoppen der Verarbeitung
def stop_processing():
    global processing_active, process, log_entries
    
    if processing_active:
        try:
            # Beende den laufenden Prozess
            if process:
                process.terminate()
                process = None
            
            processing_active = False
            dpg.set_value("status_text", "Status: Verarbeitung gestoppt")
            
            # UI aktualisieren
            dpg.set_value("process_button", "START")
            safe_configure_item("stop_button", enabled=False)
            
            # Füge Stopp-Meldung zum Log hinzu
            log_entries.append("STOPP: Verarbeitung wurde manuell beendet.")
            update_log_display()
            
            print("Verarbeitung wurde gestoppt.")
        except Exception as e:
            log_error(f"Fehler beim Stoppen der Verarbeitung: {e}", e)
            dpg.set_value("status_text", "Fehler beim Stoppen der Verarbeitung")
            
            # Füge Fehlermeldung zum Log hinzu
            log_entries.append(f"FEHLER: Konnte Verarbeitung nicht stoppen: {str(e)}")
            update_log_display()

# Debugging: Überprüfen Sie, ob Pillow in der richtigen Umgebung installiert ist
def check_pillow_installation():
    try:
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pip", "show", "pillow"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Pillow ist installiert:")
            print(result.stdout)
        else:
            print("Pillow ist nicht installiert oder nicht in der aktuellen Umgebung verfügbar.")
            print(result.stderr)
    except Exception as e:
        print(f"Fehler beim Überprüfen der Pillow-Installation: {e}")

# Rufen Sie die Überprüfung beim Start auf
check_pillow_installation()

# Hauptprogramm mit umfassender Fehlerbehandlung
try:
    # Import der benötigten Bibliotheken
    print("Importiere Bibliotheken...")
    import dearpygui.dearpygui as dpg
    
    # Prüfe, ob python-dotenv installiert ist
    try:
        from dotenv import load_dotenv, find_dotenv, set_key
        env_support = True
        print("Dotenv Unterstützung geladen.")
    except ImportError:
        env_support = False
        print("Python-dotenv nicht gefunden, Einstellungsspeicherung deaktiviert.")
    
    # Versuch, psutil zu importieren
    try:
        import psutil
        system_monitoring = True
        print("System-Monitoring verfügbar.")
    except ImportError:
        system_monitoring = False
        print("System-Monitoring nicht verfügbar.")
    
    # Hauptskript-Pfad
    script_path = "main.py"
    
    # Prüfe, ob main.py existiert
    if not os.path.exists(script_path):
        print(f"WARNUNG: {script_path} nicht gefunden!")
    else:
        print(f"Script gefunden: {os.path.abspath(script_path)}")
    
    # Alle Einstellungen aus .env
    settings = {
        # API-Einstellungen
        "API_URL": "http://192.168.1.222:8000/api",
        "API_TOKEN": "",
        
        # Ollama-Einstellungen
        "OLLAMA_URL": "http://127.0.0.1:11434",
        "OLLAMA_ENDPOINT": "/api/generate",
        
        # Modell-Einstellungen
        "MODEL_NAME": "mixtral",
        "SECOND_MODEL_NAME": "llama3:8b",
        "THIRD_MODEL_NAME": "deepseek-coder:6.7b",
        "NUM_LLM_MODELS": "3",
        
        # Paperless-Tag-Einstellungen
        "LOW_QUALITY_TAG_ID": "91",
        "HIGH_QUALITY_TAG_ID": "92",
        
        # Prozess-Einstellungen
        "MAX_DOCUMENTS": "1000",
        "IGNORE_ALREADY_TAGGED": "yes",
        "CONFIRM_PROCESS": "yes",
        "RENAME_DOCUMENTS": "yes",
        
        # Logging
        "LOG_LEVEL": "INFO",
        
        # Pfade
        "SCRIPT_PATH": "main.py",
        "LOG_PATH": "log.txt",
        "PREVIEW_PATH": "preview.png"
    }
    
    # Lade .env falls vorhanden
    if env_support:
        env_file = find_dotenv()
        if env_file:
            load_dotenv(env_file)
            print(f".env Datei gefunden: {env_file}")
            
            # Lade vorhandene Werte
            for key in settings:
                value = os.getenv(key)
                if value:
                    settings[key] = value
                    
            # Aktualisiere Skriptpfad
            script_path = os.getenv("SCRIPT_PATH", script_path)
        else:
            env_file = ".env"
            print("Keine .env Datei gefunden, werde eine erstellen.")
    
    # Verbesserte Prozesssteuerung mit Diagnostik und Emoji-Filterung
    def toggle_processing(sender, app_data):
        global processing_active, log_entries, process
        
        # Zustand umschalten
        processing_active = not processing_active
        
        if processing_active:
            # Überprüfe, ob Skript existiert
            if not os.path.exists(script_path):
                log_entries.append(f"FEHLER: Skript {script_path} nicht gefunden!")
                processing_active = False
                update_log_display()
                return
            
            # Lösche alte Log-Datei
            try:
                if os.path.exists(log_file_path):
                    with open(log_file_path, "w") as f:
                        f.write("")
            except Exception as e:
                log_entries.append(f"Warnung: Konnte Log-Datei nicht leeren: {str(e)}")
            
            # Debug-Info
            if debug_mode:
                log_entries.append(f"DEBUG: Starte Skript: {os.path.abspath(script_path)}")
                log_entries.append(f"DEBUG: Arbeitsverzeichnis: {os.getcwd()}")
                
                # Zeige Umgebungsvariablen
                log_entries.append("DEBUG: Wichtige Umgebungsvariablen:")
                for key in ["API_URL", "OLLAMA_URL", "MODEL_NAME"]:
                    log_entries.append(f"  - {key}={os.getenv(key, 'nicht gesetzt')}")
            
            try:
                # Beispiel: ID des Dokuments, das verarbeitet wird
                document_id = 83291  # Diese ID sollte dynamisch aus der Verarbeitung stammen
                
                # UI aktualisieren - OHNE configure_item für stop_button
                dpg.set_value("process_button", "STOPP")
                dpg.set_value("status_text", "Status: Aktiv")
                
                # Starte main.py mit erweiterten Optionen
                # Kommandozeilen-Argument für Test-Modi
                cmd = [sys.executable, script_path, "--no-confirm"]
                
                log_entries.append(f"Starte Prozess: {' '.join(cmd)}")
                update_log_display()
                
                # Angepasste Umgebung mit UTF-8 Unterstützung
                env = os.environ.copy()
                # Setze PYTHONIOENCODING auf UTF-8, um Unicode-Fehler zu vermeiden
                env["PYTHONIOENCODING"] = "utf-8"
                
                # Starte Prozess mit vollständiger Umgebung
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    env=env,  # Modifizierte Umgebung mit UTF-8
                    errors='replace'  # Wichtig: Ersetze nicht darstellbare Zeichen
                )
                
                # Beginne mit dem Lesen der Ausgabe
                def read_output():
                    while process and process.poll() is None:
                        try:
                            line = process.stdout.readline()
                            if line:
                                # Filtere problematische Unicode-Zeichen/Emojis
                                clean_line = filter_emojis(line)
                                
                                # Logge bereinigte Prozessausgabe
                                log_entries.append(clean_line.strip())
                                update_log_display()
                        except Exception as e:
                            if debug_mode:
                                log_entries.append(f"Fehler beim Lesen der Ausgabe: {str(e)}")
                            break
                
                # Starte separaten Thread für das Lesen der Ausgabe
                import threading
                threading.Thread(target=read_output, daemon=True).start()
                
            except Exception as e:
                log_entries.append(f"Fehler beim Starten: {str(e)}")
                processing_active = False
                dpg.set_value("process_button", "START")
                update_log_display()
        else:
            # Prozess beenden
            if process and process.poll() is None:
                try:
                    process.terminate()
                    log_entries.append(f"Prozess wird beendet...")
                except Exception as e:
                    log_entries.append(f"Fehler beim Beenden des Prozesses: {str(e)}")
            
            # UI aktualisieren
            dpg.set_value("process_button", "START")
            dpg.set_value("status_text", "Status: Bereit")
            update_log_display()
    
    # Aktualisiere Log-Anzeige mit Emoji-Filterung
    def update_log_display():
        if dpg.does_item_exist("log_area"):
            log_lines = []
            
            # Kombiniere direkte Prozessausgabe mit Logdatei
            # Zeige zuerst die internen Logs (z.B. Debug-Infos)
            if log_entries:
                # Filtere Emojis aus allen Logeinträgen
                filtered_entries = [filter_emojis(entry) for entry in log_entries[-15:]]
                log_lines.extend(filtered_entries)
            
            # Dann versuche, die tatsächliche Logdatei zu lesen
            try:
                if os.path.exists(log_file_path):
                    with open(log_file_path, "r", encoding="utf-8", errors="replace") as f:
                        file_lines = f.readlines()
                        
                    if file_lines:
                        # Füge bis zu 15 Zeilen aus der Datei hinzu
                        file_recent = file_lines[-15:] if len(file_lines) > 15 else file_lines
                        # Filtere Emojis aus allen Logzeilen
                        filtered_lines = [filter_emojis(line.strip()) for line in file_recent]
                        log_lines.extend(filtered_lines)
            except Exception as e:
                if debug_mode:
                    log_lines.append(f"Log-Datei-Fehler: {str(e)}")
            
            # Beschränke auf maximal 30 Zeilen insgesamt
            if len(log_lines) > 30:
                log_lines = log_lines[-30:]
                
            # Aktualisiere GUI
            log_text = "\n".join(log_lines)
            dpg.set_value("log_area", log_text)
            
            # Scrolle zum Ende
            try:
                dpg.set_y_scroll("log_area", -1.0)
            except:
                pass
    
    # Aktualisiere Systeminfo
    def update_system_info():
        if system_monitoring and dpg.does_item_exist("system_info"):
            try:
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory()
                
                # Zeige auch Prozessstatus
                if process and process.poll() is None:
                    try:
                        # Versuche, Prozessinformationen zu erhalten
                        proc_info = psutil.Process(process.pid)
                        proc_cpu = proc_info.cpu_percent(interval=0.1)
                        proc_mem = proc_info.memory_info().rss / (1024 * 1024)  # MB
                        proc_status = f"[PID: {process.pid}]\nCPU: {proc_cpu:.1f}%\nRAM: {proc_mem:.1f} MB"
                    except:
                        proc_status = f"[PID: {process.pid}] Läuft"
                else:
                    proc_status = "Gestoppt"
                
                info_text = f"CPU: {cpu:.1f}%\nRAM: {ram.percent:.1f}%\n\nProzess: {proc_status}"
                dpg.set_value("system_info", info_text)
            except:
                dpg.set_value("system_info", "System-Info nicht verfügbar")
    
    # Speichere alle .env Einstellungen
    def save_settings(sender, app_data):
        if not env_support:
            log_entries.append(f"[{datetime.now().strftime('%H:%M:%S')}] Einstellungen können nicht gespeichert werden (dotenv fehlt)")
            update_log_display()
            return
            
        try:
            # Sammle alle Einstellungswerte aus der UI
            for key in settings:
                if dpg.does_item_exist(f"setting_{key}"):
                    # Bei Checkboxen von Boolean zu Ja/Nein konvertieren
                    if key in ["IGNORE_ALREADY_TAGGED", "CONFIRM_PROCESS", "RENAME_DOCUMENTS"]:
                        value = "yes" if dpg.get_value(f"setting_{key}") else "no"
                    else:
                        value = dpg.get_value(f"setting_{key}")
                    
                    # In .env schreiben
                    set_key(env_file, key, str(value))
                    settings[key] = str(value)
            
            log_entries.append(f"[{datetime.now().strftime('%H:%M:%S')}] Alle Einstellungen gespeichert")
            update_log_display()
        except Exception as e:
            log_entries.append(f"[{datetime.now().strftime('%H:%M:%S')}] Fehler beim Speichern: {str(e)}")
            update_log_display()
    
    # Bestimme optimale 16:9 Fenstergröße
    width, height = get_display_size()
    
    # Stelle sicher, dass es immer ein genaues 16:9 Verhältnis hat
    # (Rundungsfehler korrigieren)
    height = int(width * 9/16)
    
    print(f"Verwende 16:9 Fenstergröße: {width}x{height}")
    
    # DearPyGui initialisieren
    print("Erstelle GUI...")
    dpg.create_context()
    
    # Berechne die Spaltenbreiten proportional zur Gesamtbreite
    left_col_width = int(width * 0.20)      # 20% der Breite
    middle_col_width = int(width * 0.30)    # 30% der Breite
    right_col_width = int(width * 0.50)     # 50% der Breite
    content_height = height - 50            # Berücksichtigt Titelleiste
    
    with dpg.window(label="DokumentenKI", tag="main_window", width=width, height=height):
        with dpg.tab_bar():
            # Tab: Verarbeitung
            with dpg.tab(label="Verarbeitung"):
                with dpg.group(horizontal=True):
                    # Linke Seite - Status
                    with dpg.child_window(width=left_col_width, height=content_height):
                        safe_add_text("SYSTEM STATUS", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        # Status
                        safe_add_text("Status: Bereit", tag="status_text")
                        
                        # System-Info
                        if system_monitoring:
                            safe_add_text("SYSTEM-INFO", color=[255, 255, 0])
                            dpg.add_separator()
                            safe_add_text("CPU: 0%\nRAM: 0%", tag="system_info")
                        
                        # Diagnose-Bereich
                        safe_add_text("DIAGNOSE", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        # Direkter Aufruf
                        safe_add_text("Skript-Pfad:")
                        dpg.add_input_text(
                            default_value=script_path,
                            tag="script_path_input",
                            width=left_col_width-20
                        )
                        
                        # Argumente
                        dpg.add_text("Argumente:")
                        dpg.add_input_text(
                            default_value="--no-confirm",
                            tag="script_args_input",
                            width=left_col_width-20
                        )
                        
                        # Debug-Modus Checkbox
                        dpg.add_checkbox(
                            label="Debug-Modus",
                            default_value=debug_mode,
                            callback=lambda sender, data: globals().update(debug_mode=data)
                        )
                    
                    # Mittlerer Teil - Verarbeitung & Log
                    with dpg.child_window(width=middle_col_width, height=content_height):
                        # Überschrift
                        safe_add_text("DOKUMENTENVERARBEITUNG", color=[255, 255, 0])
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
                    
                    # Rechter Teil - Dokumentenvorschau
                    with dpg.child_window(width=right_col_width, height=content_height):
                        safe_add_text("DOKUMENTENVORSCHAU", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        # Dateiname und Info
                        safe_add_text("Keine Datei ausgewählt", tag="document_name", wrap=right_col_width-20)
                        dpg.add_separator()
                        
                        # Vorschaubild-Bereich
                        if preview_support:
                            # Platzhalter für Vorschau
                            safe_add_text("Vorschaubild wird geladen, sobald verfügbar...")
                            
                            # Bildcontainer mit Scrolling
                            with dpg.child_window(width=right_col_width-20, height=content_height-100, horizontal_scrollbar=True):
                                # Hier wird das Bild angezeigt, wenn es verfügbar ist
                                dpg.add_image(
                                    texture_tag="preview_texture", 
                                    tag="preview_image",
                                    show=False
                                )
                        else:
                            safe_add_text("Vorschau nicht verfügbar.\nBitte installiere PIL mit 'pip install pillow'.")
            
            # Tab: Einstellungen
            with dpg.tab(label="Einstellungen"):
                with dpg.child_window(width=width-20, height=content_height, horizontal_scrollbar=True):
                    if env_support:
                        input_width = width - 40
                        
                        with dpg.collapsing_header(label="API EINSTELLUNGEN", default_open=True):
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
                        
                        with dpg.collapsing_header(label="OLLAMA EINSTELLUNGEN", default_open=True):
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
                        
                        with dpg.collapsing_header(label="KI-MODELL EINSTELLUNGEN", default_open=True):
                            dpg.add_separator()
                            
                            safe_add_text("Primäres Modell:")
                            dpg.add_input_text(
                                default_value=settings["MODEL_NAME"],
                                tag="setting_MODEL_NAME",
                                width=input_width
                            )
                            
                            safe_add_text("Sekundäres Modell:")
                            dpg.add_input_text(
                                default_value=settings["SECOND_MODEL_NAME"],
                                tag="setting_SECOND_MODEL_NAME",
                                width=input_width
                            )
                            
                            safe_add_text("Tertiäres Modell:")
                            dpg.add_input_text(
                                default_value=settings["THIRD_MODEL_NAME"],
                                tag="setting_THIRD_MODEL_NAME",
                                width=input_width
                            )
                            
                            safe_add_text("Anzahl zu verwendender Modelle:")
                            dpg.add_slider_int(
                                default_value=int(settings["NUM_LLM_MODELS"]),
                                min_value=1,
                                max_value=3,
                                tag="setting_NUM_LLM_MODELS",
                                width=input_width
                            )
                        
                        with dpg.collapsing_header(label="TAG EINSTELLUNGEN", default_open=True):
                            dpg.add_separator()
                            
                            safe_add_text("Tag ID für niedrige Qualität:")
                            dpg.add_input_text(
                                default_value=settings["LOW_QUALITY_TAG_ID"],
                                tag="setting_LOW_QUALITY_TAG_ID",
                                width=input_width
                            )
                            
                            safe_add_text("Tag ID für hohe Qualität:")
                            dpg.add_input_text(
                                default_value=settings["HIGH_QUALITY_TAG_ID"],
                                tag="setting_HIGH_QUALITY_TAG_ID",
                                width=input_width
                            )
                        
                        with dpg.collapsing_header(label="PROZESS EINSTELLUNGEN", default_open=True):
                            dpg.add_separator()
                            
                            safe_add_text("Maximale Dokumente:")
                            dpg.add_input_text(
                                default_value=settings["MAX_DOCUMENTS"],
                                tag="setting_MAX_DOCUMENTS",
                                width=input_width
                            )
                            
                            dpg.add_checkbox(
                                label="Bereits getaggte Dokumente ignorieren",
                                default_value=settings["IGNORE_ALREADY_TAGGED"].lower() == "yes",
                                tag="setting_IGNORE_ALREADY_TAGGED"
                            )
                            
                            dpg.add_checkbox(
                                label="Verarbeitung bestätigen",
                                default_value=settings["CONFIRM_PROCESS"].lower() == "yes",
                                tag="setting_CONFIRM_PROCESS"
                            )
                            
                            dpg.add_checkbox(
                                label="Dokumente automatisch umbenennen",
                                default_value=settings["RENAME_DOCUMENTS"].lower() == "yes",
                                tag="setting_RENAME_DOCUMENTS"
                            )
                        
                        with dpg.collapsing_header(label="LOGGING EINSTELLUNGEN", default_open=True):
                            dpg.add_separator()
                            
                            safe_add_text("Log-Level:")
                            dpg.add_combo(
                                items=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                default_value=settings["LOG_LEVEL"],
                                tag="setting_LOG_LEVEL",
                                width=input_width
                            )
                        
                        with dpg.collapsing_header(label="PFAD EINSTELLUNGEN", default_open=True):
                            dpg.add_separator()
                            
                            safe_add_text("Skript-Pfad:")
                            dpg.add_input_text(
                                default_value=settings.get("SCRIPT_PATH", os.path.abspath("")),
                                tag="setting_SCRIPT_PATH",
                                width=input_width
                            )
                            
                            safe_add_text("Log-Pfad:")
                            dpg.add_input_text(
                                default_value=settings.get("LOG_PATH", os.path.abspath("log.txt")),
                                tag="setting_LOG_PATH",
                                width=input_width
                            )
                            
                            safe_add_text("Vorschau-Pfad:")
                            dpg.add_input_text(
                                default_value=settings.get("PREVIEW_PATH", os.path.abspath("preview.png")),
                                tag="setting_PREVIEW_PATH",
                                width=input_width
                            )
                        
                        # Speichern-Button
                        dpg.add_spacer(height=20)
                        dpg.add_button(
                            label="ALLE EINSTELLUNGEN SPEICHERN",
                            callback=save_settings,
                            width=input_width,
                            height=60
                        )
                    else:
                        safe_add_text("Einstellungen nicht verfügbar.\nPython-dotenv nicht installiert.")
            
            # Tab: Über
            with dpg.tab(label="Über"):
                with dpg.child_window(width=width-20, height=content_height):
                    safe_add_text("DokumentenKI System", color=[255, 255, 0], size=40)
                    dpg.add_separator()
                    dpg.add_spacer(height=20)
                    safe_add_text(
                        "Version: 1.0\n\n"
                        "Dieses Programm verarbeitet Dokumente mit KI.\n\n"
                        "© 2023 Cybersecurity Systems",
                        size=30
                    )
    
    # Initial-Logs
    log_entries.append(f"System gestartet")
    log_entries.append(f"Bereit für Dokumentenverarbeitung")
    if not os.path.exists(script_path):
        log_entries.append(f"WARNUNG: Skript {script_path} nicht gefunden!")
    update_log_display()
    
    # Erstelle viewport (16:9 Größe)
    print("Erstelle Viewport...")
    dpg.create_viewport(title="DokumentenKI", width=width, height=height)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    
    # Hauptschleife
    print("Starte Hauptschleife...")
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
            log_entries.append(f"Prozess beendet mit Exit-Code: {exit_code}")
            
            # Versuche, Fehlerausgabe zu lesen, falls vorhanden
            if exit_code != 0:
                log_entries.append("Prozess endete mit Fehler!")
                # Füge weitere Diagnostik hinzu
                try:
                    # Prüfe, ob Python-Fehler in der Log-Datei sind
                    if os.path.exists(log_file_path):
                        with open(log_file_path, "r") as f:
                            log_content = f.read()
                        
                        if "Traceback" in log_content:
                            log_entries.append("Python-Fehler gefunden, siehe Logdatei")
                except:
                    pass
            
            process = None
            processing_active = False
            dpg.set_value("process_button", "START")
            dpg.set_value("status_text", "Status: Bereit")
            update_log_display()
    
    # Aufräumen
    print("Beende Programm...")
    # Beende laufende Prozesse
    if process and process.poll() is None:
        try:
            process.terminate()
            print("Prozess beendet")
        except:
            print("Konnte Prozess nicht beenden")
    
    dpg.destroy_context()
    
except Exception as e:
    log_error("Kritischer Fehler im Hauptprogramm", e)
    print("\nBitte öffne die Datei error_log.txt für Details zum Fehler")
    # Halte Konsolenfenster offen für Fehlerbericht
    input("\nDrücke Enter zum Beenden...")

print("Programm beendet.")
