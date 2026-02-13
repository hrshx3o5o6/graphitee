"""Section tree building from content blocks."""

import logging
from typing import List
from storage.models import ContentBlock, Section

logger = logging.getLogger(__name__)


class SectionBuilder:
    """Builds hierarchical section tree from content blocks."""
    
    @staticmethod
    def build_sections(blocks: List[ContentBlock]) -> List[Section]:
        """Build hierarchical sections from flat content blocks.
        
        Uses a heading stack to maintain hierarchy:
        - New heading at same or higher level closes previous section
        - Lower level heading becomes a child section
        
        Args:
            blocks: Flat list of content blocks
            
        Returns:
            List of top-level sections with nested children
        """
        logger.info("Building section tree")
        
        if not blocks:
            return []
        
        sections: List[Section] = []
        section_stack: List[Section] = []  # Stack to track current section hierarchy
        section_counter = 0
        order_index = 0
        
        for block in blocks:
            if block.type == "heading":
                # Create new section for heading
                section_counter += 1
                level = SectionBuilder._get_heading_level(block.tag)
                
                new_section = Section(
                    section_id=f"sec_{section_counter}",
                    heading=block.text,
                    level=level,
                    content_blocks=[],
                    order_index=order_index
                )
                order_index += 1
                
                # Maintain section hierarchy using stack
                SectionBuilder._add_section_to_hierarchy(
                    new_section,
                    section_stack,
                    sections
                )
                
            else:
                # Add content block to current section
                if section_stack:
                    section_stack[-1].content_blocks.append(block)
                else:
                    # No section yet, create a default one
                    section_counter += 1
                    default_section = Section(
                        section_id=f"sec_{section_counter}",
                        heading="Introduction",
                        level=1,
                        content_blocks=[block],
                        order_index=order_index
                    )
                    order_index += 1
                    sections.append(default_section)
                    section_stack.append(default_section)
        
        logger.info(f"Built {section_counter} sections")
        return sections
    
    @staticmethod
    def _get_heading_level(tag: str) -> int:
        """Extract numeric level from heading tag.
        
        Args:
            tag: Heading tag (h1, h2, etc.)
            
        Returns:
            Numeric level (1-6)
        """
        try:
            return int(tag[1])  # Extract number from h1, h2, etc.
        except (IndexError, ValueError):
            return 1
    
    @staticmethod
    def _add_section_to_hierarchy(
        new_section: Section,
        section_stack: List[Section],
        root_sections: List[Section]
    ) -> None:
        """Add a section to the hierarchy using a stack.
        
        Rules:
        - If new section level <= current level: pop stack until we find parent
        - If new section level > current level: it's a child of current
        
        Args:
            new_section: Section to add
            section_stack: Current section hierarchy stack
            root_sections: Root level sections list
        """
        # Pop sections from stack that are at same or lower level
        while section_stack and section_stack[-1].level >= new_section.level:
            section_stack.pop()
        
        # Add section to appropriate parent
        if section_stack:
            # Add as child of current section
            parent = section_stack[-1]
            parent.children.append(new_section)
        else:
            # Add as root section
            root_sections.append(new_section)
        
        # Push new section onto stack
        section_stack.append(new_section)
    
    @staticmethod
    def print_section_tree(sections: List[Section], indent: int = 0) -> None:
        """Print section tree for debugging.
        
        Args:
            sections: Sections to print
            indent: Current indentation level
        """
        for section in sections:
            prefix = "  " * indent
            logger.info(
                f"{prefix}[{section.section_id}] "
                f"{'H' + str(section.level)}: {section.heading} "
                f"({len(section.content_blocks)} blocks)"
            )
            
            if section.children:
                SectionBuilder.print_section_tree(section.children, indent + 1)
