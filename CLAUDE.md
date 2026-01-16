# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A document quality analyzer that integrates Paperless-ngx with Ollama LLMs. It fetches documents from Paperless, uses an ensemble of LLM models to evaluate content quality, tags documents as low/high quality, and automatically generates titles for high-quality documents.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Configuration

Copy `.env.example` to `.env` and configure:
- `API_URL` / `API_TOKEN`: Paperless-ngx server credentials
- `OLLAMA_URL` / `OLLAMA_ENDPOINT`: Ollama server (supports both native Ollama `/api/generate` and OpenAI-compatible `/v1/` endpoints like LM Studio)
- `MODEL_NAME`, `SECOND_MODEL_NAME`, `THIRD_MODEL_NAME`: LLM models for ensemble evaluation
- `NUM_LLM_MODELS`: Number of models to use (1-3)
- `LOW_QUALITY_TAG_ID` / `HIGH_QUALITY_TAG_ID`: Paperless tag IDs for quality classification

## Architecture

### Core Components

**OllamaService** (`main.py:62-171`): Handles LLM API communication
- Supports both native Ollama API and OpenAI-compatible format (detected via `/v1/` in endpoint)
- `evaluate_content()`: Sends quality evaluation prompts, parses "high quality"/"low quality" responses
- `generate_title()`: Creates document titles using LLM

**EnsembleOllamaService** (`main.py:173-205`): Multi-model consensus system
- Runs evaluation across multiple LLM models
- `consensus_logic()`: Majority voting - requires agreement for tagging

### Processing Flow

1. `fetch_documents_with_content()`: Paginated retrieval from Paperless API with retry logic
2. `process_documents()`: Sequential processing loop (not threaded for traceability)
3. `process_single_document()`: Per-document workflow:
   - Quality evaluation via ensemble
   - Tagging based on consensus
   - Auto-title generation for high-quality documents via `generate_new_title()`
4. `update_document_title()`: PATCH request to rename documents

### Key Behaviors

- Uses `tenacity` library for retry logic (3 attempts, 2s delay) on API calls
- CSRF token required for Paperless write operations
- Documents without consensus are skipped (no tagging)
- Title generation uses first 1000 chars of content, limited to 100 char output
