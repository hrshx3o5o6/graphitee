"""Embedding generation for semantic similarity."""

import logging
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from normalization.models import ConceptCandidate

logger = logging.getLogger(__name__)


class ConceptEmbedder:
    """Generates embeddings for semantic similarity comparison."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedder with a sentence transformer model.
        
        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2)
                       This is a lightweight fast model good for semantic similarity
        """
        logger.info(f"Loading embedding model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero vector on failure
            return [0.0] * 384  # all-MiniLM-L6-v2 dimension
    
    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 100
            )
            
            return [emb.tolist() for emb in embeddings]
            
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            # Fallback to individual encoding
            return [self.generate_embedding(text) for text in texts]
    
    def embed_concepts(
        self,
        candidates: List[ConceptCandidate]
    ) -> List[ConceptCandidate]:
        """Add embeddings to concept candidates.
        
        Uses concept name + description for richer representation.
        
        Args:
            candidates: List of concept candidates
            
        Returns:
            Same list with embedding field populated
        """
        logger.info(f"Embedding {len(candidates)} concept candidates")
        
        # Build text for embedding: name + description
        texts = []
        for candidate in candidates:
            text = f"{candidate.name}. {candidate.description}"
            texts.append(text)
        
        # Generate embeddings in batch
        embeddings = self.generate_embeddings_batch(texts)
        
        # Assign to candidates
        for candidate, embedding in zip(candidates, embeddings):
            candidate.embedding = embedding
        
        logger.info("Embedding complete")
        return candidates


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    if not vec1 or not vec2:
        return 0.0
    
    try:
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        # Compute cosine similarity
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Clamp to [0, 1]
        return float(max(0.0, min(1.0, similarity)))
        
    except Exception as e:
        logger.error(f"Cosine similarity calculation failed: {e}")
        return 0.0
