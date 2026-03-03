# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Graphitee is an "Agentic Reading Companion" - a CLI tool that transforms web articles into interactive knowledge graphs using AI. It scrapes articles, extracts concepts/relationships, and provides Q&A, quality analysis, and 3D visualization.

## Common Commands

```bash
# Install dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium

# Run the CLI
python cli.py

# Build frontend (for 3D visualization)
cd frontend && npm install && npm run build && cd ..

# Setup Ollama (macOS)
brew install ollama
ollama serve
ollama pull llama3.1:8b
```

## Architecture

### Data Flow
```
URL → BrowserManager (Playwright stealth) → Crawler → ContentExtractor
                                                         ↓
                                                    DOMCleaner
                                                         ↓
                                                    SectionBuilder
                                                         ↓
                                                    Document (sections + links)

Article Content → LLM (Ollama) → Concepts + Relationships → GraphReasoner
```

### Key Components

- **CLI** (`cli.py`) - Rich terminal UI, command routing
- **Orchestrator** (`agent/orchestrator.py`) - Main agent loop, intent handling, coordinates all tools
- **Reasoning** (`agent/reasoning.py`) - Intent parsing using LLM, quality analysis, summarization
- **GraphReasoner** (`agent/graph_reasoner.py`) - Manages in-memory knowledge graph (NetworkX)
- **State** (`agent/state.py`) - SQLite session persistence at `~/.graphitee/sessions.db`
- **Scraper** (`services/scraper.py`, `scraper/`) - Tiered article scraping via Playwright
- **LLM** (`services/llm.py`) - Ollama wrapper (llama3.1:8b)
- **BrowserManager** (`scraper/browser.py`) - Playwright with stealth config for bot detection bypass

### Intent System

The orchestrator uses `agent/reasoning.py` to parse user input into intents:
- `ASK_QUESTION` - Query article content
- `EXPLAIN_CONCEPT` - Deep dive into a concept
- `VIEW_GRAPH` - Open 3D visualization
- `QUALITY_CHECK` - Analyze credibility/bias
- `PREREQUISITES` - Show prerequisites
- `SUMMARIZE` - Generate summary
- `SUGGEST` - Get next concept suggestions

## Key Technical Details

### Scraper Tiers
- **Tier 1**: `max_depth=0`, `max_pages=1` - Quick summary
- **Tier 2**: `max_depth=1`, `max_pages=3` - Full content + internal links

### Browser Stealth Config
The `BrowserManager` includes stealth configuration to bypass bot detection:
- `--disable-blink-features=AutomationControlled` flag
- Custom user-agent, viewport, locale
- Init scripts to mask `navigator.webdriver`, mock plugins/languages

### Session Storage
SQLite at `~/.graphitee/sessions.db` with tables:
- `sessions` - Article metadata
- `messages` - Conversation history
- `concept_states` - Explored/unexplored concepts

### Environment Variables
- `TAVILY_API_KEY` - Optional, for web search/fact-checking
