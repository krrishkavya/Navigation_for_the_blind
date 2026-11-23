"""
Legacy entry point for backwards compatibility.
Redirects to the simplified edge_server/server.py module.
"""

from server import run_edge_server

if __name__ == "__main__":
    run_edge_server()
