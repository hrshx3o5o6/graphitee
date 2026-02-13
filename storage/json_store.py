"""JSON storage implementation for documents."""

import json
import logging
from pathlib import Path
from typing import List, Optional

from storage.models import Document

logger = logging.getLogger(__name__)


class JSONStore:
    """Handles document persistence to JSON files."""
    
    def __init__(self, base_dir: str = "data/docs"):
        """Initialize the JSON store.
        
        Args:
            base_dir: Directory to store JSON files
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"JSON store initialized at {self.base_dir}")
    
    def save_document(self, doc: Document) -> None:
        """Save a document to JSON file.
        
        Args:
            doc: Document to save
        """
        file_path = self.base_dir / f"{doc.id}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(doc.model_dump(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved document {doc.id} to {file_path}")
    
    def load_document(self, doc_id: str) -> Optional[Document]:
        """Load a document from JSON file.
        
        Args:
            doc_id: Document ID to load
            
        Returns:
            Document if found, None otherwise
        """
        file_path = self.base_dir / f"{doc_id}.json"
        
        if not file_path.exists():
            logger.warning(f"Document {doc_id} not found")
            return None
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return Document(**data)
    
    def list_documents(self) -> List[str]:
        """List all stored document IDs.
        
        Returns:
            List of document IDs
        """
        doc_ids = [
            f.stem for f in self.base_dir.glob("*.json")
        ]
        logger.info(f"Found {len(doc_ids)} documents")
        return doc_ids
    
    def document_exists(self, doc_id: str) -> bool:
        """Check if a document exists.
        
        Args:
            doc_id: Document ID to check
            
        Returns:
            True if document exists
        """
        return (self.base_dir / f"{doc_id}.json").exists()
