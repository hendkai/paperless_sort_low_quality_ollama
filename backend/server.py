"""
Paperless AI Document Processing Backend
Server-side processing with FastAPI
"""
import os
import threading
import time
import subprocess
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

app = FastAPI(title="Paperless AI Backend")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HISTORY_FILE = "backend/history.json"

# ============== Shared State ==============
@dataclass
class ProcessingState:
    processing: bool = False
    paused: bool = False
    stats: Dict[str, int] = field(default_factory=lambda: {
        "total": 0,
        "processed": 0,
        "high_quality": 0,
        "low_quality": 0,
        "no_consensus": 0,
        "errors": 0,
        "skipped": 0
    })
    current_doc: Optional[Dict[str, Any]] = None
    logs: List[str] = field(default_factory=list)
    llm_responses: Dict[str, str] = field(default_factory=dict)
    documents: List[Dict[str, Any]] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)

state = ProcessingState()
state_lock = threading.Lock()
worker_thread: Optional[threading.Thread] = None
stop_flag = threading.Event()


def load_history():
    """Load history from JSON file"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                data = json.load(f)
                # Ensure it's a list
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"Failed to load history: {e}")
    return []


def save_history():
    """Save history to JSON file"""
    with state_lock:
        data = state.history
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Failed to save history: {e}")


def add_history_entry(doc_id, title, action, reason, details=None, old_title=None, new_title=None):
    """Add entry to history and save"""
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "doc_id": doc_id,
        "title": title,
        "action": action, # "processed", "skipped", "error"
        "reason": reason, # "High Quality", "Empty", "No Consensus"
        "details": details or "",
        "old_title": old_title or "",
        "new_title": new_title or ""
    }
    with state_lock:
        state.history.insert(0, entry) # Newest first
        # Limit in memory to 1000
        if len(state.history) > 1000:
            state.history = state.history[:1000]
    
    # Save (simple sync save for now as volume is low)
    save_history()


def add_log(msg: str):
    """Add a log message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    with state_lock:
        state.logs.append(f"[{timestamp}] {msg}")
        # Keep last 200 logs
        if len(state.logs) > 200:
            state.logs = state.logs[-200:]


# Load history on startup
state.history = load_history()


# ============== Config ==============
API_URL = os.getenv("API_URL", "http://localhost:8000/api")
API_TOKEN = os.getenv("API_TOKEN", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "/v1/chat/completions")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3")
SECOND_MODEL_NAME = os.getenv("SECOND_MODEL_NAME", "")
THIRD_MODEL_NAME = os.getenv("THIRD_MODEL_NAME", "")
LOW_QUALITY_TAG_ID = os.getenv("LOW_QUALITY_TAG_ID", "")
HIGH_QUALITY_TAG_ID = os.getenv("HIGH_QUALITY_TAG_ID", "")
NUM_LLM_MODELS = int(os.getenv("NUM_LLM_MODELS", "3"))
IGNORE_ALREADY_TAGGED = os.getenv("IGNORE_ALREADY_TAGGED", "yes")


# ============== API Helpers ==============
def get_headers():
    return {"Authorization": f"Token {API_TOKEN}"}


def fetch_documents(limit: int = 20) -> List[Dict]:
    """Fetch documents from Paperless-ngx"""
    params = {"page_size": limit}
    
    if IGNORE_ALREADY_TAGGED == "yes":
        tags_to_exclude = []
        if LOW_QUALITY_TAG_ID:
            tags_to_exclude.append(LOW_QUALITY_TAG_ID)
        if HIGH_QUALITY_TAG_ID:
            tags_to_exclude.append(HIGH_QUALITY_TAG_ID)
        if tags_to_exclude:
            params["tags__id__none"] = ",".join(tags_to_exclude)
    
    try:
        resp = requests.get(f"{API_URL}/documents/", headers=get_headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except Exception as e:
        add_log(f"[Error] Failed to fetch documents: {e}")
        return []


def evaluate_content(content: str, model: str) -> Optional[str]:
    """Call LLM to evaluate document quality"""
    prompt = f"""Analyze this document content and classify it as either 'high quality' or 'low quality'.

A high quality document contains useful, important, or valuable information such as:
- Official documents, contracts, invoices
- Personal records, certificates
- Important correspondence

A low quality document contains:
- Junk mail, spam, advertisements
- Duplicates, empty pages
- Irrelevant or outdated content

Document content (first 2000 chars):
{content[:2000]}

Respond with ONLY 'high quality' or 'low quality', nothing else."""

    try:
        # Detect API format based on endpoint
        is_openai_format = "/v1/" in OLLAMA_ENDPOINT

        if is_openai_format:
            # OpenAI-compatible format (LM Studio, etc.)
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 1000  # Higher for reasoning models
            }
        else:
            # Native Ollama API format
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 500  # Higher for reasoning models
                }
            }

        resp = requests.post(
            f"{OLLAMA_URL}{OLLAMA_ENDPOINT}",
            json=payload,
            timeout=120
        )
        resp.raise_for_status()
        data = resp.json()

        # Parse response based on format
        if is_openai_format:
            result = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip().lower()
        else:
            result = data.get("response", "").strip().lower()

        # Clean up result - extract just the classification
        # Handle reasoning models that use [think]...[/think] or similar tags
        import re
        # Remove thinking/reasoning blocks
        result = re.sub(r'\[think\].*?\[/think\]', '', result, flags=re.DOTALL | re.IGNORECASE)
        result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL | re.IGNORECASE)
        result = re.sub(r'<reasoning>.*?</reasoning>', '', result, flags=re.DOTALL | re.IGNORECASE)
        result = result.strip().lower()

        add_log(f"[Debug] Cleaned LLM response: {result[:100]}")

        if "high quality" in result:
            return "high quality"
        elif "low quality" in result:
            return "low quality"
        else:
            add_log(f"[Warning] Unexpected LLM response: {result[:100]}")
            return None
    except Exception as e:
        add_log(f"[Error] LLM call failed ({model}): {e}")
        return None


def generate_title(content: str, model: str) -> Optional[str]:
    """Generate improved title for high-quality document"""
    prompt = f"""Output ONLY a filename, nothing else. No explanations.

Example outputs:
Rechnung_Amazon_2024-01-15
Vertrag_Telekom_2024-03
Brief_Finanzamt_Steuerbescheid

Rules: Max 60 chars, German if content German, Format: Category_Subject_Date

Document excerpt:
{content[:1500]}

Filename:"""

    try:
        # Detect API format based on endpoint
        is_openai_format = "/v1/" in OLLAMA_ENDPOINT

        if is_openai_format:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 4000  # Very high for reasoning models that think extensively
            }
        else:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 4000  # Very high for reasoning models
                }
            }

        resp = requests.post(
            f"{OLLAMA_URL}{OLLAMA_ENDPOINT}",
            json=payload,
            timeout=120
        )
        resp.raise_for_status()
        data = resp.json()

        if is_openai_format:
            result = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        else:
            result = data.get("response", "").strip()

        # Debug: Log raw response before cleaning
        add_log(f"[Debug] Raw title response (first 200 chars): '{result[:200]}'")

        # Remove thinking/reasoning blocks from reasoning models
        import re
        raw_for_fallback = result  # Keep original for fallback extraction

        result = re.sub(r'\[think\].*?\[/think\]', '', result, flags=re.DOTALL | re.IGNORECASE)
        result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL | re.IGNORECASE)
        result = re.sub(r'<reasoning>.*?</reasoning>', '', result, flags=re.DOTALL | re.IGNORECASE)
        # Also handle unclosed thinking tags (model cut off mid-think)
        result = re.sub(r'\[think\].*$', '', result, flags=re.DOTALL | re.IGNORECASE)
        result = re.sub(r'<think>.*$', '', result, flags=re.DOTALL | re.IGNORECASE)

        # Clean up: remove quotes and whitespace
        result = result.strip('"\'').strip()

        # Fallback: Try to extract filename from thinking block if result is empty
        if not result and raw_for_fallback:
            # Look for patterns like "Filename:" or filename patterns in the thinking
            filename_match = re.search(r'(?:filename|title|name):\s*["\']?([A-Za-z0-9äöüÄÖÜß_\-]+(?:_[A-Za-z0-9äöüÄÖÜß_\-]+)*)["\']?', raw_for_fallback, re.IGNORECASE)
            if filename_match:
                result = filename_match.group(1).strip('"\'').strip()
                add_log(f"[Debug] Extracted title from thinking: '{result[:60]}'")
            else:
                # Try to find any underscore-separated pattern that looks like a filename
                fallback_match = re.search(r'\b([A-Z][a-zA-Z0-9äöüÄÖÜß]+_[A-Za-z0-9äöüÄÖÜß_\-]+)\b', raw_for_fallback)
                if fallback_match:
                    result = fallback_match.group(1)
                    add_log(f"[Debug] Found filename pattern in thinking: '{result[:60]}'")

        add_log(f"[Debug] Generated title: '{result[:60] if result else ''}'")
        return result if result else None
    except Exception as e:
        add_log(f"[Error] Title generation failed: {e}")
        return None


def tag_document(doc_id: int, tag_id: int):
    """Add tag to document"""
    try:
        resp = requests.post(
            f"{API_URL}/documents/bulk_edit/",
            headers=get_headers(),
            json={
                "documents": [doc_id],
                "method": "modify_tags",
                "parameters": {"add_tags": [tag_id], "remove_tags": []}
            },
            timeout=30
        )
        resp.raise_for_status()
    except Exception as e:
        add_log(f"[Error] Failed to tag document {doc_id}: {e}")
        raise


def rename_document(doc_id: int, new_title: str):
    """Rename document"""
    import re
    # Clean the title - remove invalid characters
    original_title = new_title
    new_title = re.sub(r'[<>:"/\\|?*]', '', new_title)  # Remove invalid filename chars
    new_title = re.sub(r'\s+', ' ', new_title).strip()  # Normalize whitespace
    new_title = new_title[:128]  # Max length

    if new_title != original_title:
        add_log(f"[Debug] Title cleaned: '{original_title[:50]}' -> '{new_title[:50]}'")

    add_log(f"[Debug] Renaming doc {doc_id} to: '{new_title}'")

    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        resp = requests.patch(
            f"{API_URL}/documents/{doc_id}/",
            headers=headers,
            json={"title": new_title},
            timeout=30
        )
        if resp.status_code != 200:
            add_log(f"[Error] Rename response: {resp.status_code} - {resp.text[:200]}")
        resp.raise_for_status()
    except Exception as e:
        add_log(f"[Error] Failed to rename document {doc_id}: {e}")
        raise


# ============== Processing Loop ==============
def process_documents():
    """Main processing loop - runs in background thread"""
    global state
    
    add_log("[System] 🚀 Processing started")
    
    while not stop_flag.is_set():
        # Check pause
        while state.paused and not stop_flag.is_set():
            time.sleep(0.5)
        
        if stop_flag.is_set():
            break
        
        # Get next document from buffer
        with state_lock:
            pending = [d for d in state.documents if d.get("status") == "pending"]
        
        if not pending:
            # Fetch more documents
            add_log("[System] Buffer empty. Auto-fetching...")
            raw_docs = fetch_documents(20)
            
            # Filter empty docs
            empty_docs = [d for d in raw_docs if not d.get("content") or not d["content"].strip()]
            valid_docs = [d for d in raw_docs if d.get("content") and d["content"].strip()]
            
            # Auto-tag empty docs
            if empty_docs and LOW_QUALITY_TAG_ID:
                add_log(f"[Info] Found {len(empty_docs)} empty documents. Auto-tagging...")
                for doc in empty_docs:
                    try:
                        tag_document(doc["id"], int(LOW_QUALITY_TAG_ID))
                        add_history_entry(doc["id"], doc["title"], "skipped", "Empty Content", "Auto-tagged as Low Quality")
                    except Exception as e:
                        add_log(f"[Error] Failed to tag empty doc {doc['id']}: {e}")
            
            if not valid_docs:
                add_log("[System] No more documents found. Stopping.")
                break
            
            with state_lock:
                for doc in valid_docs:
                    state.documents.append({
                        "id": doc["id"],
                        "title": doc["title"],
                        "content": doc["content"],
                        "status": "pending"
                    })
                state.stats["total"] += len(valid_docs)
            
            add_log(f"[Info] Added {len(valid_docs)} new items to buffer.")
            continue
        
        # Process next document
        doc = pending[0]
        doc_id = doc["id"]
        
        with state_lock:
            # Update status
            for d in state.documents:
                if d["id"] == doc_id:
                    d["status"] = "processing"
            state.current_doc = doc
            state.llm_responses = {}
        
        add_log(f'[Processing] 📄 Document {doc_id}: "{doc["title"][:40]}..."')
        add_log(f'[Debug] Content length: {len(doc["content"])} chars')
        
        try:
            # Get models
            models = []
            if NUM_LLM_MODELS >= 1 and MODEL_NAME:
                models.append(MODEL_NAME)
            if NUM_LLM_MODELS >= 2 and SECOND_MODEL_NAME:
                models.append(SECOND_MODEL_NAME)
            if NUM_LLM_MODELS >= 3 and THIRD_MODEL_NAME:
                models.append(THIRD_MODEL_NAME)
            
            results = []
            for model in models:
                add_log(f"[Debug] Asking model {model}...")
                result = evaluate_content(doc["content"], model)
                add_log(f"[Debug] Model {model} replied: {result or 'empty'}")
                
                with state_lock:
                    state.llm_responses[model] = result or "No response"
                
                if result:
                    results.append(result)
            
            # Determine consensus based on number of models
            final_status = "no_consensus"

            if len(results) == 0:
                # No valid responses from any model
                add_log(f"[Error] ❌ No valid LLM response for document {doc_id}")
                add_log(f"[Error] Reason: All models returned empty or invalid responses")
                final_status = "no_consensus"
            elif len(models) == 1:
                # Single model mode: direct result, no consensus needed
                if results[0] == "high quality":
                    final_status = "high_quality"
                elif results[0] == "low quality":
                    final_status = "low_quality"
                add_log(f"[Info] Single model result: {results[0]}")
            else:
                # Multiple models: majority voting
                counts = {}
                for r in results:
                    counts[r] = counts.get(r, 0) + 1

                max_count = max(counts.values()) if counts else 0
                majority = [k for k, v in counts.items() if v == max_count]

                if len(majority) == 1:
                    if majority[0] == "high quality":
                        final_status = "high_quality"
                    elif majority[0] == "low quality":
                        final_status = "low_quality"

                add_log(f"[Info] Model votes: {counts} -> {final_status}")
            
            history_details = []
            renamed_old_title = None
            renamed_new_title = None

            # Log reason for no_consensus
            if final_status == "no_consensus":
                if len(results) == 0:
                    history_details.append("LLM returned no valid response")
                else:
                    history_details.append(f"Models disagreed: {results}")

            # Apply tags and generate title
            if final_status in ["high_quality", "low_quality"]:
                tag_id = int(HIGH_QUALITY_TAG_ID) if final_status == "high_quality" else int(LOW_QUALITY_TAG_ID)
                tag_document(doc_id, tag_id)
                add_log(f'[Tag] 🏷️ Document {doc_id} tagged as "{final_status}"')
                history_details.append(f"Tagged as {final_status}")
                
                if final_status == "high_quality" and models:
                    add_log(f"[AI] 🧠 Generating improved title for document {doc_id}...")
                    new_title = generate_title(doc["content"], models[0])
                    if new_title and new_title != doc["title"]:
                        renamed_old_title = doc["title"]
                        renamed_new_title = new_title
                        rename_document(doc_id, new_title)
                        add_log(f"[Title] ✨ TITLE CHANGED:")
                        add_log(f'[Title]    OLD: "{doc["title"]}"')
                        add_log(f'[Title]    NEW: "{new_title}"')
                        doc["new_title"] = new_title
                        history_details.append(f"Renamed")
            
            # Update stats
            with state_lock:
                state.stats["processed"] += 1
                if final_status == "high_quality":
                    state.stats["high_quality"] += 1
                elif final_status == "low_quality":
                    state.stats["low_quality"] += 1
                else:
                    state.stats["no_consensus"] += 1
                
                # Remove processed doc
                state.documents = [d for d in state.documents if d["id"] != doc_id]
            
            add_log(f"[Result] ✅ Document {doc_id}: {final_status} complete")
            
            # Add to history
            add_history_entry(
                doc_id,
                doc.get("new_title", doc["title"]),
                "processed",
                final_status,
                "; ".join(history_details),
                old_title=renamed_old_title,
                new_title=renamed_new_title
            )
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            add_log(f"[Error] ❌ Document {doc_id} failed: {e}")
            add_log(f"[Error] Details: {error_details[-500:]}")  # Last 500 chars of traceback
            with state_lock:
                state.stats["processed"] += 1
                state.stats["errors"] += 1
                state.documents = [d for d in state.documents if d["id"] != doc_id]

            add_history_entry(doc["id"], doc["title"], "error", "Failed", f"{e} - {error_details[-200:]}")
        
        # Small delay between documents
        time.sleep(0.5)
    
    with state_lock:
        state.processing = False
        state.current_doc = None
    
    add_log("[System] Processing stopped.")


# ============== API Endpoints ==============
class StatusResponse(BaseModel):
    processing: bool
    paused: bool
    stats: Dict[str, int]
    current_doc: Optional[Dict[str, Any]]
    llm_responses: Dict[str, str]
    documents: List[Dict[str, Any]]


@app.get("/api/status", response_model=StatusResponse)
def get_status():
    with state_lock:
        return StatusResponse(
            processing=state.processing,
            paused=state.paused,
            stats=state.stats,
            current_doc=state.current_doc,
            llm_responses=state.llm_responses,
            documents=state.documents[:50]  # Limit for performance
        )


@app.get("/api/logs")
def get_logs():
    with state_lock:
        return {"logs": state.logs}


@app.get("/api/history")
def get_history():
    with state_lock:
        return {"history": state.history}


@app.post("/api/reset")
def reset_stats():
    """Reset all stats, logs, and optionally history"""
    with state_lock:
        state.stats = {
            "total": 0,
            "processed": 0,
            "high_quality": 0,
            "low_quality": 0,
            "no_consensus": 0,
            "errors": 0,
            "skipped": 0
        }
        state.logs = []
        state.documents = []
        state.current_doc = None
        state.llm_responses = {}
    add_log("[System] Stats and logs reset")
    return {"message": "Stats reset"}


@app.post("/api/reset-history")
def reset_history():
    """Reset history completely"""
    with state_lock:
        state.history = []
    save_history()
    add_log("[System] History cleared")
    return {"message": "History cleared"}


@app.post("/api/start")
def start_processing():
    global worker_thread, stop_flag
    
    if state.processing:
        return {"message": "Already processing"}
    
    with state_lock:
        state.processing = True
        state.paused = False
    
    stop_flag.clear()
    worker_thread = threading.Thread(target=process_documents, daemon=True)
    worker_thread.start()
    
    return {"message": "Processing started"}


@app.post("/api/stop")
def stop_processing():
    global stop_flag
    
    if not state.processing:
        return {"message": "Not processing"}
    
    stop_flag.set()
    add_log("[System] Stop requested...")
    
    return {"message": "Stop requested"}


@app.post("/api/pause")
def toggle_pause():
    with state_lock:
        state.paused = not state.paused
        status = "paused" if state.paused else "resumed"
    add_log(f"[System] Processing {status}")
    return {"paused": state.paused}


@app.get("/api/system-stats")
def get_system_stats():
    import os as os_module
    
    # CPU and RAM
    total_mem = os_module.sysconf('SC_PAGE_SIZE') * os_module.sysconf('SC_PHYS_PAGES')
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            meminfo = {l.split(':')[0]: int(l.split(':')[1].strip().split()[0]) for l in lines if ':' in l}
            free_mem = meminfo.get('MemAvailable', 0) * 1024
            used_mem = total_mem - free_mem
            ram_percent = int((used_mem / total_mem) * 100)
    except:
        ram_percent = 0
        used_mem = 0
    
    # Load average as CPU approximation
    try:
        load_avg = os_module.getloadavg()[0]
        cpu_count = os_module.cpu_count() or 1
        cpu_percent = min(100, int((load_avg / cpu_count) * 100))
    except:
        cpu_percent = 0
    
    # GPU via nvidia-smi
    gpu_util = 0
    vram_used = 0
    vram_total = 0
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = [int(x.strip()) for x in result.stdout.strip().split(',')]
            if len(parts) >= 3:
                gpu_util, vram_used, vram_total = parts[0], parts[1], parts[2]
    except:
        pass
    
    return {
        "cpu": cpu_percent,
        "ram": ram_percent,
        "ram_txt": f"{int(used_mem / 1024 / 1024 / 1024)}GB / {int(total_mem / 1024 / 1024 / 1024)}GB",
        "gpu": gpu_util,
        "vram": int((vram_used / vram_total) * 100) if vram_total else 0,
        "vram_txt": f"{vram_used}MB / {vram_total}MB"
    }


if __name__ == "__main__":
    import uvicorn
    add_log("[System] Backend server starting...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
