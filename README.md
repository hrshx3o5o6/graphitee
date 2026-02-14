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

### Phase 5: Relationship Extraction

Extract relationships between canonical concepts to build knowledge graph edges.

```bash
# List available documents
uv run python relationship_extractor.py --list

# Process a specific document
uv run python relationship_extractor.py <doc_id> --debug

# Process all documents
uv run python relationship_extractor.py --all

# Use different model
uv run python relationship_extractor.py <doc_id> --model llama3.2:latest
```

**Output**: `data/relationships/<doc_id>_relationships.json` - Concept edges with relation types

**Requirements**: Ollama must be running with llama3.1:8b model

**Relation Types**: DEFINES, DEPENDS_ON, CAUSES, PART_OF, USES, EXTENDS, CONTRASTS_WITH, MEASURED_BY, ASSOCIATED_WITH

### Phase 6: Graph Refinement & Final Assembly

Refine and assemble the final knowledge graph from canonical concepts and relationships.

```bash
# List available documents
uv run python graph_refiner.py --list

# Process a specific document
uv run python graph_refiner.py <doc_id> --debug

# Process all documents
uv run python graph_refiner.py --all

# Adjust confidence threshold
uv run python graph_refiner.py <doc_id> --min-confidence 0.6

# Save visualization format (minimal payload)
uv run python graph_refiner.py <doc_id> --viz-format

# Keep isolated nodes (don't prune)
uv run python graph_refiner.py <doc_id> --no-prune
```

**Output**: `data/graph/<doc_id>_final_graph.json` - Refined knowledge graph ready for visualization

**Key Features**:
- Edge quality filtering (removes low confidence < 0.55)
- Duplicate edge merging
- Conflict resolution with relation priority
- Graph metrics (centrality, clustering)
- Node importance scoring
- Optional isolated node pruning

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

### Phase 4: Concept Normalizer
- **normalization/**: Concept deduplication and canonicalization
  - `models.py`: CanonicalConcept and cluster models
  - `pipeline.py`: Main normalization pipeline
  - `preprocessor.py`: String normalization
  - `embedder.py`: Semantic embeddings
  - `clustering.py`: Similarity-based clustering
  - `verifier.py`: LLM verification
  - `canonicalizer.py`: Canonical name selection

### Phase 5: Relationship Extractor
- **relationships/**: Graph edge extraction
  - `models.py`: ConceptEdge data model
  - `pipeline.py`: Main extraction pipeline
  - `candidate_builder.py`: Concept-to-block mapping
  - `extractor.py`: Ollama relationship extraction
  - `prompts.py`: LLM prompt templates
  - `parser.py`: JSON output parsing
  - `validator.py`: Edge validation and deduplication

### Phase 6: Graph Refiner
- **graph/**: Graph refinement and assembly
  - `models.py`: GraphNode, GraphEdge, FinalGraph models
  - `pipeline.py`: Main refinement pipeline
  - `validator.py`: Graph structure validation
  - `edge_refiner.py`: Edge merging, filtering, conflict resolution
  - `metrics.py`: NetworkX-based graph metrics
  - `scoring.py`: Node importance scoring
  - `assembler.py`: Final graph assembly and pruning

### Storage
- **data/docs/**: Phase 1 extracted documents
- **data/semantic_blocks/**: Phase 2 semantic blocks
- **data/concepts/**: Phase 3 concept candidates
- **data/canonical/**: Phase 4 canonical concepts
- **data/relationships/**: Phase 5 concept edges
- **data/graph/**: Phase 6 final refined graphs

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

### Phase 3
- Local LLM concept extraction via Ollama
- Structured extraction (NOT summarization)
- Quality filtering (removes generic terms)
- Concept types: core_concept, technique, metric, process, assumption
- Confidence scoring and validation
- Full source traceability (block → concept)

### Phase 4
- String normalization and exact deduplication
- Semantic similarity clustering (sentence-transformers)
- LLM verification to prevent bad merges
- Canonical name selection and alias tracking
- Importance scoring based on frequency and spread
- Typical 50-70% reduction in concept count

### Phase 5
- Text-grounded relationship extraction (NO hallucination)
- Strict relation type ontology (9 types)
- Block-level concept co-occurrence analysis
- LLM-based relationship identification
- Edge validation and deduplication
- Creates complete knowledge graph (nodes + edges)

### Phase 6 (NEW)
- Graph structure validation (removes invalid edges, self-loops)
- Edge quality filtering (confidence thresholds)
- Duplicate edge merging with aggregated evidence
- Conflict resolution with relation priority
- NetworkX-based graph metrics (centrality, clustering)
- Node importance scoring (occurrence + centrality)
- Optional isolated node pruning
- Visualization-ready output format
