# Graphitee - Agentic Reading Companion

An intelligent reading companion that transforms web articles into interactive knowledge graphs. Ask questions, explore concepts, and understand articles deeply with AI-powered assistance.

## Features

- **Knowledge Graph Exploration** - Visualize concepts and their relationships in 3D
- **Smart Q&A** - Ask questions about the article and get context-aware answers
- **Quality Analysis** - Assess article credibility, bias, and readability
- **Prerequisite Detection** - Understand what knowledge you need before reading
- **Concept Suggestions** - Get personalized recommendations on what to explore next
- **Session Persistence** - Resume reading sessions anytime

## Requirements

- Python 3.10+
- [Ollama](https://ollama.ai/) with llama3.1:8b model
- [Playwright](https://playwright.dev/) browsers
- Node.js (for frontend visualization)

### Optional
- [Tavily API](https://tavily.com/) key for web search / fact-checking

## Setup

```bash
# Clone and navigate to project
cd graphitee

# Install Python dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium

# Setup Ollama (macOS)
brew install ollama
ollama serve
ollama pull llama3.1:8b

# Build frontend
cd frontend && npm install && npm run build && cd ..
```

## Quick Start

```bash
# Start the CLI
python cli.py
```

### Example Session

```
Graphitee - Agentic Reading Companion
Type 'help' for available commands, 'quit' to exit

> load https://example.com/article
Loading https://example.com/article...
Loaded: **Article Title**

Found 12 key concepts. You can ask me questions about this article, or try:
- "ask [question]" - Ask anything about the article
- "graph" - View the knowledge graph
- "quality" - Check article quality and bias
- "prereqs" - See what you should know first

> ask What is the main argument?
[AI answers based on article content]

> graph
[Opens 3D visualization in browser]

> quality
[Shows credibility, bias, readability analysis]

> what next
[Shows suggested concepts to explore]
```

## Commands

| Command | Description |
|---------|-------------|
| `load <url>` | Load and analyze an article |
| `ask <question>` | Ask a question about the article |
| `explore <concept>` | Explore a specific concept in depth |
| `graph` | Open 3D knowledge graph visualization |
| `quality` | Analyze article quality and bias |
| `prereqs` | Show prerequisites for understanding |
| `summarize` | Get article summary |
| `what next` | Get suggested concepts to explore |
| `help` | Show available commands |
| `quit` | Exit the program |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI                                  │
│                    (Rich Terminal)                           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Orchestrator                            │
│  - Intent parsing (LLM)                                     │
│  - Tool routing                                             │
│  - State management (SQLite)                               │
└─────────────────────────────┬───────────────────────────────┘
                              │
    ┌───────────────┬─────────┼─────────┬───────────────┐
    ▼               ▼         ▼         ▼               ▼
┌────────┐   ┌────────┐  ┌────────┐ ┌────────┐   ┌────────┐
│Scraper │   │  LLM   │  │ Graph  │ │ Web    │   │Quality │
│(Play-  │   │(Ollama)│  │Reasoner│ │Search  │   │Analyzer│
│ wright)│   │         │  │        │ │(Tavily)│   │        │
└────────┘   └────────┘  └────────┘ └────────┘   └────────┘
```

### Key Components

- **agent/orchestrator.py** - Main agent loop, intent handling
- **agent/state.py** - SQLite session management
- **agent/reasoning.py** - Hybrid LLM + rule-based reasoning
- **agent/graph_reasoner.py** - Graph queries, dependency analysis
- **services/scraper.py** - Article scraping (tiered)
- **services/llm.py** - Ollama wrapper
- **services/tavily.py** - Web search for fact-checking
- **viz_server.py** - 3D visualization server
- **frontend/** - React 3D graph visualization

## Session Data

Sessions are stored in SQLite at `~/.graphitee/sessions.db`:

```bash
# View sessions
sqlite3 ~/.graphitee/sessions.db

# Query data
SELECT * FROM sessions;
SELECT * FROM messages;
SELECT * FROM concept_states;
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TAVILY_API_KEY` | Optional - for web search / fact-checking |

## Tech Stack

- **Backend**: Python 3.13, Ollama (llama3.1:8b), Playwright, SQLite
- **Frontend**: React 18, Vite, Three.js, react-force-graph-3d
- **CLI**: Rich (terminal UI)

## License

MIT
