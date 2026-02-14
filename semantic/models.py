"""Data models for semantic blocks."""

from dataclasses import dataclass
from typing import List, Literal


# Valid block types
BlockType = Literal["definition", "explanation", "example", "code", "list"]


@dataclass
class SemanticBlock:
    """Represents a single semantic unit of content.
    
    Each block should represent ONE meaningful idea while preserving
    hierarchy and context from the original document.
    """
    
    block_id: str
    doc_id: str
    section_id: str
    text: str
    block_type: BlockType
    heading_path: List[str]
    order_index: int
    token_estimate: int
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "block_id": self.block_id,
            "doc_id": self.doc_id,
            "section_id": self.section_id,
            "text": self.text,
            "block_type": self.block_type,
            "heading_path": self.heading_path,
            "order_index": self.order_index,
            "token_estimate": self.token_estimate
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SemanticBlock":
        """Create from dictionary."""
        return cls(**data)
