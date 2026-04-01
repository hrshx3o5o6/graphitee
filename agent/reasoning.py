"""Reasoning engine for hybrid LLM + rule-based decision making."""

from dataclasses import dataclass
from enum import Enum

from services.llm import OllamaLLM


class IntentType(Enum):
    """User intent types."""

    ASK_QUESTION = "ask_question"
    EXPLAIN_CONCEPT = "explain_concept"
    VIEW_GRAPH = "view_graph"
    QUALITY_CHECK = "quality_check"
    PREREQUISITES = "prerequisites"
    SUMMARIZE = "summarize"
    FACT_CHECK = "fact_check"
    SUGGEST = "suggest"
    NAVIGATE = "navigate"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Parsed user intent."""

    type: IntentType
    entities: dict  # concepts, claims, etc.
    confidence: float
    reasoning: str


SYSTEM_PROMPT = """You are a helpful reading companion that analyzes articles and helps users understand them through knowledge graphs.

Your job is to understand what the user wants and extract key entities from their query.

Available intents:
- ask_question: User wants to ask something about the article
- explain_concept: User wants to understand a specific concept
- view_graph: User wants to see the knowledge graph
- quality_check: User wants article quality/bias analysis
- prerequisites: User wants to know prerequisites
- summarize: User wants a summary
- fact_check: User wants to verify a claim
- suggest: User is asking for suggestions on what to explore next
- navigate: User wants to explore a specific concept/node
- unknown: Unclear intent

Return JSON with:
{
  "intent": "intent_type",
  "entities": {"concept": "xyz", "claim": "abc", ...},
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}

If no specific concept is mentioned, look at the conversation context to determine what's being discussed."""


class ReasoningEngine:
    """Hybrid reasoning engine (LLM + rules)."""

    def __init__(self, llm: OllamaLLM = None):
        self.llm = llm or OllamaLLM()

    async def parse_intent(
        self, user_input: str, conversation_context: str = ""
    ) -> Intent:
        """Parse user input into intent using LLM."""
        context_note = (
            f"\n\nRecent conversation:\n{conversation_context}"
            if conversation_context
            else ""
        )
        prompt = f"""User input: {user_input}{context_note}

Analyze the input and determine the intent. Return JSON only."""

        try:
            result = self.llm.generate_json(
                prompt=prompt, system_prompt=SYSTEM_PROMPT, temperature=0.3
            )

            intent_str = result.get("intent", "unknown").lower()
            try:
                intent_type = IntentType(intent_str)
            except ValueError:
                intent_type = IntentType.UNKNOWN

            return Intent(
                type=intent_type,
                entities=result.get("entities", {}),
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", ""),
            )
        except Exception as e:
            return Intent(
                type=IntentType.UNKNOWN,
                entities={},
                confidence=0.0,
                reasoning=f"Error parsing intent: {str(e)}",
            )

    async def generate_suggestion(
        self,
        current_concept: str,
        suggestions: list,
        user_explored: set,
        article_title: str,
    ) -> str:
        """Generate a natural language suggestion using LLM."""
        if not suggestions:
            return "You seem to have explored the main concepts! Try asking me something specific about the article."

        prompt = f"""You're a helpful reading companion. The user is reading "{article_title}" and just learned about "{current_concept}".

Based on the knowledge graph, here are related concepts they haven't explored yet:
{chr(10).join([f"- {s.concept}: {s.reason}" for s in suggestions[:3]])}

Write a brief, friendly suggestion (1-2 sentences) recommending 1-2 concepts to explore next.
Focus on why these concepts are useful for understanding the article.
Keep it natural and not too long."""

        try:
            result = self.llm.generate(prompt=prompt, temperature=0.7)
            return result.content.strip()
        except Exception:
            return f"You might want to explore {suggestions[0].concept} next - it's related to {current_concept}."

    async def explain_concept(
        self,
        concept: str,
        concept_info: dict,
        graph_context: list,
        article_content: str,
    ) -> str:
        """Generate a concept explanation using LLM."""
        definition = concept_info.get("definition", "No definition available")
        related = concept_info.get("related_concepts", [])

        prompt = f"""Explain the concept "{concept}" in the context of this article.

Definition: {definition}
Related concepts: {", ".join(related) if related else "None"}

Article context:
{article_content[:2000]}

Write a clear, educational explanation (2-4 sentences) that:
1. Defines the concept
2. Explains its importance in this article
3. Connects it to related concepts

Keep it concise but informative."""

        try:
            result = self.llm.generate(prompt=prompt, temperature=0.5)
            return result.content.strip()
        except Exception as e:
            return f"{concept}: {definition}"

    async def generate_summary(self, article_content: str, concepts: list[str]) -> str:
        """Generate article summary using LLM."""
        prompt = f"""Summarize this article briefly. 

Article:
{article_content[:3000]}

Key concepts covered: {", ".join(concepts[:10])}

Provide a 3-4 sentence summary that captures the main points and purpose of the article."""

        try:
            result = self.llm.generate(prompt=prompt, temperature=0.5)
            return result.content.strip()
        except Exception as e:
            return f"Error generating summary: {str(e)}"

    async def analyze_quality(self, article_content: str, claims: list[str]) -> dict:
        """Analyze article quality and bias."""
        prompt = f"""Analyze the quality and potential bias of this article.

Article excerpt:
{article_content[:2500]}

Provide a JSON response with:
{{
  "credibility_score": 0.0-1.0,
  "bias_score": 0.0-1.0 (0=neutral, 1=highly biased),
  "bias_type": "none/left/right/technical/ emotional",
  "strengths": ["point 1", "point 2"],
  "weaknesses": ["point 1", "point 2"],
  "readability": "beginner/intermediate/expert"
}}

Be objective and base your analysis on the content provided."""

        try:
            result = self.llm.generate_json(prompt=prompt, temperature=0.3)
            return result
        except Exception as e:
            return {"error": str(e), "credibility_score": 0.5, "bias_score": 0.5}

    async def detect_prerequisites(
        self, concepts: list[str], article_content: str
    ) -> list[dict]:
        """Detect prerequisite knowledge for understanding the article."""
        prompt = f"""Analyze what prerequisite knowledge would help understand this article.

Key concepts in article: {", ".join(concepts[:20])}

Article excerpt:
{article_content[:2000]}

Return JSON array of prerequisites:
[
  {{"concept": "X", "level": "basic/intermediate/advanced", "reason": "why needed"}}
]

List the most important 5-8 prerequisites."""

        try:
            result = self.llm.generate_json(prompt=prompt, temperature=0.4)
            if isinstance(result, list):
                return result
            return result.get("prerequisites", [])
        except Exception:
            return []

    def validate_suggestion(
        self, suggestion: dict, user_explored: set, available_concepts: set
    ) -> bool:
        """Rule-based validation of a suggestion."""
        # Must be a valid concept
        if suggestion.get("concept") not in available_concepts:
            return False

        # Shouldn't be already explored
        if suggestion.get("concept") in user_explored:
            return False

        # Must have positive relevance
        if suggestion.get("relevance_score", 0) <= 0:
            return False

        return True
