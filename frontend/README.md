# Graphitee Frontend

3D interactive knowledge graph visualization built with React and react-force-graph-3d.

## Setup

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build
```

## Technology Stack

- **React 18** - UI framework
- **Vite** - Build tool
- **react-force-graph-3d** - 3D graph visualization
- **Three.js** - 3D graphics (via react-force-graph-3d)

## Project Structure

```
src/
├── App.jsx           # Main app component
├── App.css           # App styles
├── GraphView.jsx     # 3D force-directed graph component
├── NodePanel.jsx     # Node details sidebar
├── NodePanel.css     # Panel styles
├── graphLoader.js    # Graph data loading utilities
└── main.jsx          # React entry point
```

## Features

### Interactive 3D Graph

- Force-directed physics simulation
- Drag to rotate, scroll to zoom
- Click nodes for details
- Double-click to focus on node

### Visual Encoding

**Nodes:**
- Size = importance score
- Color = concept type
  - Blue = Core Concept
  - Green = Technique  
  - Orange = Metric
  - Purple = Process
  - Red = Assumption

**Edges:**
- Width = confidence/weight
- Color = relation type
- Arrows show direction

### Node Highlighting

- Hover: highlights node and immediate neighbors
- Click: keeps highlighting and opens detail panel
- Navigation: click connected nodes in panel to traverse graph

### Node Panel

Shows when node is clicked:
- Concept label and type
- Importance score
- Aliases
- Graph metrics (centrality, clustering)
- Incoming/outgoing connections
- Relation types

## API Integration

Frontend expects a backend API at:

- `GET /api/graphs` - List available graphs
- `GET /api/graph/<id>` - Get specific graph data

Expected graph format:

```json
{
  "nodes": [
    {
      "id": "cn_001",
      "label": "Concept Name",
      "type": "core_concept",
      "importance": 0.82,
      "aliases": ["alias1"],
      "metrics": {...}
    }
  ],
  "edges": [
    {
      "source": "cn_001",
      "target": "cn_002",
      "relation": "CAUSES",
      "weight": 0.85
    }
  ]
}
```

## Development

```bash
# Start dev server (with hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Production Deployment

After building, the `dist/` folder contains the static files ready to be served by any web server.

The Python visualization server (`viz_server.py`) automatically serves this build.
