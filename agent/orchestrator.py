"""Main orchestrator for the agentic reading companion."""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional

from agent.graph_reasoner import GraphReasoner, ConceptSuggestion
from agent.reasoning import ReasoningEngine, Intent, IntentType
from agent.state import StateManager
from agent.tools.base import ToolRegistry
from services.llm import OllamaLLM


@dataclass
class AgentResponse:
    """Response from the agent."""

    message: str
    suggestions: list[str] = field(default_factory=list)
    should_suggest: bool = True
    tool_results: dict = field(default_factory=dict)


class Agent:
    """Main agent orchestrator."""

    def __init__(
        self, state: Optional[StateManager] = None, llm: Optional[OllamaLLM] = None
    ):
        self.state = state or StateManager()
        self.llm = llm or OllamaLLM()
        self.reasoning = ReasoningEngine(self.llm)
        self.graph_reasoner = GraphReasoner()
        self.tool_registry = ToolRegistry()

        self._current_session_id: Optional[str] = None
        self._article_content: str = ""
        self._article_title: str = ""

        self._register_tools()

    def _register_tools(self):
        """Register available tools."""
        from agent.tools.scrape import ScrapeTool
        from agent.tools.query_graph import QueryGraphTool
        from agent.tools.web_search import WebSearchTool

        scrape_tool = ScrapeTool()
        query_tool = QueryGraphTool(self.graph_reasoner)
        search_tool = WebSearchTool()

        self.tool_registry.register(scrape_tool)
        self.tool_registry.register(query_tool)
        self.tool_registry.register(search_tool)

    async def load_article(self, url: str) -> AgentResponse:
        """Load and analyze an article."""
        await self.state.connect()

        # Create session
        session_id = await self.state.create_session(url)
        self._current_session_id = session_id

        # Scrape article (tier 1)
        scrape_tool = self.tool_registry.get("scrape_article")
        result = await scrape_tool.execute(session_id, self.state, url=url, tier=1)

        if not result.success:
            await self.state.close()
            return AgentResponse(
                message=f"Failed to load article: {result.error}", should_suggest=False
            )

        self._article_title = result.title
        self._article_content = result.content

        # Save article content
        await self.state.save_article_content(
            session_id, {"title": result.title, "content": result.content}
        )

        # Build initial graph from content
        await self._build_graph_from_content(result.content)

        # Mark initial concepts as discovered
        for concept in self.graph_reasoner.get_all_concepts():
            await self.state.update_concept_state(session_id, concept, explored=False)

        # Get initial suggestions
        all_concepts = self.graph_reasoner.get_all_concepts()[:5]

        message = f"""Loaded: **{result.title}**

Found {len(all_concepts)} key concepts. You can ask me questions about this article, or try:
- "ask [question]" - Ask anything about the article
- "graph" - View the knowledge graph
- "quality" - Check article quality and bias
- "prereqs" - See what you should know first"""

        return AgentResponse(
            message=message, suggestions=all_concepts[:3], should_suggest=True
        )

    async def _build_graph_from_content(self, content: str):
        """Build a simple graph from article content using LLM."""
        prompt = f"""Extract key concepts and their relationships from this article content.

Content:
{content[:3000]}

Return a JSON graph with:
{{
  "nodes": [{{"id": "concept_name", "definition": "brief def"}}],
  "edges": [{{"source": "A", "target": "B", "type": "RELATED_TO"}}]
}}

Extract 8-15 most important concepts and their direct relationships."""

        try:
            result = self.llm.generate_json(prompt=prompt, temperature=0.3)
            if result and "nodes" in result:
                self.graph_reasoner.load_graph(result)
        except Exception as e:
            print(f"Graph building error: {e}")
            # Create empty graph
            self.graph_reasoner.load_graph({"nodes": [], "edges": []})

    async def process_input(self, user_input: str) -> AgentResponse:
        """Process user input and return response."""
        if not self._current_session_id:
            return AgentResponse(
                message="No article loaded. Use 'load <url>' to load an article first.",
                should_suggest=False,
            )

        # Get conversation history
        history = await self.state.get_conversation_history(
            self._current_session_id, limit=5
        )
        context = "\n".join([f"{m['role']}: {m['content'][:100]}" for m in history])

        # Parse intent
        intent = await self.reasoning.parse_intent(user_input, context)

        # Add user message to history
        await self.state.add_message(self._current_session_id, "user", user_input)

        # Process based on intent
        response = await self._handle_intent(intent, user_input)

        # Add assistant response to history
        await self.state.add_message(
            self._current_session_id, "assistant", response.message
        )

        return response

    async def _handle_intent(self, intent: Intent, user_input: str) -> AgentResponse:
        """Handle the parsed intent."""

        if intent.type == IntentType.ASK_QUESTION:
            return await self._handle_question(intent, user_input)

        elif intent.type == IntentType.EXPLAIN_CONCEPT:
            concept = intent.entities.get("concept", "")
            return await self._explain_concept(concept)

        elif intent.type == IntentType.VIEW_GRAPH:
            return AgentResponse(
                message="Opening 3D knowledge graph visualization...",
                should_suggest=True,
            )

        elif intent.type == IntentType.QUALITY_CHECK:
            return await self._analyze_quality()

        elif intent.type == IntentType.PREREQUISITES:
            return await self._show_prerequisites()

        elif intent.type == IntentType.SUMMARIZE:
            return await self._generate_summary()

        elif intent.type == IntentType.SUGGEST:
            return await self._get_suggestions()

        elif intent.type == IntentType.NAVIGATE:
            concept = intent.entities.get("concept", "")
            return await self._explain_concept(concept)

        else:
            # Default to question answering
            return await self._handle_question(intent, user_input)

    async def _handle_question(self, intent: Intent, user_input: str) -> AgentResponse:
        """Handle a question about the article."""

        # Extract concepts from question using graph
        concept_from_question = intent.entities.get("concept", "")

        # If we found a specific concept, explain it
        if concept_from_question:
            return await self._explain_concept(concept_from_question)

        # Otherwise, use LLM to answer from article content
        prompt = f"""Based on this article, answer the user's question.

Article:
{self._article_content[:2500]}

Question: {user_input}

Provide a clear, accurate answer based solely on the article content."""

        try:
            result = self.llm.generate(prompt=prompt, temperature=0.5)
            answer = result.content.strip()
        except Exception as e:
            answer = f"I couldn't find a clear answer to that question in the article."

        # Try to find suggestions based on the question
        suggestions = []
        explored = await self.state.get_explored_concepts(self._current_session_id)

        if not self.graph_reasoner.is_empty():
            # Find concepts related to common topics
            for concept in self.graph_reasoner.get_all_concepts()[:10]:
                if concept not in explored:
                    suggestions.append(concept)
                    if len(suggestions) >= 2:
                        break

        return AgentResponse(
            message=answer, suggestions=suggestions[:2], should_suggest=True
        )

    async def _explain_concept(self, concept: str) -> AgentResponse:
        """Explain a concept from the knowledge graph."""

        if not concept:
            return AgentResponse(
                message="Which concept would you like me to explain?",
                should_suggest=True,
            )

        # Mark as explored
        await self.state.update_concept_state(
            self._current_session_id, concept, explored=True
        )

        # Get concept info from graph
        concept_info = self.graph_reasoner.get_concept_info(concept)

        if concept_info:
            explanation = concept_info.definition or f"Concept: {concept}"
        else:
            # Generate explanation from LLM
            prompt = f"""Explain this concept based on the article.

Article:
{self._article_content[:2000]}

Concept: {concept}

Provide a brief explanation (2-3 sentences)."""

            try:
                result = self.llm.generate(prompt=prompt, temperature=0.5)
                explanation = result.content.strip()
            except Exception:
                explanation = f"Concept: {concept}"

        # Get suggestions
        explored = await self.state.get_explored_concepts(self._current_session_id)

        if not self.graph_reasoner.is_empty():
            suggestions_data = self.graph_reasoner.suggest_next_concepts(
                concept, explored
            )

            # Generate natural language suggestions
            suggestions = [s.concept for s in suggestions_data[:2]]
            suggestion_text = await self.reasoning.generate_suggestion(
                concept, suggestions_data, explored, self._article_title
            )
        else:
            suggestions = []
            suggestion_text = ""

        message = f"**{concept}**: {explanation}"

        if suggestion_text:
            message += f"\n\n{suggestion_text}"

        return AgentResponse(
            message=message, suggestions=suggestions, should_suggest=True
        )

    async def _analyze_quality(self) -> AgentResponse:
        """Analyze article quality and bias."""

        result = await self.reasoning.analyze_quality(self._article_content, [])

        credibility = result.get("credibility_score", 0.5)
        bias = result.get("bias_score", 0.5)
        bias_type = result.get("bias_type", "unknown")

        message = f"""**Article Quality Report**

Credibility: {"█" * int(credibility * 10)}{"░" * (10 - int(credibility * 10))} {int(credibility * 100)}%
Bias: {"█" * int(bias * 10)}{"░" * (10 - int(bias * bias * 10))} {bias_type}
Readability: {result.get("readability", "unknown")}

**Strengths:**
{chr(10).join(f"- {s}" for s in result.get("strengths", [])[:3]) if result.get("strengths") else "- No specific strengths identified"}

**Weaknesses:**  
{chr(10).join(f"- {w}" for w in result.get("weaknesses", [])[:3]) if result.get("weaknesses") else "- No specific weaknesses identified"}"""

        return AgentResponse(message=message, should_suggest=True)

    async def _show_prerequisites(self) -> AgentResponse:
        """Show prerequisites for understanding the article."""

        concepts = self.graph_reasoner.get_all_concepts()

        result = await self.reasoning.detect_prerequisites(
            concepts, self._article_content
        )

        if not result:
            return AgentResponse(
                message="No specific prerequisites detected. The article seems accessible to general readers.",
                should_suggest=False,
            )

        message = "**Prerequisites**\n\nTo get the most out of this article, you should be familiar with:\n\n"

        for prereq in result[:6]:
            level_indicator = {
                "basic": "●○○",
                "intermediate": "●●○",
                "advanced": "●●●",
            }.get(prereq.get("level", "basic"), "●○○")

            message += f"- **{prereq.get('concept')}** ({level_indicator})\n  {prereq.get('reason', '')}\n"

        return AgentResponse(message=message, should_suggest=True)

    async def _generate_summary(self) -> AgentResponse:
        """Generate article summary."""

        concepts = self.graph_reasoner.get_all_concepts()

        summary = await self.reasoning.generate_summary(self._article_content, concepts)

        message = f"""**Summary**

{summary}

---
*This article covers {len(concepts)} key concepts.*"""

        return AgentResponse(message=message, should_suggest=True)

    async def _get_suggestions(self) -> AgentResponse:
        """Get suggested next concepts to explore."""

        explored = await self.state.get_explored_concepts(self._current_session_id)
        all_concepts = self.graph_reasoner.get_all_concepts()

        # Get unexplored concepts
        unexplored = [c for c in all_concepts if c not in explored]

        if not unexplored:
            return AgentResponse(
                message="You've explored all the main concepts! Try asking me specific questions about the article.",
                should_suggest=False,
            )

        # Prioritize concepts that are dependencies for others
        suggestions_data = []
        for concept in unexplored[:10]:
            deps = self.graph_reasoner.get_dependencies(concept, max_depth=1)
            if deps:
                suggestions_data.append(
                    ConceptSuggestion(
                        concept=concept,
                        reason=f"Prerequisite for: {', '.join(deps[:2])}",
                        relevance_score=1.0,
                        is_prerequisite=True,
                    )
                )
            else:
                suggestions_data.append(
                    ConceptSuggestion(
                        concept=concept,
                        reason="Key concept in article",
                        relevance_score=0.5,
                        is_prerequisite=False,
                    )
                )

        suggestions_data.sort(
            key=lambda x: (x.is_prerequisite, x.relevance_score), reverse=True
        )

        message = "**Suggested Next Concepts**\n\n"
        for i, s in enumerate(suggestions_data[:4], 1):
            message += f"{i}. **{s.concept}** - {s.reason}\n"

        return AgentResponse(
            message=message,
            suggestions=[s.concept for s in suggestions_data[:3]],
            should_suggest=True,
        )

    async def close(self):
        """Clean up resources."""
        await self.state.close()
