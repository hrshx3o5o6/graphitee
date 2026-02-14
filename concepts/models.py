"""Data models for concept candidates."""

from dataclasses import dataclass
from typing import List, Literal


# Valid concept types
ConceptType = Literal["core_concept", "technique", "metric", "process", "assumption"]


@dataclass
class ConceptCandidate:
    """Represents a technical concept extracted from a semantic block.
    
    Each concept should be:
    - Explicitly mentioned in the source text
    - Technically meaningful
    - Traceable back to source block
    """
    
    concept_id: str
    name: str
    type: ConceptType
    description: str
    source_block_id: str
    heading_path: List[str]
    confidence: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "concept_id": self.concept_id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "source_block_id": self.source_block_id,
            "heading_path": self.heading_path,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ConceptCandidate":
        """Create from dictionary."""
        return cls(**data)
