"""LLM-based cluster verification to prevent incorrect merges."""

import logging
from typing import List
from normalization.models import ConceptCluster
from concepts.extractor import OllamaExtractor

logger = logging.getLogger(__name__)


class ClusterVerifier:
    """Verifies concept clusters using LLM to prevent incorrect merges."""
    
    def __init__(
        self,
        model: str = "llama3.1:8b",
        ollama_url: str = "http://localhost:11434"
    ):
        """Initialize verifier with Ollama.
        
        Args:
            model: Ollama model to use
            ollama_url: Ollama API URL
        """
        self.extractor = OllamaExtractor(model=model, base_url=ollama_url)
        self.stats = {
            "clusters_checked": 0,
            "clusters_verified": 0,
            "clusters_rejected": 0,
            "clusters_split": 0
        }
    
    def build_verification_prompt(self, concept_names: List[str]) -> str:
        """Build prompt for LLM verification.
        
        Args:
            concept_names: List of concept names in cluster
            
        Returns:
            Verification prompt
        """
        names_str = "\n".join(f"- {name}" for name in concept_names)
        
        prompt = f"""Are the following terms referring to the SAME technical concept?

Terms:
{names_str}

Consider:
- Are they synonyms or just related concepts?
- Do they refer to the exact same thing or different aspects?
- Are they truly interchangeable in technical context?

Answer ONLY with one word:
YES (if they refer to the exact same concept)
NO (if they are related but distinct concepts)

Answer:"""
        
        return prompt
    
    def verify_cluster(self, cluster: ConceptCluster) -> bool:
        """Verify if concepts in cluster should be merged.
        
        Args:
            cluster: Cluster to verify
            
        Returns:
            True if cluster is valid (concepts should merge)
        """
        # Single concept clusters are always valid
        if len(cluster.candidates) == 1:
            return True
        
        # Extract concept names
        concept_names = [c.name for c in cluster.candidates]
        
        logger.debug(f"Verifying cluster: {concept_names}")
        
        # Build prompt
        prompt = self.build_verification_prompt(concept_names)
        
        # Query LLM
        response = self.extractor.query(prompt, temperature=0.0)
        
        if not response:
            logger.warning("No LLM response, defaulting to acceptance")
            return True
        
        # Parse response
        response_lower = response.strip().lower()
        
        # Check for affirmative
        if "yes" in response_lower[:10]:  # Check first 10 chars
            logger.debug(f"✓ Cluster verified: {concept_names}")
            return True
        else:
            logger.info(f"✗ Cluster rejected: {concept_names}")
            logger.debug(f"  LLM response: {response[:100]}")
            return False
    
    def verify_clusters(
        self,
        clusters: List[ConceptCluster],
        skip_single: bool = True
    ) -> List[ConceptCluster]:
        """Verify all clusters and split rejected ones.
        
        Args:
            clusters: List of clusters to verify
            skip_single: Skip single-concept clusters (always valid)
            
        Returns:
            List of verified clusters (rejected ones split into singles)
        """
        logger.info(f"Verifying {len(clusters)} clusters with LLM")
        
        verified_clusters = []
        
        for i, cluster in enumerate(clusters, 1):
            # Skip single-concept clusters
            if skip_single and len(cluster.candidates) == 1:
                cluster.verified = True
                verified_clusters.append(cluster)
                continue
            
            logger.info(f"[{i}/{len(clusters)}] Verifying cluster of {len(cluster.candidates)} concepts")
            
            # Verify with LLM
            is_valid = self.verify_cluster(cluster)
            
            self.stats["clusters_checked"] += 1
            
            if is_valid:
                cluster.verified = True
                verified_clusters.append(cluster)
                self.stats["clusters_verified"] += 1
            else:
                # Split cluster into single-concept clusters
                logger.info(f"  Splitting rejected cluster into {len(cluster.candidates)} singles")
                
                for candidate in cluster.candidates:
                    single_cluster = ConceptCluster(
                        cluster_id=len(verified_clusters),
                        candidates=[candidate],
                        similarity_score=1.0,
                        verified=True
                    )
                    verified_clusters.append(single_cluster)
                
                self.stats["clusters_rejected"] += 1
                self.stats["clusters_split"] += len(cluster.candidates)
        
        logger.info("="*70)
        logger.info("VERIFICATION COMPLETE")
        logger.info("="*70)
        logger.info(f"Clusters checked: {self.stats['clusters_checked']}")
        logger.info(f"Clusters verified: {self.stats['clusters_verified']}")
        logger.info(f"Clusters rejected: {self.stats['clusters_rejected']}")
        logger.info(f"Concepts split: {self.stats['clusters_split']}")
        
        return verified_clusters
    
    def get_stats(self) -> dict:
        """Get verification statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.stats.copy()
