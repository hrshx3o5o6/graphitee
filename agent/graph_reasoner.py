"""Graph query engine for graph-aware reasoning."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Concept:
    """Represents a concept in the knowledge graph."""

    name: str
    definition: Optional[str] = None
    confidence: float = 1.0
    related_concepts: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


@dataclass
class ConceptSuggestion:
    """A suggested concept for the user to explore."""

    concept: str
    reason: str
    relevance_score: float
    is_prerequisite: bool


class GraphReasoner:
    """Graph-aware reasoning engine."""

    def __init__(self):
        self._graph: dict[str, Concept] = {}
        self._relationships: dict[
            str, list[tuple[str, str]]
        ] = {}  # concept -> [(related, type)]

    def load_graph(self, graph_data: dict) -> None:
        """Load graph from data."""
        self._graph.clear()
        self._relationships.clear()

        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        # Build node map
        for node in nodes:
            name = node.get("id", node.get("name", ""))
            self._graph[name] = Concept(
                name=name,
                definition=node.get("definition"),
                confidence=node.get("confidence", 1.0),
                related_concepts=[],
                dependencies=[],
            )

        # Build edges
        for edge in edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            rel_type = edge.get("type", "RELATED_TO")

            if source in self._graph and target in self._graph:
                self._relationships.setdefault(source, []).append((target, rel_type))
                self._relationships.setdefault(target, []).append((source, rel_type))

                # Track dependencies
                if rel_type in ("DEPENDS_ON", "REQUIRES", "PART_OF"):
                    self._graph[source].dependencies.append(target)
                else:
                    self._graph[source].related_concepts.append(target)

    def get_dependencies(self, concept: str, max_depth: int = 2) -> list[str]:
        """Get concepts that this concept depends on."""
        if concept not in self._graph:
            return []

        deps = set()
        to_visit = [(concept, 0)]
        visited = set()

        while to_visit:
            curr, depth = to_visit.pop(0)
            if curr in visited or depth > max_depth:
                continue
            visited.add(curr)

            for dep in self._graph[curr].dependencies:
                if dep not in deps:
                    deps.add(dep)
                    to_visit.append((dep, depth + 1))

        return list(deps)

    def get_dependents(self, concept: str) -> list[str]:
        """Get concepts that depend on this concept."""
        dependents = []
        for name, concept_obj in self._graph.items():
            if concept in concept_obj.dependencies:
                dependents.append(name)
        return dependents

    def get_related_unexplored(self, concept: str, explored: set[str]) -> list[str]:
        """Get related concepts that haven't been explored yet."""
        if concept not in self._graph:
            return []

        related = []
        for related_concept in self._graph[concept].related_concepts:
            if related_concept not in explored:
                related.append(related_concept)

        return related

    def get_prerequisite_chain(self, concept: str) -> list[str]:
        """Get full prerequisite chain for a concept."""
        chain = []
        visited = set()

        def _collect_prereqs(c: str):
            if c in visited:
                return
            visited.add(c)

            for dep in self._graph.get(c, Concept(c)).dependencies:
                _collect_prereqs(dep)
                if dep not in chain:
                    chain.append(dep)

        _collect_prereqs(concept)
        return chain

    def find_knowledge_gaps(
        self, asked_concept: str, user_explored: set[str]
    ) -> list[ConceptSuggestion]:
        """Find unexplored concepts that would help understand the asked concept."""
        suggestions = []

        if asked_concept not in self._graph:
            return suggestions

        # Get dependencies
        deps = self.get_dependencies(asked_concept, max_depth=3)

        for dep in deps:
            if dep in user_explored:
                continue

            # Score based on how direct the dependency is
            depth = 1
            if dep in self._graph[asked_concept].dependencies:
                depth = 1
            else:
                # Check if it's a second-level dependency
                for direct_dep in self._graph[asked_concept].dependencies:
                    if dep in self._graph[direct_dep].dependencies:
                        depth = 2
                        break

            relevance = 1.0 / (depth + 1)

            suggestions.append(
                ConceptSuggestion(
                    concept=dep,
                    reason=f"Required for understanding {asked_concept}",
                    relevance_score=relevance,
                    is_prerequisite=True,
                )
            )

        # Sort by relevance
        suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
        return suggestions[:5]

    def suggest_next_concepts(
        self, current_concept: str, user_explored: set[str]
    ) -> list[ConceptSuggestion]:
        """Suggest next concepts to explore after viewing current_concept."""
        suggestions = []

        if current_concept not in self._graph:
            return suggestions

        # Get related unexplored concepts
        related = self.get_related_unexplored(current_concept, user_explored)

        for rel in related:
            concept_obj = self._graph[rel]

            # Check if it's a prerequisite for other unexplored concepts
            is_prereq_for = []
            for other in related:
                if rel in self._graph[other].dependencies:
                    is_prereq_for.append(other)

            reason = f"Related to {current_concept}"
            if is_prereq_for:
                reason = f"Gateway concept to: {', '.join(is_prereq_for[:2])}"

            suggestions.append(
                ConceptSuggestion(
                    concept=rel,
                    reason=reason,
                    relevance_score=concept_obj.confidence,
                    is_prerequisite=len(is_prereq_for) > 0,
                )
            )

        # Sort by relevance and prerequisites first
        suggestions.sort(
            key=lambda x: (x.is_prerequisite, x.relevance_score), reverse=True
        )
        return suggestions[:3]

    def get_concept_info(self, concept: str) -> Optional[Concept]:
        """Get full concept information."""
        return self._graph.get(concept)

    def get_all_concepts(self) -> list[str]:
        """Get all concept names."""
        return list(self._graph.keys())

    def get_concept_relationships(self, concept: str) -> list[tuple[str, str]]:
        """Get all relationships for a concept."""
        return self._relationships.get(concept, [])

    def is_empty(self) -> bool:
        """Check if graph is empty."""
        return len(self._graph) == 0
