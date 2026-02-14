"""Data models for concept normalization."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ConceptCandidate:
    """Raw concept candidate from Phase 3."""
    
    concept_id: str
    name: str
    type: str
    description: str
    source_block_id: str
    heading_path: List[str]
    confidence: float
    
    # Added during normalization
    normalized_name: str = ""
    embedding: List[float] = field(default_factory=list)


@dataclass
class CanonicalConcept:
    """Normalized canonical concept for graph node."""
    
    canonical_id: str
    canonical_name: str
    aliases: List[str]
    type: str
    descriptions: List[str]
    source_blocks: List[str]
    occurrence_count: int
    importance_score: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "canonical_id": self.canonical_id,
            "canonical_name": self.canonical_name,
            "aliases": self.aliases,
            "type": self.type,
            "descriptions": self.descriptions,
            "source_blocks": self.source_blocks,
            "occurrence_count": self.occurrence_count,
            "importance_score": self.importance_score
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CanonicalConcept":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ConceptCluster:
    """Cluster of similar concepts."""
    
    cluster_id: int
    candidates: List[ConceptCandidate]
    similarity_score: float = 0.0
    verified: bool = False
