# Complete Workflow Example

This guide shows how to run all six phases to build a semantic knowledge graph.

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

### Step 4: Normalize Concepts

```bash
# Normalize concepts into canonical forms
uv run python concept_normalizer.py <doc_id> --debug

# Process all documents
uv run python concept_normalizer.py --all

# Skip LLM verification for faster processing (less accurate)
uv run python concept_normalizer.py <doc_id> --skip-verification

# Adjust similarity threshold (default: 0.80)
uv run python concept_normalizer.py <doc_id> --similarity-threshold 0.85

# Output: data/canonical/<doc_id>_canonical.json
```

This merges duplicate concepts and variants into canonical concepts with aliases.

**Note**: First run downloads sentence-transformers model (~80MB).

### Step 5: Extract Relationships

```bash
# Extract relationships between canonical concepts
uv run python relationship_extractor.py <doc_id> --debug

# Process all documents
uv run python relationship_extractor.py --all

# Use different model
uv run python relationship_extractor.py <doc_id> --model llama3.2:latest

# Output: data/relationships/<doc_id>_relationships.json
```

This extracts relationships between concepts to build knowledge graph edges.

**Note**: Requires Ollama to be running. Only extracts relationships grounded in text (no hallucination).

### Step 6: Refine and Assemble Final Graph

```bash
# Refine graph structure and compute metrics
uv run python graph_refiner.py <doc_id> --debug

# Process all documents
uv run python graph_refiner.py --all

# Adjust confidence threshold
uv run python graph_refiner.py <doc_id> --min-confidence 0.6

# Save visualization-ready format (minimal payload)
uv run python graph_refiner.py <doc_id> --viz-format

# Output: data/graph/<doc_id>_final_graph.json
```

This refines the graph by filtering weak edges, resolving conflicts, computing metrics, and scoring node importance.

**Note**: First time runs `uv sync` to install NetworkX if needed.

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

### Phase 4 Output (canonical)
```json
[
  {
    "canonical_id": "cn_001",
    "canonical_name": "End-to-End Testing",
    "aliases": ["E2E Testing", "e2e testing", "end to end testing"],
    "type": "core_concept",
    "importance_score": 8.5,
    "total_mentions": 12,
    "documents_present": 3,
    "descriptions": ["Testing approach that validates complete application workflows"],
    "source_concepts": ["c_001", "c_045", "c_089"]
  }
]
```

### Phase 5 Output (relationships)
```json
[
  {
    "edge_id": "e_a3f8d2c1",
    "source_concept_id": "cn_012",
    "target_concept_id": "cn_001",
    "relation_type": "USES",
    "evidence_block_id": "b_045",
    "confidence": 0.92
  }
]
```

### Phase 6 Output (final_graph)
```json
{
  "nodes": [
    {
      "id": "cn_001",
      "label": "End-to-End Testing",
      "type": "core_concept",
      "importance": 0.82,
      "metrics": {
        "degree_centrality": 0.45,
        "betweenness_centrality": 0.38,
        "clustering_coefficient": 0.15
      }
    }
  ],
  "edges": [
    {
      "source": "cn_012",
      "target": "cn_001",
      "relation": "USES",
      "weight": 0.92
    }
  ],
  "metadata": {
    "num_nodes": 28,
    "num_edges": 35,
    "graph_metrics": {...}
  }
}
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

### For Phase 4
- First run downloads sentence-transformers model (~80MB)
- Use `--debug` to see clustering details
- LLM verification is recommended for accuracy (can skip with `--skip-verification`)
- Similarity threshold 0.80 works well (0.75-0.85 range)
- Expect 50-70% reduction in concept count (duplicates merged)

### For Phase 5
- **IMPORTANT**: Ollama must be running!
- Requires both Phase 2 (semantic blocks) and Phase 4 (canonical concepts)
- Only extracts relationships from text (no hallucination or inference)
- Use `--debug` to see candidate pairs and extraction details
- Relationships are directional (source → target)
- Confidence reflects how clearly the relationship is stated in text

### For Phase 6
- Requires both Phase 4 (canonical concepts) and Phase 5 (relationships)
- Default confidence threshold (0.55) works well for most cases
- Use `--debug` to see validation, refinement, and scoring details
- `--viz-format` creates minimal payload optimized for visualization
- `--no-prune` keeps isolated nodes (useful for debugging)
- NetworkX automatically installed via `uv sync` if needed
- Graph metrics help identify most important concepts
- Typical output: 20-40 nodes, 30-50 edges after refinement

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

### "Concepts not found"
```bash
# Run Phase 3 first
uv run python concept_extractor.py <doc_id>
```

### Phase 3 is very slow
- Use `--max-blocks 10` for testing
- LLM inference takes time locally
- Consider using a faster model for testing

### Phase 4 "Model download failed"
- First run downloads ~80MB sentence-transformers model
- Ensure stable internet connection
- Model caches in ~/.cache/torch/sentence_transformers/

### "Canonical concepts not found" (Phase 5)
```bash
# Run Phase 4 first
uv run python concept_normalizer.py <doc_id>
```

### Phase 5 "No relationships extracted"
- Check that concepts actually co-occur in blocks
- Try with `--debug` to see candidate pairs
- Verify Ollama is running and responsive

## Next Steps

After Phase 6, you have:
- Original documents (Phase 1)
- Semantic blocks (Phase 2)  
- Concept candidates (Phase 3)
- Canonical concepts (Phase 4)
- Concept relationships (Phase 5)
- **Refined knowledge graph** (Phase 6) ✨

**Complete, Production-Ready Knowledge Graph**:
- High-quality nodes with importance scores
- Validated edges with confidence weights
- Graph metrics and structural analysis
- Visualization-ready format

Phase 7 (future) will:
- Create interactive 3D graph visualizations
- Implement graph exploration UI
- Add semantic search over graph
- Export to graph databases (Neo4j, ArangoDB, etc.)
- Generate graph insights and summaries
