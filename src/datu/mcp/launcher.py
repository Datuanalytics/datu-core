"""Launcher for MCP server processes."""

import atexit
import socket

# suppressing B404: no user query as input
import subprocess  # nosec B404
import sys
import time

from datu.mcp.registry import mcp_server_registry


def _wait_for_port(host: str, port: int, timeout: float = 10.0):
    """Wait for a port to be available on a given host."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for MCP server on {host}:{port}")


def launch_mcp_server(server_name: str):
    """Generalised launcher for an MCP server process."""
    cfg = mcp_server_registry[server_name]
    python_exe = sys.executable
    proc = subprocess.Popen([python_exe, str(cfg["script"])], shell=False)  # nosec B603
    atexit.register(proc.terminate)
    _wait_for_port(cfg["host"], cfg["port"], timeout=30.0)
    return proc
