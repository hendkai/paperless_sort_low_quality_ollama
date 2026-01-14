# 🤖 LLM Providers Configuration Guide

This guide provides comprehensive documentation for configuring and using various LLM (Large Language Model) providers with the Document Quality Checker. The system supports multiple providers, allowing you to choose the one that best fits your needs and infrastructure.

## ✨ Supported Providers

The following LLM providers are currently supported:

- 🦙 **Ollama** - Local, self-hosted LLM service (default, backward compatible)
- 🧠 **GLM** - Zhipu AI's GLM models (z.ai)
- 🎭 **Claude API** - Anthropic's Claude API
- 💻 **Claude Code** - Claude with Model Context Protocol (MCP)
- 🧪 **GPT** - OpenAI's GPT models

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Provider Configuration](#provider-configuration)
  - [Ollama (Local)](#ollama-local)
  - [GLM (Zhipu AI)](#glm-zhipu-ai)
  - [Claude API](#claude-api)
  - [Claude Code](#claude-code)
  - [GPT (OpenAI)](#gpt-openai)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

### Step 1: Choose Your Provider

Decide which LLM provider you want to use. Consider:

- **Ollama**: Best for local, private processing. No API costs. Requires local hardware.
- **GLM**: Good Chinese language support. Competitive pricing.
- **Claude API**: Excellent for nuanced analysis. High-quality outputs.
- **GPT**: Widely adopted, well-documented. Good performance.

### Step 2: Set Environment Variables

1. Copy `.env.example` to `.env`:
   ```sh
   cp .env.example .env
   ```

2. Edit `.env` and set `LLM_PROVIDER` to your chosen provider:
   ```bash
   LLM_PROVIDER=gpt  # or glm, claude_api, claude_code, ollama
   ```

3. Configure provider-specific variables (see below)

### Step 3: Install Dependencies

If using API-based providers (GLM, Claude, GPT), install required packages:

```bash
pip install -r requirements.txt
```

This will install:
- `anthropic>=0.18.0` (for Claude API and Claude Code)
- `openai>=1.0.0` (for GPT)
- `zhipuai` (for GLM)

### Step 4: Run the Script

```bash
python main.py
```

## ⚙️ Provider Configuration

### 🦙 Ollama (Local)

Ollama is the default provider and runs locally on your machine or network.

**Advantages:**
- ✅ Free (no API costs)
- ✅ Private (data stays local)
- ✅ No internet required
- ✅ Multiple models support with ensemble voting

**Disadvantages:**
- ❌ Requires local hardware resources
- ❌ Manual model management
- ❌ May be slower than cloud APIs

#### Configuration

```bash
# Provider selection
LLM_PROVIDER=ollama

# Ollama server URL (default: http://localhost:11434)
OLLAMA_URL=http://localhost:11434

# API endpoint (default: /api/generate)
OLLAMA_ENDPOINT=/api/generate

# Primary model
MODEL_NAME=llama3.2

# Optional: Second model for ensemble voting
SECOND_MODEL_NAME=mistral

# Optional: Third model for ensemble voting
THIRD_MODEL_NAME=dolphin mixtral

# Number of models to use (1-3)
NUM_LLM_MODELS=3
```

#### Supported Models

Popular Ollama models include:
- `llama3.2` - Meta's Llama 3.2 (excellent general performance)
- `mistral` - Mistral 7B (fast and efficient)
- `codellama` - Code-specialized model
- `phi3` - Microsoft's Phi 3 (compact, good performance)
- `qwen2` - Alibaba's Qwen 2 (good multilingual support)

To list available models on your system:
```bash
ollama list
```

To download a new model:
```bash
ollama pull llama3.2
```

#### Installation

1. Install Ollama: https://ollama.com/download
2. Start Ollama service
3. Pull your preferred model
4. Configure `.env` file

#### Example: Single Model Setup

```bash
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_ENDPOINT=/api/generate
MODEL_NAME=llama3.2
NUM_LLM_MODELS=1
```

#### Example: Ensemble Setup (Recommended for Quality)

```bash
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_ENDPOINT=/api/generate
MODEL_NAME=llama3.2
SECOND_MODEL_NAME=mistral
THIRD_MODEL_NAME=qwen2
NUM_LLM_MODELS=3
```

With ensemble mode, the system uses all 3 models and applies consensus logic for more reliable quality assessments.

---

### 🧠 GLM (Zhipu AI)

GLM is provided by Zhipu AI (BigModel), offering competitive Chinese and English language processing.

**Advantages:**
- ✅ Excellent Chinese language support
- ✅ Competitive pricing
- ✅ Fast response times
- ✅ Good multilingual capabilities

**Disadvantages:**
- ❌ Requires API key
- ❌ Internet connection required
- ❌ API costs apply

#### Configuration

```bash
# Provider selection
LLM_PROVIDER=glm

# Zhipu AI API key
# Get your key from: https://open.bigmodel.cn/
GLM_API_KEY=your_glm_api_key_here

# GLM model to use
GLM_MODEL=glm-4
```

#### Supported Models

- `glm-4` - Latest GLM model (recommended)
- `glm-3-turbo` - Faster, cost-effective option
- `chatglm3-6b` - Previous generation, still capable

#### API Key Setup

1. Visit https://open.bigmodel.cn/
2. Register for an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

#### Example Configuration

```bash
LLM_PROVIDER=glm
GLM_API_KEY=5f3d8e9a2b1c4d6f7a8b9c0d1e2f3a4b
GLM_MODEL=glm-4
```

---

### 🎭 Claude API

Anthropic's Claude API provides high-quality language understanding and generation.

**Advantages:**
- ✅ Excellent analysis quality
- ✅ Large context window
- ✅ Strong safety features
- ✅ Good at nuanced tasks

**Disadvantages:**
- ❌ Higher cost per token
- ❌ Rate limits on free tier
- ❌ Requires API key

#### Configuration

```bash
# Provider selection
LLM_PROVIDER=claude_api

# Anthropic API key
# Get your key from: https://console.anthropic.com/
CLAUDE_API_KEY=your_claude_api_key_here

# Claude model to use
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

#### Supported Models

- `claude-3-5-sonnet-20241022` - Latest Sonnet (recommended for quality)
- `claude-3-haiku-20240307` - Fast, cost-effective
- `claude-3-opus-20240229` - Highest quality, slower

#### API Key Setup

1. Visit https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy the key to your `.env` file

#### Example Configuration

```bash
LLM_PROVIDER=claude_api
CLAUDE_API_KEY=sk-ant-1234567890abcdef
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

---

### 💻 Claude Code

Claude Code uses Anthropic's Claude API with Model Context Protocol (MCP) for specialized integrations.

**Advantages:**
- ✅ Optimized for Claude Code workflows
- ✅ Same quality as Claude API
- ✅ MCP compatibility
- ✅ Good for code-related analysis

**Disadvantages:**
- ❌ Same costs as Claude API
- ❌ Requires API key
- ❌ Similar to Claude API (consider which fits your use case)

#### Configuration

```bash
# Provider selection
LLM_PROVIDER=claude_code

# Anthropic API key (same as Claude API)
# Get your key from: https://console.anthropic.com/
CLAUDE_CODE_API_KEY=your_claude_code_api_key_here

# Claude Code model to use
CLAUDE_CODE_MODEL=claude-3-5-sonnet-20241022
```

#### Supported Models

Same as Claude API:
- `claude-3-5-sonnet-20241022` (recommended)
- `claude-3-haiku-20240307` (fast, cost-effective)
- `claude-3-opus-20240229` (highest quality)

#### API Key Setup

Same as Claude API - you can use the same API key for both providers.

#### Example Configuration

```bash
LLM_PROVIDER=claude_code
CLAUDE_CODE_API_KEY=sk-ant-1234567890abcdef
CLAUDE_CODE_MODEL=claude-3-5-sonnet-20241022
```

---

### 🧪 GPT (OpenAI)

OpenAI's GPT models provide reliable, well-tested language processing capabilities.

**Advantages:**
- ✅ Widely adopted and tested
- ✅ Extensive documentation
- ✅ Good performance across tasks
- ✅ Multiple model options

**Disadvantages:**
- ❌ API costs
- ❌ Rate limits apply
- ❌ Requires API key

#### Configuration

```bash
# Provider selection
LLM_PROVIDER=gpt

# OpenAI API key
# Get your key from: https://platform.openai.com/api-keys
GPT_API_KEY=your_openai_api_key_here

# GPT model to use
GPT_MODEL=gpt-4
```

#### Supported Models

- `gpt-4` - Latest GPT-4 (recommended for quality)
- `gpt-4-turbo` - Faster GPT-4 variant
- `gpt-3.5-turbo` - Cost-effective, good performance
- `gpt-4o` - Multimodal capabilities

#### API Key Setup

1. Visit https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new secret key
5. Copy the key to your `.env` file

#### Example Configuration

```bash
LLM_PROVIDER=gpt
GPT_API_KEY=sk-proj-1234567890abcdef
GPT_MODEL=gpt-4
```

---

## 🔧 Advanced Configuration

### Custom API Endpoints

Some providers support custom API endpoints (useful for proxies or self-hosted instances):

```bash
# For GLM
GLM_API_KEY=your_key
GLM_MODEL=glm-4
GLM_URL=https://your-custom-endpoint.com/v4/chat/completions

# For Claude API
CLAUDE_API_KEY=your_key
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_URL=https://your-custom-endpoint.com/v1/messages

# For GPT
GPT_API_KEY=your_key
GPT_MODEL=gpt-4
GPT_URL=https://your-custom-endpoint.com/v1/chat/completions
```

### Fallback Behavior

The system includes automatic fallback logic:

1. If you set `LLM_PROVIDER=gpt` but `GPT_API_KEY` is missing
2. The system will fallback to Ollama (if configured)
3. This prevents configuration errors from breaking the system

To enable strict mode (no fallback), ensure all required environment variables are set.

### Model Parameters

The following parameters are configured internally and optimized for document quality analysis:

- **Temperature**: 0.3 for evaluation (consistent results), 0.7 for title generation (creative)
- **Max Tokens**: 100 for evaluation, 50 for title generation
- **Timeout**: 60 seconds for evaluation, 30 seconds for title generation

These values are tuned for the document quality analysis use case and generally should not need adjustment.

## 🔍 Troubleshooting

### Common Issues and Solutions

#### Issue: "Unknown provider type" Error

**Cause:** Invalid `LLM_PROVIDER` value

**Solution:** Ensure `LLM_PROVIDER` is one of:
- `ollama`
- `glm`
- `claude_api`
- `claude_code`
- `gpt`

#### Issue: "Provider requires 'api_key' and 'model' in config"

**Cause:** Missing required environment variables for API-based providers

**Solution:** Check that you have set:
- For GLM: `GLM_API_KEY` and `GLM_MODEL`
- For Claude API: `CLAUDE_API_KEY` and `CLAUDE_MODEL`
- For Claude Code: `CLAUDE_CODE_API_KEY` and `CLAUDE_CODE_MODEL`
- For GPT: `GPT_API_KEY` and `GPT_MODEL`

#### Issue: Ollama Connection Refused

**Cause:** Ollama service is not running or URL is incorrect

**Solution:**
1. Verify Ollama is running: `ollama list`
2. Check `OLLAMA_URL` in `.env` (default: `http://localhost:11434`)
3. If using Docker, ensure port mapping is correct
4. Test connection: `curl http://localhost:11434/api/generate`

#### Issue: API Authentication Errors

**Cause:** Invalid or expired API keys

**Solution:**
1. Verify API key is correct (no extra spaces)
2. Check API key hasn't expired
3. Ensure API key has necessary permissions
4. Regenerate API key if needed

#### Issue: Slow Response Times

**Cause:** Various factors depending on provider

**Solutions:**

**For Ollama:**
- Use a smaller model (e.g., `phi3` instead of `llama3.2`)
- Ensure sufficient RAM/CPU resources
- Consider using GPU acceleration

**For API providers:**
- Check internet connection speed
- Try a faster model variant (e.g., `claude-3-haiku` instead of `claude-3-opus`)
- Reduce `MAX_DOCUMENTS` to process fewer documents per batch

#### Issue: Inconsistent Quality Assessments

**Cause:** Model variability or insufficient context

**Solutions:**
- Use ensemble mode with Ollama (3 models)
- Try a more capable model (e.g., `claude-3-opus`, `gpt-4`)
- Adjust prompt definition in code if needed
- Ensure document content is being extracted properly

#### Issue: Import Errors

**Cause:** Missing dependencies for API-based providers

**Solution:**
```bash
pip install -r requirements.txt
```

This installs:
- `anthropic>=0.18.0`
- `openai>=1.0.0`
- `zhipuai`

### Getting Help

If you encounter issues not covered here:

1. Check the logs: Set `LOG_LEVEL=DEBUG` in `.env`
2. Verify all environment variables are set correctly
3. Test your API keys using the provider's dashboard
4. Check network connectivity to API endpoints
5. Open an issue on GitHub with:
   - Your `LLM_PROVIDER` setting
   - Relevant error messages
   - Log output (with sensitive information redacted)

## 📊 Provider Comparison

| Provider | Cost | Speed | Quality | Privacy | Setup |
|----------|------|-------|---------|---------|-------|
| **Ollama** | Free | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Easy |
| **GLM** | Paid | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Easy |
| **Claude API** | Paid | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Easy |
| **Claude Code** | Paid | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Easy |
| **GPT** | Paid | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Easy |

**Legend:**
- ⭐ = Poor, ⭐⭐⭐ = Average, ⭐⭐⭐⭐⭐ = Excellent
- Privacy: Local (⭐⭐⭐⭐⭐) vs Cloud (⭐⭐⭐)

## 🎯 Recommendations

### For Privacy/Security
Use **Ollama** with local models. All processing stays on your machine.

### For Best Quality
Use **Claude API** or **GPT-4** for the most nuanced document analysis.

### For Cost Efficiency
Use **Ollama** (free) or **GLM** (competitive pricing).

### For Chinese Documents
Use **GLM** for best Chinese language support.

### For Fast Processing
Use **GPT-3.5-turbo**, **Claude Haiku**, or a small Ollama model like **Phi-3**.

### For Production Use
Consider **ensemble mode with Ollama** (3 models) for reliability without API costs, or **Claude API** for highest quality.

## 📝 Example Configurations

### Local Development (Privacy Focused)

```bash
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_ENDPOINT=/api/generate
MODEL_NAME=llama3.2
NUM_LLM_MODELS=1
```

### Production Ensemble (High Quality)

```bash
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_ENDPOINT=/api/generate
MODEL_NAME=llama3.2
SECOND_MODEL_NAME=mistral
THIRD_MODEL_NAME=qwen2
NUM_LLM_MODELS=3
```

### Cloud-Based (Best Quality)

```bash
LLM_PROVIDER=claude_api
CLAUDE_API_KEY=sk-ant-xxxxxxxxxx
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

### Cost-Effective Cloud

```bash
LLM_PROVIDER=gpt
GPT_API_KEY=sk-proj-xxxxxxxxxx
GPT_MODEL=gpt-3.5-turbo
```

### Multilingual Support

```bash
LLM_PROVIDER=glm
GLM_API_KEY=xxxxxxxxxx
GLM_MODEL=glm-4
```

---

## 📚 Additional Resources

- [Ollama Documentation](https://ollama.com/docs)
- [Zhipu AI GLM Documentation](https://open.bigmodel.cn/dev/api)
- [Anthropic Claude Documentation](https://docs.anthropic.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Main Project README](README.md)

---

**Last Updated:** 2026-01-14
