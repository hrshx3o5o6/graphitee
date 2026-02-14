"""Data models for relationship extraction."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ConceptEdge:
    """Represents a relationship between two canonical concepts."""
    
    edge_id: str
    source_concept_id: str
    target_concept_id: str
    relation_type: str
    evidence_block_id: str
    confidence: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "edge_id": self.edge_id,
            "source_concept_id": self.source_concept_id,
            "target_concept_id": self.target_concept_id,
            "relation_type": self.relation_type,
            "evidence_block_id": self.evidence_block_id,
            "confidence": self.confidence
        }


@dataclass
class RelationshipCandidate:
    """Candidate concept pair for relationship extraction."""
    
    concept_a_id: str
    concept_a_name: str
    concept_b_id: str
    concept_b_name: str
    block_id: str
    block_text: str


@dataclass
class BlockConceptMapping:
    """Maps blocks to concepts that appear in them."""
    
    block_id: str
    concept_ids: List[str]
    concept_names: List[str]


# Strict relation type ontology
VALID_RELATION_TYPES = {
    "DEFINES",
    "DEPENDS_ON",
    "CAUSES",
    "PART_OF",
    "USES",
    "EXTENDS",
    "CONTRASTS_WITH",
    "MEASURED_BY",
    "ASSOCIATED_WITH"
}
