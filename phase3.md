```markdown
# PHASE 3 — CONCEPT EXTRACTION ENGINE (IMPLEMENTATION PROMPT)

You are implementing **Phase 3** of a knowledge-graph pipeline.

Phase 1 (web extraction) and Phase 2 (semantic block building) are already completed.

This phase extracts **concept candidates** from semantic blocks using an LLM.

Target runtime:

- Local model via Ollama
- llama3.1:8b
- Python implementation

The goal is NOT summarization.

The goal is:

> Convert semantic blocks into structured concept candidates suitable for graph construction.

---

## 1. OBJECTIVE

Input:

```

semantic_blocks.json

```

Output:

```

concept_candidates.json

````

Each concept must be:

- explicit in the text
- technically meaningful
- traceable back to source block

---

## 2. INPUT FORMAT

Assume each semantic block looks like:

```json
{
  "block_id": "b_001",
  "doc_id": "doc_001",
  "section_id": "sec_1",
  "text": "...",
  "block_type": "definition",
  "heading_path": ["Machine Learning", "Regularization"],
  "order_index": 4,
  "token_estimate": 120
}
````

---

## 3. OUTPUT FORMAT

```json
[
  {
    "concept_id": "c_001",
    "name": "Overfitting",
    "type": "core_concept",
    "description": "Model learns noise instead of signal",
    "source_block_id": "b_001",
    "heading_path": ["Machine Learning", "Regularization"],
    "confidence": 0.87
  }
]
```

---

## 4. REQUIRED MODULE STRUCTURE

Create:

```
concepts/
├── models.py
├── prompts.py
├── extractor.py
├── parser.py
├── pipeline.py
└── filters.py
```

---

## 5. DATA MODEL

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

---

## 6. PIPELINE FLOW

```
Load semantic blocks
        ↓
For each block:
    build prompt
        ↓
    call Ollama (llama3.1:8b)
        ↓
    parse JSON response
        ↓
    attach metadata
        ↓
    filter bad concepts
        ↓
Save concept_candidates.json
```

---

## 7. OLLAMA INTEGRATION

Use local Ollama API.

Example:

```python
import requests

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

No streaming required.

---

## 8. CORE PROMPT DESIGN (VERY IMPORTANT)

The model MUST behave like a structured extractor.

DO NOT allow summarization.

Prompt template:

```
You are an information extraction system.

Task:
Extract ONLY technical concepts explicitly mentioned in the text.

Rules:
- Do NOT summarize.
- Do NOT infer unstated ideas.
- Extract only concepts clearly present.
- Ignore generic words like "model", "system", "data" unless specific.

Allowed concept types:
- core_concept
- technique
- metric
- process
- assumption

Return STRICT JSON ONLY.

JSON format:
{
  "concepts": [
    {
      "name": "...",
      "type": "...",
      "description": "...",
      "confidence": 0.0-1.0
    }
  ]
}

Heading context:
{heading_path}

Text:
{block_text}
```

Model output must be pure JSON.

---

## 9. EXECUTION LOOP (pipeline.py)

```python
def extract_concepts(blocks):
    results = []

    for block in blocks:
        prompt = build_prompt(block)

        raw = query_ollama(prompt)

        concepts = parse_output(raw)

        for c in concepts:
            c.source_block_id = block.block_id
            c.heading_path = block.heading_path
            results.append(c)

    return results
```

---

## 10. OUTPUT PARSER (parser.py)

Model output may be imperfect.

Implement safe parsing:

```python
def parse_output(raw):
    try:
        data = json.loads(raw)
        return data.get("concepts", [])
    except:
        return []
```

Never crash pipeline.

---

## 11. CONCEPT FILTERING (filters.py)

Remove generic terms.

Example:

```python
STOP_CONCEPTS = {
    "model",
    "data",
    "system",
    "learning",
    "process"
}
```

Filter rules:

* lowercase comparison
* remove duplicates per block
* remove extremely short names

---

## 12. DESCRIPTION RULE

Descriptions must be:

* short
* factual
* <= 25 words

If longer, truncate.

---

## 13. CONFIDENCE HANDLING

If missing:

```
confidence = 0.6
```

Clamp range:

```
0.0 – 1.0
```

---

## 14. SAVE OUTPUT

File:

```
data/concepts/concept_candidates.json
```

Store flat list.

Duplicates allowed (normalization happens in Phase 4).

---

## 15. DEBUG MODE

Optional debug:

* block_id
* concepts extracted count
* skipped blocks
* parse failures

---

## 16. QUALITY REQUIREMENTS

Good extraction:

```
Overfitting
Gradient Descent
Cross Validation
L2 Regularization
```

Bad extraction:

```
Model
System
Data
Method
```

---

## 17. IMPORTANT CONSTRAINTS

DO NOT:

* summarize the block
* create relationships yet
* merge concepts
* use embeddings
* infer hidden ideas

Only extraction.

---

## 18. SUCCESS CRITERIA

After running:

```
python phase3_pipeline.py
```

You should have:

* clean concept candidates
* each tied to source block
* technically specific terms
* JSON structure stable

---

## 19. END GOAL

Phase 3 produces:

```
semantic text → concept candidates
```

Phase 4 will later:

```
merge duplicates → canonical concepts
```

END OF SPEC.

```
::contentReference[oaicite:0]{index=0}
```
