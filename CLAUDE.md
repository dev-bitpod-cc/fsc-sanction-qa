# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **production-ready deployment** of an AI-powered Q&A system for Financial Supervisory Commission (FSC) penalty cases in Taiwan. The system uses Google Gemini File Search Store API for RAG (Retrieval-Augmented Generation), covering 490 penalty cases from 2012-2025.

**Key Constraint**: This is a **deployment-only repository** - it contains minimal files for Streamlit Cloud deployment and does NOT include the original 490 penalty case text files or index building scripts.

## Critical Architecture Decisions

### 1. Gemini File Search Store API
- **Package**: `google-genai` (NOT `google-generativeai`)
- **Version**: 1.49.0+ required for File Search Store API
- **API Structure**:
  - Import: `from google import genai`
  - Client: `genai.Client(api_key=...)`
  - File Search uses `types.Tool(file_search=...)` configuration

### 2. Persistent Index Design
- **File Search Store** is permanently stored in Google's infrastructure
- `data/gemini_corpus/store_info.json` contains the Store ID (e.g., `fileSearchStores/fscpenaltycases...`)
- Files uploaded to Files API expire in 48 hours, but File Search Store content persists indefinitely
- No need to rebuild index unless data changes
- **Filename Mapping**: `store_info.json` also contains a mapping from Gemini's internal file IDs to original filenames, enabling display of user-friendly filenames in query results

### 3. Configuration Loading Pattern
- Secrets via Streamlit: Environment variable `GEMINI_API_KEY`
- Config file: `config/gemini_config.yaml` (model, temperature, etc.)
- `ConfigLoader` uses `Path(__file__).parent.parent` to resolve paths from any location

### 4. UI Branding Requirements
- **Remove all Gemini branding** from user-facing text per requirements
- Use generic terms: "AI 智能問答系統", "智能索引", "AI 查詢中"
- Technical implementation details (Gemini engine) remain in code/logs

## Running the Application

### Local Development
```bash
# 1. Set up secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml and add your GEMINI_API_KEY

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run application
streamlit run app/main_deploy.py
```

### Deployment to Streamlit Cloud
```bash
# 1. Push to GitHub
git add .
git commit -m "Your message"
git push -u origin main

# 2. Configure in Streamlit Cloud dashboard:
# - Main file path: app/main_deploy.py
# - Secrets: GEMINI_API_KEY = "your-key"
```

## Code Architecture

### Engine Pattern (app/engines/)
- **base.py**: Abstract `RAGEngine` class with `query()` and `build_index()` methods
- **gemini_engine.py**: Concrete implementation using Gemini File Search
  - `file_id_to_name`: Dictionary mapping Gemini internal IDs to original filenames
  - `load_corpus_info()`: Loads existing Store ID and filename mappings from `store_info.json`
  - `query()`: Uses `generate_content()` with `file_search` tool
  - `_extract_sources()`: Parses `grounding_metadata.grounding_chunks` for sources, converts internal file IDs to original filenames using the mapping table
  - Returns `RAGResponse` with answer, sources (with readable filenames), latency, cost

### Main Application (app/main_deploy.py)
- **Caching**: `@st.cache_resource` on `initialize_gemini_engine()` to persist engine instance
- **State Management**: Session state for `current_question` and `should_update_question`
- **UI Components**:
  - `render_sidebar()`: Shows index status, file count, system info
  - Main area: Question input, submit/clear buttons, results display with sources

### Response Structure
```python
RAGResponse(
    answer: str,           # Generated answer text
    sources: List[Source], # Retrieved source documents
    confidence: float,     # 0.85 default for Gemini
    latency: float,        # Query execution time
    cost_estimate: float,  # Estimated API cost
    engine_name: str       # "Gemini File Search"
)
```

## Important Implementation Notes

### When Modifying Gemini Integration
1. **File Search Store ID** is read from `data/gemini_corpus/store_info.json` on initialization
2. **Filename mapping** is built from `store_info.json` during `load_corpus_info()` - maps internal IDs (e.g., `9ky8rgmy5pdk`) to original filenames (e.g., `392_20210722_銀行局_未指定.txt`)
3. **Do not attempt to rebuild index** - original penalty files are not in this repo
4. Model configuration in `config/gemini_config.yaml` - default is `gemini-2.5-flash`
5. Source extraction relies on `grounding_metadata` structure - check for `retrieved_context.title` and `retrieved_context.text`
6. **Source count is dynamic** - determined by Gemini File Search API based on query relevance, not a fixed number

### When Modifying UI
1. Keep branding generic (no "Gemini" mentions to end users)
2. Session state pattern prevents text area from resetting on rerun
3. Example questions are hardcoded in `main_deploy.py` lines 224-231
4. **Cache management**: After deploying code changes, Streamlit Cloud may cache old instances. Use "Reboot app" or press 'C' in the app to clear cache

### Dependencies
- **Minimal by design**: Only 3 packages (streamlit, google-genai, pyyaml)
- Python 3.10+ required (Streamlit Cloud uses 3.13)
- No local vector store or embedding libraries needed

## Common Pitfalls

1. **Wrong package name**: Use `google-genai` NOT `google-generativeai`
2. **Missing Store ID**: App fails if `store_info.json` is missing or malformed
3. **API Key**: Must be set in Streamlit Secrets, NOT in code or .env files
4. **Import paths**: Use relative imports within app/ package (`from .base import ...`)

## File Structure Logic

```
app/
├── main_deploy.py          # Entry point, Streamlit UI
├── engines/
│   ├── base.py            # Abstract RAGEngine class
│   └── gemini_engine.py   # Gemini implementation
└── utils/
    └── config_loader.py    # YAML config loader

data/gemini_corpus/
└── store_info.json         # Critical: Contains File Search Store ID

config/
└── gemini_config.yaml      # Model config (temperature, tokens, etc.)
```

**Note**: Original penalty case files (`data/penalties/*.txt`) are NOT in this repo. This is a deployment-only version that relies on the pre-built File Search Store.
