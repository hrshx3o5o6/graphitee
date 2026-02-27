"""CLI interface for the agentic reading companion."""

import asyncio
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.theme import Theme

from agent.orchestrator import Agent

custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "red bold",
        "success": "green",
    }
)
console = Console(theme=custom_theme)


class CLI:
    """Command-line interface for Graphitee."""

    def __init__(self):
        self.agent = Agent()
        self.running = False
        self.viz_server_process = None

    async def start(self):
        """Start the CLI."""
        console.print("[bold cyan]Graphitee[/bold cyan] - Agentic Reading Companion")
        console.print("Type 'help' for available commands, 'quit' to exit\n")

        self.running = True

        while self.running:
            try:
                user_input = Prompt.ask("[bold green]>[/bold green]")

                if not user_input.strip():
                    continue

                await self.process_command(user_input)

            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'quit' to exit[/yellow]")
            except EOFError:
                break

        await self.cleanup()

    async def process_command(self, user_input: str):
        """Process a user command."""
        parts = user_input.strip().split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Handle CLI-level commands directly (no LLM needed)
        if command in ("quit", "exit", "q"):
            await self.cleanup()
            return

        if command == "help":
            self.show_help()
            return

        if command == "load":
            if not args:
                console.print("[error]Usage: load <url>[/error]")
                return
            await self.load_article(args)
            return

        # These are handled at CLI level before going to agent
        if command == "graph":
            await self.view_graph()
            return

        if command == "quality":
            await self.show_quality()
            return

        if command == "prereqs":
            await self.show_prereqs()
            return

        if command == "summarize":
            await self.summarize()
            return

        if command in ("what", "next") or user_input.lower().strip() in (
            "what next",
            "suggest",
            "suggestions",
        ):
            await self.show_suggestions()
            return

        if command == "explore":
            if args:
                await self.explore_concept(args)
            else:
                console.print("[error]Usage: explore <concept>[/error]")
            return

        # All other commands go to the agent for natural language processing
        response = await self.agent.process_input(user_input)

        # Display response
        console.print()
        md = Markdown(response.message)
        console.print(md)

        # Show suggestions
        if response.should_suggest and response.suggestions:
            console.print("\n[dim]Quick actions:[/dim]")
            for i, suggestion in enumerate(response.suggestions, 1):
                console.print(f"  [cyan]{i}[/cyan]. explore [bold]{suggestion}[/bold]")

    async def load_article(self, url: str):
        """Load an Article."""
        console.print(f"[info]Loading {url}...[/info]")

        response = await self.agent.load_article(url)

        console.print()
        md = Markdown(response.message)
        console.print(md)

        if response.suggestions:
            console.print("\n[dim]Quick actions:[/dim]")
            for i, suggestion in enumerate(response.suggestions, 1):
                console.print(f"  [cyan]{i}[/cyan]. explore [bold]{suggestion}[/bold]")

    async def view_graph(self):
        """View the knowledge graph - opens 3D visualization."""
        if not self.agent._current_session_id:
            console.print("[error]No article loaded. Use 'load <url>' first.[/error]")
            return

        graph_data = self._get_graph_data_for_viz()

        if not graph_data.get("nodes"):
            console.print(
                "[warning]No graph data available. Load an article first.[/warning]"
            )
            return

        console.print("[info]Preparing 3D visualization...[/info]")

        # Save graph data to temp file
        import json

        graph_file = Path(__file__).parent / "data" / "current_graph.json"
        graph_file.parent.mkdir(exist_ok=True)
        with open(graph_file, "w") as f:
            json.dump(graph_data, f)

        # Start viz server in background
        try:
            self.viz_server_process = subprocess.Popen(
                [sys.executable, "viz_server.py"],
                cwd=Path(__file__).parent,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Wait for server to start
            await asyncio.sleep(2)

            # Open browser
            webbrowser.open("http://localhost:8000")

            console.print("[success]Opened 3D graph at http://localhost:8000[/success]")
            console.print("[dim]Press Ctrl+C to stop the server when done[/dim]")

        except Exception as e:
            console.print(f"[error]Failed to open visualization: {e}[/error]")

    def _get_graph_data_for_viz(self) -> dict:
        """Extract graph data in format expected by viz server."""
        reasoner = self.agent.graph_reasoner
        concepts = reasoner.get_all_concepts()

        nodes = []
        edges = []

        for concept in concepts:
            info = reasoner.get_concept_info(concept)
            nodes.append(
                {
                    "id": concept,
                    "label": concept,
                    "name": concept,
                    "importance": info.confidence if info else 1.0,
                    "type": "core_concept",
                }
            )

            # Get relationships
            for related, rel_type in reasoner.get_concept_relationships(concept):
                edges.append(
                    {
                        "source": concept,
                        "target": related,
                        "relation": rel_type,
                        "weight": 0.5,
                    }
                )

        return {"nodes": nodes, "edges": edges}

    async def show_quality(self):
        """Show article quality analysis."""
        if not self.agent._current_session_id:
            console.print("[error]No article loaded. Use 'load <url>' first.[/error]")
            return

        response = await self.agent._analyze_quality()
        console.print()
        md = Markdown(response.message)
        console.print(md)

    async def show_prereqs(self):
        """Show prerequisites for understanding the article."""
        if not self.agent._current_session_id:
            console.print("[error]No article loaded. Use 'load <url>' first.[/error]")
            return

        response = await self.agent._show_prerequisites()
        console.print()
        md = Markdown(response.message)
        console.print(md)

    async def summarize(self):
        """Generate article summary."""
        if not self.agent._current_session_id:
            console.print("[error]No article loaded. Use 'load <url>' first.[/error]")
            return

        response = await self.agent._generate_summary()
        console.print()
        md = Markdown(response.message)
        console.print(md)

    async def show_suggestions(self):
        """Show suggested next concepts."""
        if not self.agent._current_session_id:
            console.print("[error]No article loaded. Use 'load <url>' first.[/error]")
            return

        response = await self.agent._get_suggestions()
        console.print()
        md = Markdown(response.message)
        console.print(md)

    async def explore_concept(self, concept: str):
        """Explore a specific concept."""
        if not self.agent._current_session_id:
            console.print("[error]No article loaded. Use 'load <url>' first.[/error]")
            return

        response = await self.agent._explain_concept(concept)
        console.print()
        md = Markdown(response.message)
        console.print(md)

        if response.suggestions:
            console.print("\n[dim]Related concepts:[/dim]")
            for s in response.suggestions:
                console.print(f"  • {s}")

    def show_help(self):
        """Show help message."""
        help_text = """
**Commands:**

- `load <url>` - Load and analyze an article
- `graph` - View the 3D knowledge graph (opens in browser)
- `quality` - Analyze article quality and bias
- `prereqs` - Show prerequisites for understanding
- `summarize` - Get article summary
- `what next` - Get suggested concepts to explore
- `explore <concept>` - Explore a specific concept
- `ask <question>` - Ask a question about the article
- `help` - Show this help message
- `quit` - Exit the program
        """
        console.print(Markdown(help_text))

    async def cleanup(self):
        """Clean up resources."""
        self.running = False

        # Kill viz server if running
        if self.viz_server_process:
            self.viz_server_process.terminate()
            self.viz_server_process = None

        await self.agent.close()
        console.print("[info]Goodbye![/info]")


async def main():
    """Main entry point."""
    cli = CLI()
    await cli.start()


if __name__ == "__main__":
    asyncio.run(main())
