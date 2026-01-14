# Architecture Documentation

## Overview

This document describes the modular architecture of the Document Quality Analyzer application. The architecture follows clean architecture principles with dependency injection, separation of concerns, and single responsibility.

The refactoring transformed a monolithic 440-line `main.py` into a well-organized modular structure with 7 distinct modules, each under 200 lines and focused on a single responsibility.

## Architecture Goals

- **Separation of Concerns**: Each module handles a specific aspect of the application
- **Testability**: All dependencies are injectable, enabling comprehensive unit testing
- **Maintainability**: Clear module boundaries make the codebase easier to understand and modify
- **Extensibility**: New features can be added by extending specific modules without touching others
- **Single Responsibility**: Each module has one clear purpose and stays under 200 lines

## Module Structure

```
src/
├── config/          # Configuration management
├── api/             # Paperless API client
├── llm/             # Ollama LLM service
├── quality/         # Quality analysis logic
├── processing/      # Document processing orchestration
├── cli/             # Command-line interface
└── container.py     # Dependency injection container
```

## Module Descriptions

### 1. Configuration Module (`src/config/config.py`)

**Purpose**: Centralized configuration management from environment variables

**Key Responsibilities**:
- Load and validate environment variables
- Provide typed accessors for configuration values
- Validate required settings on startup
- Define prompt templates for LLM interactions

**Public Interface**:
```python
Config.api_url() -> str
Config.api_token() -> str
Config.ollama_url() -> str
Config.model_name() -> str
Config.get_llm_models() -> List[str]
Config.low_quality_tag_id() -> int
Config.high_quality_tag_id() -> int
Config.max_documents() -> int
Config.rename_documents() -> bool
Config.log_level() -> str
Config.validate() -> None
```

**Dependencies**: None (uses only `os` and `dotenv`)

**Size**: 145 lines

### 2. API Client Module (`src/api/client.py`)

**Purpose**: Handle all Paperless API interactions

**Key Responsibilities**:
- Fetch documents with pagination
- Get CSRF tokens for write operations
- Retrieve individual document details
- Tag documents with quality tags
- Update document titles
- Retry logic with exponential backoff

**Public Interface**:
```python
PaperlessClient.fetch_documents(max_documents, page_size) -> List[dict]
PaperlessClient.get_csrf_token(session) -> str
PaperlessClient.get_document(document_id) -> dict
PaperlessClient.tag_document(document_id, tag_id, csrf_token) -> None
PaperlessClient.update_title(document_id, new_title, csrf_token) -> None
```

**Dependencies**: `requests`, `tenacity` (retry decorator)

**Size**: 194 lines

### 3. LLM Service Module (`src/llm/service.py`)

**Purpose**: Interface with Ollama LLM API for content evaluation and title generation

**Key Responsibilities**:
- Send content to Ollama for evaluation
- Generate meaningful titles from document content
- Handle JSON streaming responses
- Support ensemble evaluation across multiple models
- Implement consensus logic for quality decisions

**Public Interface**:
```python
OllamaService.evaluate_content(content, prompt, document_id) -> dict
OllamaService.generate_title(prompt, content) -> str
EnsembleOllamaService.evaluate_content(content, prompt, document_id) -> Tuple[dict, bool]
```

**Dependencies**: `requests`, `tenacity`

**Size**: 163 lines

### 4. Quality Analyzer Module (`src/quality/analyzer.py`)

**Purpose**: Evaluate document quality using LLM ensemble

**Key Responsibilities**:
- Coordinate ensemble evaluation across multiple LLMs
- Validate and normalize LLM responses
- Determine consensus on document quality
- Decide appropriate tagging action (high/low quality)
- Handle consensus failure scenarios

**Public Interface**:
```python
QualityAnalyzer.evaluate(content, document_id) -> Tuple[str, bool]
QualityAnalyzer.is_high_quality(quality_result) -> bool
QualityAnalyzer.is_low_quality(quality_result) -> bool
```

**Dependencies**: `EnsembleOllamaService` (injected via constructor)

**Size**: 136 lines

### 5. Document Processor Module (`src/processing/processor.py`)

**Purpose**: Orchestrate the complete document processing workflow

**Key Responsibilities**:
- Process documents through quality analysis pipeline
- Tag documents based on quality assessment
- Optionally rename high-quality documents with meaningful titles
- Track processing statistics
- Handle errors gracefully per-document

**Public Interface**:
```python
DocumentProcessor.process_documents(documents, ignore_already_tagged) -> dict
```

**Dependencies**:
- `PaperlessClient` (injected)
- `QualityAnalyzer` (injected)
- `OllamaService` (injected)

**Size**: 158 lines

### 6. CLI Interface Module (`src/cli/interface.py`)

**Purpose**: Provide unified command-line interface and user feedback

**Key Responsibilities**:
- Display colored console messages
- Show animated progress indicators
- Present document processing progress
- Display statistics and summaries
- Handle user confirmations

**Public Interface**:
```python
CLIInterface.show_welcome()
CLIInterface.show_documents_found(count, documents)
CLIInterface.show_processing_start(total)
CLIInterface.show_document_progress(current, total, doc_id)
CLIInterface.show_document_complete(doc_id, current, total)
CLIInterface.show_document_error(doc_id, error)
CLIInterface.show_statistics(stats)
CLIInterface.show_robot_animation()
CLIInterface.clear_animation()
```

**Dependencies**: `colorama`, `logging`

**Size**: 153 lines

### 7. Dependency Injection Container (`src/container.py`)

**Purpose**: Create and wire together all application components

**Key Responsibilities**:
- Lazy initialization of all components
- Singleton pattern for component reuse
- Manage dependency graph
- Support configuration validation
- Provide reset method for testing

**Public Interface**:
```python
Container.config -> Config
Container.api_client -> PaperlessClient
Container.llm_service -> OllamaService
Container.ensemble_llm_service -> EnsembleOllamaService
Container.quality_analyzer -> QualityAnalyzer
Container.document_processor -> DocumentProcessor
Container.cli_interface -> CLIInterface
Container.reset() -> None
```

**Dependencies**: All modules (imports and wires them together)

**Size**: 176 lines

## Dependencies and Flow

### Dependency Graph

```
Container
├── Config (no dependencies)
├── PaperlessClient
│   └── Config
├── OllamaService
│   └── Config
├── EnsembleOllamaService
│   └── [multiple OllamaService instances]
├── QualityAnalyzer
│   ├── EnsembleOllamaService
│   └── Config.PROMPT_DEFINITION
├── DocumentProcessor
│   ├── PaperlessClient
│   ├── QualityAnalyzer
│   ├── OllamaService
│   └── Config (tag IDs, rename flag)
└── CLIInterface (no dependencies)
```

### Application Flow

1. **Initialization** (`main.py` → `Container`)
   - Container validates configuration
   - Components created lazily on first access

2. **Document Fetching** (`main.py` → `PaperlessClient`)
   - Fetch documents from Paperless API
   - Display robot animation while fetching

3. **Document Processing** (`main.py` → `DocumentProcessor`)
   - For each document:
     a. Get document content from API
     b. Evaluate quality using `QualityAnalyzer`
     c. Tag document as high/low quality via API
     d. Optionally rename high-quality documents
   - Track statistics (processed, skipped, tagged)

4. **User Feedback** (`main.py` → `CLIInterface`)
   - Show progress for each document
   - Display quality decisions
   - Show final statistics

### Data Flow

```
Paperless API
    ↓ (documents)
DocumentProcessor
    ↓ (content)
QualityAnalyzer
    ↓ (evaluation request)
EnsembleOllamaService
    ↓ (parallel requests)
OllamaService (multiple models)
    ↓ (individual evaluations)
EnsembleOllamaService
    ↓ (consensus result)
QualityAnalyzer
    ↓ (quality decision)
DocumentProcessor
    ↓ (tag/rename actions)
Paperless API
```

## Design Patterns

### 1. Dependency Injection

All components receive their dependencies through constructor parameters rather than creating them internally. This enables:

- Easy testing with mock objects
- Flexible component replacement
- Clear dependency graph

**Example**:
```python
class QualityAnalyzer:
    def __init__(self, llm_service: EnsembleOllamaService, quality_prompt: str):
        self.llm_service = llm_service
        self.quality_prompt = quality_prompt
```

### 2. Singleton Pattern (via Container)

The Container ensures only one instance of each component exists:

- Lazy initialization via properties
- Cached instances in private attributes
- Reset method for testing

**Example**:
```python
@property
def api_client(self) -> PaperlessClient:
    if self._api_client is None:
        self._api_client = PaperlessClient(...)
    return self._api_client
```

### 3. Strategy Pattern

Different LLM services can be plugged in:

- `OllamaService` for single-model operations
- `EnsembleOllamaService` for multi-model consensus

### 4. Facade Pattern

`DocumentProcessor` provides a simplified interface to the complex workflow:

- Hides complexity of multi-step processing
- Coordinates interactions between multiple modules
- Provides single entry point for document processing

## Key Architectural Decisions

### Why Lazy Initialization?

Components are created only when first accessed to:

- Avoid unnecessary startup overhead
- Allow partial component usage in tests
- Enable circular dependency resolution

### Why Separate Services for Single vs Ensemble LLM?

Two separate services provide:

- Clear separation of concerns (title generation vs quality evaluation)
- Different error handling strategies
- Ability to optimize each for its use case

### Why Statistics Tracking in DocumentProcessor?

Centralized tracking enables:

- Easy aggregation across all documents
- Clean separation of processing logic from display logic
- Testable statistics without UI dependencies

### Why CLI Module Separation?

Isolating CLI logic enables:

- Easy testing of business logic without console output
- Potential for alternative UIs (GUI, web)
- Reusable business logic in different contexts

## Testing Strategy

### Unit Tests

Each module can be tested independently by injecting mock dependencies:

```python
def test_quality_analyzer():
    mock_llm = Mock(spec=EnsembleOllamaService)
    analyzer = QualityAnalyzer(mock_llm, "test prompt")
    # Test analyzer logic without real LLM calls
```

### Integration Tests

Test module interactions without external dependencies:

```python
def test_document_processing():
    # Use mock API client and LLM service
    # Verify correct orchestration and statistics
```

### Refactor Validation Tests

Compare new modular implementation with old monolithic code:

```python
def test_identical_output():
    # Run both implementations with same inputs
    # Verify identical outputs
```

## Extension Points

### Adding a New Quality Tag

1. Add tag ID to `Config` module
2. Extend `QualityAnalyzer` with new quality level
3. Update `DocumentProcessor` tagging logic
4. No changes needed to API, LLM, or CLI modules

### Adding a New LLM Provider

1. Create new service class matching `OllamaService` interface
2. Update `Container` to instantiate new service
3. No changes needed to business logic modules

### Adding a New Output Format

1. Extend `CLIInterface` with new display methods
2. Or create new `WebInterface` or `GUIInterface`
3. No changes needed to business logic modules

## Performance Considerations

### Sequential Processing

Documents are processed sequentially (not in parallel) because:

- Paperless API rate limits
- Ollama model CPU/memory usage
- Clearer error handling and debugging

### Ensemble Evaluation

Multiple LLM models are queried sequentially for consensus:

- Tradeoff between accuracy and speed
- Can be parallelized in future if needed
- Consensus logic improves quality assessment

### Pagination

API client fetches documents in pages to:

- Avoid memory issues with large document sets
- Provide progress feedback
- Enable early termination

## Security Considerations

### API Token Storage

Tokens are loaded from environment variables only:

- Never hardcoded in source
- Loaded via `python-dotenv` from `.env` file
- `.env` should be excluded from version control

### CSRF Protection

All write operations use CSRF tokens:

- Token fetched from cookies
- Included in POST request headers
- Prevents cross-site request forgery

### Input Validation

Configuration is validated on startup:

- Required variables checked
- Type conversion handled safely
- Early failure on misconfiguration

## Error Handling Strategy

### Retry Logic

Network operations use `tenacity` retry decorator:

- 3 attempts with 2-second wait
- Applied to all external API calls
- Logs retry attempts for debugging

### Per-Document Error Handling

Document processor continues on individual failures:

- Errors logged but don't stop processing
- Statistics track successes and failures
- User sees summary of any issues

### Graceful Degradation

Consensus failures are handled gracefully:

- Logs warning when consensus not reached
- Skips tagging for that document
- Continues processing remaining documents

## Future Improvements

### Potential Enhancements

1. **Parallel Processing**: Process multiple documents concurrently
2. **Caching**: Cache LLM evaluations for identical content
3. **Batch API Calls**: Reduce API round trips
4. **Configuration File**: Support config files beyond environment variables
5. **Plugin System**: Allow custom quality evaluators
6. **Metrics Export**: Export statistics to monitoring systems

### Technical Debt

1. **Type Hints**: Add full type hints to all methods
2. **Async I/O**: Consider async/await for API calls
3. **Database**: Add persistent state tracking
4. **Testing**: Increase test coverage to >90%

## References

- [Clean Code by Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Clean Architecture by Robert C. Martin](https://www.amazon.com/Clean-Architecture-Craftsmanship-Software-Structure/dp/0134494164)
- [Python Dependency Injection](https://python-dependency-injector.ets-labs.org/)
- [Paperless-ngx API Documentation](https://docs.paperless-ngx.com/api/)
- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
