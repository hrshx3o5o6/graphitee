```markdown
# PHASE 6 — GRAPH REFINEMENT & FINAL GRAPH ASSEMBLY (IMPLEMENTATION SPEC)

You are implementing **Phase 6** of a semantic knowledge graph pipeline.

Completed phases:

- Phase 1 → Website extraction
- Phase 2 → Semantic block building
- Phase 3 → Concept extraction
- Phase 4 → Concept normalization
- Phase 5 → Relationship extraction

You now have:

```

canonical_concepts.json   (graph nodes)
concept_relationships.json (graph edges)

```

Your task:

> Clean, refine, validate, and assemble a high-quality graph ready for visualization and exploration.

This phase turns raw graph output into a stable, usable knowledge graph.

---

## 1. OBJECTIVE

Input:

```

canonical_concepts.json
concept_relationships.json

```

Output:

```

final_graph.json

```

You must:

- remove noisy edges
- score edge reliability
- prune weak graph structure
- compute graph metrics
- prepare visualization-ready format

NO NEW EXTRACTION should happen here.

This is refinement only.

---

## 2. HIGH LEVEL FLOW

```

Load Nodes + Edges
↓
Validate integrity
↓
Remove weak / noisy edges
↓
Resolve edge conflicts
↓
Compute graph metrics
↓
Assign node importance
↓
Prepare visualization payload
↓
Save final_graph.json

```

---

## 3. REQUIRED MODULE STRUCTURE

Create:

```

graph/
├── models.py
├── validator.py
├── edge_refiner.py
├── scoring.py
├── metrics.py
├── assembler.py
└── pipeline.py

````

---

## 4. DATA MODELS

### Graph Node

```python
@dataclass
class GraphNode:
    id: str
    label: str
    type: str
    aliases: list[str]
    occurrence_count: int
    importance_score: float
````

### Graph Edge

```python
@dataclass
class GraphEdge:
    id: str
    source: str
    target: str
    relation_type: str
    confidence: float
    evidence_blocks: list[str]
```

---

## 5. STEP 1 — GRAPH VALIDATION

Validate structure before refinement.

Rules:

* node IDs must be unique
* edges must reference valid node IDs
* no self-loops unless explicitly allowed
* confidence must be [0,1]

Remove invalid edges immediately.

Example:

```python
if edge.source == edge.target:
    discard
```

---

## 6. STEP 2 — EDGE AGGREGATION

Multiple identical edges may exist.

Merge edges using:

```
(source, target, relation_type)
```

Merge logic:

* confidence = average
* evidence blocks = combined unique list

Result:

Cleaner graph with fewer redundant edges.

---

## 7. STEP 3 — EDGE QUALITY FILTERING

Remove weak relationships.

Filtering rules (recommended):

```
confidence < 0.55 → remove
evidence_blocks < 1 → remove
```

Optional advanced rule:

* remove edges from very small blocks (< 30 tokens).

---

## 8. STEP 4 — RELATION CONFLICT RESOLUTION

Sometimes opposite relations appear:

Example:

```
A CAUSES B
A CONTRASTS_WITH B
```

Conflict strategy:

* keep edge with higher confidence
* OR keep both if relation types are not logically contradictory.

Create simple priority ranking:

```
DEFINES > CAUSES > DEPENDS_ON > ASSOCIATED_WITH
```

Higher priority wins in conflicts.

---

## 9. STEP 5 — GRAPH METRICS COMPUTATION

Compute structural metrics for each node.

Use NetworkX.

Metrics:

* degree centrality
* betweenness centrality
* clustering coefficient

Example:

```python
nx.degree_centrality(G)
```

Store results inside node.

---

## 10. STEP 6 — IMPORTANCE SCORING

Compute final node importance.

Suggested formula:

```
importance =
    0.4 * occurrence_count +
    0.3 * degree_centrality +
    0.3 * betweenness_centrality
```

Normalize score to range [0,1].

This will later drive:

* node size
* layout weight
* relevance ranking

---

## 11. STEP 7 — GRAPH PRUNING (OPTIONAL BUT RECOMMENDED)

Remove noisy isolated nodes.

Rules:

```
if node_degree == 0 AND occurrence_count == 1:
    remove node
```

Graph should represent meaningful conceptual structure.

---

## 12. STEP 8 — PREPARE VISUALIZATION FORMAT

Final output should be visualization-ready.

Format:

```json
{
  "nodes": [
    {
      "id": "canon_001",
      "label": "Overfitting",
      "type": "core_concept",
      "importance": 0.82
    }
  ],
  "edges": [
    {
      "source": "canon_002",
      "target": "canon_001",
      "relation": "CAUSES",
      "weight": 0.86
    }
  ]
}
```

Keep payload minimal.

---

## 13. PIPELINE EXECUTION (pipeline.py)

Pseudo-flow:

```python
def build_final_graph(nodes, edges):
    edges = validate_edges(nodes, edges)
    edges = merge_duplicate_edges(edges)
    edges = filter_low_quality(edges)
    edges = resolve_conflicts(edges)

    graph = build_networkx_graph(nodes, edges)

    metrics = compute_graph_metrics(graph)
    nodes = apply_importance_scores(nodes, metrics)

    nodes, edges = prune_graph(nodes, edges)

    return assemble_final_graph(nodes, edges)
```

---

## 14. DEBUG OUTPUT

Print:

* initial node count
* initial edge count
* edges removed
* nodes pruned
* final graph density

---

## 15. IMPORTANT CONSTRAINTS

DO NOT:

* run LLMs
* change concept meaning
* create new concepts
* infer new relationships

This is structural refinement only.

---

## 16. SUCCESS CRITERIA

Final graph should:

* have meaningful connectivity
* avoid clutter
* contain strong relationships
* highlight important concepts automatically

Example result:

```
Overfitting (high importance)
↑
CAUSES
Model Complexity
```

Graph should feel coherent, not random.

---

## 17. FINAL OUTPUT LOCATION

Save:

```
data/graph/final_graph.json
```

---

## 18. END GOAL OF PHASE 6

You now have:

```
A clean, refined, stable knowledge graph
```

Ready for:

* Phase 7 → 3D visualization
* interactive exploration
* mental map navigation

END OF SPEC.

```
::contentReference[oaicite:0]{index=0}
```
