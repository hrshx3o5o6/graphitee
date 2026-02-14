```markdown
# PHASE 7 — 3D INTERACTIVE GRAPH VISUALIZATION (IMPLEMENTATION SPEC)

You are implementing **Phase 7** of a semantic knowledge graph pipeline.

Completed phases:

- Phase 1 → Website extraction
- Phase 2 → Semantic block building
- Phase 3 → Concept extraction
- Phase 4 → Concept normalization
- Phase 5 → Relationship extraction
- Phase 6 → Graph refinement & final graph assembly

You now have:

```

final_graph.json

```

Your task:

> Build an interactive 3D visualization layer that allows users to explore the knowledge graph like a mental map.

This phase contains **NO AI**, NO LLM calls, and NO graph recomputation.

This is purely visualization + interaction engineering.

---

## 1. OBJECTIVE

Input:

```

final_graph.json

```

Output:

- Local interactive web interface
- 3D force-directed graph
- Clickable nodes
- Navigable concept relationships

Goal:

- Make concepts explorable
- Preserve semantic meaning visually
- Enable mental navigation between related ideas

---

## 2. HIGH-LEVEL ARCHITECTURE

System design:

```

CLI Pipeline
↓
final_graph.json
↓
Local Web Server
↓
Frontend Visualization (3D Graph)

````

Pipeline generates data.
Frontend renders it.

---

## 3. RECOMMENDED TECH STACK

Use:

- React
- react-force-graph (3D)
- Three.js (internally used by library)

Reason:

- Built-in force physics
- Good performance
- Easy node interaction
- Designed for graph visualization

Alternative stacks are NOT recommended for this phase.

---

## 4. INPUT DATA FORMAT

Example:

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
````

---

## 5. REQUIRED FRONTEND STRUCTURE

```
frontend/
├── src/
│   ├── App.jsx
│   ├── GraphView.jsx
│   ├── NodePanel.jsx
│   ├── graphLoader.js
│   └── styles.css
└── public/
    └── final_graph.json
```

---

## 6. GRAPH LOADING

Load graph data once at startup.

Example:

```js
fetch("/final_graph.json")
  .then(res => res.json())
  .then(setGraphData);
```

Graph data should remain immutable during visualization.

---

## 7. FORCE-DIRECTED GRAPH SETUP

Render using:

```jsx
<ForceGraph3D
  graphData={data}
/>
```

Physics engine should:

* repel nodes
* treat edges as springs
* naturally form clusters

Do NOT manually position nodes initially.

---

## 8. VISUAL MAPPING RULES

### Node Styling

Map semantic meaning → visuals.

Rules:

* node size = importance score
* color = concept type

Example mapping:

```
core_concept → blue
technique → green
metric → orange
process → purple
```

Node size example:

```js
nodeVal={node => node.importance * 10}
```

---

### Edge Styling

Map:

* confidence / weight → thickness
* relation type → color

Example:

```
CAUSES → red
DEPENDS_ON → yellow
CONTRASTS_WITH → purple
ASSOCIATED_WITH → gray
```

---

## 9. INTERACTION REQUIREMENTS (MANDATORY)

### Hover Node

* highlight connected edges
* highlight neighboring nodes

---

### Click Node

Open side panel showing:

* concept label
* aliases
* type
* connected concepts
* relation types

---

### Double Click Node

Camera focuses on node.

Example:

```js
fgRef.current.centerAt(x, y, 1000);
fgRef.current.zoom(4, 1000);
```

---

## 10. LABEL STRATEGY (IMPORTANT)

DO NOT render labels for all nodes.

Rules:

* show label only on hover
* OR show labels when zoomed in

This prevents clutter.

---

## 11. NODE HIGHLIGHT LOGIC

When node selected:

* highlight immediate neighbors
* dim unrelated nodes
* emphasize relevant edges

This improves mental navigation.

---

## 12. CAMERA CONTROLS

Use default controls:

* drag = rotate
* scroll = zoom
* right drag = pan

Do NOT override default physics behavior.

---

## 13. PERFORMANCE RULES

Graph performance must remain smooth.

Guidelines:

* avoid rendering heavy text objects
* avoid per-frame recalculations
* preload graph once
* keep node payload small

---

## 14. OPTIONAL ADVANCED FEATURES

(Implement only if easy)

* cluster-based coloring
* edge hover tooltips
* search box (jump to node)
* collapse weak edges toggle

---

## 15. WHAT THIS PHASE MUST NOT DO

DO NOT:

* run LLMs
* modify graph structure
* generate new relationships
* recalculate importance scores

Visualization must remain deterministic.

---

## 16. SUCCESS CRITERIA

When running the UI:

* graph stabilizes into visible clusters
* large nodes represent important concepts
* clicking nodes reveals relationships
* user can navigate concept chains visually

Example experience:

```
Model Complexity
      ↓ CAUSES
Overfitting
      ↓ AFFECTS
Generalization Error
```

User should be able to discover ideas through traversal.

---

## 17. OUTPUT OF PHASE 7

Final result:

```
Interactive 3D Mental Map
```

The system should feel like exploring ideas spatially.

---

## 18. FINAL GOAL

At the end of Phase 7:

You have built:

* a structured knowledge graph
* an interactive exploration interface
* a mental-map style navigation system

This completes the core system.

Future phases (optional):

* agentic exploration
* guided learning paths
* dynamic explanation generation

---

END OF SPEC.

```
::contentReference[oaicite:0]{index=0}
```
