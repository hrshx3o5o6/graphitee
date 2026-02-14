"""Heading path resolution for semantic context.

Builds full hierarchical paths for each section to preserve context.
"""

from typing import Dict, List


def build_heading_paths(sections: List[dict]) -> Dict[str, List[str]]:
    """Build full heading hierarchy paths for all sections.
    
    Uses a stack to maintain the current heading hierarchy as we
    traverse sections in order.
    
    Example:
        Input sections with headings:
        - "Machine Learning" (level 1)
        - "Regularization" (level 2)
        - "L2 Regularization" (level 3)
        
        Output:
        {
            "sec_1": ["Machine Learning"],
            "sec_2": ["Machine Learning", "Regularization"],
            "sec_3": ["Machine Learning", "Regularization", "L2 Regularization"]
        }
    
    Args:
        sections: List of section dictionaries from Phase 1
        
    Returns:
        Mapping of section_id to full heading path
    """
    heading_stack = []
    path_mapping = {}
    
    for section in sections:
        section_id = section["section_id"]
        level = section["level"]
        heading = section["heading"]
        
        # Pop headings from stack that are at same or lower level
        # This maintains proper hierarchy
        while heading_stack and heading_stack[-1]["level"] >= level:
            heading_stack.pop()
        
        # Add current heading to stack
        heading_stack.append({
            "level": level,
            "heading": heading
        })
        
        # Build path from current stack
        path = [h["heading"] for h in heading_stack]
        path_mapping[section_id] = path
    
    return path_mapping
