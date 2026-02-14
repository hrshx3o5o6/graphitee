"""Main normalization pipeline."""

import logging
from typing import List, Optional
from normalization.models import ConceptCandidate, CanonicalConcept
from normalization.preprocessor import preprocess_candidates, exact_match_deduplication
from normalization.embedder import ConceptEmbedder
from normalization.clustering import cluster_concepts, get_clustering_stats
from normalization.verifier import ClusterVerifier
from normalization.canonicalizer import build_canonical_concepts

logger = logging.getLogger(__name__)


class NormalizationPipeline:
    """Main pipeline for normalizing concept candidates into canonical concepts."""
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.80,
        verify_with_llm: bool = True,
        llm_model: str = "llama3.1:8b"
    ):
        """Initialize normalization pipeline.
        
        Args:
            embedding_model: Sentence transformer model for embeddings
            similarity_threshold: Minimum similarity for clustering
            verify_with_llm: Whether to verify clusters with LLM
            llm_model: Ollama model for verification
        """
        self.embedding_model_name = embedding_model
        self.similarity_threshold = similarity_threshold
        self.verify_with_llm = verify_with_llm
        self.llm_model = llm_model
        
        # Initialize components
        self.embedder: Optional[ConceptEmbedder] = None
        self.verifier: Optional[ClusterVerifier] = None
        
        self.stats = {
            "input_candidates": 0,
            "after_preprocessing": 0,
            "after_exact_dedup": 0,
            "clusters_created": 0,
            "clusters_verified": 0,
            "canonical_concepts": 0
        }
    
    def normalize(
        self,
        candidates: List[dict],
        skip_verification: bool = False
    ) -> List[CanonicalConcept]:
        """Execute full normalization pipeline.
        
        Args:
            candidates: List of concept candidate dictionaries
            skip_verification: Skip LLM verification (faster, less accurate)
            
        Returns:
            List of canonical concepts
        """
        logger.info("="*70)
        logger.info("STARTING CONCEPT NORMALIZATION PIPELINE")
        logger.info("="*70)
        
        # Convert dicts to ConceptCandidate objects
        logger.info("Loading concept candidates")
        concept_candidates = [
            ConceptCandidate(**c) for c in candidates
        ]
        self.stats["input_candidates"] = len(concept_candidates)
        logger.info(f"Loaded {len(concept_candidates)} concept candidates")
        
        # Step 1: Preprocessing and string normalization
        logger.info("\n" + "="*70)
        logger.info("STEP 1: String Normalization")
        logger.info("="*70)
        concept_candidates = preprocess_candidates(concept_candidates)
        self.stats["after_preprocessing"] = len(concept_candidates)
        
        # Step 2: Exact match deduplication
        logger.info("\n" + "="*70)
        logger.info("STEP 2: Exact Match Deduplication")
        logger.info("="*70)
        concept_candidates = exact_match_deduplication(concept_candidates)
        self.stats["after_exact_dedup"] = len(concept_candidates)
        
        if not concept_candidates:
            logger.warning("No candidates remaining after deduplication")
            return []
        
        # Step 3: Generate embeddings
        logger.info("\n" + "="*70)
        logger.info("STEP 3: Embedding Generation")
        logger.info("="*70)
        
        if self.embedder is None:
            self.embedder = ConceptEmbedder(self.embedding_model_name)
        
        concept_candidates = self.embedder.embed_concepts(concept_candidates)
        
        # Step 4: Semantic clustering
        logger.info("\n" + "="*70)
        logger.info("STEP 4: Semantic Clustering")
        logger.info("="*70)
        
        clusters = cluster_concepts(concept_candidates, self.similarity_threshold)
        self.stats["clusters_created"] = len(clusters)
        
        # Print clustering stats
        cluster_stats = get_clustering_stats(clusters)
        logger.info(f"Clustering statistics:")
        for key, value in cluster_stats.items():
            logger.info(f"  {key}: {value}")
        
        # Step 5: LLM verification (optional but recommended)
        if self.verify_with_llm and not skip_verification:
            logger.info("\n" + "="*70)
            logger.info("STEP 5: LLM Verification")
            logger.info("="*70)
            
            if self.verifier is None:
                self.verifier = ClusterVerifier(model=self.llm_model)
            
            # Only verify multi-concept clusters
            multi_concept_clusters = [c for c in clusters if len(c.candidates) > 1]
            
            if multi_concept_clusters:
                logger.info(f"Verifying {len(multi_concept_clusters)} multi-concept clusters")
                clusters = self.verifier.verify_clusters(clusters, skip_single=True)
                self.stats["clusters_verified"] = len(clusters)
            else:
                logger.info("No multi-concept clusters to verify")
                for cluster in clusters:
                    cluster.verified = True
        else:
            logger.info("\n" + "="*70)
            logger.info("STEP 5: LLM Verification SKIPPED")
            logger.info("="*70)
            # Mark all as verified
            for cluster in clusters:
                cluster.verified = True
        
        # Step 6: Build canonical concepts
        logger.info("\n" + "="*70)
        logger.info("STEP 6: Canonical Concept Creation")
        logger.info("="*70)
        
        canonical_concepts = build_canonical_concepts(
            clusters,
            all_candidates_count=self.stats["input_candidates"]
        )
        self.stats["canonical_concepts"] = len(canonical_concepts)
        
        # Final summary
        logger.info("\n" + "="*70)
        logger.info("NORMALIZATION COMPLETE")
        logger.info("="*70)
        logger.info(f"Input candidates: {self.stats['input_candidates']}")
        logger.info(f"After preprocessing: {self.stats['after_preprocessing']}")
        logger.info(f"After exact dedup: {self.stats['after_exact_dedup']}")
        logger.info(f"Clusters created: {self.stats['clusters_created']}")
        logger.info(f"Canonical concepts: {self.stats['canonical_concepts']}")
        logger.info(f"Reduction: {self.stats['input_candidates']} → {self.stats['canonical_concepts']} "
                   f"({self.stats['canonical_concepts']/self.stats['input_candidates']*100:.1f}%)")
        
        return canonical_concepts
    
    def get_stats(self) -> dict:
        """Get pipeline statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.stats.copy()
