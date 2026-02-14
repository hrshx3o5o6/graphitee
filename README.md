# Graphitee - Semantic Knowledge Graph Pipeline

A modular system for extracting, structuring, and organizing technical content into semantic knowledge graphs.

## Setup

```bash
# Install dependencies (using uv)
uv python install 3.13
uv python pin 3.13
uv sync

# Install Playwright browsers
uv run playwright install chromium

# Install and setup Ollama (for Phase 3)
# macOS/Linux:
brew install ollama
ollama serve
ollama pull llama3.1:8b
```

## Usage

### Phase 1: Article Scraping

Extract structured content from web pages using Playwright.

```bash
# Basic usage
uv run python main.py <url>

# With debug output
uv run python main.py <url> --debug

# Control crawl depth and max pages
uv run python main.py <url> --depth 2 --max-pages 10
```

**Output**: `data/docs/<doc_id>.json` - Structured documents with sections and content blocks

### Phase 2: Semantic Block Building

Transform documents into semantic blocks (one idea per block).

```bash
# List available documents
uv run python semantic_builder.py --list

# Process a specific document
uv run python semantic_builder.py <doc_id> --debug

# Process all documents
uv run python semantic_builder.py --all
```

**Output**: `data/semantic_blocks/<doc_id>.json` - Semantic blocks with context and metadata

### Phase 3: Concept Extraction

Extract technical concepts from semantic blocks using local LLM (Ollama).

```bash
# List available documents
uv run python concept_extractor.py --list

# Process a specific document
uv run python concept_extractor.py <doc_id> --debug

# Process all documents
uv run python concept_extractor.py --all

# Test with limited blocks
uv run python concept_extractor.py <doc_id> --max-blocks 5

# Use different model or confidence threshold
uv run python concept_extractor.py <doc_id> --model llama3.1:8b --min-confidence 0.6
```

**Output**: `data/concepts/<doc_id>_concepts.json` - Extracted concept candidates

**Requirements**: Ollama must be running locally with llama3.1:8b model

### Phase 4: Concept Normalization

Normalize concept candidates into canonical concepts by merging duplicates and variants.

```bash
# List available documents
uv run python concept_normalizer.py --list

# Process a specific document
uv run python concept_normalizer.py <doc_id> --debug

# Process all documents
uv run python concept_normalizer.py --all

# Skip LLM verification (faster, less accurate)
uv run python concept_normalizer.py <doc_id> --skip-verification

# Adjust similarity threshold
uv run python concept_normalizer.py <doc_id> --similarity-threshold 0.85
```

**Output**: `data/canonical/<doc_id>_canonical.json` - Normalized canonical concepts

**Requirements**: 
- First run of Phase 4 will download sentence-transformers model (~80MB)
- LLM verification requires Ollama (can be skipped with `--skip-verification`)

## Architecture

### Phase 1: Scraper
- **scraper/**: Playwright-based DOM extraction
- **storage/**: Data models and JSON storage
- **utils/**: URL utilities

### Phase 2: Semantic Builder
- **semantic/**: Deterministic semantic block builder
  - `models.py`: SemanticBlock data model
  - `builder.py`: Main pipeline
  - `context.py`: Heading path resolution
  - `splitter.py`: Semantic text splitting
  - `heuristics.py`: Block type inference
  - `tokenizer.py`: Token estimation
  - `validator.py`: Validation logic

### Phase 3: Concept Extractor
- **concepts/**: LLM-based concept extraction
  - `models.py`: ConceptCandidate data model
  - `pipeline.py`: Main extraction pipeline
  - `extractor.py`: Ollama API integration
  - `prompts.py`: LLM prompt templates
  - `parser.py`: JSON output parsing
  - `filters.py`: Concept quality filters

### Storage
- **data/docs/**: Phase 1 extracted documents
- **data/semantic_blocks/**: Phase 2 semantic blocks
- **data/concepts/**: Phase 3 concept candidates

## Features

### Phase 1
- Pure Playwright DOM extraction (no BeautifulSoup)
- Semantic content structuring with heading hierarchies
- Controlled internal link crawling
- Clean section tree building

### Phase 2
- Deterministic semantic splitting (no AI/LLM)
- Context-aware blocks with full heading paths
- Heuristic-based type classification (definition, example, explanation, code, list)
- Token estimation for downstream processing
- Validation and statistics

### Phase 3 (NEW)
- Local LLM concept extraction via Ollama
- Structured extraction (NOT summarization)
- Quality filtering (removes generic terms)
- Concept types: core_concept, technique, metric, process, assumption
- Confidence scoring and validation
- Full source traceability (block → concept)
