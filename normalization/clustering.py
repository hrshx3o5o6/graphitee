"""Clustering logic for grouping similar concepts."""

import logging
from typing import List, Set, Dict
from normalization.models import ConceptCandidate, ConceptCluster
from normalization.embedder import cosine_similarity

logger = logging.getLogger(__name__)


def compute_similarity_matrix(
    candidates: List[ConceptCandidate],
    threshold: float = 0.80
) -> Dict[tuple, float]:
    """Compute pairwise similarity scores above threshold.
    
    Args:
        candidates: List of concept candidates with embeddings
        threshold: Minimum similarity to include
        
    Returns:
        Dictionary mapping (idx1, idx2) -> similarity score
    """
    logger.info(f"Computing similarity matrix for {len(candidates)} candidates")
    logger.info(f"Similarity threshold: {threshold}")
    
    similarities = {}
    total_pairs = len(candidates) * (len(candidates) - 1) // 2
    checked = 0
    
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            checked += 1
            
            if checked % 1000 == 0:
                logger.debug(f"Checked {checked}/{total_pairs} pairs")
            
            # Compute similarity
            sim = cosine_similarity(
                candidates[i].embedding,
                candidates[j].embedding
            )
            
            # Store if above threshold
            if sim >= threshold:
                similarities[(i, j)] = sim
    
    logger.info(f"Found {len(similarities)} similar pairs above threshold")
    return similarities


def build_similarity_graph(
    num_concepts: int,
    similarities: Dict[tuple, float]
) -> Dict[int, Set[int]]:
    """Build adjacency list representation of similarity graph.
    
    Args:
        num_concepts: Number of concepts
        similarities: Similarity pairs above threshold
        
    Returns:
        Adjacency list: concept_idx -> set of connected concept indices
    """
    graph = {i: set() for i in range(num_concepts)}
    
    for (i, j), sim in similarities.items():
        graph[i].add(j)
        graph[j].add(i)
    
    return graph


def find_connected_components(graph: Dict[int, Set[int]]) -> List[Set[int]]:
    """Find connected components using DFS.
    
    Each component is a cluster of similar concepts.
    
    Args:
        graph: Adjacency list representation
        
    Returns:
        List of connected components (sets of indices)
    """
    visited = set()
    components = []
    
    def dfs(node: int, component: Set[int]):
        """Depth-first search to find component."""
        visited.add(node)
        component.add(node)
        
        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor, component)
    
    # Find all components
    for node in graph:
        if node not in visited:
            component = set()
            dfs(node, component)
            components.append(component)
    
    return components


def cluster_concepts(
    candidates: List[ConceptCandidate],
    similarity_threshold: float = 0.80
) -> List[ConceptCluster]:
    """Cluster similar concepts using connected components.
    
    Args:
        candidates: List of concept candidates with embeddings
        similarity_threshold: Minimum similarity for clustering
        
    Returns:
        List of concept clusters
    """
    logger.info(f"Clustering {len(candidates)} concepts")
    logger.info(f"Threshold: {similarity_threshold}")
    
    if not candidates:
        return []
    
    # Compute similarities
    similarities = compute_similarity_matrix(candidates, similarity_threshold)
    
    # Build graph
    graph = build_similarity_graph(len(candidates), similarities)
    
    # Find connected components
    components = find_connected_components(graph)
    
    # Create clusters
    clusters = []
    cluster_id = 0
    
    for component in components:
        # Get candidates in this cluster
        cluster_candidates = [candidates[idx] for idx in component]
        
        # Calculate average similarity within cluster
        if len(component) > 1:
            cluster_sims = [
                similarities.get((min(i, j), max(i, j)), 0.0)
                for i in component
                for j in component
                if i < j
            ]
            avg_sim = sum(cluster_sims) / len(cluster_sims) if cluster_sims else 0.0
        else:
            avg_sim = 1.0
        
        cluster = ConceptCluster(
            cluster_id=cluster_id,
            candidates=cluster_candidates,
            similarity_score=avg_sim,
            verified=False
        )
        
        clusters.append(cluster)
        cluster_id += 1
    
    # Sort clusters by size (largest first)
    clusters.sort(key=lambda c: len(c.candidates), reverse=True)
    
    # Log statistics
    cluster_sizes = [len(c.candidates) for c in clusters]
    single_concept_clusters = sum(1 for size in cluster_sizes if size == 1)
    multi_concept_clusters = len(clusters) - single_concept_clusters
    
    logger.info(f"Created {len(clusters)} clusters")
    logger.info(f"  - Single-concept clusters: {single_concept_clusters}")
    logger.info(f"  - Multi-concept clusters: {multi_concept_clusters}")
    
    if multi_concept_clusters > 0:
        logger.info(f"  - Average cluster size: {sum(cluster_sizes) / len(clusters):.1f}")
        logger.info(f"  - Largest cluster: {max(cluster_sizes)} concepts")
    
    return clusters


def get_clustering_stats(clusters: List[ConceptCluster]) -> dict:
    """Get statistics about clustering results.
    
    Args:
        clusters: List of clusters
        
    Returns:
        Statistics dictionary
    """
    cluster_sizes = [len(c.candidates) for c in clusters]
    
    return {
        "total_clusters": len(clusters),
        "single_concept_clusters": sum(1 for size in cluster_sizes if size == 1),
        "multi_concept_clusters": sum(1 for size in cluster_sizes if size > 1),
        "avg_cluster_size": sum(cluster_sizes) / len(clusters) if clusters else 0,
        "max_cluster_size": max(cluster_sizes) if clusters else 0,
        "total_concepts": sum(cluster_sizes)
    }
