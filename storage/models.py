"""Data models for the semantic article ingestion system."""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
import hashlib


class ContentBlock(BaseModel):
    """Represents a single content block (paragraph, heading, code, list)."""
    
    type: Literal["heading", "paragraph", "code", "list"]
    tag: str
    text: str
    position: int
    
    
class Section(BaseModel):
    """Represents a hierarchical section with heading and content blocks."""
    
    section_id: str
    heading: str
    level: int  # 1-6 for h1-h6
    content_blocks: List[ContentBlock] = Field(default_factory=list)
    order_index: int
    children: List["Section"] = Field(default_factory=list)
    
    
class Link(BaseModel):
    """Represents a link found in the document."""
    
    source_doc_id: str
    target_url: str
    anchor_text: str
    is_internal: bool
    
    
class Document(BaseModel):
    """Represents a complete document with metadata and structured content."""
    
    id: str
    url: str
    title: str
    domain: str
    timestamp: str
    depth: int = 0
    parent_url: Optional[str] = None
    sections: List[Section] = Field(default_factory=list)
    links: List[Link] = Field(default_factory=list)
    
    @staticmethod
    def generate_id(url: str) -> str:
        """Generate a unique ID from URL."""
        return hashlib.md5(url.encode()).hexdigest()[:12]
    
    @classmethod
    def create(
        cls,
        url: str,
        title: str,
        domain: str,
        depth: int = 0,
        parent_url: Optional[str] = None
    ) -> "Document":
        """Create a new document with generated ID and timestamp."""
        return cls(
            id=cls.generate_id(url),
            url=url,
            title=title,
            domain=domain,
            timestamp=datetime.now().isoformat(),
            depth=depth,
            parent_url=parent_url
        )
