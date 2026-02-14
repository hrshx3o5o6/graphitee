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

### Storage
- **data/docs/**: Phase 1 extracted documents
- **data/semantic_blocks/**: Phase 2 semantic blocks

## Features

### Phase 1
- Pure Playwright DOM extraction (no BeautifulSoup)
- Semantic content structuring with heading hierarchies
- Controlled internal link crawling
- Clean section tree building

### Phase 2 (NEW)
- Deterministic semantic splitting (no AI/LLM)
- Context-aware blocks with full heading paths
- Heuristic-based type classification (definition, example, explanation, code, list)
- Token estimation for downstream processing
- Validation and statistics
