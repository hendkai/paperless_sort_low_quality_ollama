import sys
import os
import traceback
import time
import subprocess
from datetime import datetime

print("Starte DokumentenKI GUI...")

# Hilfsfunktionen für Fehlerprotokollierung
def log_error(message, exception=None):
    with open("error_log.txt", "w") as f:
        f.write(f"{message}\n")
        if exception:
            f.write(f"Exception: {str(exception)}\n")
            f.write(traceback.format_exc())
    
    print(f"FEHLER: {message}")
    if exception:
        print(f"Exception: {str(exception)}")

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
    
    # Globale Variablen
    processing_active = False
    log_entries = []
    process = None
    log_file_path = os.path.abspath("log.txt")  # Pfad zur Log-Datei
    
    # Hauptskript-Pfad
    script_path = "main.py"
    
    # Debug-Modus für ausführliche Logs
    debug_mode = True
    
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
    
    # Verbesserte Prozesssteuerung mit Diagnostik und Unicode-Unterstützung
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
                
                # UI aktualisieren
                dpg.configure_item("process_button", label="STOPP")
                dpg.configure_item("status_text", default_value="Status: Aktiv")
                
                # Beginne mit dem Lesen der Ausgabe
                def read_output():
                    while process and process.poll() is None:
                        try:
                            line = process.stdout.readline()
                            if line:
                                # Versuche Unicode-Zeichen zu ersetzen, falls nicht darstellbar
                                try:
                                    clean_line = line.encode('cp1252', errors='replace').decode('cp1252')
                                except:
                                    # Wenn alles fehlschlägt, entferne problematische Zeichen
                                    clean_line = ''.join(c if ord(c) < 128 else '?' for c in line)
                                
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
                dpg.configure_item("process_button", label="START")
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
            dpg.configure_item("process_button", label="START")
            dpg.configure_item("status_text", default_value="Status: Bereit")
            update_log_display()
    
    # Aktualisiere Log-Anzeige mit Priorität auf Ausgabe und Direktanzeige
    def update_log_display():
        if dpg.does_item_exist("log_area"):
            log_lines = []
            
            # Kombiniere direkte Prozessausgabe mit Logdatei
            # Zeige zuerst die internen Logs (z.B. Debug-Infos)
            if log_entries:
                log_lines.extend(log_entries[-15:])
            
            # Dann versuche, die tatsächliche Logdatei zu lesen
            try:
                if os.path.exists(log_file_path):
                    with open(log_file_path, "r") as f:
                        file_lines = f.readlines()
                        
                    if file_lines:
                        # Füge bis zu 15 Zeilen aus der Datei hinzu
                        file_recent = file_lines[-15:] if len(file_lines) > 15 else file_lines
                        log_lines.extend([line.strip() for line in file_recent])
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
    
    # DearPyGui initialisieren
    print("Erstelle GUI...")
    dpg.create_context()
    
    # Hauptfenster definieren
    with dpg.window(label="DokumentenKI", tag="main_window", width=800, height=600):
        with dpg.tab_bar():
            # Tab: Verarbeitung
            with dpg.tab(label="Verarbeitung"):
                with dpg.group(horizontal=True):
                    # Linke Seite - Status
                    with dpg.child_window(width=250, height=550):
                        dpg.add_text("SYSTEM STATUS", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        # Status
                        dpg.add_text("Status: Bereit", tag="status_text")
                        
                        # System-Info
                        if system_monitoring:
                            dpg.add_text("SYSTEM-INFO", color=[255, 255, 0])
                            dpg.add_separator()
                            dpg.add_text("CPU: 0%\nRAM: 0%", tag="system_info")
                        
                        # Diagnose-Bereich
                        dpg.add_text("DIAGNOSE", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        # Direkter Aufruf
                        dpg.add_text("Skript-Pfad:")
                        dpg.add_input_text(
                            default_value=script_path,
                            tag="script_path_input",
                            width=230
                        )
                        
                        # Argumente
                        dpg.add_text("Argumente:")
                        dpg.add_input_text(
                            default_value="--no-confirm",
                            tag="script_args_input",
                            width=230
                        )
                        
                        # Debug-Modus Checkbox
                        dpg.add_checkbox(
                            label="Debug-Modus",
                            default_value=debug_mode,
                            callback=lambda sender, data: globals().update(debug_mode=data)
                        )
                    
                    # Rechte Seite - Verarbeitung & Log
                    with dpg.child_window(width=550, height=550):
                        # Überschrift
                        dpg.add_text("DOKUMENTENVERARBEITUNG", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        # Start/Stop Button
                        dpg.add_button(
                            label="START", 
                            callback=toggle_processing,
                            width=530, 
                            height=40, 
                            tag="process_button"
                        )
                        
                        # Log-Bereich
                        dpg.add_text("LOG", color=[255, 255, 0])
                        dpg.add_separator()
                        dpg.add_input_text(
                            multiline=True, 
                            readonly=True, 
                            width=530, 
                            height=450, 
                            tag="log_area"
                        )
                        
            # Tab: Einstellungen
            with dpg.tab(label="Einstellungen"):
                if env_support:
                    with dpg.child_window(width=780, height=550):
                        # Scrollbarer Bereich für alle Einstellungen
                        
                        # 1. API-Einstellungen
                        dpg.add_text("PAPERLESS-NGX API EINSTELLUNGEN", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        # API URL
                        dpg.add_text("API URL:")
                        dpg.add_input_text(
                            default_value=settings["API_URL"],
                            tag="setting_API_URL",
                            width=760
                        )
                        
                        # API Token
                        dpg.add_text("API Token:")
                        dpg.add_input_text(
                            default_value=settings["API_TOKEN"],
                            tag="setting_API_TOKEN",
                            password=True,
                            width=760
                        )
                        
                        dpg.add_spacer(height=10)
                        
                        # 2. Ollama-Einstellungen
                        dpg.add_text("OLLAMA EINSTELLUNGEN", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        dpg.add_text("Ollama URL:")
                        dpg.add_input_text(
                            default_value=settings["OLLAMA_URL"],
                            tag="setting_OLLAMA_URL",
                            width=760
                        )
                        
                        dpg.add_text("Ollama Endpoint:")
                        dpg.add_input_text(
                            default_value=settings["OLLAMA_ENDPOINT"],
                            tag="setting_OLLAMA_ENDPOINT",
                            width=760
                        )
                        
                        dpg.add_spacer(height=10)
                        
                        # 3. Modell-Einstellungen
                        dpg.add_text("KI-MODELL EINSTELLUNGEN", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        dpg.add_text("Primäres Modell:")
                        dpg.add_input_text(
                            default_value=settings["MODEL_NAME"],
                            tag="setting_MODEL_NAME",
                            width=760
                        )
                        
                        dpg.add_text("Sekundäres Modell:")
                        dpg.add_input_text(
                            default_value=settings["SECOND_MODEL_NAME"],
                            tag="setting_SECOND_MODEL_NAME",
                            width=760
                        )
                        
                        dpg.add_text("Tertiäres Modell:")
                        dpg.add_input_text(
                            default_value=settings["THIRD_MODEL_NAME"],
                            tag="setting_THIRD_MODEL_NAME",
                            width=760
                        )
                        
                        dpg.add_text("Anzahl verwendeter LLM-Modelle:")
                        dpg.add_slider_int(
                            default_value=int(settings["NUM_LLM_MODELS"]),
                            min_value=1,
                            max_value=3,
                            tag="setting_NUM_LLM_MODELS",
                            width=760
                        )
                        
                        dpg.add_spacer(height=10)
                        
                        # 4. Tag-Einstellungen
                        dpg.add_text("TAG EINSTELLUNGEN", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        dpg.add_text("ID für Dokumente niedriger Qualität:")
                        dpg.add_input_int(
                            default_value=int(settings["LOW_QUALITY_TAG_ID"]),
                            tag="setting_LOW_QUALITY_TAG_ID",
                            width=760
                        )
                        
                        dpg.add_text("ID für Dokumente hoher Qualität:")
                        dpg.add_input_int(
                            default_value=int(settings["HIGH_QUALITY_TAG_ID"]),
                            tag="setting_HIGH_QUALITY_TAG_ID",
                            width=760
                        )
                        
                        dpg.add_spacer(height=10)
                        
                        # 5. Prozesseinstellungen
                        dpg.add_text("PROZESS EINSTELLUNGEN", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        dpg.add_text("Maximale Anzahl zu verarbeitender Dokumente (0 = unbegrenzt):")
                        dpg.add_input_int(
                            default_value=int(settings["MAX_DOCUMENTS"]),
                            tag="setting_MAX_DOCUMENTS",
                            width=760
                        )
                        
                        # Boolean-Einstellungen
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
                            label="Dokumente umbenennen basierend auf Inhalt",
                            default_value=settings["RENAME_DOCUMENTS"].lower() == "yes",
                            tag="setting_RENAME_DOCUMENTS"
                        )
                        
                        dpg.add_spacer(height=10)
                        
                        # 6. Logging-Einstellungen
                        dpg.add_text("LOGGING EINSTELLUNGEN", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        dpg.add_text("Log-Level:")
                        dpg.add_combo(
                            items=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                            default_value=settings["LOG_LEVEL"],
                            tag="setting_LOG_LEVEL",
                            width=760
                        )
                        
                        dpg.add_spacer(height=10)
                        
                        # 7. Pfad-Einstellungen
                        dpg.add_text("PFAD EINSTELLUNGEN", color=[255, 255, 0])
                        dpg.add_separator()
                        
                        dpg.add_text("Skript-Pfad:")
                        dpg.add_input_text(
                            default_value=settings["SCRIPT_PATH"],
                            tag="setting_SCRIPT_PATH",
                            width=760
                        )
                        
                        dpg.add_text("Log-Pfad:")
                        dpg.add_input_text(
                            default_value=settings["LOG_PATH"],
                            tag="setting_LOG_PATH",
                            width=760
                        )
                        
                        dpg.add_text("Vorschau-Pfad:")
                        dpg.add_input_text(
                            default_value=settings["PREVIEW_PATH"],
                            tag="setting_PREVIEW_PATH",
                            width=760
                        )
                        
                        dpg.add_spacer(height=20)
                        
                        # Speichern-Button
                        dpg.add_button(
                            label="ALLE EINSTELLUNGEN SPEICHERN",
                            callback=save_settings,
                            width=760,
                            height=40
                        )
                else:
                    dpg.add_text("Einstellungen nicht verfügbar.\nPython-dotenv nicht installiert.")
                    
            # Tab: Über
            with dpg.tab(label="Über"):
                dpg.add_text("DokumentenKI System")
                dpg.add_separator()
                dpg.add_text(
                    "Version: 1.0\n"
                    "Dieses Programm verarbeitet Dokumente mit KI.\n\n"
                    "© 2023 Cybersecurity Systems"
                )
    
    # Initial-Logs
    log_entries.append(f"System gestartet")
    log_entries.append(f"Bereit für Dokumentenverarbeitung")
    if not os.path.exists(script_path):
        log_entries.append(f"WARNUNG: Skript {script_path} nicht gefunden!")
    update_log_display()
    
    # Erstelle viewport
    print("Erstelle Viewport...")
    dpg.create_viewport(title="DokumentenKI", width=800, height=600)
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
            dpg.configure_item("process_button", label="START")
            dpg.configure_item("status_text", default_value="Status: Bereit")
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
