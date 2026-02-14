# Complete Workflow Example

This guide shows how to run all three phases to build a semantic knowledge graph.

## Prerequisites

1. **Python 3.13** with uv
2. **Ollama** installed and running with llama3.1:8b

## Setup

```bash
# 1. Install dependencies
uv sync

# 2. Install Playwright browsers
uv run playwright install chromium

# 3. Start Ollama (in separate terminal)
ollama serve

# 4. Pull the model
ollama pull llama3.1:8b
```

## Full Pipeline Example

### Step 1: Scrape an Article

```bash
# Scrape a technical article
uv run python main.py https://playwright.dev/docs/intro --depth 1 --max-pages 3

# Output: data/docs/<doc_id>.json
```

This extracts structured content with sections, headings, and content blocks.

### Step 2: Build Semantic Blocks

```bash
# List scraped documents
uv run python semantic_builder.py --list

# Process the document (use doc_id from list)
uv run python semantic_builder.py <doc_id> --debug

# Or process all at once
uv run python semantic_builder.py --all

# Output: data/semantic_blocks/<doc_id>.json
```

This splits content into meaningful semantic units (1 idea per block).

### Step 3: Extract Concepts

```bash
# Make sure Ollama is running!
# In another terminal: ollama serve

# Extract concepts from semantic blocks
uv run python concept_extractor.py <doc_id> --debug

# For testing (process only first 5 blocks)
uv run python concept_extractor.py <doc_id> --max-blocks 5

# Process all documents
uv run python concept_extractor.py --all

# Output: data/concepts/<doc_id>_concepts.json
```

This extracts technical concepts using the local LLM.

## Understanding the Output

### Phase 1 Output (docs)
```json
{
  "id": "abc123",
  "title": "Introduction to Testing",
  "sections": [
    {
      "section_id": "sec_1",
      "heading": "Getting Started",
      "content_blocks": [...]
    }
  ]
}
```

### Phase 2 Output (semantic_blocks)
```json
[
  {
    "block_id": "b_001",
    "text": "Playwright is a framework for Web Testing...",
    "block_type": "definition",
    "heading_path": ["Introduction", "Getting Started"],
    "token_estimate": 45
  }
]
```

### Phase 3 Output (concepts)
```json
[
  {
    "concept_id": "c_001",
    "name": "End-to-End Testing",
    "type": "core_concept",
    "description": "Testing approach that validates complete application workflows",
    "source_block_id": "b_001",
    "heading_path": ["Introduction", "Getting Started"],
    "confidence": 0.87
  }
]
```

## Tips

### For Phase 1
- Start with small sites first
- Use `--debug` to see extraction details
- Adjust `--max-pages` to control crawl size

### For Phase 2
- Check block count and token estimates
- Look at block type distribution
- Verify heading paths are correct

### For Phase 3
- **IMPORTANT**: Ollama must be running!
- Use `--max-blocks` for quick testing
- Check concept quality in output
- Adjust `--min-confidence` to filter concepts
- Phase 3 can take time (LLM calls per block)

## Troubleshooting

### "Cannot connect to Ollama"
```bash
# Make sure Ollama is running
ollama serve

# Check model is installed
ollama list

# Pull model if needed
ollama pull llama3.1:8b
```

### "No documents found"
```bash
# Run Phase 1 first
uv run python main.py https://example.com/article
```

### "Semantic blocks not found"
```bash
# Run Phase 2 first
uv run python semantic_builder.py <doc_id>
```

### Phase 3 is very slow
- Use `--max-blocks 10` for testing
- LLM inference takes time locally
- Consider using a faster model for testing

## Next Steps

After Phase 3, you have:
- Original documents (Phase 1)
- Semantic blocks (Phase 2)  
- Concept candidates (Phase 3)

Phase 4 (future) will:
- Merge duplicate concepts
- Build relationships between concepts
- Create the final knowledge graph
