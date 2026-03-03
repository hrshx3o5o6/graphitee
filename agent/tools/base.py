"""Base tool class and tool registry for agent."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from pydantic import BaseModel


class ToolInput(BaseModel):
    """Base model for tool input."""

    pass


class ToolOutput(BaseModel):
    """Base model for tool output."""

    success: bool = True
    error: Optional[str] = None


@dataclass
class Tool(ABC):
    """Base class for agent tools."""

    name: str
    description: str
    input_model: type[ToolInput] | None = None
    output_model: type[ToolOutput] | None = None

    @abstractmethod
    async def execute(self, session_id: str, state, **kwargs) -> ToolOutput:
        """Execute the tool with given input."""
        pass

    def validate_input(self, input_data: dict) -> ToolInput | None:
        """Validate input data against input model."""
        if self.input_model is None:
            return ToolInput()
        try:
            return self.input_model(**input_data)
        except Exception as e:
            return None


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": t.name, "description": t.description} for t in self._tools.values()
        ]

    def get_tool_schemas(self) -> list[dict]:
        """Get JSON schema for all tools (for LLM function calling)."""
        schemas = []
        for tool in self._tools.values():
            schema = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {"type": "object", "properties": {}, "required": []},
            }
            if tool.input_model:
                # Get fields from pydantic model
                for field_name, field_info in tool.input_model.model_fields.items():
                    schema["parameters"]["properties"][field_name] = {
                        "type": "string",
                        "description": field_info.description or "",
                    }
                    if field_info.is_required():
                        schema["parameters"]["required"].append(field_name)
            schemas.append(schema)
        return schemas
