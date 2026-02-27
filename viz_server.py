"""Phase 7: Interactive Graph Visualization Server

Serves the 3D graph visualization web interface.
"""

import json
import argparse
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os


class GraphAPIHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with API support for graph data."""

    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(
            *args, directory=str(Path(__file__).parent / "frontend" / "dist"), **kwargs
        )

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)

        # Handle API endpoints
        if parsed_path.path.startswith("/api/"):
            self.handle_api_request(parsed_path)
        else:
            # Serve static files (React app)
            super().do_GET()

    def handle_api_request(self, parsed_path):
        """Handle API requests for graph data."""
        try:
            if parsed_path.path == "/api/graphs":
                # List available graphs
                self.serve_graph_list()
            elif parsed_path.path.startswith("/api/graph/"):
                # Serve specific graph
                graph_id = parsed_path.path.split("/api/graph/")[-1]
                self.serve_graph(graph_id)
            else:
                self.send_error(404, "API endpoint not found")
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")

    def serve_graph_list(self):
        """Send list of available graphs."""
        data_dir = Path("data/graph")

        if not data_dir.exists():
            self.send_json_response([])
            return

        graphs = []
        for graph_file in data_dir.glob("*_final_graph.json"):
            try:
                with open(graph_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                doc_id = graph_file.stem.replace("_final_graph", "")

                # Get node and edge counts
                if isinstance(data, dict) and "nodes" in data:
                    node_count = len(data.get("nodes", []))
                    edge_count = len(data.get("edges", []))
                else:
                    node_count = 0
                    edge_count = 0

                graphs.append(
                    {
                        "id": doc_id,
                        "name": doc_id.replace("_", " ").title(),
                        "nodeCount": node_count,
                        "edgeCount": edge_count,
                        "file": graph_file.name,
                    }
                )
            except Exception as e:
                print(f"Error reading {graph_file}: {e}")
                continue

        self.send_json_response(graphs)

    def serve_graph(self, graph_id):
        """Send specific graph data."""
        # First check for current_graph.json (from CLI)
        if graph_id == "current":
            graph_file = Path("data/current_graph.json")
        else:
            graph_file = Path(f"data/graph/{graph_id}_final_graph.json")

        if not graph_file.exists():
            self.send_error(404, f"Graph not found: {graph_id}")
            return

        try:
            with open(graph_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # If data has nodes/edges directly, use it
            # If it has nested structure from Phase 6, extract it
            if isinstance(data, dict):
                if "nodes" in data and "edges" in data:
                    # Already in correct format
                    self.send_json_response(data)
                else:
                    self.send_error(500, "Invalid graph data format")
            else:
                self.send_error(500, "Invalid graph data format")
        except Exception as e:
            self.send_error(500, f"Error loading graph: {str(e)}")

    def send_json_response(self, data):
        """Send JSON response."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def end_headers(self):
        """Add CORS headers."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()


def check_frontend_build():
    """Check if frontend is built."""
    dist_dir = Path(__file__).parent / "frontend" / "dist"

    if not dist_dir.exists() or not (dist_dir / "index.html").exists():
        return False
    return True


def build_frontend():
    """Build the frontend if not already built."""
    frontend_dir = Path(__file__).parent / "frontend"

    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False

    print("🔨 Building frontend...")
    print("   Run: cd frontend && npm install && npm run build")
    print()
    print("   Quick setup:")
    print("   1. cd frontend")
    print("   2. npm install")
    print("   3. npm run build")
    print("   4. cd ..")
    print("   5. Run this command again")
    return False


def start_server(port: int = 8080, auto_open: bool = True):
    """Start the visualization server.

    Args:
        port: Port number to run server on
        auto_open: If True, open browser automatically
    """
    # Check if frontend is built
    if not check_frontend_build():
        print("\n❌ Frontend not built yet.")
        build_frontend()
        return

    # Check if graphs exist
    graph_dir = Path("data/graph")
    if not graph_dir.exists() or not list(graph_dir.glob("*_final_graph.json")):
        print("\n❌ No graphs found in data/graph/")
        print("   Run Phase 6 to generate graphs:")
        print("   python graph_refiner.py --all")
        return

    # Start server
    server_address = ("", port)
    httpd = HTTPServer(server_address, GraphAPIHandler)

    print(f"\n🚀 Graphitee Visualization Server")
    print(f"=" * 50)
    print(f"Server running at: http://localhost:{port}")
    print(f"API endpoint: http://localhost:{port}/api/graphs")
    print()
    print("Press Ctrl+C to stop the server")
    print()

    # Open browser
    if auto_open:
        import webbrowser

        webbrowser.open(f"http://localhost:{port}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⛔ Server stopped")
        httpd.shutdown()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 7: Start interactive graph visualization server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server on default port (8080)
  python viz_server.py
  
  # Start server on custom port
  python viz_server.py --port 3000
  
  # Don't open browser automatically
  python viz_server.py --no-open
  
  # Build frontend first
  cd frontend
  npm install
  npm run build
  cd ..
  python viz_server.py
        """,
    )

    parser.add_argument(
        "--port", type=int, default=8080, help="Port to run server on (default: 8080)"
    )

    parser.add_argument(
        "--no-open", action="store_true", help="Don't open browser automatically"
    )

    args = parser.parse_args()

    start_server(port=args.port, auto_open=not args.no_open)


if __name__ == "__main__":
    main()
