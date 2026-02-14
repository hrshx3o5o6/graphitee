```markdown
# PHASE 4 — CONCEPT NORMALIZATION ENGINE (IMPLEMENTATION SPEC)

You are implementing **Phase 4** of a semantic knowledge graph pipeline.

Completed phases:

- Phase 1 → Website extraction (Playwright)
- Phase 2 → Semantic block building
- Phase 3 → Concept extraction

Input now contains noisy concept candidates with duplicates and variations.

Your task:

> Normalize concept candidates into canonical concepts suitable for graph nodes.

This phase is CRITICAL for graph quality.

---

## 1. OBJECTIVE

Input:

```

concept_candidates.json

```

Output:

```

canonical_concepts.json

````

You must:

- identify duplicate or equivalent concepts
- cluster semantically similar concepts
- choose a canonical name
- merge metadata
- preserve provenance

DO NOT extract relationships yet.

---

## 2. INPUT FORMAT

```json
[
  {
    "concept_id": "c_001",
    "name": "Model Overfitting",
    "type": "core_concept",
    "description": "Model learns noise instead of signal",
    "source_block_id": "b_021",
    "heading_path": ["Machine Learning", "Regularization"],
    "confidence": 0.87
  }
]
````

---

## 3. OUTPUT FORMAT

```json
[
  {
    "canonical_id": "canon_001",
    "canonical_name": "Overfitting",
    "aliases": [
      "Model Overfitting",
      "Over-fit models"
    ],
    "type": "core_concept",
    "descriptions": [...],
    "source_blocks": [...],
    "occurrence_count": 12,
    "importance_score": 0.82
  }
]
```

---

## 4. REQUIRED MODULE STRUCTURE

Create:

```
normalization/
├── models.py
├── preprocessor.py
├── embedder.py
├── clustering.py
├── verifier.py
├── canonicalizer.py
└── pipeline.py
```

Each module must have a single responsibility.

---

## 5. DATA MODELS

### ConceptCandidate

```python
@dataclass
class ConceptCandidate:
    concept_id: str
    name: str
    type: str
    description: str
    source_block_id: str
    heading_path: list[str]
    confidence: float
```

### CanonicalConcept

```python
@dataclass
class CanonicalConcept:
    canonical_id: str
    canonical_name: str
    aliases: list[str]
    type: str
    descriptions: list[str]
    source_blocks: list[str]
    occurrence_count: int
    importance_score: float
```

---

## 6. PIPELINE OVERVIEW

```
Load concept candidates
        ↓
String normalization
        ↓
Embedding generation
        ↓
Similarity clustering
        ↓
LLM verification (optional but recommended)
        ↓
Canonical naming
        ↓
Metadata merge
        ↓
Save canonical concepts
```

---

## 7. STEP 1 — STRING NORMALIZATION

Implement preprocessing:

* lowercase
* trim spaces
* remove punctuation
* normalize hyphens
* basic plural cleanup

Example:

```
"Over-fitting" → "overfitting"
"Models" → "model"
```

Create normalized_name field.

---

## 8. STEP 2 — EMBEDDING GENERATION

Purpose:

Measure semantic similarity between concepts.

Use:

* sentence-transformers OR local embedding model.

Embedding input:

```
concept_name + description
```

Store embedding vector per concept.

---

## 9. STEP 3 — SIMILARITY COMPUTATION

Compute cosine similarity.

Rule:

```
similarity > 0.80 → candidate merge
```

Build similarity graph:

* concepts = nodes
* edges where similarity above threshold

---

## 10. STEP 4 — CLUSTERING

Create clusters using connected components.

Each cluster represents possible same concept.

Example:

```
Cluster:
- Overfitting
- Model Overfitting
- Over-fit models
```

---

## 11. STEP 5 — LLM VERIFICATION (RECOMMENDED)

Use Ollama (llama3.1:8b).

Purpose:

Prevent incorrect merges.

Prompt template:

```
Are the following terms referring to the SAME technical concept?

Terms:
- X
- Y
- Z

Answer only:
YES or NO
```

If NO:

* split cluster.

This prevents semantic collapse.

---

## 12. STEP 6 — CANONICAL NAME SELECTION

Rules:

1. shortest clear technical term
2. most frequent occurrence
3. properly capitalized

Example:

```
Overfitting ← canonical
```

NOT:

```
Model Overfitting Problem
```

---

## 13. STEP 7 — MERGE METADATA

Merge all cluster data:

* aliases
* descriptions
* source_blocks
* occurrence count

Example:

```python
occurrence_count = len(cluster_items)
```

---

## 14. STEP 8 — IMPORTANCE SCORE (OPTIONAL BUT RECOMMENDED)

Compute:

```
importance =
    frequency_weight +
    section_spread_weight +
    heading_depth_weight
```

Used later for graph visualization and ranking.

---

## 15. PIPELINE EXECUTION (pipeline.py)

Pseudo-flow:

```python
def normalize_concepts(candidates):
    candidates = preprocess_names(candidates)

    embeddings = generate_embeddings(candidates)

    clusters = cluster_by_similarity(candidates, embeddings)

    verified_clusters = verify_clusters_with_llm(clusters)

    canonical = build_canonical_concepts(verified_clusters)

    return canonical
```

---

## 16. SAVE OUTPUT

```
data/concepts/canonical_concepts.json
```

---

## 17. DEBUG MODE

Print:

* total candidates
* cluster count
* average cluster size
* merges rejected by LLM

---

## 18. IMPORTANT CONSTRAINTS

DO NOT:

* extract relationships
* alter meaning of concepts
* delete provenance
* summarize concepts

This phase only normalizes nodes.

---

## 19. SUCCESS CRITERIA

After execution:

* duplicates removed
* aliases grouped
* canonical names stable
* concept count significantly reduced

Example expected result:

```
Overfitting (aliases: 4)
Gradient Descent (aliases: 2)
Cross Validation (aliases: 3)
```

---

## 20. END GOAL

Phase 4 produces:

```
Stable canonical graph nodes
```

These become nodes for Phase 5:

```
Relationship Extraction
```

END OF SPEC.

```
::contentReference[oaicite:0]{index=0}
```
