```markdown
# PHASE 2 — SEMANTIC BLOCK BUILDER (IMPLEMENTATION SPEC)

You are implementing **Phase 2** of a semantic knowledge-graph pipeline.

Phase 1 (Playwright extraction) is already completed.

Your task is to build a **deterministic Semantic Block Builder**.

This phase must contain:

- NO LLM usage
- NO AI reasoning
- NO embeddings
- ONLY engineering logic

The goal is to transform structured extraction output into clean semantic units that will later be used for concept extraction.

---

## 1. OBJECTIVE

Input:

Structured extraction JSON.

Output:

```

semantic_blocks.json

````

Each semantic block should represent ONE meaningful idea while preserving hierarchy and context.

---

## 2. INPUT FORMAT (ASSUME THIS EXISTS)

```json
{
  "doc_id": "doc_001",
  "sections": [
    {
      "section_id": "sec_1",
      "heading": "Bias Variance",
      "level": 2,
      "content_blocks": [
        {"type": "paragraph", "text": "..."},
        {"type": "code", "text": "..."}
      ]
    }
  ]
}
````

Sections are already in reading order.

---

## 3. OUTPUT FORMAT

```json
[
  {
    "block_id": "b_001",
    "doc_id": "doc_001",
    "section_id": "sec_1",
    "text": "...",
    "block_type": "definition",
    "heading_path": [
      "Machine Learning",
      "Bias Variance"
    ],
    "order_index": 3,
    "token_estimate": 140
  }
]
```

---

## 4. REQUIRED FOLDER STRUCTURE

Create:

```
semantic/
├── models.py
├── builder.py
├── context.py
├── splitter.py
├── heuristics.py
├── tokenizer.py
└── validator.py
```

Each file must have one responsibility.

---

## 5. DATA MODEL (MANDATORY)

Use dataclass or pydantic.

```python
@dataclass
class SemanticBlock:
    block_id: str
    doc_id: str
    section_id: str
    text: str
    block_type: str
    heading_path: list[str]
    order_index: int
    token_estimate: int
```

---

## 6. PIPELINE OVERVIEW

Implementation flow:

```
Load Document
    ↓
Build Heading Paths
    ↓
Normalize Text
    ↓
Semantic Splitting
    ↓
Infer Block Type
    ↓
Attach Metadata
    ↓
Validate
    ↓
Save semantic_blocks.json
```

---

## 7. MAIN PIPELINE (builder.py)

Implement:

```python
def build_semantic_blocks(document):
    heading_context = build_heading_paths(document["sections"])

    blocks = []
    order_counter = 0

    for section in document["sections"]:
        path = heading_context[section["section_id"]]

        for content in section["content_blocks"]:
            chunks = split_semantically(content)

            for chunk in chunks:
                order_counter += 1
                block = create_semantic_block(
                    chunk,
                    section,
                    path,
                    order_counter
                )
                blocks.append(block)

    validate_blocks(blocks)
    return blocks
```

---

## 8. HEADING PATH RESOLUTION (context.py)

Every block must inherit full heading hierarchy.

```python
def build_heading_paths(sections):
    stack = []
    mapping = {}

    for sec in sections:
        level = sec["level"]

        while stack and stack[-1]["level"] >= level:
            stack.pop()

        stack.append({
            "level": level,
            "heading": sec["heading"]
        })

        mapping[sec["section_id"]] = [
            s["heading"] for s in stack
        ]

    return mapping
```

Example result:

```
["Machine Learning", "Regularization", "L2"]
```

---

## 9. TEXT NORMALIZATION

Minimal cleanup only.

```python
def normalize_text(text):
    return " ".join(text.split())
```

DO NOT rewrite or modify meaning.

---

## 10. SEMANTIC SPLITTER (splitter.py)

### Sentence split

```python
import re

def split_sentences(text):
    return re.split(r'(?<=[.!?])\s+', text)
```

### Semantic grouping

```python
def split_semantically(content):
    text = normalize_text(content["text"])
    sentences = split_sentences(text)

    chunks = []
    current = []

    for s in sentences:
        current.append(s)

        if should_split(s, current):
            chunks.append(" ".join(current))
            current = []

    if current:
        chunks.append(" ".join(current))

    return chunks
```

### Split rules

```python
TRANSITIONS = [
    "however",
    "for example",
    "in contrast",
    "therefore",
    "this means",
    "on the other hand"
]

def should_split(sentence, current):
    lower = sentence.lower()

    if any(t in lower for t in TRANSITIONS):
        return True

    if len(current) >= 5:
        return True

    return False
```

---

## 11. BLOCK TYPE HEURISTICS (heuristics.py)

NO AI.

```python
def infer_block_type(text, original_type):
    if original_type == "code":
        return "code"

    lower = text.lower()

    if "is defined as" in lower or "refers to" in lower:
        return "definition"

    if "for example" in lower or "consider" in lower:
        return "example"

    return "explanation"
```

Allowed types:

```
definition
explanation
example
code
list
```

---

## 12. TOKEN ESTIMATION (tokenizer.py)

Approximation only.

```python
def estimate_tokens(text):
    return int(len(text.split()) * 1.3)
```

---

## 13. CREATE BLOCK FUNCTION

```python
from uuid import uuid4

def create_semantic_block(chunk, section, path, order):
    return SemanticBlock(
        block_id=uuid4().hex,
        doc_id=section["doc_id"],
        section_id=section["section_id"],
        text=chunk,
        block_type=infer_block_type(chunk, "paragraph"),
        heading_path=path,
        order_index=order,
        token_estimate=estimate_tokens(chunk)
    )
```

---

## 14. VALIDATION (validator.py)

```python
def validate_blocks(blocks):
    for b in blocks:
        assert b.text.strip()
        assert len(b.heading_path) > 0
        assert b.token_estimate < 350
```

---

## 15. STORAGE

Save output:

```
data/semantic_blocks/<doc_id>.json
```

Serialized list of semantic blocks.

---

## 16. DEBUG MODE

Optional debug print:

* total sections
* total semantic blocks
* average token size
* block type distribution

---

## 17. SUCCESS CRITERIA

After running:

```
python semantic_builder.py <doc.json>
```

You should get:

* one idea per block
* preserved heading context
* stable order
* manageable block sizes

Example:

```
[definition]
Bias variance tradeoff refers to...

[example]
For example, a complex model...

[explanation]
As complexity increases...
```

---

## 18. IMPORTANT RULES

DO NOT:

* flatten full sections
* chunk only by tokens
* use embeddings
* call LLMs

This is purely structural.

---

## 19. END GOAL

Create deterministic semantic units ready for:

```
Phase 3 — Concept Extraction per Semantic Block
```

END OF SPEC.

```
::contentReference[oaicite:0]{index=0}
```
