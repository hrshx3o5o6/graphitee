"""Data models for final graph assembly."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph."""
    
    id: str
    label: str
    type: str
    aliases: List[str] = field(default_factory=list)
    occurrence_count: int = 0
    importance_score: float = 0.0
    
    # Graph metrics (computed later)
    degree_centrality: float = 0.0
    betweenness_centrality: float = 0.0
    clustering_coefficient: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "aliases": self.aliases,
            "occurrence_count": self.occurrence_count,
            "importance_score": round(self.importance_score, 3),
            "metrics": {
                "degree_centrality": round(self.degree_centrality, 3),
                "betweenness_centrality": round(self.betweenness_centrality, 3),
                "clustering_coefficient": round(self.clustering_coefficient, 3)
            }
        }
    
    def to_viz_dict(self) -> Dict:
        """Convert to visualization-ready format (minimal)."""
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "importance": round(self.importance_score, 2)
        }


@dataclass
class GraphEdge:
    """Represents an edge in the knowledge graph."""
    
    id: str
    source: str
    target: str
    relation_type: str
    confidence: float
    evidence_blocks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "relation_type": self.relation_type,
            "confidence": round(self.confidence, 2),
            "evidence_blocks": self.evidence_blocks
        }
    
    def to_viz_dict(self) -> Dict:
        """Convert to visualization-ready format (minimal)."""
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation_type,
            "weight": round(self.confidence, 2)
        }


@dataclass
class FinalGraph:
    """Complete knowledge graph with nodes and edges."""
    
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with full information."""
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "metadata": self.metadata
        }
    
    def to_viz_dict(self) -> Dict:
        """Convert to visualization-ready format (minimal payload)."""
        return {
            "nodes": [node.to_viz_dict() for node in self.nodes],
            "edges": [edge.to_viz_dict() for edge in self.edges]
        }


# Relation type priority for conflict resolution
RELATION_PRIORITY = {
    "DEFINES": 5,
    "CAUSES": 4,
    "DEPENDS_ON": 3,
    "PART_OF": 3,
    "USES": 2,
    "EXTENDS": 2,
    "CONTRASTS_WITH": 2,
    "MEASURED_BY": 2,
    "ASSOCIATED_WITH": 1
}
