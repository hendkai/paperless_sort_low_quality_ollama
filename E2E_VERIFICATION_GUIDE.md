# End-to-End Verification Guide
## Testing Full Workflow with Non-Ollama Providers

This guide provides step-by-step instructions for performing end-to-end verification of the custom LLM provider implementation.

---

## Overview

This verification tests the complete document analysis workflow using a non-Ollama provider (e.g., GPT, Claude API, or GLM) to ensure:
1. ✅ Documents are fetched from Paperless-ngx
2. ✅ Provider evaluates document content
3. ✅ Documents are tagged correctly based on quality
4. ✅ No errors in logs
5. ✅ Optional: Title generation works for high-quality documents

---

## Prerequisites

Before starting verification, ensure you have:

1. **A working Paperless-ngx instance** with documents
   - API URL and Token configured
   - At least one document with content
   - Tags configured for LOW_QUALITY_TAG_ID and HIGH_QUALITY_TAG_ID

2. **API credentials for at least one non-Ollama provider**:
   - GPT (OpenAI): API key from https://platform.openai.com/api-keys
   - Claude API (Anthropic): API key from https://console.anthropic.com/
   - GLM (Zhipu AI): API key from https://open.bigmodel.cn/

3. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration**:
   - Copy `.env.example` to `.env`
   - Fill in your API credentials
   - Configure Paperless-ngx connection details

---

## Step-by-Step Verification

### Step 1: Configure Environment

Choose ONE provider to test. Below are example configurations for each:

#### Option A: GPT (OpenAI)
```bash
# .env file
API_URL=http://your.paperless.instance:8000/api
API_TOKEN=your_paperless_api_token
LLM_PROVIDER=gpt
GPT_API_KEY=sk-your-actual-openai-key-here
GPT_MODEL=gpt-4
LOW_QUALITY_TAG_ID=1
HIGH_QUALITY_TAG_ID=2
MAX_DOCUMENTS=5
LOG_LEVEL=INFO
RENAME_DOCUMENTS=yes
```

#### Option B: Claude API (Anthropic)
```bash
# .env file
API_URL=http://your.paperless.instance:8000/api
API_TOKEN=your_paperless_api_token
LLM_PROVIDER=claude_api
CLAUDE_API_KEY=sk-ant-your-actual-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022
LOW_QUALITY_TAG_ID=1
HIGH_QUALITY_TAG_ID=2
MAX_DOCUMENTS=5
LOG_LEVEL=INFO
RENAME_DOCUMENTS=yes
```

#### Option C: GLM (Zhipu AI)
```bash
# .env file
API_URL=http://your.paperless.instance:8000/api
API_TOKEN=your_paperless_api_token
LLM_PROVIDER=glm
GLM_API_KEY=your_actual_glm_key_here
GLM_MODEL=glm-4
LOW_QUALITY_TAG_ID=1
HIGH_QUALITY_TAG_ID=2
MAX_DOCUMENTS=5
LOG_LEVEL=INFO
RENAME_DOCUMENTS=yes
```

---

### Step 2: Verify Provider Creation

Before running the full workflow, verify the provider can be created:

```bash
python -c "
import os
from dotenv import load_dotenv
from llm_providers import create_llm_provider

load_dotenv()

provider_type = os.getenv('LLM_PROVIDER')
print(f'Testing provider creation for: {provider_type}')

if provider_type == 'gpt':
    provider = create_llm_provider('gpt', {
        'api_key': os.getenv('GPT_API_KEY'),
        'model': os.getenv('GPT_MODEL')
    })
elif provider_type == 'claude_api':
    provider = create_llm_provider('claude_api', {
        'api_key': os.getenv('CLAUDE_API_KEY'),
        'model': os.getenv('CLAUDE_MODEL')
    })
elif provider_type == 'glm':
    provider = create_llm_provider('glm', {
        'api_key': os.getenv('GLM_API_KEY'),
        'model': os.getenv('GLM_MODEL')
    })

print(f'✅ Provider created successfully: {type(provider).__name__}')
print(f'   Model: {provider.model}')
print(f'   URL: {provider.url}')
"
```

**Expected output:**
```
Testing provider creation for: gpt
✅ Provider created successfully: GPTProvider
   Model: gpt-4
   URL: https://api.openai.com/v1/chat/completions
```

---

### Step 3: Test Basic Provider Functionality

Test that the provider can make API calls:

```bash
python test_e2e_verification.py --test-provider
```

Or manually:

```python
# test_provider.py
import os
from dotenv import load_dotenv
from llm_providers import create_llm_provider

load_dotenv()

# Create provider
provider = create_llm_provider('gpt', {
    'api_key': os.getenv('GPT_API_KEY'),
    'model': os.getenv('GPT_MODEL')
})

# Test evaluate_content
test_content = "This is a well-written, clear document with meaningful content."
test_prompt = "Please review the following document content and determine if it is of low quality or high quality."

result = provider.evaluate_content(test_content, test_prompt, doc_id=999)
print(f"Quality evaluation result: {result}")

# Test generate_title
title = provider.generate_title("Generate a title for this document.", test_content)
print(f"Generated title: {title}")
```

**Expected output:**
```
Quality evaluation result: high quality
Generated title: Well-Written Document Analysis
```

---

### Step 4: Run Full Workflow

Now run the complete document analysis workflow:

```bash
python main.py
```

---

### Step 5: Verification Checklist

As the workflow runs, verify the following:

#### ✅ Check 1: Documents are Fetched
**What to look for in logs:**
```
INFO - Searching for documents with content...
INFO - 🤖 5 documents with content found.
INFO - Document ID: 123, Title: sample_document.pdf
```

**Visual indicator:**
- Robot animation during document fetch
- Console shows number of documents found

#### ✅ Check 2: Provider Evaluates Content
**What to look for in logs:**
```
INFO - Using 1 LLM provider(s) with type: gpt
INFO - ====> Verarbeite Dokument ID: 123 ====
INFO - Aktueller Titel: 'sample_document.pdf'
INFO - Inhaltslänge: 1234 Zeichen
INFO - Model gpt-4 result for document ID 123: high quality
INFO - Ollama Qualitätsbewertung für Dokument ID 123: high quality
INFO - Konsensus erreicht: True
```

**What to verify:**
- Provider type is correct (gpt, claude_api, or glm)
- Model name matches configuration
- Quality evaluation returns "high quality" or "low quality"
- No timeout errors (60 second timeout for evaluation)

#### ✅ Check 3: Documents are Tagged Correctly
**What to look for in logs:**
```
INFO - Dokument 123 wird als 'High Quality' markiert (Tag ID: 2)
INFO - Tagging Response: 200 - {"tags": [2]}
INFO - Dokument ID 123 erfolgreich als 'High Quality' markiert.
```

**Visual indicator:**
- Green checkmark in console: `✅ Dokument 123 verarbeitet (1/5)`
- Message: "Die KI-Modelle haben entschieden, die Datei als 'High Quality' einzustufen."

**Verify in Paperless-ngx:**
1. Open Paperless-ngx web interface
2. Navigate to the processed documents
3. Check that the appropriate tag (Low Quality or High Quality) is applied
4. Verify no duplicate tags were added

#### ✅ Check 4: No Errors in Logs
**Check for these common errors:**

❌ **Authentication Errors:**
```
ERROR - Error sending request to GPT: 401 Client Error: Unauthorized
```
**Solution:** Check API key is correct

❌ **Rate Limiting:**
```
ERROR - Error sending request to GPT: 429 Client Error: Rate Limit Exceeded
```
**Solution:** Wait a few minutes and try again, or reduce MAX_DOCUMENTS

❌ **Timeout Errors:**
```
ERROR - Error sending request to GPT: timeout
```
**Solution:** Check internet connection, API service status

❌ **Invalid Model:**
```
ERROR - Error sending request to GPT: 400 Client Error: Bad Request
```
**Solution:** Verify model name is correct for your API

#### ✅ Check 5: Title Generation (Optional)
If `RENAME_DOCUMENTS=yes` and document is high quality:

**What to look for in logs:**
```
INFO - Beginne Umbenennungsprozess für High-Quality-Dokument 123...
INFO - Generiere neuen Titel basierend auf Inhalt (Länge: 1234 Zeichen)
INFO - Neuer generierter Titel: 'Meaningful Document Title'
INFO - ✅ ERFOLG: Dokument ID 123 wurde erfolgreich umbenannt
```

**Verify in Paperless-ngx:**
- Document title has been updated to a meaningful title
- Title is descriptive of the content (not generic)

---

### Step 6: Analyze Results

After the workflow completes, verify:

**Console output should show:**
```
🤖 Welcome to the Document Quality Analyzer!
🤖 5 documents with content found.
🤖 Starte sequentielle Verarbeitung von 5 Dokumenten...
🤖 Verarbeite Dokument 1/5 (ID: 123)
✅ Dokument 123 verarbeitet (1/5)
🤖 Verarbeite Dokument 2/5 (ID: 124)
✅ Dokument 124 verarbeitet (2/5)
...
🤖 Verarbeitung aller Dokumenten abgeschlossen!
🤖 Processing completed!
```

**Check log file (if configured):**
- No ERROR or CRITICAL messages
- All documents processed successfully
- API calls successful (200 status codes)

---

## Troubleshooting

### Issue: Provider not recognized
**Error:** `ValueError: Unknown provider type: 'xyz'`

**Solution:**
- Check `LLM_PROVIDER` value in .env
- Valid values: ollama, glm, claude_api, claude_code, gpt

### Issue: Missing credentials
**Error:** `ValueError: GPT provider requires 'api_key' and 'model' in config`

**Solution:**
- Ensure all required environment variables are set
- Check .env file has correct variable names
- Verify API key is not empty

### Issue: Fallback to Ollama
**Warning:** `LLM_PROVIDER 'gpt' is not configured or missing required credentials. Defaulting to Ollama`

**Solution:**
- Check API key is set correctly
- Verify API key has not expired
- Check for typos in variable names

### Issue: No documents found
**Output:** `🤖 No documents with content found.`

**Solution:**
- Verify Paperless-ngx API URL is correct
- Check API token is valid
- Ensure documents exist in Paperless-ngx
- Confirm documents have extracted content (not just uploaded files)

---

## Success Criteria

✅ **Verification PASSED if:**
1. All documents are fetched from Paperless-ngx
2. Provider evaluates each document without errors
3. Correct quality tags are applied to all documents
4. No ERROR or CRITICAL log messages
5. Console shows all documents processed successfully
6. (Optional) High-quality documents receive meaningful titles

✅ **Verification FAILED if:**
1. Any authentication errors occur
2. Documents are not fetched
3. Provider fails to evaluate content
4. Tags are not applied correctly
5. Any documents cause exceptions or errors
6. API rate limits are exceeded consistently

---

## Next Steps After Verification

If verification passes:
1. ✅ Document the provider used and results
2. ✅ Update implementation_plan.json with verification results
3. ✅ Consider testing with additional providers
4. ✅ Deploy to production with confidence

If verification fails:
1. ❌ Document the specific error
2. ❌ Check provider-specific requirements
3. ❌ Review API documentation
4. ❌ Verify network connectivity and API status
5. ❌ Re-test after fixing issues

---

## Example Successful Run

```
$ python main.py

🤖 Welcome to the Document Quality Analyzer!
🤖 Searching Documents [═══════] /
🤖 5 documents with content found.
Document ID: 123, Title: invoice.pdf
Document ID: 124, Title: contract.pdf
Document ID: 125, Title: letter.pdf
Document ID: 126, Title: report.pdf
Document ID: 127, Title: memo.pdf

🤖 Starting processing...
🤖 Starte sequentielle Verarbeitung von 5 Dokumenten...
🤖 Verarbeite Dokument 1/5 (ID: 123)
✅ Dokument 123 verarbeitet (1/5)
================================================================================
🤖 Verarbeite Dokument 2/5 (ID: 124)
✅ Dokument 124 verarbeitet (2/5)
================================================================================
...
🤖 Verarbeitung aller Dokumenten abgeschlossen!
🤖 Processing completed!
```

With `LOG_LEVEL=DEBUG` in .env, you'll see detailed API logs:
```
DEBUG - Sending POST request to https://api.openai.com/v1/chat/completions
DEBUG - Request payload: {"model": "gpt-4", "messages": [...], "temperature": 0.3}
DEBUG - Response status: 200
DEBUG - Response content: {"choices": [{"message": {"content": "high quality"}}]}
INFO - Model gpt-4 result for document ID 123: high quality
```

---

## Testing Multiple Providers

To test multiple providers sequentially:

1. Test with GPT first (fastest response times)
2. Update .env to use Claude API
3. Run verification again
4. Update .env to use GLM
5. Run verification again

Document results for each provider in `VERIFICATION_RESULTS.md`.

---

## Automated Verification Script

For automated testing, use the provided `test_e2e_verification.py` script:

```bash
# Quick test - provider only
python test_e2e_verification.py --test-provider

# Full E2E test with 1 document
python test_e2e_verification.py --max-docs 1

# Full E2E test with 5 documents
python test_e2e_verification.py --max-docs 5

# Debug mode with verbose logging
python test_e2e_verification.py --max-docs 1 --debug
```

---

## Contact & Support

If you encounter issues during verification:
1. Check logs with `LOG_LEVEL=DEBUG` in .env
2. Review LLM_PROVIDERS.md for provider-specific configuration
3. Verify API credentials are valid and not expired
4. Check API service status pages
5. Review this guide's troubleshooting section

---

**Last Updated:** 2026-01-14
**Feature Version:** Custom LLM Provider Support (v1.0)
