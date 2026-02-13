# Graphitee - Phase 1: Semantic Article Ingestion

A modular system for extracting clean, structured, semantically organized content from technical articles using Playwright.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Usage

```bash
# Basic usage
python main.py <url>

# With debug output
python main.py <url> --debug

# Control crawl depth and max pages
python main.py <url> --depth 2 --max-pages 10
```

## Architecture

- **scraper/**: Core extraction logic using Playwright DOM APIs
- **storage/**: Data models and JSON storage layer
- **utils/**: URL utilities
- **data/docs/**: JSON storage directory (created automatically)

## Features

- Pure Playwright DOM extraction (no BeautifulSoup)
- Semantic content structuring with heading hierarchies
- Controlled internal link crawling
- Clean section tree building
- Future-ready for LLM concept extraction
