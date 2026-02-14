"""Canonical concept creation and metadata merging."""

import logging
from uuid import uuid4
from typing import List, Counter
from collections import Counter
from normalization.models import ConceptCluster, CanonicalConcept, ConceptCandidate

logger = logging.getLogger(__name__)


def select_canonical_name(candidates: List[ConceptCandidate]) -> str:
    """Select the best canonical name from cluster.
    
    Rules:
    1. Most frequent occurrence
    2. Shortest clear technical term
    3. Properly capitalized
    
    Args:
        candidates: List of concept candidates
        
    Returns:
        Selected canonical name
    """
    if len(candidates) == 1:
        return candidates[0].name
    
    # Count occurrences of each name
    name_counts = Counter(c.name for c in candidates)
    
    # Get most frequent names
    max_count = max(name_counts.values())
    most_frequent = [name for name, count in name_counts.items() if count == max_count]
    
    # If tie, choose shortest
    if len(most_frequent) > 1:
        most_frequent.sort(key=len)
    
    canonical = most_frequent[0]
    
    logger.debug(f"Selected '{canonical}' from {list(name_counts.keys())}")
    
    return canonical


def compute_importance_score(
    candidates: List[ConceptCandidate],
    all_candidates_count: int
) -> float:
    """Compute importance score for canonical concept.
    
    Factors:
    - Frequency (occurrence count)
    - Section spread (appears in multiple sections)
    - Confidence (average)
    
    Args:
        candidates: List of candidates in cluster
        all_candidates_count: Total number of candidates
        
    Returns:
        Importance score (0.0 to 1.0)
    """
    if not candidates:
        return 0.0
    
    # Frequency weight (normalized)
    frequency = len(candidates) / all_candidates_count
    frequency_weight = min(1.0, frequency * 10)  # Scale up
    
    # Section spread (unique heading paths)
    unique_sections = len(set(
        tuple(c.heading_path) for c in candidates if c.heading_path
    ))
    section_spread_weight = min(1.0, unique_sections / 5)  # Normalize by 5 sections
    
    # Average confidence
    avg_confidence = sum(c.confidence for c in candidates) / len(candidates)
    
    # Combine weights
    importance = (
        0.4 * frequency_weight +
        0.3 * section_spread_weight +
        0.3 * avg_confidence
    )
    
    return round(importance, 3)


def merge_cluster_metadata(
    cluster: ConceptCluster,
    all_candidates_count: int
) -> CanonicalConcept:
    """Create canonical concept from cluster by merging metadata.
    
    Args:
        cluster: Verified concept cluster
        all_candidates_count: Total candidates for importance calculation
        
    Returns:
        Canonical concept
    """
    candidates = cluster.candidates
    
    # Select canonical name
    canonical_name = select_canonical_name(candidates)
    
    # Collect aliases (unique names different from canonical)
    aliases = list(set(
        c.name for c in candidates if c.name != canonical_name
    ))
    aliases.sort()
    
    # Collect unique descriptions
    descriptions = list(set(
        c.description for c in candidates if c.description and c.description.strip()
    ))
    
    # Collect source blocks
    source_blocks = list(set(c.source_block_id for c in candidates))
    
    # Determine type (most common)
    type_counts = Counter(c.type for c in candidates)
    concept_type = type_counts.most_common(1)[0][0]
    
    # Compute importance
    importance = compute_importance_score(candidates, all_candidates_count)
    
    # Create canonical concept
    canonical = CanonicalConcept(
        canonical_id=uuid4().hex[:12],
        canonical_name=canonical_name,
        aliases=aliases,
        type=concept_type,
        descriptions=descriptions,
        source_blocks=source_blocks,
        occurrence_count=len(candidates),
        importance_score=importance
    )
    
    return canonical


def build_canonical_concepts(
    clusters: List[ConceptCluster],
    all_candidates_count: int
) -> List[CanonicalConcept]:
    """Build canonical concepts from verified clusters.
    
    Args:
        clusters: List of verified clusters
        all_candidates_count: Total candidate count
        
    Returns:
        List of canonical concepts
    """
    logger.info(f"Building canonical concepts from {len(clusters)} clusters")
    
    canonical_concepts = []
    
    for cluster in clusters:
        canonical = merge_cluster_metadata(cluster, all_candidates_count)
        canonical_concepts.append(canonical)
    
    # Sort by importance
    canonical_concepts.sort(key=lambda c: c.importance_score, reverse=True)
    
    # Log statistics
    logger.info(f"Created {len(canonical_concepts)} canonical concepts")
    
    # Count concepts with aliases
    with_aliases = sum(1 for c in canonical_concepts if c.aliases)
    logger.info(f"  - Concepts with aliases: {with_aliases}")
    
    # Average occurrence count
    avg_occurrence = sum(c.occurrence_count for c in canonical_concepts) / len(canonical_concepts)
    logger.info(f"  - Average occurrence: {avg_occurrence:.1f}")
    
    return canonical_concepts


def print_canonical_summary(
    concepts: List[CanonicalConcept],
    max_display: int = 20
) -> None:
    """Print summary of canonical concepts.
    
    Args:
        concepts: List of canonical concepts
        max_display: Maximum concepts to display
    """
    if not concepts:
        print("\nNo canonical concepts created.")
        return
    
    print(f"\n{'='*70}")
    print("CANONICAL CONCEPTS SUMMARY")
    print(f"{'='*70}")
    print(f"Total canonical concepts: {len(concepts)}")
    
    # Type distribution
    type_counts = Counter(c.type for c in concepts)
    print(f"\nType distribution:")
    for concept_type, count in type_counts.most_common():
        print(f"  {concept_type}: {count}")
    
    # Concepts with aliases
    with_aliases = sum(1 for c in concepts if c.aliases)
    print(f"\nConcepts with aliases: {with_aliases}")
    
    # Total occurrences
    total_occurrences = sum(c.occurrence_count for c in concepts)
    print(f"Total occurrences merged: {total_occurrences}")
    
    print(f"\nTop {min(max_display, len(concepts))} concepts (by importance):")
    print(f"{'-'*70}")
    
    for i, concept in enumerate(concepts[:max_display], 1):
        alias_str = f" (aliases: {len(concept.aliases)})" if concept.aliases else ""
        
        print(f"\n[{i}] {concept.canonical_name}{alias_str}")
        print(f"    Type: {concept.type}")
        print(f"    Occurrences: {concept.occurrence_count}")
        print(f"    Importance: {concept.importance_score:.3f}")
        
        if concept.aliases:
            print(f"    Aliases: {', '.join(concept.aliases[:3])}")
            if len(concept.aliases) > 3:
                print(f"             ... and {len(concept.aliases) - 3} more")
