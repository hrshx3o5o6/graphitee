```markdown
# PHASE 5 — RELATIONSHIP EXTRACTION ENGINE (IMPLEMENTATION SPEC)

You are implementing **Phase 5** of a semantic knowledge graph pipeline.

Completed phases:

- Phase 1 → Website extraction
- Phase 2 → Semantic block building
- Phase 3 → Concept extraction
- Phase 4 → Concept normalization (canonical nodes)

You now have stable canonical concepts.

Your task:

> Extract relationships (edges) between canonical concepts to build the knowledge graph.

This phase creates graph structure.

---

## 1. OBJECTIVE

Input:

```

semantic_blocks.json
canonical_concepts.json

```

Output:

```

concept_relationships.json

````

You must:

- detect meaningful relationships between concepts
- ground relationships in source text
- assign relation types
- attach confidence and provenance

DO NOT:

- create new concepts
- modify canonical concepts

---

## 2. HIGH-LEVEL IDEA

Phase 4 produced graph **nodes**.

Phase 5 builds graph **edges**.

Two concepts should only be connected if:

- they appear together in meaningful context
- the relationship is explicitly supported by text

No guessing or hallucination.

---

## 3. INPUT FORMAT

### Canonical Concepts

```json
[
  {
    "canonical_id": "canon_001",
    "canonical_name": "Overfitting",
    "aliases": ["Model Overfitting"],
    "source_blocks": ["b12", "b38"]
  }
]
````

### Semantic Blocks

```json
{
  "block_id": "b12",
  "text": "...",
  "heading_path": ["Machine Learning", "Regularization"]
}
```

---

## 4. OUTPUT FORMAT

```json
[
  {
    "edge_id": "e_001",
    "source_concept_id": "canon_002",
    "target_concept_id": "canon_001",
    "relation_type": "CAUSES",
    "evidence_block_id": "b12",
    "confidence": 0.86
  }
]
```

---

## 5. REQUIRED MODULE STRUCTURE

Create:

```
relationships/
├── models.py
├── candidate_builder.py
├── prompts.py
├── extractor.py
├── parser.py
├── validator.py
└── pipeline.py
```

---

## 6. DATA MODELS

### ConceptEdge

```python
@dataclass
class ConceptEdge:
    edge_id: str
    source_concept_id: str
    target_concept_id: str
    relation_type: str
    evidence_block_id: str
    confidence: float
```

---

## 7. RELATION TYPES (STRICT ONTOLOGY)

ONLY allow these relation types:

```
DEFINES
DEPENDS_ON
CAUSES
PART_OF
USES
EXTENDS
CONTRASTS_WITH
MEASURED_BY
ASSOCIATED_WITH
```

No free-text relation names allowed.

---

## 8. PIPELINE OVERVIEW

```
Load canonical concepts
        ↓
Map concepts to source blocks
        ↓
Generate candidate concept pairs
        ↓
Run LLM relationship extraction
        ↓
Parse and validate output
        ↓
Deduplicate edges
        ↓
Save concept_relationships.json
```

---

## 9. CRITICAL STEP — CANDIDATE PAIR GENERATION

DO NOT compare every concept with every other concept.

Instead:

For each semantic block:

1. Find canonical concepts appearing in that block.
2. Create pair combinations.

Example:

```
Block contains:
- Overfitting
- Model Complexity
- Generalization Error

Candidate pairs:
(A,B), (A,C), (B,C)
```

This drastically reduces noise.

---

## 10. CONCEPT MATCHING TO BLOCKS

A concept exists in a block if:

* canonical name appears OR
* alias appears

Use case-insensitive matching.

Store mapping:

```python
block_id -> [concept_ids]
```

---

## 11. LLM RELATIONSHIP EXTRACTION

Use Ollama:

```
llama3.1:8b
```

LLM runs PER BLOCK.

---

## 12. RELATIONSHIP EXTRACTION PROMPT

Prompt template:

```
You are a relationship extraction system.

Task:
Identify relationships between technical concepts explicitly supported by the text.

Rules:
- ONLY use concepts listed below.
- Do NOT invent concepts.
- Do NOT infer hidden knowledge.
- Extract relationships clearly stated or directly implied.

Allowed relation types:
DEFINES, DEPENDS_ON, CAUSES, PART_OF,
USES, EXTENDS, CONTRASTS_WITH,
MEASURED_BY, ASSOCIATED_WITH

Concepts:
{concept_list}

Text:
{block_text}

Return STRICT JSON:

{
  "relationships": [
    {
      "source": "...",
      "target": "...",
      "relation_type": "...",
      "confidence": 0.0-1.0
    }
  ]
}
```

---

## 13. OLLAMA CALL

Example:

```python
def query_ollama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.1:8b",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]
```

---

## 14. PARSER (STRICT VALIDATION)

Parser must:

* load JSON safely
* discard invalid relation types
* discard self-loops
* discard missing concepts

Example rules:

```python
if source == target:
    skip
```

---

## 15. EDGE VALIDATION

Valid edge:

* both concepts exist in canonical set
* relation type valid
* confidence in range [0,1]

Otherwise discard.

---

## 16. DEDUPLICATION

Same relationship may appear multiple times.

Merge duplicates using:

```
(source, target, relation_type)
```

Aggregate:

* confidence = average
* evidence blocks = list

---

## 17. CONFIDENCE HANDLING

If confidence missing:

```
confidence = 0.6
```

Clamp range:

```
0.0 – 1.0
```

---

## 18. SAVE OUTPUT

```
data/relationships/concept_relationships.json
```

---

## 19. DEBUG MODE

Print:

* total blocks processed
* candidate pairs generated
* relationships extracted
* invalid edges removed

---

## 20. IMPORTANT DESIGN CONSTRAINTS

DO NOT:

* create edges across unrelated blocks
* infer global world knowledge
* connect concepts just because they are similar
* use embeddings for edges

Edges must be TEXT-GROUNDED.

---

## 21. SUCCESS CRITERIA

From a block:

```
Increasing model complexity causes overfitting.
```

Expected edge:

```
Model Complexity --CAUSES--> Overfitting
```

Good output:

* directional
* meaningful
* grounded in evidence block

---

## 22. END GOAL

After Phase 5 you now have:

```
Nodes (Phase 4)
+
Edges (Phase 5)
=
Complete Knowledge Graph
```

Phase 6 will later handle:

* graph refinement
* pruning weak edges
* scoring graph structure
* visualization preparation

END OF SPEC.

```
::contentReference[oaicite:0]{index=0}
```
