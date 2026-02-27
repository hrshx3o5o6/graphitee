"""Query graph tool."""

from pydantic import BaseModel

from agent.tools.base import Tool, ToolOutput


class QueryGraphInput(BaseModel):
    """Input for graph query tool."""

    concept: str
    query_type: str = "dependencies"  # dependencies, related, info


class QueryGraphOutput(ToolOutput):
    """Output from graph query tool."""

    results: list = []


class QueryGraphTool(Tool):
    """Tool for querying the knowledge graph."""

    def __init__(self, graph_reasoner=None):
        super().__init__(
            name="query_graph",
            description="Query the knowledge graph for concept relationships and information.",
            input_model=QueryGraphInput,
            output_model=QueryGraphOutput,
        )
        self.graph_reasoner = graph_reasoner

    def set_graph_reasoner(self, reasoner):
        self.graph_reasoner = reasoner

    async def execute(self, session_id: str, state, **kwargs) -> QueryGraphOutput:
        concept = kwargs.get("concept", "")
        query_type = kwargs.get("query_type", "dependencies")

        if not self.graph_reasoner or self.graph_reasoner.is_empty():
            return QueryGraphOutput(
                success=False,
                error="No knowledge graph loaded. Please load an article first.",
            )

        if not concept:
            return QueryGraphOutput(success=False, error="Concept is required")

        try:
            if query_type == "dependencies":
                results = self.graph_reasoner.get_dependencies(concept)
            elif query_type == "related":
                explored = await state.get_explored_concepts(session_id)
                results = self.graph_reasoner.get_related_unexplored(concept, explored)
            elif query_type == "info":
                info = self.graph_reasoner.get_concept_info(concept)
                if info:
                    results = [{"name": info.name, "definition": info.definition}]
                else:
                    results = []
            elif query_type == "prerequisites":
                results = self.graph_reasoner.get_prerequisite_chain(concept)
            else:
                results = []

            return QueryGraphOutput(success=True, results=results)
        except Exception as e:
            return QueryGraphOutput(success=False, error=str(e))
