# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Graphitee is an agentic reading companion that transforms web articles into interactive knowledge graphs. It uses AI (Ollama with llama3.1:8b) to extract concepts and relationships, enabling Q&A, quality analysis, and 3D visualization.

## Common Commands

```bash
# Install dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium

# Run CLI
python cli.py

# Build frontend (for 3D visualization)
cd frontend && npm install && npm run build && cd ..

# Start visualization server separately
python viz_server.py

# Ollama setup (macOS)
brew install ollama
ollama serve
ollama pull llama3.1:8b
```

## Architecture

```
CLI (Rich Terminal)
        │
        ▼
Orchestrator (agent/orchestrator.py)
        │
        ├─► Scraping Service (Playwright) ─► Browser Manager (stealth config)
        ├─► LLM Service (Ollama)
        ├─► Graph Reasoner (NetworkX)
        ├─► State Manager (SQLite)
        └─► Tools (scrape, query_graph, web_search)
```

### Core Flow
1. User loads URL via CLI → Orchestrator routes to ScrapeTool
2. BrowserManager (scraper/browser.py) fetches page with stealth config
3. ContentExtractor extracts sections/links → SectionBuilder builds hierarchy
4. LLM extracts concepts/relationships → GraphReasoner builds knowledge graph
5. User can query, explore concepts, view 3D graph, analyze quality

### Key Files
- `cli.py` - Terminal UI with Rich
- `agent/orchestrator.py` - Main agent coordinator, intent routing
- `agent/reasoning.py` - Intent parsing (LLM-based), quality analysis
- `agent/graph_reasoner.py` - Concept graph management using NetworkX
- `agent/state.py` - SQLite session persistence
- `scraper/browser.py` - Playwright browser with stealth configuration (bypasses bot detection)
- `scraper/crawler.py` - Recursive link crawling (configurable depth)
- `scraper/extractor.py` - DOM content extraction
- `services/llm.py` - Ollama wrapper for LLM calls

### Scraping Pipeline (scraper/ folder)
- `browser.py` - Launches Chromium with stealth args, handles Cloudflare challenges
- `crawler.py` - Crawls internal links recursively (max_depth configurable)
- `extractor.py` - Extracts content blocks (headings, paragraphs, code, lists)
- `cleaner.py` - Finds main content area, filters unwanted elements
- `section_builder.py` - Builds hierarchical section tree from blocks

## Configuration

- Session data: `~/.graphitee/sessions.db` (SQLite)
- Graph data output: `data/current_graph.json`
- Environment: `TAVILY_API_KEY` (optional, for web search)

## Important Notes

- Browser stealth config is in `scraper/browser.py` - includes user-agent spoofing, automation flag removal, Cloudflare challenge handling
- Scraper tier system: tier=1 (quick, depth=0), tier=2 (full, depth=1, max 3 pages)
- Intent types defined in `agent/reasoning.py` - maps user queries to actions
- Knowledge graph uses NetworkX for concept relationships and dependency analysis
