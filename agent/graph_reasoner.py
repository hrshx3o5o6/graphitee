"""Graph query engine using Neo4j GraphRAG."""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# Try importing neo4j-graphrag, provide clear error if not available
try:
    from neo4j import GraphDatabase
    from neo4j_graphrag.llm import OllamaLLM
    from neo4j_graphrag.embeddings import OllamaEmbeddings
    from neo4j_graphrag.retrievers import GraphRAG
    from neo4j_graphrag.indexes import create_vector_index
    NEO4J_GRAPHRAG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"neo4j-graphrag not installed: {e}")
    NEO4J_GRAPHRAG_AVAILABLE = False


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
    """Graph-aware reasoning engine using Neo4j GraphRAG."""

    def __init__(
        self,
        neo4j_uri: str = None,
        neo4j_user: str = None,
        neo4j_password: str = None,
        ollama_model: str = "llama3.1:8b",
        embedder_model: str = "mistral",
    ):
        if not NEO4J_GRAPHRAG_AVAILABLE:
            raise ImportError(
                "neo4j-graphrag not installed. Run: pip install 'neo4j-graphrag[ollama]'"
            )

        # Use env vars or defaults
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "password")

        # Neo4j driver
        self.driver = GraphDatabase.driver(
            self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password)
        )

        # Verify connection
        try:
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.neo4j_uri}")
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}")
            raise

        # LLM for extraction
        self.llm = OllamaLLM(model_name=ollama_model)

        # Embedder for semantic search
        self.embedder = OllamaEmbeddings(model=embedder_model)

        # GraphRAG retriever (initialized lazily)
        self._retriever = None

        # In-memory cache for quick lookups
        self._graph: dict[str, Concept] = {}
        self._relationships: dict[str, list[tuple[str, str]]] = {}

    @property
    def retriever(self) -> GraphRAG:
        """Lazy-load GraphRAG retriever."""
        if self._retriever is None:
            self._retriever = GraphRAG(
                llm=self.llm,
                driver=self.driver,
                embedder=self.embedder,
            )
        return self._retriever

    async def build_graph(self, text: str) -> None:
        """Build knowledge graph from text using SimpleKGPipeline."""
        from neo4j_graphrag.pipeline import SimpleKGPipeline
        from neo4j_graphrag.splitters import FixedSizeSplitter

        logger.info("Building knowledge graph from text...")

        # Create pipeline
        kg_builder = SimpleKGPipeline(
            llm=self.llm,
            driver=self.driver,
            text_splitter=FixedSizeSplitter(chunk_size=500, chunk_overlap=100),
            embedder=self.embedder,
        )

        # Run async
        await kg_builder.run_async(text)

        # Create vector index for semantic search
        try:
            create_vector_index(
                self.driver,
                name="text_embeddings",
                label="Chunk",
                embedding_property="embedding",
                dimensions=768,
                similarity_fn="cosine",
            )
            logger.info("Vector index created")
        except Exception as e:
            logger.debug(f"Vector index creation: {e}")

        # Sync to in-memory cache
        await self._sync_from_neo4j()

    async def _sync_from_neo4j(self) -> None:
        """Sync graph data from Neo4j to in-memory cache."""
        self._graph.clear()
        self._relationships.clear()

        # Query all entities
        query = """
        MATCH (e:Entity)
        RETURN e.name AS name, e.description AS description
        """

        with self.driver.session() as session:
            result = session.run(query)
            for record in result:
                name = record["name"]
                self._graph[name] = Concept(
                    name=name,
                    definition=record.get("description"),
                )

        # Query relationships
        rel_query = """
        MATCH (a:Entity)-[r:RELATED_TO]->(b:Entity)
        RETURN a.name AS source, b.name AS target, type(r) AS rel_type
        """

        with self.driver.session() as session:
            result = session.run(rel_query)
            for record in result:
                source = record["source"]
                target = record["target"]
                rel_type = record["rel_type"]

                self._relationships.setdefault(source, []).append((target, rel_type))
                self._relationships.setdefault(target, []).append(
                    (source, rel_type)
                )

                # Track dependencies
                if source in self._graph and rel_type in ("DEPENDS_ON", "REQUIRES"):
                    self._graph[source].dependencies.append(target)
                elif source in self._graph:
                    self._graph[source].related_concepts.append(target)

        logger.info(f"Synced {len(self._graph)} concepts from Neo4j")

    def retrieve(self, query: str, top_k: int = 5) -> str:
        """Retrieve graph-augmented context for a query."""
        try:
            result = self.retriever.search(
                query, retriever_config={"top_k": top_k}
            )
            return result.content if hasattr(result, "content") else str(result)
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return ""

    def load_graph(self, graph_data: dict) -> None:
        """Load graph from dict (legacy compatibility)."""
        self._graph.clear()
        self._relationships.clear()

        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        for node in nodes:
            name = node.get("id", node.get("name", ""))
            self._graph[name] = Concept(
                name=name,
                definition=node.get("definition"),
                confidence=node.get("confidence", 1.0),
                related_concepts=[],
                dependencies=[],
            )

        for edge in edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            rel_type = edge.get("type", "RELATED_TO")

            if source in self._graph and target in self._graph:
                self._relationships.setdefault(source, []).append((target, rel_type))
                self._relationships.setdefault(target, []).append(
                    (source, rel_type)
                )

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

    def get_related_unexplored(
        self, concept: str, explored: set[str]
    ) -> list[str]:
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

        deps = self.get_dependencies(asked_concept, max_depth=3)

        for dep in deps:
            if dep in user_explored:
                continue

            depth = 1
            if dep in self._graph[asked_concept].dependencies:
                depth = 1
            else:
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

        suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
        return suggestions[:5]

    def suggest_next_concepts(
        self, current_concept: str, user_explored: set[str]
    ) -> list[ConceptSuggestion]:
        """Suggest next concepts to explore after viewing current_concept."""
        suggestions = []

        if current_concept not in self._graph:
            return suggestions

        related = self.get_related_unexplored(current_concept, user_explored)

        for rel in related:
            concept_obj = self._graph[rel]

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

    def get_concept_relationships(
        self, concept: str
    ) -> list[tuple[str, str]]:
        """Get all relationships for a concept."""
        return self._relationships.get(concept, [])

    def is_empty(self) -> bool:
        """Check if graph is empty."""
        return len(self._graph) == 0

    def close(self) -> None:
        """Close Neo4j driver."""
        if self.driver:
            self.driver.close()